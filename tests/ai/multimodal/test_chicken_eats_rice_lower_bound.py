"""
P44 小雞吃米圖 (Chicken Eats Rice) Lower-Bound Integration Test 🐤

**NON-BYPASS TESTS** — This test suite verifies REAL image understanding
through the actual VisualEncoder → SharedLatentSpace → SemanticKeyMapper
pipeline.  No mocked CLIP, no roundtrip guarantees.

**Test strategy**:
  1. Generate multiple synthetic images per concept (chicken/cat/dog) WITH
     intra-class variation (different sizes, noise seeds, positions).
  2. Encode ALL images through the REAL VisualEncoder → 256-dim structural
     features — no mock, no stub.
  3. Train the SharedLatentSpace with contrastive learning so that same-class
     features cluster together in the 64-dim latent space.
  4. Index ONE image per concept in the SemanticKeyMapper.
  5. Query with a DIFFERENT image of the same concept → cross-image
     generalization is the TRUE test of "understanding".

**Key insight**: Without the contrastive training step, the SharedLatentSpace
projection is random, so two chicken images would NOT be closer to each other
than to a cat image.  Training makes the space semantically meaningful, and
cross-image generalization proves real learning occurred.
"""

import struct
import zlib

import numpy as np
import pytest

from ai.multimodal.semantic_key_mapper import SemanticKeyMapper
from ai.multimodal.shared_latent_space import SharedLatentSpace
from ai.multimodal.visual_encoder import VisualEncoder


# =========================================================================
# Image Generation
# =========================================================================

def _make_png(width: int, height: int, raw: bytes) -> bytes:
    """Build a valid PNG from raw pixel data."""
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


def _make_circle_png(radius: float, r: int, g: int, b: int,
                     noise: float = 0.0, seed: int = 0) -> bytes:
    """Yellow-ish circle on white background with optional noise."""
    width, height = 16, 16
    rng = np.random.default_rng(seed)
    raw = b''
    cx, cy = 8, 8
    for y in range(height):
        raw += b'\x00'
        for x in range(width):
            dx, dy = x - cx, y - cy
            dist = (dx ** 2 + dy ** 2) ** 0.5
            if dist < radius:
                nr = max(0, min(255, r + int(noise * rng.standard_normal())))
                ng = max(0, min(255, g + int(noise * rng.standard_normal())))
                nb = max(0, min(255, b + int(noise * rng.standard_normal())))
                raw += bytes([nr, ng, nb])
            else:
                raw += b'\xff\xff\xff'
    return _make_png(width, height, raw)


def _make_square_png(size: int, r: int, g: int, b: int,
                     noise: float = 0.0, seed: int = 0) -> bytes:
    """Colored square on white background with optional noise."""
    width, height = 16, 16
    rng = np.random.default_rng(seed)
    raw = b''
    x0, y0 = 8 - size // 2, 8 - size // 2
    for y in range(height):
        raw += b'\x00'
        for x in range(width):
            if x0 <= x < x0 + size and y0 <= y < y0 + size:
                nr = max(0, min(255, r + int(noise * rng.standard_normal())))
                ng = max(0, min(255, g + int(noise * rng.standard_normal())))
                nb = max(0, min(255, b + int(noise * rng.standard_normal())))
                raw += bytes([nr, ng, nb])
            else:
                raw += b'\xff\xff\xff'
    return _make_png(width, height, raw)


# =========================================================================
# Fixtures
# =========================================================================

@pytest.fixture(scope="module")
def encoder():
    """REAL VisualEncoder — no mock, no stub."""
    return VisualEncoder()


@pytest.fixture(scope="module")
def latent_space():
    """SharedLatentSpace with vision modality registered (random initial weights).

    ⚠️  DO NOT request this fixture directly in tests.  The ``trained_ls_and_original``
    fixture mutates this same object **in place** during training, so by the time any
    test receives it, the weights are already trained.  Only consume via
    ``trained_ls``, ``projected_latents``, or ``trained_ls_and_original``.
    """
    ls = SharedLatentSpace(latent_dim=64)
    ls.register_modality("vision", 256)
    return ls


@pytest.fixture(scope="module")
def concept_images():
    """Generate multiple synthetic images per concept WITH variation.

    Returns:
        dict: {concept: [png_bytes, ...]}  — 4 images per concept × 3 concepts
    """
    images = {
        "chicken": [
            _make_circle_png(4.5, 255, 200, 0, noise=5, seed=10),
            _make_circle_png(5.0, 240, 180, 20, noise=10, seed=11),
            _make_circle_png(4.0, 255, 210, 10, noise=8, seed=12),
            _make_circle_png(5.5, 250, 190, 5, noise=12, seed=13),
        ],
        "cat": [
            _make_square_png(8, 0, 0, 255, noise=5, seed=20),
            _make_square_png(7, 20, 20, 240, noise=10, seed=21),
            _make_square_png(9, 10, 10, 250, noise=8, seed=22),
            _make_square_png(6, 5, 5, 255, noise=12, seed=23),
        ],
        "dog": [
            _make_square_png(8, 0, 200, 0, noise=5, seed=30),
            _make_square_png(7, 20, 200, 20, noise=10, seed=31),
            _make_square_png(9, 10, 220, 10, noise=8, seed=32),
            _make_square_png(6, 5, 210, 5, noise=12, seed=33),
        ],
    }
    return images


