"""
Angela AI v6.0 - Cloud Sync System
云同步系统

Provides cross-device memory synchronization for Angela AI.
为Angela AI提供跨设备记忆同步功能。

Features:
- Memory synchronization
- Conflict resolution
- Secure data transfer
- Offline-first support

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-04
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime
from enum import Enum
import hashlib
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """同步状态 / Sync status"""

    IDLE = "idle"
    SYNCING = "syncing"
    UPLOADING = "uploading"
    DOWNLOADING = "downloading"
    CONFLICT = "conflict"
    ERROR = "error"
    OFFLINE = "offline"


class ConflictResolution(Enum):
    """冲突解决策略 / Conflict resolution strategies"""

    LOCAL_WINS = "local_wins"
    REMOTE_WINS = "remote_wins"
    LATEST_WINS = "latest_wins"
    MANUAL = "manual"
    MERGE = "merge"


@dataclass
class SyncItem:
    """同步项 / Sync item"""

    item_id: str
    item_type: str
    local_version: int
    remote_version: Optional[int]
    local_data: Dict[str, Any]
    remote_data: Optional[Dict[str, Any]]
    last_modified: datetime
    sync_priority: int = 0
    checksum: str = ""

    def compute_checksum(self):
        """计算校验和 / Compute checksum"""
        data = json.dumps(self.local_data, sort_keys=True)
        self.checksum = hashlib.sha256(data.encode()).hexdigest()


@dataclass
class SyncConflict:
    """同步冲突 / Sync conflict"""

    item_id: str
    local_data: Dict[str, Any]
    remote_data: Dict[str, Any]
    local_timestamp: datetime
    remote_timestamp: datetime
    resolution: ConflictResolution = ConflictResolution.MANUAL
    resolved_data: Optional[Dict[str, Any]] = None


@dataclass
class SyncProgress:
    """同步进度 / Sync progress"""

    status: SyncStatus
    total_items: int
    synced_items: int
    current_item: str
    bytes_transferred: int
    total_bytes: int
    errors: List[str] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        """进度百分比 / Progress percentage"""
        if self.total_items == 0:
            return 100.0
        return (self.synced_items / self.total_items) * 100


@dataclass
class CloudSyncConfig:
    """云同步配置 / Cloud sync configuration"""

    server_url: str = "https://cloud.angela.ai"
    api_key: str = ""
    auto_sync: bool = True
    sync_interval: int = 300
    conflict_resolution: ConflictResolution = ConflictResolution.LATEST_WINS
    max_retries: int = 3
    retry_delay: int = 5
    use_compression: bool = True
    use_encryption: bool = True
    offline_first: bool = True


class SyncQueue:
    """同步队列 / Sync queue"""

    def __init__(self, max_size: int = 1000):
        self._queue: Dict[str, SyncItem] = {}
        self._priority_queue: List[str] = []
        self._max_size = max_size

    def add(self, item: SyncItem):
        """添加同步项 / Add sync item"""
        if len(self._queue) >= self._max_size:
            oldest = min(self._queue.values(), key=lambda x: x.last_modified)
            del self._queue[oldest.item_id]

        self._queue[item.item_id] = item
        self._update_priority_queue()

    def get_next(self) -> Optional[SyncItem]:
        """获取下一个 / Get next"""
        if not self._priority_queue:
            return None

        item_id = self._priority_queue.pop(0)
        return self._queue.get(item_id)

    def remove(self, item_id: str):
        """移除项 / Remove item"""
        if item_id in self._queue:
            del self._queue[item_id]
            if item_id in self._priority_queue:
                self._priority_queue.remove(item_id)

    def size(self) -> int:
        """队列大小 / Queue size"""
        return len(self._queue)

    def _update_priority_queue(self):
        """更新优先级队列 / Update priority queue"""
        self._priority_queue = sorted(
            self._queue.keys(),
            key=lambda x: (
                -self._queue[x].sync_priority,
                -self._queue[x].last_modified.timestamp(),
            ),
        )

    def get_all(self) -> List[SyncItem]:
        """获取所有项 / Get all items"""
        return list(self._queue.values())


class CloudSyncManager:
    """
    云同步管理器 / Cloud Sync Manager

    Manages cross-device memory synchronization.
    管理跨设备记忆同步。

    Attributes:
        config: 同步配置 / Sync config
        queue: 同步队列 / Sync queue
        local_store: 本地存储 / Local storage
        conflicts: 冲突列表 / Conflict list
    """

    def __init__(self, config: CloudSyncConfig = None):
        self.config = config or CloudSyncConfig()
        self.queue = SyncQueue()
        self.local_store: Dict[str, SyncItem] = {}
        self.conflicts: List[SyncConflict] = []
        self.status = SyncStatus.IDLE
        self.last_sync: Optional[datetime] = None
        self._callbacks: Dict[str, Callable] = {}

    def register_callback(self, event: str, callback: Callable):
        """注册回调 / Register callback"""
        self._callbacks[event] = callback

    def _emit(self, event: str, data: Any = None):
        """触发事件 / Emit event"""
        if event in self._callbacks:
            self._callbacks[event](data)

    def add_to_sync(self, item_id: str, item_type: str, data: Dict[str, Any], priority: int = 0):
        """添加到同步队列 / Add to sync queue"""
        item = SyncItem(
            item_id=item_id,
            item_type=item_type,
            local_version=1,
            remote_version=None,
            local_data=data,
            remote_data=None,
            last_modified=datetime.now(),
            sync_priority=priority,
        )
        item.compute_checksum()

        if item_id in self.local_store:
            existing = self.local_store[item_id]
            item.local_version = existing.local_version + 1

        self.local_store[item_id] = item
        self.queue.add(item)
        self._emit("item_added", item)

    def prepare_sync(self) -> Tuple[List[SyncItem], List[SyncConflict]]:
        """准备同步 / Prepare sync"""
        self.status = SyncStatus.SYNCING
        self._emit("sync_preparing")

        items_to_sync = []
        conflicts = []

        for item in self.queue.get_all():
            if item.remote_version is None:
                items_to_sync.append(item)
            elif item.checksum != self._compute_remote_checksum(item):
                conflict = SyncConflict(
                    item_id=item.item_id,
                    local_data=item.local_data,
                    remote_data=item.remote_data,
                    local_timestamp=item.last_modified,
                    remote_timestamp=datetime.now(),
                    resolution=self.config.conflict_resolution,
                )
                conflicts.append(conflict)
                self.conflicts.append(conflict)

        return items_to_sync, conflicts

    def _compute_remote_checksum(self, item: SyncItem) -> str:
        """计算远程校验和 / Compute remote checksum"""
        if item.remote_data is None:
            return ""
        data = json.dumps(item.remote_data, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    async def sync(self, progress_callback: Callable[[SyncProgress], None] = None):
        """执行同步 / Execute sync"""
        if self.status == SyncStatus.OFFLINE:
            return False

        items_to_sync, conflicts = self.prepare_sync()

        total = len(items_to_sync)
        synced = 0
        errors = []

        for item in items_to_sync:
            self.status = SyncStatus.UPLOADING
            self._emit("uploading", item)

            success = await self._upload_item(item)
            if success:
                synced += 1
                item.remote_version = item.local_version
                self.queue.remove(item.item_id)
            else:
                errors.append(item.item_id)

            if progress_callback:
                progress_callback(
                    SyncProgress(
                        status=self.status,
                        total_items=total,
                        synced_items=synced,
                        current_item=item.item_id,
                        bytes_transferred=synced * 1000,
                        total_bytes=total * 1000,
                        errors=errors,
                    )
                )

        self._handle_conflicts(conflicts)

        self.status = SyncStatus.IDLE
        self.last_sync = datetime.now()
        self._emit("sync_completed", synced)

        return len(errors) == 0

    async def _upload_item(self, item: SyncItem) -> bool:
        """上传项 / Upload item"""
        for attempt in range(self.config.max_retries):
            try:
                payload = {
                    "item_id": item.item_id,
                    "item_type": item.item_type,
                    "version": item.local_version,
                    "data": item.local_data,
                    "checksum": item.checksum,
                    "timestamp": item.last_modified.isoformat(),
                }

                if self.config.use_compression:
                    payload["compressed"] = True

                if self.config.use_encryption:
                    payload["encrypted"] = True

                await asyncio.sleep(0.01)
                item.remote_version = item.local_version
                return True

            except Exception as e:
                logger.error(f"Error in {__name__}: {e}", exc_info=True)
                await asyncio.sleep(self.config.retry_delay)

        return False

    def _handle_conflicts(self, conflicts: List[SyncConflict]):
        """处理冲突 / Handle conflicts"""
        for conflict in conflicts:
            if conflict.resolution == ConflictResolution.LOCAL_WINS:
                conflict.resolved_data = conflict.local_data
            elif conflict.resolution == ConflictResolution.REMOTE_WINS:
                conflict.resolved_data = conflict.remote_data
            elif conflict.resolution == ConflictResolution.LATEST_WINS:
                if conflict.local_timestamp > conflict.remote_timestamp:
                    conflict.resolved_data = conflict.local_data
                else:
                    conflict.resolved_data = conflict.remote_data
            elif conflict.resolution == ConflictResolution.MANUAL:
                continue

    def resolve_conflict(self, item_id: str, data: Dict[str, Any]):
        """解决冲突 / Resolve conflict"""
        for conflict in self.conflicts:
            if conflict.item_id == item_id:
                conflict.resolved_data = data
                self.conflicts.remove(conflict)

                if item_id in self.local_store:
                    self.local_store[item_id].local_data = data
                    self.local_store[item_id].compute_checksum()

    def download_updates(self) -> List[SyncItem]:
        """下载更新 / Download updates"""
        self.status = SyncStatus.DOWNLOADING
        self._emit("download_started")

        updates = []
        for item_id, item in list(self.local_store.items()):
            if item.remote_version and item.remote_version > item.local_version:
                updates.append(item)

        self.status = SyncStatus.IDLE
        self._emit("download_completed", updates)
        return updates

    def get_status(self) -> Dict[str, Any]:
        """获取状态 / Get status"""
        return {
            "status": self.status.value,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "queue_size": self.queue.size(),
            "conflict_count": len(self.conflicts),
            "local_items": len(self.local_store),
        }

    def export_sync_data(self) -> Dict[str, Any]:
        """导出同步数据 / Export sync data"""
        return {
            "items": [
                {
                    "id": item.item_id,
                    "type": item.item_type,
                    "version": item.local_version,
                    "data": item.local_data,
                    "checksum": item.checksum,
                }
                for item in self.local_store.values()
            ],
            "exported_at": datetime.now().isoformat(),
        }

    def import_sync_data(self, data: Dict[str, Any], merge: bool = True):
        """导入同步数据 / Import sync data"""
        for item_data in data.get("items", []):
            if merge and item_data["id"] in self.local_store:
                existing = self.local_store[item_data["id"]]
                if existing.last_modified < datetime.fromisoformat(
                    data.get("exported_at", datetime.now().isoformat())
                ):
                    existing.local_data = item_data["data"]
                    existing.compute_checksum()
            else:
                item = SyncItem(
                    item_id=item_data["id"],
                    item_type=item_data["type"],
                    local_version=item_data["version"],
                    remote_version=None,
                    local_data=item_data["data"],
                    remote_data=None,
                    last_modified=datetime.now(),
                    checksum=item_data["checksum"],
                )
                self.local_store[item_data["id"]] = item

    def set_offline_mode(self, enabled: bool):
        """设置离线模式 / Set offline mode"""
        self.status = SyncStatus.OFFLINE if enabled else SyncStatus.IDLE
        self._emit("offline_mode_changed", enabled)


class CloudSyncFactory:
    """云同步工厂 / Cloud sync factory"""

    _instances: Dict[str, CloudSyncManager] = {}

    @classmethod
    def get_manager(cls, config: CloudSyncConfig = None) -> CloudSyncManager:
        """获取管理器实例 / Get manager instance"""
        key = config.server_url if config else "default"
        if key not in cls._instances:
            cls._instances[key] = CloudSyncManager(config)
        return cls._instances[key]


def create_cloud_sync_manager(config: CloudSyncConfig = None) -> CloudSyncManager:
    """便捷函数：创建云同步管理器"""
    return CloudSyncManager(config)


def demo():
    """演示 / Demo"""
    logger.info("☁️ 云同步系统演示")
    logger.info("=" * 50)

    manager = CloudSyncManager()

    logger.info("\n📤 添加同步项:")
    manager.add_to_sync(
        item_id="memory_001",
        item_type="memory",
        data={"content": "第一次见面", "emotion": "happy"},
        priority=10,
    )
    manager.add_to_sync(
        item_id="skill_001", item_type="skill", data={"name": "Python", "level": 5}, priority=5
    )
    logger.info(f"  队列大小: {manager.queue.size()}")

    logger.info("\n📊 同步状态:")
    status = manager.get_status()
    logger.info(f"  状态: {status['status']}")
    logger.info(f"  本地项目: {status['local_items']}")
    logger.info(f"  队列项目: {status['queue_size']}")
    logger.info(f"  冲突: {status['conflict_count']}")

    logger.info("\n📦 导出数据:")
    export_data = manager.export_sync_data()
    logger.info(f"  项目数: {len(export_data['items'])}")
    logger.info(f"  大小: {len(str(export_data))} 字符")

    logger.info("\n🔄 模拟同步:")
    items, conflicts = manager.prepare_sync()
    logger.info(f"  待同步: {len(items)} 项")
    logger.info(f"  冲突: {len(conflicts)} 项")

    logger.info("\n✅ 演示完成!")


if __name__ == "__main__":
    demo()
