"""
Simple Budget Manager for Atlas Code V2

Provides basic budget tracking and cost estimation without
the complexity of the V1 system.
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class UsageRecord:
    """Record of a single API usage"""
    timestamp: str
    model: str
    tokens_sent: int
    tokens_received: int
    cost: float
    task_type: str = "unknown"


class BudgetManager:
    """
    Simple budget tracking that works as a wrapper around Aider.
    Tracks spending and provides warnings without blocking functionality.
    """
    
    def __init__(self, daily_limit: Optional[float] = None, 
                 data_dir: Optional[Path] = None):
        """
        Initialize budget manager.
        
        Args:
            daily_limit: Daily spending limit in USD (None for no limit)
            data_dir: Directory to store usage data (defaults to ~/.atlas-code)
        """
        self.daily_limit = daily_limit
        if isinstance(data_dir, str):
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = data_dir or Path.home() / ".atlas-code"
        self.data_dir.mkdir(exist_ok=True)
        
        self.usage_file = self.data_dir / "usage.jsonl"
        self.config_file = self.data_dir / "budget_config.json"
        
        self._load_config()
    
    def _load_config(self):
        """Load budget configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.daily_limit = config.get('daily_limit', self.daily_limit)
                    logger.info(f"Loaded budget config: daily_limit=${self.daily_limit}")
            except Exception as e:
                logger.warning(f"Failed to load budget config: {e}")
    
    def save_config(self):
        """Save current budget configuration."""
        config = {
            'daily_limit': self.daily_limit,
            'updated': datetime.now().isoformat()
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Budget config saved")
        except Exception as e:
            logger.error(f"Failed to save budget config: {e}")
    
    def record_usage(self, model: str, tokens_sent: int, tokens_received: int, 
                    cost: float, task_type: str = "coding"):
        """
        Record API usage for budget tracking.
        
        Args:
            model: Model name used
            tokens_sent: Number of tokens sent
            tokens_received: Number of tokens received  
            cost: Cost in USD
            task_type: Type of task (for analysis)
        """
        record = UsageRecord(
            timestamp=datetime.now().isoformat(),
            model=model,
            tokens_sent=tokens_sent,
            tokens_received=tokens_received,
            cost=cost,
            task_type=task_type
        )
        
        try:
            with open(self.usage_file, 'a') as f:
                f.write(json.dumps(asdict(record)) + '\n')
            logger.info(f"Recorded usage: ${cost:.4f} for {model}")
        except Exception as e:
            logger.error(f"Failed to record usage: {e}")
    
    def get_daily_usage(self, target_date: Optional[date] = None) -> List[UsageRecord]:
        """
        Get usage records for a specific date.
        
        Args:
            target_date: Date to get usage for (defaults to today)
            
        Returns:
            List of usage records for the date
        """
        if target_date is None:
            target_date = date.today()
        
        target_str = target_date.isoformat()
        records = []
        
        if not self.usage_file.exists():
            return records
        
        try:
            with open(self.usage_file, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        record = UsageRecord(**data)
                        record_date = datetime.fromisoformat(record.timestamp).date()
                        
                        if record_date == target_date:
                            records.append(record)
                    except Exception as e:
                        logger.warning(f"Failed to parse usage record: {e}")
        except Exception as e:
            logger.error(f"Failed to read usage file: {e}")
        
        return records
    
    def get_daily_total(self, target_date: Optional[date] = None) -> float:
        """Get total spending for a specific date."""
        records = self.get_daily_usage(target_date)
        return sum(record.cost for record in records)
    
    def check_budget_status(self) -> Dict:
        """
        Check current budget status and return summary.
        
        Returns:
            Dictionary with budget status information
        """
        today_total = self.get_daily_total()
        
        status = {
            'daily_limit': self.daily_limit,
            'today_spent': today_total,
            'remaining': None,
            'percentage_used': None,
            'warning_level': 'green'  # green, yellow, red
        }
        
        if self.daily_limit is not None:
            status['remaining'] = max(0, self.daily_limit - today_total)
            status['percentage_used'] = min(100, (today_total / self.daily_limit) * 100)
            
            # Set warning levels
            if status['percentage_used'] >= 90:
                status['warning_level'] = 'red'
            elif status['percentage_used'] >= 70:
                status['warning_level'] = 'yellow'
        
        return status
    
    def should_warn_user(self) -> bool:
        """Check if user should be warned about budget usage."""
        status = self.check_budget_status()
        return status['warning_level'] in ['yellow', 'red']
    
    def estimate_cost(self, model: str, estimated_tokens: int) -> float:
        """
        Estimate cost for a model and token count.
        
        Args:
            model: Model name
            estimated_tokens: Estimated total tokens (input + output)
            
        Returns:
            Estimated cost in USD
        """
        # Import here to avoid circular imports
        from .router import ModelRouter
        
        router = ModelRouter()
        if model in router.MODELS:
            cost_per_1k = router.MODELS[model].cost_per_1k_tokens
            return (estimated_tokens / 1000) * cost_per_1k
        
        # Default estimation for unknown models
        logger.warning(f"Unknown model {model}, using default cost estimation")
        return (estimated_tokens / 1000) * 1.0  # $1 per 1K tokens default
    
    def get_usage_summary(self, days: int = 7) -> Dict:
        """
        Get usage summary for the past N days.
        
        Args:
            days: Number of days to include in summary
            
        Returns:
            Dictionary with usage statistics
        """
        today = date.today()
        total_cost = 0
        total_tokens = 0
        model_usage = {}
        
        for i in range(days):
            day = today - timedelta(days=i)
            day_records = self.get_daily_usage(day)
            
            for record in day_records:
                total_cost += record.cost
                total_tokens += record.tokens_sent + record.tokens_received
                
                if record.model not in model_usage:
                    model_usage[record.model] = {'count': 0, 'cost': 0, 'tokens': 0}
                
                model_usage[record.model]['count'] += 1
                model_usage[record.model]['cost'] += record.cost
                model_usage[record.model]['tokens'] += record.tokens_sent + record.tokens_received
        
        return {
            'period_days': days,
            'total_cost': total_cost,
            'total_tokens': total_tokens,
            'average_daily_cost': total_cost / days,
            'model_breakdown': model_usage,
            'daily_limit': self.daily_limit
        }
    
    def set_daily_limit(self, limit: float):
        """Set or update daily spending limit."""
        self.daily_limit = limit
        self.save_config()
        logger.info(f"Daily budget limit set to ${limit}")
    
    def disable_budget(self):
        """Disable budget tracking."""
        self.daily_limit = None
        self.save_config()
        logger.info("Budget tracking disabled")


# Helper function for date calculations
from datetime import timedelta