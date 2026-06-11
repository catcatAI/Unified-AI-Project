"""
Unified AI Project - 集成模块
提供与外部服务和平台的集成功能
"""

try:
    from .rovo_dev_connector import RovoDevConnector
except ImportError:
    RovoDevConnector = None
from .rovo_dev_agent import RovoDevAgent
try:
    from .atlassian_bridge import AtlassianBridge
except ImportError:
    AtlassianBridge = None
from .google_drive_service import GoogleDriveService
from .os_bridge_adapter import OSBridgeAdapter
try:
    from . import atlassian_bridge
except ImportError:
    atlassian_bridge = None

__all__ = [
    "RovoDevConnector",
    "RovoDevAgent",
    "AtlassianBridge",
    "GoogleDriveService",
    "OSBridgeAdapter",
]
