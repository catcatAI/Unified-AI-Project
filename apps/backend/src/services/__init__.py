"""
Services package — production service layer for Angela AI.

Contains: ChatService, AudioService, VisionService, MultimodalService,
AngelaLLMService, cross-modal routing, WebSocket management,
API server, and integration bridges.

All imports are lazy to avoid slow/torch-dependent module loading.
Import directly from submodules: from services.chat_service import ChatService
"""

import importlib
import logging
from typing import Any, List

logger = logging.getLogger(__name__)

_LAZY_SERVICES: dict = {
    "AudioService": ("services.audio_service", "AudioService"),
    "VisionService": ("services.vision_service", "VisionService"),
    "ChatService": ("services.chat_service", "ChatService"),
    "MultimodalService": ("services.multimodal_service", "MultimodalService"),
    "AngelaLLMServiceRouter": ("services.angela_llm_service", "AngelaLLMService"),
    "BrainBridgeService": ("services.brain_bridge_service", "BrainBridgeService"),
    "WeatherService": ("services.weather_service", "WeatherService"),
    "AtlassianCLIBridge": ("services.atlassian_api", "AtlassianCLIBridge"),
    "ResourceAwarenessService": ("services.resource_awareness_service", "ResourceAwarenessService"),
    "MathVerifier": ("services.math_verifier", "MathVerifier"),
    "ConnectionSession": ("services.connection_session", "ConnectionSession"),
    "SessionManager": ("services.connection_session", "SessionManager"),
    "ConnectionManager": ("services.websocket_manager", "ConnectionManager"),
    "CrossModalRouter": ("services.cross_modal_router", "CrossModalRouter"),
    "CrossModalQualityDashboard": ("services.cross_modal_quality", "CrossModalQualityDashboard"),
    "MultimodalQualityMonitor": ("services.multimodal_quality_monitor", "MultimodalQualityMonitor"),
    "MultimodalErrorRecovery": ("services.multimodal_error_recovery", "MultimodalErrorRecovery"),
    "MultimodalStatePersistence": (
        "services.multimodal_state_persistence",
        "MultimodalStatePersistence",
    ),
    "HotReloadService": ("services.hot_reload_service", "HotReloadService"),
    "MainApiServer": ("services.main_api_server", "MainApiServer"),
    "SystemMetricsManager": ("services.main_api_server", "SystemMetricsManager"),
    "MessageManager": ("services.main_api_server", "MessageManager"),
}

_lazy_cache: dict = {}
_warned: set = set()


class _ServicesSentinel:
    """Sentinel for test patch compatibility."""

    _warned: set = set()

    def __init__(self, name: str) -> None:
        self._name = name
        if name not in self._warned:
            logger.warning("services.%s not available", name)
            self._warned.add(name)

    def __getattr__(self, attr: str) -> "_ServicesSentinel":
        return _ServicesSentinel(f"{self._name}.{attr}")

    def __call__(self, *args, **kwargs):
        return self

    def __bool__(self):
        return True

    def __repr__(self):
        return f"<services.{self._name} (missing)>"


def __getattr__(name: str) -> Any:
    if name in _LAZY_SERVICES:
        if name in _lazy_cache:
            return _lazy_cache[name]
        module_path, attr = _LAZY_SERVICES[name]
        try:
            module = importlib.import_module(module_path)
            result = getattr(module, attr)
            _lazy_cache[name] = result
            return result
        except Exception as e:
            if name not in _warned:
                logger.warning("Failed to lazy-import %s: %s", name, e)
                _warned.add(name)
            _lazy_cache[name] = None
            return None

    # Dynamic submodule import for test patches
    try:
        module = importlib.import_module(f"services.{name}")
        return module
    except ImportError:
        logger.debug("Lazy import failed for services.%s, using sentinel", name, exc_info=True)
        pass

    return _ServicesSentinel(name)


def __dir__() -> List[str]:
    return sorted(__all__)


__all__ = [
    "AudioService",
    "VisionService",
    "ChatService",
    "MultimodalService",
    "AngelaLLMServiceRouter",
    "BrainBridgeService",
    "WeatherService",
    "AtlassianCLIBridge",
    "ResourceAwarenessService",
    "MathVerifier",
    "ConnectionSession",
    "SessionManager",
    "ConnectionManager",
    "CrossModalRouter",
    "CrossModalQualityDashboard",
    "MultimodalQualityMonitor",
    "MultimodalErrorRecovery",
    "MultimodalStatePersistence",
    "HotReloadService",
    "MainApiServer",
    "SystemMetricsManager",
    "MessageManager",
]
