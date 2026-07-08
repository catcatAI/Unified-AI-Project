"""
Unified AI Project - 集成模块
提供与外部服务和平台的集成功能
"""

from .google_drive_service import GoogleDriveService
from .os_bridge_adapter import OSBridgeAdapter

__all__ = [
    "GoogleDriveService",
    "OSBridgeAdapter",
]
