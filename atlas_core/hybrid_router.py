"""
Hybrid Intelligence Router for Atlas Code V5

Combines AI classification, semantic routing, and pattern matching
for maximum accuracy and 100% uptime.
"""

import json
import re
import logging
import math
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class IntentClassification:
    """Results of intent classification."""
    
    def __init__(
        self,
        intent: str,
        confidence: float,
        method: str,
        complexity: str = "medium",
        estimated_tokens: int = 500,
        reasoning: str = "",
        fallback_used: bool = False
    ):
        self.intent = intent
        self.confidence = confidence
        self.method = method  # "ai", "semantic", "pattern", "fallback"
        self.complexity = complexity
        self.estimated_tokens = estimated_tokens
        self.reasoning = reasoning
        self.fallback_used = fallback_used
        self.timestamp = datetime.now()

class HybridRouter:
    """
    Multi-method task classification with AI, semantic, and pattern fallbacks
    for maximum accuracy and 100% uptime.
    """
    
    def __init__(self, config_dir: str):
        """Initialize the hybrid router with configuration."""
        self.config_dir = config_dir
        
        # Load configuration files
        self.intent_routes = self._load_intent_routes()
        self.pattern_rules = self._load_pattern_rules()
        self.prompts = self._load_prompts()
        self.settings = self._load_settings()
        self.semantic_cache = self._load_semantic_cache()
        
        # Initialize OpenRouter client for AI classification
        try:
            from .openrouter_client import OpenRouterClient
            self.openrouter_client = OpenRouterClient(config_dir)
            self.ai_classification_enabled = True
            logger.info("AI classification enabled with OpenRouter")
        except Exception as e:
            logger.warning(f"AI classification disabled: {e}")
            self.openrouter_client = None
            self.ai_classification_enabled = False
        
        # Classification history for learning
        self.classification_history: List[IntentClassification] = []
        
        # Performance metrics
        self.method_performance = {
            "ai": {"attempts": 0, "successes": 0, "avg_confidence": 0.0},
            "semantic": {"attempts": 0, "successes": 0, "avg_confidence": 0.0},
            "pattern": {"attempts": 0, "successes": 0, "avg_confidence": 0.0}
        }
        
        logger.info("Hybrid router initialized successfully")
    
    def _load_intent_routes(self) -> Dict[str, Any]:
        """Load intent routing configuration."""
        try:
            route_path = os.path.join(self.config_dir, 'intent_routes.json')
            with open(route_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load intent routes: {e}")
            return self._get_default_intent_routes()
    
    def _load_pattern_rules(self) -> Dict[str, Any]:
        """Load pattern matching rules."""
        try:
            pattern_path = os.path.join(self.config_dir, 'pattern_rules.json')
            with open(pattern_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load pattern rules: {e}")
            return self._get_default_pattern_rules()
    
    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompt templates."""
        try:
            prompts_path = os.path.join(self.config_dir, 'prompts.json')
            with open(prompts_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load prompts: {e}")
            return self._get_default_prompts()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load system settings."""
        try:
            settings_path = os.path.join(self.config_dir, 'settings.json')
            with open(settings_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return self._get_default_settings()
    
    def _load_semantic_cache(self) -> Dict[str, Any]:
        """Load semantic embeddings cache."""
        try:
            cache_path = os.path.join(self.config_dir, '../data/semantic_embeddings.json')
            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load semantic cache: {e}")
            return self._build_default_semantic_cache()
    
    def classify_intent(
        self,
        user_input: str,
        file_context: Optional[str] = None,
        language: Optional[str] = None,
        previous_context: Optional[List[str]] = None
    ) -> IntentClassification:
        """
        Classify user intent using hybrid approach.
        
        Args:
            user_input: The user's request or query
            file_context: Optional file content for context
            language: Programming language if known
            previous_context: Previous conversation context
            
        Returns:
            IntentClassification with intent, confidence, and metadata
        """
        logger.debug(f"Classifying intent for: {user_input[:100]}...")
        
        # Try AI classification first (highest accuracy)
        if self.ai_classification_enabled:
            try:
                ai_result = self._classify_with_ai(
                    user_input, file_context, language, previous_context
                )
                if ai_result.confidence >= 0.7:  # High confidence threshold
                    self._update_performance_metrics("ai", ai_result.confidence)
                    self.classification_history.append(ai_result)
                    logger.info(f"AI classification: {ai_result.intent} ({ai_result.confidence:.2f})")
                    return ai_result
            except Exception as e:
                logger.warning(f"AI classification failed: {e}")
        
        # Fallback to semantic classification
        try:
            semantic_result = self._classify_with_semantics(
                user_input, file_context, language
            )
            if semantic_result.confidence >= 0.6:  # Medium confidence threshold
                self._update_performance_metrics("semantic", semantic_result.confidence)
                self.classification_history.append(semantic_result)
                logger.info(f"Semantic classification: {semantic_result.intent} ({semantic_result.confidence:.2f})")
                return semantic_result
        except Exception as e:
            logger.warning(f"Semantic classification failed: {e}")
        
        # Final fallback to pattern matching
        try:
            pattern_result = self._classify_with_patterns(
                user_input, file_context, language
            )
            pattern_result.fallback_used = True
            self._update_performance_metrics("pattern", pattern_result.confidence)
            self.classification_history.append(pattern_result)
            logger.info(f"Pattern classification: {pattern_result.intent} ({pattern_result.confidence:.2f})")
            return pattern_result
        except Exception as e:
            logger.error(f"All classification methods failed: {e}")
            
            # Absolute fallback
            return IntentClassification(
                intent="general_query",
                confidence=0.3,
                method="fallback",
                reasoning="All classification methods failed, using default",
                fallback_used=True
            )
    
    def _classify_with_ai(
        self,
        user_input: str,
        file_context: Optional[str] = None,
        language: Optional[str] = None,
        previous_context: Optional[List[str]] = None
    ) -> IntentClassification:
        """Classify intent using AI/LLM."""
        
        # Prepare context information
        context_info = {
            "file_extensions": self._extract_file_extensions(file_context) if file_context else [],
            "keywords": self._extract_keywords(user_input),
            "previous_context": previous_context[-3:] if previous_context else []
        }
        
        # Get available intents
        available_intents = list(self.intent_routes['routing_rules'].keys())
        
        # Format the classification prompt
        classification_prompt = self.prompts['classification_prompt']
        system_prompt = classification_prompt['system']
        user_prompt = classification_prompt['user_template'].format(
            user_input=user_input,
            file_extensions=", ".join(context_info["file_extensions"]),
            keywords=", ".join(context_info["keywords"]),
            previous_context=", ".join(context_info["previous_context"]),
            available_intents=", ".join(available_intents)
        )
        
        # Make API request
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.openrouter_client.generate_response(
            model="anthropic/claude-3-haiku",  # Fast model for classification
            messages=messages,
            max_tokens=150,
            temperature=0.1  # Low temperature for consistent classification
        )
        
        if not response.success:
            raise Exception(f"AI classification API error: {response.error}")
        
        # Parse JSON response
        try:
            result = json.loads(response.content.strip())
            
            intent = result.get('intent', 'general_query')
            confidence = float(result.get('confidence', 0.5))
            reasoning = result.get('reasoning', 'AI classification')
            complexity = result.get('complexity', 'medium')
            estimated_tokens = int(result.get('estimated_tokens', 500))
            
            # Validate intent is in allowed list
            if intent not in available_intents:
                intent = 'general_query'
                confidence = max(0.3, confidence - 0.2)
                reasoning += " (corrected invalid intent)"
            
            return IntentClassification(
                intent=intent,
                confidence=confidence,
                method="ai",
                complexity=complexity,
                estimated_tokens=estimated_tokens,
                reasoning=reasoning
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse AI classification response: {e}")
            raise Exception(f"Invalid AI response format: {e}")
    
    def _classify_with_semantics(
        self,
        user_input: str,
        file_context: Optional[str] = None,
        language: Optional[str] = None
    ) -> IntentClassification:
        """Classify intent using semantic similarity."""
        
        # Simple embedding simulation (in production, use proper embeddings)
        input_embedding = self._create_simple_embedding(user_input)
        
        best_intent = "general_query"
        best_similarity = 0.0
        best_reasoning = "Semantic similarity matching"
        
        # Compare with cached semantic embeddings
        cache = self.semantic_cache.get('default_semantic_cache', {})
        
        for intent, intent_data in cache.items():
            if 'centroid' in intent_data:
                centroid = intent_data['centroid']
                similarity = self._cosine_similarity(input_embedding, centroid)
                
                # Apply threshold
                threshold = intent_data.get('threshold', 0.6)
                if similarity > threshold and similarity > best_similarity:
                    best_intent = intent
                    best_similarity = similarity
                    best_reasoning = f"Semantic match with {intent} (similarity: {similarity:.3f})"
        
        # Determine complexity based on intent and input
        complexity = self._determine_complexity(user_input, best_intent)
        
        # Estimate tokens based on intent
        estimated_tokens = self.intent_routes['routing_rules'].get(
            best_intent, {}
        ).get('estimated_tokens', 500)
        
        return IntentClassification(
            intent=best_intent,
            confidence=min(best_similarity + 0.1, 0.95),  # Boost confidence slightly
            method="semantic",
            complexity=complexity,
            estimated_tokens=estimated_tokens,
            reasoning=best_reasoning
        )
    
    def _classify_with_patterns(
        self,
        user_input: str,
        file_context: Optional[str] = None,
        language: Optional[str] = None
    ) -> IntentClassification:
        """Classify intent using pattern matching."""
        
        classification_rules = self.pattern_rules.get('pattern_classification_rules', {})
        
        best_intent = "general_query"
        best_confidence = 0.0
        best_reasoning = "Pattern matching"
        matched_patterns = []
        
        # Preprocess input
        processed_input = user_input.lower().strip()
        
        # Check each intent's patterns
        for intent, rule_data in classification_rules.items():
            intent_confidence = 0.0
            patterns_matched = []
            
            # Check positive patterns
            patterns = rule_data.get('patterns', [])
            for pattern_info in patterns:
                if isinstance(pattern_info, dict):
                    pattern = pattern_info['regex']
                    pattern_confidence = pattern_info.get('confidence', 0.7)
                else:
                    pattern = pattern_info
                    pattern_confidence = 0.7
                
                try:
                    if re.search(pattern, processed_input):
                        intent_confidence = max(intent_confidence, pattern_confidence)
                        patterns_matched.append(pattern)
                except re.error:
                    logger.warning(f"Invalid regex pattern: {pattern}")
                    continue
            
            # Check negative patterns (reduce confidence)
            negative_patterns = rule_data.get('negative_patterns', [])
            for neg_pattern in negative_patterns:
                try:
                    if re.search(neg_pattern, processed_input):
                        intent_confidence *= 0.7  # Reduce confidence
                except re.error:
                    continue
            
            # Apply priority boost
            priority = rule_data.get('priority', 50)
            priority_boost = (priority - 50) / 100  # Convert to boost factor
            intent_confidence += priority_boost
            
            # Check context requirements
            context_requirements = rule_data.get('context_requirements', [])
            if context_requirements:
                context_met = self._check_context_requirements(
                    context_requirements, file_context, language
                )
                if not context_met:
                    intent_confidence *= 0.8  # Reduce if context not met
            
            # Update best match
            if intent_confidence > best_confidence:
                best_intent = intent
                best_confidence = intent_confidence
                best_reasoning = f"Pattern match: {', '.join(patterns_matched[:2])}"
                matched_patterns = patterns_matched
        
        # Ensure confidence is within valid range
        best_confidence = max(0.3, min(best_confidence, 0.9))
        
        # Determine complexity
        complexity = self._determine_complexity(user_input, best_intent)
        
        # Estimate tokens
        estimated_tokens = self.intent_routes['routing_rules'].get(
            best_intent, {}
        ).get('estimated_tokens', 500)
        
        return IntentClassification(
            intent=best_intent,
            confidence=best_confidence,
            method="pattern",
            complexity=complexity,
            estimated_tokens=estimated_tokens,
            reasoning=best_reasoning
        )
    
    def _extract_file_extensions(self, file_context: str) -> List[str]:
        """Extract file extensions from context."""
        if not file_context:
            return []
        
        # Simple extraction - look for common patterns
        extensions = []
        lines = file_context.split('\n')[:10]  # Check first 10 lines
        
        for line in lines:
            if line.strip().startswith('#') and '.' in line:
                # Look for file references in comments
                words = line.split()
                for word in words:
                    if '.' in word and len(word.split('.')[-1]) <= 4:
                        ext = '.' + word.split('.')[-1]
                        if ext not in extensions:
                            extensions.append(ext)
        
        return extensions[:3]  # Limit to 3 extensions
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key keywords from text."""
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter for meaningful keywords
        meaningful_words = []
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
        
        for word in words:
            if len(word) > 2 and word not in stop_words:
                meaningful_words.append(word)
        
        return meaningful_words[:10]  # Limit to 10 keywords
    
    def _create_simple_embedding(self, text: str) -> List[float]:
        """Create a simple embedding for text (placeholder for real embeddings)."""
        # This is a very simple embedding - in production, use proper embeddings
        words = text.lower().split()
        
        # Simple hash-based embedding
        embedding = [0.0] * 8  # Match the dimension in semantic cache
        
        for i, word in enumerate(words[:8]):
            hash_val = hash(word) % 100
            embedding[i % 8] += hash_val / 100.0
        
        # Normalize
        norm = math.sqrt(sum(x * x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            dot_product = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(x * x for x in b))
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            return dot_product / (norm_a * norm_b)
        except Exception:
            return 0.0
    
    def _determine_complexity(self, user_input: str, intent: str) -> str:
        """Determine task complexity based on input and intent."""
        text_lower = user_input.lower()
        
        # High complexity indicators
        high_complexity_words = {
            'algorithm', 'optimization', 'performance', 'architecture',
            'design pattern', 'scalability', 'distributed', 'concurrent',
            'machine learning', 'neural network', 'complex', 'advanced'
        }
        
        # Medium complexity indicators  
        medium_complexity_words = {
            'function', 'class', 'module', 'refactor', 'integration',
            'database', 'api', 'framework', 'library', 'interface'
        }
        
        # Check for complexity indicators
        if any(word in text_lower for word in high_complexity_words):
            return "high"
        elif any(word in text_lower for word in medium_complexity_words):
            return "medium"
        elif len(user_input.split()) > 20:  # Long requests tend to be more complex
            return "medium"
        else:
            return "low"
    
    def _check_context_requirements(
        self,
        requirements: List[str],
        file_context: Optional[str],
        language: Optional[str]
    ) -> bool:
        """Check if context requirements are met."""
        for requirement in requirements:
            if requirement == "existing_code" and not file_context:
                return False
            elif requirement == "language" and not language:
                return False
            elif requirement == "file_context" and not file_context:
                return False
        return True
    
    def _update_performance_metrics(self, method: str, confidence: float):
        """Update performance metrics for classification methods."""
        if method in self.method_performance:
            metrics = self.method_performance[method]
            metrics["attempts"] += 1
            
            if confidence >= 0.7:  # Consider high confidence as success
                metrics["successes"] += 1
            
            # Update average confidence (running average)
            current_avg = metrics["avg_confidence"]
            metrics["avg_confidence"] = (
                (current_avg * (metrics["attempts"] - 1) + confidence) / metrics["attempts"]
            )
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report for classification methods."""
        report = {
            "total_classifications": len(self.classification_history),
            "method_breakdown": {},
            "recent_accuracy": 0.0,
            "avg_confidence": 0.0
        }
        
        if not self.classification_history:
            return report
        
        # Calculate method breakdown
        method_counts = {}
        total_confidence = 0.0
        
        for classification in self.classification_history:
            method = classification.method
            method_counts[method] = method_counts.get(method, 0) + 1
            total_confidence += classification.confidence
        
        for method, count in method_counts.items():
            percentage = (count / len(self.classification_history)) * 100
            report["method_breakdown"][method] = {
                "count": count,
                "percentage": percentage,
                "performance": self.method_performance.get(method, {})
            }
        
        # Calculate recent accuracy (last 10 classifications)
        recent_classifications = self.classification_history[-10:]
        if recent_classifications:
            high_confidence_count = sum(
                1 for c in recent_classifications if c.confidence >= 0.7
            )
            report["recent_accuracy"] = high_confidence_count / len(recent_classifications)
        
        # Average confidence
        report["avg_confidence"] = total_confidence / len(self.classification_history)
        
        return report
    
    # Default configurations (fallbacks)
    def _get_default_intent_routes(self) -> Dict[str, Any]:
        """Get default intent routes if config file is missing."""
        return {
            "routing_rules": {
                "code_generation": {"default_tier": "premium", "estimated_tokens": 1500},
                "code_editing": {"default_tier": "standard", "estimated_tokens": 800},
                "debugging": {"default_tier": "premium", "estimated_tokens": 1200},
                "explanation": {"default_tier": "standard", "estimated_tokens": 600},
                "general_query": {"default_tier": "budget", "estimated_tokens": 200}
            }
        }
    
    def _get_default_pattern_rules(self) -> Dict[str, Any]:
        """Get default pattern rules if config file is missing."""
        return {
            "pattern_classification_rules": {
                "code_generation": {
                    "patterns": [{"regex": r"(?i)(write|create|generate|build)", "confidence": 0.8}],
                    "priority": 90
                },
                "debugging": {
                    "patterns": [{"regex": r"(?i)(error|bug|debug|fix)", "confidence": 0.9}],
                    "priority": 95
                },
                "general_query": {
                    "patterns": [{"regex": r"(?i)(help|question|what|how)", "confidence": 0.6}],
                    "priority": 50
                }
            }
        }
    
    def _get_default_prompts(self) -> Dict[str, Any]:
        """Get default prompts if config file is missing."""
        return {
            "classification_prompt": {
                "system": "You are an intent classifier. Analyze the user input and classify it.",
                "user_template": "Classify this request: {user_input}\n\nAvailable intents: {available_intents}\n\nRespond with JSON containing intent, confidence, reasoning, complexity, and estimated_tokens."
            }
        }
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings if config file is missing."""
        return {
            "system_settings": {
                "timeout_seconds": 30,
                "max_context_length": 100000
            }
        }
    
    def _build_default_semantic_cache(self) -> Dict[str, Any]:
        """Build default semantic cache if file is missing."""
        return {
            "default_semantic_cache": {
                "code_generation": {
                    "centroid": [0.3, -0.067, 0.8, 0.3, -0.4, 0.6, 0.1, -0.3],
                    "threshold": 0.75
                },
                "debugging": {
                    "centroid": [0.1, -0.6, -0.2, 0.8, 0.7, 0.3, -0.4, 0.5],
                    "threshold": 0.78
                },
                "general_query": {
                    "centroid": [0.0, 0.033, 0.1, 0.1, 0.1, 0.1, 0.1, 0.0],
                    "threshold": 0.50
                }
            }
        }

# Example usage and testing
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test the hybrid router
    router = HybridRouter("../config")
    
    test_queries = [
        "write a python function to sort a list",
        "debug this error in my code", 
        "explain how binary search works",
        "optimize this slow algorithm"
    ]
    
    print("🧠 Testing Hybrid Router Classification")
    print("=" * 50)
    
    for query in test_queries:
        result = router.classify_intent(query)
        print(f"\nQuery: {query}")
        print(f"Intent: {result.intent}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Method: {result.method}")
        print(f"Complexity: {result.complexity}")
        print(f"Reasoning: {result.reasoning}")
    
    # Performance report
    print("\n📊 Performance Report:")
    report = router.get_performance_report()
    print(f"Total Classifications: {report['total_classifications']}")
    print(f"Average Confidence: {report['avg_confidence']:.2f}")
    print(f"Recent Accuracy: {report['recent_accuracy']:.2f}")