"""
实时同步系統 - 系統間的實時數據同步和狀態同步
Real-time sync system for inter-system data and state synchronization
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SyncEventType(Enum):
    """同步事件類型 / Sync event types"""
    DATA_UPDATE = "data_update"
    STATUS_CHANGE = "status_change"
    MODEL_UPDATE = "model_update"
    AGENT_ACTION = "agent_action"
    SYSTEM_ALERT = "system_alert"
    USER_ACTION = "user_action"
    TRAINING_PROGRESS = "training_progress"


class SyncEvent:
    """同步事件 / Sync event"""
    def __init__(
        self,
        id: str,
        event_type: SyncEventType,
        source: str,
        data: Dict[str, Any],
        priority: int = 1
    ):
        self.id = id
        self.type = event_type
        self.source = source
        self.target = None
        self.data = data
        self.timestamp = datetime.now()
        self.priority = priority
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典 / Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value if hasattr(self.type, 'value') else str(self.type),
            "source": self.source,
            "target": self.target,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority
        }


class SyncManager:
    """同步管理器 / Sync manager"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._clients: Dict[str, Any] = {}
        self._event_queue: List[SyncEvent] = []
    
    async def initialize(self):
        """初始化 / Initialize"""
        logger.info("同步管理器初始化完成")
        return True
    
    async def shutdown(self):
        """關閉 / Shutdown"""
        self._clients.clear()
        self._event_queue.clear()
        logger.info("同步管理器已關閉")
    
    async def sync_system_status(
        self,
        system_id: str,
        status: Dict[str, Any]
    ):
        """同步系統狀態 / Sync system status"""
        logger.info(f"同步系統狀態: {system_id}")
        return True
    
    async def register_client(
        self,
        client_id: str,
        callback: Callable
    ):
        """註冊客戶端 / Register client"""
        self._clients[client_id] = callback
        logger.info(f"客戶端已註冊: {client_id}")
    
    async def unregister_client(self, client_id: str):
        """註銷客戶端 / Unregister client"""
        if client_id in self._clients:
            del self._clients[client_id]
        logger.info(f"客戶端已註銷: {client_id}")
    
    async def broadcast_event(self, event: SyncEvent):
        """廣播事件 / Broadcast event"""
        for client_id, callback in self._clients.items():
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"廣播事件失敗: {e}")


# 全局同步管理器實例
sync_manager = SyncManager()
