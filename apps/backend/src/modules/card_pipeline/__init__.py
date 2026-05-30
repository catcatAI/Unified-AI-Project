from core.card.card_store import CardRegistry
from core.card.resolver.pipeline_orchestrator import CardImportPipeline


async def init(deps: dict = None) -> CardImportPipeline:
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
    pass


async def stop(instance: CardImportPipeline) -> None:
    pass
