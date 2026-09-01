# =============================================================================
# ANGELA-MATRIX: L1-L6[全层] αβγδεθζη [A] L2+
# =============================================================================
#
# 職責: 掛載/釋放機制（§4.2/§4.3）— idle timeout 自動釋放 + lazy mount
# 維度: η 執行維度（資源效率、活躍模組數）
# 安全: 使用 Key A (後端控制)
# 成熟度: L2+ 等級開始接觸資源掛載概念
#
# =============================================================================

"""掛載/釋放機制（§4.2 / §4.3）。

不常使用的模態不常駐記憶體，使用時才從磁碟載入（`mount`），用完可釋放
（`unmount`）。支援 **idle timeout 自動釋放** 與 **lazy mount**（存取時若未
掛載 → 自動載入）。

狀態機（§4.3）：

    DISK ──mount()──▶ MEMORY ──unmount()/idle──▶ DISK
     ▲                   │
     └──── re-mount() ───┘  (flush + free)

介面：
- `MountableWrapper`：包裝任何實作 `Mountable` 協定的物件，追蹤 idle 時間。
- `MountManager`：管理多個可掛載資源，提供 `mount/unmount/mounted` 統一入口。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import threading
import time
from typing import Any, Dict, Optional



def _is_mountable_instance(obj: Any) -> bool:
    """物件是否已實作 Mountable 協定（有 mount/unmount/is_mounted/persistence_path 方法）。"""
    return all(hasattr(obj, m) for m in ("mount", "unmount", "is_mounted", "persistence_path"))


class MountableWrapper:
    """包裝單一 `Mountable` 資源，加上 idle 追蹤。

    Attributes:
        resource: 實作 `Mountable` 協定的底層物件。
        idle_timeout: 閒置逾時（秒）。超過後自動釋放。
        last_access: 最後存取時間（unix timestamp）。
    """

    def __init__(self, resource: Any, idle_timeout: float = 300.0) -> None:
        # 支援 lazy factory：resource 為 callable（不具 mount/unmount 方法）時，
        # 視為資源的創建工廠，mount() 才實例化（符合 §4.4 惰性載入原則）。
        if callable(resource) and not _is_mountable_instance(resource):
            self._factory = resource
            self.resource: Any = None
        else:
            self._factory = None
            self.resource = resource
        self.idle_timeout = idle_timeout
        self._lock = threading.RLock()
        self._mounted = False
        self.last_access = 0.0
        self.access_count = 0

    # ------------------------------------------------------------------
    # Mountable 協定代理
    # ------------------------------------------------------------------
    def mount(self) -> bool:
        with self._lock:
            if self._mounted:
                self.last_access = time.time()
                return True
            if self.resource is None and self._factory is not None:
                try:
                    self.resource = self._factory()
                except Exception:
                    self.resource = None
                    return False
            if self.resource is None:
                return False
            mount = getattr(self.resource, "mount", None)
            if mount is not None:
                ok = bool(mount())
            else:
                ok = True
            if ok:
                self._mounted = True
            self.last_access = time.time()
            return ok

    def unmount(self) -> bool:
        with self._lock:
            if not self._mounted:
                return True
            unmount = getattr(self.resource, "unmount", None)
            if unmount is not None:
                ok = bool(unmount())
            else:
                ok = True
            if ok:
                self._mounted = False
            self.last_access = time.time()
            return ok

    def is_mounted(self) -> bool:
        with self._lock:
            return self._mounted

    def persistence_path(self) -> str:
        path = getattr(self.resource, "persistence_path", None)
        if path is not None:
            try:
                return str(path())
            except Exception as e:
                logger.debug(f"persistence_path failed: {e}", exc_info=True)
        return getattr(self.resource, "persistence_path", "")

    # ------------------------------------------------------------------
    # 存取 + lazy mount
    # ------------------------------------------------------------------
    def _ensure_mounted(self) -> bool:
        """存取前確保已掛載（lazy mount）。"""
        if not self._mounted:
            return self.mount()
        return True

    def access(self, *args: Any, **kwargs: Any) -> Any:
        """透過包裝器存取底層資源（自動 lazy mount + 更新 idle）。"""
        if not self._ensure_mounted():
            return None
        self.access_count += 1
        self.last_access = time.time()
        return self.resource

    def touch(self) -> None:
        self.last_access = time.time()

    def idle_seconds(self) -> float:
        now = time.time()
        return max(0.0, now - self.last_access) if self.last_access else 0.0

    def is_idle(self, now: Optional[float] = None) -> bool:
        """是否已閒置超過 idle_timeout（且已掛載）。"""
        if not self._mounted:
            return False
        idle = self.idle_seconds()
        return idle >= self.idle_timeout

    def sweep_if_idle(self) -> bool:
        """若閒置逾時則自動釋放。回傳是否釋放。"""
        if self.is_idle():
            return self.unmount()
        return False


class MountManager:
    """管理多個可掛載資源（§4.2 統一入口）。

    使用方式：
        manager = MountManager()
        manager.register("vision", mountable_resource)
        manager.mount("vision")          # 顯式掛載
        manager.access("vision")          # 統一入口（lazy mount）
        manager.unmount("vision")         # 顯式釋放
        manager.mounted()                 # -> {"vision": True, ...}
        manager.sweep()                   # 掃描閒置資源並自動釋放
    """

    def __init__(self) -> None:
        self._resources: Dict[str, MountableWrapper] = {}
        self._lock = threading.RLock()

    def register(self, key: str, resource: Any, idle_timeout: float = 300.0) -> MountableWrapper:
        wrapper = MountableWrapper(resource, idle_timeout=idle_timeout)
        with self._lock:
            self._resources[key] = wrapper
        return wrapper

    def unregister(self, key: str) -> bool:
        with self._lock:
            return self._resources.pop(key, None) is not None

    def has(self, key: str) -> bool:
        return key in self._resources

    def get(self, key: str, default: Any = None) -> Any:
        wrapper = self._resources.get(key)
        return wrapper if wrapper else default

    def mount(self, key: str) -> bool:
        wrapper = self._resources.get(key)
        return bool(wrapper and wrapper.mount())

    def unmount(self, key: str) -> bool:
        wrapper = self._resources.get(key)
        return bool(wrapper and wrapper.unmount())

    def access(self, key: str, *args: Any, **kwargs: Any) -> Any:
        """統一入口：回傳已掛載的底層資源（未掛載則 lazy mount）。"""
        wrapper = self._resources.get(key)
        if wrapper is None:
            return None
        return wrapper.access(*args, **kwargs)

    def mounted(self) -> Dict[str, bool]:
        return {key: wrapper.is_mounted() for key, wrapper in self._resources.items()}

    def is_mounted(self, key: str) -> bool:
        wrapper = self._resources.get(key)
        return bool(wrapper and wrapper.is_mounted())

    def sweep(self) -> int:
        """掃描並自動釋放所有閒置逾時資源。回傳釋放數。"""
        released = 0
        with self._lock:
            for wrapper in list(self._resources.values()):
                if wrapper.sweep_if_idle():
                    released += 1
        return released

    def persistence_path(self, key: str) -> str:
        wrapper = self._resources.get(key)
        return wrapper.persistence_path() if wrapper else ""

    def clear(self) -> None:
        with self._lock:
            self._resources.clear()
