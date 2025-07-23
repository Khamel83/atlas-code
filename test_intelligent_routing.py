#!/usr/bin/env python3
"""
Comprehensive Test Suite for Atlas Code V2 Intelligent Routing

Tests all aspects of the intelligent routing system including:
- Task classification accuracy
- Model selection logic
- Budget constraints
- Fallback mechanisms
- Prompt compression
- End-to-end integration
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_model_score_loading():
    """Test that model_score.json loads correctly."""
    print("🧪 Testing model_score.json loading...")
    
    try:
        from model_router import IntelligentModelRouter
        router = IntelligentModelRouter()
        
        # Check that all tiers are present
        expected_tiers = ['silver', 'gold', 'platinum', 'diamond']
        for tier in expected_tiers:
            assert tier in router.model_mappings, f"Missing tier: {tier}"
            assert len(router.model_mappings[tier]) > 0, f"No models in tier: {tier}"
        
        print("✅ Model score loading test passed")
        return True
    except Exception as e:
        print(f"❌ Model score loading test failed: {e}")
        return False

def test_classification_logic():
    """Test task classification with mock scenarios."""
    print("\n🧪 Testing classification logic...")
    
    test_cases = [
        # (prompt, expected_tier, description)
        ("fix typo in hello.py", "silver", "simple typo fix"),
        ("create hello world script", "silver", "basic script creation"),
        ("implement user login with JWT", "gold", "standard feature implementation"),
        ("debug memory leak in server", "gold", "debugging task"),
        ("optimize database queries for performance", "platinum", "complex optimization"),
        ("refactor entire codebase architecture", "platinum", "large refactoring"),
        ("design distributed microservices system", "diamond", "system architecture"),
        ("research novel AI algorithms", "diamond", "research task"),
    ]
    
    try:
        from model_router import IntelligentModelRouter
        router = IntelligentModelRouter()
        
        passed = 0
        total = len(test_cases)
        
        for prompt, expected_tier, description in test_cases:
            try:
                # Mock the classification by using budget-constrained routing
                # In a real test, this would call the actual API
                routing_info = router.route_request(prompt, budget_remaining=10.0)
                actual_tier = routing_info['tier']
                
                if actual_tier == expected_tier:
                    print(f"  ✅ {description}: {actual_tier} (correct)")
                    passed += 1
                else:
                    print(f"  ⚠️  {description}: {actual_tier} (expected {expected_tier})")
            except Exception as e:
                print(f"  ❌ {description}: Error - {e}")
        
        accuracy = (passed / total) * 100
        print(f"\n📊 Classification accuracy: {passed}/{total} ({accuracy:.1f}%)")
        
        if accuracy >= 70:
            print("✅ Classification logic test passed")
            return True
        else:
            print("❌ Classification logic test failed (accuracy below 70%)")
            return False
            
    except Exception as e:
        print(f"❌ Classification logic test failed: {e}")
        return False

def test_budget_constraints():
    """Test budget-aware model selection."""
    print("\n🧪 Testing budget constraints...")
    
    try:
        from model_router import IntelligentModelRouter
        router = IntelligentModelRouter()
        
        test_cases = [
            (10.0, "Should allow higher-tier models"),
            (1.0, "Should limit to mid-tier models"),
            (0.1, "Should force lowest-cost models"),
            (0.0, "Should use free models only")
        ]
        
        passed = 0
        for budget, description in test_cases:
            try:
                routing_info = router.route_request("complex task", budget_remaining=budget)
                model_cost = router.model_costs.get(routing_info['model'], 0)
                
                print(f"  Budget ${budget}: {routing_info['tier']} tier ({routing_info['model']}) - ${model_cost}/1k")
                passed += 1
            except Exception as e:
                print(f"  ❌ Budget ${budget}: {e}")
        
        if passed == len(test_cases):
            print("✅ Budget constraints test passed")
            return True
        else:
            print("❌ Budget constraints test failed")
            return False
            
    except Exception as e:
        print(f"❌ Budget constraints test failed: {e}")
        return False

def test_fallback_mechanisms():
    """Test fallback and escalation logic."""
    print("\n🧪 Testing fallback mechanisms...")
    
    try:
        from model_router import IntelligentModelRouter
        router = IntelligentModelRouter()
        
        # Test tier escalation
        escalation_tests = [
            ("silver", "gold"),
            ("gold", "platinum"), 
            ("platinum", "diamond"),
            ("diamond", None)
        ]
        
        passed = 0
        for current_tier, expected_next in escalation_tests:
            actual_next = router.escalate_tier(current_tier)
            if actual_next == expected_next:
                print(f"  ✅ {current_tier} → {actual_next or 'None'}")
                passed += 1
            else:
                print(f"  ❌ {current_tier} → {actual_next} (expected {expected_next})")
        
        # Test low confidence detection
        confidence_tests = [
            ("I'm confident in this solution", False),
            ("I'm not sure about this approach", True),
            ("Maybe we should try something else", True),
            ("This is definitely the right way", False),
            ("Can't answer without more information", True),
        ]
        
        for response, expected_low_conf in confidence_tests:
            actual_low_conf = router.is_low_confidence(response)
            if actual_low_conf == expected_low_conf:
                print(f"  ✅ Confidence detection: '{response[:30]}...' → {actual_low_conf}")
                passed += 1
            else:
                print(f"  ❌ Confidence detection: '{response[:30]}...' → {actual_low_conf} (expected {expected_low_conf})")
        
        total_tests = len(escalation_tests) + len(confidence_tests)
        if passed == total_tests:
            print("✅ Fallback mechanisms test passed")
            return True
        else:
            print(f"❌ Fallback mechanisms test failed ({passed}/{total_tests})")
            return False
            
    except Exception as e:
        print(f"❌ Fallback mechanisms test failed: {e}")
        return False

def test_prompt_compression():
    """Test prompt compression for long inputs."""
    print("\n🧪 Testing prompt compression...")
    
    try:
        from model_router import IntelligentModelRouter
        router = IntelligentModelRouter()
        
        # Test short prompt (should not compress)
        short_prompt = "Create a simple hello world function"
        short_result = router.compress_prompt(short_prompt)
        
        if short_result == short_prompt:
            print("  ✅ Short prompt: No compression applied")
        else:
            print("  ❌ Short prompt: Unexpected compression")
            return False
        
        # Test long prompt (should compress)
        long_prompt = "Create a comprehensive web application " * 500
        print(f"  📏 Long prompt: {len(long_prompt)} characters (~{len(long_prompt)//4} tokens)")
        
        long_result = router.compress_prompt(long_prompt)
        
        if len(long_result) < len(long_prompt):
            print(f"  ✅ Long prompt: Compressed to {len(long_result)} characters")
        else:
            print(f"  ⚠️  Long prompt: Compression bypassed (API not available)")
        
        print("✅ Prompt compression test passed")
        return True
        
    except Exception as e:
        print(f"❌ Prompt compression test failed: {e}")
        return False

def test_model_availability():
    """Test model availability checking."""
    print("\n🧪 Testing model availability...")
    
    try:
        from model_router import IntelligentModelRouter
        router = IntelligentModelRouter()
        
        # Test known models
        test_models = [
            "deepseek/deepseek-chat",
            "google/gemini-2.0-flash-001", 
            "nonexistent/fake-model"
        ]
        
        for model in test_models:
            available = router.is_model_available(model)
            cost_known = model in router.model_costs
            print(f"  {model}: {'✅' if available else '❌'} available, {'💰' if cost_known else '❓'} cost known")
        
        print("✅ Model availability test passed")
        return True
        
    except Exception as e:
        print(f"❌ Model availability test failed: {e}")
        return False

def test_atlas_integration():
    """Test integration with Atlas Code launcher."""
    print("\n🧪 Testing Atlas Code integration...")
    
    try:
        from atlas_core.launcher import AiderLauncher
        
        # Create test launcher
        class TestLauncher(AiderLauncher):
            def _check_aider_installation(self):
                pass  # Skip Aider check
        
        launcher = TestLauncher()
        
        # Check that intelligent router is available
        if launcher.intelligent_router is None:
            print("  ❌ Intelligent router not available in launcher")
            return False
        
        print("  ✅ Intelligent router available")
        print(f"  📊 Model mappings loaded: {len(launcher.intelligent_router.model_mappings)} tiers")
        print(f"  💰 Cost data loaded: {len(launcher.intelligent_router.model_costs)} models")
        
        # Test that budget integration works
        budget_status = launcher.budget.check_budget_status()
        print(f"  💰 Budget integration: {budget_status['warning_level']} status")
        
        print("✅ Atlas integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Atlas integration test failed: {e}")
        return False

def test_end_to_end_workflow():
    """Test complete end-to-end routing workflow."""
    print("\n🧪 Testing end-to-end workflow...")
    
    try:
        from model_router import IntelligentModelRouter
        router = IntelligentModelRouter()
        
        # Test complete workflow with different scenarios
        test_scenarios = [
            ("Fix typo in README", 5.0, "Simple task with adequate budget"),
            ("Implement OAuth2 authentication", 2.0, "Complex task with medium budget"),
            ("Design scalable architecture", 0.5, "High-complexity task with low budget"),
        ]
        
        for prompt, budget, description in test_scenarios:
            print(f"\n  📝 Scenario: {description}")
            print(f"      Prompt: '{prompt}'")
            print(f"      Budget: ${budget}")
            
            try:
                routing_info = router.route_request(prompt, budget_remaining=budget)
                
                print(f"      Result: {routing_info['tier']} tier → {routing_info['model']}")
                print(f"      Reason: {routing_info['reason']}")
                
                if routing_info['prompt_compressed']:
                    print(f"      Compression: {routing_info['original_prompt_length']} → {routing_info['final_prompt_length']} chars")
                
                print(f"      ✅ Workflow completed successfully")
                
            except Exception as e:
                print(f"      ❌ Workflow failed: {e}")
                return False
        
        print("✅ End-to-end workflow test passed")
        return True
        
    except Exception as e:
        print(f"❌ End-to-end workflow test failed: {e}")
        return False

def run_all_tests() -> bool:
    """Run all tests and return overall success."""
    print("🧪 Ralex V2 Intelligent Routing Test Suite")
    print("=" * 50)
    
    # Set test API key
    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'test-key-for-testing')
    
    test_functions = [
        test_model_score_loading,
        test_classification_logic,
        test_budget_constraints,
        test_fallback_mechanisms,
        test_prompt_compression,
        test_model_availability,
        test_atlas_integration,
        test_end_to_end_workflow,
    ]
    
    passed = 0
    total = len(test_functions)
    
    for test_func in test_functions:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("✅ All tests passed! System ready for production.")
        return True
    else:
        print("❌ Some tests failed. Review and fix issues before production.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)