from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class HotReloadService:
    def __init__(self):
        self._draining = False

    async def begin_draining(self) -> dict:
        self._draining = True
        logger.info("HotReloadService: draining started")
        return {"draining": True}

    async def end_draining(self) -> dict:
        self._draining = False
        logger.info("HotReloadService: draining ended")
        return {"draining": False}

    async def status(self) -> dict:
        return {"status": "draining" if self._draining else "ready"}


_instance: HotReloadService | None = None


def get_hot_reload_service() -> HotReloadService:
    global _instance
    if _instance is None:
        _instance = HotReloadService()
    return _instance
