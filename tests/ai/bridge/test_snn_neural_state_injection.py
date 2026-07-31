# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================
"""
Integration test: GARDEN SNN forward() reads the ``neural_state`` context
slot injected by the NeuralBridge (the designed-but-unused context parameter
is now activated as the StateMatrix → SNN connection point).
"""

import pytest

from ai.garden.snn_core import TensorSNNCore


class TestSNNNeuralStateInjection:
    """Tests that SNN forward() consumes the NeuralBridge context slot."""

    def test_neural_state_merges_into_activations(self):
        core = TensorSNNCore(timesteps=4)
        core._register_key("emo_happy")
        core._register_key("emo_sadness")
        core._register_key("r1")
        core._register_key("r2")
        core.add_relation("emo_happy", "r1", weight=0.9, bidirectional=True)
        core.add_relation("emo_sadness", "r2", weight=0.9, bidirectional=True)

        # Without neural_state: only emo_happy's target r1 is activated.
        base = core.forward({"emo_happy": 1.0})
        assert "r1" in base
        assert "r2" not in base
        # With neural_state: emo_sadness is also injected, activating r2.
        injected = core.forward(
            {"emo_happy": 1.0},
            context={"neural_state": {"emo_sadness": 0.8}},
        )
        assert "r2" in injected

    def test_neural_state_ignores_unregistered_keys(self):
        core = TensorSNNCore(timesteps=4)
        core._register_key("g1")
        core.add_relation("g1", "r1", weight=0.9, bidirectional=True)
        # A key outside the vocab must be silently skipped (no crash, no forced
        # injection of arbitrary state into the neural network).
        result = core.forward(
            {"g1": 1.0},
            context={"neural_state": {"not_a_real_concept": 1.0}},
        )
        assert isinstance(result, dict)
        assert "not_a_real_concept" not in result

    def test_neural_state_without_context_unchanged(self):
        core = TensorSNNCore(timesteps=4)
        core._register_key("g1")
        core.add_relation("g1", "r1", weight=0.9, bidirectional=True)
        with_ctx = core.forward({"g1": 1.0}, context={"mode": "x"})
        without_ctx = core.forward({"g1": 1.0})
        # Same behaviour — a non-neural_state context must not alter output.
        assert with_ctx == without_ctx
