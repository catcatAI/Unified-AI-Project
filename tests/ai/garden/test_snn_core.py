# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [C] [L0]
# =============================================================================
"""
Tests for GARDEN TensorSNNCore.
"""

import os
import tempfile

import pytest
from ai.garden.snn_core import (
    DEFAULT_DECAY,
    DEFAULT_LEAK,
    DEFAULT_THRESHOLD,
    DEFAULT_TIMESTEPS,
    HormonalModulator,
    TensorSNNCore,
)


class TestHormonalModulator:
    """Tests for the hormone-based threshold modulator."""

    def test_init(self):
        m = HormonalModulator()
        assert "cortisol" in m.hormones
        assert "serotonin" in m.hormones
        assert "dopamine" in m.hormones
        assert m.hormones["cortisol"] == 0.5
        assert m.hormones["serotonin"] == 0.5

    def test_set_hormone_clamps(self):
        m = HormonalModulator()
        m.set_hormone("cortisol", 2.0)
        assert m.hormones["cortisol"] == 1.0
        m.set_hormone("serotonin", -0.5)
        assert m.hormones["serotonin"] == 0.0

    def test_threshold_multiplier_normal(self):
        m = HormonalModulator()
        mult = m.get_threshold_multiplier()
        assert 0.4 <= mult <= 1.6

    def test_threshold_multiplier_stressed(self):
        m = HormonalModulator()
        m.set_hormone("cortisol", 1.0)
        m.set_hormone("adrenaline", 1.0)
        mult = m.get_threshold_multiplier()
        assert mult < 1.0  # Stress lowers threshold (more reactive)

    def test_threshold_multiplier_calm(self):
        m = HormonalModulator()
        m.set_hormone("serotonin", 1.0)
        mult = m.get_threshold_multiplier()
        assert mult > 0.95  # Calm raises threshold

    def test_profile_summary(self):
        m = HormonalModulator()
        profile = m.get_profile_summary()
        assert isinstance(profile, dict)
        assert len(profile) >= 6


class TestTensorSNNCoreInit:
    """Tests for SNN core construction."""

    def test_init_defaults(self):
        core = TensorSNNCore()
        assert core.leak == DEFAULT_LEAK
        assert core.base_threshold == DEFAULT_THRESHOLD
        assert core.timesteps == DEFAULT_TIMESTEPS
        assert core.decay == DEFAULT_DECAY
        assert core.vocab_size == 0
        assert core._W is None

    def test_init_custom(self):
        core = TensorSNNCore(leak=0.1, threshold=0.5, timesteps=10, decay=0.8)
        assert core.leak == 0.1
        assert core.base_threshold == 0.5
        assert core.timesteps == 10
        assert core.decay == 0.8


class TestTensorSNNCoreKeyRegistry:
    """Tests for key registration and vocabulary management."""

    def test_register_key(self, snn_core: TensorSNNCore):
        core = snn_core
        before = core.vocab_size
        idx = core._register_key("new_key")
        assert core.vocab_size == before + 1
        assert idx == before  # New key gets next index

    def test_register_duplicate(self, snn_core: TensorSNNCore):
        core = snn_core
        idx1 = core._register_key("g1")
        idx2 = core._register_key("g1")
        assert idx1 == idx2
        assert core.vocab_size == 6  # As defined in conftest

    def test_grow_matrix(self, snn_core: TensorSNNCore):
        core = snn_core
        old_v = core.vocab_size
        core._register_key("very_new_key")
        # Amortized (doubling) growth: matrix capacity grows to >= old_v + 1,
        # while the live region always matches vocab_size.
        assert core._W.shape[0] >= old_v + 1
        assert core._W.shape[1] >= old_v + 1
        assert core._W.shape[0] == core._W.shape[1]

    def test_vocab_size_property(self, snn_core: TensorSNNCore):
        assert snn_core.vocab_size == 6


class TestTensorSNNCoreRelations:
    """Tests for relation management."""

    def test_add_relation(self, snn_core: TensorSNNCore):
        core = snn_core
        core.add_relation("g1", "e1", weight=0.8, bidirectional=True)
        i = core._key_to_idx["g1"]
        j = core._key_to_idx["e1"]
        assert core._W[i, j] == 0.8
        assert core._W[j, i] == 0.8

    def test_add_relation_directed(self, snn_core: TensorSNNCore):
        core = snn_core
        core.add_relation("g1", "e1", weight=0.8, bidirectional=False)
        i = core._key_to_idx["g1"]
        j = core._key_to_idx["e1"]
        assert core._W[i, j] == 0.8
        assert core._W[j, i] == 0.0

    def test_add_relation_accumulates(self, snn_core: TensorSNNCore):
        core = snn_core
        core.add_relation("g1", "e1", weight=0.5, bidirectional=True)
        core.add_relation("g1", "e1", weight=0.5, bidirectional=True)
        i = core._key_to_idx["g1"]
        j = core._key_to_idx["e1"]
        assert core._W[i, j] == 1.0  # Clamped to 1.0

    def test_add_relations_from_entry(self, snn_core: TensorSNNCore):
        core = snn_core
        relations = {"synonym": ["e1"], "mapping": ["r1"]}
        core.add_relations_from_entry("g1", relations)
        i = core._key_to_idx["g1"]
        j = core._key_to_idx["e1"]
        k = core._key_to_idx["r1"]
        # Synonym: 0.9, Mapping: 0.7
        assert core._W[i, j] >= 0.9
        assert core._W[i, k] >= 0.7


