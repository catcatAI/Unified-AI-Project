"""
ANGELA-MATRIX: [L4-L5] [βδ] [A] [L3]
Application lifecycle management — startup/shutdown + service factories.
Extracted from main_api_server.py (A3 god module split).
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from core.plugin.plugin_manager import plugin_manager
from core.plugin.handlers.message_logger import MessageLoggerHandler
from core.plugin.handlers.metrics_collector import MetricsCollectorHandler
from core.plugin.handlers.audit_logger import AuditLoggerHandler

logger = logging.getLogger(__name__)

_STANDARD_HOOKS = [
    "on_message",
    "on_response",
    "on_state_change",
    "on_bio_event",
    "on_tick",
]


def setup_middleware(app: FastAPI) -> None:
    """Configure application middleware."""
    pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: initialize plugins on startup, log metrics on shutdown."""
    # --- Startup ---
    plugin_manager.register_plugin("core", "1.0.0", "Core built-in plugin handlers")

    msg_handler = MessageLoggerHandler()
    metrics_handler = MetricsCollectorHandler()
    audit_handler = AuditLoggerHandler()

    # Register message_logger for on_message hook only
    plugin_manager.add_handler("core", "on_message", msg_handler)

    # Register metrics and audit for all standard hooks
    for hook in _STANDARD_HOOKS:
        plugin_manager.add_handler("core", hook, metrics_handler.handler_for(hook))
        plugin_manager.add_handler("core", hook, audit_handler.handler_for(hook))

    stats = plugin_manager.get_stats()
    logger.info(
        "[Plugin] Initialized: %d hooks, %d handlers, %d plugins",
        stats["hook_registry"]["hook_count"],
        stats["hook_registry"]["handler_count"],
        stats["plugin_count"],
    )

    yield

    # --- Shutdown ---
    metric_data = metrics_handler.get_metrics()
    logger.info("[Plugin] Shutdown — hook invocation counts: %s", metric_data["counts"])

