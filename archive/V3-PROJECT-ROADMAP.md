# Atlas Code V3: Universal LLM Router Project

## 🎯 **Project Vision**

Transform Atlas Code from an "Aider wrapper" into a **universal intelligent LLM router** that can layer on top of any code editing agent (Aider, Cursor, Continue.dev, OpenDevin, custom CLI tools).

## 📋 **Complete Implementation Guide for Any LLM**

This document provides a step-by-step roadmap that any capable LLM (Claude, GPT-4, Gemini, etc.) can follow to implement Atlas Code V3 from the current V2 codebase.

---

## 🏗️ **PHASE 1: Core Router Extraction**

### **Goal**: Decouple intelligent routing from Aider-specific execution

### **Current Problem**: 
- `atlas_core/launcher.py` contains Aider-specific command construction
- Routing logic is mixed with execution logic
- Cannot easily swap out Aider for other editors

### **Implementation Steps**:

#### Step 1.1: Create Universal Router Class
**File**: `atlas_core/universal_router.py`

```python
"""
Universal LLM Router - Editor Agnostic
Handles task classification, model selection, and budget management
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import logging

@dataclass
class RoutingDecision:
    """Complete routing decision with all context"""
    model: str
    tier: str
    estimated_cost: float
    enhanced_prompt: str
    reasoning: str
    confidence: float
    fallback_available: bool
    budget_impact: Dict[str, float]

class AtlasRouter:
    """Universal intelligent router - works with any code editor"""
    
    def __init__(self):
        self.classifier_model = "meta-llama/llama-3.3-70b-instruct"
        self.fallback_classifier = "google/gemini-1.5-flash"
        self.pattern_classifier = PatternClassifier()
        self.budget_optimizer = BudgetOptimizer()
        self.telemetry = RoutingTelemetry()
    
    def route_task(self, prompt: str, context: Dict) -> RoutingDecision:
        """Main routing function - completely editor agnostic"""
        try:
            # AI-powered classification with confidence scoring
            tier, confidence = self.classify_with_confidence(prompt)
            
            # Budget-aware model selection
            model = self.budget_optimizer.select_affordable_model(
                tier, context.get('budget_remaining', float('inf'))
            )
            
            # Enhance prompt with Agent OS standards
            enhanced_prompt = self.enhance_prompt(prompt, context)
            
            # Cost estimation
            estimated_cost = self.estimate_task_cost(model, enhanced_prompt)
            
            decision = RoutingDecision(
                model=model,
                tier=tier,
                estimated_cost=estimated_cost,
                enhanced_prompt=enhanced_prompt,
                reasoning=f"AI classified as {tier} (confidence: {confidence:.2f})",
                confidence=confidence,
                fallback_available=self.escalate_tier(tier) is not None,
                budget_impact=self.calculate_budget_impact(estimated_cost, context)
            )
            
            # Log decision for analytics
            self.telemetry.log_decision(prompt, decision)
            
            return decision
            
        except Exception as e:
            # Graceful fallback to pattern-based classification
            return self.fallback_route(prompt, context, error=e)
    
    def fallback_route(self, prompt: str, context: Dict, error: Exception) -> RoutingDecision:
        """Pattern-based fallback when AI classification fails"""
        logging.warning(f"AI classification failed: {error}, using pattern fallback")
        
        tier = self.pattern_classifier.classify(prompt)
        model = self.budget_optimizer.select_affordable_model(
            tier, context.get('budget_remaining', float('inf'))
        )
        
        return RoutingDecision(
            model=model,
            tier=tier,
            estimated_cost=self.estimate_task_cost(model, prompt),
            enhanced_prompt=prompt,
            reasoning=f"Pattern-based fallback (AI unavailable)",
            confidence=0.6,  # Lower confidence for pattern matching
            fallback_available=True,
            budget_impact={}
        )
```

#### Step 1.2: Create Pattern-Based Fallback System
**File**: `atlas_core/pattern_classifier.py`

```python
"""
Pattern-based task classification fallback
Used when AI classification unavailable
"""

import re
from typing import Dict, List

class PatternClassifier:
    """Regex-based task classification for offline/fallback use"""
    
    TIER_PATTERNS = {
        'silver': [
            r'\b(fix|correct|typo|spelling|syntax)\b',
            r'\b(hello\s+world|print|echo|simple\s+script)\b',
            r'\b(comment|document|explain|clarify)\b',
            r'\b(quick|small|minor|trivial)\b'
        ],
        'gold': [
            r'\b(implement|create|build|develop)\b.*\b(function|method|feature)\b',
            r'\b(debug|troubleshoot|fix\s+bug)\b',
            r'\b(refactor|improve|enhance|update)\b',
            r'\b(add|modify|change|adjust)\b.*\b(code|logic)\b'
        ],
        'platinum': [
            r'\b(optimize|performance|efficiency|algorithm)\b',
            r'\b(complex|advanced|sophisticated)\b.*\b(implementation|solution)\b',
            r'\b(integration|api|database|security)\b.*\b(system|service)\b',
            r'\b(multi-file|cross-module|large-scale)\b'
        ],
        'diamond': [
            r'\b(architect|architecture|design\s+system)\b',
            r'\b(distributed|microservices|scalable)\b',
            r'\b(research|analyze|investigation|novel)\b',
            r'\b(enterprise|production|high-stakes)\b'
        ]
    }
    
    def classify(self, prompt: str) -> str:
        """Classify prompt using regex patterns"""
        prompt_lower = prompt.lower()
        
        # Check patterns in order (diamond -> silver)
        for tier in ['diamond', 'platinum', 'gold', 'silver']:
            patterns = self.TIER_PATTERNS[tier]
            for pattern in patterns:
                if re.search(pattern, prompt_lower):
                    return tier
        
        return 'gold'  # Safe default
    
    def get_classification_reason(self, prompt: str, tier: str) -> str:
        """Explain why pattern classifier chose this tier"""
        prompt_lower = prompt.lower()
        patterns = self.TIER_PATTERNS.get(tier, [])
        
        for pattern in patterns:
            if re.search(pattern, prompt_lower):
                return f"Matched pattern: {pattern}"
        
        return "Default tier (no specific patterns matched)"
```

#### Step 1.3: Create Budget Optimizer
**File**: `atlas_core/budget_optimizer.py`

