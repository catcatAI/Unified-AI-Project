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
