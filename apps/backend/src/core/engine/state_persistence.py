"""
State Persistence Layer — Redis/JSON Hybrid Storage
====================================================

提供雙模式持久化：
- Redis: 快速快照（最新狀態 + 最近 N 筆歷史）
- JSON File: 長期歸檔（完整狀態 + 審計軌跡）

設計原則：
- 惰性連接：Redis 不可用時自動降級到內存模式
- 異步操作：所有 I/O 都是 async，不阻塞主流程
- 快照策略：每 N 次 update 或每 M 秒自動 checkpoint

使用方式:
    from core.engine.state_persistence import StatePersistence

    persistence = StatePersistence()
    await persistence.save_checkpoint(state_adapter)  # 存
    await persistence.load_checkpoint(state_adapter)   # 取

Author: Angela AI v6.2.1
"""

from __future__ import annotations
import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, TYPE_CHECKING

logger = logging.getLogger("angela_persistence")

# Redis 可用性檢查
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


if TYPE_CHECKING:
    from core.engine.state_matrix_adapter import StateMatrixAdapter


class PersistenceConfig:
    """持久化配置"""

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        redis_enabled: bool = True,
        json_storage_path: str = "data/checkpoints",
        auto_save_interval: int = 300,
        max_snapshots: int = 100,
        checkpoint_every_n_updates: int = 50,
        compression_enabled: bool = True,
    ):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.redis_password = redis_password
        self.redis_enabled = redis_enabled
        self.json_storage_path = json_storage_path
        self.auto_save_interval = auto_save_interval
        self.max_snapshots = max_snapshots
        self.checkpoint_every_n_updates = checkpoint_every_n_updates
        self.compression_enabled = compression_enabled