```python
"""
Budget-aware model selection and optimization
"""

from typing import Dict, List, Optional
import logging

class BudgetOptimizer:
    """Handles budget constraints and model cost optimization"""
    
    def __init__(self):
        # Load from model_score.json
        self.model_mappings = self.load_model_mappings()
        self.model_costs = self.load_model_costs()
    
    def select_affordable_model(self, tier: str, budget_remaining: float) -> str:
        """Select cheapest available model within tier and budget"""
        tier_models = self.model_mappings.get(tier, [])
        
        # Filter models that fit within budget
        affordable_models = []
        avg_tokens = 2000  # Conservative estimate
        
        for model in tier_models:
            estimated_cost = self.estimate_cost(model, avg_tokens)
            if estimated_cost <= budget_remaining:
                affordable_models.append((model, estimated_cost))
        
        if affordable_models:
            # Return cheapest model
            return min(affordable_models, key=lambda x: x[1])[0]
        
        # Budget constraint - try lower tiers
        return self.downgrade_for_budget(tier, budget_remaining)
    
    def downgrade_for_budget(self, original_tier: str, budget_remaining: float) -> str:
        """Downgrade to lower tier when budget insufficient"""
        tier_hierarchy = ['diamond', 'platinum', 'gold', 'silver']
        
        try:
            current_index = tier_hierarchy.index(original_tier)
        except ValueError:
            current_index = 2  # Default to gold
        
        # Try each lower tier
        for i in range(current_index + 1, len(tier_hierarchy)):
            lower_tier = tier_hierarchy[i]
            try:
                model = self.select_affordable_model(lower_tier, budget_remaining)
                logging.warning(f"Budget constraint: downgraded {original_tier} → {lower_tier}")
                return model
            except BudgetExhaustedException:
                continue
        
        # Last resort: find any free model
        free_models = [m for m, cost in self.model_costs.items() if cost == 0]
        if free_models:
            logging.warning("Using free model due to budget exhaustion")
            return free_models[0]
        
        raise BudgetExhaustedException(
            f"No models available within budget ${budget_remaining:.2f}"
        )
    
    def estimate_cost(self, model: str, estimated_tokens: int) -> float:
        """Estimate cost for model and token count"""
        cost_per_1k = self.model_costs.get(model, 1.0)
        return (estimated_tokens / 1000) * cost_per_1k
    
    def calculate_budget_impact(self, estimated_cost: float, context: Dict) -> Dict[str, float]:
        """Calculate budget impact analysis"""
        daily_limit = context.get('daily_limit')
        spent_today = context.get('spent_today', 0)
        
        if daily_limit:
            remaining_after = daily_limit - spent_today - estimated_cost
            percentage_used = ((spent_today + estimated_cost) / daily_limit) * 100
            
            return {
                'remaining_after': remaining_after,
                'percentage_used': percentage_used,
                'daily_limit': daily_limit,
                'estimated_cost': estimated_cost
            }
        
        return {'estimated_cost': estimated_cost}

class BudgetExhaustedException(Exception):
    """Raised when no models available within budget"""
    pass
```

---

## 🔌 **PHASE 2: Executor Abstraction**

### **Goal**: Create pluggable architecture for different code editors

#### Step 2.1: Define Executor Interface
**File**: `atlas_core/executors/base.py`

```python
"""
Abstract base class for code editor executors
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import time

@dataclass
class ExecutionResult:
    """Result of code editor execution"""
    exit_code: int
    output: str
    error_output: str
    tokens_used: Optional[int]
    actual_cost: Optional[float]
    duration: float
    success: bool
    
    @property
    def failed(self) -> bool:
        return not self.success

class CodeExecutor(ABC):
    """Abstract base class for all code editor integrations"""
    
    @abstractmethod
    def check_installation(self) -> bool:
        """Verify the editor is installed and accessible"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Get editor version for logging and compatibility"""
        pass
    
    @abstractmethod
    def execute(self, 
                decision: 'RoutingDecision', 
                files: List[str] = None,
                project_root: str = None,
                extra_args: List[str] = None) -> ExecutionResult:
        """Execute a coding task using this editor"""
        pass
    
    @abstractmethod
    def supports_model(self, model: str) -> bool:
        """Check if editor supports the specified model"""
        pass
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return editor capabilities for optimization"""
        return {
            'supports_streaming': False,
            'supports_multifile': True,
            'supports_context_files': True,
            'max_prompt_length': 100000,
            'supports_model_switching': True
        }
    
    def prepare_prompt(self, decision: 'RoutingDecision') -> str:
        """Editor-specific prompt preparation"""
        return decision.enhanced_prompt
    
    def log_execution(self, decision: 'RoutingDecision', result: ExecutionResult):
        """Log execution details for analytics"""
        logging.info(f"Executed {decision.model} via {self.__class__.__name__}: "
                    f"exit_code={result.exit_code}, duration={result.duration:.2f}s")
```

#### Step 2.2: Implement Aider Executor
**File**: `atlas_core/executors/aider.py`

```python
"""
Aider-specific executor implementation
"""

import subprocess
import logging
import time
from typing import List, Optional
from .base import CodeExecutor, ExecutionResult
from ..universal_router import RoutingDecision

class AiderExecutor(CodeExecutor):
    """Executor for Aider-based code editing"""
    
    def __init__(self):
        self.name = "aider"
        self.command = "aider"
    
    def check_installation(self) -> bool:
        """Verify Aider is installed and accessible"""
        try:
            result = subprocess.run(
                [self.command, '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_version(self) -> str:
        """Get Aider version"""
        try:
            result = subprocess.run(
                [self.command, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "unknown"
    
    def supports_model(self, model: str) -> bool:
        """Check if Aider supports this model"""
        # Aider supports most OpenRouter models
        return 'openrouter/' in model or model.startswith(('gpt-', 'claude-', 'gemini-'))
    
    def execute(self, 
                decision: RoutingDecision,
                files: List[str] = None,
                project_root: str = None,
                extra_args: List[str] = None) -> ExecutionResult:
        """Execute task using Aider"""
        
        start_time = time.time()
        
        # Build Aider command
        cmd = [
            self.command,
            '--model', decision.model,
            '--message', self.prepare_prompt(decision)
        ]
        
        # Add files if specified
        if files:
            cmd.extend(files)
        
        # Add extra arguments
        if extra_args:
            cmd.extend(extra_args)
        
        try:
            # Execute Aider
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            duration = time.time() - start_time
            
            execution_result = ExecutionResult(
                exit_code=result.returncode,
                output=result.stdout,
                error_output=result.stderr,
                tokens_used=None,  # Aider doesn't report this
                actual_cost=None,  # Would need to calculate from API usage
                duration=duration,
                success=result.returncode == 0
            )
            
            self.log_execution(decision, execution_result)
            return execution_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return ExecutionResult(
                exit_code=124,  # Timeout exit code
                output="",
                error_output="Execution timed out after 10 minutes",
                tokens_used=None,
                actual_cost=None,
                duration=duration,
                success=False
            )
        
        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                exit_code=1,
                output="",
                error_output=f"Execution failed: {str(e)}",
                tokens_used=None,
                actual_cost=None,
                duration=duration,
                success=False
            )
    
    def prepare_prompt(self, decision: RoutingDecision) -> str:
        """Aider-specific prompt preparation"""
        # Aider works best with direct, actionable prompts
        return decision.enhanced_prompt
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Aider-specific capabilities"""
        return {
            'supports_streaming': False,
            'supports_multifile': True,
            'supports_context_files': True,
            'max_prompt_length': 200000,  # Aider handles long prompts well
            'supports_model_switching': True,
            'supports_git_integration': True,
            'supports_diff_output': True
        }
```

