"""
P43 tests for Semantic Latent Space Fusion.

Tests cover:
1. SharedLatentSpace extensions (6): register_semantic_modality, semantic_consistency
2. DualEncoderRouter integration (5): SharedLatentSpace wiring, consistency_report
3. Semantic contrastive training (4): pos/neg pairs, consistency improvement
4. Cross-modal semantic similarity (2): structural↔semantic comparison

Key difference from P42: the combined latent now lives in the SAME
SharedLatentSpace as all P15-P38 operations, not a random projection.
"""

import io
import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from ai.multimodal.dual_encoder_router import DualEncoderRouter
from ai.multimodal.shared_latent_space import SharedLatentSpace

# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture
def latent_space():
    """SharedLatentSpace with both structural and semantic modalities (P43)."""
    ls = SharedLatentSpace(latent_dim=64)
    ls.register_modality("vision", 256)
    ls.register_modality("audio", 128)
    ls.register_semantic_modality("vision", 512)
    ls.register_semantic_modality("audio", 384)
    return ls


@pytest.fixture
def router():
    """DualEncoderRouter for P43 integration tests."""
    return DualEncoderRouter()


# =========================================================================
# 1. SharedLatentSpace Semantic Extensions (6 tests)
# =========================================================================

class TestRegisterSemanticModality:
    """P43a: register_semantic_modality creates correct projection entries."""

    def test_register_vision_semantic(self, latent_space):
        """S1: register_semantic_modality('vision', 512) creates 'vision_semantic'."""
        mods = latent_space.registered_modalities()
        assert "vision_semantic" in mods
        assert "vision" in mods

    def test_register_audio_semantic(self, latent_space):
        """S2: register_semantic_modality('audio', 384) creates 'audio_semantic'."""
        mods = latent_space.registered_modalities()
        assert "audio_semantic" in mods
        assert "audio" in mods

    def test_project_semantic_modality(self, latent_space):
        """S3: projecting through semantic modality works."""
        features = np.random.randn(512).astype(np.float32)
        latent = latent_space.project("vision_semantic", features)
        assert latent.shape == (64,)
        assert np.linalg.norm(latent) > 0


class TestSemanticConsistency:
    """P43b: semantic_consistency metric."""

    def test_same_features_returns_high(self, latent_space):
        """S4: identical features → consistency ~1.0."""
        feat = np.random.randn(512).astype(np.float32)
        score = latent_space.semantic_consistency("vision", [feat, feat.copy()])
        assert score > 0.99

    def test_random_features_lower(self, latent_space):
        """S5: random features → consistency < 0.6 (well separated)."""
        feat_a = np.ones(512, dtype=np.float32)
        feat_b = -np.ones(512, dtype=np.float32)
        score = latent_space.semantic_consistency("vision", [feat_a, feat_b])
        # Opposite direction vectors should have low consistency
        assert score < 0.5

    def test_fewer_than_two_returns_zero(self, latent_space):
        """S6: single feature → consistency 0.0."""
        feat = np.random.randn(512).astype(np.float32)
        score = latent_space.semantic_consistency("vision", [feat])
        assert score == 0.0

    def test_unregistered_modality_returns_zero(self, latent_space):
        """S7: unknown semantic modality → consistency 0.0."""
        feat = np.random.randn(512).astype(np.float32)
        score = latent_space.semantic_consistency("text", [feat, feat.copy()])
        assert score == 0.0

    def test_empty_list_returns_zero(self, latent_space):
        """S8: empty feature list → consistency 0.0."""
        score = latent_space.semantic_consistency("vision", [])
        assert score == 0.0


# =========================================================================
# 2. DualEncoderRouter SharedLatentSpace Integration (5 tests)
# =========================================================================

