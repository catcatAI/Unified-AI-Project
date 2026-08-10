# =============================================================================
# ANGELA-MATRIX: L1-L6[全層] αβγδεθζη [A] L2+
# =============================================================================
#
# 職責: 上層訓練工作流的掛載/釋放（§5.5.3 步驟 C3）— TrainingMount
# 維度: η 執行維度（資源效率、活躍工作流數）+ ζ 連通維度
# 安全: Key A (後端控制)
#
# =============================================================================

"""訓練工作流掛載（§5.5.3 / 步驟 C3）。

把 ED3NTrainer / FullTrainingPipeline 等訓練工作流以 `TrainingMount` 包裝成
`Mountable`：掛載時 lazy 建立（呼叫 factory）、釋放時呼叫物件的 save 後釋放
記憶體，符合 §4 掛載狀態機（DISK ──mount()──▶ MEMORY ──unmount()──▶ DISK）。

用途：
    from core.backbone.training import TrainingMount

    mount = TrainingMount(
        name="ed3n",
        factory=lambda: ED3NTrainer(engine),
        save_func=lambda obj, path: obj.save(path),
        load_func=lambda obj, path: obj.load(path),
        persistence_path="data/ed3n_trainer.pt",
    )
    backbone.register_mountable("training:ed3n", mount)
    backbone.mount("training:ed3n")
    trainer = backbone.access("training:ed3n")   # 已建例
    backbone.unmount("training:ed3n")            # save + 釋放
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class TrainingMount:
    """把「訓練工作流」包裝成可掛載/釋放的 Mountable。

    - `mount()`：若未掛載，呼叫 factory() 建例並標記 mounted。
    - `unmount()`：若已掛載，呼叫 save_func(instance, path)（若提供）後釋放
      記憶體（instance=None）。
    - `access()`：統一入口（未掛載則 lazy mount），回傳工作流實例。
    - `is_mounted()` / `persistence_path()`：Mountable 協議其餘部分。

    Attributes:
        name: 工作流名稱。
        factory: () -> instance 的建立函式。
        save_func: (instance, path) -> bool 的儲存函式（可省略）。
        load_func: (instance, path) -> bool 的載入函式（可省略）。
        persistence_path: 權重存檔路徑。
        idle_timeout: 閒置逾時（秒），sweep 自動釋放。
    """

    def __init__(
        self,
        name: str,
        factory: Callable[[], Any],
        save_func: Optional[Callable[[Any, str], Any]] = None,
        load_func: Optional[Callable[[Any, str], Any]] = None,
        persistence_path: str = "",
        idle_timeout: float = 600.0,
    ) -> None:
        self.name = name
        self.factory = factory
        self.save_func = save_func
        self.load_func = load_func
        self.persistence_path = persistence_path
        self.idle_timeout = idle_timeout

        self._instance: Any = None
        self._mounted = False
        self.last_access = 0.0
        self.access_count = 0

    # ------------------------------------------------------------------
    # Mountable 協議
    # ------------------------------------------------------------------
    def mount(self) -> bool:
        if self._mounted and self._instance is not None:
            self.last_access = time.time()
            return True
        try:
            self._instance = self.factory()
        except Exception as exc:
            logger.warning("TrainingMount %s factory failed: %s", self.name, exc, exc_info=True)
            self._instance = None
            self._mounted = False
            return False
        self._mounted = True
        self.last_access = time.time()
        # 若提供 load_func 且存檔存在，嘗試載入既有權重（不失敗則僅建例）
        if self.load_func is not None and self.persistence_path:
            try:
                self.load_func(self._instance, self.persistence_path)
            except Exception:
                logger.debug("TrainingMount %s no persisted weights to load", self.name)
        return True

    def unmount(self) -> bool:
        if not self._mounted or self._instance is None:
            return True
        try:
            if self.save_func is not None and self.persistence_path:
                self.save_func(self._instance, self.persistence_path)
        except Exception as exc:
            logger.warning("TrainingMount %s save failed: %s", self.name, exc, exc_info=True)
        self._instance = None
        self._mounted = False
        self.last_access = time.time()
        return True

    def is_mounted(self) -> bool:
        return self._mounted and self._instance is not None

    def persistence_path(self) -> str:
        return self.persistence_path

    # ------------------------------------------------------------------
    # 存取 + lazy mount
    # ------------------------------------------------------------------
    def access(self) -> Any:
        if not self.is_mounted():
            if not self.mount():
                return None
        self.access_count += 1
        self.last_access = time.time()
        return self._instance

    def touch(self) -> None:
        self.last_access = time.time()

    def idle_seconds(self) -> float:
        return max(0.0, time.time() - self.last_access) if self.last_access else 0.0

    def is_idle(self, now: Optional[float] = None) -> bool:
        if not self.is_mounted():
            return False
        return self.idle_seconds() >= self.idle_timeout

    def sweep_if_idle(self) -> bool:
        if self.is_idle():
            return self.unmount()
        return False

    # ------------------------------------------------------------------
    # 診斷
    # ------------------------------------------------------------------
    def info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "mounted": self.is_mounted(),
            "access_count": self.access_count,
            "idle_seconds": round(self.idle_seconds(), 2),
            "persistence_path": self.persistence_path,
        }


__all__ = ["TrainingMount"]
