"""Tests for theta_router.py"""

import pytest
from core.engine.theta_router import AxisBinding, RouteAction, RouteDecision, ThetaRouter


def make_vector(val: float = 0.5, nonzero: int = 8) -> list:
    vec = [0.0] * 32
    for i in range(nonzero):
        vec[i] = val
    return vec


def test_route_decision():
    decision = RouteDecision(
        action=RouteAction.BIND,
        port_name="test_port",
        target_axis="alpha",
        confidence=0.75,
        reasoning="test reason",
    )
    assert decision.action == RouteAction.BIND
    assert decision.target_axis == "alpha"
    assert decision.confidence == 0.75
    d = decision.to_dict()
    assert d["action"] == "bind"


def test_route_decision_create_axis():
    decision = RouteDecision(
        action=RouteAction.CREATE_AXIS,
        port_name="new_port",
        proposed_name="zeta",
        confidence=0.9,
        reasoning="low similarity",
    )
    assert decision.action == RouteAction.CREATE_AXIS
    assert decision.proposed_name == "zeta"


def test_theta_router_init():
    router = ThetaRouter(state_adapter=None, port_registry=None)
    assert router._state_adapter is None
    assert router._port_registry is None
    assert router._routing_history == []


def test_theta_router_resolve_skip_no_port():
    router = ThetaRouter(state_adapter=None, port_registry=None)
    decision = router.resolve_route("nonexistent")
    assert decision.action == RouteAction.SKIP


def test_theta_router_auto_allocate_no_registry():
    router = ThetaRouter(state_adapter=None, port_registry=None)
    bindings = router.auto_allocate()
    assert bindings == []


def test_theta_router_merge_input_no_registry():
    router = ThetaRouter(state_adapter=None, port_registry=None)
    result = router.merge_input("alpha", [("p1", {"val": 0.8})])
    assert result is None


def test_theta_router_cascade_no_registry():
    router = ThetaRouter(state_adapter=None, port_registry=None)
    result = router.cascade_output("alpha", {"focus": 0.8})
    assert result["status"] == "skip"


@pytest.mark.skip("TODO: PortRegistry class not yet implemented in axis_port_registry.py")
def test_theta_router_cascade_empty_outputs():
    pytest.importorskip("core.engine.axis_port_registry")
    from core.engine.axis_port_registry import PortDirection, PortRegistry

    registry = PortRegistry(state_adapter=None)
    registry.register(name="test", direction=PortDirection.IO, semantic_vector=make_vector())

    router = ThetaRouter(state_adapter=None, port_registry=registry)
    result = router.cascade_output("nonexistent_axis", {"data": 1.0})
    assert result["status"] == "no_outputs"


def test_theta_router_re_evaluate_no_registry():
    router = ThetaRouter(state_adapter=None, port_registry=None)
    decisions = router.re_evaluate_routing()
    assert decisions == []


def test_theta_router_record_routing():
    router = ThetaRouter(state_adapter=None, port_registry=None)
    decision = RouteDecision(
        action=RouteAction.BIND,
        port_name="p1",
        target_axis="beta",
        confidence=0.6,
        reasoning="test",
    )
    router._record_routing("p1", decision)
    assert len(router._routing_history) == 1
    assert router._routing_history[0]["port_name"] == "p1"


def test_theta_router_report():
    router = ThetaRouter(state_adapter=None, port_registry=None)
    report = router.get_routing_report()
    assert "theta_values" in report
    assert "total_decisions" in report
    assert "recent_decisions" in report


def _registry_with_port():
    from core.engine.axis_port_registry import AxisPortRegistry

    reg = AxisPortRegistry()
    reg.register_port("alpha", {"direction": "IO", "semantic_vector": make_vector()})
    return reg


def test_re_evaluate_with_dict_ports_no_crash():
    """R20: registry 回 dict ports 時不得 AttributeError（曾崩潰）。"""
    router = ThetaRouter(state_adapter=None, port_registry=_registry_with_port())
    assert router.re_evaluate_routing() == []


def test_auto_allocate_no_binding_api_no_crash():
    """R20: 綁定系 API 缺失時顯式 no-op（曾 TypeError/AttributeError）。"""
    from unittest.mock import MagicMock

    router = ThetaRouter(state_adapter=MagicMock(), port_registry=_registry_with_port())
    assert router._binding_api_ready() is False
    assert router.auto_allocate() == []


def test_apply_routing_decisions_no_binding_api_no_crash():
    """R20: REBIND/UNBIND 無綁定 API 時回 0 且不拋錯。"""
    from unittest.mock import MagicMock

    router = ThetaRouter(state_adapter=MagicMock(), port_registry=_registry_with_port())
    d = RouteDecision(
        action=RouteAction.REBIND,
        port_name="alpha",
        target_axis="beta",
        confidence=0.9,
        reasoning="t",
    )
    assert router.apply_routing_decisions([d]) == 0


def test_port_name_extraction_dict_and_object():
    """R20: dict 用 .get，物件用屬性，缺名回 None。"""
    assert ThetaRouter._port_name({"name": "p1"}) == "p1"
    assert ThetaRouter._port_name({"axis": "alpha"}) is None

    class FakePort:
        name = "p2"

    assert ThetaRouter._port_name(FakePort()) == "p2"
    assert ThetaRouter._port_name(object()) is None
