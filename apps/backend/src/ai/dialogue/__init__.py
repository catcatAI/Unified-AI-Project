"""
Angela AI - Dialogue Module
对话管理模块

提供对话流程管理、意图识别、响应生成和会话管理功能
"""

from .dialogue_manager import DialogueManager
from .project_coordinator import ProjectCoordinator
import logging
logger = logging.getLogger(__name__)

__all__ = [
    'DialogueManager',
    'ProjectCoordinator',
]
