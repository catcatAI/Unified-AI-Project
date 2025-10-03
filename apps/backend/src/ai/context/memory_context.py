"""记忆上下文子系统"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .manager import ContextManager
from .storage.base import ContextType

logger: Any = logging.getLogger(__name__)

class Memory:
    """记忆"""

    def __init__(self, content: str, memory_type: str = "short_term") -> None:
    self.memory_id = f"mem_{datetime.now.strftime('%Y%m%d%H%M%S%f')}"
    self.content = content
    self.memory_type = memory_type  # short_term, long_term
    self.created_at = datetime.now
    self.last_accessed = datetime.now
    self.access_count = 0
    self.embedding: Optional[List[float]] = None  # 向量表示
    self.metadata: Dict[str, Any] = {}

    def access(self)
    """访问记忆"""
    self.last_accessed = datetime.now
    self.access_count += 1

class MemoryContextManager:
    """记忆上下文管理器"""

    def __init__(self, context_manager: ContextManager) -> None:
    self.context_manager = context_manager
    self.memories: Dict[str, Memory] =

    def create_memory(self, content: str, memory_type: str = "short_term",
                     metadata: Optional[Dict[str, Any]] = None) -> str:
    """创建记忆"""
        try:

            memory = Memory(content, memory_type)
            if metadata:

    memory.metadata = metadata

            self.memories[memory.memory_id] = memory

            # 创建对应的上下文
            context_content = {
                "memory": {
                    "memory_id": memory.memory_id,
                    "content": content,
                    "memory_type": memory_type,
                    "created_at": memory.created_at.isoformat,
                    "metadata": metadata or
                }
            }

            context_id = self.context_manager.create_context(ContextType.MEMORY, context_content)
            logger.info(f"Created memory {memory.memory_id} with context {context_id}")
    return memory.memory_id
        except Exception as e:

            logger.error(f"Failed to create memory: {e}")
            raise

    def access_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
    """访问记忆"""
        try:

            if memory_id not in self.memories:


    logger.error(f"Memory {memory_id} not found")
                return None

            memory = self.memories[memory_id]
            memory.access

            # 创建访问记录上下文
            context_content = {
                "memory_access": {
                    "memory_id": memory_id,
                    "access_time": memory.last_accessed.isoformat,
                    "access_count": memory.access_count
                }
            }

            context_id = self.context_manager.create_context(ContextType.MEMORY, context_content)
            logger.info(f"Accessed memory {memory_id} with context {context_id}")

    return {
                "memory_id": memory.memory_id,
                "content": memory.content,
                "memory_type": memory.memory_type,
                "created_at": memory.created_at.isoformat,
                "last_accessed": memory.last_accessed.isoformat,
                "access_count": memory.access_count,
                "metadata": memory.metadata
            }
        except Exception as e:

            logger.error(f"Failed to access memory {memory_id}: {e}")
            return None

    def update_memory_embedding(self, memory_id: str, embedding: List[float]) -> bool:
    """更新记忆向量表示"""
        try:

            if memory_id not in self.memories:


    logger.error(f"Memory {memory_id} not found")
                return False

            memory = self.memories[memory_id]
            memory.embedding = embedding

            # 更新上下文
            context_content = {
                "memory_embedding": {
                    "memory_id": memory_id,
                    "embedding_updated": datetime.now.isoformat,
                    "embedding_length": len(embedding)
                }
            }

            context_id = self.context_manager.create_context(ContextType.MEMORY, context_content)
            logger.info(f"Updated embedding for memory {memory_id} with context {context_id}")
    return True
        except Exception as e:

            logger.error(f"Failed to update embedding for memory {memory_id}: {e}")
            return False

    def get_memory_context(self, memory_id: str) -> Optional[Dict[str, Any]]:
    """获取记忆上下文"""
        try:

            if memory_id not in self.memories:


    logger.error(f"Memory {memory_id} not found")
                return None

            memory = self.memories[memory_id]

            # 搜索相关的上下文
            contexts = self.context_manager.search_contexts(memory_id, [ContextType.MEMORY])

            if not contexts:


    logger.debug(f"No context found for memory {memory_id}")
    return None

            # 返回最新的上下文
            latest_context = max(contexts, key=lambda c: c.updated_at)
            return {
                "context_id": latest_context.context_id,
                "content": latest_context.content,
                "metadata": latest_context.metadata,
                "updated_at": latest_context.updated_at.isoformat
            }
        except Exception as e:

            logger.error(f"Failed to get context for memory {memory_id}: {e}")
            return None

    def get_memories_by_type(self, memory_type: str, limit: int = 10) -> List[Dict[str, Any]]:
    """根据类型获取记忆"""
        try:
            # 筛选指定类型的记忆
            type_memories = [
                mem for mem in self.memories.values :
    if mem.memory_type == memory_type
            ]

            # 按最后访问时间排序
            type_memories.sort(key=lambda x: x.last_accessed, reverse=True)

            # 限制返回数量
            type_memories = type_memories[:limit]

            # 转换为字典格式
            result =
            for memory in type_memories:

    result.append({
                    "memory_id": memory.memory_id,
                    "content": memory.content,
                    "memory_type": memory.memory_type,
                    "created_at": memory.created_at.isoformat,
                    "last_accessed": memory.last_accessed.isoformat,
                    "access_count": memory.access_count
                })

            return result
        except Exception as e:

            logger.error(f"Failed to get memories by type {memory_type}: {e}")
            return

    def cleanup_old_memories(self, days: int = 30) -> int
    """清理旧记忆"""
        try:

            cutoff_date = datetime.now - timedelta(days=days)
            deleted_count = 0

            # 找到需要删除的旧记忆
            memories_to_delete = [
                mem_id for mem_id, memory in self.memories.items:
    if memory.last_accessed < cutoff_date
            ]

            # 删除记忆
            for mem_id in memories_to_delete:

    del self.memories[mem_id]
                deleted_count += 1

                # 创建删除记录上下文
                context_content = {
                    "memory_cleanup": {
                        "memory_id": mem_id,
                        "cleanup_time": datetime.now.isoformat,
                        "reason": "old_memory"
                    }
                }

                context_id = self.context_manager.create_context(ContextType.MEMORY, context_content)
                logger.info(f"Cleaned up old memory {mem_id} with context {context_id}")

    logger.info(f"Cleaned up {deleted_count} old memories")
            return deleted_count
        except Exception as e:

            logger.error(f"Failed to cleanup old memories: {e}")
            return 0

    def transfer_memory(self, source_memory_id: str, target_memory_type: str) -> Optional[str]:
    """转移记忆（例如从短期记忆转移到长期记忆）"""
        try:

            if source_memory_id not in self.memories:


    logger.error(f"Source memory {source_memory_id} not found")
                return None

            source_memory = self.memories[source_memory_id]

            # 创建新的记忆（转移后的记忆）
            new_memory_id = self.create_memory(
                content=source_memory.content,
                memory_type=target_memory_type,
                metadata=source_memory.metadata.copy if source_memory.metadata else None
            )

            # 如果源记忆有向量表示，也复制过去
            if source_memory.embedding:

    self.update_memory_embedding(new_memory_id, source_memory.embedding)

            # 创建转移记录上下文
            context_content = {
                "memory_transfer": {
                    "source_memory_id": source_memory_id,
                    "target_memory_id": new_memory_id,
                    "source_type": source_memory.memory_type,
                    "target_type": target_memory_type,
                    "transfer_time": datetime.now.isoformat
                }
            }

            context_id = self.context_manager.create_context(ContextType.MEMORY, context_content)
            logger.info(f"Transferred memory from {source_memory_id} to {new_memory_id} with context {context_id}")
    return new_memory_id
        except Exception as e:

            logger.error(f"Failed to transfer memory {source_memory_id}: {e}")
            return None