#### Step 2.3: Create Executor Factory
**File**: `atlas_core/executor_factory.py`

```python
"""
Factory for creating code editor executors
"""

from typing import Dict, Type, Optional
import logging
from .executors.base import CodeExecutor
from .executors.aider import AiderExecutor

class ExecutorFactory:
    """Factory for creating and managing code editor executors"""
    
    EXECUTORS: Dict[str, Type[CodeExecutor]] = {
        'aider': AiderExecutor,
        # Future executors:
        # 'cursor': CursorExecutor,
        # 'continue': ContinueExecutor,
        # 'opendevin': OpenDevinExecutor,
        # 'shell': ShellExecutor
    }
    
    @classmethod
    def create_executor(cls, name: str) -> CodeExecutor:
        """Create executor by name"""
        executor_class = cls.EXECUTORS.get(name)
        if not executor_class:
            available = list(cls.EXECUTORS.keys())
            raise ValueError(f"Unknown executor '{name}'. Available: {available}")
        
        executor = executor_class()
        
        # Verify executor is usable
        if not executor.check_installation():
            raise RuntimeError(f"Executor '{name}' not installed or not accessible")
        
        return executor
    
    @classmethod
    def detect_available_executor(cls) -> Optional[str]:
        """Auto-detect first available executor"""
        for name, executor_class in cls.EXECUTORS.items():
            try:
                executor = executor_class()
                if executor.check_installation():
                    logging.info(f"Auto-detected executor: {name}")
                    return name
            except Exception as e:
                logging.debug(f"Executor {name} not available: {e}")
        
        return None
    
    @classmethod
    def list_available_executors(cls) -> Dict[str, Dict]:
        """List all available executors with status"""
        result = {}
        
        for name, executor_class in cls.EXECUTORS.items():
            try:
                executor = executor_class()
                available = executor.check_installation()
                version = executor.get_version() if available else "not installed"
                capabilities = executor.get_capabilities() if available else {}
                
                result[name] = {
                    'available': available,
                    'version': version,
                    'capabilities': capabilities
                }
            except Exception as e:
                result[name] = {
                    'available': False,
                    'error': str(e),
                    'version': "unknown",
                    'capabilities': {}
                }
        
        return result
```

---

## 🎭 **PHASE 3: Universal Orchestrator**

### **Goal**: Coordinate router + executor + budget tracking

#### Step 3.1: Create Universal Orchestrator
**File**: `atlas_core/orchestrator.py`

