import pytest
from security.permission_control import (
    PermissionControlSystem,
    PermissionContext,
    PermissionRule,
    PermissionType,
    PermissionLevel,
)


class TestPermissionControlSystem:
    def test_default_initialization(self):
        pcs = PermissionControlSystem(config_path="nonexistent.json")
        assert len(pcs.default_rules) == 6
        assert pcs.audit_log_enabled is True

    def test_default_rule_file_access_read_allowed(self):
        pcs = PermissionControlSystem(config_path="nonexistent.json")
        ctx = PermissionContext(
            user_id="test_user",
            operation="file_access",
            resource="/projects/test.txt",
            action="read",
        )
        assert pcs.check_permission(ctx) is True

    def test_unknown_operation_denied(self):
        pcs = PermissionControlSystem(config_path="nonexistent.json")
        ctx = PermissionContext(
            user_id="test_user",
            operation="unknown_op",
            resource="anything",
            action="any",
        )
        assert pcs.check_permission(ctx) is False

    def test_denied_action_rejected(self):
        pcs = PermissionControlSystem(config_path="nonexistent.json")
        # Sandbox execution denies os/sys/subprocess
        ctx = PermissionContext(
            user_id="test_user",
            operation="sandbox_execution",
            resource="script.py",
            action="os",
        )
        assert pcs.check_permission(ctx) is False

    def test_add_user_rule_overrides_default(self):
        pcs = PermissionControlSystem(config_path="nonexistent.json")
        rule = PermissionRule(
            permission_type=PermissionType.FILE_ACCESS,
            level=PermissionLevel.NONE,
            resource_pattern="/restricted/*",
            allowed_actions=["read"],
        )
        pcs.add_user_rule("test_user", rule)
        ctx = PermissionContext(
            user_id="test_user",
            operation="file_access",
            resource="/restricted/secret.txt",
            action="read",
        )
        assert pcs.check_permission(ctx) is False

    def test_resource_pattern_matching(self):
        pcs = PermissionControlSystem(config_path="nonexistent.json")
        rule = PermissionRule(
            permission_type=PermissionType.FILE_ACCESS,
            level=PermissionLevel.FULL_ACCESS,
            resource_pattern="/tmp/*",
            allowed_actions=["read", "write"],
        )
        pcs.add_user_rule("user2", rule)
        ctx = PermissionContext(
            user_id="user2",
            operation="file_access",
            resource="/tmp/test.txt",
            action="write",
        )
        assert pcs.check_permission(ctx) is True

    def test_save_and_load_configuration(self, tmp_path):
        config_file = tmp_path / "test_perm_config.json"
        pcs = PermissionControlSystem(config_path=str(config_file))
        rule = PermissionRule(
            permission_type=PermissionType.NETWORK_ACCESS,
            level=PermissionLevel.READ_ONLY,
            resource_pattern="*",
            allowed_actions=["connect"],
        )
        pcs.add_user_rule("agent1", rule)
        pcs.save_configuration()
        assert config_file.exists()

        pcs2 = PermissionControlSystem(config_path=str(config_file))
        assert "agent1" in pcs2.rules
        assert len(pcs2.rules["agent1"]) == 1

    def test_audit_logging_disabled(self):
        pcs = PermissionControlSystem(config_path="nonexistent.json")
        pcs.audit_log_enabled = False
        ctx = PermissionContext(
            user_id="test_user",
            operation="file_access",
            resource="/test.txt",
            action="read",
        )
        # Should not raise
        assert pcs.check_permission(ctx) is True

    def test_none_level_denies(self):
        pcs = PermissionControlSystem(config_path="nonexistent.json")
        rule = PermissionRule(
            permission_type=PermissionType.FILE_ACCESS,
            level=PermissionLevel.NONE,
            resource_pattern="*",
            allowed_actions=["read"],
        )
        pcs.add_user_rule("blocked_user", rule)
        ctx = PermissionContext(
            user_id="blocked_user",
            operation="file_access",
            resource="/any/file.txt",
            action="read",
        )
        assert pcs.check_permission(ctx) is False
