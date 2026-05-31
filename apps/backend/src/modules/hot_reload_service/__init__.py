"""Module wrapper for HotReloadService — initialized via lifespan.py, not module auto-start."""

from services.hot_reload_service import HotReloadService


async def init(deps: dict = None) -> HotReloadService:
    return HotReloadService()


async def start(instance: HotReloadService) -> None:
    pass


async def stop(instance: HotReloadService) -> None:
    pass
