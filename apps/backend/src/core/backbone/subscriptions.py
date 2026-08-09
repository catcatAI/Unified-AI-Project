# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================
#
# 職責: 中層「CNS domain 訂閱同步器」（§11.3 #4 / 步驟 B10）
# 維度: ζ 連通維度（CNS 事件匯流排 ↔ 狀態矩陣）
# 安全: 使用 Key A (後端控制)
# 成熟度: L2+ 等級開始接觸 CNS 訂閱概念
#
# =============================================================================

"""中層「CNS domain 訂閱同步器」（§11.3 #4 / 步驟 B10）。

問題：CNS **domain 無訂閱者**（StateMatrix4D 同步後無人讀），事件匯流排半空轉；
composer / router 直接呼叫全域 `state_store.update_state`，缺乏統一訂閱點。

統一經中層 `CNSDomainSync`：

```python
backbone.state.subscribe("core", on_core_change)      # 直接訂閱（既有 API）
sync = backbone.state_sync(subscribe=True)             # 統一同步器
```

`CNSDomainSync` 做三件事：
1. **訂閱** CNS domain 變更（`core` / `neuro_vocabulary` / …）。
2. **寫回矩陣**：域值含軸字典（如 `{"alpha": {...}}`）時，call
   backbone `state.write_axis`，使 StateMatrix4D 真正反映 CNS。
3. **統一入口**：backbone 聚合的一層，各元件不再直接碰全域 state_store。
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("angela_backbone_subscriptions")

CORE_DOMAIN = "core"


class CNSDomainSync:
    """CNS domain 訂閱同步器（§11.3 #4）。

    Args:
        state: `BackboneState` 實例（統一狀態讀寫門面）。
        matrix: 主狀態矩陣（StateMatrix4D，可選，由 `bind_matrix` 注入）。
    """

    #: 訂閱後嘗試同步成軸寫入的 domain（值會含軸字典）
    AXIS_DOMAINS = (CORE_DOMAIN, "state_matrix", "matrix")

    def __init__(self, state: Any = None, matrix: Any = None) -> None:
        self.state = state
        self._matrix = matrix
        self._subscribed: set = set()
        self._callbacks: Dict[str, Callable] = {}
        self._default_callback = self._on_domain_change

    # ------------------------------------------------------------------
    # 綁定
    # ------------------------------------------------------------------
    def bind_matrix(self, matrix: Any) -> None:
        """綁定主狀態矩陣。"""
        self._matrix = matrix

    def bind_state(self, state: Any) -> None:
        """綁定 BackboneState 門面。"""
        self.state = state

    # ------------------------------------------------------------------
    # 訂閱
    # ------------------------------------------------------------------
    def subscribe(self, domain: str = CORE_DOMAIN) -> bool:
        """訂閱 CNS domain 變更（透過 backbone.state 統一點）。"""
        if self.state is None:
            return False
        if domain in self._subscribed:
            return True
        callback = self._callbacks.pop(domain, None) or self._default_callback
        try:
            if self.state.subscribe(domain, callback):
                self._subscribed.add(domain)
                return True
        except Exception as exc:
            logger.warning("CNS domain subscribe failed for %s: %s", domain, exc)
        return False

    def subscribe_with(self, domain: str, callback: Callable) -> bool:
        """以自訂 callback 訂閱 domain。"""
        self._callbacks[domain] = callback
        return self.subscribe(domain)

    def unsubscribe(self, domain: str) -> bool:
        if domain not in self._subscribed:
            return False
        if self.state is None:
            return False
        try:
            if self.state.unsubscribe is not None:
                did = self.state.unsubscribe(
                    domain, self._callbacks.get(domain) or self._default_callback
                )
            else:  # pragma: no cover - 無 unsubscribe API 時僅清本地狀態
                did = False
        except Exception as exc:
            logger.debug("CNS domain unsubscribe failed: %s", exc)
            did = False
        if did:
            self._subscribed.discard(domain)
        return did

    def subscribed_domains(self) -> list:
        return sorted(self._subscribed)

    # ------------------------------------------------------------------
    # 同步
    # ------------------------------------------------------------------
    def _on_domain_change(self, domain: str, data: Dict[str, Any]) -> None:
        """CNS 域變更 callback：若值含軸字典則同步到主狀態矩陣。"""
        if not isinstance(data, dict) or not data:
            return
        for axis, value in data.items():
            if isinstance(value, dict):
                self._sync_axis_to_matrix(domain, axis, value)

    def _sync_axis_to_matrix(self, domain: str, axis: str, values: Dict[str, Any]) -> None:
        """把軸字典寫入主狀態矩陣（經 state.write_axis 統一入口）。"""
        if self.state is None or self._matrix is None:
            return
        try:
            for key, value in values.items():
                if isinstance(value, (int, float, bool, str)) or value is None:
                    self.state.write_axis(axis, key, value)
        except Exception as exc:
            logger.debug("CNS axis sync to matrix failed: %s", exc)

    # ------------------------------------------------------------------
    # 便捷：emit 事件（統一經 backbone.state）
    # ------------------------------------------------------------------
    def emit_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        if self.state is None:
            return False
        return bool(self.state.emit_event(event_type, data))