```python
"""
Universal Atlas Code Orchestrator
Coordinates routing, execution, and budget management
"""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from .universal_router import AtlasRouter, RoutingDecision
from .executor_factory import ExecutorFactory
from .budget import BudgetManager
from .executors.base import ExecutionResult

class AtlasOrchestrator:
    """Universal orchestrator for Atlas Code V3"""
    
    def __init__(self, 
                 executor_name: Optional[str] = None,
                 project_root: Optional[Path] = None):
        """
        Initialize orchestrator with specific executor or auto-detect
        
        Args:
            executor_name: Name of executor to use ('aider', 'cursor', etc.)
            project_root: Project root directory
        """
        self.project_root = project_root or Path.cwd()
        
        # Initialize core components
        self.router = AtlasRouter()
        self.budget = BudgetManager()
        
        # Initialize executor
        if executor_name:
            self.executor = ExecutorFactory.create_executor(executor_name)
            self.executor_name = executor_name
        else:
            # Auto-detect available executor
            detected = ExecutorFactory.detect_available_executor()
            if not detected:
                raise RuntimeError("No compatible code editor found. Please install Aider or another supported editor.")
            
            self.executor = ExecutorFactory.create_executor(detected)
            self.executor_name = detected
        
        logging.info(f"Atlas Orchestrator initialized with {self.executor_name} executor")
    
    def execute_task(self, 
                     prompt: str,
                     files: Optional[List[str]] = None,
                     force_tier: Optional[str] = None,
                     budget_check: bool = True,
                     extra_args: Optional[List[str]] = None) -> ExecutionResult:
        """
        Execute a coding task with intelligent routing
        
        Args:
            prompt: Task description
            files: Files to include in editing session
            force_tier: Override tier selection
            budget_check: Whether to enforce budget limits
            extra_args: Additional arguments for executor
            
        Returns:
            ExecutionResult with details of execution
        """
        
        # Prepare context for router
        budget_status = self.budget.check_budget_status()
        context = {
            'budget_remaining': budget_status.get('remaining', float('inf')),
            'daily_limit': budget_status.get('daily_limit'),
            'spent_today': budget_status.get('today_spent', 0),
            'file_count': len(files) if files else 0,
            'project_root': str(self.project_root),
            'executor_capabilities': self.executor.get_capabilities()
        }
        
        # Get routing decision
        if force_tier:
            # User override - skip AI classification
            decision = self._create_forced_decision(prompt, force_tier, context)
        else:
            # Intelligent routing
            decision = self.router.route_task(prompt, context)
        
        # Budget check
        if budget_check and not self._check_budget_allowance(decision):
            # Try to downgrade for budget
            try:
                decision = self._downgrade_for_budget(decision, context)
            except Exception as e:
                return ExecutionResult(
                    exit_code=1,
                    output="",
                    error_output=f"Budget constraint: {str(e)}",
                    tokens_used=None,
                    actual_cost=None,
                    duration=0,
                    success=False
                )
        
        # Verify executor supports the selected model
        if not self.executor.supports_model(decision.model):
            logging.warning(f"Executor {self.executor_name} may not support model {decision.model}")
        
        # Execute the task
        try:
            result = self.executor.execute(
                decision=decision,
                files=files,
                project_root=str(self.project_root),
                extra_args=extra_args
            )
            
            # Record usage for budget tracking
            if result.success:
                self.budget.record_usage(
                    model=decision.model,
                    tokens_sent=result.tokens_used or self._estimate_tokens(decision.enhanced_prompt),
                    tokens_received=result.tokens_used or 1000,  # Conservative estimate
                    cost=result.actual_cost or decision.estimated_cost,
                    task_type=decision.tier
                )
            
            # Log successful execution
            self._log_execution_summary(decision, result)
            
            return result
            
        except Exception as e:
            logging.error(f"Task execution failed: {str(e)}")
            return ExecutionResult(
                exit_code=1,
                output="",
                error_output=f"Execution error: {str(e)}",
                tokens_used=None,
                actual_cost=None,
                duration=0,
                success=False
            )
    
    def dry_run(self, prompt: str, **kwargs) -> RoutingDecision:
        """Show routing decision without execution"""
        context = self._build_context(**kwargs)
        return self.router.route_task(prompt, context)
    
    def explain_decision(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Detailed explanation of routing decision"""
        decision = self.dry_run(prompt, **kwargs)
        
        return {
            'task': prompt,
            'classification': {
                'tier': decision.tier,
                'confidence': decision.confidence,
                'reasoning': decision.reasoning
            },
            'model_selection': {
                'model': decision.model,
                'estimated_cost': decision.estimated_cost,
                'alternatives': self._get_tier_alternatives(decision.tier)
            },
            'budget_impact': decision.budget_impact,
            'executor_info': {
                'name': self.executor_name,
                'version': self.executor.get_version(),
                'supports_model': self.executor.supports_model(decision.model)
            },
            'escalation': {
                'available': decision.fallback_available,
                'next_tier': self.router.escalate_tier(decision.tier) if decision.fallback_available else None
            }
        }
    
    def list_capabilities(self) -> Dict[str, Any]:
        """List system capabilities and status"""
        return {
            'router': {
                'classification_models': [
                    self.router.classifier_model,
                    self.router.fallback_classifier
                ],
                'supported_tiers': list(self.router.model_mappings.keys()),
                'pattern_fallback': True
            },
            'executor': {
                'name': self.executor_name,
                'version': self.executor.get_version(),
                'capabilities': self.executor.get_capabilities()
            },
            'budget': {
                'tracking_enabled': True,
                'status': self.budget.check_budget_status()
            },
            'available_executors': ExecutorFactory.list_available_executors()
        }
    
    def _build_context(self, **kwargs) -> Dict[str, Any]:
        """Build context dictionary for router"""
        budget_status = self.budget.check_budget_status()
        return {
            'budget_remaining': budget_status.get('remaining', float('inf')),
            'daily_limit': budget_status.get('daily_limit'),
            'spent_today': budget_status.get('today_spent', 0),
            'file_count': len(kwargs.get('files', [])),
            'project_root': str(self.project_root),
            **kwargs
        }
    
    def _check_budget_allowance(self, decision: RoutingDecision) -> bool:
        """Check if decision fits within budget"""
        budget_status = self.budget.check_budget_status()
        remaining = budget_status.get('remaining')
        
        if remaining is None:  # No budget limit
            return True
        
        return decision.estimated_cost <= remaining
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation for logging"""
        return len(text.split()) * 1.3
    
    def _log_execution_summary(self, decision: RoutingDecision, result: ExecutionResult):
        """Log execution summary for analytics"""
        logging.info(f"Atlas execution complete: "
                    f"tier={decision.tier}, "
                    f"model={decision.model}, "
                    f"cost=${decision.estimated_cost:.4f}, "
                    f"success={result.success}, "
                    f"duration={result.duration:.2f}s")
```

---

## 🖥️ **PHASE 4: Enhanced CLI**

### **Goal**: User-friendly command-line interface with rich features

#### Step 4.1: Enhanced Main CLI
**File**: `atlas-code-v3`

