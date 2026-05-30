"""Shared dependency functions for FastAPI Depends injection (A5)."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def get_tactile_service():
    from core.interfaces.service_registry import get_registry
    svc = get_registry().get("tactile_service")
    if svc is not None:
        return svc
    from services.tactile_service import TactileService
    if not hasattr(get_tactile_service, "_instance"):
        get_tactile_service._instance = TactileService()
    return get_tactile_service._instance


async def get_vision_service():
    from core.interfaces.service_registry import get_registry
    svc = get_registry().get("vision_service")
    if svc is not None:
        return svc
    from services.vision_service import VisionService
    if not hasattr(get_vision_service, "_instance"):
        get_vision_service._instance = VisionService()
    return get_vision_service._instance


async def get_audio_service():
    from core.interfaces.service_registry import get_registry
    svc = get_registry().get("audio_service")
    if svc is not None:
        return svc
    from services.audio_service import AudioService
    if not hasattr(get_audio_service, "_instance"):
        get_audio_service._instance = AudioService()
    return get_audio_service._instance


async def get_drive_service():
    from core.interfaces.service_registry import get_registry
    svc = get_registry().get("google_drive_service")
    if svc is not None:
        return svc
    from integrations.google_drive_service import get_drive_service as _get_drive_svc
    return _get_drive_svc()


async def get_economy_manager():
    if not hasattr(get_economy_manager, "_instance"):
        from economy.economy_manager import EconomyManager
        get_economy_manager._instance = EconomyManager()
    return get_economy_manager._instance


def set_economy_manager(manager):
    """Set economy manager instance externally (for startup wiring)."""
    get_economy_manager._instance = manager
    logger.info("EconomyManager instance set via set_economy_manager()")
