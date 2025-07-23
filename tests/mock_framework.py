"""
Mock Framework for Atlas Code V5 Testing

Provides token-free testing infrastructure with realistic mock responses
for all API interactions and component testing.
"""

import json
import random
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class MockUsage:
    """Mock usage statistics for API responses."""
    tokens_input: int
    tokens_output: int
    cost_input: float
    cost_output: float
    total_cost: float
    timestamp: datetime

@dataclass
class MockAPIResponse:
    """Mock API response structure."""
    success: bool
    content: str
    usage: Optional[MockUsage]
    model: str
    error: Optional[str] = None
    retry_after: Optional[int] = None

class MockResponseGenerator:
    """Generates realistic mock responses based on intent and model."""
    
    def __init__(self):
        """Initialize with predefined response templates."""
        self.response_templates = {
            "code_generation": {
                "python": [
                    '''```python
def fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Example usage
result = fibonacci(10)
print(f"10th Fibonacci number: {result}")
```''',
                    '''```python
class Calculator:
    """Simple calculator class."""
    
    def add(self, a: float, b: float) -> float:
        return a + b
    
    def subtract(self, a: float, b: float) -> float:
        return a - b
    
    def multiply(self, a: float, b: float) -> float:
        return a * b
    
    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

# Example usage
calc = Calculator()
result = calc.add(5, 3)
```'''
                ],
                "javascript": [
                    '''```javascript
function bubbleSort(arr) {
    const n = arr.length;
    for (let i = 0; i < n - 1; i++) {
        for (let j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                [arr[j], arr[j + 1]] = [arr[j + 1], arr[j]];
            }
        }
    }
    return arr;
}

// Example usage
const numbers = [64, 34, 25, 12, 22, 11, 90];
const sorted = bubbleSort(numbers);
console.log("Sorted array:", sorted);
```''',
                    '''```javascript
class EventEmitter {
    constructor() {
        this.events = {};
    }
    
    on(event, listener) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(listener);
    }
    
    emit(event, ...args) {
        if (this.events[event]) {
            this.events[event].forEach(listener => {
                listener(...args);
            });
        }
    }
}

// Example usage
const emitter = new EventEmitter();
emitter.on('message', (msg) => console.log('Received:', msg));
emitter.emit('message', 'Hello World!');
```'''
                ]
            },
            "code_editing": [
                "I've modified your function to include proper error handling and input validation. The changes ensure the code is more robust and follows best practices.",
                "The code has been refactored to improve readability and performance. Key changes include variable renaming, loop optimization, and added comments.",
                "Updated the implementation with the requested modifications. The new version maintains backward compatibility while adding the requested features."
            ],
            "debugging": [
                '''The error is caused by an undefined variable. Here's the fix:

**Root Cause**: The variable `user_name` is referenced before being defined.

**Solution**:
```python
# Add this line before using the variable
user_name = "John Doe"  # or get from user input

# Then your existing code will work
print(f"Hello, {user_name}!")
```

**Prevention**: Always initialize variables before using them, or add proper error checking.''',
                '''This is a classic off-by-one error. Here's the fix:

**Root Cause**: The loop condition `i < len(array)` should be `i <= len(array)` or the array access should be `array[i-1]`.

**Solution**:
```python
# Change from:
for i in range(1, len(array)):
    print(array[i])

# To:
for i in range(len(array)):
    print(array[i])
```'''
            ],
            "explanation": [
                '''This code implements a binary search algorithm:

## How it works:
1. **Divide**: Split the sorted array in half
2. **Compare**: Check if the target equals the middle element
3. **Conquer**: If not found, recursively search the appropriate half

## Key Points:
- Time complexity: O(log n)
- Space complexity: O(1) for iterative version
- Requires a sorted array
- Much faster than linear search for large datasets

## Example:
```python
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1  # Not found
```''',
                '''This is a recursive function that calls itself with a smaller problem:

## Understanding Recursion:
- **Base Case**: The condition that stops the recursion
- **Recursive Case**: The function calling itself with modified parameters
- **Stack**: Each call is added to the call stack until base case is reached

## Example - Factorial:
```python
def factorial(n):
    if n <= 1:        # Base case
        return 1
    return n * factorial(n-1)  # Recursive case
```

Think of it like Russian nesting dolls - each doll contains a smaller version until you reach the smallest one.'''
            ],
            "optimization": [
                '''Here's the optimized version with improved performance:

## Performance Analysis:
- **Before**: O(n²) time complexity with nested loops
- **After**: O(n log n) using sorting and binary search
- **Memory**: Reduced from O(n²) to O(1) extra space

## Optimized Code:
```python
def optimized_search(data, target):
    # Sort once if not already sorted
    if not hasattr(data, '_sorted'):
        data.sort()
        data._sorted = True
    
    # Use binary search instead of linear
    return binary_search(data, target)
```

## Trade-offs:
- ✅ Much faster for repeated searches
- ✅ Lower memory usage
- ⚠️ Initial sorting cost if data changes frequently''',
                '''Performance improvements applied:

## Optimizations Made:
1. **Replaced nested loops** with dictionary lookup (O(1) vs O(n))
2. **Added memoization** to cache expensive calculations
3. **Used list comprehension** instead of explicit loops
4. **Eliminated redundant operations** in the main loop

## Results:
- 85% faster execution time
- 60% less memory usage
- Better scalability for large datasets

The code now handles 10x more data in the same time while maintaining readability.'''
            ],
            "testing": [
                '''```python
import pytest
from your_module import Calculator

class TestCalculator:
    def setup_method(self):
        self.calc = Calculator()
    
    def test_addition(self):
        assert self.calc.add(2, 3) == 5
        assert self.calc.add(-1, 1) == 0
        assert self.calc.add(0, 0) == 0
    
    def test_division_by_zero(self):
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            self.calc.divide(10, 0)
    
    def test_edge_cases(self):
        # Test with floating point numbers
        assert abs(self.calc.divide(1, 3) - 0.333333) < 0.000001
        
        # Test with negative numbers
        assert self.calc.multiply(-2, -3) == 6
```

This test suite covers:
- ✅ Basic functionality
- ✅ Edge cases
- ✅ Error conditions
- ✅ Floating point precision''',
                '''```python
import unittest
from unittest.mock import patch, MagicMock

class TestFileProcessor:
    @patch('builtins.open')
    def test_file_reading(self, mock_open):
        # Mock file content
        mock_open.return_value.__enter__.return_value.read.return_value = "test data"
        
        processor = FileProcessor()
        result = processor.read_file("test.txt")
        
        assert result == "test data"
        mock_open.assert_called_once_with("test.txt", 'r')
    
    def test_data_validation(self):
        processor = FileProcessor()
        
        # Test valid data
        assert processor.validate({"name": "John", "age": 30}) == True
        
        # Test invalid data
        assert processor.validate({"name": ""}) == False
        assert processor.validate({}) == False
```'''
            ],
            "documentation": [
                '''# API Documentation

## Overview
This module provides core functionality for data processing and analysis.

## Classes

### DataProcessor
Handles data cleaning, transformation, and analysis operations.

#### Methods

##### `process_data(data: List[Dict]) -> Dict`
Processes raw data and returns analysis results.

**Parameters:**
- `data`: List of dictionaries containing raw data records

**Returns:**
- Dictionary with processed results and statistics

**Example:**
```python
processor = DataProcessor()
results = processor.process_data([
    {"name": "Alice", "score": 95},
    {"name": "Bob", "score": 87}
])
print(results["average"])  # 91.0
```

**Raises:**
- `ValueError`: If data is empty or invalid format
- `TypeError`: If data is not a list of dictionaries''',
                '''# User Guide

## Getting Started

### Installation
```bash
pip install atlas-code-v5
```

### Quick Start
```python
from atlas_core import AtlasRouter

# Initialize the router
router = AtlasRouter(config_dir="./config")

# Process a coding request
result = router.process_request("write a python function to sort a list")
print(result.response)
```

### Configuration

Create a `config/settings.json` file:
```json
{
  "user_preferences": {
    "default_language": "python",
    "preferred_tier": "standard"
  }
}
```

### Advanced Usage

#### Custom Model Selection
```python
result = router.process_request(
    "optimize this code", 
    forced_tier="premium"
)
```

#### File Context
```python
with open("mycode.py", "r") as f:
    code_content = f.read()

result = router.process_request(
    "debug this error",
    file_context=code_content
)
```'''
            ],
            "file_operations": [
                '''```python
import json
import csv
from pathlib import Path

def read_json_file(filepath: str) -> dict:
    """Safely read and parse a JSON file."""
    try:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {filepath}: {e}")
    except PermissionError:
        raise PermissionError(f"No permission to read {filepath}")

def write_csv_data(filepath: str, data: list, headers: list):
    """Write data to a CSV file with proper error handling."""
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(data)
        
        print(f"Successfully wrote {len(data)} rows to {filepath}")
    
    except PermissionError:
        raise PermissionError(f"No permission to write to {filepath}")
    except Exception as e:
        raise Exception(f"Error writing CSV: {e}")
```''',
                '''```python
import xml.etree.ElementTree as ET
from typing import Dict, Any

def parse_xml_file(filepath: str) -> Dict[str, Any]:
    """Parse XML file and convert to dictionary structure."""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        def element_to_dict(element):
            result = {}
            
            # Add attributes
            if element.attrib:
                result['@attributes'] = element.attrib
            
            # Add text content
            if element.text and element.text.strip():
                if len(element) == 0:  # No children
                    return element.text.strip()
                result['#text'] = element.text.strip()
            
            # Add children
            for child in element:
                child_data = element_to_dict(child)
                if child.tag in result:
                    if not isinstance(result[child.tag], list):
                        result[child.tag] = [result[child.tag]]
                    result[child.tag].append(child_data)
                else:
                    result[child.tag] = child_data
            
            return result
        
        return {root.tag: element_to_dict(root)}
    
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML in {filepath}: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"XML file not found: {filepath}")
```'''
            ],
            "general_query": [
                "Python is a high-level, interpreted programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
                "The main difference between lists and tuples in Python is that lists are mutable (can be changed) while tuples are immutable (cannot be changed). Lists use square brackets [], tuples use parentheses ().",
                "Best practices for Python development include: using meaningful variable names, following PEP 8 style guidelines, writing docstrings for functions, using virtual environments, and implementing proper error handling.",
                "Git is a distributed version control system that tracks changes in source code during software development. It allows multiple developers to work on the same project efficiently and maintain a complete history of changes."
            ]
        }
        
        # Model-specific response variations
        self.model_characteristics = {
            "anthropic/claude-3.5-sonnet": {
                "style": "detailed and comprehensive",
                "code_quality": "production-ready with extensive comments",
                "explanation_depth": "thorough with examples"
            },
            "anthropic/claude-3-haiku": {
                "style": "concise and efficient",
                "code_quality": "clean and functional",
                "explanation_depth": "clear and direct"
            },
            "openai/gpt-4-turbo": {
                "style": "structured and methodical",
                "code_quality": "well-organized with good practices",
                "explanation_depth": "comprehensive with context"
            },
            "openai/gpt-3.5-turbo": {
                "style": "straightforward and practical",
                "code_quality": "functional with basic comments",
                "explanation_depth": "adequate with examples"
            }
        }
    
    def generate_response(self, intent: str, model: str, query: str, **kwargs) -> str:
        """Generate a mock response based on intent and model."""
        # Get base response templates for intent
        templates = self.response_templates.get(intent, ["Generic response for your request."])
        
        # Select template based on language or random selection
        language = kwargs.get('language', 'python')
        
        if intent == "code_generation" and language in templates:
            response_pool = templates[language]
        elif isinstance(templates, dict):
            response_pool = list(templates.values())[0] if templates else ["Generic response."]
        else:
            response_pool = templates
        
        # Select a random response from the pool
        base_response = random.choice(response_pool)
        
        # Modify response based on model characteristics
        model_style = self.model_characteristics.get(model, {})
        
        if model_style.get("style") == "detailed and comprehensive":
            base_response += "\n\n*Note: This implementation follows best practices and includes comprehensive error handling.*"
        elif model_style.get("style") == "concise and efficient":
            base_response += "\n\n*This solution is optimized for performance and simplicity.*"
        
        return base_response
    
    def generate_usage_stats(self, model: str, response_length: int) -> MockUsage:
        """Generate realistic usage statistics."""
        # Estimate tokens based on response length (rough approximation)
        tokens_output = max(10, response_length // 4)  # ~4 chars per token
        tokens_input = random.randint(50, 200)  # Typical input size
        
        # Get model costs (simplified)
        cost_rates = {
            'anthropic/claude-3.5-sonnet': {'input': 0.000003, 'output': 0.000015},
            'anthropic/claude-3-haiku': {'input': 0.00000025, 'output': 0.00000125},
            'openai/gpt-4-turbo': {'input': 0.00001, 'output': 0.00003},
            'openai/gpt-3.5-turbo': {'input': 0.0000005, 'output': 0.0000015},
        }
        
        rates = cost_rates.get(model, {'input': 0.000001, 'output': 0.000001})
        
        cost_input = tokens_input * rates['input']
        cost_output = tokens_output * rates['output']
        
        return MockUsage(
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_input=cost_input,
            cost_output=cost_output,
            total_cost=cost_input + cost_output,
            timestamp=datetime.now()
        )

class MockOpenRouterClient:
    """Mock OpenRouter client for testing."""
    
    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self.response_generator = MockResponseGenerator()
        self.usage_history = []
        self.call_count = 0
        self.should_fail = False
        self.failure_rate = 0.0
        
        logger.info("Mock OpenRouter client initialized")
    
    def generate_response(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> MockAPIResponse:
        """Generate a mock API response."""
        self.call_count += 1
        
        # Simulate occasional failures
        if self.should_fail or (self.failure_rate > 0 and random.random() < self.failure_rate):
            return MockAPIResponse(
                success=False,
                content="",
                usage=None,
                model=model,
                error="Mock API failure for testing"
            )
        
        # Simulate rate limiting occasionally
        if random.random() < 0.05:  # 5% chance
            return MockAPIResponse(
                success=False,
                content="",
                usage=None,
                model=model,
                error="Rate limited",
                retry_after=60
            )
        
        # Extract user query from messages
        user_message = ""
        for msg in messages:
            if msg.get('role') == 'user':
                user_message = msg.get('content', '')
                break
        
        # Determine intent from query (simplified)
        intent = self._classify_intent_simple(user_message)
        
        # Generate response
        response_content = self.response_generator.generate_response(
            intent=intent,
            model=model,
            query=user_message,
            **kwargs
        )
        
        # Generate usage statistics
        usage = self.response_generator.generate_usage_stats(model, len(response_content))
        self.usage_history.append(usage)
        
        # Simulate processing delay
        time.sleep(0.1)  # 100ms delay
        
        return MockAPIResponse(
            success=True,
            content=response_content,
            usage=usage,
            model=model
        )
    
    def _classify_intent_simple(self, query: str) -> str:
        """Simple intent classification for mock responses."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['write', 'create', 'generate', 'implement']):
            return 'code_generation'
        elif any(word in query_lower for word in ['debug', 'error', 'fix', 'bug']):
            return 'debugging'
        elif any(word in query_lower for word in ['explain', 'what', 'how', 'why']):
            return 'explanation'
        elif any(word in query_lower for word in ['optimize', 'improve', 'faster']):
            return 'optimization'
        elif any(word in query_lower for word in ['test', 'unittest', 'pytest']):
            return 'testing'
        elif any(word in query_lower for word in ['document', 'readme', 'docs']):
            return 'documentation'
        elif any(word in query_lower for word in ['read', 'write', 'file', 'csv', 'json']):
            return 'file_operations'
        else:
            return 'general_query'
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Return mock list of available models."""
        return [
            {
                "id": "anthropic/claude-3.5-sonnet",
                "name": "Claude 3.5 Sonnet",
                "pricing": {"input": 0.000003, "output": 0.000015}
            },
            {
                "id": "anthropic/claude-3-haiku",
                "name": "Claude 3 Haiku",
                "pricing": {"input": 0.00000025, "output": 0.00000125}
            },
            {
                "id": "openai/gpt-4-turbo",
                "name": "GPT-4 Turbo",
                "pricing": {"input": 0.00001, "output": 0.00003}
            },
            {
                "id": "openai/gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "pricing": {"input": 0.0000005, "output": 0.0000015}
            }
        ]
    
    def test_connection(self) -> bool:
        """Mock connection test."""
        return not self.should_fail
    
    def get_usage_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get mock usage summary."""
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
    
    def set_failure_mode(self, should_fail: bool = True, failure_rate: float = 0.0):
        """Configure mock failures for testing error handling."""
        self.should_fail = should_fail
        self.failure_rate = failure_rate

class MockTestRunner:
    """Test runner that uses mock components."""
    
    def __init__(self, config_dir: str = "../config"):
        self.config_dir = config_dir
        self.mock_client = MockOpenRouterClient(config_dir)
        self.test_results = []
    
    def run_intent_classification_tests(self) -> Dict[str, Any]:
        """Test intent classification with mock responses."""
        test_cases = [
            ("write a python function to sort a list", "code_generation"),
            ("debug this error in my code", "debugging"),
            ("explain how binary search works", "explanation"),
            ("optimize this slow algorithm", "optimization"),
            ("write unit tests for this function", "testing"),
            ("create documentation for this API", "documentation"),
            ("read data from a CSV file", "file_operations"),
            ("what is machine learning", "general_query")
        ]
        
        correct = 0
        results = []
        
        for query, expected_intent in test_cases:
            predicted_intent = self.mock_client._classify_intent_simple(query)
            is_correct = predicted_intent == expected_intent
            
            if is_correct:
                correct += 1
            
            results.append({
                "query": query,
                "expected": expected_intent,
                "predicted": predicted_intent,
                "correct": is_correct
            })
        
        accuracy = correct / len(test_cases)
        
        return {
            "accuracy": accuracy,
            "correct": correct,
            "total": len(test_cases),
            "results": results
        }
    
    def run_api_response_tests(self) -> Dict[str, Any]:
        """Test API response generation."""
        test_queries = [
            "write a hello world program",
            "fix this syntax error",
            "explain recursion",
            "optimize this loop"
        ]
        
        results = []
        
        for query in test_queries:
            messages = [{"role": "user", "content": query}]
            
            response = self.mock_client.generate_response(
                model="anthropic/claude-3-haiku",
                messages=messages
            )
            
            results.append({
                "query": query,
                "success": response.success,
                "has_content": bool(response.content),
                "has_usage": response.usage is not None,
                "response_length": len(response.content) if response.content else 0
            })
        
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        
        return {
            "success_rate": success_rate,
            "total_tests": len(results),
            "results": results
        }
    
    def run_error_handling_tests(self) -> Dict[str, Any]:
        """Test error handling with mock failures."""
        # Test normal operation
        self.mock_client.set_failure_mode(False)
        normal_response = self.mock_client.generate_response(
            model="anthropic/claude-3-haiku",
            messages=[{"role": "user", "content": "test query"}]
        )
        
        # Test failure mode
        self.mock_client.set_failure_mode(True)
        failure_response = self.mock_client.generate_response(
            model="anthropic/claude-3-haiku",
            messages=[{"role": "user", "content": "test query"}]
        )
        
        # Test rate limiting (reset failure mode first)
        self.mock_client.set_failure_mode(False, failure_rate=1.0)  # 100% rate limit
        rate_limit_response = self.mock_client.generate_response(
            model="anthropic/claude-3-haiku",
            messages=[{"role": "user", "content": "test query"}]
        )
        
        return {
            "normal_operation": normal_response.success,
            "handles_api_failure": not failure_response.success and failure_response.error,
            "handles_rate_limiting": not rate_limit_response.success and "rate" in rate_limit_response.error.lower(),
            "error_messages_present": all([
                failure_response.error,
                rate_limit_response.error
            ])
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites."""
        print("🧪 Running Atlas Code V5 Mock Tests...")
        
        # Intent classification tests
        print("  Testing intent classification...")
        intent_results = self.run_intent_classification_tests()
        
        # API response tests
        print("  Testing API responses...")
        api_results = self.run_api_response_tests()
        
        # Error handling tests
        print("  Testing error handling...")
        error_results = self.run_error_handling_tests()
        
        # Usage tracking test
        print("  Testing usage tracking...")
        usage_summary = self.mock_client.get_usage_summary()
        
        overall_results = {
            "intent_classification": intent_results,
            "api_responses": api_results,
            "error_handling": error_results,
            "usage_tracking": {
                "tracks_requests": usage_summary["total_requests"] > 0,
                "tracks_costs": usage_summary["total_cost"] > 0,
                "tracks_tokens": usage_summary["total_tokens"] > 0
            },
            "summary": {
                "intent_accuracy": intent_results["accuracy"],
                "api_success_rate": api_results["success_rate"],
                "error_handling_works": all(error_results.values()),
                "overall_health": "PASS" if (
                    intent_results["accuracy"] >= 0.8 and
                    api_results["success_rate"] >= 0.9 and
                    all(error_results.values())
                ) else "FAIL"
            }
        }
        
        return overall_results

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Run comprehensive tests
    test_runner = MockTestRunner()
    results = test_runner.run_all_tests()
    
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    
    summary = results["summary"]
    print(f"Intent Classification Accuracy: {summary['intent_accuracy']:.1%}")
    print(f"API Success Rate: {summary['api_success_rate']:.1%}")
    print(f"Error Handling: {'✅ PASS' if summary['error_handling_works'] else '❌ FAIL'}")
    print(f"Overall Health: {'✅ ' + summary['overall_health'] if summary['overall_health'] == 'PASS' else '❌ ' + summary['overall_health']}")
    
    # Show detailed results
    if results["summary"]["overall_health"] == "FAIL":
        print("\n🔍 Detailed Results:")
        print(json.dumps(results, indent=2, default=str))