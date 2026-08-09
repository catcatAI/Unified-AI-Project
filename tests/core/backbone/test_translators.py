# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""內建轉譯器測試（§5.3 步驟 B2 — neural_bridge / semantic_key_mapper 註冊）。"""

import pytest
from core.backbone.translators import NeuralBridgeTranslator, SemanticKeyMapperTranslator


class _FakeDim:
    def __init__(self, values):
        self.values = values


class _FakeStateMatrix:
    alpha = _FakeDim({"energy": 0.9})
    beta = _FakeDim({"focus": 0.4})
    gamma = _FakeDim({"happiness": 0.7})
    delta = _FakeDim({"attention": 0.3})


@pytest.fixture
def bb():
    from core.backbone import get_backbone, reset_backbone

    reset_backbone()
    yield get_backbone()
    reset_backbone()


class TestDefaultTranslatorRegistration:
    def test_neural_bridge_registered(self, bb):
        assert bb.registries.translators.has("neural_bridge")

    def test_semantic_key_mapper_registered(self, bb):
        assert bb.registries.translators.has("semantic_key_mapper")

    def test_summary_counts(self, bb):
        assert bb.summary()["translators"] == 2


class TestNeuralBridgeTranslator:
    def test_can_translate_state_to_neural(self):
        t = NeuralBridgeTranslator()
        assert t.can_translate("state_matrix", "neural", "down")
        assert t.can_translate("neural", "state_matrix", "up")
        assert not t.can_translate("neural", "garden", "down")

    def test_state_to_neural_maps_axis_values(self):
        t = NeuralBridgeTranslator()
        result = t.translate(_FakeStateMatrix(), direction="down")
        assert result["sci_energy"] == 0.9  # alpha.energy → sci_energy
        assert result["c1"] == 0.4  # beta.focus → c1
        assert result["emo_happy"] == 0.7  # gamma.happiness → emo_happy

    def test_neural_to_state_updates(self):
        t = NeuralBridgeTranslator()
        updates = t.translate({"sci_energy": 0.8, "emo_anger": 0.5}, direction="up")
        assert updates == {"alpha": {"energy": 0.8}, "gamma": {"anger": 0.5}}

    def test_backbone_translate_integration(self, bb):
        result = bb.translate("state_matrix", "neural", _FakeStateMatrix(), direction="down")
        assert result["sci_energy"] == 0.9


class TestSemanticKeyMapperTranslator:
    def test_can_translate_latent_to_keys(self):
        t = SemanticKeyMapperTranslator()
        assert t.can_translate("latent", "keys", "down")
        assert not t.can_translate("keys", "latent", "down")

    def test_translate_identity_without_index(self, bb):
        import numpy as np

        result = bb.translate("latent", "keys", np.zeros(64), direction="down", top_k=3)
        assert result == []

    def test_index_then_map(self, bb):
        import numpy as np

        t = SemanticKeyMapperTranslator()
        key = "concept_1"
        t.index_key(key, np.ones(64), mode="semantic")
        t.index_key("concept_2", np.zeros(64), mode="semantic")
        result = t.translate(np.ones(64), direction="down", top_k=1, mode="semantic")
        assert result and result[0]["key"] == key

    def test_reverse_direction_identity(self, bb):
        t = SemanticKeyMapperTranslator()
        data = {"some": "data"}
        assert t.translate(data, direction="up") == data
