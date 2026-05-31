"""Module wrapper for ChatService — initialized via lifespan.py, not module auto-start."""

from services.chat_service import ChatService


async def init(deps: dict = None) -> ChatService:
    return ChatService()


async def start(instance: ChatService, deps: dict = None) -> None:
    await instance.initialize()


async def stop(instance: ChatService) -> None:
    pass
