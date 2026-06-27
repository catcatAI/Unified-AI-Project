"""
Security Module for Unified AI Project:
Provides comprehensive security controls for AI operations:
"""

import logging

logger = logging.getLogger(__name__)

from .audit_logger import AuditEvent, AuditEventType, AuditLogger  # noqa: E402
from .content_filter import ContentFilter, FilterAction, FilterResult, SafetyLevel  # noqa: E402
from .permission_control import (  # noqa: E402
    PermissionContext,
    PermissionControlSystem,
    PermissionLevel,
    PermissionRule,
    PermissionType,
)
from .safety_audit import AuditEntry as SafetyAuditEntry  # noqa: E402
from .safety_audit import AuditEventType as SafetyAuditEventType
from .safety_audit import SafetyAudit, Severity

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
