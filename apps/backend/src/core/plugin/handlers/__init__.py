"""
ANGELA-MATRIX: [L3] [β] [B] [L2]
Plugin handlers package — deployed handlers registered at startup.
"""

from core.plugin.handlers.audit_logger import AuditLoggerHandler
from core.plugin.handlers.message_logger import MessageLoggerHandler
from core.plugin.handlers.metrics_collector import MetricsCollectorHandler

__all__ = [
    "MessageLoggerHandler",
    "MetricsCollectorHandler",
    "AuditLoggerHandler",
]
