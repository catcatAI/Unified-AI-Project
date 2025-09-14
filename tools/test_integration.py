#!/usr/bin/env python3
"""
Test script for system integration
"""

import sys
import json
from pathlib import Path

# Add the backend src directory to the path
backend_src = Path(__file__).parent.parent / "apps" / "backend" / "src"
sys.path.insert(0, str(backend_src))

def test_system_initialization():
    """Test system initialization"""
    print("Testing system initialization...")
    
    try:
        from system_integration import UnifiedAISystem
        
        # Create unified AI system
        unified_ai = UnifiedAISystem()
        
        # Check that all components are initialized
        assert hasattr(unified_ai, 'agent_manager'), "Agent manager not initialized"
        assert hasattr(unified_ai, 'execution_manager'), "Execution manager not initialized"
        assert hasattr(unified_ai, 'ham_memory_manager'), "HAM memory manager not initialized"
        assert hasattr(unified_ai, 'multi_llm_service'), "Multi LLM service not initialized"
        assert hasattr(unified_ai, 'ai_editor_service'), "AI editor service not initialized"
        assert hasattr(unified_ai, 'atlassian_bridge'), "Atlassian bridge not initialized"
        assert hasattr(unified_ai, 'permission_control'), "Permission control not initialized"
        assert hasattr(unified_ai, 'audit_logger'), "Audit logger not initialized"
        assert hasattr(unified_ai, 'sandbox_executor'), "Sandbox executor not initialized"
        assert hasattr(unified_ai, 'tool_dispatcher'), "Tool dispatcher not initialized"
        
        print("System initialization test passed!")
        return True
    except Exception as e:
        print(f"Error during system initialization test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_request_processing():
    """Test request processing"""
    print("Testing request processing...")
    
    try:
        from system_integration import UnifiedAISystem
        
        # Create unified AI system
        unified_ai = UnifiedAISystem()
        
        # Test dialogue request
        dialogue_request = {
            "type": "dialogue",
            "message": "Hello, how can you help me today?",
            "context": {}
        }
        
        result = unified_ai.process_request("test_user", dialogue_request)
        print(f"Dialogue request result: {result}")
        
        # Test tool request
        tool_request = {
            "type": "tool_execution",
            "tool_name": "calculator",
            "tool_params": {"operation": "add", "a": 5, "b": 3}
        }
        
        result = unified_ai.process_request("test_user", tool_request)
        print(f"Tool request result: {result}")
        
        # Test Atlassian request
        atlassian_request = {
            "type": "atlassian_operation",
            "operation": "get_jira_projects",
            "params": {}
        }
        
        result = unified_ai.process_request("test_user", atlassian_request)
        print(f"Atlassian request result: {result}")
        
        # Test editor request
        editor_request = {
            "type": "ai_editor_operation",
            "operation": "process_data",
            "params": {"data": {"text": "Sample text for processing"}}
        }
        
        result = unified_ai.process_request("test_user", editor_request)
        print(f"Editor request result: {result}")
        
        print("Request processing test passed!")
        return True
    except Exception as e:
        print(f"Error during request processing test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("System Integration Test")
    print("=" * 30)
    print()
    
    # Run all tests
    try:
        test1 = test_system_initialization()
        test2 = test_request_processing()
        
        if test1 and test2:
            print("\nAll integration tests completed successfully!")
            return True
        else:
            print("\nSome integration tests failed!")
            return False
    except Exception as e:
        print(f"Error during integration testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)