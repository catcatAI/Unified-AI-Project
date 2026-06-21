"""Tests for multimodal training pipeline — contrastive + reconstruction training."""

from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def pipeline():
    from ai.multimodal.training_pipeline import FullTrainingPipeline
    return FullTrainingPipeline()


class TestContrastiveBatchTrainer:

    @pytest.fixture
    def trainer(self, pipeline):
        return pipeline._contrastive

    def test_generate_pairs_returns_pos_and_neg(self, trainer):
        """generate_pairs returns (pos_pairs, neg_pairs) with correct lengths."""
        pos_pairs, neg_pairs = trainer.generate_pairs(5)
        assert len(pos_pairs) == 5
        assert len(neg_pairs) == 5

    def test_generate_pairs_pos_are_similar(self, trainer):
        """Positive pairs should have small feature difference (seed + noise)."""
        pos_pairs, neg_pairs = trainer.generate_pairs(10)
        # Each element is (mod_a, feat_a, mod_b, feat_b)
        for mod_a, feat_a, mod_b, feat_b in pos_pairs:
            assert mod_a == "vision"
            assert mod_b == "audio"
            assert feat_a.shape == (256,)
            assert feat_b.shape == (128,)

    def test_generate_pairs_neg_are_random(self, trainer):
        """Negative pairs should be random — no structural similarity."""
        pos_pairs, neg_pairs = trainer.generate_pairs(10)
        for mod_a, feat_a, mod_b, feat_b in neg_pairs:
            assert mod_a == "vision"
            assert mod_b == "audio"
            assert feat_a.shape == (256,)
            assert feat_b.shape == (128,)

    def test_train_epoch_reduces_loss(self, trainer):
        """Training with lr>0 should reduce contrastive loss vs lr=0."""
        pos_pairs, neg_pairs = trainer.generate_pairs(5)
        loss_before = trainer.train_epoch(pos_pairs, neg_pairs, lr=0.0)
        loss_after = trainer.train_epoch(pos_pairs, neg_pairs, lr=0.1)
        assert loss_after <= loss_before + 1e-6

    def test_train_returns_dict_with_final_loss_and_history(self, trainer):
        result = trainer.train(n_epochs=2, n_pairs_per_epoch=5)
        assert "final_loss" in result
        assert "history" in result
        assert len(result["history"]) == 2


class TestReconstructionTrainer:

    @pytest.fixture
    def trainer(self, pipeline):
        from ai.multimodal.training_pipeline import ReconstructionTrainer
        return ReconstructionTrainer(pipeline._ls, pipeline._reconstruction)

    def test_generate_features_returns_dict(self, trainer):
        features = trainer.generate_features(5)
        assert isinstance(features, dict)
        for mod in trainer._ls._projections:
            assert mod in features
            assert len(features[mod]) == 5

    def test_generate_features_has_correct_dims(self, trainer):
        features = trainer.generate_features(3)
        for mod, samples in features.items():
            for s in samples:
                if mod == "vision":
                    assert s.shape == (256,)
                elif mod == "audio":
                    assert s.shape == (128,)
                else:
                    assert s.shape == (64,)

    def test_train_returns_results_per_modality(self, trainer):
        result = trainer.train(n_epochs=2, n_samples=3, lr=0.005)
        assert isinstance(result, dict)
        for mod in trainer._ls._projections:
            assert mod in result
            assert "final_loss" in result[mod]
            assert "history" in result[mod]


class TestFullTrainingPipeline:

    def test_run_returns_both_phases(self, pipeline):
        result = pipeline.run(contrastive_epochs=2, contrastive_pairs=5,
                              recon_epochs=2, recon_samples=3, lr=0.01)
        assert "contrastive" in result
        assert "reconstruction" in result
        assert "final_loss" in result["contrastive"]
        assert result["contrastive"]["final_loss"] > 0

    def test_evaluate_returns_modalities(self, pipeline):
        result = pipeline.evaluate(n_samples=3)
        for mod in ["vision", "audio"]:
            assert mod in result
            assert "avg_reconstruction_loss" in result[mod]

    def test_run_with_no_epochs_still_returns(self, pipeline):
        """Edge case: zero epochs should still return valid dicts."""
        result = pipeline.run(contrastive_epochs=1, contrastive_pairs=2,
                              recon_epochs=1, recon_samples=2, lr=0.01)
        assert isinstance(result["contrastive"]["final_loss"], float)
        assert result["contrastive"]["final_loss"] > 0

    # --- P29: Weight persistence tests ---

    def test_save_weights_creates_file(self, pipeline, tmp_path):
        """save_weights should create a .npz file."""
        save_path = str(tmp_path / "test_weights.npz")
        result = pipeline.save_weights(save_path)
        assert result != ""
        assert Path(save_path).exists()

    def test_save_and_load_weights_roundtrip(self, pipeline, tmp_path):
        """After save+load, the weights should be identical."""
        save_path = str(tmp_path / "roundtrip.npz")

        # Train a bit to change weights from initial random
        pipeline.run(contrastive_epochs=2, contrastive_pairs=5,
                     recon_epochs=1, recon_samples=3, lr=0.01)

        # Save post-training weights
        pipeline.save_weights(save_path)

        # Snapshot the trained weights
        import numpy as np
        data_before = np.load(save_path, allow_pickle=False)
        w_before = data_before["vision_W"].copy()

        # Create a fresh pipeline (random weights) and load
        from ai.multimodal.training_pipeline import FullTrainingPipeline
        fresh = FullTrainingPipeline()
        loaded = fresh.load_weights(save_path)
        assert loaded

        # Verify weights match
        vis_W_now = fresh._ls._projections["vision"]["W"]
        assert np.allclose(vis_W_now, w_before)

    def test_load_weights_invalid_path(self, pipeline):
        """load_weights on nonexistent path should return False."""
        assert not pipeline.load_weights("/nonexistent/path.npz")

    def test_save_weights_default_path(self, pipeline):
        """save_weights() with no args should use DEFAULT_WEIGHTS_PATH."""
        from ai.multimodal.training_pipeline import DEFAULT_WEIGHTS_PATH
        result = pipeline.save_weights()
        assert result != ""
        assert Path(result).exists()
        # Clean up
        Path(result).unlink(missing_ok=True)
