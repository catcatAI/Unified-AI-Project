# =============================================================================
# FILE_HASH: CTXINIT01
# FILE_PATH: apps/backend/src/ai/context/__init__.py
# FILE_TYPE: module_init
# PURPOSE: 上下文系统模块初始化 - 导出核心组件
# VERSION: 6.2.1
# STATUS: production_ready
# LAST_MODIFIED: 2026-02-19
# CHANGE_LOG: 添加 ContextManager 导出
# =============================================================================

"""上下文系统模块初始化"""
# Angela Matrix: [L2:MEM] [L4:CTX] Context system initialization

# 从修复版本导入 ContextManager
from .manager_fixed import ContextManager
from .storage.base import Context, ContextType, ContextStatus
from .storage.memory import MemoryStorage
from .storage.disk import DiskStorage

__all__ = [
    "ContextManager",  # 主要导出 - 修复版本
    "Context",
    "ContextType",
    "ContextStatus",
    "MemoryStorage",
    "DiskStorage",
    "DatabaseStorage",
    "ToolContextManager",
    "ToolCategory",
    "Tool",
    "ModelContextManager",
    "AgentContextManager",
    "DialogueContextManager",
    "MemoryContextManager",
]