class StatePersistence:
    """
    狀態持久化層

    雙模式：
    - Redis: 快速讀寫，適合即時快照
    - JSON File: 長期歸檔，適合完整狀態

    快照策略：
    - 時間觸發：每 auto_save_interval 秒
    - 更新觸發：每 checkpoint_every_n_updates 次 update
    - 混合：同時使用兩種策略
    """

    KEY_PREFIX = "angela:state:"
    SNAPSHOT_LIST_KEY = f"{KEY_PREFIX}snapshots"
    CURRENT_STATE_KEY = f"{KEY_PREFIX}current"

    def __init__(self, config: Optional[PersistenceConfig] = None):
        self.config = config or PersistenceConfig()
        self._redis_client: Optional[Any] = None
        self._redis_available: bool = False
        self._last_save_time: float = 0.0
        self._update_count_since_save: int = 0
        self._checkpoint_id: Optional[str] = None

    async def initialize(self) -> None:
        """初始化 Redis 連接（惰性）"""
        if not self.config.redis_enabled or not REDIS_AVAILABLE:
            logger.info("[Persistence] Redis disabled or not available, using JSON mode")
            self._redis_available = False
            return

        try:
            self._redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            await self._redis_client.ping()
            self._redis_available = True
            logger.info(f"[Persistence] Redis connected: {self.config.redis_host}:{self.config.redis_port}")
        except Exception as e:
            logger.warning(f"[Persistence] Redis connection failed: {e}. Using JSON mode.")
            self._redis_available = False
            self._redis_client = None

    def _get_json_path(self) -> Path:
        """獲取 JSON 存儲路徑"""
        storage_path = Path(self.config.json_storage_path)
        storage_path.mkdir(parents=True, exist_ok=True)
        return storage_path

    def _serialize(self, data: Dict[str, Any]) -> str:
        """序列化數據"""
        return json.dumps(data, ensure_ascii=False, default=str)

    def _deserialize(self, raw: str) -> Dict[str, Any]:
        """反序列化數據"""
        return json.loads(raw)

    async def save_checkpoint(
        self,
        state_adapter: "StateMatrixAdapter",
        label: Optional[str] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        保存狀態快照

        優先使用 Redis，否則用 JSON 文件。

        Args:
            state_adapter: StateMatrixAdapter 實例
            label: 快照標籤（如 "manual", "auto", "critical_fix"）
            force: 是否強制保存（忽略時間/更新閾值）

        Returns:
            保存結果摘要
        """
        state_data = state_adapter.save_state()
        timestamp = datetime.now().isoformat()
        checkpoint_id = self._checkpoint_id or str(uuid.uuid4())[:8]
        tag = label or "auto"

        snapshot = {
            "id": checkpoint_id,
            "tag": tag,
            "timestamp": timestamp,
            "update_count": state_adapter._sm.update_count,
            "data": state_data,
        }

        if self._redis_available and self._redis_client:
            result = await self._save_to_redis(snapshot)
        else:
            result = await self._save_to_json(snapshot)

        self._last_save_time = time.time()
        self._update_count_since_save = 0
        self._checkpoint_id = None

        return result

    async def _save_to_redis(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """保存到 Redis"""
        try:
            r = self._redis_client

            snapshot_key = f"{self.KEY_PREFIX}snapshot:{snapshot['id']}"
            await r.set(snapshot_key, self._serialize(snapshot), ex=86400 * 7)

            await r.lpush(self.SNAPSHOT_LIST_KEY, snapshot["id"])
            await r.ltrim(self.SNAPSHOT_LIST_KEY, 0, self.config.max_snapshots - 1)

            await r.hset(self.CURRENT_STATE_KEY, mapping={
                "id": snapshot["id"],
                "tag": snapshot["tag"],
                "timestamp": snapshot["timestamp"],
                "update_count": snapshot["update_count"],
            })

            logger.info(f"[Persistence] Saved to Redis: {snapshot['id']} ({snapshot['tag']})")

            return {
                "status": "saved",
                "mode": "redis",
                "id": snapshot["id"],
                "tag": snapshot["tag"],
                "timestamp": snapshot["timestamp"],
            }
        except Exception as e:
            logger.error(f"[Persistence] Redis save failed: {e}")
            return await self._save_to_json_fallback(snapshot)

    async def _save_to_json(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """保存到 JSON 文件"""
        try:
            storage_path = self._get_json_path()

            checkpoint_file = storage_path / f"checkpoint_{snapshot['id']}.json"
            checkpoint_file.write_text(self._serialize(snapshot), encoding="utf-8")

            index_file = storage_path / "checkpoint_index.json"
            index = self._load_json_index(index_file)

            index["checkpoints"].insert(0, {
                "id": snapshot["id"],
                "tag": snapshot["tag"],
                "timestamp": snapshot["timestamp"],
                "file": checkpoint_file.name,
                "update_count": snapshot["update_count"],
            })
            if len(index["checkpoints"]) > self.config.max_snapshots:
                old = index["checkpoints"][self.config.max_snapshots:]
                for old_entry in old:
                    old_file = storage_path / old_entry.get("file", "")
                    if old_file.exists():
                        old_file.unlink()
                index["checkpoints"] = index["checkpoints"][:self.config.max_snapshots]

            index["last_checkpoint"] = index["checkpoints"][0] if index["checkpoints"] else None
            index_file.write_text(self._serialize(index), encoding="utf-8")

            logger.info(f"[Persistence] Saved to JSON: {snapshot['id']} ({snapshot['tag']})")

            return {
                "status": "saved",
                "mode": "json",
                "id": snapshot["id"],
                "tag": snapshot["tag"],
                "timestamp": snapshot["timestamp"],
                "path": str(checkpoint_file),
            }
        except Exception as e:
            logger.error(f"[Persistence] JSON save failed: {e}")
            return {"status": "error", "reason": str(e)}

    async def _save_to_json_fallback(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Redis 失敗時的 JSON 回退"""
        return await self._save_to_json(snapshot)

    def _load_json_index(self, index_file: Path) -> Dict[str, Any]:
        """加載 JSON 索引"""
        if index_file.exists():
            try:
                return json.loads(index_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"checkpoints": [], "last_checkpoint": None}

    async def load_checkpoint(
        self,
        state_adapter: "StateMatrixAdapter",
        checkpoint_id: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        加載狀態快照

        Args:
            state_adapter: StateMatrixAdapter 實例
            checkpoint_id: 指定快照 ID（優先）
            tag: 指定標籤（如 "latest", "auto", "critical_fix"）

        Returns:
            加載結果摘要
        """
        if checkpoint_id:
            if self._redis_available and self._redis_client:
                snapshot = await self._load_from_redis(checkpoint_id)
            else:
                snapshot = await self._load_from_json(checkpoint_id)
        elif tag:
            snapshot = await self._find_by_tag(tag)
        else:
            if self._redis_available and self._redis_client:
                snapshot = await self._load_latest_from_redis()
            else:
                snapshot = await self._load_latest_from_json()

        if not snapshot:
            return {"status": "not_found", "reason": "No checkpoint found"}

        try:
            state_adapter.load_state(snapshot["data"])
            self._checkpoint_id = snapshot.get("id")
            logger.info(f"[Persistence] Loaded checkpoint: {snapshot.get('id')} ({snapshot.get('tag')})")
            return {
                "status": "loaded",
                "id": snapshot.get("id"),
                "tag": snapshot.get("tag"),
                "timestamp": snapshot.get("timestamp"),
                "update_count": snapshot.get("update_count"),
            }
        except Exception as e:
            logger.error(f"[Persistence] Load failed: {e}")
            return {"status": "error", "reason": str(e)}

    async def _load_from_redis(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """從 Redis 加载快照"""
        try:
            raw = await self._redis_client.get(f"{self.KEY_PREFIX}snapshot:{checkpoint_id}")
            if raw:
                return self._deserialize(raw)
        except Exception as e:
            logger.error(f"[Persistence] Redis load failed: {e}")
        return None

    async def _load_from_json(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """從 JSON 文件加载快照"""
        try:
            storage_path = self._get_json_path()
            checkpoint_file = storage_path / f"checkpoint_{checkpoint_id}.json"
            if checkpoint_file.exists():
                return json.loads(checkpoint_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"[Persistence] JSON load failed: {e}")
        return None

    async def _load_latest_from_redis(self) -> Optional[Dict[str, Any]]:
        """從 Redis 加载最新快照"""
        try:
            ids = await self._redis_client.lrange(self.SNAPSHOT_LIST_KEY, 0, 0)
            if ids:
                return await self._load_from_redis(ids[0])
        except Exception as e:
            logger.error(f"[Persistence] Redis latest load failed: {e}")
        return None

    async def _load_latest_from_json(self) -> Optional[Dict[str, Any]]:
        """從 JSON 文件加载最新快照"""
        try:
            index_file = self._get_json_path() / "checkpoint_index.json"
            index = self._load_json_index(index_file)
            last = index.get("last_checkpoint")
            if last:
                return await self._load_from_json(last["id"])
        except Exception as e:
            logger.error(f"[Persistence] JSON latest load failed: {e}")
        return None

    async def _find_by_tag(self, tag: str) -> Optional[Dict[str, Any]]:
        """根據標籤查找快照"""
        if self._redis_available and self._redis_client:
            ids = await self._redis_client.lrange(self.SNAPSHOT_LIST_KEY, 0, -1)
            for cid in ids:
                snap = await self._load_from_redis(cid)
                if snap and snap.get("tag") == tag:
                    return snap
        else:
            index_file = self._get_json_path() / "checkpoint_index.json"
            index = self._load_json_index(index_file)
            for entry in index.get("checkpoints", []):
                if entry.get("tag") == tag:
                    return await self._load_from_json(entry["id"])
        return None

    async def list_checkpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """列舉最近的快照"""
        checkpoints = []

        if self._redis_available and self._redis_client:
            try:
                ids = await self._redis_client.lrange(self.SNAPSHOT_LIST_KEY, 0, limit - 1)
                for cid in ids:
                    snap = await self._load_from_redis(cid)
                    if snap:
                        checkpoints.append({
                            "id": snap["id"],
                            "tag": snap["tag"],
                            "timestamp": snap["timestamp"],
                            "update_count": snap["update_count"],
                        })
            except Exception:
                pass

        if not checkpoints:
            try:
                index_file = self._get_json_path() / "checkpoint_index.json"
                index = self._load_json_index(index_file)
                for entry in index.get("checkpoints", [])[:limit]:
                    checkpoints.append({
                        "id": entry["id"],
                        "tag": entry["tag"],
                        "timestamp": entry["timestamp"],
                        "update_count": entry.get("update_count", 0),
                    })
            except Exception:
                pass

        return checkpoints

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """刪除指定快照"""
        if self._redis_available and self._redis_client:
            try:
                await self._redis_client.delete(f"{self.KEY_PREFIX}snapshot:{checkpoint_id}")
                ids = await self._redis_client.lrange(self.SNAPSHOT_LIST_KEY, 0, -1)
                if checkpoint_id in ids:
                    new_ids = [i for i in ids if i != checkpoint_id]
                    await self._redis_client.delete(self.SNAPSHOT_LIST_KEY)
                    if new_ids:
                        await self._redis_client.rpush(self.SNAPSHOT_LIST_KEY, *new_ids)
                logger.info(f"[Persistence] Deleted from Redis: {checkpoint_id}")
                return True
            except Exception as e:
                logger.error(f"[Persistence] Redis delete failed: {e}")

        try:
            storage_path = self._get_json_path()
            checkpoint_file = storage_path / f"checkpoint_{checkpoint_id}.json"
            if checkpoint_file.exists():
                checkpoint_file.unlink()

            index_file = storage_path / "checkpoint_index.json"
            index = self._load_json_index(index_file)
            index["checkpoints"] = [c for c in index["checkpoints"] if c["id"] != checkpoint_id]
            index_file.write_text(self._serialize(index), encoding="utf-8")
            logger.info(f"[Persistence] Deleted from JSON: {checkpoint_id}")
            return True
        except Exception as e:
            logger.error(f"[Persistence] JSON delete failed: {e}")
        return False

    def should_auto_save(self, update_count: int) -> bool:
        """判斷是否應該自動保存"""
        if self.config.auto_save_interval <= 0 and self.config.checkpoint_every_n_updates <= 0:
            return False

        time_since = time.time() - self._last_save_time
        if self.config.auto_save_interval > 0 and time_since >= self.config.auto_save_interval:
            return True

        if self.config.checkpoint_every_n_updates > 0:
            if update_count - self._update_count_since_save >= self.config.checkpoint_every_n_updates:
                return True

        return False

    async def auto_checkpoint(
        self,
        state_adapter: "StateMatrixAdapter",
        update_count: int,
    ) -> Optional[Dict[str, Any]]:
        """自動 checkpoint（如果滿足條件）"""
        if self.should_auto_save(update_count):
            return await self.save_checkpoint(state_adapter, label="auto")
        return None

    def set_checkpoint_id(self, checkpoint_id: str) -> None:
        """設置即將保存的 checkpoint ID（用於標記特定操作）"""
        self._checkpoint_id = checkpoint_id

    def get_stats(self) -> Dict[str, Any]:
        """獲取持久化層狀態統計"""
        return {
            "redis_available": self._redis_available,
            "redis_host": self.config.redis_host if self._redis_available else None,
            "json_storage_path": str(self._get_json_path()),
            "auto_save_interval": self.config.auto_save_interval,
            "checkpoint_every_n_updates": self.config.checkpoint_every_n_updates,
            "max_snapshots": self.config.max_snapshots,
            "last_save_time": self._last_save_time,
            "update_count_since_save": self._update_count_since_save,
        }