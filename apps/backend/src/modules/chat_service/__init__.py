"""Module wrapper for ChatService — initialized via lifespan.py, not module auto-start."""

import logging

from services.chat_service import ChatService

logger = logging.getLogger(__name__)


async def init(deps: dict = None) -> ChatService:
    return ChatService()


async def start(instance: ChatService, deps: dict = None) -> None:
    await instance.initialize()


async def stop(instance: ChatService) -> None:
    logger.debug("ChatService stop — deferred-init wrapper (no-op)")
