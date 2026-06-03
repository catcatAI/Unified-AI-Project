import logging

from core.card.card_store import CardRegistry
from core.card.resolver.pipeline_orchestrator import CardImportPipeline

logger = logging.getLogger(__name__)


async def init(deps: dict = None) -> CardImportPipeline:
    """Init."""
    registry = CardRegistry()
    deps = deps or {}
    memory_adapter = deps.get("ham_memory")
    llm_service = deps.get("llm_module")
    pipeline = CardImportPipeline(
        registry=registry,
        memory_adapter=memory_adapter,
        llm_service=llm_service,
    )
    return pipeline


async def start(instance: CardImportPipeline, deps: dict = None) -> None:
    logger.debug("CardImportPipeline start — deferred-init wrapper (no-op)")


async def stop(instance: CardImportPipeline) -> None:
    logger.debug("CardImportPipeline stop — deferred-init wrapper (no-op)")
