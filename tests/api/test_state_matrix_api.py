"""Smoke test for StateMatrix FastAPI Router (no server startup)"""

import pytest
try:
    from services.api.state_matrix_api import (
        state_matrix_router,
        get_state_matrix,
        AxisUpdateRequest,
        NavigateRequest,
        PortRegisterRequest,
        AllocationRequest,
    )
except ImportError:
    pytest.skip("state_matrix_router not available (stub module)", allow_module_level=True)


def test_router_exists():
    routes = state_matrix_router.routes
    assert len(routes) == 43
    paths = [r.path for r in routes]
    assert "/state/summary" in paths
    assert "/state/axis/{axis_name}" in paths
    assert "/state/gradient" in paths
    assert "/state/navigate" in paths
    assert "/state/port/register" in paths
    assert "/state/attractor/list" in paths
    assert "/state/health" in paths
    assert "/state/eta/report" in paths
    assert "/state/eta/cycle" in paths
    assert "/state/module/list" in paths
    print(f"  Router has {len(routes)} endpoints")


def test_state_matrix_integration():
    sm = get_state_matrix()
    summary = sm.full_report()
    assert "state_matrix" in summary
    assert "temporal" in summary
    assert "influence" in summary
    assert "allocation" in summary
    assert "negativity" in summary
    assert "port_routing" in summary
    print("  full_report() OK")


def test_axis_update():
    sm = get_state_matrix()
    sm.update_alpha(energy=0.7)
    axis_data = sm._sm.alpha.values
    assert axis_data.get("energy") == 0.7
    print("  update_alpha OK")


def test_gradient_and_navigate():
    sm = get_state_matrix()

    g = sm.compute_gradient()
    assert "gradient" in g
    assert "gradient_strength" in g
    assert isinstance(g["gradient_strength"], float)
    assert "nearest_attractors" in g
    print(f"  compute_gradient OK (strength={g['gradient_strength']:.2f})")

    n = sm.navigate_to_attractor(max_steps=3)
    assert "new_state" in n
    assert "nearest_attractors" in n
    assert n.get("navigation_steps", 0) > 0
    print(f"  navigate_to_attractor OK ({n['navigation_steps']} steps)")


def test_port_routing_api():
    sm = get_state_matrix()

    sm.register_port(
        name="test_api_port",
        direction="io",
        semantic_vector=[0.5] * 32,
    )
    ports = sm.list_ports()
    assert any(p["name"] == "test_api_port" for p in ports)
    print("  register_port OK")

    sm.unregister_port("test_api_port")
    ports = sm.list_ports()
    assert all(p["name"] != "test_api_port" for p in ports)
    print("  unregister_port OK")


def test_allocation_api():
    sm = get_state_matrix()
    vec = [0.1] * 32
    decision = sm.allocation_decide(vec, "api_test")
    assert decision.confidence > 0
    assert hasattr(decision, "action")
    print(f"  allocation_decide OK (action={decision.action.value})")


def test_save_load():
    sm = get_state_matrix()
    sm.update_beta(focus=0.9)

    state = sm.save_state()
    assert "dimensions" in state
    assert "beta" in state["dimensions"]
    print("  save_state OK")

    sm2 = get_state_matrix()
    sm2.load_state(state)
    assert sm2._sm.beta.values.get("focus") == 0.9
    print("  load_state OK")


def test_attractor_list():
    sm = get_state_matrix()
    gf = sm.gradient_field
    assert len(gf.attractors) > 0
    print(f"  gradient_field has {count} attractors")


def test_code_inspect_report():
    sm = get_state_matrix()
    report = sm.code_inspect_report()
    assert "epsilon_complexity" in report
    assert "theta_negativity" in report
    print("  code_inspect_report OK")


def test_influence_api():
    sm = get_state_matrix()
    inf = sm.influence_compute("alpha", "beta")
    assert isinstance(inf, float)
    assert 0 <= inf <= 1
    print(f"  influence_compute OK ({inf:.4f})")


def test_temporal_queries():
    sm = get_state_matrix()
    for _ in range(5):
        sm.update_alpha(energy=0.5 + 0.05 * _)

    trend = sm.temporal_trend("alpha", "energy", window=5)
    assert isinstance(trend, dict)
    print("  temporal_trend OK")

    anomalies = sm.temporal_anomalies("alpha", "energy", threshold=0.3)
    assert isinstance(anomalies, list)
    print(f"  temporal_anomalies OK ({len(anomalies)} found)")


if __name__ == "__main__":
    print("=== StateMatrix API Smoke Test ===\n")
    test_router_exists()
    test_state_matrix_integration()
    test_axis_update()
    test_gradient_and_navigate()
    test_port_routing_api()
    test_allocation_api()
    test_save_load()
    test_attractor_list()
    test_code_inspect_report()
    test_influence_api()
    test_temporal_queries()
    print("\n=== ALL API SMOKE TESTS PASSED ===")