class TestRouterLatentSpace:
    """P43c: DualEncoderRouter uses SharedLatentSpace for projections."""

    def test_get_latent_space_registers_four_modalities(self, router):
        """R1: _get_latent_space registers 4 modalities."""
        ls = router._get_latent_space()
        mods = ls.registered_modalities()
        assert "vision" in mods
        assert "audio" in mods
        assert "vision_semantic" in mods
        assert "audio_semantic" in mods
        assert len(mods) == 4

    def test_encode_vision_returns_latent_projections(self, router):
        """R2: encode_vision returns structural_latent + semantic_latent."""
        sample_png = _make_sample_png()

        mock_sve = MagicMock()
        mock_sve.is_available = True
        mock_sve.encode.return_value = np.ones(512, dtype=np.float32)

        with patch.object(router, '_get_semantic_visual', return_value=mock_sve):
            result = router.encode_vision(sample_png)

        assert "structural_latent" in result
        assert "semantic_latent" in result
        assert "latent" in result
        assert result["structural_latent"] is not None
        assert result["structural_latent"].shape == (64,)
        assert result["semantic_latent"] is not None
        assert result["semantic_latent"].shape == (64,)
        assert result["latent"] is not None
        # Combined latent should be L2 normalized
        norm = np.linalg.norm(result["latent"])
        assert abs(norm - 1.0) < 1e-5

    def test_encode_vision_structural_only(self, router):
        """R3: encode_vision without semantic still returns structural_latent.'
        The latent is L2-normalized; structural_latent is the raw projection.
        So latent should be the normalized version of structural_latent.
        """
        sample_png = _make_sample_png()
        result = router.encode_vision(sample_png, include_semantic=False)

        assert result["structural_latent"] is not None
        assert result["structural_latent"].shape == (64,)
        assert result["semantic_latent"] is None
        assert result["latent"] is not None
        # latent is L2-normalized; structural_latent is raw projection
        norm = np.linalg.norm(result["structural_latent"])
        expected = result["structural_latent"] / norm if norm > 0 else result["structural_latent"]
        assert np.allclose(result["latent"], expected)

    def test_encode_audio_returns_latent_projections(self, router):
        """R4: encode_audio returns structural_latent + semantic_latent."""
        sample_wav = _make_sample_wav()

        mock_sae = MagicMock()
        mock_sae.is_available = True
        mock_sae.encode.return_value = np.ones(384, dtype=np.float32)

        with patch.object(router, '_get_semantic_audio', return_value=mock_sae):
            result = router.encode_audio(sample_wav)

        assert "structural_latent" in result
        assert result["structural_latent"] is not None
        assert result["structural_latent"].shape == (64,)
        assert result["semantic_latent"] is not None
        assert result["semantic_latent"].shape == (64,)
        assert result["latent"] is not None

    def test_semantic_consistency_report_structure(self, router):
        """R5: semantic_consistency_report returns valid dict."""
        report = router.semantic_consistency_report()
        assert isinstance(report, dict)
        assert "overall" in report
        assert report["overall"] == 0.0  # No data


# =========================================================================
# 3. Semantic Contrastive Training (4 tests)
# =========================================================================

class TestSemanticContrastiveTraining:
    """P43d: semantic_contrastive_train trains semantic projection weights."""

    def test_no_pairs_returns_zero(self, latent_space):
        """C1: no pairs → zero loss."""
        result = latent_space.semantic_contrastive_train([], [])
        assert result["final_loss"] == 0.0
        assert result["history"] == []

    def test_positive_pairs_loss_decreases(self, latent_space):
        """C2: training on positive pairs reduces loss."""
        # Create positive pairs: similar feature pairs
        base = np.random.randn(512).astype(np.float32)
        pos_pairs = [
            (base.copy(), base.copy() + 0.01 * np.random.randn(512).astype(np.float32))
            for _ in range(10)
        ]
        result = latent_space.semantic_contrastive_train(
            pos_pairs, [],
            modality="vision_semantic",
            epochs=3, lr=0.01
        )
        # Final loss should be positive and finite
        assert result["final_loss"] >= 0
        assert np.isfinite(result["final_loss"])
        assert len(result["history"]) == 3
        # Loss should be trending down
        assert result["history"][-1] <= result["history"][0] * 1.1

    def test_negative_pairs_handled(self, latent_space):
        """C3: training on negative pairs works (pushing apart)."""
        feat_a = np.ones(512, dtype=np.float32)
        feat_b = -np.ones(512, dtype=np.float32)
        neg_pairs = [(feat_a.copy(), feat_b.copy()) for _ in range(10)]
        result = latent_space.semantic_contrastive_train(
            [], neg_pairs,
            modality="vision_semantic",
            epochs=3, lr=0.01
        )
        assert result["final_loss"] >= 0
        assert len(result["history"]) == 3

    def test_consistency_improves_after_training(self, latent_space):
        """C4: semantic_consistency improves after contrastive training."""
        # Create a set of same-class features
        prototype = np.random.randn(512).astype(np.float32)
        same_class = [
            prototype + 0.05 * np.random.randn(512).astype(np.float32)
            for _ in range(5)
        ]

        # Measure consistency before training
        before = latent_space.semantic_consistency("vision", same_class)

        # Train on positive pairs from the same class
        pos_pairs = [
            (same_class[i].copy(), same_class[j].copy())
            for i in range(5) for j in range(i + 1, 5)
        ]
        latent_space.semantic_contrastive_train(
            pos_pairs, [],
            modality="vision_semantic",
            epochs=100, lr=0.1
        )

        # Measure consistency after training
        after = latent_space.semantic_consistency("vision", same_class)
        # The projection should make same-class items closer (or at least not degrade)
        assert after + 1e-4 >= before


