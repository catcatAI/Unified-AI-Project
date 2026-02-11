"""
Context Storage Interface Definition

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

    def update_content(self, new_content: Dict[str, Any]):
        """更新上下文内容"""
        self.content.update(new_content)
        self.updated_at = datetime.now()

    def add_tag(self, tag: str):
        """添加标签"""
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str):
        """移除标签"""
        if tag in self.tags:
            self.tags.remove(tag)

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
        """列出上下文"""
        pass

    @abstractmethod
    def update_context_metadata(self, context_id: str, metadata: Dict[str, Any]) -> bool:
        """更新上下文元数据"""
        pass