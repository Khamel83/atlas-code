"""
Intelligent Model Router for Atlas Code V2

Provides AI-powered task classification and cost-aware model selection
using OpenRouter's API for dynamic routing decisions.
"""

import json
import logging
import requests
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ModelInfo:
    """Information about a model's capabilities and cost"""
    name: str
    tier: str
    cost_per_1k_tokens: float
    available: bool = True

class IntelligentModelRouter:
    """
    AI-powered model router that classifies tasks and selects optimal models
    based on complexity, cost, and availability.
    """
    
    def __init__(self, model_score_file: str = "model_score.json"):
        """
        Initialize the router with model scoring data.
        
        Args:
            model_score_file: Path to JSON file containing tier-to-model mappings
        """
        self.model_score_file = Path(model_score_file)
        self.openrouter_base_url = "https://openrouter.ai/api/v1"
        self.classifier_model = "meta-llama/llama-3.3-70b-instruct"
        self.compression_model = "google/gemini-1.5-flash"
        self.fallback_classifier = "google/gemini-1.5-flash"
        
        # Load model mappings
        self.model_mappings = self._load_model_mappings()
        
        # Model cost data (approximate, should be updated from OpenRouter API)
        self.model_costs = {
            "google/gemini-2.0-flash-001": 0.075,
            "deepseek/deepseek-chat": 0.14,
            "moonshotai/kimi-k2": 0.1,
            "google/gemini-2.5-flash": 0.2,
            "openai/gpt-4.1": 10.0,
            "anthropic/claude-3-sonnet-20240229": 15.0,
            "meta-llama/llama-3.3-70b-instruct": 0.59,
            "google/gemini-1.5-flash": 0.075,
            "mistralai/mixtral-8x7b-instruct": 0.24
        }
    
    def _load_model_mappings(self) -> Dict[str, List[str]]:
        """Load tier-to-model mappings from JSON file."""
        try:
            with open(self.model_score_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Model score file {self.model_score_file} not found")
            # Return default mappings
            return {
                "silver": ["google/gemini-2.0-flash-001"],
                "gold": ["deepseek/deepseek-chat"],
                "platinum": ["google/gemini-2.5-flash"],
                "diamond": ["anthropic/claude-3-sonnet-20240229"]
            }
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing model score file: {e}")
            return {}
    
    def _call_openrouter(self, model: str, messages: List[Dict], max_tokens: int = 150) -> str:
        """
        Make API call to OpenRouter.
        
        Args:
            model: Model name to use
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
        """
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Khamel83/atlas-code",
            "X-Title": "Ralex V2"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.1
        }
        
        try:
            response = requests.post(
                f"{self.openrouter_base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API call failed: {e}")
            raise
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected OpenRouter response format: {e}")
            raise
    
    def classify_task(self, task_text: str) -> str:
        """
        Classify a task using AI to determine appropriate tier.
        
        Args:
            task_text: The task description to classify
            
        Returns:
            Tier name as string ('silver', 'gold', 'platinum', 'diamond')
        """
        messages = [
            {
                "role": "system",
                "content": """Classify the user task into: silver, gold, platinum, or diamond.
Think step by step. Focus on reasoning depth, context length, ambiguity, and novelty.

silver: trivial tasks, typos, simple explanations, basic scripts, quick fixes
gold: regular programming tasks, debugging, simple features, standard implementations
platinum: complex refactoring, multi-file reasoning, advanced algorithms, optimization
diamond: high-stakes reasoning, architecture design, complex system analysis, research

Respond with only one word."""
            },
            {
                "role": "user", 
                "content": task_text
            }
        ]
        
        try:
            response = self._call_openrouter(self.classifier_model, messages, max_tokens=10)
            tier = response.lower().strip()
            
            # Validate response
            if tier in ['silver', 'gold', 'platinum', 'diamond']:
                logger.info(f"Task classified as: {tier} using {self.classifier_model}")
                return tier
            else:
                logger.warning(f"Invalid classification response: {response}, trying fallback classifier")
                # Try fallback classifier
                try:
                    fallback_response = self._call_openrouter(self.fallback_classifier, messages, max_tokens=10)
                    fallback_tier = fallback_response.lower().strip()
                    if fallback_tier in ['silver', 'gold', 'platinum', 'diamond']:
                        logger.info(f"Fallback classification successful: {fallback_tier}")
                        return fallback_tier
                except Exception as fallback_error:
                    logger.error(f"Fallback classification failed: {fallback_error}")
                
                logger.warning("Both classifiers failed, defaulting to gold")
                return 'gold'
                
        except Exception as e:
            logger.error(f"Primary classification failed: {e}, trying fallback")
            # Try fallback classifier
            try:
                fallback_response = self._call_openrouter(self.fallback_classifier, messages, max_tokens=10)
                fallback_tier = fallback_response.lower().strip()
                if fallback_tier in ['silver', 'gold', 'platinum', 'diamond']:
                    logger.info(f"Fallback classification successful: {fallback_tier}")
                    return fallback_tier
            except Exception as fallback_error:
                logger.error(f"Fallback classification failed: {fallback_error}")
            
            logger.error("All classification attempts failed, defaulting to gold")
            return 'gold'
    
    def is_model_available(self, model_name: str) -> bool:
        """
        Check if a model is available via OpenRouter.
        
        Args:
            model_name: Name of the model to check
            
        Returns:
            True if model is available, False otherwise
        """
        # For now, assume all models in our mappings are available
        # In production, this could query OpenRouter's models endpoint
        return model_name in self.model_costs
    
    def budget_ok(self, model_name: str, budget_remaining: float) -> bool:
        """
        Check if using a model is within budget constraints.
        
        Args:
            model_name: Name of the model to check
            budget_remaining: Remaining budget in USD
            
        Returns:
            True if model is within budget, False otherwise
        """
        if budget_remaining <= 0:
            return False
            
        cost_per_1k = self.model_costs.get(model_name, 1.0)
        # Assume average request uses ~2k tokens
        estimated_cost = (2000 / 1000) * cost_per_1k
        
        return estimated_cost <= budget_remaining
    
    def is_low_confidence(self, response: str) -> bool:
        """
        Check if a response indicates low confidence and should be escalated.
        
        Args:
            response: The model's response text
            
        Returns:
            True if confidence is low, False otherwise
        """
        low_confidence_tokens = [
            "i'm not sure", "maybe", "probably", "<escalate>", "can't answer",
            "i'm not certain", "might be", "could be", "uncertain", "unclear",
            "escalate", "need help", "difficult", "not confident"
        ]
        
        response_lower = response.lower()
        return any(token in response_lower for token in low_confidence_tokens)
    
    def compress_prompt(self, prompt: str) -> str:
        """
        Compress a long prompt while preserving essential information.
        
        Args:
            prompt: The original prompt text
            
        Returns:
            Compressed prompt text
        """
        # Rough token estimation: ~4 characters per token
        estimated_tokens = len(prompt) // 4
        
        if estimated_tokens <= 5000:
            logger.debug(f"Prompt length OK: ~{estimated_tokens} tokens")
            return prompt
            
        logger.warning(f"Long prompt detected: ~{estimated_tokens} tokens ({len(prompt)} chars)")
        
        messages = [
            {
                "role": "system",
                "content": "Summarize this coding task in 1–2 paragraphs, preserving all essential details. Keep all technical requirements, file names, and specific instructions."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            compressed = self._call_openrouter(self.compression_model, messages, max_tokens=500)
            compressed_tokens = len(compressed) // 4
            logger.info(f"Compressed prompt: {estimated_tokens} → {compressed_tokens} tokens ({len(prompt)} → {len(compressed)} chars)")
            return compressed
        except Exception as e:
            logger.error(f"Prompt compression failed: {e}, using original")
            return prompt
    
    def choose_model(self, task_text: str, budget_remaining: float = float('inf')) -> Tuple[str, str, str]:
        """
        Choose the optimal model for a given task and budget.
        
        Args:
            task_text: The task description
            budget_remaining: Remaining budget in USD
            
        Returns:
            Tuple of (model_name, tier, reason)
        """
        # Classify the task
        tier = self.classify_task(task_text)
        original_tier = tier
        
        # Get models for this tier
        tier_models = self.model_mappings.get(tier, [])
        
        # Try to find an available model within budget
        for model in tier_models:
            if self.is_model_available(model) and self.budget_ok(model, budget_remaining):
                logger.info(f"Selected {model} from {tier} tier")
                return model, tier, f"optimal choice for {tier} tier"
        
        # Fallback 1: Try lower tiers if budget constrained
        tier_order = ['diamond', 'platinum', 'gold', 'silver']
        current_tier_idx = tier_order.index(tier) if tier in tier_order else 2
        
        for fallback_tier in tier_order[current_tier_idx + 1:]:
            fallback_models = self.model_mappings.get(fallback_tier, [])
            for model in fallback_models:
                if self.is_model_available(model) and self.budget_ok(model, budget_remaining):
                    logger.warning(f"Falling back to {model} from {fallback_tier} tier due to budget")
                    return model, fallback_tier, f"budget fallback from {original_tier} to {fallback_tier}"
        
        # Fallback 2: Use cheapest available model
        cheapest_model = min(
            [m for m in self.model_costs.keys() if self.is_model_available(m)],
            key=lambda m: self.model_costs[m]
        )
        
        if self.budget_ok(cheapest_model, budget_remaining):
            logger.warning(f"Using cheapest available model: {cheapest_model}")
            return cheapest_model, "silver", f"emergency fallback - cheapest available"
        
        # Fallback 3: Use free model if available
        free_models = [m for m, cost in self.model_costs.items() if cost == 0 and self.is_model_available(m)]
        if free_models:
            free_model = free_models[0]
            logger.warning(f"Using free model due to budget constraints: {free_model}")
            return free_model, "silver", "free model due to budget exhaustion"
        
        # Last resort: use the classifier model
        logger.error("No suitable model found, using classifier model as last resort")
        return self.classifier_model, "silver", "last resort - no budget remaining"
    
    def escalate_tier(self, current_tier: str) -> Optional[str]:
        """
        Get the next higher tier for escalation.
        
        Args:
            current_tier: Current tier name
            
        Returns:
            Next higher tier name, or None if already at highest tier
        """
        tier_hierarchy = ['silver', 'gold', 'platinum', 'diamond']
        
        if current_tier not in tier_hierarchy:
            return 'gold'  # Default fallback
            
        current_idx = tier_hierarchy.index(current_tier)
        if current_idx < len(tier_hierarchy) - 1:
            return tier_hierarchy[current_idx + 1]
        
        return None  # Already at highest tier
    
    def route_request(self, task_text: str, budget_remaining: float = float('inf'), 
                     allow_compression: bool = True) -> Dict:
        """
        Complete routing decision with all logic applied.
        
        Args:
            task_text: The task description
            budget_remaining: Remaining budget in USD
            allow_compression: Whether to compress long prompts
            
        Returns:
            Dictionary with routing decision details
        """
        # Compress prompt if needed
        original_prompt = task_text
        if allow_compression and len(task_text) > 5000:
            task_text = self.compress_prompt(task_text)
            compressed = True
        else:
            compressed = False
        
        # Choose initial model
        model, tier, reason = self.choose_model(task_text, budget_remaining)
        
        routing_info = {
            'model': model,
            'tier': tier,
            'reason': reason,
            'budget_remaining': budget_remaining,
            'prompt_compressed': compressed,
            'original_prompt_length': len(original_prompt),
            'final_prompt_length': len(task_text),
            'escalation_available': self.escalate_tier(tier) is not None
        }
        
        logger.info(f"Routing decision: {routing_info}")
        return routing_info

# Convenience functions for backward compatibility
def classify_task(task_text: str) -> str:
    """Classify a task using AI to determine appropriate tier."""
    router = IntelligentModelRouter()
    return router.classify_task(task_text)

def choose_model(task_text: str, budget_remaining: float = float('inf')) -> str:
    """Choose the optimal model for a given task and budget."""
    router = IntelligentModelRouter()
    model, _, _ = router.choose_model(task_text, budget_remaining)
    return model

def is_model_available(model_name: str) -> bool:
    """Check if a model is available via OpenRouter."""
    router = IntelligentModelRouter()
    return router.is_model_available(model_name)

def budget_ok(model_name: str, budget_remaining: float) -> bool:
    """Check if using a model is within budget constraints."""
    router = IntelligentModelRouter()
    return router.budget_ok(model_name, budget_remaining)

def is_low_confidence(response: str) -> bool:
    """Check if a response indicates low confidence."""
    router = IntelligentModelRouter()
    return router.is_low_confidence(response)