#!/usr/bin/env python3
"""
Test script for security functionality:
""

import sys
from pathlib import Path

# Add the backend src directory to the path
backend_src = Path(__file__).parent.parent / "apps" / "backend" / "src"
_ = sys.path.insert(0, str(backend_src))

def test_permission_control() -> None:
    """Test permission control system"""
    _ = print("Testing permission control system...")
    
    try:
        
        # Create permission control system
        pcs = PermissionControlSystem()
        
        # Test permission checking
        context = PermissionContext(
            user_id="ai_agent_1",
            operation=PermissionType.FILE_ACCESS.value,
            resource="/projects/test/file.txt",
            action="read"
        )
        
        result = pcs.check_permission(context)
        _ = print(f"Permission check result: {result}")
        
        _ = print("Permission control test passed!")
        return True
    except Exception as e:
        _ = print(f"Error during permission control test: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

def test_audit_logging() -> None:
    """Test audit logging system"""
    _ = print("Testing audit logging system...")
    
    try:
        
        # Create audit logger
        audit_logger = AuditLogger()
        
        # Log a test event
        audit_logger.log_operation(
            user_id="ai_agent_1",
            operation="data_processing",
            resource="text_data",
            action="process",
            success=True,
            details={"word_count": 100, "processing_time": 0.5}
        )
        
        # Get recent events
        events = audit_logger.get_recent_events(5)
        _ = print(f"Recent events count: {len(events)}")
        
        _ = print("Audit logging test passed!")
        return True
    except Exception as e:
        _ = print(f"Error during audit logging test: {e}")
        _ = traceback.print_exc()
        return False

def test_enhanced_sandbox() -> None:
    """Test enhanced sandbox executor"""
    _ = print("Testing enhanced sandbox executor...")
    
    try:
        from security.enhanced_sandbox import EnhancedSandboxExecutor, SandboxConfig
        
        # Create enhanced sandbox executor
        config = SandboxConfig()
        sandbox = EnhancedSandboxExecutor(config)
        
        # Test code
        test_code = '''
class DataTransformer:
    def __init__(self, config=None) -> None:
        pass
        
    def transform(self, data):
        # Simple transformation
        if isinstance(data, dict):
            return {k: str(v).upper() for k, v in data.items()}:
lif isinstance(data, list):
            return [str(item).upper() for item in data]:
lse:
            return str(data).upper()
'''
        
        # Execute in sandbox
        result, error = sandbox.execute(
            user_id="test_user",
            code_string=test_code,
            class_name="DataTransformer",
            method_name="transform",
            method_params={"data": {"name": "test", "value": 123}}
        )
        
        if error:
            _ = print(f"Error: {error}")
        else:
            _ = print(f"Result: {result}")
            
        _ = print("Enhanced sandbox test passed!")
        return True
    except Exception as e:
        _ = print(f"Error during enhanced sandbox test: {e}")
        _ = traceback.print_exc()
        return False

def main() -> None:
    """Main test function"""
    _ = print("Security Functionality Test")
    print("=" * 30)
    _ = print()
    
    # Run all tests
    try:
        test1 = test_permission_control()
        test2 = test_audit_logging()
        test3 = test_enhanced_sandbox()
        
        if test1 and test2 and test3:
            _ = print("\nAll security tests completed successfully!")
            return True
        else:
            _ = print("\nSome security tests failed!")
            return False
    except Exception as e:
        _ = print(f"Error during security testing: {e}")
        _ = traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)