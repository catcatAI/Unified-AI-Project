"""Module wrapper for ResourceAwarenessService — initialized via lifespan.py, not module auto-start."""

import logging

from services.resource_awareness_service import ResourceAwarenessService

logger = logging.getLogger(__name__)


async def init(deps: dict = None) -> ResourceAwarenessService:
    return ResourceAwarenessService()


async def start(instance: ResourceAwarenessService, deps: dict = None) -> None:
    logger.debug("ResourceAwarenessService start — deferred-init wrapper (no-op)")


async def stop(instance: ResourceAwarenessService) -> None:
    logger.debug("ResourceAwarenessService stop — deferred-init wrapper (no-op)")
