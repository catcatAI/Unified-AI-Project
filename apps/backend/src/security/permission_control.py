# src/security/permission_control.py
"""
Permission Control System for AI Editor
Implements multi-level permission control for AI operations
"""

import logging
from enum import Enum
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import fnmatch

logger: Any = logging.getLogger(__name__)

class PermissionType(Enum)
    """Types of permissions"""
    FILE_ACCESS = "file_access"
    NETWORK_ACCESS = "network_access"
    SYSTEM_COMMAND = "system_command"
    APPLICATION_CONTROL = "application_control"
    DATA_PROCESSING = "data_processing"
    SANDBOX_EXECUTION = "sandbox_execution"

class PermissionLevel(Enum)
    """Permission levels"""
    NONE = 0
    READ_ONLY = 1
    READ_WRITE = 2
    FULL_ACCESS = 3

@dataclass
class PermissionRule:
    """A permission rule"""
    permission_type: PermissionType
    level: PermissionLevel
    resource_pattern: str = "*"  # Wildcard pattern for resources
    allowed_actions: List[str] = field(default_factory=list)
    denied_actions: List[str] = field(default_factory=list)

@dataclass
class PermissionContext:
    """Context for permission checking""":
    user_id: str
    operation: str
    resource: str
    action: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class PermissionControlSystem:
    """Main permission control system"""

    def __init__(self, config_path: str = None) -> None:
    self.rules: Dict[str, List[PermissionRule]] =
    self.default_rules: List[PermissionRule] =
    self.audit_log_enabled = True
    self.config_path = config_path or "configs/permission_config.json"

        # Load configuration if available
    self._load_configuration

        # Set default rules if none loaded
    if not self.default_rules:

    self._set_default_rules

    logger.info("PermissionControlSystem initialized")

    def _load_configuration(self)
    """Load permission configuration from file"""
        try:

            if os.path.exists(self.config_path)


    with open(self.config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

                # Load default rules
                if 'default_rules' in config:

    for rule_data in config['default_rules']:


    rule = PermissionRule(
                            permission_type=PermissionType(rule_data['permission_type']),
                            level=PermissionLevel(rule_data['level: str']),
                            resource_pattern=rule_data.get('resource_pattern', '*'),
                            allowed_actions=rule_data.get('allowed_actions', ),
                            denied_actions=rule_data.get('denied_actions', )
                        )
                        self.default_rules.append(rule)

                # Load user-specific rules
                if 'user_rules' in config:

    for user_id, rules_data in config['user_rules'].items:


    self.rules[user_id] =
                        for rule_data in rules_data:

    rule = PermissionRule(
                                permission_type=PermissionType(rule_data['permission_type']),
                                level=PermissionLevel(rule_data['level: str']),
                                resource_pattern=rule_data.get('resource_pattern', '*'),
                                allowed_actions=rule_data.get('allowed_actions', ),
                                denied_actions=rule_data.get('denied_actions', )
                            )
                            self.rules[user_id].append(rule)

                logger.info(f"Loaded permission configuration from {self.config_path}")
        except Exception as e:

            logger.error(f"Error loading permission configuration: {e}")

    def _set_default_rules(self)
    """Set default permission rules"""
        # Default rules for development environment
    self.default_rules = [
            # Allow file access to project directories with read-write access
    PermissionRule(
                permission_type=PermissionType.FILE_ACCESS,
                level=PermissionLevel.READ_WRITE,
                resource_pattern="**/*",
                allowed_actions=["read", "write", "create", "delete"]
            ),

            # Allow network access to localhost only
            PermissionRule(
                permission_type=PermissionType.NETWORK_ACCESS,
                level=PermissionLevel.READ_ONLY,
                resource_pattern="127.0.0.1:*",
                allowed_actions=["connect"]
            ),

            # Allow system commands with restrictions
    PermissionRule(
                permission_type=PermissionType.SYSTEM_COMMAND,
                level=PermissionLevel.READ_ONLY,
                resource_pattern="*",
                allowed_actions=["ls", "dir", "pwd", "echo"]
            ),

            # Allow application control
            PermissionRule(
                permission_type=PermissionType.APPLICATION_CONTROL,
                level=PermissionLevel.FULL_ACCESS,
                resource_pattern="*",
                allowed_actions=["start", "stop", "control"]
            ),

            # Allow data processing
            PermissionRule(
                permission_type=PermissionType.DATA_PROCESSING,
                level=PermissionLevel.FULL_ACCESS,
                resource_pattern="*",
                allowed_actions=["process", "transform", "analyze"]
            ),

            # Allow sandbox execution with restrictions
    PermissionRule(
                permission_type=PermissionType.SANDBOX_EXECUTION,
                level=PermissionLevel.READ_WRITE,
                resource_pattern="*",
                allowed_actions=["execute"],
                denied_actions=["os", "sys", "subprocess"]  # These are additionally restricted by sandbox
            )
    ]

    logger.info("Set default permission rules")

    def add_user_rule(self, user_id: str, rule: PermissionRule)
        """Add a permission rule for a specific user""":
    if user_id not in self.rules:

    self.rules[user_id] =

    self.rules[user_id].append(rule)
        logger.info(f"Added permission rule for user {user_id}: {rule}")

    def check_permission(self, context: PermissionContext) -> bool:
        """Check if a permission is granted""":
    try:
            # First check user-specific rules
            if context.user_id in self.rules:

    for rule in self.rules[context.user_id]:


    if self._rule_matches_context(rule, context)



    result = self._evaluate_rule(rule, context)
                        self._log_audit_event(context, result)
                        return result

            # Then check default rules
            for rule in self.default_rules:

    if self._rule_matches_context(rule, context)


    result = self._evaluate_rule(rule, context)
                    self._log_audit_event(context, result)
                    return result

            # Default deny if no rules match
    self._log_audit_event(context, False)
            return False

        except Exception as e:


            logger.error(f"Error checking permission: {e}")
            self._log_audit_event(context, False)
            return False

    def _rule_matches_context(self, rule: PermissionRule, context: PermissionContext) -> bool:
        """Check if a rule matches the context"""
    # Check permission type
        if rule.permission_type.value != context.operation:

    return False

    # Check resource pattern (simple wildcard matching)
        if rule.resource_pattern != "*" and not self._matches_pattern(context.resource, rule.resource_pattern)

    return False

    # Check action
        if rule.denied_actions and context.action in rule.denied_actions:

    return False

        if rule.allowed_actions and context.action not in rule.allowed_actions:


    return False

    return True

    def _matches_pattern(self, resource: str, pattern: str) -> bool:
        """Simple pattern matching for resources"""
    # This is a simplified implementation
    # In a real system, you might want to use more sophisticated pattern matching

        if pattern == "*":


    return True

        # Use fnmatch for more sophisticated pattern matching
    return fnmatch.fnmatch(resource, pattern)

    def _evaluate_rule(self, rule: PermissionRule, context: PermissionContext) -> bool:
        """Evaluate if a rule grants permission"""
        # For now, we simply check if the rule's level is sufficient
    # In a more complex system, you might have more sophisticated logic
    return rule.level != PermissionLevel.NONE

    def _log_audit_event(self, context: PermissionContext, granted: bool)
    """Log an audit event"""
        if not self.audit_log_enabled:

    return

    audit_event = {
            "user_id": context.user_id,
            "operation": context.operation,
            "resource": context.resource,
            "action": context.action,
            "granted": granted,
            "metadata": context.metadata
    }

    logger.info(f"Permission audit: {json.dumps(audit_event)}")

    def save_configuration(self, config_path: str = None)
    """Save current configuration to file"""
        try:

            config_path = config_path or self.config_path
            config_dir = Path(config_path).parent
            config_dir.mkdir(parents=True, exist_ok=True)

            # Convert rules to serializable format
            config = {
                "default_rules": ,
                "user_rules":
            }

            # Save default rules
            for rule in self.default_rules:

    rule_data = {
                    "permission_type": rule.permission_type.value,
                    "level": rule.level.value,
                    "resource_pattern": rule.resource_pattern,
                    "allowed_actions": rule.allowed_actions,
                    "denied_actions": rule.denied_actions
                }
                _ = config["default_rules"].append(rule_data)

            # Save user rules
            for user_id, rules in self.rules.items:

    config["user_rules"][user_id] =
                for rule in rules:

    rule_data = {
                        "permission_type": rule.permission_type.value,
                        "level": rule.level.value,
                        "resource_pattern": rule.resource_pattern,
                        "allowed_actions": rule.allowed_actions,
                        "denied_actions": rule.denied_actions
                    }
                    _ = config["user_rules"][user_id].append(rule_data)

            # Write to file
            with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved permission configuration to {config_path}")
        except Exception as e:

            logger.error(f"Error saving permission configuration: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Create permission control system
    pcs = PermissionControlSystem

    # Test permission checking
    context = PermissionContext(
    user_id="ai_agent_1",
    operation="file_access",
    resource="/projects/test/file.txt",
    action="read"
    )

    result = pcs.check_permission(context)
    print(f"Permission check result: {result}")

    # Add a custom rule
    custom_rule = PermissionRule(
    permission_type=PermissionType.FILE_ACCESS,
    level=PermissionLevel.FULL_ACCESS,
    resource_pattern="/tmp/*",
    allowed_actions=["read", "write", "delete"]
    )

    pcs.add_user_rule("ai_agent_1", custom_rule)

    # Test with custom rule
    context2 = PermissionContext(
    user_id="ai_agent_1",
    operation="file_access",
    resource="/tmp/test.txt",
    action="write"
    )

    result2 = pcs.check_permission(context2)
    print(f"Permission check result with custom rule: {result2}")

    # Save configuration
    pcs.save_configuration("test_permission_config.json")
    print("Permission configuration saved")