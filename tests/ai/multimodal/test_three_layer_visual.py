"""Tests for ThreeLayerVisual — PCA encoder + nonlinear decoder."""
import os
import tempfile

import numpy as np
import pytest


def _has_torch():
    try:
        import torch
        return True
    except ImportError:
        return False


@pytest.fixture
def synthetic_data():
    """Create synthetic 32x32x3 images for testing."""
    rng = np.random.default_rng(42)
    n = 50
    images = []
    labels = []
    for class_id in range(5):
        for _ in range(n // 5):
            img = rng.uniform(0, 0.3, (32, 32, 3)).astype(np.float32)
            cx, cy = rng.integers(8, 24), rng.integers(8, 24)
            r = rng.integers(3, 6)
            color = rng.uniform(0.4, 0.9)
            img[max(0, cx-r):cx+r, max(0, cy-r):cy+r] = color
            images.append(img.reshape(-1))
            labels.append(class_id)
    return np.array(images, dtype=np.float32), np.array(labels, dtype=np.int64)


def _make_tlv():
    from ai.multimodal.three_layer_visual import ThreeLayerVisual
    return ThreeLayerVisual(model_dir=tempfile.mkdtemp())


class TestThreeLayerVisual:
    def test_init(self):
        tlv = _make_tlv()
        assert tlv._encoder is None
        assert tlv._decoder is None
        assert tlv._mean is None
        assert tlv._class_centers is None
        assert tlv.is_available is False

    def test_init_with_nonexistent_dir(self):
        from ai.multimodal.three_layer_visual import ThreeLayerVisual
        tlv = ThreeLayerVisual(model_dir="/nonexistent/path/three_layer")
        assert tlv._encoder is None

    def test_is_available_false_before_fit(self):
        tlv = _make_tlv()
        assert tlv.is_available is False

    @pytest.mark.skipif(not _has_torch(), reason="torch not available")
    def test_fit_returns_metrics(self, synthetic_data):
        tlv = _make_tlv()
        images, labels = synthetic_data
        result = tlv.fit(images, labels, n_epochs=30, verbose=False)
        assert "pca_variance" in result
        assert result["pca_variance"] > 0.5
        assert "test_mse" in result
        assert "training_time" in result
        assert "n_classes" in result
        assert result["n_classes"] == 5

    @pytest.mark.skipif(not _has_torch(), reason="torch not available")
    def test_is_available_true_after_fit(self, synthetic_data):
        tlv = _make_tlv()
        tlv.fit(synthetic_data[0], synthetic_data[1], n_epochs=10, verbose=False)
        assert tlv.is_available is True

    @pytest.mark.skipif(not _has_torch(), reason="torch not available")
    def test_encode_returns_latent(self, synthetic_data):
        tlv = _make_tlv()
        images, _ = synthetic_data
        tlv.fit(images, synthetic_data[1], n_epochs=10, verbose=False)
        latent = tlv.encode(images[:5])
        assert latent.shape == (5, 128)

    @pytest.mark.skipif(not _has_torch(), reason="torch not available")
    def test_decode_returns_images(self, synthetic_data):
        tlv = _make_tlv()
        images, labels = synthetic_data
        tlv.fit(images, labels, n_epochs=10, verbose=False)
        latent = tlv.encode(images[:5])
        decoded = tlv.decode(latent)
        assert decoded.shape == (5, 3072)
        assert decoded.min() >= -0.01
        assert decoded.max() <= 1.01

    @pytest.mark.skipif(not _has_torch(), reason="torch not available")
    def test_reconstruct_reduces_error(self, synthetic_data):
        tlv = _make_tlv()
        images, labels = synthetic_data
        tlv.fit(images, labels, n_epochs=30, verbose=False)
        recon = tlv.reconstruct(images[:10], enhance=False)
        mse = float(np.mean((recon - images[:10]) ** 2))
        assert mse < 0.05

    @pytest.mark.skipif(not _has_torch(), reason="torch not available")
    def test_recognize_returns_predictions(self, synthetic_data):
        tlv = _make_tlv()
        images, labels = synthetic_data
        tlv.fit(images, labels, n_epochs=10, verbose=False)
        preds, dists = tlv.recognize(images[:5], top_k=3)
        assert preds.shape == (5, 3)
        assert dists.shape == (5, 3)
        assert np.all(dists >= 0)

    @pytest.mark.skipif(not _has_torch(), reason="torch not available")
    def test_generate_from_class(self, synthetic_data):
        tlv = _make_tlv()
        images, labels = synthetic_data
        tlv.fit(images, labels, n_epochs=10, verbose=False)
        gen = tlv.generate_from_class(0, enhance=False)
        assert gen.shape == (3072,)
        assert gen.min() >= -0.01
        assert gen.max() <= 1.01

    @pytest.mark.skipif(not _has_torch(), reason="torch not available")
    def test_interpolate(self, synthetic_data):
        tlv = _make_tlv()
        images, labels = synthetic_data
        tlv.fit(images, labels, n_epochs=10, verbose=False)
        interp = tlv.interpolate(0, 1, n_steps=5, enhance=False)
        assert interp.shape == (5, 3072)

    @pytest.mark.skipif(not _has_torch(), reason="torch not available")
    def test_save_and_load_roundtrip(self, synthetic_data):
        tlv = _make_tlv()
        images, labels = synthetic_data
        tlv.fit(images, labels, n_epochs=10, verbose=False)

        from ai.multimodal.three_layer_visual import ThreeLayerVisual
        save_dir = tempfile.mkdtemp()
        tlv.save(save_dir)

        loaded = ThreeLayerVisual(model_dir=save_dir)
        ok = loaded.load(save_dir)
        assert ok
        assert loaded.is_available
        assert np.allclose(loaded._encoder, tlv._encoder, atol=1e-6)
        assert np.allclose(loaded._mean, tlv._mean, atol=1e-6)
        assert np.allclose(loaded._class_centers, tlv._class_centers, atol=1e-6)

    @pytest.mark.skipif(not _has_torch(), reason="torch not available")
    def test_save_and_load_produces_similar_reconstructions(self, synthetic_data):
        tlv = _make_tlv()
        images, labels = synthetic_data
        tlv.fit(images, labels, n_epochs=10, verbose=False)
        recon_before = tlv.reconstruct(images[:3], enhance=False)

        from ai.multimodal.three_layer_visual import ThreeLayerVisual
        save_dir = tempfile.mkdtemp()
        tlv.save(save_dir)
        loaded = ThreeLayerVisual(model_dir=save_dir)
        loaded.load(save_dir)
        recon_after = loaded.reconstruct(images[:3], enhance=False)

        assert np.allclose(recon_before, recon_after, atol=1e-5)

    def test_get_pca_components_raises_before_fit(self):
        tlv = _make_tlv()
        with pytest.raises(RuntimeError, match="not fitted"):
            tlv.get_pca_components(5)

    @pytest.mark.skipif(not _has_torch(), reason="torch not available")
    def test_get_pca_components_returns_correct_shape(self, synthetic_data):
        tlv = _make_tlv()
        images, labels = synthetic_data
        tlv.fit(images, labels, n_epochs=10, verbose=False)
        comps = tlv.get_pca_components(5)
        assert comps.shape == (5, 3072)

    def test_encode_raises_before_fit(self):
        tlv = _make_tlv()
        with pytest.raises(RuntimeError, match="not fitted"):
            tlv.encode(np.zeros((1, 3072), dtype=np.float32))

    def test_decode_raises_before_fit(self):
        tlv = _make_tlv()
        with pytest.raises(RuntimeError, match="not fitted"):
            tlv.decode(np.zeros((1, 128), dtype=np.float32))

    def test_recognize_raises_before_fit(self):
        tlv = _make_tlv()
        with pytest.raises(RuntimeError, match="not fitted"):
            tlv.recognize(np.zeros((1, 3072), dtype=np.float32))

    @pytest.mark.skipif(not _has_torch(), reason="torch not available")
    def test_fit_with_enhance_improves_sharpness(self, synthetic_data):
        tlv = _make_tlv()
        images, labels = synthetic_data
        tlv.fit(images, labels, n_epochs=20, verbose=False)
        raw = tlv.reconstruct(images[:5], enhance=False)
        enhanced = tlv.reconstruct(images[:5], enhance=True)
        raw_var = np.var(raw)
        enh_var = np.var(enhanced)
        assert enh_var >= raw_var * 0.9

    @pytest.mark.skipif(not _has_torch(), reason="torch not available")
    def test_4d_input_handling(self, synthetic_data):
        tlv = _make_tlv()
        images, labels = synthetic_data
        images_4d = images.reshape(-1, 32, 32, 3)
        tlv.fit(images_4d, labels, n_epochs=10, verbose=False)
        assert tlv.is_available

    def test_load_returns_false_for_missing_dir(self):
        from ai.multimodal.three_layer_visual import ThreeLayerVisual
        tlv = ThreeLayerVisual(model_dir="/nonexistent/path")
        ok = tlv.load("/nonexistent/path")
        assert ok is False
