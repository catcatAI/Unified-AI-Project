"""上下文存储接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class ContextType(Enum)
    TOOL = "tool"
    MODEL = "model"
    DIALOGUE = "dialogue"
    MEMORY = "memory"
    CUSTOM = "custom"

class ContextStatus(Enum)
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

class Context:
    def __init__(self, context_id: str, context_type: ContextType) -> None:
    self.context_id = context_id
    self.context_type = context_type
    self.created_at = datetime.now
    self.updated_at = datetime.now
    self.status = ContextStatus.ACTIVE
    self.metadata: Dict[str, Any] =
    self.content: Dict[str, Any] =
    self.version = "1.0"
    self.tags: List[str] =

    def update_content(self, new_content: Dict[str, Any])
    self.content.update(new_content)
    self.updated_at = datetime.now

    def add_tag(self, tag: str)
    if tag not in self.tags:

    self.tags.append(tag)

    def remove_tag(self, tag: str)
    if tag in self.tags:

    self.tags.remove(tag)

class Storage(ABC)
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