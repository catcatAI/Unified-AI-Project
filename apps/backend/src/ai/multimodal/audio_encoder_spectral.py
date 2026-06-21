"""Audio spectral encoder — real waveform-to-feature-vector extraction using numpy."""

import io
import logging
import struct
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class AudioSpectralEncoder:
    """Encodes raw audio bytes into a fixed-size spectral feature vector.

    Extracts spectral features:
      - Mel-frequency band energies (20 bands)
      - Spectral centroid, rolloff, bandwidth
      - Zero-crossing rate
      - RMS energy envelope (4 regions)
    Total: ~28 dimensions.
    """

    SAMPLE_RATE: int = 16000
    N_MELS: int = 20
    N_FFT: int = 512
    HOP_LENGTH: int = 256
    FEATURE_DIM: int = 32

    def __init__(self, feature_dim: Optional[int] = None):
        self._feature_dim = feature_dim or self.FEATURE_DIM
        self._projection: Optional[np.ndarray] = None

    def encode(self, audio_data: bytes) -> np.ndarray:
        """Encode raw audio bytes (WAV or raw PCM) into a feature vector."""
        if not audio_data:
            return np.zeros(self._feature_dim, dtype=np.float32)
        try:
            samples = self._decode_audio(audio_data)
            return self._encode_samples(samples)
        except Exception as e:
            logger.debug("AudioSpectralEncoder failed: %s", e)
            return np.zeros(self._feature_dim, dtype=np.float32)

    def _decode_audio(self, audio_data: bytes) -> np.ndarray:
        """Decode audio bytes to float samples [-1, 1]."""
        if audio_data[:4] == b"RIFF":
            return self._decode_wav(audio_data)
        fmt = "<" + "h" * (len(audio_data) // 2)
        samples = np.frombuffer(audio_data[:len(audio_data) - len(audio_data) % 2],
                                dtype=np.int16).astype(np.float32) / 32768.0
        return samples

    def _decode_wav(self, data: bytes) -> np.ndarray:
        """Decode WAV file bytes to float samples."""
        try:
            import wave
            with io.BytesIO(data) as buf:
                with wave.open(buf, "rb") as wf:
                    frames = wf.readframes(wf.getnframes())
                    sampwidth = wf.getsampwidth()
                    nchannels = wf.getnchannels()
            if sampwidth == 2:
                dtype = np.int16
            elif sampwidth == 1:
                dtype = np.uint8
            else:
                return np.array([], dtype=np.float32)
            samples = np.frombuffer(frames, dtype=dtype).astype(np.float32)
            if sampwidth == 2:
                samples /= 32768.0
            elif sampwidth == 1:
                samples = (samples - 128.0) / 128.0
            if nchannels > 1:
                samples = samples.reshape(-1, nchannels).mean(axis=1)
            return samples
        except Exception:
            return np.array([], dtype=np.float32)

    def _encode_samples(self, samples: np.ndarray) -> np.ndarray:
        """Extract spectral features from audio samples."""
        if len(samples) < 2:
            return np.zeros(self._feature_dim, dtype=np.float32)

        if len(samples) < self.N_FFT:
            samples = np.pad(samples, (0, max(0, self.N_FFT - len(samples))))

        if len(samples) > self.SAMPLE_RATE * 5:
            samples = samples[:self.SAMPLE_RATE * 5]

        stft = self._stft(samples)
        magnitude = np.abs(stft)

        features = []
        features.extend(self._mel_energies(magnitude))
        features.append(self._spectral_centroid(magnitude))
        features.append(self._spectral_rolloff(magnitude))
        features.append(self._spectral_bandwidth(magnitude, self._spectral_centroid(magnitude)))
        features.append(self._zero_crossing_rate(samples))
        features.extend(self._rms_envelope(samples))

        raw = np.array(features, dtype=np.float32)
        return self._project_if_needed(raw)

    def _stft(self, samples: np.ndarray) -> np.ndarray:
        """Simple STFT using numpy."""
        window = np.hanning(self.N_FFT)
        n_frames = max(1, (len(samples) - self.N_FFT) // self.HOP_LENGTH + 1)
        stft = np.zeros((self.N_FFT // 2 + 1, n_frames), dtype=np.complex64)
        for t in range(n_frames):
            start = t * self.HOP_LENGTH
            frame = samples[start:start + self.N_FFT]
            if len(frame) < self.N_FFT:
                frame = np.pad(frame, (0, self.N_FFT - len(frame)))
            stft[:, t] = np.fft.rfft(frame * window)
        return stft

    def _mel_energies(self, magnitude: np.ndarray) -> list:
        """Compute Mel-frequency band energies."""
        n_freqs, n_frames = magnitude.shape
        mel_matrix = np.zeros((self.N_MELS, n_freqs), dtype=np.float32)
        mel_min = 0.0
        mel_max = 2595.0 * np.log10(1.0 + self.SAMPLE_RATE / 2.0 / 700.0)
        mel_points = np.linspace(mel_min, mel_max, self.N_MELS + 2)
        hz_points = 700.0 * (10.0 ** (mel_points / 2595.0) - 1.0)
        bin_points = hz_points / self.SAMPLE_RATE * 2.0 * n_freqs
        for m in range(1, self.N_MELS + 1):
            left = int(bin_points[m - 1])
            center = int(bin_points[m])
            right = int(bin_points[m + 1])
            for f in range(left, center):
                if f < n_freqs:
                    mel_matrix[m - 1, f] = (f - left) / (center - left)
            for f in range(center, min(right, n_freqs)):
                mel_matrix[m - 1, f] = (right - f) / (right - center)
        mel_spec = mel_matrix @ magnitude
        log_mel = np.log(np.maximum(mel_spec, 1e-10))
        return log_mel.mean(axis=1).tolist()

    def _spectral_centroid(self, magnitude: np.ndarray) -> float:
        """Weighted mean of frequencies."""
        freqs = np.arange(magnitude.shape[0])
        total = magnitude.sum()
        if total == 0:
            return 0.0
        return float((freqs[:, None] * magnitude).sum() / total)

    def _spectral_rolloff(self, magnitude: np.ndarray, percentile: float = 0.85) -> float:
        """Frequency below which percentile of energy is contained."""
        cumsum = np.cumsum(magnitude.sum(axis=1))
        total = cumsum[-1]
        if total == 0:
            return 0.0
        return float(np.searchsorted(cumsum, percentile * total))

    def _spectral_bandwidth(self, magnitude: np.ndarray, centroid: float) -> float:
        """Spectral bandwidth (spread around centroid)."""
        freqs = np.arange(magnitude.shape[0])
        diff = (freqs[:, None] - centroid) ** 2
        total = magnitude.sum()
        if total == 0:
            return 0.0
        return float(np.sqrt((diff * magnitude).sum() / total))

    def _zero_crossing_rate(self, samples: np.ndarray) -> float:
        """Rate of sign changes."""
        if len(samples) < 2:
            return 0.0
        return float(np.mean(np.abs(np.diff(np.sign(samples))) > 0))

    def _rms_envelope(self, samples: np.ndarray) -> list:
        """RMS energy in 4 equal regions."""
        n_regions = 4
        region_len = len(samples) // n_regions
        rms = []
        for i in range(n_regions):
            region = samples[i * region_len:(i + 1) * region_len]
            rms.append(float(np.sqrt(np.mean(region ** 2))) if len(region) > 0 else 0.0)
        return rms

    def _project_if_needed(self, raw: np.ndarray) -> np.ndarray:
        """Project to target dimension if needed."""
        if len(raw) <= self._feature_dim:
            padded = np.zeros(self._feature_dim, dtype=np.float32)
            padded[:len(raw)] = raw
            return padded
        if self._projection is None or self._projection.shape[1] != len(raw):
            rng = np.random.default_rng(42)
            self._projection = rng.normal(
                0, 1 / np.sqrt(len(raw)),
                (self._feature_dim, len(raw))
            ).astype(np.float32)
        return self._projection @ raw
