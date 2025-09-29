"""磁盘存储实现"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from .base import Storage, Context, ContextType

logger: Any = logging.getLogger(__name__)

class DiskStorage(Storage):
    """磁盘存储实现"""
    
    def __init__(self, storage_dir: str = "./context_storage") -> None:
        self.storage_dir = storage_dir
        # 确保存储目录存在
        os.makedirs(self.storage_dir, exist_ok=True)
        
    def _get_context_file_path(self, context_id: str) -> str:
        """获取上下文文件路径"""
        return os.path.join(self.storage_dir, f"{context_id}.json")
    
    def _context_to_dict(self, context: Context) -> Dict[str, Any]:
        """将Context对象转换为字典"""
        return {
            "context_id": context.context_id,
            "context_type": context.context_type.value,
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat(),
            "status": context.status.value,
            "metadata": context.metadata,
            "content": context.content,
            "version": context.version,
            "tags": context.tags
        }
    
    def _dict_to_context(self, data: Dict[str, Any]) -> Context:
        """将字典转换为Context对象"""
        context = Context(
            context_id=data["context_id"],
            context_type=ContextType(data["context_type"])
        )
        context.created_at = datetime.fromisoformat(data["created_at"])
        context.updated_at = datetime.fromisoformat(data["updated_at"])
        context.status = ContextType(data["status"])
        context.metadata = data["metadata"]
        context.content = data["content"]
        context.version = data["version"]
        context.tags = data["tags"]
        return context
    
    def save_context(self, context: Context) -> bool:
        """保存上下文到磁盘"""
        try:
            file_path = self._get_context_file_path(context.context_id)
            
            # 将上下文转换为字典并保存为JSON文件
            context_data = self._context_to_dict(context)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(context_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Context {context.context_id} saved to disk storage at {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save context {context.context_id} to disk storage: {e}")
            return False
    
    def load_context(self, context_id: str) -> Optional[Context]:
        """从磁盘加载上下文"""
        try:
            file_path = self._get_context_file_path(context_id)
            
            if not os.path.exists(file_path):
                logger.debug(f"Context {context_id} not found in disk storage")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                context_data = json.load(f)
            
            context = self._dict_to_context(context_data)
            logger.debug(f"Context {context_id} loaded from disk storage")
            return context
        except Exception as e:
            logger.error(f"Failed to load context {context_id} from disk storage: {e}")
            return None
    
    def delete_context(self, context_id: str) -> bool:
        """从磁盘删除上下文"""
        try:
            file_path = self._get_context_file_path(context_id)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Context {context_id} deleted from disk storage")
                return True
            else:
                logger.debug(f"Context {context_id} not found in disk storage for deletion")
                return False
        except Exception as e:
            logger.error(f"Failed to delete context {context_id} from disk storage: {e}")
            return False
    
    def list_contexts(self, context_type: Optional[ContextType] = None) -> List[str]:
        """列出磁盘中的上下文ID"""
        try:
            context_ids = []
            
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json"):
                    context_id = filename[:-5]  # 移除.json后缀
                    
                    # 如果指定了上下文类型，需要加载上下文来检查类型
                    if context_type is not None:
                        context = self.load_context(context_id)
                        if context and context.context_type == context_type:
                            context_ids.append(context_id)
                    else:
                        context_ids.append(context_id)
            
            logger.debug(f"Listed {len(context_ids)} contexts from disk storage")
            return context_ids
        except Exception as e:
            logger.error(f"Failed to list contexts from disk storage: {e}")
            return []
    
    def update_context_metadata(self, context_id: str, metadata: Dict[str, Any]) -> bool:
        """更新上下文元数据"""
        try:
            context = self.load_context(context_id)
            if context:
                context.metadata.update(metadata)
                context.updated_at = datetime.now()
                return self.save_context(context)
            else:
                logger.debug(f"Context {context_id} not found in disk storage for metadata update")
                return False
        except Exception as e:
            logger.error(f"Failed to update context {context_id} metadata in disk storage: {e}")
            return False
    
    def get_storage_info(self) -> Dict[str, Any]:
        """获取存储信息"""
        try:
            total_size = 0
            file_count = 0
            
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(self.storage_dir, filename)
                    total_size += os.path.getsize(file_path)
                    file_count += 1
            
            return {
                "total_contexts": file_count,
                "total_size_bytes": total_size,
                "storage_dir": self.storage_dir
            }
        except Exception as e:
            logger.error(f"Failed to get storage info: {e}")
            return {}