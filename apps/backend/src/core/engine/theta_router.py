"""
Theta Router — θ 元認知路由引擎
================================

讓 θ 軸作為「路由大腦」，自動決定：
- 端口 → 軸 綁定（auto_allocate）
- 軸 → 端口 路由（cascade_output / merge_input）

核心概念：
- ThetaRouter: θ 軸驅動的路由決策器
- RouteDecision: 路由決策結果
- 與 PortRegistry 配合使用

使用方式:
    from core.engine.theta_router import ThetaRouter

    router = ThetaRouter(state_adapter, port_registry)
    decision = router.resolve_route("llm_output")
    router.auto_allocate()

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Protocol

from core.system.config.magic_numbers import cache_value

if TYPE_CHECKING:
    from core.engine.axis_port_registry import PortRegistry
    from core.engine.state_matrix_adapter import StateMatrixAdapter


class _ThetaStateMatrixProtocol(Protocol):
    """Protocol for StateMatrixAdapter interface needed by ThetaRouter."""

    @property
    def theta(self) -> Any: ...

    @property
    def semantic_anchors(self) -> Dict[str, Any]: ...

    @property
    def dimensions(self) -> Dict[str, Any]: ...

    def create_axis(
        self, name: str, label: str, semantic_vector: List[float], initial_values: Dict[str, float]
    ) -> None: ...


logger = logging.getLogger("angela_theta_router")


class RouteAction(Enum):
    """路由動作"""

    BIND = "bind"  # 綁定端口到軸
    CREATE_AXIS = "create_axis"  # 創建新軸
    REBIND = "rebind"  # 重新綁定
    UNBIND = "unbind"  # 解綁定
    CASCADE = "cascade"  # 廣播輸出
    MERGE = "merge"  # 合併輸入
    SKIP = "skip"  # 跳過


@dataclass
class RouteDecision:
    """
    路由決策結果

    Attributes:
        action: 路由動作
        port_name: 涉及的端口
        target_axis: 目標軸（action=BIND/REBIND）
        proposed_name: 提議的軸名（action=CREATE_AXIS）
        confidence: 置信度
        reasoning: 決策理由
    """

    action: RouteAction
    port_name: Optional[str] = None
    target_axis: Optional[str] = None
    proposed_name: Optional[str] = None
    confidence: float = 0.0
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert RouteDecision to a dictionary representation."""
        return {
            "action": self.action.value,
            "port_name": self.port_name,
            "target_axis": self.target_axis,
            "proposed_name": self.proposed_name,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


@dataclass
class AxisBinding:
    """
    軸綁定結果

    Attributes:
        axis_name: 軸名
        port_names: 綁定的端口列表
        direction: 方向
        confidence: 置信度
    """

    axis_name: str
    port_names: List[str] = field(default_factory=list)
    direction: str = "io"
    confidence: float = 0.0


class ThetaRouter:
    """
    θ 元認知路由引擎

    根據 θ 軸的狀態（novelty, complexity, creation_urge）和
    所有端口的語義向量，自動決定：
    1. 端口 → 軸 路由（resolve_route / auto_allocate）
    2. 軸 → 端口 輸出（cascade_output）
    3. 端口 → 軸 輸入（merge_input）

    路由觸發時機：
    - PortRegistry.register() 時自動調用
    - StateMatrixAdapter.update_theta() 時重新評估
    - StateMatrixAdapter.create_axis() 時更新路由表
    """

    DEFAULT_THRESHOLD = 0.5  # 相似度閾值
    CREATE_THRESHOLD = 0.3  # 創建新軸的閾值
    CASCADE_WEIGHT = 0.6  # 廣播閾值

    def __init__(
        self,
        state_adapter: Optional[_ThetaStateMatrixProtocol] = None,
        port_registry: Optional["PortRegistry"] = None,
    ):
        self._state_adapter: Optional[_ThetaStateMatrixProtocol] = state_adapter
        self._port_registry = port_registry
        self._routing_history: List[Dict[str, Any]] = []
        self._max_history = cache_value("routing_history", 100)

    @property
    def theta_values(self) -> Dict[str, float]:
        """獲取 θ 軸當前值"""
        if not self._state_adapter:
            return {}

        # Try new API (StateMatrixAdapter) first: has theta property
        theta_proxy = getattr(self._state_adapter, "theta", None)
        if theta_proxy and hasattr(theta_proxy, "values"):
            vals = getattr(theta_proxy, "values", {})
            if isinstance(vals, dict):
                return vals

        # Fallback to legacy _MatrixAdapter: has _sm attribute with theta
        sm = getattr(self._state_adapter, "_sm", None)
        if sm and hasattr(sm, "theta"):
            theta_proxy = getattr(sm, "theta", None)
            if theta_proxy and hasattr(theta_proxy, "values"):
                vals = getattr(theta_proxy, "values", {})
                if isinstance(vals, dict):
                    return vals

        return {}

    def resolve_route(self, port_name: str) -> RouteDecision:
        """
        為單個端口解析路由決策

        流程：
        1. 獲取端口的語義向量
        2. 計算與所有軸的相似度
        3. θ 軸更新（novelty = 1 - max_sim）
        4. 根據閾值決定動作

        Args:
            port_name: 端口名

        Returns:
            RouteDecision
        """
        port = self._port_registry.get_port(port_name) if self._port_registry else None
        if not port:
            return RouteDecision(
                action=RouteAction.SKIP,
                port_name=port_name,
                reasoning="Port not found",
            )

        # Guard: StateMatrixAdapter may not implement the full protocol
        if not self._state_adapter:
            return RouteDecision(
                action=RouteAction.SKIP,
                port_name=port_name,
                reasoning="StateMatrixAdapter not available",
            )

        # Extract semantic_anchors from state adapter (new API or legacy _sm)
        semantic_anchors = getattr(self._state_adapter, "semantic_anchors", {})
        if not semantic_anchors:
            # Fallback to legacy _MatrixAdapter._sm
            sm = getattr(self._state_adapter, "_sm", None)
            if sm:
                semantic_anchors = getattr(sm, "semantic_anchors", {})
        if not semantic_anchors:
            return RouteDecision(
                action=RouteAction.SKIP,
                port_name=port_name,
                reasoning="No semantic anchors available",
            )

        # Port is a dict from PortRegistry.get_port()
        port_vector = port.get("semantic_vector", []) if isinstance(port, dict) else []
        if not port_vector:
            return RouteDecision(
                action=RouteAction.SKIP,
                port_name=port_name,
                reasoning="Port has no semantic vector",
            )

        axis_similarities: Dict[str, float] = {}
        for axis_name, anchor in semantic_anchors.items():
            if hasattr(anchor, "compute_resonance"):
                sim = anchor.compute_resonance(port_vector)
                axis_similarities[axis_name] = sim

        max_sim = max(axis_similarities.values()) if axis_similarities else 0.0
        best_axis = (
            max(axis_similarities, key=lambda k: axis_similarities[k])
            if axis_similarities
            else None
        )

        novelty = 1.0 - max_sim
        active_dims = sum(1 for v in axis_similarities.values() if v > self.DEFAULT_THRESHOLD)

        # Update theta values via state adapter's theta proxy (new API or legacy)
        theta_proxy = getattr(self._state_adapter, "theta", None)
        if not theta_proxy:
            # Fallback to legacy _MatrixAdapter._sm.theta
            sm = getattr(self._state_adapter, "_sm", None)
            if sm:
                theta_proxy = getattr(sm, "theta", None)

        if theta_proxy and hasattr(theta_proxy, "update"):
            dimensions = getattr(self._state_adapter, "dimensions", {})
            if not dimensions:
                sm = getattr(self._state_adapter, "_sm", None)
                if sm:
                    dimensions = getattr(sm, "dimensions", {})
            theta_proxy.update(
                novelty=novelty,
                complexity=active_dims / max(1, len(dimensions)),
            )

        if max_sim >= self.DEFAULT_THRESHOLD and best_axis:
            return RouteDecision(
                action=RouteAction.BIND,
                port_name=port_name,
                target_axis=best_axis,
                confidence=max_sim,
                reasoning=f"相似度 {max_sim:.3f} >= 閾值 {self.DEFAULT_THRESHOLD}，綁定到 {best_axis}",
            )

        if max_sim < self.CREATE_THRESHOLD and self.theta_values.get("creation_urge", 0) > 0.6:
            dimensions = getattr(self._state_adapter, "dimensions", {})
            if not dimensions:
                sm = getattr(self._state_adapter, "_sm", None)
                if sm:
                    dimensions = getattr(sm, "dimensions", {})
            proposed = f"axis_{port_name}_{len(dimensions) + 1}"
            return RouteDecision(
                action=RouteAction.CREATE_AXIS,
                port_name=port_name,
                proposed_name=proposed,
                confidence=1.0 - max_sim,
                reasoning=f"相似度過低({max_sim:.3f})，creation_urge={self.theta_values.get('creation_urge', 0):.2f}，建議創建新軸",
            )

        return RouteDecision(
            action=RouteAction.BIND,
            port_name=port_name,
            target_axis=best_axis,
            confidence=max_sim,
            reasoning=f"中等相似度 {max_sim:.3f}，綁定到現有軸 {best_axis}",
        )

    def _binding_api_ready(self) -> bool:
        """綁定系 registry API 是否就緒（R20 生存守衛）。

        auto_allocate / apply_routing_decisions 依賴的
        bind_port_to_axis / unbind_port / list_ports(bound=) 尚未實作；
        未就緒時呼叫方顯式短路（log + 空回傳），不拋 AttributeError。
        綁定模型一旦定案，實作 registry 側後刪此守衛。
        """
        import inspect

        reg = self._port_registry
        if reg is None:
            return False
        if not all(hasattr(reg, n) for n in ("bind_port_to_axis", "unbind_port")):
            return False
        try:
            params = inspect.signature(reg.list_ports).parameters
        except (TypeError, ValueError):
            return False
        return "bound" in params

    @staticmethod
    def _port_name(port: Any) -> Optional[str]:
        """端口名安全提取：registry 回 dict（.get），物件才用屬性。"""
        if isinstance(port, dict):
            name = port.get("name")
            return str(name) if name is not None else None
        return getattr(port, "name", None)

    @staticmethod
    def _port_axis(port: Any) -> Optional[str]:
        if isinstance(port, dict):
            axis = port.get("axis")
            return str(axis) if axis is not None else None
        return getattr(port, "axis", None)

    def auto_allocate(self) -> List[AxisBinding]:
        """
        自動為所有未綁定的端口分配軸

        遍歷未綁定端口，調用 resolve_route()，
        根據決策執行綁定或創建軸。

        Returns:
            新增的軸綁定列表
        """
        if not self._port_registry or not self._state_adapter:
            return []
        if not self._binding_api_ready():
            logger.warning("[ThetaRouter] auto_allocate no-op: port-binding API 未實作")
            return []

        # The code below is unreachable at runtime since _binding_api_ready() returns False
        # but we keep it for future implementation. Using proper dict access for mypy.
        unbound_ports = self._port_registry.list_ports()
        bindings: List[AxisBinding] = []

        for port in unbound_ports:
            port_name = self._port_name(port)
            if not port_name:
                continue
            decision = self.resolve_route(port_name)

            if decision.action == RouteAction.BIND and decision.target_axis:
                # self._port_registry.bind_port_to_axis(port_name, decision.target_axis)
                binding = AxisBinding(
                    axis_name=decision.target_axis,
                    port_names=[port_name],
                    direction=self._port_axis(port) or "io",
                    confidence=decision.confidence,
                )
                bindings.append(binding)
                self._record_routing(port_name, decision)

            elif decision.action == RouteAction.CREATE_AXIS and decision.proposed_name:
                # sm.create_axis(...) - not implemented in StateMatrixAdapter
                # self._port_registry.bind_port_to_axis(port_name, decision.proposed_name)
                binding = AxisBinding(
                    axis_name=decision.proposed_name,
                    port_names=[port_name],
                    direction=self._port_axis(port) or "io",
                    confidence=decision.confidence,
                )
                bindings.append(binding)
                self._record_routing(port_name, decision)

        if bindings:
            logger.info(f"[ThetaRouter] Auto-allocated {len(bindings)} port-axis bindings")

        return bindings

    def cascade_output(self, axis_name: str, data: Any) -> Dict[str, Any]:
        """
        將軸的數據廣播到所有綁定的輸出端口

        θ 軸根據路由策略決定：
        - 哪些端口接收數據（priority 閾值）
        - 數據如何轉換（metadata）

        Args:
            axis_name: 軸名
            data: 要輸出的數據

        Returns:
            廣播結果摘要
        """
        if not self._port_registry:
            return {"status": "skip", "reason": "no port registry"}

        outputs = self._port_registry.get_outputs_for_axis(axis_name)
        if not outputs:
            return {"status": "no_outputs", "axis": axis_name}

        results = {}
        threshold = self.CASCADE_WEIGHT

        for port in outputs:
            priority = port.get("priority", 0.0) if isinstance(port, dict) else 0.0
            port_name = port.get("name", "unknown") if isinstance(port, dict) else "unknown"
            if priority >= threshold:
                results[port_name] = {
                    "status": "dispatched",
                    "priority": priority,
                    "data": data,
                }
            else:
                results[port_name] = {
                    "status": "skipped",
                    "priority": priority,
                }

        logger.info(
            f"[ThetaRouter] Cascaded {axis_name} → {len(results)} ports ({sum(1 for r in results.values() if r['status'] == 'dispatched')} dispatched)"
        )

        return {
            "status": "completed",
            "axis": axis_name,
            "total_ports": len(outputs),
            "dispatched": sum(1 for r in results.values() if r["status"] == "dispatched"),
            "skipped": sum(1 for r in results.values() if r["status"] == "skipped"),
            "results": results,
        }

    def merge_input(self, axis_name: str, port_data_list: List[Tuple[str, Any]]) -> Any:
        """
        將多個輸入端口的數據合併到軸

        合併策略（由 θ 軸決定）：
        - priority 加權平均
        - 最新數據優先
        - 全部拼接

        Args:
            axis_name: 目標軸名
            port_data_list: [(port_name, data), ...]

        Returns:
            合併後的數據
        """
        if not self._port_registry:
            return None

        inputs = self._port_registry.get_inputs_for_axis(axis_name)
        if not inputs:
            return None

        port_map: Dict[str, Dict[str, Any]] = {}
        for p in inputs:
            if isinstance(p, dict):
                name = p.get("name")
                if name:
                    port_map[name] = p
        merged: Dict[str, Any] = {}
        total_weight = 0.0

        for port_name, data in port_data_list:
            port = port_map.get(port_name)
            if not port:
                continue

            weight = port.get("priority", 0.0)
            total_weight += weight

            if isinstance(data, dict):
                for key, value in data.items():
                    if key not in merged:
                        merged[key] = 0.0
                    merged[key] += value * weight
            else:
                if "raw" not in merged:
                    merged["raw"] = 0.0
                merged["raw"] += data * weight

        if total_weight > 0:
            for key in merged:
                merged[key] /= total_weight

        logger.info(f"[ThetaRouter] Merged {len(port_data_list)} inputs → '{axis_name}'")
        return merged

    def re_evaluate_routing(self) -> List[RouteDecision]:
        """
        重新評估所有端口的路由（當 θ 軸更新後調用）

        遍歷所有端口，重新計算相似度，
        對需要重新綁定的端口做出決策。

        Returns:
            重新路由決策列表
        """
        if not self._port_registry:
            return []

        decisions = []
        all_ports = self._port_registry.list_ports()

        for port in all_ports:
            pname = self._port_name(port)
            if pname is None:
                continue
            decision = self.resolve_route(pname)
            if decision.action in (RouteAction.BIND, RouteAction.REBIND):
                if decision.target_axis != self._port_axis(port):
                    decisions.append(decision)

        if decisions:
            logger.info(f"[ThetaRouter] Re-evaluated {len(decisions)} ports need re-routing")

        return decisions

    def apply_routing_decisions(self, decisions: List[RouteDecision]) -> int:
        """
        批量應用路由決策

        Args:
            decisions: 路由決策列表

        Returns:
            成功應用的數量
        """
        if not self._port_registry or not self._state_adapter:
            return 0
        if not self._binding_api_ready():
            logger.warning("[ThetaRouter] apply_routing_decisions no-op: port-binding API 未實作")
            return 0

        count = 0
        for decision in decisions:
            if decision.action == RouteAction.REBIND and decision.port_name:
                self._port_registry.bind_port_to_axis(decision.port_name, decision.target_axis)  # type: ignore[attr-defined]
                self._record_routing(decision.port_name, decision)
                count += 1
            elif decision.action == RouteAction.UNBIND and decision.port_name:
                self._port_registry.unbind_port(decision.port_name)  # type: ignore[attr-defined]
                self._record_routing(decision.port_name, decision)
                count += 1

        return count

    def _record_routing(self, port_name: str, decision: RouteDecision) -> None:
        """記錄路由歷史"""
        entry = {
            "port_name": port_name,
            "action": decision.action.value,
            "target_axis": decision.target_axis,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "theta_state": self.theta_values.copy(),
        }
        self._routing_history.append(entry)
        if len(self._routing_history) > self._max_history:
            self._routing_history = self._routing_history[-self._max_history :]

    def get_routing_report(self) -> Dict[str, Any]:
        """獲取路由狀態報告"""
        return {
            "theta_values": self.theta_values,
            "total_decisions": len(self._routing_history),
            "recent_decisions": self._routing_history[-10:],
            "creation_urge": self.theta_values.get("creation_urge", 0),
            "theta_negativity": self.theta_values.get("theta_negativity", 0),
        }
