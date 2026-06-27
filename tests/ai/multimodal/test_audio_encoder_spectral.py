import io
import struct
import wave

import numpy as np
import pytest


@pytest.fixture
def encoder():
    from ai.multimodal.audio_encoder_spectral import AudioSpectralEncoder
    return AudioSpectralEncoder()


def _make_sine_wav(freq=440, duration=1.0, sample_rate=16000):
    """Generate a simple sine wave WAV file bytes."""
    n_samples = int(sample_rate * duration)
    samples = (np.sin(2 * np.pi * freq * np.arange(n_samples) / sample_rate) * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()


class TestAudioSpectralEncoder:

    def test_encode_returns_vector(self, encoder):
        wav_data = _make_sine_wav(440, 0.5)
        vec = encoder.encode(wav_data)
        assert isinstance(vec, np.ndarray)
        assert vec.shape == (128,)
        assert vec.dtype == np.float32

    def test_encode_empty_returns_zeros(self, encoder):
        vec = encoder.encode(b"")
        assert np.all(vec == 0.0)

    def test_different_frequencies_different_vectors(self, encoder):
        wav_440 = _make_sine_wav(440, 0.3)
        wav_880 = _make_sine_wav(880, 0.3)
        v1 = encoder.encode(wav_440)
        v2 = encoder.encode(wav_880)
        assert not np.allclose(v1, v2)

    def test_same_audio_same_vector(self, encoder):
        wav_data = _make_sine_wav(440, 0.3)
        v1 = encoder.encode(wav_data)
        v2 = encoder.encode(wav_data)
        assert np.allclose(v1, v2)

    def test_raw_pcm_works(self, encoder):
        samples = (np.sin(2 * np.pi * 440 * np.arange(8000) / 16000) * 32767).astype(np.int16)
        raw = samples.tobytes()
        vec = encoder.encode(raw)
        assert not np.all(vec == 0.0)

    def test_vector_not_constant(self, encoder):
        wav_data = _make_sine_wav(440, 0.3)
        vec = encoder.encode(wav_data)
        unique = np.unique(vec)
        assert len(unique) > 1
