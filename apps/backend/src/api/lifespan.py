"""
ANGELA-MATRIX: [L4-L5] [βδ] [A] [L3]
Application lifecycle management — startup/shutdown + service factories.
Extracted from main_api_server.py (A3 god module split).
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config_loader import get_angela_config
from core.autonomous.desktop_interaction import DesktopInteraction
from core.autonomous.action_executor import ActionExecutor, Action, ActionCategory, ActionPriority
from core.autonomous.heartbeat import MetabolicHeartbeat
from services.vision_service import VisionService
from services.audio_service import AudioService
from services.tactile_service import TactileService
from services.angela_llm_service import get_llm_service
from economy.economy_manager import EconomyManager
from core.autonomous.digital_life_integrator import DigitalLifeIntegrator
from system.security_monitor import ABCKeyManager
from shared.security_middleware import SignedCommunicationMiddleware

logger = logging.getLogger(__name__)

_angela_cfg = None
_abc_key_manager = None
_llm_service = None
_chat_service_instance = None

_desktop_interaction = None
_action_executor = None
_vision_service = None
_audio_service = None
_tactile_service = None
_digital_life = None
_economy_manager = None
_metabolic_heartbeat = None


def setup_middleware(app: FastAPI):
    """Configure CORS and signed-communication middleware."""
    global _angela_cfg
    try:
        _angela_cfg = get_angela_config()
        _cors_cfg = _angela_cfg.get_authority("angela_core", {}).get("middleware", {}).get("cors", {})
        if _cors_cfg.get("enabled", True):
            app.add_middleware(
                CORSMiddleware,
                allow_origins=_cors_cfg.get("allow_origins", ["*"]),
                allow_credentials=_cors_cfg.get("allow_credentials", True),
                allow_methods=_cors_cfg.get("allow_methods", ["*"]),
                allow_headers=_cors_cfg.get("allow_headers", ["*"]),
            )
            logger.info("[Middleware] CORS enabled from config")
    except Exception as e:
        logger.warning(f"[Middleware] CORS setup skipped: {e}")

    try:
        app.add_middleware(
            SignedCommunicationMiddleware,
            key_b=_get_abc_key_manager().get_key("KeyB"),
        )
        logger.info("[Middleware] EncryptedCommunication enabled")
    except Exception as e:
        logger.warning(f"[Middleware] EncryptedCommunication setup skipped: {e}")


def _get_abc_key_manager():
    global _abc_key_manager
    if _abc_key_manager is None:
        _abc_key_manager = ABCKeyManager()
    return _abc_key_manager


def get_abc_key_manager() -> ABCKeyManager:
    return _get_abc_key_manager()


def get_metabolic_heartbeat() -> MetabolicHeartbeat:
    global _metabolic_heartbeat
    if _metabolic_heartbeat is None:
        _metabolic_heartbeat = MetabolicHeartbeat(update_interval=30.0)
    return _metabolic_heartbeat


def get_desktop_interaction() -> DesktopInteraction:
    global _desktop_interaction
    if _desktop_interaction is None:
        _desktop_interaction = DesktopInteraction()
    return _desktop_interaction


def get_action_executor() -> ActionExecutor:
    global _action_executor
    if _action_executor is None:
        _action_executor = ActionExecutor()
    return _action_executor


def get_vision_service() -> VisionService:
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
    return _vision_service


def get_audio_service() -> AudioService:
    global _audio_service
    if _audio_service is None:
        _audio_service = AudioService()
    return _audio_service


def get_tactile_service() -> TactileService:
    global _tactile_service
    if _tactile_service is None:
        _tactile_service = TactileService()
    return _tactile_service


def get_digital_life() -> DigitalLifeIntegrator:
    global _digital_life
    if _digital_life is None:
        _digital_life = DigitalLifeIntegrator()
    return _digital_life


def get_economy_manager() -> EconomyManager:
    global _economy_manager
    if _economy_manager is None:
        _economy_manager = EconomyManager({})
    return _economy_manager


async def _get_chat_service():
    """Lazy-init chat service via registry (replaces direct import)."""
    global _chat_service_instance
    if _chat_service_instance is None:
        from core.interfaces.service_registry import get_registry
        _chat_service_instance = get_registry().get("chat_service")
        if _chat_service_instance is None:
            from services.chat_service import get_angela_chat_service as _init_chat
            _chat_service_instance = await _init_chat()
    return _chat_service_instance


def _validate_environment_variables():
    required_keys = ["ANGELA_KEY_A", "ANGELA_KEY_B", "ANGELA_KEY_C"]
    missing_keys = []
    for key in required_keys:
        value = os.environ.get(key)
        if not value:
            missing_keys.append(key)
    if missing_keys:
        if len(missing_keys) == 3:
            logger.warning("All Angela keys missing — running in demo mode")
        else:
            logger.warning(f"Missing keys: {', '.join(missing_keys)} — some features may be limited")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: pre-init core services. Shutdown: cleanup resources."""
    from services.websocket_manager import broadcast_state_updates

    logger.info("[Lifecycle] Starting Angela AI API server...")
    try:
        _lc = _angela_cfg.get("lifecycle", {}) if _angela_cfg else {}
        if _lc.get("preinitialize_on_startup", True):
            for svc_name in _lc.get("services_to_preinit", []):
                try:
                    if svc_name == "AngelaChatService":
                        svc = await _get_chat_service()
                        await svc.initialize()
                        logger.info("[Lifecycle] AngelaChatService initialized")
                    elif svc_name == "AngelaLLMService":
                        await get_llm_service()
                        logger.info("[Lifecycle] AngelaLLMService initialized")
                    elif svc_name == "BiologicalIntegrator":
                        from core.autonomous.biological_integrator import BiologicalIntegrator
                        bio = BiologicalIntegrator()
                        await bio.initialize()
                        logger.info("[Lifecycle] BiologicalIntegrator initialized")
                except Exception as e:
                    logger.warning(f"[Lifecycle] Failed to pre-init {svc_name}: {e}")
    except Exception as e:
        logger.warning(f"[Lifecycle] Startup config error: {e}")

    try:
        from services.wiring import initialize_all_services
        from services.websocket_manager import manager as _ws_manager
        initialize_all_services(_ws_manager)
        logger.info("[Lifecycle] Cross-service wiring complete")
    except Exception as e:
        logger.warning(f"[Lifecycle] Service wiring failed: {e}")

    try:
        heartbeat = get_metabolic_heartbeat()
        await heartbeat.start()
        logger.info("[Lifecycle] MetabolicHeartbeat started")
    except Exception as e:
        logger.warning(f"[Lifecycle] Heartbeat start failed: {e}")

    async def run_security_audit_task():
        while True:
            try:
                from core.security.security_audit import get_security_audit
                from core.system.state_store import state_store
                audit = get_security_audit()
                results = audit.scan_directory()
                logger.info(f"[Security] Periodic audit complete. Score: {results.get('score', 0)}")
                state_store.update_state("hardware", {"security_score": results.get("score", 0)})
            except Exception as e:
                logger.error(f"[Security] Audit task failed: {e}")
            await asyncio.sleep(3600)

    asyncio.create_task(run_security_audit_task(), name="Security-Audit-Task")
    asyncio.create_task(broadcast_state_updates(), name="WS-State-Broadcast")

    logger.info("[Lifecycle] Server startup complete")
    yield

    logger.info("[Lifecycle] Shutting down...")
    _sd_timeout = _lc.get("shutdown_timeout", 10.0) if _angela_cfg else 10.0
    try:
        hb = get_metabolic_heartbeat()
        await hb.stop()
    except Exception:
        pass
    logger.info(f"[Lifecycle] Shutdown complete (timeout={_sd_timeout}s)")
