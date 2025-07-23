"""
OpenRouter API Client for Atlas Code V5

Handles all OpenRouter API interactions with robust error handling,
rate limiting, and cost tracking.
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

@dataclass
class ModelUsage:
    """Track model usage statistics."""
    tokens_input: int
    tokens_output: int
    cost_input: float
    cost_output: float
    total_cost: float
    timestamp: datetime

@dataclass
class APIResponse:
    """Structured API response."""
    success: bool
    content: str
    usage: Optional[ModelUsage]
    model: str
    error: Optional[str] = None
    retry_after: Optional[int] = None

class RateLimiter:
    """Simple rate limiter for API requests."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = []
    
    def wait_if_needed(self):
        """Wait if we're hitting rate limits."""
        now = datetime.now()
        # Remove old requests (older than 1 minute)
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < timedelta(minutes=1)]
        
        if len(self.requests) >= self.requests_per_minute:
            # Wait until the oldest request is > 1 minute old
            wait_time = 60 - (now - self.requests[0]).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
        
        self.requests.append(now)

class OpenRouterClient:
    """
    OpenRouter API client with comprehensive error handling and optimization.
    """
    
    def __init__(self, config_dir: str):
        """Initialize OpenRouter client with configuration."""
        self.config_dir = config_dir
        self.settings = self._load_settings()
        self.api_key = self._get_api_key()
        self.base_url = self.settings['api_configuration']['openrouter']['base_url']
        
        # Initialize session with retry strategy
        self.session = self._create_session()
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            self.settings['api_configuration']['rate_limits']['requests_per_minute']
        )
        
        # Track usage
        self.usage_history: List[ModelUsage] = []
        
        logger.info("OpenRouter client initialized successfully")
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from configuration."""
        settings_path = os.path.join(self.config_dir, 'settings.json')
        try:
            with open(settings_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            raise Exception(f"Configuration error: {e}")
    
    def _get_api_key(self) -> str:
        """Get OpenRouter API key from environment or config."""
        # Try environment variable first
        api_key = os.getenv('OPENROUTER_API_KEY')
        
        if not api_key:
            # Try loading from config file (not recommended for production)
            try:
                config_path = os.path.join(self.config_dir, 'api_keys.json')
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        keys = json.load(f)
                        api_key = keys.get('openrouter_api_key')
            except Exception:
                pass
        
        if not api_key:
            raise Exception(
                "OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable "
                "or add to config/api_keys.json"
            )
        
        return api_key
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.settings['api_configuration']['openrouter']['max_retries'],
            backoff_factor=self.settings['api_configuration']['openrouter']['retry_delay'],
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': self.settings['api_configuration']['openrouter']['headers']['HTTP-Referer'],
            'X-Title': self.settings['api_configuration']['openrouter']['headers']['X-Title'],
        })
        
        return session
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from OpenRouter."""
        try:
            self.rate_limiter.wait_if_needed()
            
            response = self.session.get(
                f"{self.base_url}/models",
                timeout=self.settings['api_configuration']['openrouter']['timeout']
            )
            
            response.raise_for_status()
            models_data = response.json()
            
            return models_data.get('data', [])
            
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []
    
    def generate_response(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> APIResponse:
        """
        Generate response from OpenRouter API.
        
        Args:
            model: Model name (e.g., 'anthropic/claude-3.5-sonnet')
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional model parameters
        
        Returns:
            APIResponse with generated content and usage info
        """
        try:
            self.rate_limiter.wait_if_needed()
            
            # Prepare request payload
            payload = {
                'model': model,
                'messages': messages,
                'temperature': temperature,
                **kwargs
            }
            
            if max_tokens:
                payload['max_tokens'] = max_tokens
            
            logger.debug(f"Sending request to {model}: {len(messages)} messages")
            
            # Make API request
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=self.settings['api_configuration']['openrouter']['timeout']
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Retry after {retry_after} seconds")
                return APIResponse(
                    success=False,
                    content="",
                    usage=None,
                    model=model,
                    error="Rate limited",
                    retry_after=retry_after
                )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract response content
            content = ""
            if 'choices' in result and result['choices']:
                choice = result['choices'][0]
                if 'message' in choice:
                    content = choice['message'].get('content', '')
                elif 'text' in choice:
                    content = choice['text']
            
            # Extract usage information
            usage = None
            if 'usage' in result:
                usage_data = result['usage']
                
                # Get model pricing (simplified - in production, load from model metadata)
                input_cost_per_token = self._get_model_cost(model, 'input')
                output_cost_per_token = self._get_model_cost(model, 'output')
                
                tokens_input = usage_data.get('prompt_tokens', 0)
                tokens_output = usage_data.get('completion_tokens', 0)
                
                cost_input = tokens_input * input_cost_per_token
                cost_output = tokens_output * output_cost_per_token
                
                usage = ModelUsage(
                    tokens_input=tokens_input,
                    tokens_output=tokens_output,
                    cost_input=cost_input,
                    cost_output=cost_output,
                    total_cost=cost_input + cost_output,
                    timestamp=datetime.now()
                )
                
                # Track usage
                self.usage_history.append(usage)
            
            logger.info(f"Successful response from {model}: {len(content)} chars")
            
            return APIResponse(
                success=True,
                content=content,
                usage=usage,
                model=model
            )
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for model {model}")
            return APIResponse(
                success=False,
                content="",
                usage=None,
                model=model,
                error="Request timeout"
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for model {model}: {e}")
            return APIResponse(
                success=False,
                content="",
                usage=None,
                model=model,
                error=f"Request error: {e}"
            )
            
        except Exception as e:
            logger.error(f"Unexpected error for model {model}: {e}")
            return APIResponse(
                success=False,
                content="",
                usage=None,
                model=model,
                error=f"Unexpected error: {e}"
            )
    
    def _get_model_cost(self, model: str, token_type: str) -> float:
        """Get per-token cost for a model (simplified implementation)."""
        # In production, this would load from model metadata
        # For now, return default costs
        cost_map = {
            'anthropic/claude-3.5-sonnet': {'input': 0.000003, 'output': 0.000015},
            'anthropic/claude-3-haiku': {'input': 0.00000025, 'output': 0.00000125},
            'openai/gpt-4-turbo': {'input': 0.00001, 'output': 0.00003},
            'openai/gpt-3.5-turbo': {'input': 0.0000005, 'output': 0.0000015},
            'meta-llama/llama-3-8b-instruct': {'input': 0.00000015, 'output': 0.00000015},
            'mistralai/mistral-7b-instruct': {'input': 0.00000015, 'output': 0.00000015},
        }
        
        model_costs = cost_map.get(model, {'input': 0.000001, 'output': 0.000001})
        return model_costs.get(token_type, 0.000001)
    
    def get_usage_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get usage summary for the specified time period."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_usage = [u for u in self.usage_history if u.timestamp > cutoff]
        
        if not recent_usage:
            return {
                'total_requests': 0,
                'total_tokens': 0,
                'total_cost': 0.0,
                'period_hours': hours
            }
        
        total_tokens = sum(u.tokens_input + u.tokens_output for u in recent_usage)
        total_cost = sum(u.total_cost for u in recent_usage)
        
        return {
            'total_requests': len(recent_usage),
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'average_tokens_per_request': total_tokens / len(recent_usage),
            'average_cost_per_request': total_cost / len(recent_usage),
            'period_hours': hours
        }
    
    def test_connection(self) -> bool:
        """Test connection to OpenRouter API."""
        try:
            models = self.get_available_models()
            return len(models) > 0
        except Exception:
            return False

# Example usage and testing
if __name__ == "__main__":
    # This would normally be run as part of tests
    logging.basicConfig(level=logging.INFO)
    
    try:
        client = OpenRouterClient('../config')
        
        # Test connection
        if client.test_connection():
            print("✅ OpenRouter connection successful")
            
            # Test simple request
            messages = [
                {"role": "user", "content": "Say hello in Python code"}
            ]
            
            response = client.generate_response(
                model="anthropic/claude-3-haiku",
                messages=messages,
                max_tokens=100
            )
            
            if response.success:
                print(f"✅ Test response: {response.content[:100]}...")
                if response.usage:
                    print(f"💰 Cost: ${response.usage.total_cost:.6f}")
            else:
                print(f"❌ Test failed: {response.error}")
        else:
            print("❌ OpenRouter connection failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")