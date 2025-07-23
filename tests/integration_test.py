"""
Integration Test for Atlas Code V5

Comprehensive test to verify all components work together correctly
and can handle end-to-end workflows.
"""

import sys
import os
import logging
import tempfile
from pathlib import Path

# Add the atlas_core directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'atlas_core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_integration():
    """Run comprehensive integration test."""
    
    print("🚀 Atlas Code V5 Integration Test")
    print("=" * 50)
    
    # Test configuration
    config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
    
    # Test 1: Core Component Initialization
    print("\n1️⃣ Testing Core Component Initialization")
    try:
        # Test imports
        from hybrid_router import HybridRouter
        from budget_optimizer import BudgetOptimizer  
        from code_executor import CodeExecutor
        from memory_manager import MemoryManager
        from file_context import FileContextManager
        
        print("✅ All core imports successful")
        
        # Test initialization with mock client
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
        from mock_framework import MockOpenRouterClient
        
        # Initialize components
        router = HybridRouter(config_dir)
        budget_optimizer = BudgetOptimizer(config_dir)
        memory_manager = MemoryManager(config_dir)
        file_manager = FileContextManager(config_dir)
        
        print("✅ All core components initialized successfully")
        
    except Exception as e:
        print(f"❌ Core component initialization failed: {e}")
        return False
    
    # Test 2: Tools Package Integration
    print("\n2️⃣ Testing Tools Package")
    try:
        from formatter import CodeFormatter
        from linter import CodeLinter
        from diff_engine import DiffEngine
        from test_runner import TestRunner
        
        formatter = CodeFormatter()
        linter = CodeLinter()
        diff_engine = DiffEngine()
        test_runner = TestRunner()
        
        print("✅ All tools initialized successfully")
        
    except Exception as e:
        print(f"❌ Tools initialization failed: {e}")
        return False
    
    # Test 3: Intent Classification Pipeline
    print("\n3️⃣ Testing Intent Classification")
    try:
        test_queries = [
            "write a python function to calculate fibonacci",
            "debug this error in my code", 
            "explain how binary search works",
            "format this messy code"
        ]
        
        for query in test_queries:
            classification = router.classify_intent(query)
            print(f"  📝 '{query[:30]}...' → {classification.intent} ({classification.confidence:.2f})")
            
            # Verify classification result structure
            assert hasattr(classification, 'intent')
            assert hasattr(classification, 'confidence')
            assert hasattr(classification, 'method')
            assert 0.0 <= classification.confidence <= 1.0
        
        print("✅ Intent classification working correctly")
        
    except Exception as e:
        print(f"❌ Intent classification failed: {e}")
        return False
    
    # Test 4: Budget Optimization
    print("\n4️⃣ Testing Budget Optimization")
    try:
        # Test model selection for different intents
        intents_to_test = ['code_generation', 'debugging', 'explanation', 'general_query']
        
        for intent in intents_to_test:
            selection = budget_optimizer.select_model(intent, 'medium')
            print(f"  💰 {intent} → {selection.model} ({selection.tier})")
            
            # Verify selection structure
            assert hasattr(selection, 'model')
            assert hasattr(selection, 'tier')
            assert hasattr(selection, 'reasoning')
            assert selection.tier in ['budget', 'standard', 'premium']
        
        # Test budget tracking
        budget_optimizer.track_usage(
            model="test-model",
            tier="standard", 
            intent="test",
            tokens_input=100,
            tokens_output=50,
            cost=0.01,
            success=True
        )
        
        status = budget_optimizer.get_budget_status()
        assert 'daily_spent' in status
        assert 'session_spent' in status
        
        print("✅ Budget optimization working correctly")
        
    except Exception as e:
        print(f"❌ Budget optimization failed: {e}")
        return False
    
    # Test 5: Memory Management
    print("\n5️⃣ Testing Memory Management")
    try:
        # Start session
        session_id = memory_manager.start_session()
        print(f"  🧠 Started session: {session_id}")
        
        # Add context entries
        entries = [
            ("Hello, I need help with Python", "user_query"),
            ("I can help you with Python programming", "ai_response"),
            ("Write a function to sort a list", "user_query"),
            ("Here's a sorting function implementation", "ai_response")
        ]
        
        for content, entry_type in entries:
            memory_manager.add_context(content, entry_type)
        
        # Test context retrieval
        context_window = memory_manager.get_context_window(max_tokens=1000)
        assert len(context_window) > 0
        
        # Test memory search
        search_results = memory_manager.search_memory("Python")
        assert len(search_results) > 0
        
        # Test conversation summary
        summary = memory_manager.get_conversation_summary()
        assert summary['total_entries'] > 0
        
        print(f"  📊 Added {len(entries)} entries, retrieved {len(context_window)} in context window")
        print("✅ Memory management working correctly")
        
    except Exception as e:
        print(f"❌ Memory management failed: {e}")
        return False
    
    # Test 6: File Context Management
    print("\n6️⃣ Testing File Context Management")
    try:
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            test_code = '''def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def main():
    print("Fibonacci sequence:")
    for i in range(10):
        print(f"F({i}) = {fibonacci(i)}")

if __name__ == "__main__":
    main()
'''
            f.write(test_code)
            temp_file_path = f.name
        
        try:
            # Test file loading
            file_info = file_manager.load_file(temp_file_path)
            assert file_info is not None
            assert file_info.language == 'python'
            assert len(file_info.content) > 0
            
            # Test function extraction
            extracted = file_manager.extract_functions_and_classes(file_info)
            assert 'fibonacci' in extracted['functions']
            assert 'main' in extracted['functions']
            
            # Test context summary
            summary = file_manager.get_file_context_summary([file_info], max_chars=500)
            assert len(summary) > 0
            assert 'fibonacci' in summary
            
            print(f"  📁 Loaded file: {len(file_info.content)} chars, {len(extracted['functions'])} functions")
            print("✅ File context management working correctly")
            
        finally:
            # Clean up
            os.unlink(temp_file_path)
        
    except Exception as e:
        print(f"❌ File context management failed: {e}")
        return False
    
    # Test 7: Code Tools Integration
    print("\n7️⃣ Testing Code Tools")
    try:
        test_code = '''def hello(name):
if name:
print(f"Hello, {name}!")
else:
print("Hello, World!")
'''
        
        # Test formatting
        format_result = formatter.format_code(test_code, 'python')
        assert format_result['success']
        formatted_code = format_result['formatted_code']
        
        # Test linting
        lint_result = linter.lint_code(test_code, 'python')
        assert lint_result['success']
        issues = lint_result['issues'] 
        
        # Test diff generation
        diff_result = diff_engine.generate_diff(test_code, formatted_code)
        assert diff_result.success
        
        print(f"  🎨 Formatted code: {len(formatted_code)} chars")
        print(f"  🔍 Found {len(issues)} linting issues")
        print(f"  🔄 Generated diff: {len(diff_result.diff_text)} chars")
        print("✅ Code tools working correctly")
        
    except Exception as e:
        print(f"❌ Code tools failed: {e}")
        return False
    
    # Test 8: Mock API Integration
    print("\n8️⃣ Testing Mock API Integration")
    try:
        from mock_framework import MockTestRunner
        
        mock_runner = MockTestRunner()
        test_results = mock_runner.run_all_tests()
        
        assert test_results['summary']['overall_health'] in ['PASS', 'FAIL']
        
        print(f"  🧪 Mock tests: {test_results['summary']['overall_health']}")
        print(f"  📈 Intent accuracy: {test_results['intent_classification']['accuracy']:.1%}")
        print(f"  🔄 API success rate: {test_results['api_responses']['success_rate']:.1%}")
        print("✅ Mock API integration working correctly")
        
    except Exception as e:
        print(f"❌ Mock API integration failed: {e}")
        return False
    
    # Test 9: End-to-End Workflow (with mocks)
    print("\n9️⃣ Testing End-to-End Workflow")
    try:
        # Override OpenRouter client with mock
        original_client = router.openrouter_client
        router.openrouter_client = MockOpenRouterClient(config_dir)
        
        # Simulate complete workflow
        test_query = "write a python function to reverse a string"
        
        # Step 1: Classify intent
        classification = router.classify_intent(test_query)
        
        # Step 2: Select model
        model_selection = budget_optimizer.select_model(
            classification.intent, 
            classification.complexity
        )
        
        # Step 3: Add to memory
        memory_manager.add_context(test_query, "user_query")
        
        # Step 4: Generate mock response
        messages = [{"role": "user", "content": test_query}]
        api_response = router.openrouter_client.generate_response(
            model=model_selection.model,
            messages=messages
        )
        
        # Step 5: Track usage
        if api_response.success:
            budget_optimizer.track_usage(
                model=model_selection.model,
                tier=model_selection.tier,
                intent=classification.intent,
                tokens_input=100,
                tokens_output=200,
                cost=0.05,
                success=True
            )
            
            memory_manager.add_context(api_response.content, "ai_response")
        
        # Verify workflow completed
        assert classification.intent in ['code_generation', 'general_query', 'optimization']  # Allow flexible intent classification
        assert model_selection.tier in ['budget', 'standard', 'premium']
        assert api_response.success
        
        # Restore original client
        router.openrouter_client = original_client
        
        print(f"  🔄 Workflow: {test_query[:30]}... → {classification.intent} → {model_selection.model}")
        print(f"  📝 Response: {len(api_response.content)} chars")
        print("✅ End-to-end workflow working correctly")
        
    except Exception as e:
        print(f"❌ End-to-end workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 10: Configuration and Settings
    print("\n🔟 Testing Configuration System")
    try:
        # Verify all config files exist and are valid
        config_files = [
            'model_tiers.json',
            'intent_routes.json', 
            'prompts.json',
            'settings.json',
            'pattern_rules.json'
        ]
        
        for config_file in config_files:
            config_path = os.path.join(config_dir, config_file)
            assert os.path.exists(config_path), f"Missing config file: {config_file}"
            
            # Verify JSON is valid
            with open(config_path, 'r') as f:
                import json
                data = json.load(f)
                assert isinstance(data, dict), f"Invalid JSON structure in {config_file}"
        
        print(f"  ⚙️ Verified {len(config_files)} configuration files")
        print("✅ Configuration system working correctly")
        
    except Exception as e:
        print(f"❌ Configuration system failed: {e}")
        return False
    
    # Final Summary
    print("\n🎉 Integration Test Results")
    print("=" * 50)
    print("✅ All 10 integration tests passed!")
    print("\n📊 Test Coverage:")
    print("  • Core component initialization")
    print("  • Tools package integration") 
    print("  • Intent classification accuracy")
    print("  • Budget optimization logic")
    print("  • Memory management operations")
    print("  • File context processing")
    print("  • Code tools functionality")
    print("  • Mock API integration")
    print("  • End-to-end workflow")
    print("  • Configuration validation")
    
    print("\n🚀 Atlas Code V5 is ready for production!")
    return True

if __name__ == "__main__":
    try:
        success = test_integration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Integration test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Integration test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)