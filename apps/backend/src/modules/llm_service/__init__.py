"""Module wrapper for AngelaLLMService — initialized via lifespan.py, not module auto-start."""

from services.llm.router import AngelaLLMService


async def init(deps: dict = None) -> AngelaLLMService:
    return AngelaLLMService()


async def start(instance: AngelaLLMService, deps: dict = None) -> None:
    await instance.initialize()


async def stop(instance: AngelaLLMService) -> None:
    pass
