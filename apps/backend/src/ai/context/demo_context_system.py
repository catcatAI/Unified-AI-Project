"""上下文系统演示脚本"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

# Angela Matrix: [L2:MEM] [L4:CTX] Context system demonstration

import logging
from typing import Any, Dict, Optional

from ai.context.manager_fixed import ContextManager, get_context_manager
from ai.context.storage.base import Context, ContextType
from ai.context.storage.memory import MemoryStorage

logger = logging.getLogger(__name__)


class DemoContextSystem:
    """演示上下文系统 - 展示 context 模块的核心功能"""

    def __init__(self, storage: Optional[MemoryStorage] = None):
        self.manager: ContextManager = get_context_manager()
        self.storage = storage or MemoryStorage()

    def demo_create_context(
        self, context_id: str, context_type: ContextType, data: Dict[str, Any]
    ) -> Context:
        ctx = Context(context_id=context_id, context_type=context_type)
        ctx.update_content(data)
        self.storage.save_context(ctx)
        logger.info(f"[DemoContext] Created context: {context_id}")
        return ctx

    def demo_retrieve_context(self, context_id: str) -> Optional[Context]:
        ctx = self.storage.load_context(context_id)
        logger.info(f"[DemoContext] Retrieved context: {context_id}")
        return ctx

    async def run_demo(self) -> None:
        logger.info("[DemoContext] Running context system demo...")
        ctx = self.demo_create_context(
            "demo-001", ContextType.DIALOGUE, {"message": "Hello, Angela!"}
        )
        loaded = self.demo_retrieve_context(ctx.context_id)
        if loaded:
            logger.info(f"[DemoContext] Demo passed - context loaded: {loaded.context_id}")
        else:
            logger.warning("[DemoContext] Demo failed - context not found")
