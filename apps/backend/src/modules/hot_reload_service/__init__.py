"""Module wrapper for HotReloadService — initialized via lifespan.py, not module auto-start."""

import logging

try:
    from services.hot_reload_service import HotReloadService
except ImportError:
    HotReloadService = None

logger = logging.getLogger(__name__)


async def init(deps: dict = None) -> HotReloadService:
    return HotReloadService()


async def start(instance: HotReloadService) -> None:
    logger.debug("HotReloadService start — deferred-init wrapper (no-op)")


async def stop(instance: HotReloadService) -> None:
    logger.debug("HotReloadService stop — deferred-init wrapper (no-op)")
