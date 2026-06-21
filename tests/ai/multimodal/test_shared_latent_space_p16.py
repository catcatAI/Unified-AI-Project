import numpy as np
import pytest


@pytest.fixture
def ls():
    from ai.multimodal.shared_latent_space import SharedLatentSpace
    space = SharedLatentSpace(latent_dim=64)
    space.register_modality("vision", 128)
    space.register_modality("audio", 32)
    space.register_modality("text", 256)
    return space


def _random_feat(dim):
    return np.random.default_rng(42).normal(0, 1, dim).astype(np.float32)


class TestContrastiveLearning:

    def test_train_reduces_loss(self, ls):
        pos_pairs = [
            ("vision", _random_feat(128), "text", _random_feat(256)),
            ("vision", _random_feat(128), "text", _random_feat(256)),
        ]
        neg_pairs = [
            ("vision", _random_feat(128), "audio", _random_feat(32)),
            ("audio", _random_feat(32), "text", _random_feat(256)),
        ]
        result = ls.train(pos_pairs, neg_pairs, epochs=50, lr=0.05, margin=0.5)
        assert "final_loss" in result
        assert "history" in result
        assert len(result["history"]) == 50
        assert result["final_loss"] <= result["history"][0] * 0.98

    def test_positive_pairs_become_closer(self, ls):
        feat_a = _random_feat(128)
        feat_b = _random_feat(256)

        before = ls.project("vision", feat_a) - ls.project("text", feat_b)
        dist_before = float(np.dot(before, before))

        pos_pairs = [("vision", feat_a, "text", feat_b)]
        ls.train(pos_pairs, [], epochs=100, lr=0.1, margin=0.5)

        after = ls.project("vision", feat_a) - ls.project("text", feat_b)
        dist_after = float(np.dot(after, after))

        assert dist_after < dist_before * 0.98

    def test_negative_pairs_become_farther(self, ls):
        feat_a = _random_feat(128)
        feat_b = _random_feat(32)

        before = ls.project("vision", feat_a) - ls.project("audio", feat_b)
        dist_before = float(np.dot(before, before))

        neg_pairs = [("vision", feat_a, "audio", feat_b)]
        ls.train([], neg_pairs, epochs=100, lr=0.1, margin=1.0)

        after = ls.project("vision", feat_a) - ls.project("audio", feat_b)
        dist_after = float(np.dot(after, after))

        assert dist_after >= dist_before - 1e-4

    def test_no_registered_modality_returns_zero_loss(self, ls):
        result = ls.train([("unknown", _random_feat(10), "vision", _random_feat(128))], [], epochs=1)
        assert result["final_loss"] == 0.0

    def test_training_updates_weights(self, ls):
        W_before = ls._projections["vision"]["W"].copy()
        pos_pairs = [("vision", _random_feat(128), "text", _random_feat(256))]
        ls.train(pos_pairs, [], epochs=10, lr=0.05)
        W_after = ls._projections["vision"]["W"]
        assert not np.allclose(W_before, W_after)


class TestCrossModalAttention:

    def test_attention_weights_sum_to_one(self, ls):
        ls.project("vision", _random_feat(128))
        ls.project("audio", _random_feat(32))
        ls.project("text", _random_feat(256))

        weights = ls.cross_modal_attention("vision", ["audio", "text"])
        assert abs(sum(weights.values()) - 1.0) < 1e-5

    def test_attention_self_is_highest(self, ls):
        ls.project("vision", _random_feat(128))
        ls.project("audio", _random_feat(32))

        weights = ls.cross_modal_attention("vision", ["vision", "audio"])
        assert weights["vision"] >= weights["audio"]

    def test_unknown_query_returns_zeros(self, ls):
        weights = ls.cross_modal_attention("unknown", ["vision"])
        assert all(v == 0.0 for v in weights.values())

    def test_all_modalities_in_result(self, ls):
        ls.project("vision", _random_feat(128))
        ls.project("audio", _random_feat(32))
        ls.project("text", _random_feat(256))

        weights = ls.cross_modal_attention("vision", ["audio", "text"])
        assert set(weights.keys()) == {"audio", "text"}
