"""
Tests for StateMatrixAdapter — Phase 7 integration adapter.

Tests core wrapper methods (update, influence, temporal, allocation).
StateMatrix4D (torch/numpy) is resolved at runtime; if unavailable the
test session gracefully skips.
"""

import pytest


@pytest.fixture(scope="module")
def adapter():
    """Lazy import: StateMatrixAdapter triggers StateMatrix4D init."""
    from core.engine.state_matrix_adapter import StateMatrixAdapter

    return StateMatrixAdapter()


class TestAxisAccess:
    """All axes accessible as properties through the adapter."""

    @pytest.mark.parametrize("axis_name", ["alpha", "beta", "gamma", "delta", "theta", "zeta"])
    def test_axis_returns_values_dict(self, adapter, axis_name):
        axis = getattr(adapter, axis_name)
        assert isinstance(getattr(axis, "values", None), dict)

    def test_history_is_list_like(self, adapter):
        assert hasattr(adapter.history, "__len__")


class TestUpdateMethods:
    """All update methods can be called and verify state changed."""

    @pytest.mark.parametrize("axis_name,field,value", [
        ("alpha", "focus", 0.8),
        ("beta", "curiosity", 0.6),
        ("gamma", "excitement", 0.7),
        ("delta", "engagement", 0.5),
        ("epsilon", "awareness", 0.9),
        ("theta", "doubt", 0.3),
        ("zeta", "surprise", 0.4),
    ])
    def test_update_axis_succeeds(self, adapter, axis_name, field, value):
        update_fn = getattr(adapter, f"update_{axis_name}")
        update_fn(**{field: value})
        axis = getattr(adapter, axis_name)
        assert axis.values.get(field) == value
        assert adapter.theta.values.get("doubt") == 0.3

    def test_update_zeta_succeeds(self, adapter):
        adapter.update_zeta(surprise=0.4)
        assert adapter.zeta.values.get("surprise") == 0.4


class TestInfluenceComputation:
    """Cross-axis influence computation."""

    def test_compute_influences_returns_dict(self, adapter):
        result = adapter.compute_influences()
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_compute_influences_has_known_keys(self, adapter):
        result = adapter.compute_influences()
        for axis in ("alpha", "beta", "gamma", "delta"):
            assert axis in result

    def test_compute_influences_reflects_actual_state(self):
        from core.engine.state_matrix_adapter import StateMatrixAdapter
        sm = StateMatrixAdapter()
        sm.update_alpha(energy=0.8, comfort=0.6)
        sm.update_beta(focus=0.9, curiosity=0.7)
        result = sm.compute_influences()
        assert result["alpha"] > 0, "alpha influence should be > 0 when both alpha and beta have values"
        assert result["beta"] > 0, "beta influence should be > 0 when both alpha and beta have values"

    def test_compute_influences_empty_when_no_state(self):
        from core.engine.state_matrix_adapter import StateMatrixAdapter
        sm = StateMatrixAdapter()
        result = sm.compute_influences()
        assert all(v == 0.0 for v in result.values()), "all influences should be 0 with empty state"


class TestTemporalQueries:
    """New API: temporal trend / anomalies."""

    def test_temporal_trend_returns_value(self, adapter):
        result = adapter.temporal_trend("alpha", "focus", window=5)
        assert result is not None

    def test_temporal_trend_computes_real_trend(self):
        from core.engine.state_matrix_adapter import StateMatrixAdapter
        sm = StateMatrixAdapter()
        for v in [0.1, 0.2, 0.3, 0.4, 0.5]:
            sm.temporal.record("alpha", "energy", v)
        trend = sm.temporal_trend("alpha", "energy", window=5)
        assert trend is not None
        assert trend > 0, f"trend should be positive (increasing values), got {trend}"

    def test_temporal_trend_zero_for_empty(self):
        from core.engine.state_matrix_adapter import StateMatrixAdapter
        sm = StateMatrixAdapter()
        trend = sm.temporal_trend("alpha", "energy")
        assert trend == 0.0

    def test_temporal_anomalies_detects_outliers(self):
        from core.engine.state_matrix_adapter import StateMatrixAdapter
        sm = StateMatrixAdapter()
        for v in [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 5.0]:
            sm.temporal.record("alpha", "energy", v)
        anomalies = sm.temporal.anomalies
        assert len(anomalies) > 0, "should detect 5.0 as anomaly in [0.5, ..., 0.5, 5.0]"


class TestStateExportImport:
    """State serialization round-trip via old API."""

    def test_export_to_dict_returns_axes(self, adapter):
        data = adapter.export_to_dict()
        assert isinstance(data, dict)
        assert "alpha" in data or "dimensions" in data

    def test_import_from_dict_succeeds(self, adapter):
        data = adapter.export_to_dict()
        adapter.import_from_dict(data)
        re_exported = adapter.export_to_dict()
        assert isinstance(re_exported, dict)


class TestNewApiAccess:
    """Refactored module accessor properties."""

    def test_temporal_property(self, adapter):
        assert hasattr(adapter.temporal, "record")

    def test_influence_space_property(self, adapter):
        assert hasattr(adapter.influence_space, "compute")

    def test_eta_property(self, adapter):
        assert hasattr(adapter.eta, "module_registry")

    def test_anchor_learning_property(self, adapter):
        assert hasattr(adapter.anchor_learning, "get_best_axis")

    def test_resonance_engine_property(self, adapter):
        assert hasattr(adapter.resonance_engine, "compute_profile")

    def test_allocation_policy_property(self, adapter):
        assert hasattr(adapter.allocation_policy, "stages")