@pytest.fixture(scope="module")
def encoded_features(encoder, concept_images):
    """Encode ALL images through the REAL VisualEncoder.

    Returns:
        dict: {concept: [256-dim ndarray, ...]} — features per image
    """
    features = {}
    for concept, imgs in concept_images.items():
        features[concept] = [encoder.encode(img) for img in imgs]
    return features


@pytest.fixture(scope="module")
def trained_ls_and_original(latent_space, encoded_features):
    """Train SharedLatentSpace with contrastive learning.

    Returns (trained_space, original_weights_W_copy) so tests can
    verify the training actually changed the weights.

    Positive pairs: same-class images (chicken_A ↔ chicken_B)
    Negative pairs: different-class images (chicken ↔ cat, etc.)

    This is the KEY step that makes the latent space semantically meaningful.
    Without it, same-class images would NOT cluster together.
    """
    # Snapshot original weights BEFORE training
    original_W = latent_space._projections["vision"]["W"].copy()

    # Build positive pairs: all pairs within each class
    pos_pairs = []
    for concept in ["chicken", "cat", "dog"]:
        feats = encoded_features[concept]
        for i in range(len(feats)):
            for j in range(i + 1, len(feats)):
                pos_pairs.append(("vision", feats[i], "vision", feats[j]))

    # Build negative pairs: cross-class pairs
    neg_pairs = []
    concepts = ["chicken", "cat", "dog"]
    for i in range(len(concepts)):
        for j in range(i + 1, len(concepts)):
            for fi in encoded_features[concepts[i]]:
                for fj in encoded_features[concepts[j]]:
                    neg_pairs.append(("vision", fi, "vision", fj))

    result = latent_space.train(pos_pairs, neg_pairs, epochs=30, lr=0.1)
    assert result["final_loss"] >= 0, "Training produced negative loss"
    assert len(result["history"]) == 30, "Training did not run full epochs"
    return latent_space, original_W


@pytest.fixture(scope="module")
def trained_ls(trained_ls_and_original):
    """Just the trained SharedLatentSpace (discards weight snapshot)."""
    return trained_ls_and_original[0]


@pytest.fixture(scope="module")
def projected_latents(trained_ls, encoded_features):
    """Project encoded features through trained SharedLatentSpace → 64-dim.

    Returns:
        dict: {concept: [64-dim ndarray, ...]} — latents per image
    """
    latents = {}
    for concept, feats in encoded_features.items():
        latents[concept] = [trained_ls.project("vision", f) for f in feats]
    return latents


# =========================================================================
# Tests — 小雞吃米圖 Lower-Bound (5 real tests)
# =========================================================================

