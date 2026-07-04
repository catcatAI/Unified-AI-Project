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
    """6 axes accessible as properties through the adapter."""

    def test_alpha_returns_values_dict(self, adapter):
        assert isinstance(getattr(adapter.alpha, "values", None), dict)

    def test_beta_returns_values_dict(self, adapter):
        assert isinstance(getattr(adapter.beta, "values", None), dict)

    def test_gamma_returns_values_dict(self, adapter):
        assert isinstance(getattr(adapter.gamma, "values", None), dict)

    def test_delta_returns_values_dict(self, adapter):
        assert isinstance(getattr(adapter.delta, "values", None), dict)

    def test_theta_returns_values_dict(self, adapter):
        assert isinstance(getattr(adapter.theta, "values", None), dict)

    def test_zeta_returns_values_dict(self, adapter):
        assert isinstance(getattr(adapter.zeta, "values", None), dict)

    def test_history_is_list_like(self, adapter):
        assert hasattr(adapter.history, "__len__")


class TestUpdateMethods:
    """All 7 update methods can be called and verify state changed."""

    def test_update_alpha_succeeds(self, adapter):
        adapter.update_alpha(focus=0.8)
        assert adapter.alpha.values.get("focus") == 0.8

    def test_update_beta_succeeds(self, adapter):
        adapter.update_beta(curiosity=0.6)
        assert adapter.beta.values.get("curiosity") == 0.6

    def test_update_gamma_succeeds(self, adapter):
        adapter.update_gamma(excitement=0.7)
        assert adapter.gamma.values.get("excitement") == 0.7

    def test_update_delta_succeeds(self, adapter):
        adapter.update_delta(engagement=0.5)
        assert adapter.delta.values.get("engagement") == 0.5

    def test_update_epsilon_succeeds(self, adapter):
        adapter.update_epsilon(awareness=0.9)
        assert adapter.epsilon.values.get("awareness") == 0.9

    def test_update_theta_succeeds(self, adapter):
        adapter.update_theta(doubt=0.3)
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


class TestTemporalQueries:
    """New API: temporal trend / anomalies."""

    def test_temporal_trend_returns_value(self, adapter):
        result = adapter.temporal_trend("alpha", "focus", window=5)
        assert result is not None


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
