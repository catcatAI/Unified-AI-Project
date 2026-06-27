"""记忆上下文子系统"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

# Angela Matrix: [L2:MEM] [L4:CTX] Memory context subsystem

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Memory:
    """记忆"""

    def __init__(self, content: str, memory_type: str = "short_term") -> None:
        self.memory_id = f"mem_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        self.content = content
        self.memory_type = memory_type  # short_term, long_term
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.access_count = 0
        self.embedding: Optional[List[float]] = None  # 向量表示
        self.metadata: Dict[str, Any] = {}

    def access(self) -> None:
        """访问记忆"""
        self.last_accessed = datetime.now()
        self.access_count += 1


class MemoryContextManager:
    """记忆上下文管理器"""

    def __init__(self, context_manager=None, session_dir: str = "sessions") -> None:
        self.context_manager = context_manager
        self.memories: Dict[str, Memory] = {}
        self._session_dir = session_dir

    def create_memory(
        self,
        content: str,
        memory_type: str = "short_term",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """创建记忆"""
        try:
            memory = Memory(content, memory_type)
            if metadata:
                memory.metadata = metadata

            self.memories[memory.memory_id] = memory

            # 创建对应的上下文
            {
                "memory": {
                    "memory_id": memory.memory_id,
                    "content": content,
                    "memory_type": memory_type,
                    "created_at": memory.created_at.isoformat(),
                    "metadata": metadata or {},
                }
            }

            # context_id = self.context_manager.create_context(ContextType.MEMORY, context_content)  # Commented - needs proper import
            logger.info(f"Created memory {memory.memory_id} with context")
            return memory.memory_id
        except Exception as e:  # broad exception acceptable: initialization continues on optional component failure
            logger.error(f"Failed to create memory: {e}", exc_info=True)
            raise

    def access_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """访问记忆"""
        try:
            if memory_id not in self.memories:
                logger.error(f"Memory {memory_id} not found", exc_info=True)
                return None

            memory = self.memories[memory_id]
            memory.access()

            # 创建访问记录上下文
            {
                "memory_access": {
                    "memory_id": memory_id,
                    "access_time": memory.last_accessed.isoformat(),
                    "access_count": memory.access_count,
                }
            }

            # context_id = self.context_manager.create_context(ContextType.MEMORY, context_content)  # Commented - needs proper import
            logger.info(f"Accessed memory {memory_id} with context")
            return {
                "memory_id": memory.memory_id,
                "content": memory.content,
                "memory_type": memory.memory_type,
                "created_at": memory.created_at.isoformat(),
                "last_accessed": memory.last_accessed.isoformat(),
                "access_count": memory.access_count,
                "metadata": memory.metadata,
            }
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(f"Failed to access memory {memory_id}: {e}", exc_info=True)
            return None

    def update_memory_embedding(self, memory_id: str, embedding: List[float]) -> bool:
        """更新记忆向量表示"""
        try:
            if memory_id not in self.memories:
                logger.error(f"Memory {memory_id} not found", exc_info=True)
                return False

            memory = self.memories[memory_id]
            memory.embedding = embedding

            # 更新上下文
            {
                "memory_embedding": {
                    "memory_id": memory_id,
                    "embedding_updated": datetime.now().isoformat(),
                    "embedding_length": len(embedding),
                }
            }

            # context_id = self.context_manager.create_context(ContextType.MEMORY, context_content)  # Commented - needs proper import
            logger.info(f"Updated embedding for memory {memory_id} with context")
            return True
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(f"Failed to update embedding for memory {memory_id}: {e}", exc_info=True)
            return False

    def get_memory_context(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """获取记忆上下文"""
        try:
            if memory_id not in self.memories:
                logger.error(f"Memory {memory_id} not found", exc_info=True)
                return None

            mem = self.memories[memory_id]
            mem.access()
            result: Dict[str, Any] = {
                "memory_id": mem.memory_id,
                "content": mem.content,
                "memory_type": mem.memory_type,
                "created_at": mem.created_at.isoformat(),
                "last_accessed": mem.last_accessed.isoformat(),
                "access_count": mem.access_count,
                "has_embedding": mem.embedding is not None,
                "metadata": mem.metadata,
            }
            return result
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(f"Failed to get context for memory {memory_id}: {e}", exc_info=True)
            return None

    def get_memories_by_type(self, memory_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """根据类型获取记忆"""
        try:
            # 筛选指定类型的记忆
            type_memories = [
                mem for mem in self.memories.values() if mem.memory_type == memory_type
            ]

            # 按最后访问时间排序
            type_memories.sort(key=lambda x: x.last_accessed, reverse=True)

            # 限制返回数量
            type_memories = type_memories[:limit]

            # 转换为字典格式
            result = []
            for memory in type_memories:
                result.append(
                    {
                        "memory_id": memory.memory_id,
                        "content": memory.content,
                        "memory_type": memory.memory_type,
                        "created_at": memory.created_at.isoformat(),
                        "last_accessed": memory.last_accessed.isoformat(),
                        "access_count": memory.access_count,
                    }
                )

            return result
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(f"Failed to get memories by type {memory_type}: {e}", exc_info=True)
            return []

    def cleanup_old_memories(self, days: int = 30) -> int:
        """清理旧记忆"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0

            # 找到需要删除的旧记忆
            memories_to_delete = [
                mem_id
                for mem_id, memory in self.memories.items()
                if memory.last_accessed < cutoff_date
            ]

            # 删除记忆
            for mem_id in memories_to_delete:
                del self.memories[mem_id]
                deleted_count += 1

                # 创建删除记录上下文
                {
                    "memory_cleanup": {
                        "memory_id": mem_id,
                        "cleanup_time": datetime.now().isoformat(),
                        "reason": "old_memory",
                    }
                }

                # context_id = self.context_manager.create_context(ContextType.MEMORY, context_content)  # Commented - needs proper import
                logger.info(f"Cleaned up old memory {mem_id} with context")

            logger.info(f"Cleaned up {deleted_count} old memories")
            return deleted_count
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(f"Failed to cleanup old memories: {e}", exc_info=True)
            return 0

    def transfer_memory(self, source_memory_id: str, target_memory_type: str) -> Optional[str]:
        """转移记忆(例如从短期记忆转移到长期记忆)"""
        try:
            if source_memory_id not in self.memories:
                logger.error(f"Source memory {source_memory_id} not found", exc_info=True)
                return None

            source_memory = self.memories[source_memory_id]

            # 创建新的记忆(转移后的记忆)
            new_memory_id = self.create_memory(
                content=source_memory.content,
                memory_type=target_memory_type,
                metadata=source_memory.metadata.copy() if source_memory.metadata else None,
            )

            # 如果源记忆有向量表示, 也复制过去
            if source_memory.embedding:
                self.update_memory_embedding(new_memory_id, source_memory.embedding)

            # 创建转移记录上下文
            {
                "memory_transfer": {
                    "source_memory_id": source_memory_id,
                    "target_memory_id": new_memory_id,
                    "source_type": source_memory.memory_type,
                    "target_type": target_memory_type,
                    "transfer_time": datetime.now().isoformat(),
                }
            }

            # context_id = self.context_manager.create_context(ContextType.MEMORY, context_content)  # Commented - needs proper import
            logger.info(
                f"Transferred memory from {source_memory_id} to {new_memory_id} with context"
            )
            return new_memory_id
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(f"Failed to transfer memory {source_memory_id}: {e}", exc_info=True)
            return None

    def save_session(self, session_id: str) -> str:
        """Save session memories to disk for cross-session persistence (Phase 5.4)."""
        try:
            os.makedirs(self._session_dir, exist_ok=True)
            memories_data = {}
            for mem_id, memory in self.memories.items():
                memories_data[mem_id] = {
                    "content": memory.content,
                    "memory_type": memory.memory_type,
                    "created_at": memory.created_at.isoformat(),
                    "last_accessed": memory.last_accessed.isoformat(),
                    "access_count": memory.access_count,
                    "embedding": memory.embedding,
                    "metadata": memory.metadata,
                }
            session_data = {
                "session_id": session_id,
                "saved_at": datetime.now().isoformat(),
                "memory_count": len(memories_data),
                "memories": memories_data,
            }
            path = os.path.join(self._session_dir, f"{session_id}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            logger.info("Session %s saved: %d memories to %s", session_id, len(memories_data), path)
            return path
        except Exception as e:
            logger.error("Failed to save session %s: %s", session_id, e, exc_info=True)
            return ""

    def load_session(self, session_id: str) -> bool:
        """Load session memories from disk (Phase 5.4)."""
        try:
            path = os.path.join(self._session_dir, f"{session_id}.json")
            if not os.path.exists(path):
                logger.debug("Session file not found: %s", path)
                return False
            with open(path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            memories_data = session_data.get("memories", {})
            loaded_count = 0
            for mem_id, mem_dict in memories_data.items():
                memory = Memory(
                    content=mem_dict["content"],
                    memory_type=mem_dict.get("memory_type", "short_term"),
                )
                memory.memory_id = mem_id
                try:
                    memory.created_at = datetime.fromisoformat(mem_dict["created_at"])
                    memory.last_accessed = datetime.fromisoformat(mem_dict["last_accessed"])
                except (KeyError, ValueError):
                    pass
                memory.access_count = mem_dict.get("access_count", 0)
                memory.embedding = mem_dict.get("embedding")
                memory.metadata = mem_dict.get("metadata", {})
                self.memories[mem_id] = memory
                loaded_count += 1
            logger.info("Session %s loaded: %d memories", session_id, loaded_count)
            return True
        except Exception as e:
            logger.error("Failed to load session %s: %s", session_id, e, exc_info=True)
            return False

    def get_memory_count(self) -> int:
        """Return total number of stored memories."""
        return len(self.memories)

    def search_by_embedding(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search memories by embedding similarity (Phase 5.4)."""
        try:
            if not query_embedding:
                return []
            scored = []
            for memory in self.memories.values():
                if memory.embedding is None:
                    continue
                similarity = self._cosine_similarity(query_embedding, memory.embedding)
                scored.append((similarity, memory))
            scored.sort(key=lambda x: x[0], reverse=True)
            results = []
            for sim, memory in scored[:top_k]:
                results.append({
                    "memory_id": memory.memory_id,
                    "content": memory.content,
                    "memory_type": memory.memory_type,
                    "similarity": sim,
                    "access_count": memory.access_count,
                })
            return results
        except Exception as e:
            logger.debug("Embedding search failed: %s", e)
            return []

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