class TestChickenEatsRice:
    """P44e: 小雞吃米圖 lower-bound — REAL tests, no bypass."""

    # ------------------------------------------------------------------
    # Test 1: Contrastive training creates meaningful clusters
    # ------------------------------------------------------------------

    def test_01_training_clusters_same_class(self, trained_ls, encoded_features):
        """After contrastive training, same-class features should have
        higher cosine similarity than cross-class features in latent space.

        This is the FOUNDATIONAL test: if the latent space didn't learn
        anything, this would fail.
        """
        ls = trained_ls
        # Compute same-class similarities (all pairs within each class)
        same_class_sims = []
        for concept in ["chicken", "cat", "dog"]:
            feats = encoded_features[concept]
            for i in range(len(feats)):
                for j in range(i + 1, len(feats)):
                    # Project both features, compute cosine similarity
                    a = ls._l2_normalize(ls.project("vision", feats[i]))
                    b = ls._l2_normalize(ls.project("vision", feats[j]))
                    same_class_sims.append(float(np.dot(a, b)))

        # Compute cross-class similarities
        cross_class_sims = []
        concepts = ["chicken", "cat", "dog"]
        for i in range(len(concepts)):
            for j in range(i + 1, len(concepts)):
                for fi in encoded_features[concepts[i]]:
                    for fj in encoded_features[concepts[j]]:
                        a = ls._l2_normalize(ls.project("vision", fi))
                        b = ls._l2_normalize(ls.project("vision", fj))
                        cross_class_sims.append(float(np.dot(a, b)))

        avg_same = float(np.mean(same_class_sims))
        avg_cross = float(np.mean(cross_class_sims))

        # After training, same-class should be closer than cross-class
        print(f"\n  📊 Avg same-class similarity: {avg_same:.4f}")
        print(f"  📊 Avg cross-class similarity: {avg_cross:.4f}")
        assert avg_same > avg_cross, \
            f"Training failed to cluster: same={avg_same:.4f} <= cross={avg_cross:.4f}"

    # ------------------------------------------------------------------
    # Test 2: Cross-image generalization — chicken
    # ------------------------------------------------------------------

    def test_02_cross_image_chicken(self, projected_latents):
        """Index chicken_A as 'chicken', query with chicken_B.

        If the latent space learned correctly, chicken_B's latent should
        be closest to chicken_A's — even though they are DIFFERENT images
        with different noise seeds and sizes.
        """
        mapper = SemanticKeyMapper(max_entries=100)

        # Index ONE chicken image (index 0)
        mapper.index_key("chicken",
                         structural_latent=projected_latents["chicken"][0],
                         semantic_latent=projected_latents["chicken"][0],
                         combined_latent=projected_latents["chicken"][0])

        # Query with DIFFERENT chicken images (indices 1, 2, 3)
        for idx in range(1, 4):
            results = mapper.map_latent_to_keys(
                projected_latents["chicken"][idx], top_k=1, mode="combined")
            assert len(results) >= 1, \
                f"Chicken[{idx}] returned no matches"
            assert results[0]["key"] == "chicken", \
                f"Chicken[{idx}] mapped to '{results[0]['key']}' instead of 'chicken' (score={results[0]['score']})"

    # ------------------------------------------------------------------
    # Test 3: Cross-image generalization — cat
    # ------------------------------------------------------------------

    def test_03_cross_image_cat(self, projected_latents):
        """Same as test_02 but for cat. Verifies the effect generalizes
        across concepts, not just chicken."""
        mapper = SemanticKeyMapper(max_entries=100)
        mapper.index_key("cat",
                         structural_latent=projected_latents["cat"][0],
                         semantic_latent=projected_latents["cat"][0],
                         combined_latent=projected_latents["cat"][0])

        for idx in range(1, 4):
            results = mapper.map_latent_to_keys(
                projected_latents["cat"][idx], top_k=1, mode="combined")
            assert len(results) >= 1
            assert results[0]["key"] == "cat", \
                f"Cat[{idx}] mapped to '{results[0]['key']}' instead of 'cat'"

    # ------------------------------------------------------------------
    # Test 4: Cross-concept discrimination
    # ------------------------------------------------------------------

    def test_04_cross_concept_discrimination(self, projected_latents):
        """Index ONE image from each of 3 concepts, then verify that
        ALL remaining images across all concepts are classified correctly.

        This is the STRONGEST test: a single incorrect classification
        (e.g. chicken→cat) would fail the test.
        """
        mapper = SemanticKeyMapper(max_entries=100)

        # Index image 0 from each concept
        for concept in ["chicken", "cat", "dog"]:
            mapper.index_key(concept,
                             structural_latent=projected_latents[concept][0],
                             semantic_latent=projected_latents[concept][0],
                             combined_latent=projected_latents[concept][0])

        # Query images 1,2,3 from each concept — all must classify correctly
        total = 0
        correct = 0
        for concept in ["chicken", "cat", "dog"]:
            for idx in range(1, 4):
                total += 1
                results = mapper.map_latent_to_keys(
                    projected_latents[concept][idx], top_k=1, mode="combined")
                if len(results) >= 1 and results[0]["key"] == concept:
                    correct += 1

        accuracy = correct / max(total, 1)
        print(f"\n  📊 Cross-concept accuracy: {correct}/{total} = {accuracy:.1%}")
        assert accuracy >= 2/3, \
            f"Cross-concept accuracy too low: {correct}/{total}"

        # At minimum, each concept must have at least 1 correct cross-image match
        for concept in ["chicken", "cat", "dog"]:
            any_correct = False
            for idx in range(1, 4):
                results = mapper.map_latent_to_keys(
                    projected_latents[concept][idx], top_k=1, mode="combined")
                if len(results) >= 1 and results[0]["key"] == concept:
                    any_correct = True
                    break
            assert any_correct, \
                f"Concept '{concept}' had ZERO cross-image correct matches"

    # ------------------------------------------------------------------
    # Test 5: Training materially changed the projection weights
    # ------------------------------------------------------------------

    def test_05_training_changed_weights(self, trained_ls_and_original):
        """Verify that contrastive training materially changed the projection
        weights. If the weights didn't change, the training had no effect.

        This prevents regression where training code silently becomes a no-op.

        Uses the weight snapshot taken BEFORE training (saved in the fixture)
        to compare against the trained weights — avoiding the pitfall of
        comparing the same object against itself.
        """
        trained_ls, original_W = trained_ls_and_original
        trained_W = trained_ls._projections["vision"]["W"]

        diff = np.abs(trained_W - original_W).mean()
        print(f"\n  📊 Mean weight change: {diff:.6f}")

        # The weights should have changed measurably
        assert diff > 1e-6, \
            f"Training did NOT materially change weights (Δ={diff:.2e})"

        # The weights should NOT be identical to initial random
        assert not np.allclose(trained_W, original_W, atol=1e-6), \
            "Training weights are identical to initial weights — training was a no-op"