```python
#!/usr/bin/env python3
"""
Atlas Code V3 - Universal LLM Router
Main executable with intelligent routing for any code editor
"""

import sys
import argparse
import logging
import json
from pathlib import Path

# Add atlas_core to path
sys.path.insert(0, str(Path(__file__).parent))

from atlas_core.orchestrator import AtlasOrchestrator
from atlas_core.executor_factory import ExecutorFactory
from atlas_core.exceptions import AtlasException, BudgetExhaustedException

def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity"""
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

def create_parser():
    """Create comprehensive argument parser"""
    parser = argparse.ArgumentParser(
        description="Atlas Code V3 - Universal LLM Router with intelligent task classification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  atlas-code-v3 "fix typo in main.py"
  atlas-code-v3 "implement user auth" --tier gold --executor cursor
  atlas-code-v3 "optimize database" --dry-run --explain
  atlas-code-v3 --list-executors
  atlas-code-v3 --system-status

Supported Executors:
  aider      - Aider-based code editing (default)
  cursor     - Cursor editor integration (planned)
  continue   - Continue.dev integration (planned)
  opendevin  - OpenDevin agent integration (planned)
        """
    )
    
    # Task specification
    parser.add_argument(
        "task",
        nargs="?",
        help="Description of the coding task to perform"
    )
    
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to include in the editing session"
    )
    
    # Executor selection
    parser.add_argument(
        "--executor",
        choices=list(ExecutorFactory.EXECUTORS.keys()),
        help="Code editor to use for execution (auto-detected if not specified)"
    )
    
    # Routing control
    parser.add_argument(
        "--tier",
        choices=["silver", "gold", "platinum", "diamond"],
        help="Force specific model tier (overrides AI classification)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show routing decision without executing task"
    )
    
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Provide detailed explanation of routing decision"
    )
    
    # Budget management
    parser.add_argument(
        "--set-budget",
        type=float,
        metavar="AMOUNT",
        help="Set daily budget limit in USD"
    )
    
    parser.add_argument(
        "--budget-status",
        action="store_true",
        help="Show current budget status and usage"
    )
    
    parser.add_argument(
        "--no-budget-check",
        action="store_true",
        help="Skip budget validation for this request"
    )
    
    # System information
    parser.add_argument(
        "--list-executors",
        action="store_true",
        help="List available code editor executors"
    )
    
    parser.add_argument(
        "--system-status",
        action="store_true",
        help="Show complete system status and capabilities"
    )
    
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show Atlas Code version"
    )
    
    # Advanced options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--config-file",
        type=Path,
        help="Custom configuration file path"
    )
    
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Output format for machine-readable results"
    )
    
    return parser

def print_system_status(orchestrator: AtlasOrchestrator, output_format: str = "text"):
    """Display comprehensive system status"""
    capabilities = orchestrator.list_capabilities()
    
    if output_format == "json":
        print(json.dumps(capabilities, indent=2))
        return
    
    print("🎛️  Atlas Code V3 System Status")
    print("=" * 40)
    
    # Router status
    print(f"\n🧠 Router:")
    print(f"   Primary classifier: {capabilities['router']['classification_models'][0]}")
    print(f"   Fallback classifier: {capabilities['router']['classification_models'][1]}")
    print(f"   Supported tiers: {', '.join(capabilities['router']['supported_tiers'])}")
    print(f"   Pattern fallback: {'✅' if capabilities['router']['pattern_fallback'] else '❌'}")
    
    # Executor status
    print(f"\n🔧 Current Executor:")
    print(f"   Name: {capabilities['executor']['name']}")
    print(f"   Version: {capabilities['executor']['version']}")
    exec_caps = capabilities['executor']['capabilities']
    print(f"   Multi-file support: {'✅' if exec_caps.get('supports_multifile') else '❌'}")
    print(f"   Max prompt length: {exec_caps.get('max_prompt_length', 'unknown'):,} chars")
    
    # Budget status
    budget = capabilities['budget']['status']
    print(f"\n💰 Budget:")
    if budget.get('daily_limit'):
        print(f"   Daily limit: ${budget['daily_limit']}")
        print(f"   Spent today: ${budget['today_spent']:.2f}")
        print(f"   Remaining: ${budget.get('remaining', 0):.2f}")
        print(f"   Status: {budget['warning_level']}")
    else:
        print(f"   No daily limit set")
        print(f"   Spent today: ${budget['today_spent']:.2f}")
    
    # Available executors
    print(f"\n🎯 Available Executors:")
    for name, info in capabilities['available_executors'].items():
        status = "✅" if info['available'] else "❌"
        version = info.get('version', 'unknown')
        print(f"   {status} {name}: {version}")

def print_executor_list(output_format: str = "text"):
    """Display available executors"""
    executors = ExecutorFactory.list_available_executors()
    
    if output_format == "json":
        print(json.dumps(executors, indent=2))
        return
    
    print("🎯 Available Code Editor Executors")
    print("=" * 40)
    
    for name, info in executors.items():
        status = "✅ Available" if info['available'] else "❌ Not Available"
        print(f"\n{name.upper()}:")
        print(f"   Status: {status}")
        print(f"   Version: {info.get('version', 'unknown')}")
        
        if not info['available'] and 'error' in info:
            print(f"   Error: {info['error']}")
        
        if info['available'] and 'capabilities' in info:
            caps = info['capabilities']
            print(f"   Capabilities:")
            print(f"     Multi-file: {'✅' if caps.get('supports_multifile') else '❌'}")
            print(f"     Streaming: {'✅' if caps.get('supports_streaming') else '❌'}")
            print(f"     Max prompt: {caps.get('max_prompt_length', 'unknown'):,} chars")

def handle_dry_run(orchestrator: AtlasOrchestrator, args):
    """Handle dry run mode"""
    try:
        decision = orchestrator.dry_run(
            prompt=args.task,
            files=args.files,
            force_tier=args.tier
        )
        
        if args.output_format == "json":
            print(json.dumps({
                'tier': decision.tier,
                'model': decision.model,
                'estimated_cost': decision.estimated_cost,
                'reasoning': decision.reasoning,
                'confidence': decision.confidence
            }, indent=2))
        else:
            print("🧪 Dry Run - Routing Decision")
            print("=" * 30)
            print(f"🎯 Task: {args.task}")
            print(f"🧠 Classification: {decision.tier} tier (confidence: {decision.confidence:.2f})")
            print(f"🤖 Selected model: {decision.model}")
            print(f"💰 Estimated cost: ${decision.estimated_cost:.4f}")
            print(f"💡 Reasoning: {decision.reasoning}")
            
            if decision.fallback_available:
                next_tier = orchestrator.router.escalate_tier(decision.tier)
                print(f"⬆️  Escalation available: {next_tier} tier")
        
        return 0
        
    except Exception as e:
        print(f"❌ Dry run failed: {str(e)}")
        return 1

def handle_explain_mode(orchestrator: AtlasOrchestrator, args):
    """Handle explain mode"""
    try:
        explanation = orchestrator.explain_decision(
            prompt=args.task,
            files=args.files,
            force_tier=args.tier
        )
        
        if args.output_format == "json":
            print(json.dumps(explanation, indent=2))
        else:
            print("🔍 Detailed Routing Explanation")
            print("=" * 35)
            
            # Task analysis
            print(f"\n📝 Task Analysis:")
            print(f"   Input: {explanation['task']}")
            
            # Classification details
            classification = explanation['classification']
            print(f"\n🧠 AI Classification:")
            print(f"   Tier: {classification['tier']}")
            print(f"   Confidence: {classification['confidence']:.2f}")
            print(f"   Reasoning: {classification['reasoning']}")
            
            # Model selection
            selection = explanation['model_selection']
            print(f"\n🤖 Model Selection:")
            print(f"   Selected: {selection['model']}")
            print(f"   Estimated cost: ${selection['estimated_cost']:.4f}")
            print(f"   Alternatives in tier: {', '.join(selection.get('alternatives', []))}")
            
            # Budget impact
            if explanation['budget_impact']:
                budget = explanation['budget_impact']
                print(f"\n💰 Budget Impact:")
                if 'daily_limit' in budget:
                    print(f"   Daily limit: ${budget['daily_limit']}")
                    print(f"   After this task: ${budget.get('remaining_after', 0):.2f} remaining")
                    print(f"   Usage: {budget.get('percentage_used', 0):.1f}%")
            
            # Executor info
            executor = explanation['executor_info']
            print(f"\n🔧 Executor:")
            print(f"   Name: {executor['name']}")
            print(f"   Version: {executor['version']}")
            print(f"   Model support: {'✅' if executor['supports_model'] else '❌'}")
            
            # Escalation options
            escalation = explanation['escalation']
            if escalation['available']:
                print(f"\n⬆️  Escalation:")
                print(f"   Next tier: {escalation['next_tier']}")
                print(f"   Available if low confidence detected")
        
        return 0
        
    except Exception as e:
        print(f"❌ Explanation failed: {str(e)}")
        return 1

def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    try:
        # Handle version request
        if args.version:
            print("Atlas Code V3.0.0-alpha")
            return 0
        
        # Handle system information requests
        if args.list_executors:
            print_executor_list(args.output_format)
            return 0
        
        # Initialize orchestrator
        try:
            orchestrator = AtlasOrchestrator(
                executor_name=args.executor,
                project_root=Path.cwd()
            )
        except Exception as e:
            print("❌ Failed to initialize Ralex: {str(e)}")
            print("💡 Try: atlas-code-v3 --list-executors to see available options")
            return 1
        
        # Handle system status
        if args.system_status:
            print_system_status(orchestrator, args.output_format)
            return 0
        
        # Handle budget management
        if args.set_budget is not None:
            orchestrator.budget.set_daily_limit(args.set_budget)
            print(f"✅ Daily budget set to ${args.set_budget}")
            return 0
        
        if args.budget_status:
            status = orchestrator.budget.check_budget_status()
            if args.output_format == "json":
                print(json.dumps(status, indent=2))
            else:
                print("💰 Budget Status")
                print("=" * 20)
                if status.get('daily_limit'):
                    print(f"Daily limit: ${status['daily_limit']}")
                    print(f"Spent today: ${status['today_spent']:.2f}")
                    print(f"Remaining: ${status.get('remaining', 0):.2f}")
                    print(f"Warning level: {status['warning_level']}")
                else:
                    print("No daily limit set")
                    print(f"Spent today: ${status['today_spent']:.2f}")
            return 0
        
        # Validate task is provided for execution modes
        if not args.task:
            print("❌ No task provided!")
            print("Usage: atlas-code-v3 'your task description'")
            print("Try: atlas-code-v3 --help for more options")
            return 1
        
        # Handle special modes
        if args.dry_run:
            return handle_dry_run(orchestrator, args)
        
        if args.explain:
            return handle_explain_mode(orchestrator, args)
        
        # Execute the task
        print(f"🚀 Atlas Code V3 - Executing Task")
        print(f"🎯 Task: {args.task}")
        if args.executor:
            print(f"🔧 Executor: {args.executor}")
        if args.tier:
            print(f"🎚️  Forced tier: {args.tier}")
        print()
        
        result = orchestrator.execute_task(
            prompt=args.task,
            files=args.files,
            force_tier=args.tier,
            budget_check=not args.no_budget_check
        )
        
        # Display results
        if result.success:
            print(f"\n✅ Task completed successfully!")
            if args.verbose and result.output:
                print(f"Output:\n{result.output}")
        else:
            print(f"\n❌ Task failed (exit code: {result.exit_code})")
            if result.error_output:
                print(f"Error: {result.error_output}")
        
        return result.exit_code
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        return 130
    
    except BudgetExhaustedException as e:
        print(f"💸 Budget constraint: {str(e)}")
        print("💡 Try: --set-budget AMOUNT to increase limit")
        return 1
    
    except AtlasException as e:
        print(f"❌ Atlas error: {str(e)}")
        if e.recovery_action:
            print(f"💡 Try: {e.recovery_action}")
        return 1
    
    except Exception as e:
        if args.verbose:
            import traceback
            traceback.print_exc()
        else:
            print(f"❌ Unexpected error: {str(e)}")
            print("💡 Try: --verbose for detailed error information")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## 🧪 **PHASE 5: Comprehensive Testing Framework**

### **Goal**: Test all functionality without burning API tokens

#### Step 5.1: Mock Testing Infrastructure
**File**: `tests/mock_framework.py`

```python
"""
Mock testing framework for Atlas Code V3
Tests routing logic without API calls or token usage
"""

