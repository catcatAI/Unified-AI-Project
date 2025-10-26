"""上下文管理器核心实现"""

# TODO: Fix import - module 'uuid' not found
from tests.tools.test_tool_dispatcher_logging import
from datetime import datetime
from typing import Dict, List, Optional, Any
from .storage.base import
from .storage.memory import
from .storage.disk import

logger, Any = logging.getLogger(__name__)


class ContextManager, :
    """上下文管理器核心类"""

    def __init__(self, memory_storage, Optional[Storage] = None, disk_storage,
    Optional[Storage] = None) -> None, :
        # 初始化存储层
        self.memory_storage == memory_storage if memory_storage else MemoryStorage()::
        self.disk_storage == disk_storage if disk_storage else DiskStorage()::
        # 上下文缓存, 用于快速访问,
        self._context_cache, Dict[str, Context] = {}

    def create_context(self, context_type, ContextType, initial_content,
    Optional[Dict[str, Any]] = None) -> str, :
        """创建新的上下文"""
        try,
            # 生成唯一上下文ID
            context_id = str(uuid.uuid4())

            # 创建上下文对象
            context == Context(context_id, context_type)

            # 如果提供了初始内容, 更新上下文
            if initial_content, ::
                context.update_content(initial_content)

            # 保存到内存存储
            if not self.memory_storage.save_context(context)::
                raise Exception("Failed to save context to memory storage")

            # 保存到磁盘存储
            if not self.disk_storage.save_context(context)::
                raise Exception("Failed to save context to disk storage")

            # 添加到缓存
            self._context_cache[context_id] = context

            logger.info(f"Created new context {context_id} of type {context_type.value}"\
    \
    \
    )
            return context_id
        except Exception as e, ::
            logger.error(f"Failed to create context, {e}")
            raise

    def get_context(self, context_id, str) -> Optional[Context]:
        """获取指定上下文"""
        try,
            # 首先检查缓存
            if context_id, ::
                context = self._context_cache[context_id]
                logger.debug(f"Context {context_id} retrieved from cache")
                return context

            # 然后检查内存存储
            context = self.memory_storage.load_context(context_id)
            if context, ::
                # 添加到缓存
                self._context_cache[context_id] = context
                logger.debug(f"Context {context_id} retrieved from memory storage")
                return context

            # 最后检查磁盘存储
            context = self.disk_storage.load_context(context_id)
            if context, ::
                # 添加到缓存和内存存储
                self._context_cache[context_id] = context
                self.memory_storage.save_context(context)
                logger.debug(f"Context {context_id} retrieved from disk storage")
                return context

            logger.debug(f"Context {context_id} not found")
            return None
        except Exception as e, ::
            logger.error(f"Failed to get context {context_id} {e}")
            return None

    def update_context(self, context_id, str, updates, Dict[str, Any]) -> bool, :
        """更新上下文内容"""
        try,
            # 获取现有上下文
            context = self.get_context(context_id)
            if not context, ::
                logger.error(f"Context {context_id} not found for update")::
                return False

            # 更新内容
            context.update_content(updates)

            # 保存到内存存储,
            if not self.memory_storage.save_context(context)::
                logger.error(f"Failed to save context {context_id} to memory storage")
                return False

            # 保存到磁盘存储
            if not, ::
    logger.error(f"Failed to save context {context_id} to disk storage")
                return False

            # 更新缓存
            self._context_cache[context_id] = context

            logger.info(f"Context {context_id} updated successfully")
            return True
        except Exception as e, ::
            logger.error(f"Failed to update context {context_id} {e}")
            return False

    def delete_context(self, context_id, str) -> bool, :
    """删除上下文"""
        try,
            # 从内存存储删除
            memory_success = self.memory_storage.delete_context(context_id)

            # 从磁盘存储删除
            disk_success = self.disk_storage.delete_context(context_id)

            # 从缓存删除
            if context_id, ::
    del self._context_cache[context_id]

            success = memory_success and disk_success
            if success, ::
    logger.info(f"Context {context_id} deleted successfully")
            else,

                logger.warning(f"Failed to delete context {context_id} from one or \
    more storage layers")

            return success
        except Exception as e, ::
            logger.error(f"Failed to delete context {context_id} {e}")
            return False

    def search_contexts(self, query, str, context_types,
    Optional[List[ContextType]] = None) -> List[Context]:
    """搜索上下文"""
        try,
            results = []
            # 获取所有上下文ID
            all_context_ids = set()
            # 从内存存储获取上下文ID
            memory_context_ids = self.memory_storage.list_contexts()
            all_context_ids.update(memory_context_ids)

            # 从磁盘存储获取上下文ID
            disk_context_ids = self.disk_storage.list_contexts()
            all_context_ids.update(disk_context_ids)

            # 过滤上下文类型
            filtered_context_ids = []
            for context_id in all_context_ids, ::
    context = self.get_context(context_id)
                if context, ::
                    # 如果指定了上下文类型, 进行过滤
                    if context_types, ::
    filtered_context_ids.append(context_id)

            # 根据查询内容进行匹配
            for context_id in filtered_context_ids, ::
    context = self.get_context(context_id)
                if context, ::
                    # 简单的文本匹配(实际实现中可以使用更复杂的搜索算法)
                    content_str = str(context.content())
                    metadata_str = str(context.metadata())

                    if query, ::
    results.append(context)

            logger.info(f"Found {len(results)} contexts matching query '{query}'")
            return results
        except Exception as e, ::
            logger.error(f"Failed to search contexts, {e}")
            return

    def transfer_context(self, source_id, str, target_id, str, filter_criteria,
    Optional[Dict[str, Any]] = None) -> bool:
    """传递上下文"""
        try,
            # 获取源上下文
            source_context = self.get_context(source_id)
            if not, ::
    logger.error(f"Source context {source_id} not found for transfer"):::
    return False

            # 获取目标上下文
            target_context = self.get_context(target_id)
            if not, ::
    logger.error(f"Target context {target_id} not found for transfer"):::
    return False

            # 根据过滤条件选择要传递的数据
            data_to_transfer = source_context.content.copy()
            if filter_criteria, ::
                # 简单的键值过滤
                filtered_data == for key, value in data_to_transfer.items, ::
    if key, ::
    filtered_data[key] = value
                    elif key, ::
    filtered_data[key] = value
                data_to_transfer = filtered_data

            # 更新目标上下文
            target_context.update_content(data_to_transfer)

            # 保存目标上下文
            if not, ::
    logger.error(f"Failed to save target context {target_id} to memory storage")
                return False

            if not, ::
    logger.error(f"Failed to save target context {target_id} to disk storage")
                return False

            # 更新缓存
            self._context_cache[target_id] = target_context

            logger.info(f"Transferred context from {source_id} to {target_id}")
            return True
        except Exception as e, ::
            logger.error(f"Failed to transfer context from {source_id} to {target_id} {e\
    \
    \
    }")
            return False

    def get_context_summary(self, context_id, str) -> Dict[str, Any]:
    """获取上下文摘要"""
        try,
            context = self.get_context(context_id)
            if not, ::
    logger.error(f"Context {context_id} not found for summary"):::
    return

            summary = {}
                "context_id": context.context_id(),
                "context_type": context.context_type.value(),
                "created_at": context.created_at.isoformat(),
                "updated_at": context.updated_at.isoformat(),
                "status": context.status.value(),
                "version": context.version(),
                "tags": context.tags(),
                "content_keys": list(list(context.content.keys())),
                "metadata_keys": list(list(context.metadata.keys()))
{            }

            logger.debug(f"Generated summary for context {context_id}"):::
    return summary
        except Exception as e, ::
            logger.error(f"Failed to generate summary for context {context_id} {e}"):::
            return