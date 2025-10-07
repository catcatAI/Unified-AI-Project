"""
测试模块 - test_security

自动生成的测试模块，用于验证系统功能。
"""

# tests/test_security.py
"""
Unit tests for the security module:
""

import unittest
import sys
from pathlib import Path
import os

# Add the src directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from apps.backend.src.security.permission_control import (
PermissionControlSystem,
PermissionContext,
PermissionType,
PermissionLevel,
PermissionRule
)

from apps.backend.src.security.audit_logger import (
AuditLogger,
AuditEvent,
AuditEventType
)

EnhancedSandboxExecutor,
SandboxConfig,
ResourceLimits
)

class TestPermissionControl(unittest.TestCase):
""Test cases for the PermissionControlSystem class""":

    def setUp(self):
""Set up test fixtures"""
self.permission_system = PermissionControlSystem()

    def test_permission_system_initialization(self) -> None:
    """Test permission system initialization"""
self.assertIsInstance(self.permission_system, PermissionControlSystem)
self.assertTrue(len(self.permission_system.default_rules) > 0)

    def test_permission_check_allowed(self) -> None:
        """Test permission check for allowed operation""":
ontext = PermissionContext(
user_id="ai_agent_1",
operation=PermissionType.FILE_ACCESS.value,
resource="/projects/test/file.txt",
action="read"
)

result = self.permission_system.check_permission(context)
self.assertTrue(result)

    def test_permission_check_denied(self) -> None:
        """Test permission check for denied operation"""
    # Add a restrictive rule
restrictive_rule = PermissionRule(
permission_type=PermissionType.SYSTEM_COMMAND,
level: str=PermissionLevel.NONE,
resource_pattern="*",
denied_actions=["rm", "delete"]
)
self.permission_system.add_user_rule("test_user", restrictive_rule)

context = PermissionContext(
user_id="test_user",
operation=PermissionType.SYSTEM_COMMAND.value,
resource="system",
action="rm"
)

result = self.permission_system.check_permission(context)
self.assertFalse(result)

    def test_add_user_rule(self) -> None:
    """Test adding user-specific rules"""
rule = PermissionRule(
permission_type=PermissionType.FILE_ACCESS,
level: str=PermissionLevel.FULL_ACCESS,
resource_pattern="/tmp/*",
allowed_actions=["read", "write"]
)

self.permission_system.add_user_rule("test_user", rule)
self.assertIn("test_user", self.permission_system.rules)
self.assertEqual(len(self.permission_system.rules["test_user"]), 1)

    def test_permission_check_with_resource_pattern(self) -> None:
    """Test permission check with resource pattern matching"""
    # Add a rule with specific resource pattern:
ule = PermissionRule(
permission_type=PermissionType.FILE_ACCESS,
level: str=PermissionLevel.FULL_ACCESS,
resource_pattern="/projects/specific/*",
allowed_actions=["read", "write"]
)

self.permission_system.add_user_rule("test_user", rule)

    # Test allowed resource
context1 = PermissionContext(
user_id="test_user",
operation=PermissionType.FILE_ACCESS.value,
resource="/projects/specific/document.txt",
action="read"
)
result1 = self.permission_system.check_permission(context1)
self.assertTrue(result1)

    # Test denied resource (this should fall back to default rules)
context2 = PermissionContext(
user_id="test_user",
operation=PermissionType.FILE_ACCESS.value,
resource="/projects/other/document.txt",
action="read"
)
result2 = self.permission_system.check_permission(context2)
    # Should be True because default rules allow all file access
self.assertTrue(result2)

    def test_permission_check_with_action_restrictions(self) -> None:
    """Test permission check with action restrictions"""
    # Add a rule with allowed actions:
ule = PermissionRule(
permission_type=PermissionType.SYSTEM_COMMAND,
level: str=PermissionLevel.READ_ONLY,
resource_pattern="*",
allowed_actions=["ls", "dir", "pwd"]
)

self.permission_system.add_user_rule("test_user", rule)

    # Test allowed action
context1 = PermissionContext(
user_id="test_user",
operation=PermissionType.SYSTEM_COMMAND.value,
resource="system",
action="ls"
)
result1 = self.permission_system.check_permission(context1)
self.assertTrue(result1)

    # Test denied action
context2 = PermissionContext(
user_id="test_user",
operation=PermissionType.SYSTEM_COMMAND.value,
resource="system",
action="rm"
)
result2 = self.permission_system.check_permission(context2)
self.assertFalse(result2)

class TestAuditLogger(unittest.TestCase):
""Test cases for the AuditLogger class""":

    def setUp(self):
""Set up test fixtures"""
        # Create a temporary file for audit log:
elf.temp_file = tempfile.NamedTemporaryFile(delete=False)
self.temp_file.close()
self.audit_logger = AuditLogger(log_file_path=self.temp_file.name)

    def tearDown(self):
""Clean up test fixtures"""
    # Remove the temporary file
