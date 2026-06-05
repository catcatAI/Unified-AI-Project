"""Tests for theta_router.py"""

import pytest

from core.engine.theta_router import ThetaRouter, RouteAction, RouteDecision, AxisBinding


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


def test_theta_router_cascade_empty_outputs():
    pytest.importorskip("core.autonomous.axis_port_registry")
    from core.autonomous.axis_port_registry import PortRegistry, PortDirection

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


if __name__ == "__main__":
    test_route_decision()
    test_route_decision_create_axis()
    test_theta_router_init()
    test_theta_router_resolve_skip_no_port()
    test_theta_router_auto_allocate_no_registry()
    test_theta_router_merge_input_no_registry()
    test_theta_router_cascade_no_registry()
    test_theta_router_cascade_empty_outputs()
    test_theta_router_re_evaluate_no_registry()
    test_theta_router_record_routing()
    test_theta_router_report()
    print("All theta_router tests passed!")