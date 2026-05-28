"""
Axis Port Registry — 6D 軸端口路由系統 Phase 1
===============================================

讓 θ 元認知軸作為「路由大腦」，端口只需聲明存在。

核心概念：
- Port: 數據進出的抽象端點（IN/OUT/IO）
- PortRegistry: 端口註冊表，管理所有端口與軸的綁定
- θ 軸根據語義相似度自動路由

使用方式:
    from core.engine.axis_port_registry import PortRegistry, PortDirection, Port

    registry = PortRegistry(state_matrix_adapter)
    registry.register(name="llm_out", direction=PortDirection.IN,
                      semantic_vector=[...], tags=["llm"])

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from core.engine.state_matrix_adapter import StateMatrixAdapter

logger = logging.getLogger("angela_port_registry")


class PortDirection(Enum):
    """端口方向"""
    IN = "in"      # 外部 → 軸
    OUT = "out"    # 軸 → 外部
    IO = "io"      # 雙向


@dataclass
class Port:
    """
    端口 — 數據進出的抽象端點

    Attributes:
        name: 唯一標識（不可重複）
        direction: 方向（IN/OUT/IO）
        semantic_vector: 32-dim 語義向量，用於 θ 軸路由匹配
        axis: 當前綁定的軸名（None 表示未綁定）
        priority: 路由優先級（0-1）
        tags: 分類標籤
        metadata: 額外元數據
    """
    name: str
    direction: PortDirection
    semantic_vector: List[float]
    axis: Optional[str] = None
    priority: float = 0.5
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def compute_similarity(self, target_vector: List[float]) -> float:
        """計算與目標向量的餘弦相似度"""
        if len(self.semantic_vector) != len(target_vector):
            return 0.0
        dot = sum(a * b for a, b in zip(self.semantic_vector, target_vector))
        norm_self = (sum(v * v for v in self.semantic_vector)) ** 0.5
        norm_target = (sum(v * v for v in target_vector)) ** 0.5
        if norm_self == 0 or norm_target == 0:
            return 0.0
        return dot / (norm_self * norm_target)

    def is_bound(self) -> bool:
        """是否已綁定軸"""
        return self.axis is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "direction": self.direction.value,
            "axis": self.axis,
            "priority": self.priority,
            "tags": self.tags,
            "bound": self.is_bound(),
        }


class PortRegistry:
    """
    端口註冊表 — 管理所有端口與軸的綁定

    核心功能：
    - 註冊/註銷端口
    - 端口→軸 綁定（手動/自動）
    - 軸→端口 查詢（用於輸出）
    - 語義相似度匹配

    自動路由：由 θ 軸驅動，見 ThetaRouter
    """

    def __init__(self, state_adapter: Optional["StateMatrixAdapter"] = None):
        self._state_adapter = state_adapter
        self._ports: Dict[str, Port] = {}
        self._axis_to_ports: Dict[str, List[str]] = {}  # axis_name → [port_name, ...]
        self._unbound_ports: List[str] = []  # 未綁定的端口名

    def register(
        self,
        name: str,
        direction: PortDirection,
        semantic_vector: List[float],
        priority: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_bind: bool = True,
    ) -> Port:
        """
        註冊端口

        Args:
            name: 唯一標識
            direction: 方向
            semantic_vector: 32-dim 語義向量
            priority: 優先級
            tags: 分類標籤
            metadata: 額外數據
            auto_bind: 是否自動綁定到軸

        Returns:
            創建的 Port
        """
        if name in self._ports:
            logger.warning(f"[PortRegistry] Port '{name}' already exists, updating", exc_info=True)
            port = self._ports[name]
            port.direction = direction
            port.semantic_vector = semantic_vector
            port.priority = priority
            port.tags = tags or []
            port.metadata = metadata or {}
        else:
            port = Port(
                name=name,
                direction=direction,
                semantic_vector=semantic_vector,
                priority=priority,
                tags=tags or [],
                metadata=metadata or {},
            )
            self._ports[name] = port
            self._unbound_ports.append(name)
            logger.info(f"[PortRegistry] Registered port '{name}' direction={direction.value}")

        if auto_bind:
            self._auto_bind_port(port)

        return port

    def unregister(self, name: str) -> bool:
        """註銷端口"""
        if name not in self._ports:
            return False

        port = self._ports[name]
        if port.axis and port.axis in self._axis_to_ports:
            self._axis_to_ports[port.axis] = [
                p for p in self._axis_to_ports[port.axis] if p != name
            ]
            if not self._axis_to_ports[port.axis]:
                del self._axis_to_ports[port.axis]

        del self._ports[name]
        self._unbound_ports = [p for p in self._unbound_ports if p != name]
        logger.info(f"[PortRegistry] Unregistered port '{name}'")
        return True

    def get_port(self, name: str) -> Optional[Port]:
        """獲取端口"""
        return self._ports.get(name)

    def list_ports(
        self,
        direction: Optional[PortDirection] = None,
        bound: Optional[bool] = None,
        axis: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[Port]:
        """列舉端口（支持過濾）"""
        result = list(self._ports.values())

        if direction is not None:
            result = [p for p in result if p.direction == direction]

        if bound is not None:
            result = [p for p in result if p.is_bound() == bound]

        if axis is not None:
            result = [p for p in result if p.axis == axis]

        if tag is not None:
            result = [p for p in result if tag in p.tags]

        return result

    def bind_port_to_axis(self, port_name: str, axis_name: str) -> bool:
        """
        手動綁定端口到軸（覆蓋自動路由）

        Args:
            port_name: 端口名
            axis_name: 軸名

        Returns:
            是否成功
        """
        port = self._ports.get(port_name)
        if not port:
            logger.warning(f"[PortRegistry] Port '{port_name}' not found", exc_info=True)
            return False

        old_axis = port.axis
        if old_axis and old_axis in self._axis_to_ports:
            self._axis_to_ports[old_axis] = [
                p for p in self._axis_to_ports[old_axis] if p != port_name
            ]
            if not self._axis_to_ports[old_axis]:
                del self._axis_to_ports[old_axis]

        port.axis = axis_name
        if axis_name not in self._axis_to_ports:
            self._axis_to_ports[axis_name] = []
        if port_name not in self._axis_to_ports[axis_name]:
            self._axis_to_ports[axis_name].append(port_name)

        if port_name in self._unbound_ports:
            self._unbound_ports.remove(port_name)

        logger.info(f"[PortRegistry] Bound '{port_name}' → '{axis_name}' (was: {old_axis})")
        return True

    def unbind_port(self, port_name: str) -> bool:
        """解除端口的軸綁定"""
        port = self._ports.get(port_name)
        if not port:
            return False

        if port.axis and port.axis in self._axis_to_ports:
            self._axis_to_ports[port.axis] = [
                p for p in self._axis_to_ports[port.axis] if p != port_name
            ]
            if not self._axis_to_ports[port.axis]:
                del self._axis_to_ports[port.axis]

        port.axis = None
        if port_name not in self._unbound_ports:
            self._unbound_ports.append(port_name)

        logger.info(f"[PortRegistry] Unbound port '{port_name}'")
        return True

    def get_outputs_for_axis(self, axis_name: str) -> List[Port]:
        """獲取軸的所有輸出端口（direction=OUT 或 IO）"""
        port_names = self._axis_to_ports.get(axis_name, [])
        return [
            self._ports[p]
            for p in port_names
            if p in self._ports
            and self._ports[p].direction in (PortDirection.OUT, PortDirection.IO)
        ]

    def get_inputs_for_axis(self, axis_name: str) -> List[Port]:
        """獲取軸的所有輸入端口（direction=IN 或 IO）"""
        port_names = self._axis_to_ports.get(axis_name, [])
        return [
            self._ports[p]
            for p in port_names
            if p in self._ports
            and self._ports[p].direction in (PortDirection.IN, PortDirection.IO)
        ]

    def find_best_axis_for_port(self, port: Port) -> Optional[str]:
        """
        根據語義相似度找到最匹配的軸

        遍歷所有軸的 semantic_anchors，計算相似度，返回最佳匹配

        Returns:
            最匹配的軸名，None 如果無匹配
        """
        if not self._state_adapter:
            return None

        sm = self._state_adapter._sm
        best_axis = None
        best_sim = 0.0

        for axis_name, anchor in sm.semantic_anchors.items():
            sim = anchor.compute_resonance(port.semantic_vector)
            if sim > best_sim:
                best_sim = sim
                best_axis = axis_name

        return best_axis

    def _auto_bind_port(self, port: Port) -> None:
        """自動綁定端口到最匹配的軸"""
        best_axis = self.find_best_axis_for_port(port)
        if best_axis:
            self.bind_port_to_axis(port.name, best_axis)
        else:
            logger.debug(f"[PortRegistry] No matching axis for port '{port.name}'")

    def auto_bind_idle_ports(self) -> int:
        """
        自動綁定所有未綁定的端口

        Returns:
            綁定的端口數量
        """
        count = 0
        for port_name in list(self._unbound_ports):
            port = self._ports.get(port_name)
            if port:
                self._auto_bind_port(port)
                if port.is_bound():
                    count += 1
        return count

    def size(self) -> int:
        """端口總數"""
        return len(self._ports)

    def bound_count(self) -> int:
        """已綁定端口數"""
        return sum(1 for p in self._ports.values() if p.is_bound())

    def unbound_count(self) -> int:
        """未綁定端口數"""
        return len(self._unbound_ports)

    def get_report(self) -> Dict[str, Any]:
        """獲取註冊表狀態報告"""
        return {
            "total_ports": self.size(),
            "bound_ports": self.bound_count(),
            "unbound_ports": self.unbound_count(),
            "axes_with_ports": list(self._axis_to_ports.keys()),
            "ports": [p.to_dict() for p in self._ports.values()],
        }