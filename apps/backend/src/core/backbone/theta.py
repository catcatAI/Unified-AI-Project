# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================
#
# 職責: 中層「θ 元認知路由橋接」（§11.3 #3 / 步驟 B9）
# 維度: η θ 元認知維度（novelty/complexity/creation_urge）
# 安全: 使用 Key A (後端控制)
# 成熟度: L2+ 等級開始接觸元認知路由概念
#
# =============================================================================

"""中層「θ 元認知路由橋接」（§11.3 #3 / 步驟 B9）。

原本 `prompt_builder._get_theta_router()` 以 `ThetaRouter()` 無參建構，
`_state_adapter` / `_port_registry` 皆為 None → `theta_values` 永遠空 dict
→ `get_routing_report()` 的 creation_urge / theta_negativity 恆為 0 → θ 永不進 prompt。

統一經中層 `ThetaBridge` 注入 state_adapter + port_registry：

```python
bridge = backbone.theta()                # 惰性建立、注入主幹線矩陣 + PortRegistry
report = bridge.get_routing_report()     # θ 值來自主幹線 StateMatrix4D
```

- `state_adapter`：主幹線註冊的 StateMatrix4D（具 `.theta.values`）。
- `port_registry`：`AxisPortRegistry`（無參建構，θ 端口路由）。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("angela_backbone_theta")


class _MatrixAdapter:
    """把 StateMatrix4D 包成 ThetaRouter 期望的 state_adapter（具 `_sm`）。"""

    def __init__(self, matrix: Any) -> None:
        self._sm = matrix


class ThetaBridge:
    """θ 元認知路由橋接（§11.3 #3）。

    Args:
        primary_matrix: 主幹線 StateMatrix4D（可省略，之後用 `bind_matrix` 注入）。
        matrix_provider: callable 回傳當前主矩陣（動態反映主幹線註冊狀態）。
        port_registry: `PortRegistry`（可省略，省略時惰性建立）。
    """

    def __init__(
        self,
        primary_matrix: Any = None,
        port_registry: Any = None,
        matrix_provider: Any = None,
    ) -> None:
        self._matrix = primary_matrix
        self._matrix_provider = matrix_provider
        self._port_registry = port_registry
        self._router = None

    # ------------------------------------------------------------------
    # 注入
    # ------------------------------------------------------------------
    def bind_matrix(self, matrix: Any) -> None:
        """綁定主幹線 StateMatrix4D（供 θ 值讀取）。"""
        self._matrix = matrix
        self._router = None  # 需要重建

    def bind_port_registry(self, port_registry: Any) -> None:
        """綁定 PortRegistry。"""
        self._port_registry = port_registry
        self._router = None

    def _current_matrix(self) -> Any:
        """動態解析當前主矩陣（matrix_provider 優先）。"""
        if self._matrix_provider is not None:
            try:
                return self._matrix_provider()
            except Exception as exc:
                logger.debug("matrix_provider failed: %s", exc)
        return self._matrix

    def router(self) -> Any:
        """取得 ThetaRouter 實例（惰性建立，注入 state_adapter + port_registry）。"""
        if self._router is None:
            from core.engine.theta_router import ThetaRouter

            if self._port_registry is None:
                try:
                    from core.engine.axis_port_registry import PortRegistry

                    self._port_registry = PortRegistry()
                except Exception as exc:
                    logger.debug("PortRegistry unavailable: %s", exc)
            matrix = self._current_matrix()
            adapter = _MatrixAdapter(matrix) if matrix is not None else None
            self._router = ThetaRouter(state_adapter=adapter, port_registry=self._port_registry)
        return self._router

    # ------------------------------------------------------------------
    # 查詢
    # ------------------------------------------------------------------
    def theta_values(self) -> Dict[str, float]:
        """θ 軸當前值（自主幹線 StateMatrix4D）。"""
        try:
            return self.router().theta_values
        except Exception as exc:
            logger.debug("theta values unavailable: %s", exc)
            return {}

    def get_routing_report(self) -> Dict[str, Any]:
        """θ 路由狀態報告（供 prompt 注入）。"""
        try:
            return self.router().get_routing_report()
        except Exception as exc:
            logger.warning("theta routing report unavailable: %s", exc)
            return {
                "theta_values": {},
                "total_decisions": 0,
                "recent_decisions": [],
                "creation_urge": 0,
                "theta_negativity": 0,
            }

    def resolve_route(self, port_name: str) -> Any:
        """為單個端口解析路由決策（委派 ThetaRouter）。"""
        return self.router().resolve_route(port_name)

    def auto_allocate(self) -> list:
        return self.router().auto_allocate()
