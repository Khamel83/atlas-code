"""
Smart Model Router for Atlas Code V2

Implements the 4-tier model system with intelligent routing based on:
- Task complexity and type
- User budget and preferences  
- Project context from Agent OS
- Historical performance
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """4-tier model classification system"""
    SILVER = "silver"    # Budget tier
    GOLD = "gold"        # Balanced tier  
    PLATINUM = "platinum"  # Premium tier
    DIAMOND = "diamond"   # Flagship tier


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    name: str
    tier: ModelTier
    cost_per_1k_tokens: float
    description: str
    best_for: List[str]


class ModelRouter:
    """
    Intelligent model routing system that selects the optimal model
    based on task analysis and user preferences.
    """
    
    # OpenRouter model configurations for the 4-tier system
    MODELS = {
        # Silver Tier - Budget
        "openrouter/deepseek/deepseek-r1:free": ModelConfig(
            name="openrouter/deepseek/deepseek-r1:free",
            tier=ModelTier.SILVER,
            cost_per_1k_tokens=0.0,
            description="Free DeepSeek R1 (rate limited)",
            best_for=["learning", "simple tasks", "experimentation"]
        ),
        "openrouter/anthropic/claude-3-haiku": ModelConfig(
            name="openrouter/anthropic/claude-3-haiku",
            tier=ModelTier.SILVER,
            cost_per_1k_tokens=0.25,
            description="Fast and economical Claude model",
            best_for=["quick fixes", "simple coding", "documentation"]
        ),
        "openrouter/openai/gpt-4o-mini": ModelConfig(
            name="openrouter/openai/gpt-4o-mini",
            tier=ModelTier.SILVER,
            cost_per_1k_tokens=0.15,
            description="OpenAI's most affordable model",
            best_for=["basic tasks", "code review", "simple debugging"]
        ),
        
        # Gold Tier - Balanced
        "openrouter/deepseek/deepseek-chat": ModelConfig(
            name="openrouter/deepseek/deepseek-chat",
            tier=ModelTier.GOLD,
            cost_per_1k_tokens=0.14,
            description="Excellent value DeepSeek model",
            best_for=["general coding", "refactoring", "feature development"]
        ),
        "openrouter/meta-llama/llama-3.1-70b-instruct": ModelConfig(
            name="openrouter/meta-llama/llama-3.1-70b-instruct",
            tier=ModelTier.GOLD,
            cost_per_1k_tokens=0.59,
            description="Strong performance Llama model",
            best_for=["complex logic", "algorithm development", "optimization"]
        ),
        
        # Platinum Tier - Premium
        "openrouter/anthropic/claude-3.5-sonnet": ModelConfig(
            name="openrouter/anthropic/claude-3.5-sonnet",
            tier=ModelTier.PLATINUM,
            cost_per_1k_tokens=3.0,
            description="Best coding performance Claude",
            best_for=["complex coding", "architecture", "critical features"]
        ),
        "openrouter/openai/gpt-4o": ModelConfig(
            name="openrouter/openai/gpt-4o",
            tier=ModelTier.PLATINUM,
            cost_per_1k_tokens=2.50,
            description="Strong overall performance GPT-4",
            best_for=["analysis", "complex problem solving", "integration"]
        ),
        
        # Diamond Tier - Flagship
        "openrouter/anthropic/claude-3.7-sonnet": ModelConfig(
            name="openrouter/anthropic/claude-3.7-sonnet",
            tier=ModelTier.DIAMOND,
            cost_per_1k_tokens=15.0,
            description="Latest flagship Claude model",
            best_for=["architectural planning", "complex systems", "research"]
        ),
        "openrouter/deepseek/deepseek-r1": ModelConfig(
            name="openrouter/deepseek/deepseek-r1",
            tier=ModelTier.DIAMOND,
            cost_per_1k_tokens=2.19,
            description="Advanced reasoning DeepSeek model",
            best_for=["deep analysis", "mathematical problems", "research"]
        ),
    }
    
    # Task classification patterns
    TASK_PATTERNS = {
        ModelTier.DIAMOND: [
            r'\b(architect|architecture|design|system|framework|infrastructure)\b',
            r'\b(complex|advanced|sophisticated|enterprise)\b',
            r'\b(research|analyze|investigation|deep)\b',
            r'\b(refactor\s+entire|complete\s+rewrite|major\s+changes)\b'
        ],
        ModelTier.PLATINUM: [
            r'\b(implement|build|create|develop)\b.*\b(feature|module|component)\b',
            r'\b(optimize|performance|efficiency|algorithm)\b',
            r'\b(integration|api|database|security)\b',
            r'\b(test|testing|unittest|pytest)\b'
        ],
        ModelTier.GOLD: [
            r'\b(refactor|improve|enhance|update)\b',
            r'\b(fix|debug|troubleshoot|resolve)\b',
            r'\b(add|modify|change|adjust)\b',
            r'\b(function|method|class|variable)\b'
        ],
        ModelTier.SILVER: [
            r'\b(fix.*typo|typo|spelling|syntax\s+error)\b',
            r'\b(comment|document|explain|clarify)\b',
            r'\b(simple|basic|quick|small)\b.*\b(script|function|example)\b',
            r'\b(hello\s+world|print|echo)\b',
            r'\b(help|question|what\s+is|how\s+to|why)\b'
        ]
    }
    
    def __init__(self, default_tier: ModelTier = ModelTier.GOLD, 
                 budget_limit: Optional[float] = None):
        """
        Initialize the model router.
        
        Args:
            default_tier: Default tier to use when task analysis is unclear
            budget_limit: Daily budget limit in USD (None for no limit)
        """
        self.default_tier = default_tier
        self.budget_limit = budget_limit
        self.usage_history = []
        
    def analyze_task(self, prompt: str, context: Optional[Dict] = None) -> ModelTier:
        """
        Analyze a task prompt to determine the appropriate model tier.
        
        Args:
            prompt: The user's task description
            context: Additional context from Agent OS or project settings
            
        Returns:
            Recommended ModelTier for the task
        """
        prompt_lower = prompt.lower()
        
        # Check for explicit tier requests
        if any(word in prompt_lower for word in ['diamond', 'flagship', 'best', 'premium']):
            return ModelTier.DIAMOND
        if any(word in prompt_lower for word in ['platinum', 'complex', 'important']):
            return ModelTier.PLATINUM
        if any(word in prompt_lower for word in ['gold', 'balanced', 'normal']):
            return ModelTier.GOLD
        if any(word in prompt_lower for word in ['silver', 'cheap', 'budget', 'simple']):
            return ModelTier.SILVER
            
        # Pattern-based classification - check SILVER first for specific simple tasks
        # Check SILVER tier first (most specific patterns)
        silver_patterns = self.TASK_PATTERNS.get(ModelTier.SILVER, [])
        for pattern in silver_patterns:
            if re.search(pattern, prompt_lower):
                logger.info(f"Task classified as SILVER based on pattern: {pattern}")
                return ModelTier.SILVER
        
        # Then check higher tiers in order
        for tier in [ModelTier.DIAMOND, ModelTier.PLATINUM, ModelTier.GOLD]:
            patterns = self.TASK_PATTERNS.get(tier, [])
            for pattern in patterns:
                if re.search(pattern, prompt_lower):
                    logger.info(f"Task classified as {tier.value} based on pattern: {pattern}")
                    return tier
        
        # Context-based classification
        if context:
            # Check if this is a new project (might need architectural work)
            if context.get('is_new_project', False):
                return ModelTier.PLATINUM
                
            # Check file count - large projects might need better models
            file_count = context.get('file_count', 0)
            if file_count > 50:
                return ModelTier.PLATINUM
            elif file_count > 10:
                return ModelTier.GOLD
                
        logger.info(f"Using default tier: {self.default_tier.value}")
        return self.default_tier
    
    def get_models_for_tier(self, tier: ModelTier) -> List[ModelConfig]:
        """Get all models available for a specific tier."""
        return [model for model in self.MODELS.values() if model.tier == tier]
    
    def select_model(self, tier: ModelTier, prefer_free: bool = False) -> str:
        """
        Select the best model for a given tier.
        
        Args:
            tier: The desired model tier
            prefer_free: Whether to prefer free models when available
            
        Returns:
            Model name string for use with Aider
        """
        tier_models = self.get_models_for_tier(tier)
        
        if not tier_models:
            logger.warning(f"No models found for tier {tier.value}, falling back to Gold")
            tier_models = self.get_models_for_tier(ModelTier.GOLD)
        
        # Prefer free models if requested
        if prefer_free:
            free_models = [m for m in tier_models if m.cost_per_1k_tokens == 0.0]
            if free_models:
                selected = free_models[0]
                logger.info(f"Selected free model: {selected.name}")
                return selected.name
        
        # Select the first (primary) model for the tier
        selected = tier_models[0]
        logger.info(f"Selected {tier.value} tier model: {selected.name}")
        return selected.name
    
    def route_request(self, prompt: str, context: Optional[Dict] = None, 
                     force_tier: Optional[ModelTier] = None,
                     prefer_free: bool = False) -> Tuple[str, ModelTier, float]:
        """
        Main routing function that analyzes the request and returns the optimal model.
        
        Args:
            prompt: User's task description
            context: Additional context information
            force_tier: Override automatic tier selection
            prefer_free: Prefer free models when available
            
        Returns:
            Tuple of (model_name, selected_tier, estimated_cost_per_1k_tokens)
        """
        # Determine tier
        if force_tier:
            tier = force_tier
            logger.info(f"Using forced tier: {tier.value}")
        else:
            tier = self.analyze_task(prompt, context)
        
        # Select model
        model_name = self.select_model(tier, prefer_free)
        model_config = self.MODELS[model_name]
        
        # Log the decision
        logger.info(f"Routed request to {model_name} ({tier.value} tier)")
        logger.info(f"Reason: {model_config.description}")
        
        return model_name, tier, model_config.cost_per_1k_tokens
    
    def get_tier_info(self, tier: ModelTier) -> Dict:
        """Get information about a specific tier."""
        models = self.get_models_for_tier(tier)
        return {
            'tier': tier.value,
            'models': [{'name': m.name, 'cost': m.cost_per_1k_tokens, 'description': m.description} 
                      for m in models],
            'best_for': models[0].best_for if models else []
        }
    
    def list_all_tiers(self) -> Dict:
        """Get information about all tiers."""
        return {
            tier.value: self.get_tier_info(tier) 
            for tier in ModelTier
        }