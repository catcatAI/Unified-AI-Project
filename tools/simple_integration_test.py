#!/usr/bin/env python3
"""
Simple integration test for the Unified AI Project
Tests the integration of major components without complex imports
"""

import sys
from pathlib import Path

# Add the backend src directory to the path
backend_src = Path(__file__).parent.parent / "apps" / "backend" / "src"
_ = sys.path.insert(0, str(backend_src))

def test_security_components() -> None:
    """Test security components functionality"""
    _ = print("Testing security components...")
    
    try:
        from security.permission_control import PermissionControlSystem, PermissionContext, PermissionType
        from security.enhanced_sandbox import EnhancedSandboxExecutor, SandboxConfig
        
        # Test permission control
        permission_system = PermissionControlSystem()
        context = PermissionContext(
            user_id="test_user",
            operation=PermissionType.FILE_ACCESS.value,
            resource="/test/file.txt",
            action="read"
        )
        permission_result = permission_system.check_permission(context)
        _ = print(f"  Permission check result: {permission_result}")
        
        # Test audit logging
        audit_logger = AuditLogger()
        audit_logger.log_operation(
            user_id="test_user",
            operation="test_operation",
            resource="test_resource",
            action="test_action",
            success=True
        )
        _ = print(f"  Audit log recorded {len(audit_logger.log_buffer)} events")
        
        # Test sandbox
        sandbox_config = SandboxConfig()
        sandbox = EnhancedSandboxExecutor(sandbox_config)
        test_code = '''
class TestClass:
    def test_method(self, data) -> None:
        return {"result": "success", "data": data}
'''
        result, error = sandbox._validate_code(test_code)
        _ = print(f"  Sandbox code validation: {result}, {error}")
        
        _ = print("Security components test passed!")
        return True
    except Exception as e:
        _ = print(f"Error during security components test: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

def test_service_components() -> None:
    """Test service components functionality"""
    _ = print("Testing service components...")
    
    try:
        from apps.backend.src.core.services.ai_editor import AIEditorService
        from integrations.enhanced_atlassian_bridge import EnhancedAtlassianBridge
        
        # Test AI Editor
        editor_service = AIEditorService()
        test_data = {"text": "This is a test text for processing."}
        processed_data = editor_service.process_data(test_data)
        _ = print(f"  AI Editor processed data: {processed_data is not None}")
        
        # Test Atlassian Bridge (initialization only)
        atlassian_bridge = EnhancedAtlassianBridge()
        _ = print(f"  Atlassian Bridge initialized: {atlassian_bridge is not None}")
        
        _ = print("Service components test passed!")
        return True
    except Exception as e:
        _ = print(f"Error during service components test: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

def test_tool_components() -> None:
    """Test tool components functionality"""
    _ = print("Testing tool components...")
    
    try:
        from apps.backend.src.core.tools.tool_dispatcher import ToolDispatcher
        
        # Test Tool Dispatcher
        tool_dispatcher = ToolDispatcher()
        _ = print(f"  Tool Dispatcher initialized: {tool_dispatcher is not None}")
        
        _ = print("Tool components test passed!")
        return True
    except Exception as e:
        _ = print(f"Error during tool components test: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

def main() -> None:
    """Main test function"""
    _ = print("Simple System Integration Test")
    print("=" * 40)
    _ = print()
    
    # Run all tests
    try:
        test1 = test_security_components()
        test2 = test_service_components()
        test3 = test_tool_components()
        
        if test1 and test2 and test3:
            _ = print("\nAll simple integration tests completed successfully!")
            return True
        else:
            _ = print("\nSome simple integration tests failed!")
            return False
    except Exception as e:
        _ = print(f"Error during simple integration testing: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)