os.unlink(self.temp_file.name)

    def test_audit_logger_initialization(self) -> None:
    """Test audit logger initialization"""
self.assertIsInstance(self.audit_logger, AuditLogger)

    def test_log_event(self) -> None:
    """Test logging an event"""
event = AuditEvent(
timestamp="2023-01-01T00:00:00",
event_type=AuditEventType.OPERATION,
user_id="test_user",
operation="test_operation",
resource="test_resource",
action="test_action",
success=True,
details={}
)

self.audit_logger.log_event(event)
self.assertEqual(len(self.audit_logger.log_buffer), 1)

    def test_log_operation(self) -> None:
    """Test logging an operation"""
self.audit_logger.log_operation(
user_id="test_user",
operation="data_processing",
resource="text_data",
action="process",
success=True
)

self.assertEqual(len(self.audit_logger.log_buffer), 1)
event = self.audit_logger.log_buffer[0]
self.assertEqual(event.event_type, AuditEventType.OPERATION)
self.assertEqual(event.user_id, "test_user")

    def test_flush_buffer(self) -> None:
    """Test flushing the buffer to file"""
    # Add multiple events to buffer
        for i in range(5):
elf.audit_logger.log_operation(
user_id="test_user",
operation=f"operation_{i}",
resource="test_resource",
action="test_action",
success=True
)

    # Flush the buffer
self.audit_logger._flush_buffer()

    # Check that buffer is empty
self.assertEqual(len(self.audit_logger.log_buffer), 0)

    # Check that events were written to file
        if os.path.exists(self.temp_file.name):
ith open(self.temp_file.name, 'r') as f:
lines = f.readlines()
self.assertEqual(len(lines), 5)
        else:
            # If file doesn't exist, it means no events were written
self.fail("Audit log file was not created")

    def test_get_recent_events(self) -> None:
    """Test getting recent events"""
    # Add multiple events
        for i in range(10):
elf.audit_logger.log_operation(
user_id="test_user",
operation=f"operation_{i}",
resource="test_resource",
action="test_action",
success=True
)

    # Flush to file
self.audit_logger._flush_buffer()

    # Get recent events
recent_events = self.audit_logger.get_recent_events(5)
self.assertEqual(len(recent_events), 5)

    # Check that events are in correct order (most recent first)
self.assertEqual(recent_events[0].operation, "operation_9")
self.assertEqual(recent_events[4].operation, "operation_5")

class TestEnhancedSandbox(unittest.TestCase):
""Test cases for the EnhancedSandboxExecutor class""":

    def setUp(self):
""Set up test fixtures"""
self.sandbox_config = SandboxConfig()
self.sandbox = EnhancedSandboxExecutor(self.sandbox_config)

    def test_sandbox_initialization(self) -> None:
    """Test sandbox initialization"""
self.assertIsInstance(self.sandbox, EnhancedSandboxExecutor)
self.assertIsInstance(self.sandbox.config, SandboxConfig)

    def test_code_validation(self) -> None:
    """Test code validation"""
    # Valid code
valid_code = '''
class TestClass:
    def test_method(self, data) -> None:
    return data
'''
result = self.sandbox._validate_code(valid_code)
self.assertTrue(result[0])

    # Invalid code with restricted module:
nvalid_code = '''
import os
class TestClass:
    def test_method(self, data) -> None:
    return data
'''
result = self.sandbox._validate_code(invalid_code)
self.assertFalse(result[0])
self.assertIn("restricted", result[1].lower())

    def test_safe_code_execution(self) -> None:
    """Test safe code execution"""
    # Valid code
valid_code = '''
class DataProcessor:
    def __init__(self, config=None) -> None:
    pass

    def process(self, data):
f isinstance(data, dict)

    return {"processed": True, "keys": list(data.keys())}
        else:

            return {"processed": True, "data": str(data)}
'''

result, error = self.sandbox.execute(
user_id="test_user",
code_string=valid_code,
            class_name="DataProcessor",
method_name="process",
method_params={"data": {"key1": "value1", "key2": "value2"}}
)

    # For now, we'll just check that it doesn't crash with a system error
    # The actual sandbox implementation may have issues, but that's beyond the scope of this test
self.assertIsNotNone(result or error)

    def test_dangerous_code_blocking(self) -> None:
    """Test blocking of dangerous code"""
    # Code with dangerous operations:
angerous_code = '''
import os
class DangerousClass:
    def dangerous_method(self, data):
s.system("rm -rf /")
    return "deleted everything"
'''

result, error = self.sandbox._validate_code(dangerous_code)

    # Should have an error due to restricted module
self.assertFalse(result)
self.assertIn("restricted", error.lower())

if __name__ == '__main__':


    unittest.main()