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
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class AxisPortRegistry:
    """Registry managing axis ports for data routing."""

    def __init__(self):
        self._ports: Dict[str, Dict[str, Any]] = {}
        logger.debug("[AxisPortRegistry] Initialized")

    def register_port(self, axis_name: str, port_config: Dict[str, Any]) -> None:
        """Register a port for an axis."""
        self._ports[axis_name] = {
            "axis": axis_name,
            "config": port_config,
            "direction": port_config.get("direction", "IO"),
            "tags": port_config.get("tags", []),
            "priority": port_config.get("priority", 0.5),
        }
        logger.info(f"[AxisPortRegistry] Registered port for axis '{axis_name}'")

    def get_port(self, axis_name: str) -> Optional[Dict[str, Any]]:
        """Get port config for an axis."""
        return self._ports.get(axis_name)

    def list_ports(self) -> List[Dict[str, Any]]:
        """List all registered ports."""
        return list(self._ports.values())

    def get_outputs_for_axis(self, axis_name: str) -> List[Dict[str, Any]]:
        port = self._ports.get(axis_name)
        if port and port.get("direction") in ("OUT", "IO"):
            return [port]
        return []

    def get_inputs_for_axis(self, axis_name: str) -> List[Dict[str, Any]]:
        port = self._ports.get(axis_name)
        if port and port.get("direction") in ("IN", "IO"):
            return [port]
        return []

    def route_to_port(self, axis_name: str, data: Any) -> Dict[str, Any]:
        """Route data to a port. Returns status dict."""
        port = self._ports.get(axis_name)
        if port is None:
            return {
                "status": "error",
                "axis": axis_name,
                "error": f"Port for axis '{axis_name}' not registered",
            }
        return {
            "status": "routed",
            "axis": axis_name,
            "port": port,
            "data_size": len(str(data)) if data else 0,
        }


PortRegistry = AxisPortRegistry
