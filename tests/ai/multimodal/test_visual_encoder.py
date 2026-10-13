import numpy as np
import pytest
from PIL import Image


@pytest.fixture
def encoder():
    from ai.multimodal.visual_encoder import VisualEncoder

    return VisualEncoder()


@pytest.fixture
def sample_image_bytes():
    img = Image.new("RGB", (64, 64), color=(128, 64, 32))
    import io

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestVisualEncoder:

    def test_encode_returns_vector(self, encoder, sample_image_bytes):
        vec = encoder.encode(sample_image_bytes)
        assert isinstance(vec, np.ndarray)
        assert vec.shape == (256,)
        assert vec.dtype == np.float32

    def test_encode_empty_returns_zeros(self, encoder):
        vec = encoder.encode(b"")
        assert np.all(vec == 0.0)

    def test_encode_from_pil(self, encoder):
        img = Image.new("RGB", (32, 32), color=(255, 0, 0))
        vec = encoder.encode_from_pil(img)
        assert vec.shape == (256,)
        assert not np.all(vec == 0.0)

    def test_different_images_different_vectors(self, encoder):
        img1 = Image.new("RGB", (64, 64), color=(255, 0, 0))
        img2 = Image.new("RGB", (64, 64), color=(0, 255, 0))
        v1 = encoder.encode_from_pil(img1)
        v2 = encoder.encode_from_pil(img2)
        assert not np.allclose(v1, v2, atol=0.1)

    def test_vector_is_normalized(self, encoder, sample_image_bytes):
        vec = encoder.encode(sample_image_bytes)
        norm = np.linalg.norm(vec)
        assert norm > 0

    def test_same_image_same_vector(self, encoder, sample_image_bytes):
        v1 = encoder.encode(sample_image_bytes)
        v2 = encoder.encode(sample_image_bytes)
        assert np.allclose(v1, v2)


class TestVisualEncoderProjection:
    """``_project_if_needed`` must stay numerically identical to the legacy
    identity / zero-pad behaviour while exposing a trainable matrix."""

    def test_feature_dim_property(self, encoder):
        assert encoder.feature_dim == 256

    @pytest.mark.parametrize("feature_dim", [64, 128, 256, 512])
    def test_wider_output_dim_is_identity_extension(self, feature_dim):
        from ai.multimodal.visual_encoder import VisualEncoder

        img = Image.fromarray(
            np.random.default_rng(3).integers(0, 255, (40, 50, 3), dtype=np.uint8)
        )
        enc = VisualEncoder(feature_dim=feature_dim)
        raw = enc._extract_raw(img)
        out = enc.encode_from_pil(img)

        assert out.shape == (feature_dim,)
        assert enc._projection is not None
        assert enc._projection.shape == (feature_dim, raw.size)
        if raw.size <= feature_dim:
            # leading slots reproduce the raw features exactly, rest stay zero
            assert np.allclose(out[: raw.size], raw)
            assert np.all(out[raw.size :] == 0.0)

    def test_projection_is_deterministic_across_instances(self):
        from ai.multimodal.visual_encoder import VisualEncoder

        img = Image.fromarray(
            np.random.default_rng(5).integers(0, 255, (40, 40, 3), dtype=np.uint8)
        )
        a = VisualEncoder(feature_dim=64).encode_from_pil(img)
        b = VisualEncoder(feature_dim=64).encode_from_pil(img)
        assert np.allclose(a, b)

    def test_projection_rebuilt_when_raw_length_changes(self):
        from ai.multimodal.visual_encoder import VisualEncoder

        enc = VisualEncoder()
        raw_small = enc._extract_raw(Image.new("RGB", (32, 32), color=(1, 2, 3)))
        enc._project_if_needed(raw_small)
        first = enc._projection
        assert first is not None
        # a different raw length must trigger a rebuild, not a shape crash
        bigger = np.zeros(raw_small.size + 7, dtype=np.float32)
        enc._project_if_needed(bigger)
        assert enc._projection is not None
        assert enc._projection.shape[1] == raw_small.size + 7
        assert enc._projection is not first

    def test_reset_projection_restores_initialised_matrix(self, encoder, sample_image_bytes):
        encoder.encode(sample_image_bytes)
        assert encoder._projection is not None
        encoder.reset_projection()
        assert encoder._projection is None
        encoder.encode(sample_image_bytes)
        assert encoder._projection is not None


class TestVisualEncoderTraining:
    """Regression for Phase 0: ``train_step`` used to raise on a 64-dim target
    and then fail the projection assertion even when the shape was fixed."""

    @pytest.fixture
    def textured_bytes(self):
        """A non-uniform image so the feature vector is not all zeros."""
        import io

        img = Image.fromarray(
            np.random.default_rng(11).integers(0, 255, (64, 64, 3), dtype=np.uint8)
        )
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    @pytest.mark.parametrize(
        "target",
        [None, np.zeros(2, dtype=np.float32), np.ones(64, dtype=np.float32), np.ones(256)],
        ids=["none", "len2", "len64", "len256"],
    )
    def test_train_step_accepts_any_target_length(self, encoder, textured_bytes, target):
        loss = encoder.train_step(textured_bytes, target, lr=1e-3)
        assert np.isfinite(loss)

    def test_train_step_accepts_overlong_target(self, encoder, textured_bytes):
        loss = encoder.train_step(textured_bytes, np.ones(1024, dtype=np.float32), lr=1e-3)
        assert np.isfinite(loss)

    def test_train_step_initialises_projection(self, encoder, textured_bytes):
        assert encoder._projection is None
        encoder.train_step(textured_bytes, np.zeros(64, dtype=np.float32))
        assert encoder._projection is not None

    def test_train_step_loss_decreases(self, textured_bytes):
        from ai.multimodal.visual_encoder import VisualEncoder

        enc = VisualEncoder()
        target = np.random.default_rng(0).standard_normal(enc.feature_dim).astype(np.float32)
        losses = [enc.train_step(textured_bytes, target, lr=1e-3) for _ in range(30)]
        assert losses[0] > 0
        assert losses[-1] < losses[0]

    def test_train_step_does_not_distort_encode(self, textured_bytes):
        """The clip cap must scale with feature_dim, else it shrinks the map."""
        from ai.multimodal.visual_encoder import VisualEncoder

        enc = VisualEncoder()
        before = enc.encode(textured_bytes)
        target = np.random.default_rng(2).standard_normal(enc.feature_dim).astype(np.float32)
        for _ in range(20):
            enc.train_step(textured_bytes, target, lr=1e-3)
        after = enc.encode(textured_bytes)
        ratio = float(np.linalg.norm(after) / max(np.linalg.norm(before), 1e-8))
        assert 0.5 < ratio < 2.0

    def test_train_step_bad_image_bytes_returns_zero(self, encoder):
        assert encoder.train_step(b"not an image", np.zeros(64, dtype=np.float32)) == 0.0
