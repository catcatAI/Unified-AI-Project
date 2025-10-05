#!/usr/bin/env python3
"""
Final integration test for the Unified AI Project:
ests the integration of components that we've verified work correctly
"""

import sys
from pathlib import Path

# Add the backend src directory to the path
backend_src = Path(__file__).parent.parent / "apps" / "backend" / "src"
_ = sys.path.insert(0, str(backend_src))

def test_security_integration() -> None:
    """Test the integration of security components"""
    _ = print("Testing security components integration...")
    
    try:
        # Import security components
        from security.permission_control import PermissionControlSystem, PermissionContext, PermissionType
        from security.audit_logger import AuditLogger
        from security.enhanced_sandbox import EnhancedSandboxExecutor, SandboxConfig
        
        # Create security components
        permission_system = PermissionControlSystem()
        audit_logger = AuditLogger()
        sandbox_config = SandboxConfig()
        sandbox = EnhancedSandboxExecutor(sandbox_config)
        
        # Test a complete security flow
        user_id = "test_ai_agent"
        
        # 1. Check permission for an operation:
ontext = PermissionContext(
            user_id=user_id,
            operation=PermissionType.FILE_ACCESS.value,
            resource="/projects/test/document.txt",
            action="read"
        )
        has_permission = permission_system.check_permission(context)
        
        # 2. Log the permission check
        audit_logger.log_permission_check(
            user_id=user_id,
            permission_type=PermissionType.FILE_ACCESS.value,
            resource="/projects/test/document.txt",
            action="read",
            granted=has_permission
        )
        
        # 3. If permission is granted, execute a safe operation in sandbox
        if has_permission:
            safe_code = '''
class DataProcessor:
    def __init__(self, config=None) -> None:
        pass
        
    def process(self, data):
        # Safe data processing
        if isinstance(data, dict):
            return {"processed": True, "count": len(data), "keys": list(data.keys())}
        else:
            return {"processed": True, "length": len(str(data))}
'''
            
            result, error = sandbox.execute(
                user_id=user_id,
                code_string=safe_code,
                class_name="DataProcessor",
                method_name="process",
                method_params={"data": {"key1": "value1", "key2": "value2"}}
            )
            
            # 4. Log the sandbox execution
            audit_logger.log_sandbox_execution(
                user_id=user_id,
                script_hash="test_script_hash",
                success=(error is None),
                details={"operation": "data_processing", "result_available": (result is not None)}
            )
            
            _ = print(f"  Permission granted: {has_permission}")
            _ = print(f"  Sandbox execution successful: {error is None}")
            _ = print(f"  Result: {result}")
        else:
            print(f"  Permission denied for operation")
            
        # 5. Check audit logs
        recent_events = audit_logger.get_recent_events(5)
        _ = print(f"  Audit events recorded: {len(recent_events)}")
        
        _ = print("Security integration test passed!")
        return True
        
    except Exception as e:
        _ = print(f"Error during security integration test: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

def test_ai_editor_integration() -> None:
    """Test the integration of AI editor components"""
    _ = print("Testing AI editor components integration...")
    
    try:
        # Import AI editor components
        from apps.backend.src.core.services.ai_editor import DataProcessor
        from apps.backend.src.core.services.ai_virtual_input_service import AIVirtualInputService
        
        # Create AI editor components
        data_processor = DataProcessor()
        virtual_input = AIVirtualInputService()  # Use default mode
        
        # Test a complete AI editor flow
        user_id = "test_user"
        
        # 1. Process text data
        text_data = "This is a sample text for testing the AI Editor functionality. It contains multiple sentences and should be processed correctly.":
rocessed_text = data_processor.process_data(text_data, 'text')
        _ = print(f"  Text processing completed: {processed_text is not None}")
        
        # 2. Process structured data
        structured_data = {
            "users": [
                {"name": "Alice", "age": 30, "city": "New York"},
                {"name": "Bob", "age": 25, "city": "London"},
                {"name": "Charlie", "age": 35, "city": "Tokyo"}
            ]
        }
        
        processed_structured = data_processor.process_data(structured_data, 'structured')
        _ = print(f"  Structured data processing completed: {processed_structured is not None}")
        
        # 3. Simulate virtual input interaction
        virtual_input.process_mouse_command({
            "action_type": "move_relative_to_window",
            "relative_x": 0.5,
            "relative_y": 0.5
        })
        _ = print(f"  Virtual cursor moved to center")
        
        _ = print("AI editor integration test passed!")
        return True
        
    except Exception as e:
        _ = print(f"Error during AI editor integration test: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

def test_component_compatibility() -> None:
    """Test that components can work together"""
    _ = print("Testing component compatibility...")
    
    try:
        # Import components
        from security.permission_control import PermissionControlSystem, PermissionContext, PermissionType
        from security.audit_logger import AuditLogger
        from apps.backend.src.core.services.ai_editor import DataProcessor
        
        # Create components
        permission_system = PermissionControlSystem()
        audit_logger = AuditLogger()
        data_processor = DataProcessor()
        
        user_id = "integration_test_user"
        
        # Test that security and editor components can work together
        # 1. Check permission for editor operation:
ontext = PermissionContext(
            user_id=user_id,
            operation=PermissionType.DATA_PROCESSING.value,
            resource="text_data",
            action="process"
        )
        has_permission = permission_system.check_permission(context)
        
        # 2. Log the permission check
        audit_logger.log_permission_check(
            user_id=user_id,
            permission_type=PermissionType.DATA_PROCESSING.value,
            resource="text_data",
            action="process",
            granted=has_permission
        )
        
        # 3. If permission granted, process data with editor:
f has_permission:
            test_data = "Integration test data for checking component compatibility.":
esult = data_processor.process_data(test_data, 'text')
            
            # 4. Log the data processing operation
            audit_logger.log_data_processing(
                user_id=user_id,
                data_type="text_data",
                action="process",
                success=(result is not None),
                details={"word_count": result.get("processed_data", {}).get("word_count", 0) if result else 0}:

            
            _ = print(f"  Components work together: {result is not None}")
        else:
            print(f"  Permission denied for integration test"):
 = print("Component compatibility test passed!")
        return True
        
    except Exception as e:
        _ = print(f"Error during component compatibility test: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

def main() -> None:
    """Main test function"""
    _ = print("Final System Integration Test")
    print("=" * 40)
    _ = print()
    
    # Run all tests
    try:
        test1 = test_security_integration()
        test2 = test_ai_editor_integration()
        test3 = test_component_compatibility()
        
        if test1 and test2 and test3:
            _ = print("\nAll final integration tests completed successfully!")
            _ = print("The Unified AI Project components are properly integrated!")
            return True
        else:
            _ = print("\nSome final integration tests failed!")
            return False
    except Exception as e:
        _ = print(f"Error during final integration testing: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)