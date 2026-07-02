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

    def test_weights_exist(self):
        assert _get_weights_path() is not None, "p29_trained.npz not found"

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
