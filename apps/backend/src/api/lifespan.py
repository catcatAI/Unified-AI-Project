"""
ANGELA-MATRIX: [L4-L5] [βδ] [A] [L3]
Application lifecycle management — startup/shutdown + service factories.
Extracted from main_api_server.py (A3 god module split).
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from fastapi import FastAPI

# Plugin imports are lazy inside lifespan() to avoid slow core package import

logger = logging.getLogger(__name__)

_STANDARD_HOOKS = [
    "on_message",
    "on_response",
    "on_state_change",
    "on_bio_event",
    "on_tick",
]

# Lazy-loaded service instances
_chat_service_instance = None
_digital_life_instance = None
_abc_key_manager_instance = None

# --- Config (lazy proxy) ---
class _LazyAngelaConfig:
    """Lazy-loaded proxy for AngelaConfig that avoids heavy imports at module level."""

    def __init__(self):
        self._cfg = None
        self._loaded = False

    def _ensure(self):
        if not self._loaded:
            self._loaded = True
            try:
                from core.config_loader import get_angela_config
                self._cfg = get_angela_config()
            except Exception as e:
                logger.warning(f"AngelaConfig not available: {e}")

    def get_authority(self, section, default=None):
        self._ensure()
        if self._cfg is None:
            return default or {}
        return self._cfg.get_authority(section, default)

    def __bool__(self):
        self._ensure()
        return self._cfg is not None

    def __getattr__(self, name):
        self._ensure()
        if self._cfg is None:
            raise AttributeError(f"AngelaConfig not loaded")
        return getattr(self._cfg, name)


_angela_cfg = _LazyAngelaConfig()


# --- Service factories ---

async def _get_chat_service():
    """Get or create the chat service singleton."""
    global _chat_service_instance
    if _chat_service_instance is None:
        try:
            from services.chat_service import ChatService
            _chat_service_instance = ChatService()
            await _chat_service_instance.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize chat service: {e}", exc_info=True)
            raise
    return _chat_service_instance


def get_abc_key_manager():
    """Get or create the ABC key manager singleton."""
    global _abc_key_manager_instance
    if _abc_key_manager_instance is None:
        try:
            from system.security_monitor import ABCKeyManager
            _abc_key_manager_instance = ABCKeyManager()
        except Exception as e:
            logger.warning(f"ABCKeyManager not available: {e}", exc_info=True)
            raise
    return _abc_key_manager_instance


def get_digital_life():
    """Get or create the digital life integrator singleton."""
    global _digital_life_instance
    if _digital_life_instance is None:
        try:
            from core.life.digital_life_integrator import DigitalLifeIntegrator
            _digital_life_instance = DigitalLifeIntegrator()
        except Exception as e:
            logger.warning(f"DigitalLifeIntegrator not available: {e}", exc_info=True)
            raise
    return _digital_life_instance


def get_desktop_interaction():
    """Lazy import for desktop interaction."""
    try:
        from core.engine.desktop_interaction import DesktopInteraction
        return DesktopInteraction()
    except Exception as e:
        logger.warning(f"DesktopInteraction not available: {e}")
        return None


def get_action_executor():
    """Lazy import for action executor."""
    try:
        from core.engine.action_executor import ActionExecutor
        return ActionExecutor()
    except Exception as e:
        logger.warning(f"ActionExecutor not available: {e}")
        return None


def get_vision_service():
    try:
        from services.vision_service import VisionService
        return VisionService()
    except Exception as e:
        logger.warning(f"VisionService not available: {e}")
        return None


def get_audio_service():
    try:
        from services.audio_service import AudioService
        return AudioService()
    except Exception as e:
        logger.warning(f"AudioService not available: {e}")
        return None


def get_tactile_service():
    try:
        from services.tactile_service import TactileService
        return TactileService()
    except Exception as e:
        logger.warning(f"TactileService not available: {e}")
        return None


def get_economy_manager():
    try:
        from core.economy.economy_manager import EconomyManager
        return EconomyManager()
    except Exception as e:
        logger.warning(f"EconomyManager not available: {e}")
        return None


def setup_middleware(app: FastAPI) -> None:
    """Configure application middleware."""
    pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: initialize plugins on startup, log metrics on shutdown."""
    # --- Startup ---
    from core.plugin.plugin_manager import plugin_manager
    from core.plugin.handlers.message_logger import MessageLoggerHandler
    from core.plugin.handlers.metrics_collector import MetricsCollectorHandler
    from core.plugin.handlers.audit_logger import AuditLoggerHandler

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

    # Initialize module manager (discovers and starts all 11 modules)
    _module_manager = None
    try:
        from core.interfaces.service_registry import get_registry
        from services.wiring import initialize_module_manager
        _module_manager = await initialize_module_manager(get_registry())
        logger.info("[ModuleManager] Module system initialized and started")
    except Exception as e:
        logger.error(f"[ModuleManager] Initialization failed, continuing without module system: {e}", exc_info=True)

    yield

    # --- Shutdown ---
    if _module_manager is not None:
        try:
            await _module_manager.stop()
            logger.info("[ModuleManager] Module system shut down cleanly")
        except Exception as e:
            logger.error(f"[ModuleManager] Shutdown error: {e}", exc_info=True)
    metric_data = metrics_handler.get_metrics()
    logger.info("[Plugin] Shutdown — hook invocation counts: %s", metric_data["counts"])

