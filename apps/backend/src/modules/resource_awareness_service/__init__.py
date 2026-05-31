"""Module wrapper for ResourceAwarenessService — initialized via lifespan.py, not module auto-start."""

from services.resource_awareness_service import ResourceAwarenessService


async def init(deps: dict = None) -> ResourceAwarenessService:
    return ResourceAwarenessService()


async def start(instance: ResourceAwarenessService) -> None:
    pass


async def stop(instance: ResourceAwarenessService) -> None:
    pass
