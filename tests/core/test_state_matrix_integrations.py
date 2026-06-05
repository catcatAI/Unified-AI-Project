"""Tests for StateMatrixAdapter integration features"""


try:
    from core.engine.state_matrix_adapter import StateMatrixAdapter
except ImportError:
    import pytest; pytest.skip("StateMatrixAdapter is a stub", allow_module_level=True)


def test_attractor_field_integration():
    sm = StateMatrixAdapter()

    g = sm.compute_gradient()
    assert g is not None
    assert "gradient" in g
    assert "gradient_strength" in g
    assert "nearest_attractors" in g
    assert len(g["nearest_attractors"]) > 0

    n = sm.navigate_to_attractor(max_steps=3)
    assert n is not None
    assert "navigation_steps" in n
    assert "new_state" in n
    assert "nearest_attractors" in n


def test_attractor_add_remove():
    sm = StateMatrixAdapter()

    result = sm.add_attractor(
        coord=(0.5, 0.5, 0.5, 0.5, 0.5),
        behavior="test behavior",
        tone="calm",
        mass=1.5,
        tags=["test_tag"],
    )
    assert result is True

    removed = sm.remove_attractor_by_tags(["test_tag"])
    assert removed >= 0


def test_gradient_field_property():
    sm = StateMatrixAdapter()
    gf = sm.gradient_field
    assert gf is not None
    assert hasattr(gf, "compute_gradient")
    assert hasattr(gf, "navigate")


def test_save_load_state():
    sm = StateMatrixAdapter()
    sm.update_alpha(energy=0.8)
    sm.update_beta(focus=0.7)
    sm.update_gamma(happiness=0.6)

    state = sm.save_state()
    assert "dimensions" in state
    assert "alpha" in state["dimensions"]
    assert "update_count" in state
    assert state["update_count"] > 0

    sm2 = StateMatrixAdapter()
    sm2.load_state(state)
    assert sm2._sm.alpha.values.get("energy") == 0.8


def test_temporal_property():
    sm = StateMatrixAdapter()
    assert sm.temporal is not None
    assert hasattr(sm.temporal, "trend")
    assert hasattr(sm.temporal, "anomalies")
    assert hasattr(sm.temporal, "record")


def test_influence_space_property():
    sm = StateMatrixAdapter()
    assert sm.influence_space is not None
    assert hasattr(sm.influence_space, "compute")


def test_allocation_policy_property():
    sm = StateMatrixAdapter()
    assert sm.allocation_policy is not None
    assert hasattr(sm.allocation_policy, "decide")


def test_code_inspect_integration():
    sm = StateMatrixAdapter()

    result = sm.integrate_code_inspect({"report": None})
    assert result["status"] == "skip"

    report = sm.code_inspect_report()
    assert "epsilon_complexity" in report
    assert "theta_negativity" in report


def test_full_report_includes_new_fields():
    sm = StateMatrixAdapter()
    sm.navigate_to_attractor(max_steps=2)

    report = sm.full_report()
    assert "state_matrix" in report
    assert "temporal" in report
    assert "influence" in report
    assert "allocation" in report
    assert "negativity" in report
    assert "port_routing" in report


if __name__ == "__main__":
    test_attractor_field_integration()
    test_attractor_add_remove()
    test_gradient_field_property()
    test_save_load_state()
    test_temporal_property()
    test_influence_space_property()
    test_allocation_policy_property()
    test_code_inspect_integration()
    test_full_report_includes_new_fields()
    print("All integration tests passed!")