"""Audio waveform decoder — latent vector → audio waveform using numpy.

P22: Multi-band synthesis + non-linear detail branch.
"""

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class AudioWaveformDecoder:
    """Decodes a 64-dim latent vector into a PCM waveform.

    Pipeline:
      1. Linear projection Wx+b → 128-dim spectral feature space
      2. Non-linear detail branch → noise component for unvoiced texture
      3. Multi-band synthesis: 3 independent frequency bands
      4. Mix + envelope shaping → output waveform
    """

    SAMPLE_RATE: int = 16000
    DURATION: float = 1.0
    LATENT_DIM: int = 64
    FEATURE_DIM: int = 128
    HIDDEN_DIM: int = 64
    N_HARMONICS: int = 8
    N_BANDS: int = 3

    # Band frequency ranges: low, mid, high
    BAND_LIMITS: list = [(50, 500), (500, 2500), (2500, 7500)]

    def __init__(self):
        rng = np.random.default_rng(42)
        scale = 1.0 / np.sqrt(self.LATENT_DIM)
        self._W = rng.normal(0, scale, (self.FEATURE_DIM, self.LATENT_DIM)).astype(np.float32)
        self._b = np.zeros(self.FEATURE_DIM, dtype=np.float32)
        # Non-linear detail branch
        h_scale = 1.0 / np.sqrt(self.LATENT_DIM)
        self._W_hidden = rng.normal(0, h_scale, (self.HIDDEN_DIM, self.LATENT_DIM)).astype(np.float32)
        self._b_hidden = np.zeros(self.HIDDEN_DIM, dtype=np.float32)
        self._W_noise = rng.normal(0, 1.0 / np.sqrt(self.HIDDEN_DIM), (16, self.HIDDEN_DIM)).astype(np.float32)
        self._b_noise = np.zeros(16, dtype=np.float32)

    def decode(self, latent: np.ndarray) -> np.ndarray:
        """Decode latent vector into float32 waveform samples [-1, 1]."""
        if len(latent) != self.LATENT_DIM:
            logger.warning("Expected latent dim %d, got %d", self.LATENT_DIM, len(latent))
            return np.array([], dtype=np.float32)

        raw = self._W @ latent + self._b
        spectral_env = raw[:40]
        temporal_env = raw[40:50]
        detail = raw[50:]

        n_samples = int(self.SAMPLE_RATE * self.DURATION)
        t = np.arange(n_samples, dtype=np.float32) / self.SAMPLE_RATE

        waveform = self._synthesize_bands(t, spectral_env, detail, n_samples)
        waveform = self._add_noise_component(waveform, latent, n_samples)
        waveform = self._apply_envelope(waveform, temporal_env, n_samples)

        peak = max(np.abs(waveform).max(), 1e-8)
        waveform = waveform / peak
        return waveform.astype(np.float32)

    def _synthesize_bands(self, t: np.ndarray, spectral_env: np.ndarray,
                          detail: np.ndarray, n_samples: int) -> np.ndarray:
        """Synthesize multi-band waveform from spectral envelope features."""
        waveform = np.zeros(n_samples, dtype=np.float32)

        feats_per_band = len(spectral_env) // self.N_BANDS
        detail_per_band = len(detail) // self.N_BANDS

        for band_idx, (lo, hi) in enumerate(self.BAND_LIMITS):
            feat_start = band_idx * feats_per_band
            band_feats = spectral_env[feat_start:feat_start + feats_per_band]

            detail_start = band_idx * detail_per_band
            band_detail = detail[detail_start:detail_start + detail_per_band] if detail_start + detail_per_band <= len(detail) else detail[detail_start:]

            freqs = 200.0 + np.abs(band_feats[:5]) * (hi - lo) / max(np.abs(band_feats[:5]).max(), 1e-8)
            freqs = np.clip(freqs, lo, hi)
            amps = np.abs(band_feats[5:10]) / max(np.abs(band_feats[5:10]).max(), 1e-8)
            amps = np.clip(amps, 0.01, 1.0)

            band_wave = np.zeros(n_samples, dtype=np.float32)
            for h in range(self.N_HARMONICS):
                harmonic_amp = amps[h % len(amps)] / (h + 1)
                harmonic_freq = freqs[h % len(freqs)] * (h + 1)
                harmonic_freq = min(harmonic_freq, self.SAMPLE_RATE / 2 - 100)
                phase = float(np.sum(band_detail[h * 5:(h + 1) * 5])) if (h + 1) * 5 <= len(band_detail) else 0.0
                band_wave += harmonic_amp * np.sin(2 * np.pi * harmonic_freq * t + phase)

            waveform += band_wave * (1.0 / self.N_BANDS)

        return waveform

    def _add_noise_component(self, waveform: np.ndarray, latent: np.ndarray,
                             n_samples: int) -> np.ndarray:
        """Add noise from non-linear hidden branch for richer timbre."""
        h = np.tanh(self._W_hidden @ latent + self._b_hidden)
        noise_mod = self._W_noise @ h + self._b_noise
        noise_strength = float(np.clip(np.abs(np.mean(noise_mod)) * 0.01, 0, 0.15))
        if noise_strength < 0.001:
            return waveform
        rng = np.random.default_rng(int(abs(float(noise_mod[0] * 1000)) % (2 ** 31)))
        noise = rng.normal(0, noise_strength, n_samples).astype(np.float32)
        return waveform + noise

    def _apply_envelope(self, waveform: np.ndarray, temporal_env: np.ndarray,
                        n_samples: int) -> np.ndarray:
        """Apply temporal amplitude envelope."""
        n_env = len(temporal_env)
        env_points = np.linspace(0, n_samples, n_env + 1).astype(int)
        envelope = np.zeros(n_samples, dtype=np.float32)
        for i in range(n_env):
            start = env_points[i]
            end = env_points[i + 1]
            val = np.clip(np.abs(temporal_env[i]), 0.0, 1.0)
            envelope[start:end] = val
        return waveform * envelope

    def get_projection(self) -> np.ndarray:
        return self._W.copy()

    def set_projection(self, W: np.ndarray) -> None:
        if W.shape == self._W.shape:
            self._W = W.astype(np.float32)