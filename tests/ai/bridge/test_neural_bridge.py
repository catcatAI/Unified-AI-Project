# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================
"""
Tests for the NeuralBridge — minimal-translation direct link between
StateMatrix axis values and GARDEN/ED3N SNN concept activations.

Both sides are "key → [0,1] value" dictionaries; the bridge connects them
with a pure symbolic key mapping (no vector projection, no numeric scaling).
"""

import pytest

from ai.bridge.neural_bridge import (
    _GARDEN_TO_STATE,
    _STATE_TO_GARDEN,
    apply_state_updates,
    build_neural_context,
    neural_bridge_enabled,
    neural_outputs_to_state_updates,
    state_to_neural_inputs,
)


class _FakeDim:
    """Minimal stand-in for DimensionState exposing a `.values` dict."""

    def __init__(self, values):
        self.values = dict(values)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.values:
                self.values[key] = max(0.0, min(1.0, float(value)))


class _FakeStateMatrix:
    """Minimal stand-in for StateMatrix4D exposing axis objects."""

    def __init__(self):
        self.alpha = _FakeDim({"energy": 0.8, "comfort": 0.5})
        self.beta = _FakeDim({"focus": 0.9, "curiosity": 0.6})
        self.gamma = _FakeDim(
            {"happiness": 0.7, "sadness": 0.1, "anger": 0.0, "fear": 0.2}
        )
        self.delta = _FakeDim({"attention": 0.5, "bond": 0.4})
        self.epsilon = _FakeDim({"logic": 0.5})
        self.theta = _FakeDim({"novelty": 0.5})
        self.zeta = _FakeDim({"narrative_flow": 0.5})

    def apply(self, updates):
        for axis, values in updates.items():
            dim = getattr(self, axis, None)
            if dim is not None:
                dim.values.update(values)


class TestSwitch:
    """Tests for the neural_bridge compute-config switch."""

    def test_enabled_returns_bool(self):
        assert isinstance(neural_bridge_enabled(), bool)

    def test_mapping_tables_are_inverse(self):
        # Every state→neural entry must have a reverse entry.
        assert len(_STATE_TO_GARDEN) == len(_GARDEN_TO_STATE)
        for axis_key, neural_key in _STATE_TO_GARDEN.items():
            assert _GARDEN_TO_STATE[neural_key] == axis_key


class TestStateToNeural:
    """Tests for StateMatrix → SNN injection mapping."""

    def test_maps_mapped_keys_only(self):
        sm = _FakeStateMatrix()
        inputs = state_to_neural_inputs(sm)
        assert "emo_happy" in inputs
        assert "emo_sadness" in inputs
        assert "sci_energy" in inputs
        # Unmapped state keys (e.g. comfort, bond) are NOT forced into the SNN.
        assert "comfort" not in inputs
        assert "bond" not in inputs

    def test_values_passthrough_unchanged(self):
        sm = _FakeStateMatrix()
        inputs = state_to_neural_inputs(sm)
        assert inputs["sci_energy"] == 0.8
        assert inputs["emo_happy"] == 0.7

    def test_values_clamped_to_unit_interval(self):
        sm = _FakeStateMatrix()
        sm.gamma.values["happiness"] = 1.7
        sm.beta.values["focus"] = -0.3
        inputs = state_to_neural_inputs(sm)
        assert inputs["emo_happy"] == 1.0
        assert inputs["c1"] == 0.0

    def test_none_state_returns_empty(self):
        assert state_to_neural_inputs(None) == {}

    def test_missing_axis_skipped(self):
        sm = _FakeStateMatrix()
        del sm.delta
        inputs = state_to_neural_inputs(sm)
        # c2 (delta.attention) must be absent — no forced zero injection.
        assert "c2" not in inputs


class TestNeuralToState:
    """Tests for SNN → StateMatrix writeback mapping."""

    def test_maps_neural_keys_back(self):
        updates = neural_outputs_to_state_updates({"emo_happy": 0.6, "sci_energy": 0.9})
        assert updates["gamma"]["happiness"] == 0.6
        assert updates["alpha"]["energy"] == 0.9

    def test_unknown_neural_keys_ignored(self):
        updates = neural_outputs_to_state_updates({"some_random_concept": 0.9})
        assert updates == {}

    def test_empty_output(self):
        assert neural_outputs_to_state_updates(None) == {}
        assert neural_outputs_to_state_updates({}) == {}

    def test_clamps_on_writeback(self):
        updates = neural_outputs_to_state_updates({"emo_happy": 1.9, "emo_sadness": -0.2})
        assert updates["gamma"]["happiness"] == 1.0
        assert updates["gamma"]["sadness"] == 0.0


class TestApplyUpdates:
    """Tests for applying writeback updates to a state matrix."""

    def test_applies_via_dimension_api(self):
        sm = _FakeStateMatrix()
        updates = {"gamma": {"happiness": 0.6}, "alpha": {"energy": 0.9}}
        count = apply_state_updates(sm, updates)
        assert count == 2
        assert sm.gamma.values["happiness"] == 0.6
        assert sm.alpha.values["energy"] == 0.9

    def test_none_state_returns_zero(self):
        assert apply_state_updates(None, {"gamma": {"happiness": 0.5}}) == 0

    def test_unknown_axis_skipped(self):
        sm = _FakeStateMatrix()
        updates = {"nonexistent_axis": {"energy": 0.5}}
        assert apply_state_updates(sm, updates) == 0


class TestNeuralContext:
    """Tests for the forward-direction context injection slot."""

    def test_injects_neural_state_slot(self):
        sm = _FakeStateMatrix()
        ctx = build_neural_context({"mode": "test"}, sm)
        assert ctx["mode"] == "test"
        assert "neural_state" in ctx
        assert ctx["neural_state"]["emo_happy"] == 0.7

    def test_no_neural_state_when_no_mapped_values(self):
        sm = _FakeStateMatrix()
        sm.alpha.values.clear()
        sm.beta.values.clear()
        sm.gamma.values.clear()
        sm.delta.values.clear()
        ctx = build_neural_context({"mode": "test"}, sm)
        assert "neural_state" not in ctx

    def test_context_copy_not_mutated(self):
        original = {"mode": "test"}
        sm = _FakeStateMatrix()
        ctx = build_neural_context(original, sm)
        assert "neural_state" not in original
        assert ctx is not original
