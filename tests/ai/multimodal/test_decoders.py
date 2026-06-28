import numpy as np
import pytest


@pytest.fixture
def visual_decoder():
    from ai.multimodal.visual_decoder import VisualDecoder
    return VisualDecoder()


@pytest.fixture
def audio_decoder():
    from ai.multimodal.audio_decoder import AudioWaveformDecoder
    return AudioWaveformDecoder()


@pytest.fixture
def latent():
    return np.random.default_rng(42).normal(0, 1, 64).astype(np.float32)


class TestVisualDecoder:

    def test_decode_returns_uint8_array(self, visual_decoder, latent):
        img = visual_decoder.decode(latent)
        assert isinstance(img, np.ndarray)
        assert img.shape == (128, 128, 3)
        assert img.dtype == np.uint8

    def test_decode_to_pil(self, visual_decoder, latent):
        from PIL import Image
        pil = visual_decoder.decode_to_pil(latent)
        assert isinstance(pil, Image.Image)
        assert pil.size == (128, 128)
        assert pil.mode == "RGB"

    def test_different_latents_give_different_images(self, visual_decoder):
        l1 = np.random.default_rng(1).normal(0, 1, 64).astype(np.float32)
        l2 = np.random.default_rng(2).normal(0, 1, 64).astype(np.float32)
        i1 = visual_decoder.decode(l1)
        i2 = visual_decoder.decode(l2)
        assert not np.allclose(i1, i2)

    def test_wrong_latent_dim_returns_zeros(self, visual_decoder):
        bad = np.zeros(10, dtype=np.float32)
        result = visual_decoder.decode(bad)
        assert np.all(result == 0)

    def test_same_latent_same_image(self, visual_decoder):
        l = np.random.default_rng(42).normal(0, 1, 64).astype(np.float32)
        i1 = visual_decoder.decode(l)
        i2 = visual_decoder.decode(l)
        assert np.array_equal(i1, i2)

    def test_image_has_variation(self, visual_decoder, latent):
        img = visual_decoder.decode(latent)
        unique = np.unique(img)
        assert len(unique) > 1

    def test_get_projection_shape(self, visual_decoder):
        W = visual_decoder.get_projection()
        assert W.shape == (256, 64)

    def test_set_projection(self, visual_decoder):
        W_new = np.zeros((256, 64), dtype=np.float32)
        visual_decoder.set_projection(W_new)
        assert np.allclose(visual_decoder.get_projection(), W_new)

    def test_reconstruction_cycle_backward_compat(self, visual_decoder):
        """Verify _W and _b are writable arrays for ReconstructionCycle compatibility."""
        l = np.random.default_rng(42).normal(0, 1, 64).astype(np.float32)
        before = visual_decoder.decode(l)
        visual_decoder._W[:] = 0.0
        visual_decoder._b[:] = 0.0
        after = visual_decoder.decode(l)
        assert not np.array_equal(before, after)

    def test_set_texture_weights(self, visual_decoder):
        W_hidden_new = np.zeros((64, 64), dtype=np.float32)
        visual_decoder.set_texture_weights(W_hidden_new)
        assert np.allclose(visual_decoder._W_hidden, W_hidden_new)

    def test_set_texture_weights_partial(self, visual_decoder):
        """Partial call only updates what's given."""
        saved = visual_decoder._b_hidden.copy()
        W_hidden_new = np.full((64, 64), 0.5, dtype=np.float32)
        visual_decoder.set_texture_weights(W_hidden_new)
        assert np.allclose(visual_decoder._b_hidden, saved)

    def test_save_and_load_weights(self, visual_decoder, tmp_path):
        from ai.multimodal.visual_decoder import (VisualDecoder,
                                                   save_visual_decoder_weights,
                                                   load_default_visual_decoder_weights)
        save_path = str(tmp_path / "test_weights.npz")
        assert save_visual_decoder_weights(visual_decoder, save_path)
        decoder2 = VisualDecoder()
        assert load_default_visual_decoder_weights(decoder2, save_path)
        assert np.allclose(decoder2._W, visual_decoder._W)
        assert np.allclose(decoder2._W_hidden, visual_decoder._W_hidden)
        assert np.allclose(decoder2._tex_kernels, visual_decoder._tex_kernels)


class TestAudioWaveformDecoder:

    def test_decode_returns_float32(self, audio_decoder, latent):
        wav = audio_decoder.decode(latent)
        assert isinstance(wav, np.ndarray)
        assert wav.dtype == np.float32

    def test_decode_length(self, audio_decoder, latent):
        wav = audio_decoder.decode(latent)
        assert len(wav) == 16000  # 1s at 16kHz

    def test_waveform_in_range(self, audio_decoder, latent):
        wav = audio_decoder.decode(latent)
        assert np.all(wav >= -1.0)
        assert np.all(wav <= 1.0)

    def test_waveform_not_silent(self, audio_decoder, latent):
        wav = audio_decoder.decode(latent)
        rms = np.sqrt(np.mean(wav ** 2))
        assert rms > 0.001

    def test_different_latents_different_waveforms(self, audio_decoder):
        l1 = np.random.default_rng(1).normal(0, 1, 64).astype(np.float32)
        l2 = np.random.default_rng(2).normal(0, 1, 64).astype(np.float32)
        w1 = audio_decoder.decode(l1)
        w2 = audio_decoder.decode(l2)
        assert not np.allclose(w1, w2)

    def test_wrong_latent_dim_returns_empty(self, audio_decoder):
        bad = np.zeros(10, dtype=np.float32)
        result = audio_decoder.decode(bad)
        assert len(result) == 0

    def test_has_frequency_content(self, audio_decoder, latent):
        wav = audio_decoder.decode(latent)
        spec = np.abs(np.fft.rfft(wav))
        assert np.sum(spec > 0.1 * spec.max()) > 1

    def test_get_projection_shape(self, audio_decoder):
        W = audio_decoder.get_projection()
        assert W.shape == (128, 64)

    def test_multi_band_frequency_distribution(self, audio_decoder, latent):
        """Verify multi-band synthesis produces energy across band ranges."""
        wav = audio_decoder.decode(latent)
        spec = np.abs(np.fft.rfft(wav))
        freqs = np.fft.rfftfreq(len(wav), d=1.0 / 16000)
        band_energies = []
        for lo, hi in [(50, 500), (500, 2500), (2500, 7500)]:
            mask = (freqs >= lo) & (freqs <= hi)
            energy = float(np.sum(spec[mask] ** 2)) if np.any(mask) else 0.0
            band_energies.append(energy)
        active = sum(1 for e in band_energies if e > 0.01 * max(band_energies))
        assert active >= 2, f"Expected >=2 active bands, got {active}: {band_energies}"
