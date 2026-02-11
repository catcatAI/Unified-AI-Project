"""
Context Storage Interface Definition - Fixed Version

Angela Matrix Annotation:
- α: L0 (基础接口)
- β: 0.5 (抽象定义)
- γ: 1.0 (完整度)
- δ: 1.0 (稳定性)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class ContextType(Enum):
    TOOL = "tool"
    MODEL = "model"
    DIALOGUE = "dialogue"
    MEMORY = "memory"
    CUSTOM = "custom"

class ContextStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

class Context:
    """上下文数据结构"""

    def __init__(self, context_id: str, context_type: ContextType):
        """初始化上下文"""
        self.context_id = context_id
        self.context_type = context_type
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.status = ContextStatus.ACTIVE
        self.metadata: Dict[str, Any] = {}
        self.content: Dict[str, Any] = {}
        self.version = "1.0"
        self.tags: List[str] = []

    def update_content(self, new_content: Dict[str, Any]) -> None:
        """更新上下文内容"""
        self.content.update(new_content)
        self.updated_at = datetime.now()
        self.version = str(float(self.version) + 0.1)

    def update_metadata(self, new_metadata: Dict[str, Any]) -> None:
        """更新元数据"""
        self.metadata.update(new_metadata)
        self.updated_at = datetime.now()

    def add_tag(self, tag: str) -> None:
        """添加标签"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()

    def remove_tag(self, tag: str) -> None:
        """移除标签"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'context_id': self.context_id,
            'context_type': self.context_type.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'status': self.status.value,
            'metadata': self.metadata,
            'content': self.content,
            'version': self.version,
            'tags': self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Context':
        """从字典创建上下文"""
        # 这里可以实现从字典恢复上下文的逻辑
        # 为了简化, 暂时返回一个新的上下文实例
        context = cls(data['context_id'], ContextType(data['context_type']))
        context.created_at = datetime.fromisoformat(data['created_at'])
        context.updated_at = datetime.fromisoformat(data['updated_at'])
        context.status = ContextStatus(data['status'])
        context.metadata = data.get('metadata', {})
        context.content = data.get('content', {})
        context.version = data.get('version', '1.0')
        context.tags = data.get('tags', [])
        return context

class Storage(ABC):
    """存储接口"""

    @abstractmethod
    def save_context(self, context: Context) -> bool:
        """保存上下文"""
        pass

    @abstractmethod
    def load_context(self, context_id: str) -> Optional[Context]:
        """加载上下文"""
        pass

    @abstractmethod
    def delete_context(self, context_id: str) -> bool:
        """删除上下文"""
        pass

    @abstractmethod
    def list_contexts(self, context_type: Optional[ContextType] = None) -> List[str]:
        """列出所有上下文ID"""
        pass

    @abstractmethod
    def update_context_metadata(self, context_id: str, metadata: Dict[str, Any]) -> bool:
        """更新上下文元数据"""
        pass