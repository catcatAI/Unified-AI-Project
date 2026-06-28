"""
Services package — production service layer for Angela AI.

Contains: ChatService, AudioService, VisionService, MultimodalService,
AngelaLLMService, cross-modal routing, WebSocket management,
API server, and integration bridges.
"""

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