import json
import random
from typing import Dict, List, Tuple, Optional
from unittest.mock import Mock, patch
from dataclasses import dataclass

from atlas_core.universal_router import AtlasRouter, RoutingDecision
from atlas_core.orchestrator import AtlasOrchestrator
from atlas_core.executors.base import ExecutionResult

@dataclass
class MockTestCase:
    """Test case for mock framework"""
    prompt: str
    expected_tier: str
    expected_model_contains: str
    budget_limit: Optional[float] = None
    should_escalate: bool = False
    description: str = ""

class MockAtlasRouter(AtlasRouter):
    """Mock router that simulates AI classification without API calls"""
    
    # Predefined classification patterns for testing
    MOCK_CLASSIFICATIONS = {
        # Silver tier patterns
        'typo': ('silver', 0.95),
        'fix simple': ('silver', 0.90),
        'hello world': ('silver', 0.92),
        'print statement': ('silver', 0.88),
        
        # Gold tier patterns  
        'implement': ('gold', 0.85),
        'create function': ('gold', 0.80),
        'debug': ('gold', 0.82),
        'add feature': ('gold', 0.78),
        
        # Platinum tier patterns
        'optimize': ('platinum', 0.88),
        'refactor': ('platinum', 0.85),
        'algorithm': ('platinum', 0.90),
        'performance': ('platinum', 0.87),
        
        # Diamond tier patterns
        'architecture': ('diamond', 0.93),
        'design system': ('diamond', 0.95),
        'microservices': ('diamond', 0.92),
        'research': ('diamond', 0.89)
    }
    
    def __init__(self):
        super().__init__()
        self.call_count = 0
        self.classification_history = []
    
    def classify_with_confidence(self, prompt: str) -> Tuple[str, float]:
        """Mock classification without API calls"""
        self.call_count += 1
        prompt_lower = prompt.lower()
        
        # Find best matching pattern
        best_match = ('gold', 0.7)  # Default
        
        for pattern, (tier, confidence) in self.MOCK_CLASSIFICATIONS.items():
            if pattern in prompt_lower:
                if confidence > best_match[1]:
                    best_match = (tier, confidence)
        
        # Add some randomness to simulate real AI variation
        confidence_variation = random.uniform(-0.05, 0.05)
        final_confidence = max(0.5, min(0.99, best_match[1] + confidence_variation))
        
        result = (best_match[0], final_confidence)
        self.classification_history.append({
            'prompt': prompt,
            'result': result,
            'call_count': self.call_count
        })
        
        return result
    
    def _call_openrouter(self, model: str, messages: List[Dict], max_tokens: int = 150) -> str:
        """Mock OpenRouter API call"""
        # Never actually called in mock mode, but included for completeness
        prompt = messages[-1]['content'].lower()
        
        for pattern, (tier, _) in self.MOCK_CLASSIFICATIONS.items():
            if pattern in prompt:
                return tier
        
        return 'gold'

