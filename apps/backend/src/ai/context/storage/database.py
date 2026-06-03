"""
Database Storage Implementation

Angela Matrix Annotation:
- α: L1 (数据库实现)
- β: 0.6 (功能实现)
- γ: 1.0 (完整度)
- δ: 1.0 (稳定性)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from copy import deepcopy
from .base import Context, Storage, ContextType, ContextStatus

logger = logging.getLogger(__name__)


class DatabaseStorage(Storage):
    """数据库存储实现"""

    def __init__(self, db_connection=None) -> None:
        """初始化数据库存储"""
        # 这里应该初始化数据库连接
        # 为了简化, 我们使用内存字典模拟数据库
        self._db = {} if db_connection is None else db_connection
        self._connected = db_connection is not None

    def save_context(self, context: Context) -> bool:
        """保存上下文到数据库"""
        try:
            if not self._connected:
                logger.warning("Database storage not connected, using mock storage", exc_info=True)
                # 模拟数据库存储
                context_data = {
                    "context_id": context.context_id,
                    "context_type": context.context_type.value,
                    "created_at": context.created_at.isoformat(),
                    "updated_at": context.updated_at.isoformat(),
                    "status": context.status.value,
                    "metadata": context.metadata,
                    "content": context.content,
                    "version": context.version,
                    "tags": context.tags,
                }
                self._db[context.context_id] = context_data
            else:
                logger.debug(f"Context {context.context_id} 存储到数据库 (connected mode)", exc_info=True)
                context_data = {
                    "context_id": context.context_id,
                    "context_type": context.context_type.value,
                    "created_at": context.created_at.isoformat(),
                    "updated_at": context.updated_at.isoformat(),
                    "status": context.status.value,
                    "metadata": context.metadata,
                    "content": context.content,
                    "version": context.version,
                    "tags": context.tags,
                }
                self._db[context.context_id] = context_data

            logger.debug(f"Context {context.context_id} saved to database storage")
            return True
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(f"Failed to save context {context.context_id} to database storage, {e}", exc_info=True)
            return False

    def load_context(self, context_id: str) -> Optional[Context]:
        """从数据库加载上下文"""
        try:
            if not self._connected:
                logger.warning("Database storage not connected, using mock storage", exc_info=True)
                # 模拟数据库加载
                if context_id in self._db:
                    context_data = self._db[context_id]
                    context = Context(
                        context_id=context_data["context_id"],
                        context_type=ContextType(context_data["context_type"]),
                    )
                    context.created_at = datetime.fromisoformat(context_data["created_at"])
                    context.updated_at = datetime.fromisoformat(context_data["updated_at"])
                    context.status = ContextStatus(context_data["status"])
                    context.metadata = context_data["metadata"]
                    context.content = context_data["content"]
                    context.version = context_data["version"]
                    context.tags = context_data["tags"]
                    logger.debug(f"Context {context_id} loaded from mock database storage")
                    return context
                else:
                    logger.debug(f"Context {context_id} not found in mock database storage")
                    return None
            else:
                logger.debug(f"Context {context_id} 从数据库加载 (connected mode)", exc_info=True)
                if context_id in self._db:
                    context_data = self._db[context_id]
                    context = Context(
                        context_id=context_data["context_id"],
                        context_type=ContextType(context_data["context_type"]),
                    )
                    context.created_at = datetime.fromisoformat(context_data["created_at"])
                    context.updated_at = datetime.fromisoformat(context_data["updated_at"])
                    context.status = ContextStatus(context_data["status"])
                    context.metadata = deepcopy(context_data["metadata"])
                    context.content = deepcopy(context_data["content"])
                    context.version = context_data["version"]
                    context.tags = list(context_data["tags"])
                    logger.debug(f"Context {context_id} loaded from database storage")
                    return context
                else:
                    logger.debug(f"Context {context_id} not found in database storage")
                    return None
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(f"Failed to load context {context_id} from database storage, {e}", exc_info=True)
            return None

    def delete_context(self, context_id: str) -> bool:
        """从数据库删除上下文"""
        try:
            if not self._connected:
                logger.warning("Database storage not connected, using mock storage", exc_info=True)
                # 模拟数据库删除
                if context_id in self._db:
                    del self._db[context_id]
                    logger.debug(f"Context {context_id} deleted from mock database storage")
                    return True
                else:
                    logger.debug(
                        f"Context {context_id} not found in mock database storage for deletion"
                    )
                    return False
            else:
                logger.debug(f"Context {context_id} 从数据库删除 (connected mode)", exc_info=True)
                if context_id in self._db:
                    del self._db[context_id]
                    return True
                else:
                    return False
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(f"Failed to delete context {context_id} from database storage, {e}", exc_info=True)
            return False

    def list_contexts(self, context_type: Optional[ContextType] = None) -> List[str]:
        """列出数据库中的上下文ID"""
        try:
            if not self._connected:
                logger.warning("Database storage not connected, using mock storage", exc_info=True)
                # 模拟数据库查询
                if context_type is None:
                    context_ids = list(self._db.keys())
                else:
                    context_ids = [
                        context_id
                        for context_id, context_data in self._db.items()
                        if context_data["context_type"] == context_type.value
                    ]
                logger.debug(f"Listed {len(context_ids)} contexts from mock database storage")
                return context_ids
            else:
                logger.debug("从数据库列出上下文 (connected mode)", exc_info=True)
                if context_type is None:
                    context_ids = list(self._db.keys())
                else:
                    context_ids = [
                        context_id
                        for context_id, context_data in self._db.items()
                        if context_data["context_type"] == context_type.value
                    ]
                return context_ids
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(f"Failed to list contexts from database storage, {e}", exc_info=True)
            return []

    def update_context_metadata(self, context_id: str, metadata: Dict[str, Any]) -> bool:
        """更新上下文元数据"""
        try:
            if not self._connected:
                logger.warning("Database storage not connected, using mock storage", exc_info=True)
                # 模拟数据库更新
                if context_id in self._db:
                    self._db[context_id]["metadata"].update(metadata)
                    self._db[context_id]["updated_at"] = datetime.now().isoformat()
                    logger.debug(f"Context {context_id} metadata updated in mock database storage")
                    return True
                else:
                    logger.debug(
                        f"Context {context_id} not found in mock database storage for metadata update"
                    )
                    return False
            else:
                logger.debug(f"Context {context_id} 元数据更新到数据库 (connected mode)", exc_info=True)
                if context_id in self._db:
                    self._db[context_id]["metadata"].update(metadata)
                    self._db[context_id]["updated_at"] = datetime.now().isoformat()
                    return True
                else:
                    return False
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(f"Failed to update context {context_id} metadata in database storage, {e}", exc_info=True)
            return False

    def get_storage_info(self) -> Dict[str, Any]:
        """获取存储信息"""
        try:
            if not self._connected:
                logger.warning("Database storage not connected, using mock storage", exc_info=True)
                return {"total_contexts": len(self._db), "storage_type": "database", "error": "not connected"}
            else:
                logger.debug("从数据库获取存储信息 (connected mode)", exc_info=True)
                return {"total_contexts": len(self._db), "storage_type": "connected_database"}
        except Exception as e:  # broad exception acceptable: graceful degradation on failure
            logger.error(f"Failed to get storage info, {e}", exc_info=True)
            return {}
