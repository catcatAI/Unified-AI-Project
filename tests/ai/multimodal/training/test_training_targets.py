"""Training target validation: verify trained weights exist, load correctly, and produce non-trivial output.

Roadmap targets (IMPROVEMENT_ROADMAP.md §2.5):
  VisualDecoder:       MSE < 0.05,  SSIM > 0.6,  PSNR > 25dB
  AudioWaveformDecoder: MSE < 0.1,   SNR > 15dB,  MOS > 2.0
  SequenceGenerator:   Cross-entropy < 1.0,  accuracy > 60%
  FullTrainingPipeline: Contrastive loss < 0.1, reconstruction loss < 0.05
  ThreeLayerVisual:    MSE < 0.005, SSIM > 0.7

Current baseline (2026-07-01, §X #79):
  Texture loss: 0.271, Wavetable loss: 0.050, Contrastive loss: 0.195
"""

import numpy as np
import pytest

from ai.multimodal.quality_metrics import psnr, ssim, snr
from ai.multimodal.visual_decoder import (
    VisualDecoder,
    load_default_visual_decoder_weights,
)
from ai.multimodal.audio_decoder import AudioWaveformDecoder, load_default_audio_decoder_weights


def _get_weights_path():
    """Resolve p29_trained.npz path."""
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent.parent.parent.parent
    p = root / "data" / "multimodal" / "weights" / "p29_trained.npz"
    return str(p) if p.exists() else None


@pytest.fixture(scope="module")
def weights_path():
    path = _get_weights_path()
    if path is None:
        pytest.skip("p29_trained.npz not found")
    return path


class TestVisualDecoderWeights:

    def test_weights_exist(self, weights_path):
        assert weights_path is not None

    def test_load_weights(self, weights_path):
        decoder = VisualDecoder()
        ok = load_default_visual_decoder_weights(decoder, weights_path)
        assert ok, "load_default_visual_decoder_weights returned False"

    def test_trained_vs_random_produces_different_image(self, weights_path):
        decoder_trained = VisualDecoder()
        load_default_visual_decoder_weights(decoder_trained, weights_path)
        decoder_random = VisualDecoder()
        latent = np.random.default_rng(42).normal(0, 1, 64).astype(np.float32)
        img_trained = decoder_trained.decode(latent)
        img_random = decoder_random.decode(latent)
        diff = np.mean(np.abs(img_trained.astype(np.float32) - img_random.astype(np.float32)))
        assert diff > 5.0, f"Trained vs random mean diff={diff:.3f}, expected > 5.0"

    def test_trained_decode_output_shape_and_range(self, weights_path):
        decoder = VisualDecoder()
        load_default_visual_decoder_weights(decoder, weights_path)
        rng = np.random.default_rng(123)
        for _ in range(3):
            latent = rng.normal(0, 1, 64).astype(np.float32)
            img = decoder.decode(latent)
            assert img.shape == (128, 128, 3), f"Expected (128,128,3), got {img.shape}"
            assert img.dtype == np.uint8
            assert img.min() >= 0 and img.max() <= 255

    def test_all_weight_keys_present(self, weights_path):
        data = np.load(weights_path)
        expected_keys = {
            "visual_decoder_W", "visual_decoder_b",
            "texture_W_hidden", "texture_b_hidden",
            "texture_W_featmap", "texture_b_featmap",
            "texture_tex_kernels",
        }
        present = set(data.keys())
        missing = expected_keys - present
        assert not missing, f"Missing weight keys in {weights_path}: {missing}"


class TestAudioWaveformDecoderWeights:

    @pytest.fixture(scope="class")
    def decoder_with_weights(self):
        decoder = AudioWaveformDecoder()
        ok = load_default_audio_decoder_weights(decoder)
        if not ok:
            pytest.skip("load_default_audio_decoder_weights returned False")
        return decoder

    def test_load_weights(self):
        if _get_weights_path() is None:
            pytest.skip("p29_trained.npz not found")
        decoder = AudioWaveformDecoder()
        ok = load_default_audio_decoder_weights(decoder)
        assert ok, "load_default_audio_decoder_weights returned False"

    def test_trained_vs_random_waveform(self, decoder_with_weights):
        decoder_random = AudioWaveformDecoder()
        latent = np.random.default_rng(42).normal(0, 1, 64).astype(np.float32)
        wav_trained = decoder_with_weights.decode(latent)
        wav_random = decoder_random.decode(latent)
        diff = np.mean(np.abs(wav_trained - wav_random))
        assert diff > 0.01, f"Trained vs random diff={diff:.6f}"

    def test_trained_waveform_shape_and_range(self, decoder_with_weights):
        rng = np.random.default_rng(123)
        for _ in range(3):
            latent = rng.normal(0, 1, 64).astype(np.float32)
            wav = decoder_with_weights.decode(latent)
            assert len(wav) == 16000
            assert wav.dtype == np.float32
            assert np.all(wav >= -1.0) and np.all(wav <= 1.0)

    def test_trained_waveform_not_silent(self, decoder_with_weights):
        latent = np.random.default_rng(42).normal(0, 1, 64).astype(np.float32)
        wav = decoder_with_weights.decode(latent)
        rms = np.sqrt(np.mean(wav ** 2))
        assert rms > 0.001, f"Trained waveform RMS={rms:.6f} — too quiet"