class MockExecutor:
    """Mock executor that simulates code editor execution"""
    
    def __init__(self, name: str = "mock"):
        self.name = name
        self.execution_count = 0
        self.execution_history = []
    
    def check_installation(self) -> bool:
        return True
    
    def get_version(self) -> str:
        return "mock-1.0.0"
    
    def supports_model(self, model: str) -> bool:
        return True
    
    def execute(self, decision: RoutingDecision, files: List[str] = None, **kwargs) -> ExecutionResult:
        """Mock execution that always succeeds"""
        self.execution_count += 1
        
        # Simulate execution time based on tier
        tier_durations = {
            'silver': random.uniform(1, 3),
            'gold': random.uniform(3, 8),
            'platinum': random.uniform(8, 15),
            'diamond': random.uniform(15, 30)
        }
        
        duration = tier_durations.get(decision.tier, 5.0)
        
        result = ExecutionResult(
            exit_code=0,
            output=f"Mock execution completed for {decision.tier} tier task",
            error_output="",
            tokens_used=random.randint(1000, 5000),
            actual_cost=decision.estimated_cost * random.uniform(0.8, 1.2),
            duration=duration,
            success=True
        )
        
        self.execution_history.append({
            'decision': decision,
            'result': result,
            'files': files,
            'execution_count': self.execution_count
        })
        
        return result
    
    def get_capabilities(self) -> Dict:
        return {
            'supports_streaming': False,
            'supports_multifile': True,
            'supports_context_files': True,
            'max_prompt_length': 100000,
            'supports_model_switching': True,
            'is_mock': True
        }

class MockTestSuite:
    """Comprehensive test suite using mock framework"""
    
    def __init__(self):
        self.router = MockAtlasRouter()
        self.executor = MockExecutor()
        self.test_cases = self._generate_test_cases()
        self.results = []
    
    def _generate_test_cases(self) -> List[MockTestCase]:
        """Generate comprehensive test cases"""
        return [
            # Silver tier tests
            MockTestCase(
                "fix typo in README",
                "silver",
                "gemini-2.0-flash",
                description="Simple typo fix"
            ),
            MockTestCase(
                "create hello world script",
                "silver", 
                "gemini-2.0-flash",
                description="Basic script creation"
            ),
            
            # Gold tier tests
            MockTestCase(
                "implement user authentication",
                "gold",
                "deepseek",
                description="Standard feature implementation"
            ),
            MockTestCase(
                "debug memory leak in server",
                "gold",
                "deepseek",
                description="Debugging task"
            ),
            
            # Platinum tier tests
            MockTestCase(
                "optimize database queries for performance",
                "platinum",
                "gpt-4",
                description="Performance optimization"
            ),
            MockTestCase(
                "refactor entire authentication system",
                "platinum",
                "gpt-4",
                description="Large refactoring task"
            ),
            
            # Diamond tier tests
            MockTestCase(
                "design microservices architecture",
                "diamond",
                "claude-3-sonnet",
                description="System architecture design"
            ),
            MockTestCase(
                "research novel AI algorithms for optimization",
                "diamond",
                "claude-3-sonnet",
                description="Research task"
            ),
            
            # Budget constraint tests
            MockTestCase(
                "complex optimization task",
                "silver",  # Should downgrade from platinum
                "gemini",
                budget_limit=0.10,
                description="Budget-constrained task"
            )
        ]
    
    def run_classification_tests(self) -> Dict[str, float]:
        """Test classification accuracy"""
        correct = 0
        total = len(self.test_cases)
        
        for test_case in self.test_cases:
            decision = self.router.route_task(
                test_case.prompt,
                {'budget_remaining': test_case.budget_limit or 10.0}
            )
            
            # Check tier classification
            tier_correct = decision.tier == test_case.expected_tier
            
            # Check model selection
            model_correct = test_case.expected_model_contains.lower() in decision.model.lower()
            
            if tier_correct:
                correct += 1
            
            self.results.append({
                'test_case': test_case,
                'decision': decision,
                'tier_correct': tier_correct,
                'model_correct': model_correct,
                'passed': tier_correct and model_correct
            })
        
        accuracy = correct / total
        return {
            'accuracy': accuracy,
            'correct': correct,
            'total': total,
            'results': self.results
        }
    
    def run_budget_constraint_tests(self) -> Dict[str, Any]:
        """Test budget-aware downgrading"""
        budget_tests = [
            (0.01, "Very low budget - should use free models"),
            (0.50, "Low budget - should prefer cheap models"),
            (2.00, "Medium budget - should allow gold tier"),
            (10.0, "High budget - should allow all tiers")
        ]
        
        results = []
        
        for budget, description in budget_tests:
            decision = self.router.route_task(
                "implement complex feature",
                {'budget_remaining': budget}
            )
            
            model_cost = self.router.budget_optimizer.model_costs.get(decision.model, 0)
            
            results.append({
                'budget': budget,
                'description': description,
                'selected_tier': decision.tier,
                'selected_model': decision.model,
                'model_cost': model_cost,
                'estimated_cost': decision.estimated_cost,
                'within_budget': decision.estimated_cost <= budget
            })
        
        return {
            'test_count': len(budget_tests),
            'results': results,
            'all_within_budget': all(r['within_budget'] for r in results)
        }
    
    def run_escalation_tests(self) -> Dict[str, Any]:
        """Test escalation and fallback logic"""
        escalation_tests = [
            ("silver", "gold"),
            ("gold", "platinum"),
            ("platinum", "diamond"),
            ("diamond", None)
        ]
        
        results = []
        
        for current_tier, expected_next in escalation_tests:
            next_tier = self.router.escalate_tier(current_tier)
            
            results.append({
                'current_tier': current_tier,
                'expected_next': expected_next,
                'actual_next': next_tier,
                'correct': next_tier == expected_next
            })
        
        # Test low confidence detection
        low_confidence_phrases = [
            ("I'm not sure about this", True),
            ("This is definitely correct", False),
            ("<ESCALATE> Need better model", True),
            ("Maybe we should try a different approach", True),
            ("This solution is optimal", False)
        ]
        
        confidence_results = []
        for phrase, expected_low in low_confidence_phrases:
            detected = self.router.is_low_confidence(phrase)
            confidence_results.append({
                'phrase': phrase,
                'expected_low': expected_low,
                'detected_low': detected,
                'correct': detected == expected_low
            })
        
        return {
            'escalation_tests': results,
            'confidence_tests': confidence_results,
            'escalation_accuracy': sum(1 for r in results if r['correct']) / len(results),
            'confidence_accuracy': sum(1 for r in confidence_results if r['correct']) / len(confidence_results)
        }
    
    def run_full_test_suite(self) -> Dict[str, Any]:
        """Run complete test suite"""
        print("🧪 Running Atlas Code V3 Mock Test Suite")
        print("=" * 45)
        
        # Classification tests
        print("\n1. 🎯 Testing Task Classification...")
        classification_results = self.run_classification_tests()
        print(f"   Accuracy: {classification_results['accuracy']:.1%} "
              f"({classification_results['correct']}/{classification_results['total']})")
        
        # Budget tests
        print("\n2. 💰 Testing Budget Constraints...")
        budget_results = self.run_budget_constraint_tests()
        within_budget_count = sum(1 for r in budget_results['results'] if r['within_budget'])
        print(f"   Budget compliance: {within_budget_count}/{budget_results['test_count']} tests")
        
        # Escalation tests
        print("\n3. ⬆️  Testing Escalation Logic...")
        escalation_results = self.run_escalation_tests()
        print(f"   Escalation accuracy: {escalation_results['escalation_accuracy']:.1%}")
        print(f"   Confidence detection: {escalation_results['confidence_accuracy']:.1%}")
        
        # Performance summary
        total_calls = self.router.call_count
        total_executions = self.executor.execution_count
        print(f"\n📊 Performance Summary:")
        print(f"   Classification calls: {total_calls}")
        print(f"   Mock executions: {total_executions}")
        print(f"   Average confidence: {sum(r['decision'].confidence for r in self.results) / len(self.results):.2f}")
        
        # Overall assessment
        overall_score = (
            classification_results['accuracy'] * 0.4 +
            (within_budget_count / budget_results['test_count']) * 0.3 +
            escalation_results['escalation_accuracy'] * 0.2 +
            escalation_results['confidence_accuracy'] * 0.1
        )
        
        print(f"\n🎯 Overall Test Score: {overall_score:.1%}")
        
        if overall_score >= 0.85:
            print("✅ System ready for production!")
        elif overall_score >= 0.70:
            print("⚠️  System functional but needs improvement")
        else:
            print("❌ System needs significant work before production")
        
        return {
            'classification': classification_results,
            'budget': budget_results,
            'escalation': escalation_results,
            'performance': {
                'total_calls': total_calls,
                'total_executions': total_executions,
                'average_confidence': sum(r['decision'].confidence for r in self.results) / len(self.results)
            },
            'overall_score': overall_score,
            'production_ready': overall_score >= 0.85
        }

