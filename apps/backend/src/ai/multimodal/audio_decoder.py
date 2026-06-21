"""Audio waveform decoder — latent vector → audio waveform using numpy.

Reverse pipeline of AudioSpectralEncoder: 64-dim latent → PCM waveform.
"""

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class AudioWaveformDecoder:
    """Decodes a 64-dim latent vector into a PCM waveform.

    Pipeline:
      1. Wx+b projection: 64-dim latent → 128-dim spectral feature space
      2. Extract spectral envelope + temporal structure
      3. Sinusoidal synthesis with harmonics → mix → output waveform
    """

    SAMPLE_RATE: int = 16000
    DURATION: float = 1.0
    LATENT_DIM: int = 64
    FEATURE_DIM: int = 128
    N_HARMONICS: int = 8

    def __init__(self):
        rng = np.random.default_rng(42)
        scale = 1.0 / np.sqrt(self.LATENT_DIM)
        self._W = rng.normal(0, scale, (self.FEATURE_DIM, self.LATENT_DIM)).astype(np.float32)
        self._b = np.zeros(self.FEATURE_DIM, dtype=np.float32)

    def decode(self, latent: np.ndarray) -> np.ndarray:
        """Decode latent vector into float32 waveform samples [-1, 1].

        Args:
            latent: 64-dim float32 vector

        Returns:
            1D float32 array of samples in [-1, 1]
        """
        if len(latent) != self.LATENT_DIM:
            logger.warning("Expected latent dim %d, got %d", self.LATENT_DIM, len(latent))
            return np.array([], dtype=np.float32)

        raw = self._W @ latent + self._b

        spectral_env = raw[:40]
        temporal_env = raw[40:50]
        detail = raw[50:]

        n_samples = int(self.SAMPLE_RATE * self.DURATION)
        t = np.arange(n_samples, dtype=np.float32) / self.SAMPLE_RATE

        freqs = 200.0 + np.abs(spectral_env[:5]) * 800.0 / max(np.abs(spectral_env[:5]).max(), 1e-8)
        amps = np.abs(spectral_env[5:10]) / max(np.abs(spectral_env[5:10]).max(), 1e-8)
        amps = np.clip(amps, 0.01, 1.0)

        waveform = np.zeros(n_samples, dtype=np.float32)
        for h in range(self.N_HARMONICS):
            harmonic_amp = amps[h % len(amps)] / (h + 1)
            harmonic_freq = freqs[h % len(freqs)] * (h + 1)
            harmonic_freq = min(harmonic_freq, self.SAMPLE_RATE / 2 - 100)
            phase = np.sum(detail[h * 5:(h + 1) * 5]) if (h + 1) * 5 <= len(detail) else 0.0
            waveform += harmonic_amp * np.sin(2 * np.pi * harmonic_freq * t + phase)

        n_env = len(temporal_env)
        env_points = np.linspace(0, n_samples, n_env + 1).astype(int)
        envelope = np.zeros(n_samples, dtype=np.float32)
        for i in range(n_env):
            start = env_points[i]
            end = env_points[i + 1]
            val = np.clip(np.abs(temporal_env[i]), 0.0, 1.0)
            envelope[start:end] = val

        waveform = waveform * envelope
        peak = max(np.abs(waveform).max(), 1e-8)
        waveform = waveform / peak
        return waveform.astype(np.float32)

    def get_projection(self) -> np.ndarray:
        return self._W.copy()

    def set_projection(self, W: np.ndarray) -> None:
        if W.shape == self._W.shape:
            self._W = W.astype(np.float32)