"""
Memory Storage Implementation

Angela Matrix Annotation:
- α: L1 (内存实现)
- β: 0.6 (功能实现)
- γ: 1.0 (完整度)
- δ: 1.0 (稳定性)
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
import os
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import Context, ContextType, Storage

logger = logging.getLogger(__name__)

DEFAULT_MAX_SIZE = 1000
MAX_SIZE_ENV = "CONTEXT_MEMORY_MAX_SIZE"


def resolve_max_size(max_size: Optional[int] = None) -> int:
    """解析快取上限: 明確參數 > CONTEXT_MEMORY_MAX_SIZE > DEFAULT_MAX_SIZE。

    這個環境變數在 .env.example 有記載, 所以它必須真的被讀到。數值不合法時
    退回預設值而不是拋錯: 這段程式在 ContextManager 建構時執行, 一個 .env 裡
    的手誤不該把整個管理器在啟動時打壞。
    """
    if max_size is not None:
        return max_size
    raw = os.getenv(MAX_SIZE_ENV, "").strip()
    if not raw:
        return DEFAULT_MAX_SIZE
    try:
        value = int(raw)
    except ValueError:
        logger.warning(
            "%s=%r is not an integer; falling back to %d", MAX_SIZE_ENV, raw, DEFAULT_MAX_SIZE
        )
        return DEFAULT_MAX_SIZE
    if value <= 0:
        logger.warning(
            "%s=%d is not positive; falling back to %d", MAX_SIZE_ENV, value, DEFAULT_MAX_SIZE
        )
        return DEFAULT_MAX_SIZE
    return value


class MemoryStorage(Storage):
    """内存存储实现, 使用LRU缓存策略"""

    def __init__(self, max_size: Optional[int] = None) -> None:
        """初始化内存存储"""
        self.max_size = resolve_max_size(max_size)
        self._storage: OrderedDict[str, Context] = OrderedDict()

    def save_context(self, context: Context) -> bool:
        """保存上下文到内存"""
        try:
            # 如果已达到最大大小, 移除最旧的条目
            if len(self._storage) >= self.max_size:
                self._storage.popitem(last=False)

            # 保存上下文
            self._storage[context.context_id] = context
            # 移动到末尾(最近使用)
            self._storage.move_to_end(context.context_id)

            logger.debug(f"Context {context.context_id} saved to memory storage")
            return True
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(
                f"Failed to save context {context.context_id} to memory storage, {e}", exc_info=True
            )
            return False

    def load_context(self, context_id: str) -> Optional[Context]:
        """从内存加载上下文"""
        try:
            if context_id in self._storage:
                context = self._storage[context_id]
                # 移动到末尾(最近使用)
                self._storage.move_to_end(context_id)
                logger.debug(f"Context {context_id} loaded from memory storage")
                return context
            else:
                logger.debug(f"Context {context_id} not found in memory storage")
                return None
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(
                f"Failed to load context {context_id} from memory storage, {e}", exc_info=True
            )
            return None

    def delete_context(self, context_id: str) -> bool:
        """从内存删除上下文"""
        try:
            if context_id in self._storage:
                del self._storage[context_id]
                logger.debug(f"Context {context_id} deleted from memory storage")
                return True
            else:
                logger.debug(f"Context {context_id} not found in memory storage for deletion")
                return False
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(
                f"Failed to delete context {context_id} from memory storage, {e}", exc_info=True
            )
            return False

    def list_contexts(self, context_type: Optional[ContextType] = None) -> List[str]:
        """列出内存中的上下文ID"""
        try:
            if context_type is None:
                context_ids = list(self._storage.keys())
            else:
                context_ids = [
                    context_id
                    for context_id, context in self._storage.items()
                    if context.context_type == context_type
                ]

            logger.debug(f"Listed {len(context_ids)} contexts from memory storage")
            return context_ids
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(f"Failed to list contexts from memory storage, {e}", exc_info=True)
            return []

    def update_context_metadata(self, context_id: str, metadata: Dict[str, Any]) -> bool:
        """更新上下文元数据"""
        try:
            if context_id in self._storage:
                context = self._storage[context_id]
                context.metadata.update(metadata)
                context.updated_at = datetime.now()
                # 移动到末尾(最近使用)
                self._storage.move_to_end(context_id)
                logger.debug(f"Context {context_id} metadata updated in memory storage")
                return True
            else:
                logger.debug(
                    f"Context {context_id} not found in memory storage for metadata update"
                )
                return False
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(
                f"Failed to update context {context_id} metadata in memory storage, {e}",
                exc_info=True,
            )
            return False

    def get_storage_info(self) -> Dict[str, Any]:
        """获取存储信息"""
        return {
            "total_contexts": len(self._storage),
            "max_size": self.max_size,
            "usage_percentage": (
                (len(self._storage) / self.max_size) * 100 if self.max_size > 0 else 0
            ),
        }
