#!/usr/bin/env python3
"""
Test Script for Atlas Code Systematic Handover System

This script validates the core functionality of the handover system
to ensure all components work correctly together.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_handover_manager():
    """Test HandoverManager basic functionality"""
    print("🧪 Testing HandoverManager...")
    
    try:
        from aider.handover_manager import HandoverManager
        from aider.io import InputOutput
        
        # Create mock IO
        io = InputOutput(pretty=False, yes=True)
        
        # Initialize manager
        manager = HandoverManager(io=io)
        
        # Test state capture
        state = manager.capture_current_state(
            coder=None,
            reason="test",
            trigger="unit_test"
        )
        
        print(f"✅ State captured: {state.session_id}")
        
        # Test state validation
        validation = manager.validate_handover_readiness(state)
        print(f"✅ Validation score: {validation.get('readiness_score', 0):.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ HandoverManager test failed: {e}")
        return False


def test_production_validator():
    """Test ProductionValidator functionality"""
    print("🧪 Testing ProductionValidator...")
    
    try:
        from aider.production_validator import ProductionReadinessValidator
        from aider.io import InputOutput
        
        # Create mock IO
        io = InputOutput(pretty=False, yes=True)
        
        # Initialize validator
        validator = ProductionReadinessValidator(io=io, root_path=os.getcwd())
        
        # Run validation
        result = validator.validate_project(coder=None)
        
        print(f"✅ Validation completed: {result.overall_status}")
        print(f"✅ Readiness score: {result.readiness_score:.1%}")
        print(f"✅ Checks: {result.total_checks} total, {result.passed_checks} passed")
        
        return True
        
    except Exception as e:
        print(f"❌ ProductionValidator test failed: {e}")
        return False


def test_github_integration():
    """Test GitHub integration (basic functionality)"""
    print("🧪 Testing GitHub integration...")
    
    try:
        from aider.github_integration import GitHubHandoverIntegration
        from aider.io import InputOutput
        
        # Create mock IO
        io = InputOutput(pretty=False, yes=True)
        
        # Initialize GitHub integration
        github = GitHubHandoverIntegration(io=io, project_root=os.getcwd())
        
        # Test repository info
        repo_info = github.get_github_repository_info()
        
        print(f"✅ Repository info retrieved")
        print(f"   Has remote: {repo_info['has_remote']}")
        print(f"   Is GitHub: {repo_info['is_github']}")
        
        if repo_info['remote_url']:
            print(f"   Remote URL: {repo_info['remote_url']}")
        
        return True
        
    except Exception as e:
        print(f"❌ GitHub integration test failed: {e}")
        return False


def test_handover_state_file():
    """Test handover state file creation and validation"""
    print("🧪 Testing handover state file handling...")
    
    try:
        from aider.handover_manager import HandoverManager
        from aider.io import InputOutput
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Create mock IO
                io = InputOutput(pretty=False, yes=True)
                
                # Initialize manager
                manager = HandoverManager(io=io)
                
                # Capture and save state
                state = manager.capture_current_state(
                    coder=None,
                    reason="test_file_handling",
                    trigger="unit_test"
                )
                
                state_file = manager.save_handover_state(state)
                print(f"✅ State file created: {state_file}")
                
                # Verify file exists and is valid JSON
                assert os.path.exists(state_file), "State file not created"
                
                with open(state_file, 'r') as f:
                    loaded_state = json.load(f)
                
                print(f"✅ State file is valid JSON")
                print(f"   Session ID: {loaded_state.get('session_id', 'unknown')}")
                
                # Test loading state
                loaded_state_obj = manager.load_handover_state(state_file)
                assert loaded_state_obj is not None, "Could not load state"
                
                print(f"✅ State loaded successfully")
                
                return True
                
            finally:
                os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Handover state file test failed: {e}")
        return False


def test_loop_integration():
    """Test loop.py integration capabilities"""
    print("🧪 Testing loop.py integration...")
    
    try:
        # Import the CodeAgent class from loop.py
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Test if loop.py can be imported (handover components)
        import loop
        
        # Test CodeAgent instantiation with handover
        agent = loop.CodeAgent(
            auto_commit=False,
            dry_run=True,
            enable_handover=True
        )
        
        print(f"✅ CodeAgent created with handover enabled")
        print(f"   Handover enabled: {agent.enable_handover}")
        print(f"   Session start time: {agent.session_start_time}")
        
        # Test handover status method
        if hasattr(agent, '_show_handover_status'):
            print(f"✅ Handover status method available")
        
        # Test instruction processing
        result = agent.process_instruction("handover status")
        print(f"✅ Handover instruction processing: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Loop.py integration test failed: {e}")
        return False


def test_commands_integration():
    """Test commands integration"""
    print("🧪 Testing commands integration...")
    
    try:
        from aider.commands import Commands
        from aider.io import InputOutput
        
        # Create mock IO
        io = InputOutput(pretty=False, yes=True)
        
        # Create commands instance (without coder for basic test)
        commands = Commands(io=io, coder=None)
        
        # Test if handover commands exist
        handover_commands = [
            'cmd_handover',
            'cmd_handover_status', 
            'cmd_handover_list',
            'cmd_handover_cleanup',
            'cmd_handover_rename',
            'cmd_production'
        ]
        
        available_commands = []
        for cmd in handover_commands:
            if hasattr(commands, cmd):
                available_commands.append(cmd)
        
        print(f"✅ Available handover commands: {len(available_commands)}/{len(handover_commands)}")
        for cmd in available_commands:
            print(f"   - {cmd}")
        
        return len(available_commands) == len(handover_commands)
        
    except Exception as e:
        print(f"❌ Commands integration test failed: {e}")
        return False


def run_all_tests():
    """Run all handover system tests"""
    print("🚀 Starting Atlas Code Handover System Tests")
    print("=" * 60)
    
    tests = [
        ("HandoverManager", test_handover_manager),
        ("ProductionValidator", test_production_validator),
        ("GitHub Integration", test_github_integration),
        ("Handover State Files", test_handover_state_file),
        ("Loop.py Integration", test_loop_integration),
        ("Commands Integration", test_commands_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<10} {test_name}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed ({passed/total:.1%})")
    
    if passed == total:
        print("\n🎉 All tests passed! The handover system is ready for use.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)