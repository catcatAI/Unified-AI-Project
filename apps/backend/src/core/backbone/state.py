# =============================================================================
# ANGELA-MATRIX: L1-L6[全层] αβγδεθζη [A] L2+
# =============================================================================
#
# 職責: 統一狀態讀寫（代理 GlobalStateStore + StateMatrix4D）
#       （§6 state.py）
# 維度: αβγδεθζη 所有維度狀態讀寫
# 安全: 使用 Key A (後端控制)
# 成熟度: L2+ 等級開始接觸統一狀態存取概念
#
# =============================================================================

"""統一狀態讀寫（§6 state.py）。

主幹線對「全域狀態」提供單一入口，代理兩大來源：
- `GlobalStateStore`（CNS domain 式狀態，`global_store.state_store`）
- `StateMatrix4D`（8D 狀態矩陣，經 registry.matrices.primary() 取得）

設計：
- `BackboneState` 提供 `get/update/domain/subscribe/emit` 等統一介面。
- 寫入一律經 `update_state`（不直接改 `.values[]`，§8 繞過 API 修正），
  讀取則優先去狀態矩陣查軸值，再退回 domain 狀態。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

from typing import Any, Callable, Dict, List, Optional

try:  # 延遲導入，避免啟動時硬依賴
    from core.system.state_store import state_store as _default_state_store
except Exception:  # pragma: no cover - 環境無 GlobalStateStore 時的降級
    _default_state_store = None


class BackboneState:
    """統一狀態讀寫門面。

    Args:
        state_store: GlobalStateStore 實例（預設取全域單例）。
        matrix_registry: 用於讀取主狀態矩陣的 MatrixRegistry。
        axis_registry: 用於讀寫座標軸的 AxisRegistry。
    """

    def __init__(
        self,
        state_store: Any = None,
        matrix_registry: Any = None,
        axis_registry: Any = None,
    ) -> None:
        self._store = state_store if state_store is not None else _default_state_store
        self._matrix_registry = matrix_registry
        self._axis_registry = axis_registry

    # ------------------------------------------------------------------
    # Domain 狀態（GlobalStateStore）
    # ------------------------------------------------------------------
    def get(self, domain: str, key: Optional[str] = None, default: Any = None) -> Any:
        """讀取 domain 狀態（可選單一 key）。"""
        if self._store is None:
            return default
        try:
            data = self._store.get_state(domain) or {}
        except Exception as e:
            logger.debug(f"state get {domain} failed: {e}", exc_info=True)
            return default
        if key is None:
            return data
        return data.get(key, default)

    def update(self, domain: str, data: Dict[str, Any], notify: bool = True) -> bool:
        """寫入 domain 狀態（選擇性更新，不覆蓋未提及鍵）。"""
        if self._store is None:
            return False
        try:
            self._store.update_state(domain, data, notify=notify)
            return True
        except Exception:
            return False

    def set(self, domain: str, key: str, value: Any, notify: bool = True) -> bool:
        """寫入單一鍵。"""
        return self.update(domain, {key: value}, notify=notify)

    def domain_keys(self) -> List[str]:
        if self._store is None:
            return []
        try:
            data = self._store.get_state(None) or {}
            return list(data.keys())
        except Exception:
            return []

    def subscribe(self, domain: str, callback: Callable) -> bool:
        """訂閱 domain 變更。"""
        if self._store is None:
            return False
        try:
            self._store.subscribe(domain, callback)
            return True
        except Exception:
            return False

    def unsubscribe(self, domain: str, callback: Callable = None) -> bool:
        """取消訂閱 domain 變更。

        依賴下層 GlobalStateStore 的 unsubscribe 支援；不支援則回傳 False。
        """
        if self._store is None or not hasattr(self._store, "unsubscribe"):
            return False
        try:
            return bool(self._store.unsubscribe(domain, callback))
        except Exception:
            return False

    def emit_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """發送 CNS 事件。"""
        if self._store is None:
            return False
        try:
            self._store.emit_event(event_type, data)
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # 狀態矩陣讀寫（StateMatrix4D / 座標軸）
    # ------------------------------------------------------------------
    def matrix(self) -> Any:
        if self._matrix_registry is None:
            return None
        return self._matrix_registry.primary()

    def read_axis(self, axis: str, key: Optional[str] = None, default: Any = None) -> Any:
        """優先從座標軸註冊表讀取；無則退回狀態矩陣。"""
        if self._axis_registry is not None and self._axis_registry.has(axis):
            return self._axis_registry.read(axis, key, default)
        m = self.matrix()
        if m is None:
            return default
        try:
            if key is not None:
                return getattr(m, axis).get(key, default) if hasattr(m, axis) else default
            return getattr(m, axis)
        except Exception:
            return default

    def write_axis(self, axis: str, key: str, value: Any) -> bool:
        """統一寫入軸值（§8：不直接改 `.values[]`）。

        優先走 AxisRegistry.write（統一 API）；若無註冊軸則嘗試狀態矩陣的
        `update_*` 方法。
        """
        if self._axis_registry is not None and self._axis_registry.has(axis):
            return self._axis_registry.write(axis, key, value)
        m = self.matrix()
        if m is None:
            return False
        update_method = getattr(m, f"update_{axis}", None)
        if callable(update_method):
            try:
                update_method(**{key: value})
                return True
            except Exception:
                return False
        return False

    def update_axes(self, axis: str, data: Dict[str, Any]) -> bool:
        """一次寫入多個軸值。"""
        if self._axis_registry is not None and self._axis_registry.has(axis):
            return self._axis_registry.update(axis, data)
        m = self.matrix()
        if m is None:
            return False
        update_method = getattr(m, f"update_{axis}", None)
        if callable(update_method):
            try:
                update_method(**data)
                return True
            except Exception:
                return False
        return False
