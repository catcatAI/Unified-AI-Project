"""Module wrapper for AngelaLLMService — initialized via lifespan.py, not module auto-start."""

import logging

from services.llm.router import AngelaLLMService

logger = logging.getLogger(__name__)


async def init(deps: dict = None) -> AngelaLLMService:
    return AngelaLLMService()


async def start(instance: AngelaLLMService, deps: dict = None) -> None:
    await instance.initialize()


async def stop(instance: AngelaLLMService) -> None:
    logger.debug("AngelaLLMService stop — deferred-init wrapper (no-op)")