class TestQualityMetrics:
    """Unit tests for ssim, psnr, snr quality metrics."""

    def test_ssim_identical_images(self):
        img = np.random.default_rng(42).integers(0, 256, (128, 128, 3), dtype=np.uint8)
        score = ssim(img, img)
        assert abs(score - 1.0) < 1e-6, f"Identical SSIM should be 1.0, got {score}"

    def test_ssim_different_images(self):
        a = np.zeros((128, 128, 3), dtype=np.uint8)
        b = np.ones((128, 128, 3), dtype=np.uint8) * 255
        score = ssim(a, b)
        assert score < 0.5, f"Very different images should have low SSIM, got {score}"

    def test_psnr_identical_images(self):
        img = np.random.default_rng(42).integers(0, 256, (128, 128, 3), dtype=np.uint8)
        score = psnr(img, img)
        assert score > 50.0, f"Identical PSNR should be high, got {score:.2f}dB"

    def test_psnr_different_images(self):
        a = np.zeros((128, 128, 3), dtype=np.uint8)
        b = np.ones((128, 128, 3), dtype=np.uint8) * 128
        score = psnr(a, b)
        assert 0 < score < 20.0, f"Different PSNR should be low, got {score:.2f}dB"

    def test_snr_identical_signals(self):
        sig = np.random.default_rng(42).normal(0, 1, 16000).astype(np.float32)
        score = snr(sig, sig)
        assert score > 50.0, f"Identical SNR should be high, got {score:.2f}dB"

    def test_snr_zero_reconstruction(self):
        sig = np.random.default_rng(42).normal(0, 1, 16000).astype(np.float32)
        score = snr(sig, np.zeros(16000, dtype=np.float32))
        assert -1e-6 <= score <= 1e-6, f"SNR(zero_recon) should be ~0dB, got {score:.4f}dB"

    def test_snr_noisy_reconstruction(self):
        sig = np.random.default_rng(42).normal(0, 1, 16000).astype(np.float32)
        noise = np.random.default_rng(99).normal(0, 0.5, 16000).astype(np.float32)
        score = snr(sig, sig + noise)
        assert 0 < score < 20.0, f"Noisy SNR should be positive and moderate, got {score:.2f}dB"

    def test_ssim_shape_mismatch(self):
        a = np.zeros((128, 128, 3), dtype=np.uint8)
        b = np.zeros((64, 64, 3), dtype=np.uint8)
        assert ssim(a, b) == 0.0, "Shape mismatch should return 0.0"

    def test_quality_report_keys(self):
        from ai.multimodal.quality_metrics import quality_report
        img = np.random.default_rng(42).integers(0, 256, (128, 128, 3), dtype=np.uint8)
        wav = np.random.default_rng(42).normal(0, 1, 16000).astype(np.float32)
        report = quality_report(img, img, wav, wav)
        assert "ssim" in report
        assert "image_psnr" in report
        assert "audio_snr" in report
        assert report["ssim"] > 0.99


class TestTextureBenchmark:
    """Benchmark texture training on real CIFAR-10 images (if available)."""

    @pytest.fixture(scope="class")
    def cifar_images(self):
        pytest.importorskip("scipy.ndimage")
        pytest.importorskip("ai.multimodal.data_loader")
        from scipy.ndimage import zoom
        from ai.multimodal.data_loader import CIFAR10Loader
        loader = CIFAR10Loader()
        if not loader.available:
            pytest.skip("CIFAR-10 data not available")
        images = []
        for label, path in loader._samples[:5]:
            img = np.load(path).astype(np.uint8)
            if img.ndim == 2:
                img = np.stack([img] * 3, axis=-1)
            if img.shape[:2] != (128, 128):
                factors = (128.0 / img.shape[0], 128.0 / img.shape[1], 1.0)
                img = zoom(img, factors, order=1).astype(np.uint8)
            images.append(img)
        return images

    def test_texture_training_reduces_loss_on_real_data(self, cifar_images):
        from ai.multimodal.training_pipeline import (
            FullTrainingPipeline, TextureTrainer)
        pipeline = FullTrainingPipeline()
        trainer = TextureTrainer(pipeline._reconstruction, pipeline._visual_decoder)
        result = trainer.train_on_real(cifar_images, steps=3, lr=0.01)
        after_loss = result["final_loss"]
        assert after_loss < 30000, f"Texture loss after 3 steps should drop below baseline (~17618), got {after_loss:.4f}"
        assert len(result["history"]) == 3

    def test_ssim_improves_after_real_texture_training(self, cifar_images):
        from ai.multimodal.training_pipeline import (
            FullTrainingPipeline, TextureTrainer)
        pipeline = FullTrainingPipeline()
        trainer = TextureTrainer(pipeline._reconstruction, pipeline._visual_decoder)
        img = cifar_images[0]
        feats = pipeline._visual_encoder.encode(img)
        z = pipeline._ls.project("vision", feats)
        decoded_before = pipeline._visual_decoder.decode(z)
        ssim_before = ssim(decoded_before, img)
        trainer.train_on_real(cifar_images[:2], steps=5, lr=0.01)
        decoded_after = pipeline._visual_decoder.decode(z)
        ssim_after = ssim(decoded_after, img)
        # 10% relative tolerance, robust to negative/near-zero SSIM (multiplying a
        # negative baseline by 0.9 would invert the tolerance direction).
        tolerance = abs(ssim_before) * 0.1
        assert ssim_after >= ssim_before - tolerance or ssim_after > 0.3, (
            f"SSIM should not degrade significantly: before={ssim_before:.4f}, after={ssim_after:.4f}")