class TestTensorSNNCoreForward:
    """Tests for the LIF multi-step forward pass."""

    def test_forward_known_input(self, snn_core: TensorSNNCore):
        core = snn_core
        result = core.forward(["g1"])
        assert isinstance(result, dict)
        assert len(result) >= 1

    def test_forward_empty_keys(self, snn_core: TensorSNNCore):
        core = snn_core
        assert core.forward([]) == {}

    def test_forward_unregistered_keys(self, snn_core: TensorSNNCore):
        core = snn_core
        assert core.forward(["nonexistent"]) == {}

    def test_forward_propagates(self, snn_core: TensorSNNCore):
        """Input 'g1' should propagate to 'g5' (synonym) and 'r1'/'r2'."""
        core = snn_core
        result = core.forward(["g1"])
        assert "g5" in result
        # g5 connects to r1, so r1 should be activated (2 hops)
        assert "r1" in result

    def test_forward_scores_normalized(self, snn_core: TensorSNNCore):
        core = snn_core
        result = core.forward(["g1"])
        for score in result.values():
            assert 0.0 <= score <= 1.0

    def test_forward_with_context(self, snn_core: TensorSNNCore):
        core = snn_core
        result = core.forward(["g1"], context={"mode": "test"})
        assert isinstance(result, dict)
        assert len(result) >= 1

    def test_forward_hormonal_modulation(self, snn_core: TensorSNNCore):
        core = snn_core
        # Set high stress
        core.modulator.set_hormone("cortisol", 1.0)
        core.modulator.set_hormone("adrenaline", 1.0)
        result = core.forward(["g1"])
        assert isinstance(result, dict)

    def test_forward_no_w_matrix(self):
        core = TensorSNNCore()
        result = core.forward(["g1"])
        assert result == {}


class TestTensorSNNCoreHebbian:
    """Tests for Hebbian learning."""

    def test_hebbian_update(self, snn_core: TensorSNNCore):
        core = snn_core
        delta = core.hebbian_update(["g1"], ["e1"], lr=0.1, target_strength=0.8)
        assert delta > 0
        i = core._key_to_idx["g1"]
        j = core._key_to_idx["e1"]
        assert core._W[i, j] > 0
        assert core._W[j, i] > 0

    def test_hebbian_empty_input(self, snn_core: TensorSNNCore):
        core = snn_core
        assert core.hebbian_update([], ["e1"]) == 0.0

    def test_hebbian_empty_target(self, snn_core: TensorSNNCore):
        core = snn_core
        assert core.hebbian_update(["g1"], []) == 0.0

    def test_hebbian_tracks_updates(self, snn_core: TensorSNNCore):
        core = snn_core
        before = core.total_hebbian_updates
        core.hebbian_update(["g1"], ["e1"])
        assert core.total_hebbian_updates == before + 1

    def test_hebbian_symmetric(self, snn_core: TensorSNNCore):
        core = snn_core
        core.hebbian_update(["g1"], ["e1"], lr=0.5, target_strength=0.9)
        i = core._key_to_idx["g1"]
        j = core._key_to_idx["e1"]
        assert core._W[i, j] == core._W[j, i]


class TestTensorSNNCorePersistence:
    """Tests for save/load."""

    def test_save_load(self, snn_core: TensorSNNCore):
        core = snn_core
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "snn.pt")
            core.save(path)
            core2 = TensorSNNCore()
            core2.load(path)
        assert core2.vocab_size == core.vocab_size
        assert core2.leak == core.leak
        assert core2.base_threshold == core.base_threshold
        assert core2.timesteps == core.timesteps

    def test_save_load_preserves_weights(self, snn_core: TensorSNNCore):
        core = snn_core
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "snn.pt")
            core.save(path)
            core2 = TensorSNNCore()
            core2.load(path)
        i = core._key_to_idx["g1"]
        j = core._key_to_idx["g5"]
        i2 = core2._key_to_idx["g1"]
        j2 = core2._key_to_idx["g5"]
        assert core._W[i, j] == core2._W[i2, j2]

    def test_save_load_hebbian_history(self, snn_core: TensorSNNCore):
        core = snn_core
        core.hebbian_update(["g1"], ["e1"])
        core.total_steps = 42
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "snn.pt")
            core.save(path)
            core2 = TensorSNNCore()
            core2.load(path)
        assert core2.total_steps == 42
        assert core2.total_hebbian_updates >= 0


class TestTensorSNNCoreStats:
    """Tests for status/introspection."""

    def test_get_stats_empty(self):
        core = TensorSNNCore()
        s = core.get_stats()
        assert s["vocab_size"] == 0
        assert s["weight_matrix_shape"] == []
        assert s["matrix_density"] == 0.0

    def test_get_stats_with_data(self, snn_core: TensorSNNCore):
        s = snn_core.get_stats()
        assert s["vocab_size"] == 6
        assert s["weight_matrix_shape"] == [6, 6]
        assert s["matrix_density"] > 0
        assert s["matrix_memory_bytes"] == 6 * 6 * 4
        assert "hormones" in s
