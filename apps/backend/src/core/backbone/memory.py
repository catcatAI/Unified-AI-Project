# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================
#
# 職責: 中層「記憶登錄器」（§11.3 #2 / 步驟 B7）
# 維度: δ 記憶維度（長期/情境記憶）
# 安全: 使用 Key A (後端控制)
# 成熟度: L2+ 等級開始接觸記憶統一概念
#
# =============================================================================

"""中層「記憶登錄器」（§11.3 #2 / 步驟 B7）。

`HAMMemoryManager` 目前有 4+ 實例（router / chat_service / drive / DLI），
記憶各自分片。統一經中層 `MemoryRegistry` 註冊單例：

```python
backbone.register_memory("ham", HAMMemoryManager)   # 惰性建立單例
ham = backbone.memory("ham")                         # 回傳同一個實例
```

支援三種註冊形式（彈性對應既有元件）：
- **類別**（callable 無參可建立）→ 惰性建立單例。
- **實例**（已是物件）→ 直接收錄。
- **factory**（`name` 開頭為 `factory:`）→ 每次呼叫 factory。

對既有元件保持向後相容：`backbone.memory("ham")` 的預設建構與
`HAMMemoryManager()` 相同（共用同一 data/memory/ham_memory.json），
因此多處呼叫不再產生分片實例。
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("angela_backbone_memory")


class MemoryRegistry:
    """記憶登錄器（§11.3 #2）。

    Args:
        lazy: 首次存取時惰性建立記憶後端（預設 True）。
    """

    def __init__(self, lazy: bool = True) -> None:
        self.lazy = lazy
        self._entries: Dict[str, Callable[[], Any]] = {}
        self._instances: Dict[str, Any] = {}
        self._factories: set = set()

    # ------------------------------------------------------------------
    # 註冊
    # ------------------------------------------------------------------
    def register(self, name: str, backend: Any) -> bool:
        """註冊記憶後端。

        - callable（類別/工廠）→ 惰性建立單例。
        - 已實例化物件 → 直接收錄。
        """
        name = self._normalize(name)
        if callable(backend) and not isinstance(backend, type) and name.startswith("factory:"):
            key = name
            self._entries[key] = backend
            return True
        if isinstance(backend, type):
            self._entries[name] = backend
            return True
        if callable(backend):
            self._entries[name] = backend
            return True
        # 已實例化物件
        self._instances[name] = backend
        return True

    def register_factory(self, name: str, factory: Callable[[], Any]) -> bool:
        """註冊每次呼叫建立新實例的 factory。"""
        self._entries[name] = factory
        self._factories.add(name)
        return True

    def unregister(self, name: str) -> bool:
        name = self._normalize(name)
        removed = False
        if name in self._entries:
            del self._entries[name]
            removed = True
        if name in self._factories:
            self._factories.discard(name)
            removed = True
        if name in self._instances:
            del self._instances[name]
            removed = True
        return removed

    # ------------------------------------------------------------------
    # 存取
    # ------------------------------------------------------------------
    def get(self, name: str) -> Any:
        """取得記憶後端（惰性建立單例；factory 每次新建）。"""
        name = self._normalize(name)
        if name in self._factories:
            return self._entries[name]()
        if name in self._instances:
            return self._instances[name]
        if name in self._entries:
            backend = self._entries[name]
            try:
                instance = backend() if not isinstance(backend, type) else backend()
            except TypeError:
                # 有些類別需要參數 → 嘗試無參；仍失敗則記錄並回傳 None
                logger.warning("memory %s instantiation failed, returning None", name)
                return None
            self._instances[name] = instance
            return instance
        # 預設：註冊 HAMMemoryManager（與既有 HAMMemoryManager() 同構）
        if name == "ham":
            return self.register_default("ham")
        logger.warning("memory %s not registered", name)
        return None

    def register_default(self, name: str) -> Any:
        """註冊並回傳預設 HAM 記憶後端（§11.3 #2）。"""
        if name == "ham":
            from ai.memory.ham_memory.ham_manager import HAMMemoryManager

            instance = HAMMemoryManager()
            self._instances["ham"] = instance
            return instance
        return None

    def names(self) -> list:
        return sorted(set(self._entries.keys()) | set(self._instances.keys()))

    def has(self, name: str) -> bool:
        return self._normalize(name) in self.names()

    def clear(self) -> None:
        self._entries.clear()
        self._instances.clear()
        self._factories.clear()

    @staticmethod
    def _normalize(name: str) -> str:
        return name.strip().lower()
