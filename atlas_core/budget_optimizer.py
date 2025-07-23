"""
Budget Optimizer for Atlas Code V5

Advanced budget management with real-time cost tracking, automatic model selection,
and intelligent downgrade/upgrade decisions based on spending patterns.
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time

logger = logging.getLogger(__name__)

@dataclass
class UsageEntry:
    """Single usage entry for tracking."""
    timestamp: datetime
    model: str
    tier: str
    intent: str
    tokens_input: int
    tokens_output: int
    cost_input: float
    cost_output: float
    total_cost: float
    success: bool
    response_time: float = 0.0

@dataclass
class BudgetAlert:
    """Budget alert information."""
    alert_type: str  # "warning", "critical", "exceeded"
    threshold: float
    current_spending: float
    percentage: float
    message: str
    timestamp: datetime

@dataclass
class ModelSelection:
    """Result of model selection."""
    model: str
    tier: str
    reasoning: str
    estimated_cost: float
    confidence: float
    fallback_used: bool = False

class BudgetOptimizer:
    """
    Advanced budget management system with real-time cost control,
    intelligent model selection, and automatic scaling.
    """
    
    def __init__(self, config_dir: str):
        """Initialize budget optimizer with configuration."""
        self.config_dir = config_dir
        
        # Load configuration
        self.model_tiers = self._load_model_tiers()
        self.intent_routes = self._load_intent_routes()
        self.settings = self._load_settings()
        
        # Initialize budget tracking
        self.usage_history: List[UsageEntry] = []
        self.session_start = datetime.now()
        self.budget_alerts: List[BudgetAlert] = []
        
        # Budget limits from config
        budget_limits = self.model_tiers.get('budget_limits', {})
        self.daily_budget = budget_limits.get('daily_budget', 10.0)
        self.session_budget = budget_limits.get('session_budget', 2.0)
        self.task_budget = budget_limits.get('task_budget', 0.5)
        self.warning_threshold = budget_limits.get('warning_threshold', 0.8)
        self.emergency_threshold = budget_limits.get('emergency_threshold', 0.95)
        
        # Current spending tracking
        self.daily_spending = 0.0
        self.session_spending = 0.0
        self.last_daily_reset = datetime.now().date()
        
        # Performance tracking
        self.model_performance: Dict[str, Dict[str, Any]] = {}
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Load existing usage data
        self._load_usage_history()
        
        logger.info(f"Budget optimizer initialized - Daily: ${self.daily_budget}, Session: ${self.session_budget}")
    
    def _load_model_tiers(self) -> Dict[str, Any]:
        """Load model tier configuration."""
        try:
            tiers_path = os.path.join(self.config_dir, 'model_tiers.json')
            with open(tiers_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load model tiers: {e}")
            return self._get_default_model_tiers()
    
    def _load_intent_routes(self) -> Dict[str, Any]:
        """Load intent routing configuration."""
        try:
            routes_path = os.path.join(self.config_dir, 'intent_routes.json')
            with open(routes_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load intent routes: {e}")
            return self._get_default_intent_routes()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load system settings."""
        try:
            settings_path = os.path.join(self.config_dir, 'settings.json')
            with open(settings_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return {}
    
    def _load_usage_history(self):
        """Load existing usage history from file."""
        try:
            data_dir = os.path.join(os.path.dirname(self.config_dir), 'data')
            usage_file = os.path.join(data_dir, 'usage_history.json')
            
            if os.path.exists(usage_file):
                with open(usage_file, 'r') as f:
                    data = json.load(f)
                    
                # Convert to UsageEntry objects
                for entry_data in data.get('entries', []):
                    entry = UsageEntry(
                        timestamp=datetime.fromisoformat(entry_data['timestamp']),
                        model=entry_data['model'],
                        tier=entry_data['tier'],
                        intent=entry_data['intent'],
                        tokens_input=entry_data['tokens_input'],
                        tokens_output=entry_data['tokens_output'],
                        cost_input=entry_data['cost_input'],
                        cost_output=entry_data['cost_output'],
                        total_cost=entry_data['total_cost'],
                        success=entry_data['success'],
                        response_time=entry_data.get('response_time', 0.0)
                    )
                    self.usage_history.append(entry)
                
                # Calculate current spending
                self._recalculate_spending()
                
                logger.info(f"Loaded {len(self.usage_history)} usage entries")
        
        except Exception as e:
            logger.warning(f"Failed to load usage history: {e}")
    
    def _save_usage_history(self):
        """Save usage history to file."""
        try:
            data_dir = os.path.join(os.path.dirname(self.config_dir), 'data')
            os.makedirs(data_dir, exist_ok=True)
            usage_file = os.path.join(data_dir, 'usage_history.json')
            
            # Convert to serializable format
            entries_data = []
            for entry in self.usage_history:
                entry_dict = asdict(entry)
                entry_dict['timestamp'] = entry.timestamp.isoformat()
                entries_data.append(entry_dict)
            
            data = {
                'entries': entries_data,
                'last_updated': datetime.now().isoformat(),
                'total_entries': len(entries_data)
            }
            
            with open(usage_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save usage history: {e}")
    
    def _recalculate_spending(self):
        """Recalculate current spending from usage history."""
        now = datetime.now()
        today = now.date()
        
        # Reset daily spending if new day
        if self.last_daily_reset != today:
            self.daily_spending = 0.0
            self.last_daily_reset = today
        
        # Calculate daily spending
        daily_total = 0.0
        session_total = 0.0
        
        for entry in self.usage_history:
            # Daily spending
            if entry.timestamp.date() == today:
                daily_total += entry.total_cost
            
            # Session spending
            if entry.timestamp >= self.session_start:
                session_total += entry.total_cost
        
        self.daily_spending = daily_total
        self.session_spending = session_total
    
    def select_model(
        self,
        intent: str,
        complexity: str = "medium",
        forced_tier: Optional[str] = None,
        estimated_tokens: Optional[int] = None
    ) -> ModelSelection:
        """
        Select optimal model based on budget, intent, and requirements.
        
        Args:
            intent: The classified intent (e.g., "code_generation")
            complexity: Task complexity ("low", "medium", "high")
            forced_tier: Force specific tier if provided
            estimated_tokens: Estimated token usage
            
        Returns:
            ModelSelection with chosen model and reasoning
        """
        
        with self._lock:
            # Check if we need to reset daily budget
            self._check_daily_reset()
            
            # Get default tier for intent
            intent_config = self.intent_routes.get('routing_rules', {}).get(intent, {})
            default_tier = intent_config.get('default_tier', 'standard')
            
            # Use forced tier if provided
            if forced_tier:
                if self._can_afford_tier(forced_tier, estimated_tokens):
                    model = self._select_model_from_tier(forced_tier, complexity)
                    return ModelSelection(
                        model=model['name'],
                        tier=forced_tier,
                        reasoning=f"User forced tier: {forced_tier}",
                        estimated_cost=self._estimate_cost(model, estimated_tokens),
                        confidence=1.0
                    )
                else:
                    logger.warning(f"Cannot afford forced tier {forced_tier}, falling back")
            
            # Check budget constraints
            budget_check = self._check_budget_constraints()
            
            if budget_check['status'] == 'exceeded':
                # Emergency fallback to cheapest model
                model = self._get_cheapest_model()
                return ModelSelection(
                    model=model['name'],
                    tier='budget',
                    reasoning="Budget exceeded, using emergency fallback",
                    estimated_cost=self._estimate_cost(model, estimated_tokens),
                    confidence=0.3,
                    fallback_used=True
                )
            
            elif budget_check['status'] == 'critical':
                # Force budget tier
                selected_tier = 'budget'
                reasoning = f"Critical budget warning ({budget_check['percentage']:.1%}), downgraded to budget tier"
            
            elif budget_check['status'] == 'warning':
                # Downgrade by one tier if possible
                tier_hierarchy = ['premium', 'standard', 'budget']
                try:
                    current_index = tier_hierarchy.index(default_tier)
                    selected_tier = tier_hierarchy[min(current_index + 1, len(tier_hierarchy) - 1)]
                    reasoning = f"Budget warning ({budget_check['percentage']:.1%}), downgraded from {default_tier} to {selected_tier}"
                except ValueError:
                    selected_tier = default_tier
                    reasoning = f"Budget warning, maintaining {default_tier} tier"
            
            else:
                # Normal operation - check for upgrade opportunities
                selected_tier = self._consider_tier_upgrade(default_tier, complexity, intent)
                if selected_tier != default_tier:
                    reasoning = f"Upgraded from {default_tier} to {selected_tier} based on {complexity} complexity"
                else:
                    reasoning = f"Standard tier selection: {selected_tier}"
            
            # Select best model from chosen tier
            model = self._select_model_from_tier(selected_tier, complexity)
            estimated_cost = self._estimate_cost(model, estimated_tokens)
            
            # Final affordability check
            if not self._can_afford_cost(estimated_cost):
                # Fallback to cheaper tier
                fallback_tier = self._get_affordable_tier(estimated_tokens)
                model = self._select_model_from_tier(fallback_tier, complexity)
                estimated_cost = self._estimate_cost(model, estimated_tokens)
                reasoning += f" (downgraded to {fallback_tier} for affordability)"
            
            return ModelSelection(
                model=model['name'],
                tier=selected_tier,
                reasoning=reasoning,
                estimated_cost=estimated_cost,
                confidence=0.8
            )
    
    def track_usage(
        self,
        model: str,
        tier: str,
        intent: str,
        tokens_input: int,
        tokens_output: int,
        cost: float,
        success: bool,
        response_time: float = 0.0
    ):
        """Track model usage and update budget."""
        
        with self._lock:
            # Get model cost breakdown
            model_info = self._get_model_info(model)
            cost_input = tokens_input * model_info.get('cost_input', 0.001)
            cost_output = tokens_output * model_info.get('cost_output', 0.001)
            
            # Create usage entry
            entry = UsageEntry(
                timestamp=datetime.now(),
                model=model,
                tier=tier,
                intent=intent,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost_input=cost_input,
                cost_output=cost_output,
                total_cost=cost,
                success=success,
                response_time=response_time
            )
            
            # Add to history
            self.usage_history.append(entry)
            
            # Update spending
            self.daily_spending += cost
            self.session_spending += cost
            
            # Update model performance tracking
            self._update_model_performance(model, entry)
            
            # Check for budget alerts
            self._check_budget_alerts()
            
            # Cleanup old entries (keep last 1000)
            if len(self.usage_history) > 1000:
                self.usage_history = self.usage_history[-1000:]
            
            # Save periodically
            if len(self.usage_history) % 10 == 0:
                self._save_usage_history()
            
            logger.debug(f"Tracked usage: {model} - ${cost:.4f} (Daily: ${self.daily_spending:.2f})")
    
    def _check_daily_reset(self):
        """Check if we need to reset daily budget."""
        today = datetime.now().date()
        if self.last_daily_reset != today:
            self.daily_spending = 0.0
            self.last_daily_reset = today
            logger.info("Daily budget reset")
    
    def _check_budget_constraints(self) -> Dict[str, Any]:
        """Check current budget status."""
        daily_percentage = self.daily_spending / self.daily_budget
        session_percentage = self.session_spending / self.session_budget
        
        # Use the higher percentage for decisions
        max_percentage = max(daily_percentage, session_percentage)
        
        if max_percentage >= 1.0:
            status = 'exceeded'
        elif max_percentage >= self.emergency_threshold:
            status = 'critical'
        elif max_percentage >= self.warning_threshold:
            status = 'warning'
        else:
            status = 'normal'
        
        return {
            'status': status,
            'percentage': max_percentage,
            'daily_spent': self.daily_spending,
            'session_spent': self.session_spending,
            'daily_budget': self.daily_budget,
            'session_budget': self.session_budget
        }
    
    def _can_afford_tier(self, tier: str, estimated_tokens: Optional[int] = None) -> bool:
        """Check if we can afford a specific tier."""
        tier_models = self.model_tiers.get('tiers', {}).get(tier, {}).get('models', [])
        if not tier_models:
            return False
        
        # Get cheapest model in tier
        cheapest_model = min(tier_models, key=lambda m: m.get('cost_input', 0) + m.get('cost_output', 0))
        estimated_cost = self._estimate_cost(cheapest_model, estimated_tokens)
        
        return self._can_afford_cost(estimated_cost)
    
    def _can_afford_cost(self, estimated_cost: float) -> bool:
        """Check if we can afford a specific cost."""
        daily_remaining = self.daily_budget - self.daily_spending
        session_remaining = self.session_budget - self.session_spending
        
        return estimated_cost <= min(daily_remaining, session_remaining) * 0.9  # 10% buffer
    
    def _get_affordable_tier(self, estimated_tokens: Optional[int] = None) -> str:
        """Get the most affordable tier we can use."""
        for tier in ['budget', 'standard', 'premium']:
            if self._can_afford_tier(tier, estimated_tokens):
                return tier
        return 'budget'  # Last resort
    
    def _consider_tier_upgrade(self, default_tier: str, complexity: str, intent: str) -> str:
        """Consider upgrading tier based on task complexity and budget availability."""
        
        # Don't upgrade if we're in warning territory
        budget_check = self._check_budget_constraints()
        if budget_check['percentage'] >= self.warning_threshold:
            return default_tier
        
        # Upgrade logic based on complexity
        tier_hierarchy = ['budget', 'standard', 'premium']
        
        try:
            current_index = tier_hierarchy.index(default_tier)
        except ValueError:
            return default_tier
        
        # High complexity tasks benefit from premium models
        if complexity == 'high' and current_index < 2:
            upgraded_tier = tier_hierarchy[current_index + 1]
            if self._can_afford_tier(upgraded_tier):
                return upgraded_tier
        
        # Check if we have plenty of budget remaining (< 30% used)
        if budget_check['percentage'] < 0.3 and current_index < 2:
            upgraded_tier = tier_hierarchy[current_index + 1]
            if self._can_afford_tier(upgraded_tier):
                return upgraded_tier
        
        return default_tier
    
    def _select_model_from_tier(self, tier: str, complexity: str) -> Dict[str, Any]:
        """Select best model from a specific tier."""
        tier_data = self.model_tiers.get('tiers', {}).get(tier, {})
        models = tier_data.get('models', [])
        
        if not models:
            # Fallback to budget tier
            budget_models = self.model_tiers.get('tiers', {}).get('budget', {}).get('models', [])
            return budget_models[0] if budget_models else self._get_default_model()
        
        # For high complexity, prefer models with better capabilities
        if complexity == 'high':
            # Look for models with "reasoning" or "analysis" strengths
            for model in models:
                strengths = model.get('strengths', [])
                if any(s in ['complex reasoning', 'analysis', 'reasoning'] for s in strengths):
                    return model
        
        # For code tasks, prefer models good at coding
        elif complexity == 'medium':
            for model in models:
                strengths = model.get('strengths', [])
                if 'code generation' in strengths or 'coding' in strengths:
                    return model
        
        # Default to first model in tier (usually the best)
        return models[0]
    
    def _get_cheapest_model(self) -> Dict[str, Any]:
        """Get the cheapest available model."""
        all_models = []
        for tier_data in self.model_tiers.get('tiers', {}).values():
            all_models.extend(tier_data.get('models', []))
        
        if not all_models:
            return self._get_default_model()
        
        # Sort by total cost (input + output)
        cheapest = min(all_models, key=lambda m: m.get('cost_input', 1) + m.get('cost_output', 1))
        return cheapest
    
    def _estimate_cost(self, model: Dict[str, Any], estimated_tokens: Optional[int] = None) -> float:
        """Estimate cost for a model and token count."""
        if not estimated_tokens:
            estimated_tokens = 500  # Default estimate
        
        # Assume 70% input, 30% output split
        input_tokens = int(estimated_tokens * 0.7)
        output_tokens = int(estimated_tokens * 0.3)
        
        cost_input = input_tokens * model.get('cost_input', 0.001)
        cost_output = output_tokens * model.get('cost_output', 0.001)
        
        return cost_input + cost_output
    
    def _get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get model information by name."""
        for tier_data in self.model_tiers.get('tiers', {}).values():
            for model in tier_data.get('models', []):
                if model.get('name') == model_name:
                    return model
        
        # Return default if not found
        return {'cost_input': 0.001, 'cost_output': 0.001}
    
    def _update_model_performance(self, model: str, entry: UsageEntry):
        """Update model performance tracking."""
        if model not in self.model_performance:
            self.model_performance[model] = {
                'total_requests': 0,
                'successful_requests': 0,
                'total_cost': 0.0,
                'total_tokens': 0,
                'avg_response_time': 0.0,
                'success_rate': 0.0
            }
        
        perf = self.model_performance[model]
        perf['total_requests'] += 1
        
        if entry.success:
            perf['successful_requests'] += 1
        
        perf['total_cost'] += entry.total_cost
        perf['total_tokens'] += entry.tokens_input + entry.tokens_output
        
        # Update averages
        perf['success_rate'] = perf['successful_requests'] / perf['total_requests']
        
        if entry.response_time > 0:
            current_avg = perf['avg_response_time']
            perf['avg_response_time'] = (current_avg * (perf['total_requests'] - 1) + entry.response_time) / perf['total_requests']
    
    def _check_budget_alerts(self):
        """Check for budget alerts and create notifications."""
        budget_check = self._check_budget_constraints()
        
        alert_type = None
        threshold = 0.0
        
        if budget_check['status'] == 'exceeded':
            alert_type = 'exceeded'
            threshold = 1.0
        elif budget_check['status'] == 'critical':
            alert_type = 'critical'
            threshold = self.emergency_threshold
        elif budget_check['status'] == 'warning':
            alert_type = 'warning'
            threshold = self.warning_threshold
        
        if alert_type:
            # Check if we already have a recent alert of this type
            recent_alerts = [a for a in self.budget_alerts 
                           if a.alert_type == alert_type and 
                           (datetime.now() - a.timestamp).seconds < 300]  # 5 minutes
            
            if not recent_alerts:
                alert = BudgetAlert(
                    alert_type=alert_type,
                    threshold=threshold,
                    current_spending=max(self.daily_spending, self.session_spending),
                    percentage=budget_check['percentage'],
                    message=f"Budget {alert_type}: {budget_check['percentage']:.1%} of limit used",
                    timestamp=datetime.now()
                )
                
                self.budget_alerts.append(alert)
                logger.warning(alert.message)
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get comprehensive budget status."""
        self._check_daily_reset()
        
        budget_check = self._check_budget_constraints()
        
        # Recent alerts
        recent_alerts = [a for a in self.budget_alerts 
                        if (datetime.now() - a.timestamp).total_seconds() < 3600]  # Last hour
        
        # Usage statistics
        total_requests = len(self.usage_history)
        successful_requests = sum(1 for e in self.usage_history if e.success)
        
        return {
            'daily_budget': self.daily_budget,
            'session_budget': self.session_budget,
            'daily_spent': self.daily_spending,
            'session_spent': self.session_spending,
            'daily_remaining': self.daily_budget - self.daily_spending,
            'session_remaining': self.session_budget - self.session_spending,
            'status': budget_check['status'],
            'percentage_used': budget_check['percentage'],
            'total_requests': total_requests,
            'success_rate': successful_requests / max(total_requests, 1),
            'recent_alerts': [asdict(a) for a in recent_alerts],
            'model_performance': self.model_performance,
            'session_duration': (datetime.now() - self.session_start).total_seconds() / 3600
        }
    
    def set_session_budget(self, budget: float):
        """Set session budget limit."""
        self.session_budget = budget
        logger.info(f"Session budget set to ${budget:.2f}")
    
    def get_cost_projection(self, intent: str, complexity: str = "medium") -> Dict[str, Any]:
        """Get cost projection for a task."""
        
        # Get recommended model
        model_selection = self.select_model(intent, complexity)
        
        # Historical cost analysis
        similar_entries = [e for e in self.usage_history 
                          if e.intent == intent and e.success]
        
        if similar_entries:
            avg_cost = sum(e.total_cost for e in similar_entries) / len(similar_entries)
            avg_tokens = sum(e.tokens_input + e.tokens_output for e in similar_entries) / len(similar_entries)
        else:
            avg_cost = model_selection.estimated_cost
            avg_tokens = 500
        
        return {
            'recommended_model': model_selection.model,
            'estimated_cost': model_selection.estimated_cost,
            'historical_avg_cost': avg_cost,
            'historical_avg_tokens': int(avg_tokens),
            'confidence': model_selection.confidence,
            'similar_requests': len(similar_entries)
        }
    
    # Default configurations
    def _get_default_model_tiers(self) -> Dict[str, Any]:
        """Default model tiers if config missing."""
        return {
            'tiers': {
                'budget': {
                    'models': [{'name': 'default-budget', 'cost_input': 0.0001, 'cost_output': 0.0001}]
                },
                'standard': {
                    'models': [{'name': 'default-standard', 'cost_input': 0.001, 'cost_output': 0.001}]
                },
                'premium': {
                    'models': [{'name': 'default-premium', 'cost_input': 0.003, 'cost_output': 0.015}]
                }
            },
            'budget_limits': {
                'daily_budget': 10.0,
                'session_budget': 2.0,
                'task_budget': 0.5,
                'warning_threshold': 0.8,
                'emergency_threshold': 0.95
            }
        }
    
    def _get_default_intent_routes(self) -> Dict[str, Any]:
        """Default intent routes if config missing."""
        return {
            'routing_rules': {
                'code_generation': {'default_tier': 'standard'},
                'debugging': {'default_tier': 'premium'},
                'general_query': {'default_tier': 'budget'}
            }
        }
    
    def _get_default_model(self) -> Dict[str, Any]:
        """Default model fallback."""
        return {
            'name': 'fallback-model',
            'cost_input': 0.001,
            'cost_output': 0.001,
            'strengths': ['general purpose']
        }

# Example usage
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test budget optimizer
    optimizer = BudgetOptimizer("../config")
    
    print("💰 Testing Budget Optimizer")
    print("=" * 40)
    
    # Test model selection
    test_cases = [
        ("code_generation", "high"),
        ("debugging", "medium"),
        ("general_query", "low")
    ]
    
    for intent, complexity in test_cases:
        selection = optimizer.select_model(intent, complexity)
        print(f"\nIntent: {intent} ({complexity})")
        print(f"Selected: {selection.model} ({selection.tier})")
        print(f"Estimated Cost: ${selection.estimated_cost:.4f}")
        print(f"Reasoning: {selection.reasoning}")
        
        # Simulate usage tracking
        optimizer.track_usage(
            model=selection.model,
            tier=selection.tier,
            intent=intent,
            tokens_input=300,
            tokens_output=200,
            cost=selection.estimated_cost,
            success=True,
            response_time=1.5
        )
    
    # Show budget status
    print("\n📊 Budget Status:")
    status = optimizer.get_budget_status()
    print(f"Daily: ${status['daily_spent']:.2f} / ${status['daily_budget']:.2f}")
    print(f"Session: ${status['session_spent']:.2f} / ${status['session_budget']:.2f}")
    print(f"Status: {status['status'].upper()}")
    print(f"Success Rate: {status['success_rate']:.1%}")