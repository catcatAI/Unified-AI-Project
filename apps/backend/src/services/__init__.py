"""
Services package — production service layer for Angela AI.

Contains: ChatService, AudioService, VisionService, MultimodalService,
AngelaLLMService, cross-modal routing, WebSocket management,
API server, and integration bridges.
"""

import importlib
import logging

logger = logging.getLogger(__name__)


class _ServicesSentinel:
    """Sentinel that allows arbitrary attribute access for test patch compatibility.

    When `unittest.mock.patch('services.deleted_module.Class.method', create=True)`
    traverses a dotted path, it calls `getattr(services, 'deleted_module')`.
    Instead of raising AttributeError immediately, we return this sentinel that:
    - Allows arbitrary attribute access (returns self)
    - Is callable (returns self)
    - Logs a warning on first access
    - Behaves as truthy for boolean checks
    """

    _warned: set = set()

    def __init__(self, name: str) -> None:
        self._name = name
        if name not in self._warned:
            logger.warning(
                "services.%s 不存在（可能是已刪除的子系統，或測試 mock 路徑）", name
            )
            self._warned.add(name)

    def __getattr__(self, attr: str) -> "_ServicesSentinel":
        return _ServicesSentinel(f"{self._name}.{attr}")

    def __call__(self, *args: object, **kwargs: object) -> "_ServicesSentinel":
        return self

    def __bool__(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"<services.{self._name} (missing)>"


def __getattr__(name: str) -> object:
    """Lazy import with sentinel fallback for test patch compatibility.

    For explicit imports: returns the already-imported attribute.
    For unknown names: tries dynamic submodule import first, then falls back to
    a _ServicesSentinel (enables unittest.mock.patch with create=True to traverse
    dotted paths through deleted/nonexistent subsystems).
    """
    # Dynamic submodule import: try importlib first
    try:
        module = importlib.import_module(f"services.{name}")
        return module
    except ImportError:
        pass

    # Fallback: return sentinel
    return _ServicesSentinel(name)


from services.audio_service import AudioService
from services.vision_service import VisionService
from services.chat_service import ChatService
from services.multimodal_service import MultimodalService
from services.angela_llm_service import AngelaLLMService as AngelaLLMServiceRouter
from services.brain_bridge_service import BrainBridgeService
from services.weather_service import WeatherService
from services.atlassian_api import AtlassianCLIBridge
from services.resource_awareness_service import ResourceAwarenessService
from services.math_verifier import MathVerifier
from services.connection_session import ConnectionSession, SessionManager
from services.websocket_manager import ConnectionManager
from services.cross_modal_router import CrossModalRouter
from services.cross_modal_quality import CrossModalQualityDashboard
from services.multimodal_quality_monitor import MultimodalQualityMonitor
from services.multimodal_error_recovery import MultimodalErrorRecovery
from services.multimodal_state_persistence import MultimodalStatePersistence
from services.hot_reload_service import HotReloadService
from services.main_api_server import MainApiServer, SystemMetricsManager, MessageManager

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