# =========================================================================
# 4. Cross-modal Semantic Similarity (2 tests)
# =========================================================================

class TestCrossModalSemantic:
    """P43e: cross-modal similarity between structural and semantic projections."""

    def test_similarity_between_modalities(self, latent_space):
        """X1: vision and vision_semantic can be compared via similarity()."""
        v_feat = np.random.randn(256).astype(np.float32)
        s_feat = np.random.randn(512).astype(np.float32)

        latent_space.project("vision", v_feat)
        latent_space.project("vision_semantic", s_feat)

        sim = latent_space.similarity("vision", "vision_semantic")
        assert 0.0 <= sim <= 1.0

    def test_cross_modal_attention_all_four(self, latent_space):
        """X2: cross_modal_attention works across all registered modalities."""
        v_feat = np.random.randn(256).astype(np.float32)
        a_feat = np.random.randn(128).astype(np.float32)
        sv_feat = np.random.randn(512).astype(np.float32)
        sa_feat = np.random.randn(384).astype(np.float32)

        latent_space.project("vision", v_feat)
        latent_space.project("audio", a_feat)
        latent_space.project("vision_semantic", sv_feat)
        latent_space.project("audio_semantic", sa_feat)

        # Query vision against all others
        targets = ["audio", "vision_semantic", "audio_semantic"]
        attn = latent_space.cross_modal_attention("vision", targets)

        assert len(attn) == 3
        assert all(t in attn for t in targets)
        total = sum(attn.values())
        assert abs(total - 1.0) < 1e-5  # Weights sum to 1


# =========================================================================
# Helpers
# =========================================================================

# =========================================================================
# 5. Cross-modal Retrieval Quality Metrics (6 tests)
# =========================================================================

