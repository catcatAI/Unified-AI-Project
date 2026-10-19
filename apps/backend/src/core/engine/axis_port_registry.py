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

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AxisPortRegistry:
    """Registry managing axis ports for data routing.

    Two layers, both real:

    - the **port** layer: a port is an IO endpoint of an axis
      (``register_port(axis, config)``), keyed by the axis it belongs to;
    - the **binding** layer: a named port can be *bound* to an axis
      (``bind_port_to_axis(port, axis)`` / ``unbind_port(port)``), which is
      what the θ router drives when it decides where a port belongs.

    The binding API used to be missing, so ``ThetaRouter.auto_allocate`` and
    ``apply_routing_decisions`` were permanent no-ops behind a guard
    ("綁定系 API 尚未實作"). With the API in place the router can actually
    bind, unbind and enumerate.
    """

    def __init__(self):
        self._ports: Dict[str, Dict[str, Any]] = {}
        # port name -> bound axis name
        self._bindings: Dict[str, str] = {}
        logger.debug("[AxisPortRegistry] Initialized")

    def register_port(self, axis_name: str, port_config: Dict[str, Any]) -> None:
        """Register a port for an axis.

        The config is kept *flat* in the entry (next to the canonical
        ``name``/``axis`` keys) as well as under ``config``: the θ router
        reads ``port["semantic_vector"]`` directly, and a nested-only shape
        made every port look vector-less (and therefore unroutable).
        """
        entry = dict(port_config)
        entry.update(
            {
                "name": port_config.get("name", axis_name),
                "axis": axis_name,
                "config": port_config,
                "direction": port_config.get("direction", "IO"),
                "tags": port_config.get("tags", []),
                "priority": port_config.get("priority", 0.5),
            }
        )
        self._ports[axis_name] = entry
        logger.info(f"[AxisPortRegistry] Registered port for axis '{axis_name}'")

    def unregister_port(self, axis_name: str) -> bool:
        """Remove the port of an axis (and any binding to it).

        Returns True when a port was removed.
        """
        port = self._ports.pop(axis_name, None)
        if port is None:
            return False
        name = port.get("name")
        if name:
            self._bindings.pop(name, None)
        logger.info(f"[AxisPortRegistry] Unregistered port for axis '{axis_name}'")
        return True

    # ------------------------------------------------------------------
    # Binding layer (the API the θ router drives)
    # ------------------------------------------------------------------
    def bind_port_to_axis(self, port_name: str, axis_name: str) -> None:
        """Bind a named port to an axis.

        The port is created if it does not exist yet, so a binding is always
        representable — the router may decide on an axis the port was never
        registered for.
        """
        port_name = str(port_name)
        axis_name = str(axis_name)
        existing = None
        for port in self._ports.values():
            if port.get("name") == port_name:
                existing = port
                break
        if existing is None:
            self._ports[axis_name] = {
                "name": port_name,
                "axis": axis_name,
                "config": {},
                "direction": "IO",
                "tags": [],
                "priority": 0.5,
            }
        self._bindings[port_name] = axis_name
        logger.info(f"[AxisPortRegistry] Bound port '{port_name}' to axis '{axis_name}'")

    def unbind_port(self, port_name: str) -> bool:
        """Remove the binding of a port (the port itself stays)."""
        port_name = str(port_name)
        if self._bindings.pop(port_name, None) is None:
            return False
        logger.info(f"[AxisPortRegistry] Unbound port '{port_name}'")
        return True

    def get_binding(self, port_name: str) -> Optional[str]:
        """The axis a port is bound to (None when unbound)."""
        return self._bindings.get(str(port_name))

    def list_ports(self, bound: Optional[bool] = None) -> List[Dict[str, Any]]:
        """List the registered ports.

        ``bound`` filters: True → only the bound ports, False → only the
        unbound ones, None → all. Every entry carries its ``name`` and the
        axis it is bound to (``bound_axis``), so a caller does not have to
        know the registry's internals.
        """
        ports: List[Dict[str, Any]] = []
        for port in self._ports.values():
            name = port.get("name")
            bound_axis = self._bindings.get(name) if name else None
            if bound is True and not bound_axis:
                continue
            if bound is False and bound_axis:
                continue
            entry = dict(port)
            entry["bound_axis"] = bound_axis
            entry["bound"] = bool(bound_axis)
            ports.append(entry)
        return ports

    def get_port(self, axis_name: str) -> Optional[Dict[str, Any]]:
        """Get a port by axis, or by port name when the axis key misses.

        The θ router looks ports up by *name*; the registry is keyed by axis.
        Accepting both keeps the two views consistent.
        """
        port = self._ports.get(axis_name)
        if port is not None:
            return port
        for candidate in self._ports.values():
            if candidate.get("name") == axis_name:
                return candidate
        return None

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
