"""Audio waveform decoder — latent vector → audio waveform using numpy.

P24: Wavetable synthesis + LPC-style spectral shaping for natural timbre.
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class AudioWaveformDecoder:
    """Decodes a 64-dim latent vector into a PCM waveform.

    Pipeline:
      1. Linear projection Wx+b → 128-dim spectral feature space
      2. Wavetable oscillator: generate wavetable from latent → table lookup per cycle
      3. Multi-band: split into 3 frequency bands with independent wavetables
      4. Noise component + envelope shaping → output waveform
    """

    SAMPLE_RATE: int = 16000
    DURATION: float = 1.0
    LATENT_DIM: int = 64
    FEATURE_DIM: int = 128
    HIDDEN_DIM: int = 64
    N_HARMONICS: int = 8
    N_BANDS: int = 3
    WAVETABLE_SIZE: int = 256

    BAND_LIMITS: list = [(50, 500), (500, 2500), (2500, 7500)]

    def __init__(self):
        rng = np.random.default_rng(42)
        scale = 1.0 / np.sqrt(self.LATENT_DIM)
        self._W = rng.normal(0, scale, (self.FEATURE_DIM, self.LATENT_DIM)).astype(np.float32)
        self._b = np.zeros(self.FEATURE_DIM, dtype=np.float32)
        h_scale = 1.0 / np.sqrt(self.LATENT_DIM)
        self._W_hidden = rng.normal(0, h_scale, (self.HIDDEN_DIM, self.LATENT_DIM)).astype(np.float32)
        self._b_hidden = np.zeros(self.HIDDEN_DIM, dtype=np.float32)
        self._W_noise = rng.normal(0, 1.0 / np.sqrt(self.HIDDEN_DIM), (16, self.HIDDEN_DIM)).astype(np.float32)
        self._b_noise = np.zeros(16, dtype=np.float32)
        # Wavetable generators (per band): hidden → WAVETABLE_SIZE waveform
        self._W_wavetable = rng.normal(0, 1.0 / np.sqrt(self.HIDDEN_DIM),
                                       (self.N_BANDS * self.WAVETABLE_SIZE, self.HIDDEN_DIM)).astype(np.float32)
        self._b_wavetable = np.zeros(self.N_BANDS * self.WAVETABLE_SIZE, dtype=np.float32)

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

        waveform = self._synthesize_wavetable(t, spectral_env, detail, latent, n_samples)
        waveform = self._add_noise_component(waveform, latent, n_samples)
        waveform = self._apply_envelope(waveform, temporal_env, n_samples)

        peak = max(np.abs(waveform).max(), 1e-8)
        waveform = waveform / peak
        return waveform.astype(np.float32)

    def _synthesize_wavetable(self, t: np.ndarray, spectral_env: np.ndarray,
                               detail: np.ndarray, latent: np.ndarray,
                               n_samples: int) -> np.ndarray:
        """Synthesize multi-band waveform using wavetable oscillators.

        Each band gets its own wavetable (256-sample waveform) derived from
        the latent's hidden layer. The wavetable is read at the band's
        fundamental frequency, producing rich harmonic content.
        """
        h = np.tanh(self._W_hidden @ latent + self._b_hidden)
        wt_flat = self._W_wavetable @ h + self._b_wavetable
        wavetables = wt_flat.reshape(self.N_BANDS, self.WAVETABLE_SIZE)

        waveform = np.zeros(n_samples, dtype=np.float32)

        for band_idx, (lo, hi) in enumerate(self.BAND_LIMITS):
            wt = wavetables[band_idx]
            feats = spectral_env[band_idx * (len(spectral_env) // self.N_BANDS):
                                 (band_idx + 1) * (len(spectral_env) // self.N_BANDS)]
            freq_hz = 200.0 + np.abs(feats[:5]).mean() * (hi - lo) / 800.0
            freq_hz = np.clip(freq_hz, lo, hi)

            phase = np.cumsum(2 * np.pi * freq_hz / self.SAMPLE_RATE * np.ones(n_samples))
            phase = phase % (2 * np.pi)
            idx = (phase / (2 * np.pi) * self.WAVETABLE_SIZE).astype(int) % self.WAVETABLE_SIZE
            band_wave = wt[idx]

            # Mix in a few harmonics from the detail features
            d_start = band_idx * (len(detail) // self.N_BANDS)
            d_end = (band_idx + 1) * (len(detail) // self.N_BANDS)
            band_detail = detail[d_start:d_end] if d_end <= len(detail) else detail[d_start:]
            for h_idx in range(min(self.N_HARMONICS // self.N_BANDS, len(band_detail) // 2)):
                amp = np.abs(band_detail[h_idx * 2]) / max(np.abs(band_detail).max(), 1e-8)
                amp = np.clip(amp, 0.0, 0.5)
                h_freq = freq_hz * (h_idx + 2)
                if h_freq < self.SAMPLE_RATE / 2:
                    band_wave += amp * np.sin(2 * np.pi * h_freq * t)

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

    def set_projection(self, W: np.ndarray, b: Optional[np.ndarray] = None) -> None:
        if W.shape == self._W.shape:
            self._W = W.astype(np.float32)
        if b is not None and b.shape == self._b.shape:
            self._b = b.astype(np.float32)

    def set_wavetable_weights(self, W_hidden: np.ndarray, b_hidden: np.ndarray,
                                W_wavetable: np.ndarray, b_wavetable: np.ndarray,
                                W_noise: np.ndarray, b_noise: np.ndarray) -> bool:
        if W_hidden.shape == self._W_hidden.shape:
            self._W_hidden = W_hidden.astype(np.float32)
        if b_hidden.shape == self._b_hidden.shape:
            self._b_hidden = b_hidden.astype(np.float32)
        if W_wavetable.shape == self._W_wavetable.shape:
            self._W_wavetable = W_wavetable.astype(np.float32)
        if b_wavetable.shape == self._b_wavetable.shape:
            self._b_wavetable = b_wavetable.astype(np.float32)
        if W_noise.shape == self._W_noise.shape:
            self._W_noise = W_noise.astype(np.float32)
        if b_noise.shape == self._b_noise.shape:
            self._b_noise = b_noise.astype(np.float32)
        return True


def save_audio_decoder_weights(decoder: AudioWaveformDecoder, weights_path: str) -> bool:
    """Save all audio decoder weight arrays to a .npz file.

    Includes projection (W, b), wavetable (W_hidden, b_hidden,
    W_wavetable, b_wavetable), and noise (W_noise, b_noise) weights.

    Returns True on success.
    """
    try:
        np.savez(weights_path,
                 audio_decoder_W=decoder._W,
                 audio_decoder_b=decoder._b,
                 audio_W_hidden=decoder._W_hidden,
                 audio_b_hidden=decoder._b_hidden,
                 audio_W_wavetable=decoder._W_wavetable,
                 audio_b_wavetable=decoder._b_wavetable,
                 audio_W_noise=decoder._W_noise,
                 audio_b_noise=decoder._b_noise)
        logger.info("Audio decoder weights saved to %s", weights_path)
        return True
    except Exception as e:
        logger.warning("Failed to save audio decoder weights: %s", e)
        return False


def load_default_audio_decoder_weights(decoder: AudioWaveformDecoder, weights_path: Optional[str] = None) -> bool:
    """Load pre-trained audio decoder weights from p29_trained.npz.

    Returns True if weights were loaded, False otherwise.
    """
    if weights_path is None:
        # audio_decoder.py → multimodal → ai → src → backend → apps → root
        weights_path = str(Path(__file__).resolve().parent.parent.parent.parent.parent.parent /
                          "data" / "multimodal" / "weights" / "p29_trained.npz")
    wpath = Path(weights_path)
    if not wpath.exists():
        logger.debug("No pre-trained audio decoder weights at %s", wpath)
        return False
    try:
        data = np.load(wpath)
        if "audio_decoder_W" in data:
            decoder._W = data["audio_decoder_W"]
            decoder._b = data.get("audio_decoder_b", decoder._b)
            if "audio_W_hidden" in data:
                decoder._W_hidden = data["audio_W_hidden"]
                decoder._b_hidden = data["audio_b_hidden"]
                decoder._W_wavetable = data["audio_W_wavetable"]
                decoder._b_wavetable = data["audio_b_wavetable"]
                decoder._W_noise = data["audio_W_noise"]
                decoder._b_noise = data["audio_b_noise"]
            logger.info("Loaded pre-trained audio decoder weights from %s", wpath)
            return True
    except Exception as e:
        logger.warning("Failed to load audio decoder weights: %s", e)
    return False