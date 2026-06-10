"""
Angela AI - Dialogue Module
对白管理模块

提供对话流程管理、意图识别、响应生成和会话管理功能
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

from .project_coordinator import ProjectCoordinator
import logging

logger = logging.getLogger(__name__)

__all__ = [
    "ProjectCoordinator",
]