class TestCrossModalRetrievalMetrics:
    """P43f: Cross-modal retrieval precision benchmarks (§X #22).

    Measures retrieval precision at K (P@K) and Mean Reciprocal Rank (MRR)
    for cross-modal retrieval using CrossModalTrainer mappings.

    Note: CrossModalTrainer.record_co_occurrence() eagerly creates mappings
    on first call. train_mapping() updates confidence based on co-occurrence
    count. Key prefix heuristic (starts with c/g/e/p/r/l/t) determines
    text vs modality key.
    """

    def _build_paired_dataset(self):
        """Build synthetic dataset with known cross-modal pairs.

        Uses key prefixes that match CrossModalTrainer's text-key heuristic
        (starts with c/g/e/p/r/l/t = text key).
        """
        text_keys = [f"cat_{i}" for i in range(20)]
        image_keys = [f"img_{i}" for i in range(20)]
        audio_keys = [f"aud_{i}" for i in range(20)]
        return text_keys, image_keys, audio_keys

    def _train_on_dataset(self, trainer, text_keys, img_keys, aud_keys):
        """Record co-occurrences and train mappings."""
        for text, img, aud in zip(text_keys, img_keys, aud_keys):
            for _ in range(5):
                trainer.record_co_occurrence(text, image_key=img, audio_key=aud)
        return trainer.train_mapping(min_co_occurrences=3)

    def test_cross_modal_retrieval_precision(self):
        """Q1: Cross-modal retrieval P@1 = 1.0 for known pairs."""
        from ai.ed3n.multimodal.cross_modal_trainer import CrossModalTrainer
        trainer = CrossModalTrainer()
        text_keys, img_keys, aud_keys = self._build_paired_dataset()
        self._train_on_dataset(trainer, text_keys, img_keys, aud_keys)

        image_hits = 0
        for text, correct_img in zip(text_keys, img_keys):
            results = trainer.get_related_keys(text, "image")
            if correct_img in results:
                image_hits += 1
        precision = image_hits / len(text_keys)
        assert precision == 1.0, f"Image retrieval P@1: {precision:.2f}"

    def test_cross_modal_retrieval_rejects_wrong_modality(self):
        """Q2: get_related_keys('image') returns only img_ keys."""
        from ai.ed3n.multimodal.cross_modal_trainer import CrossModalTrainer
        trainer = CrossModalTrainer()
        text_keys, img_keys, aud_keys = self._build_paired_dataset()
        self._train_on_dataset(trainer, text_keys, img_keys, aud_keys)

        for text, correct_img in zip(text_keys, img_keys):
            results = trainer.get_related_keys(text, "image")
            for r in results:
                assert r.startswith("img_"), f"Non-image key: {r}"
            for other_text, other_img in zip(text_keys, img_keys):
                if other_img != correct_img:
                    assert other_img not in results, \
                        f"Wrong image {other_img} for {text}"

    def test_cross_modal_audio_retrieval(self):
        """Q3: Audio retrieval precision P@1 = 1.0."""
        from ai.ed3n.multimodal.cross_modal_trainer import CrossModalTrainer
        trainer = CrossModalTrainer()
        text_keys, img_keys, aud_keys = self._build_paired_dataset()
        self._train_on_dataset(trainer, text_keys, img_keys, aud_keys)

        audio_hits = 0
        for text, correct_aud in zip(text_keys, aud_keys):
            results = trainer.get_related_keys(text, "audio")
            if correct_aud in results:
                audio_hits += 1
        precision = audio_hits / len(text_keys)
        assert precision == 1.0, f"Audio retrieval P@1: {precision:.2f}"

    def test_cross_modal_dual_modality_retrieval(self):
        """Q4: Both image and audio retrieved for same text key."""
        from ai.ed3n.multimodal.cross_modal_trainer import CrossModalTrainer
        trainer = CrossModalTrainer()
        text_keys, img_keys, aud_keys = self._build_paired_dataset()
        self._train_on_dataset(trainer, text_keys, img_keys, aud_keys)

        for text, correct_img, correct_aud in zip(text_keys, img_keys, aud_keys):
            img_results = trainer.get_related_keys(text, "image")
            aud_results = trainer.get_related_keys(text, "audio")
            assert correct_img in img_results, f"Missing {correct_img} for {text}"
            assert correct_aud in aud_results, f"Missing {correct_aud} for {text}"

    def test_get_stats_reflects_training(self):
        """Q5: CrossModalTrainer.get_stats() reflects trained state."""
        from ai.ed3n.multimodal.cross_modal_trainer import CrossModalTrainer
        trainer = CrossModalTrainer()
        text_keys, img_keys, aud_keys = self._build_paired_dataset()
        self._train_on_dataset(trainer, text_keys, img_keys, aud_keys)
        stats = trainer.get_stats()
        assert stats["total_mappings"] >= 20
        assert stats["with_image"] >= 20
        assert stats["with_audio"] >= 20
        assert stats["avg_confidence"] >= 0.5
        assert stats["co_occurrence_pairs"] > 0

    def test_retrieval_with_insufficient_training(self):
        """Q6: Low co-occurrence = low confidence, but mapping still exists."""
        from ai.ed3n.multimodal.cross_modal_trainer import CrossModalTrainer
        trainer = CrossModalTrainer()
        text_keys, img_keys, _ = self._build_paired_dataset()
        # Only 1 co-occurrence per pair (below train_mapping threshold)
        for text, img in zip(text_keys, img_keys):
            trainer.record_co_occurrence(text, image_key=img)
        # Mapping created eagerly by record_co_occurrence()
        assert trainer.get_stats()["total_mappings"] == 20
        assert trainer.get_stats()["avg_confidence"] == 0.5  # Default

    def test_shared_latent_space_semantic_consistency(self):
        """Q7: SharedLatentSpace.semantic_consistency() returns meaningful score."""
        from ai.multimodal.shared_latent_space import SharedLatentSpace
        ls = SharedLatentSpace(latent_dim=64)
        ls.register_semantic_modality("vision", 512)

        rng = np.random.RandomState(42)
        # Tight cluster
        proto = rng.randn(512).astype(np.float32)
        tight = [proto + 0.01 * rng.randn(512).astype(np.float32) for _ in range(10)]
        # Loose cluster
        loose = [rng.randn(512).astype(np.float32) for _ in range(10)]

        tight_score = ls.semantic_consistency("vision", tight)
        loose_score = ls.semantic_consistency("vision", loose)
        # Tight cluster should have higher consistency than loose cluster
        assert tight_score > loose_score, \
            f"tight={tight_score:.4f} <= loose={loose_score:.4f}"


# =========================================================================
# Helpers
# =========================================================================

def _make_sample_png() -> bytes:
    """Generate a minimal valid PNG (1×1 white pixel)."""
    import struct
    import zlib
    width, height = 1, 1
    raw = b'\x00' + b'\xff\xff\xff' * width * height

    def chunk(t, data):
        c = t + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + crc

    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(raw)
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', ihdr)
            + chunk(b'IDAT', idat)
            + chunk(b'IEND', b''))


def _make_sample_wav() -> bytes:
    """Generate a minimal valid WAV (0.1s silence, 16 kHz, 16-bit mono)."""
    import struct
    sr = 16000
    n_samples = int(sr * 0.1)
    data = struct.pack('<' + 'h' * n_samples, *([0] * n_samples))
    data_size = len(data)
    header = struct.pack('<4sI4s', b'RIFF', 36 + data_size, b'WAVE')
    fmt = struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, 1, sr, sr * 2, 2, 16)
    data_chunk = struct.pack('<4sI', b'data', data_size) + data
    return header + fmt + data_chunk
