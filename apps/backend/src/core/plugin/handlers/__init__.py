"""
ANGELA-MATRIX: [L3] [β] [B] [L2]
Plugin handlers package — deployed handlers registered at startup.
"""

from core.plugin.handlers.message_logger import MessageLoggerHandler

__all__ = [
    "MessageLoggerHandler",
]
