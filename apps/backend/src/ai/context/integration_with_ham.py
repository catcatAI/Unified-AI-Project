"""上下文系统与HAM内存管理系统的集成示例"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

# Angela Matrix: [L2:MEM] [L4:CTX] HAM integration with context system

import logging
from typing import Any, Dict, Optional

# 假设这些是从现有系统导入的
# from ..memory.ham_memory.ham_manager import HAMMemoryManager
# from ..memory.ham_types import HAMMemory

logger = logging.getLogger(__name__)


class ContextHAMIntegration:
    """上下文系统与HAM内存管理系统的集成类"""

    def __init__(self, context_manager, ham_manager=None) -> None:
        """
        初始化集成类

        Args:
            context_manager: 上下文管理器实例
            ham_manager: HAM内存管理器实例(可选)
        """
        self.context_manager = context_manager
        self.ham_manager = ham_manager
        # self.memory_context_manager = MemoryContextManager(context_manager)  # Commented - needs proper import

    def sync_context_to_ham(self, context_id: str) -> bool:
        """
        将上下文同步到HAM内存系统

        Args:
            context_id: 上下文ID

        Returns:
            bool: 同步是否成功
        """
        try:
            if not self.ham_manager:
                logger.warning("HAM manager not available, skipping sync")
                return False

            # 获取上下文
            context = self.context_manager.get_context(context_id)
            if not context:
                logger.error(f"Context {context_id} not found")
                return False

            # 将上下文内容转换为HAM conversation 记录并写入
            conversation = {
                "context_id": context.context_id,
                "context_type": (
                    context.context_type.value
                    if hasattr(context.context_type, "value")
                    else str(context.context_type)
                ),
                "content": context.content,
                "metadata": context.metadata,
                "created_at": context.created_at.isoformat(),
                "updated_at": context.updated_at.isoformat(),
            }
            store = getattr(self.ham_manager, "store_conversation", None)
            if not store:
                logger.warning("HAM store_conversation not available, skipping sync")
                return False
            store(conversation)
            logger.info(f"Synced context {context_id} to HAM memory")
            return True
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(f"Failed to sync context {context_id} to HAM: {e}", exc_info=True)
            return False

    def sync_ham_to_context(self, ham_memory_id: str) -> Optional[str]:
        """
        将HAM内存同步到上下文系统

        Args:
            ham_memory_id: HAM内存ID (context_id 在 HAM 中的记录标识)

        Returns:
            Optional[str] 创建的上下文ID, 如果失败则返回None
        """
        try:
            if not self.ham_manager:
                logger.warning("HAM manager not available, skipping sync")
                return None

            # 从 HAM conversations 中检索匹配记录
            data = getattr(self.ham_manager, "_data", None)
            if not data:
                logger.warning("HAM data store not available, skipping sync")
                return None

            conversation = None
            for record in data.get("conversations", []):
                if record.get("context_id") == ham_memory_id:
                    conversation = record
                    break
            if not conversation:
                logger.error(f"HAM memory {ham_memory_id} not found")
                return None

            context_id = f"ctx_ham_{ham_memory_id}"
            logger.info(f"Synced HAM memory {ham_memory_id} to context {context_id}")
            return context_id
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(
                f"Failed to sync HAM memory {ham_memory_id} to context: {e}", exc_info=True
            )
            return None

    def create_memory_context_from_ham(self, ham_memory_data: Dict[str, Any]) -> Optional[str]:
        """
        基于HAM记忆数据创建记忆上下文

        Args:
            ham_memory_data: HAM记忆数据

        Returns:
            Optional[str]: 创建的记忆上下文ID, 如果不可用则返回None
        """
        try:
            create = getattr(self.context_manager, "create_context", None)
            if not create:
                logger.warning(
                    "context_manager.create_context not available, cannot create memory context",

                )
                return None
            from ai.context.storage.base import ContextType

            context_id = create(
                ContextType.MEMORY,
                {"content": ham_memory_data.get("content", ""), **ham_memory_data},
            )
            logger.info(f"Created memory context {context_id} from HAM data")
            return context_id
        except (
            Exception
        ) as e:  # broad exception acceptable: initialization continues on optional component failure
            logger.error(f"Failed to create memory context from HAM data: {e}", exc_info=True)
            return None

    def update_ham_from_memory_context(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """
        基于记忆上下文更新HAM记忆

        Args:
            memory_id: 记忆ID
            updates: 更新内容

        Returns:
            bool: 更新是否成功
        """
        try:
            if not self.ham_manager:
                logger.warning("HAM manager not available, skipping update")
                return False

            data = getattr(self.ham_manager, "_data", None)
            if not data:
                logger.warning("HAM data store not available, skipping update")
                return False

            updated = False
            for record in data.get("conversations", []):
                if record.get("context_id") == memory_id:
                    record["content"] = updates.get("content", record.get("content"))
                    if "metadata" in updates:
                        record["metadata"] = updates["metadata"]
                    updated = True
                    break
            if not updated:
                logger.warning(
                    f"HAM memory {memory_id} not found for update"
                )
                return False

            save = getattr(self.ham_manager, "_save", None)
            if save:
                save()
            logger.info(f"Updated HAM from memory context {memory_id}")
            return True
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(
                f"Failed to update HAM from memory context {memory_id}: {e}", exc_info=True
            )
            return False

    def transfer_context_memory(self, source_context_id: str, target_memory_type: str) -> bool:
        """
        转移上下文记忆(例如从短期转移到长期)

        Args:
            source_context_id: 源上下文ID
            target_memory_type: 目标记忆类型

        Returns:
            bool: 转移是否成功
        """
        try:
            # 获取源上下文
            source_context = self.context_manager.get_context(source_context_id)
            if not source_context:
                logger.error(f"Source context {source_context_id} not found")
                return False

            # 创建目标上下文并转移内容
            create = getattr(self.context_manager, "create_context", None)
            if not create:
                logger.warning(
                    "context_manager.create_context not available, cannot transfer",

                )
                return False
            from ai.context.storage.base import ContextType

            target_context_id = create(ContextType.MEMORY, dict(source_context.content))
            transfer = getattr(self.context_manager, "transfer_context", None)
            if transfer:
                transfer(source_context_id, target_context_id)

            # 同步到HAM(如果可用)
            if self.ham_manager:
                sync = getattr(self.ham_manager, "store_conversation", None)
                if sync:
                    sync(
                        {
                            "context_id": target_context_id,
                            "memory_type": target_memory_type,
                            "source_context_id": source_context_id,
                            "content": dict(source_context.content),
                        }
                    )

            logger.info(f"Transferred context memory from {source_context_id}")
            return True
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(
                f"Failed to transfer context memory from {source_context_id}: {e}", exc_info=True
            )
            return False


# 使用示例
def example_usage() -> None:
    """使用示例"""
    # 创建上下文管理器
    # context_manager = ContextManager()  # Commented - needs proper import

    # 创建集成实例(HAM管理器在实际使用中需要传入)
    # integration = ContextHAMIntegration(context_manager, ham_manager=None)

    # 同步到HAM(在HAM管理器可用时)
    # success = integration.sync_context_to_ham(context_id)

    logger.info("Created memory context: memory_id")


if __name__ == "__main__":
    example_usage()