# Usage example
if __name__ == "__main__":
    test_suite = MockTestSuite()
    results = test_suite.run_full_test_suite()
```

---

## 📋 **PHASE 6: Implementation Checklist**

### **For Any LLM Following This Guide**:

#### **Step-by-Step Implementation Order**:

1. **Phase 1: Router Extraction** (1-2 days)
   - [ ] Create `atlas_core/universal_router.py` with `AtlasRouter` class
   - [ ] Create `atlas_core/pattern_classifier.py` for fallback classification
   - [ ] Create `atlas_core/budget_optimizer.py` for cost management
   - [ ] Update existing `atlas_core/launcher.py` to use new router
   - [ ] Test basic routing without API calls

2. **Phase 2: Executor Abstraction** (1 day)
   - [ ] Create `atlas_core/executors/base.py` with abstract interface
   - [ ] Create `atlas_core/executors/aider.py` implementation
   - [ ] Create `atlas_core/executor_factory.py` for dynamic loading
   - [ ] Test executor factory and Aider integration

3. **Phase 3: Universal Orchestrator** (1 day)
   - [ ] Create `atlas_core/orchestrator.py` to coordinate all components
   - [ ] Implement dry-run and explain modes
   - [ ] Add comprehensive error handling
   - [ ] Test full orchestration workflow

4. **Phase 4: Enhanced CLI** (1 day)
   - [ ] Create new `atlas-code-v3` executable
   - [ ] Implement all CLI features (dry-run, explain, system-status)
   - [ ] Add help text and error messages
   - [ ] Test all CLI options

5. **Phase 5: Testing Framework** (1 day)
   - [ ] Create `tests/mock_framework.py` for token-free testing
   - [ ] Implement comprehensive test suite
   - [ ] Create validation scripts
   - [ ] Run full test suite and validate results

6. **Phase 6: Documentation & Deployment** (0.5 days)
   - [ ] Update all documentation
   - [ ] Create migration guide from V2
   - [ ] Test installation process
   - [ ] Validate MVP readiness

### **Testing Without API Costs**:

```bash
# Set up mock testing environment
export ATLAS_MOCK_MODE=true

# Run comprehensive mock tests
python -m tests.mock_framework

# Test CLI with mock executor
./atlas-code-v3 "implement auth" --executor mock --dry-run

# Validate system status
./atlas-code-v3 --system-status

# Test all features without API calls
./validate-v3-mvp.sh --mock-mode
```

### **Production Readiness Validation**:

```bash
# Final validation script
#!/bin/bash
echo "🧪 Atlas Code V3 MVP Validation"

# 1. Mock tests (free)
python -m tests.mock_framework || exit 1

# 2. System status
./atlas-code-v3 --system-status || exit 1

# 3. All CLI modes
./atlas-code-v3 "hello world" --dry-run || exit 1
./atlas-code-v3 "hello world" --explain || exit 1

# 4. Budget management
./atlas-code-v3 --set-budget 1.00
./atlas-code-v3 --budget-status || exit 1

# 5. Executor listing
./atlas-code-v3 --list-executors || exit 1

echo "✅ Atlas Code V3 MVP validation complete!"
```

This complete roadmap provides any LLM with step-by-step instructions to implement Atlas Code V3 as a universal, editor-agnostic intelligent routing system while maintaining full backward compatibility and providing comprehensive testing capabilities.