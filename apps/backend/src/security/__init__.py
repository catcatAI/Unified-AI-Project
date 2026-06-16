"""
Security Module for Unified AI Project:
Provides comprehensive security controls for AI operations:
"""

import logging

logger = logging.getLogger(__name__)

from .permission_control import (  # noqa: E402
    PermissionControlSystem,
    PermissionType,
    PermissionLevel,
    PermissionRule,
    PermissionContext,
)

from .audit_logger import AuditLogger, AuditEvent, AuditEventType  # noqa: E402
from .content_filter import ContentFilter, FilterResult, SafetyLevel, FilterAction  # noqa: E402
from .safety_audit import SafetyAudit, AuditEntry as SafetyAuditEntry, AuditEventType as SafetyAuditEventType, Severity  # noqa: E402

# Assuming these exist and are correct
# from .enhanced_sandbox import (
#     EnhancedSandboxExecutor,
#     SandboxConfig,
# #    ResourceLimits
# )

__all__ = [
    "PermissionControlSystem",
    "PermissionType",
    "PermissionLevel",
    "PermissionRule",
    "PermissionContext",
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "ContentFilter",
    "FilterResult",
    "SafetyLevel",
    "FilterAction",
    "SafetyAudit",
    "SafetyAuditEntry",
    "SafetyAuditEventType",
    "Severity",
    # 'EnhancedSandboxExecutor',
    # 'SandboxConfig',
    # 'ResourceLimits'
]
