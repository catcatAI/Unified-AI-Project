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
    samples = (np.sin(2 * np.pi * freq * np.arange(n_samples) / sample_rate) * 32767).astype(
        np.int16
    )
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


class TestAudioSpectralProjection:
    """``_project_if_needed`` must keep the legacy zero-pad output while
    exposing a trainable matrix."""

    def test_feature_dim_property(self, encoder):
        assert encoder.feature_dim == 128

    @pytest.mark.parametrize("feature_dim", [64, 128, 256])
    def test_output_shape_follows_feature_dim(self, feature_dim):
        from ai.multimodal.audio_encoder_spectral import AudioSpectralEncoder

        enc = AudioSpectralEncoder(feature_dim=feature_dim)
        wav = _make_sine_wav(440, 0.3)
        samples = enc._decode_audio(wav)
        raw = enc._extract_raw(samples)
        out = enc.encode(wav)

        assert out.shape == (feature_dim,)
        assert enc._projection is not None
        assert enc._projection.shape == (feature_dim, raw.size)
        if raw.size <= feature_dim:
            assert np.allclose(out[: raw.size], raw)
            assert np.all(out[raw.size :] == 0.0)

    def test_projection_is_deterministic_across_instances(self):
        from ai.multimodal.audio_encoder_spectral import AudioSpectralEncoder

        wav = _make_sine_wav(330, 0.3)
        a = AudioSpectralEncoder(feature_dim=256).encode(wav)
        b = AudioSpectralEncoder(feature_dim=256).encode(wav)
        assert np.allclose(a, b)


class TestAudioSpectralTraining:
    """Regression for Phase 0: ``train_step`` raised on a 64-dim target and
    its gradient had the wrong shape for the projection matrix."""

    @pytest.mark.parametrize(
        "target",
        [None, np.zeros(2, dtype=np.float32), np.ones(64, dtype=np.float32), np.ones(128)],
        ids=["none", "len2", "len64", "len128"],
    )
    def test_train_step_accepts_any_target_length(self, encoder, target):
        loss = encoder.train_step(_make_sine_wav(440, 0.3), target, lr=1e-3)
        assert np.isfinite(loss)

    def test_train_step_accepts_overlong_target(self, encoder):
        loss = encoder.train_step(_make_sine_wav(440, 0.3), np.ones(1024), lr=1e-3)
        assert np.isfinite(loss)

    def test_train_step_initialises_projection(self, encoder):
        wav = _make_sine_wav(440, 0.3)
        samples = encoder._decode_audio(wav)
        encoder._extract_raw(samples)  # raw exists but is not projected yet
        encoder.train_step(wav, np.zeros(64, dtype=np.float32))
        assert encoder._projection is not None

    def test_train_step_loss_decreases(self):
        from ai.multimodal.audio_encoder_spectral import AudioSpectralEncoder

        enc = AudioSpectralEncoder()
        wav = _make_sine_wav(440, 0.5)
        target = np.random.default_rng(0).standard_normal(enc.feature_dim).astype(np.float32)
        losses = [enc.train_step(wav, target, lr=1e-3) for _ in range(30)]
        assert losses[0] > 0
        assert losses[-1] < losses[0]

    def test_train_step_empty_audio_returns_zero(self, encoder):
        assert encoder.train_step(b"", np.zeros(64, dtype=np.float32)) == 0.0
