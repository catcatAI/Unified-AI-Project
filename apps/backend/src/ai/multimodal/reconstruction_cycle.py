"""Reconstruction cycle + cross-modal synthesis — autoencoder train loop and cross-modal generation.

P19: Closes the encoder→latent→decoder→encoder reconstruction loop with
feature-level MSE training, and enables cross-modal latent blending.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from ai.multimodal.audio_decoder import AudioWaveformDecoder
from ai.multimodal.shared_latent_space import SharedLatentSpace
from ai.multimodal.visual_decoder import VisualDecoder

logger = logging.getLogger(__name__)


class ReconstructionCycle:
    """Trains encoder↔decoder projection weights via feature-level autoencoding.

    Pipeline:
      f → W_e @ f + b_e = z → W_d @ z + b_d = f_hat
      loss = 0.5 * ||f - f_hat||²

    Gradients are computed analytically (pure numpy). Only the projection
    matrices W_e (SharedLatentSpace) and W_d (Decoder) are updated.
    """

    def __init__(
        self,
        latent_space: SharedLatentSpace,
        visual_decoder: Optional[VisualDecoder] = None,
        audio_decoder: Optional[AudioWaveformDecoder] = None,
    ):
        self._ls = latent_space
        self._visual_decoder = visual_decoder
        self._audio_decoder = audio_decoder

    def train_step(self, modality: str, features: np.ndarray, lr: float = 0.01) -> float:
        """Single gradient descent step for feature-level reconstruction.

        Args:
            modality: Modality name (registered in latent_space)
            features: Input feature vector from the encoder
            lr: Learning rate

        Returns:
            Loss value before the update
        """
        proj = self._ls._projections.get(modality)
        if proj is None:
            return 0.0

        decoder = self._get_decoder(modality)
        if decoder is None:
            return 0.0

        f = features.astype(np.float32)
        W_e = proj["W"]
        b_e = proj["b"]
        W_d = decoder._W
        b_d = decoder._b

        z = W_e @ f + b_e
        f_hat = W_d @ z + b_d
        loss = 0.5 * float(np.sum((f_hat - f) ** 2))

        grad_f_hat = f_hat - f
        grad_W_d = np.outer(grad_f_hat, z)
        grad_b_d = grad_f_hat.copy()
        grad_z = W_d.T @ grad_f_hat
        grad_W_e = np.outer(grad_z, f)
        grad_b_e = grad_z.copy()

        # Gradient clipping (norm-based)
        max_norm = 10.0
        for g in [grad_W_d, grad_W_e]:
            norm = np.sqrt(np.sum(g**2))
            if norm > max_norm:
                g *= max_norm / norm
        for g in [grad_b_d, grad_b_e]:
            norm = np.sqrt(np.sum(g**2))
            if norm > max_norm:
                g *= max_norm / norm

        W_d -= lr * grad_W_d
        b_d -= lr * grad_b_d
        W_e -= lr * grad_W_e
        b_e -= lr * grad_b_e

        return loss

    def train(
        self, modality: str, features_list: List[np.ndarray], epochs: int = 20, lr: float = 0.005
    ) -> Dict:
        """Train over multiple samples for multiple epochs.

        Args:
            modality: Modality name
            features_list: List of feature vectors
            epochs: Number of passes over the data
            lr: Learning rate

        Returns:
            Dict with 'final_loss' and 'history'
        """
        history = []
        for epoch in range(epochs):
            epoch_loss = 0.0
            for f in features_list:
                epoch_loss += self.train_step(modality, f, lr)
            avg_loss = epoch_loss / max(len(features_list), 1)
            history.append(avg_loss)
        return {"final_loss": history[-1] if history else 0.0, "history": history}

    def reconstruct(self, modality: str, features: np.ndarray) -> np.ndarray:
        """Full forward pass: encode to latent → decode back to features.

        Args:
            modality: Modality name
            features: Input feature vector

        Returns:
            Reconstructed feature vector
        """
        proj = self._ls._projections.get(modality)
        decoder = self._get_decoder(modality)
        if proj is None or decoder is None:
            return np.zeros_like(features)

        z = self._ls.project(modality, features)
        f_hat = decoder._W @ z + decoder._b
        return np.asarray(f_hat)

    def reconstruction_error(self, modality: str, features: np.ndarray) -> float:
        """Compute MSE between original and reconstructed features."""
        f_hat = self.reconstruct(modality, features)
        return float(np.mean((features - f_hat) ** 2))

    def _get_decoder(self, modality: str):
        if modality == "vision" and self._visual_decoder:
            return self._visual_decoder
        if modality == "audio" and self._audio_decoder:
            return self._audio_decoder
        return None

    def _texture_forward(self, decoder: Any, latent: np.ndarray) -> tuple:
        """Forward texture branch with gradient cache. Returns (base_img, detail, cached_up, cached_windows)."""
        h = np.tanh(decoder._W_hidden @ latent + decoder._b_hidden)
        fm_flat = decoder._W_featmap @ h + decoder._b_featmap
        fm = fm_flat.reshape(
            decoder.TEXTURE_MAP_SIZE, decoder.TEXTURE_MAP_SIZE, decoder.TEXTURE_CHANNELS
        )

        H = W = decoder.INPUT_SIZE
        scale = decoder.INPUT_SIZE // decoder.TEXTURE_MAP_SIZE
        ms = decoder.TEXTURE_MAP_SIZE
        tc = decoder.TEXTURE_CHANNELS
        k_h, k_w = 5, 5
        pad_h, pad_w = k_h // 2, k_w // 2

        # Forward: projection branch (frozen) → base image
        raw = decoder._W @ latent + decoder._b
        spatial_feats = raw[: decoder.SPATIAL_FEATURES]
        color_feats = raw[
            decoder.SPATIAL_FEATURES : decoder.SPATIAL_FEATURES + decoder.COLOR_FEATURES
        ]
        base_img = decoder._layout_to_image(spatial_feats)
        base_img = decoder._apply_color_adjust(base_img, color_feats)

        detail = np.zeros((H, W, 3), dtype=np.float32)
        cached_up = np.zeros((H, W, tc), dtype=np.float32)
        cached_windows = {}
        for c_in in range(tc):
            up = np.repeat(np.repeat(fm[:, :, c_in], scale, axis=0), scale, axis=1)
            cached_up[:, :, c_in] = up

        for c_out in range(3):
            for c_in in range(tc):
                kernel = decoder._tex_kernels[c_out, c_in]
                padded = np.pad(
                    cached_up[:, :, c_in], ((pad_h, pad_h), (pad_w, pad_w)), mode="reflect"
                )
                windows = np.lib.stride_tricks.sliding_window_view(padded, (k_h, k_w))
                cached_windows[(c_out, c_in)] = windows
                conv = np.tensordot(windows, kernel, axes=((2, 3), (0, 1)))
                detail[:, :, c_out] += conv

        return base_img, detail, cached_up, cached_windows

    def _texture_backward(
        self,
        decoder: Any,
        latent: np.ndarray,
        h: np.ndarray,
        base_img: np.ndarray,
        detail: np.ndarray,
        target: np.ndarray,
        cached_windows: dict,
        d_W_hidden: np.ndarray,
        d_b_hidden: np.ndarray,
        d_W_featmap: np.ndarray,
        d_b_featmap: np.ndarray,
        d_tex_kernels: np.ndarray,
    ) -> float:
        """Backward pass for texture branch. Returns loss."""
        H = W = decoder.INPUT_SIZE
        ms = decoder.TEXTURE_MAP_SIZE
        tc = decoder.TEXTURE_CHANNELS
        k_h, k_w = 5, 5
        pad_h, pad_w = k_h // 2, k_w // 2

        output_img = np.clip(base_img + detail, 0, 255)
        diff = output_img - target
        loss = 0.5 * float(np.mean(diff**2))

        d_detail = diff / (H * W * 3)

        d_up_acc = np.zeros((H, W, tc), dtype=np.float32)
        for c_out in range(3):
            for c_in in range(tc):
                kernel = decoder._tex_kernels[c_out, c_in]
                windows = cached_windows[(c_out, c_in)]
                d_conv = d_detail[:, :, c_out]
                grad_k = np.tensordot(d_conv, windows, axes=((0, 1), (0, 1)))
                d_tex_kernels[c_out, c_in] += grad_k

                dL_dpadded = np.zeros((H + 2 * pad_h, W + 2 * pad_w), dtype=np.float32)
                for di in range(k_h):
                    for dj in range(k_w):
                        dL_dpadded[di : di + H, dj : dj + W] += d_conv * kernel[di, dj]
                d_up_acc[:, :, c_in] += dL_dpadded[pad_h:-pad_h, pad_w:-pad_w]

        d_fm = np.zeros((ms, ms, tc), dtype=np.float32)
        scale = decoder.INPUT_SIZE // decoder.TEXTURE_MAP_SIZE
        for c_in in range(tc):
            for i in range(ms):
                for j in range(ms):
                    block = d_up_acc[i * scale : (i + 1) * scale, j * scale : (j + 1) * scale, c_in]
                    d_fm[i, j, c_in] = np.sum(block)
        d_fm_flat = d_fm.reshape(-1)

        d_W_featmap += np.outer(d_fm_flat, h)
        d_b_featmap += d_fm_flat
        d_h = decoder._W_featmap.T @ d_fm_flat

        d_pre_act = d_h * (1.0 - h**2)
        d_W_hidden += np.outer(d_pre_act, latent)
        d_b_hidden += d_pre_act
        return loss

    def _apply_texture_gradients(
        self,
        decoder: Any,
        lr: float,
        d_W_hidden: np.ndarray,
        d_b_hidden: np.ndarray,
        d_W_featmap: np.ndarray,
        d_b_featmap: np.ndarray,
        d_tex_kernels: np.ndarray,
    ) -> None:
        """Apply gradient clipping and update texture weights."""
        max_norm = 10.0
        for g in [d_W_hidden, d_W_featmap, d_tex_kernels.reshape(-1)]:
            norm = np.sqrt(np.sum(g**2))
            if norm > max_norm:
                g *= max_norm / norm
        for g in [d_b_hidden, d_b_featmap]:
            norm = np.sqrt(np.sum(g**2))
            if norm > max_norm:
                g *= max_norm / norm

        decoder._W_hidden -= lr * d_W_hidden
        decoder._b_hidden -= lr * d_b_hidden
        decoder._W_featmap -= lr * d_W_featmap
        decoder._b_featmap -= lr * d_b_featmap
        decoder._tex_kernels -= lr * d_tex_kernels

    def train_texture_step(
        self, latents: np.ndarray, target_images: np.ndarray, lr: float = 0.001
    ) -> float:
        """Train VisualDecoder texture branch weights via pixel-level MSE.

        Takes a batch of (latent, target_image) pairs, runs the full decoder
        (projection + texture), and updates only the 5 texture weight arrays
        (W_hidden, b_hidden, W_featmap, b_featmap, tex_kernels).

        The projection branch weights (W, b) are FROZEN during this step.

        Args:
            latents: (B, 64) latent vectors
            target_images: (B, 128, 128, 3) target uint8 images, values in [0,255]
            lr: Learning rate for texture weights

        Returns:
            Average pixel-level MSE loss before update
        """
        decoder = self._visual_decoder
        if decoder is None or latents.size == 0:
            return 0.0

        B = latents.shape[0]
        H = W = decoder.INPUT_SIZE
        dtype = np.float32
        z = latents.astype(dtype)
        targets = target_images.astype(dtype)

        total_loss = 0.0

        d_W_hidden = np.zeros_like(decoder._W_hidden)
        d_b_hidden = np.zeros_like(decoder._b_hidden)
        d_W_featmap = np.zeros_like(decoder._W_featmap)
        d_b_featmap = np.zeros_like(decoder._b_featmap)
        d_tex_kernels = np.zeros_like(decoder._tex_kernels)

        for b in range(B):
            latent = z[b]
            target = targets[b]

            base_img, detail, cached_up, cached_windows = self._texture_forward(decoder, latent)
            h = np.tanh(decoder._W_hidden @ latent + decoder._b_hidden)

            loss = self._texture_backward(
                decoder,
                latent,
                h,
                base_img,
                detail,
                target,
                cached_windows,
                d_W_hidden,
                d_b_hidden,
                d_W_featmap,
                d_b_featmap,
                d_tex_kernels,
            )
            total_loss += loss

        n = max(B, 1)
        d_W_hidden /= n
        d_b_hidden /= n
        d_W_featmap /= n
        d_b_featmap /= n
        d_tex_kernels /= n

        self._apply_texture_gradients(
            decoder, lr, d_W_hidden, d_b_hidden, d_W_featmap, d_b_featmap, d_tex_kernels
        )

        return float(total_loss / n)

    @staticmethod
    def _init_wt_grads(decoder: Any) -> Dict[str, np.ndarray]:
        """Fresh gradient buffers for the 6 non-projection weight arrays."""
        return {
            "W_hidden": np.zeros_like(decoder._W_hidden),
            "b_hidden": np.zeros_like(decoder._b_hidden),
            "W_wavetable": np.zeros_like(decoder._W_wavetable),
            "b_wavetable": np.zeros_like(decoder._b_wavetable),
            "W_noise": np.zeros_like(decoder._W_noise),
            "b_noise": np.zeros_like(decoder._b_noise),
        }

    @staticmethod
    def _synthesize_bands(
        decoder: Any,
        spectral_env: np.ndarray,
        wavetables: np.ndarray,
        detail: np.ndarray,
        t: np.ndarray,
        n_samples: int,
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """Render all band wavetables + harmonics. Returns (waveform, band caches)."""
        waveform = np.zeros(n_samples, dtype=np.float32)
        cached_band_info: List[Dict[str, Any]] = []
        for band_idx, (lo, hi) in enumerate(decoder.BAND_LIMITS):
            wt = wavetables[band_idx]
            feats = spectral_env[
                band_idx
                * (len(spectral_env) // decoder.N_BANDS) : (band_idx + 1)
                * (len(spectral_env) // decoder.N_BANDS)
            ]
            freq_hz = 200.0 + np.abs(feats[:5]).mean() * (hi - lo) / 800.0
            freq_hz = np.clip(freq_hz, lo, hi)

            phase = np.cumsum(2 * np.pi * freq_hz / decoder.SAMPLE_RATE * np.ones(n_samples))
            phase = phase % (2 * np.pi)
            idx = (phase / (2 * np.pi) * decoder.WAVETABLE_SIZE).astype(
                int
            ) % decoder.WAVETABLE_SIZE
            band_wave = wt[idx].copy()

            d_start = band_idx * (len(detail) // decoder.N_BANDS)
            d_end = (band_idx + 1) * (len(detail) // decoder.N_BANDS)
            band_detail = detail[d_start:d_end] if d_end <= len(detail) else detail[d_start:]
            sin_terms: list = []
            for h_idx in range(min(decoder.N_HARMONICS // decoder.N_BANDS, len(band_detail) // 2)):
                amp = np.abs(band_detail[h_idx * 2]) / max(np.abs(band_detail).max(), 1e-8)
                amp = np.clip(amp, 0.0, 0.5)
                h_freq = freq_hz * (h_idx + 2)
                if h_freq < decoder.SAMPLE_RATE / 2:
                    st = np.sin(2 * np.pi * h_freq * t).astype(np.float32)
                    sin_terms.append(st)
                    band_wave += amp * st

            cached_band_info.append(
                {
                    "idx": idx.copy(),
                    "sin_terms": sin_terms,
                }
            )
            waveform += band_wave * (1.0 / decoder.N_BANDS)
        return waveform, cached_band_info

    @staticmethod
    def _build_envelope(temporal_env: np.ndarray, n_samples: int) -> np.ndarray:
        """Piecewise-constant amplitude envelope from temporal_env segments."""
        n_env = len(temporal_env)
        env_points = np.linspace(0, n_samples, n_env + 1).astype(int)
        envelope = np.zeros(n_samples, dtype=np.float32)
        for i in range(n_env):
            start = env_points[i]
            end = env_points[i + 1]
            val = np.clip(np.abs(temporal_env[i]), 0.0, 1.0)
            envelope[start:end] = val
        return envelope

    def _wavetable_forward(
        self, decoder: Any, latent: np.ndarray, n_samples: int
    ) -> Dict[str, Any]:
        """Full decoder forward for one sample (projection branch frozen).

        Returns cached intermediates for backward.
        """
        raw = decoder._W @ latent + decoder._b
        spectral_env = raw[:40]
        temporal_env = raw[40:50]
        detail = raw[50:]

        t = np.arange(n_samples, dtype=np.float32) / decoder.SAMPLE_RATE
        h = np.tanh(decoder._W_hidden @ latent + decoder._b_hidden)
        wt_flat = decoder._W_wavetable @ h + decoder._b_wavetable
        wavetables = wt_flat.reshape(decoder.N_BANDS, decoder.WAVETABLE_SIZE)

        noise_mod = decoder._W_noise @ h + decoder._b_noise
        noise_strength = float(np.clip(np.abs(np.mean(noise_mod)) * 0.01, 0, 0.15))

        waveform, cached_band_info = self._synthesize_bands(
            decoder, spectral_env, wavetables, detail, t, n_samples
        )

        noise_rng = np.random.default_rng(int(abs(float(noise_mod[0] * 1000)) % (2**31)))
        noise_signal = (
            noise_rng.normal(0, noise_strength, n_samples).astype(np.float32)
            if noise_strength >= 0.001
            else np.zeros(n_samples, dtype=np.float32)
        )
        waveform += noise_signal

        envelope = self._build_envelope(temporal_env, n_samples)
        waveform = waveform * envelope

        peak = max(np.abs(waveform).max(), 1e-8)
        output = waveform / peak
        return {
            "latent": latent,
            "h": h,
            "noise_mod": noise_mod,
            "noise_strength": noise_strength,
            "noise_signal": noise_signal,
            "envelope": envelope,
            "peak": peak,
            "output": output,
            "cached_band_info": cached_band_info,
        }

    def _wavetable_backward(
        self,
        decoder: Any,
        latent: np.ndarray,
        cache: Dict[str, Any],
        d_pre_env: np.ndarray,
        grads: Dict[str, np.ndarray],
    ) -> None:
        """Accumulate gradients for the 6 non-projection weight arrays."""
        cached_h = cache["h"]
        cached_band_info = cache["cached_band_info"]

        # Noise branch
        if cache["noise_strength"] >= 0.001:
            d_noise_strength = float(
                np.sum(d_pre_env * cache["noise_signal"] / max(cache["noise_strength"], 1e-8))
            )
            mean_nm = float(np.mean(cache["noise_mod"]))
            clip_val = abs(mean_nm) * 0.01
            if 0.001 < clip_val < 0.15:
                d_noise_mod = np.full(
                    16, d_noise_strength * 0.01 * np.sign(mean_nm) / 16.0, dtype=np.float32
                )
            else:
                d_noise_mod = np.zeros(16, dtype=np.float32)
            grads["W_noise"] += np.outer(d_noise_mod, cached_h)
            grads["b_noise"] += d_noise_mod
            d_h_noise = decoder._W_noise.T @ d_noise_mod
        else:
            d_h_noise = np.zeros(64, dtype=np.float32)

        # Wavetable lookup gradients (scatter-add per band)
        d_per_band = d_pre_env / decoder.N_BANDS
        d_wt_flat = np.zeros(decoder.N_BANDS * decoder.WAVETABLE_SIZE, dtype=np.float32)
        for band_idx in range(decoder.N_BANDS):
            idx = cached_band_info[band_idx]["idx"]
            wt_grad_band = np.zeros(decoder.WAVETABLE_SIZE, dtype=np.float32)
            np.add.at(wt_grad_band, idx, d_per_band)
            start = band_idx * decoder.WAVETABLE_SIZE
            end = (band_idx + 1) * decoder.WAVETABLE_SIZE
            d_wt_flat[start:end] = wt_grad_band

        grads["W_wavetable"] += np.outer(d_wt_flat, cached_h)
        grads["b_wavetable"] += d_wt_flat
        d_h = decoder._W_wavetable.T @ d_wt_flat + d_h_noise
        d_pre_hidden = d_h * (1.0 - cached_h**2)
        grads["W_hidden"] += np.outer(d_pre_hidden, latent)
        grads["b_hidden"] += d_pre_hidden

    @staticmethod
    def _clip_wt_gradients(grads: Dict[str, np.ndarray], max_norm: float = 10.0) -> None:
        """Gradient clipping (per-array norm-based, as before)."""
        for g in grads.values():
            norm = np.sqrt(np.sum(g**2))
            if norm > max_norm:
                g *= max_norm / norm

    @staticmethod
    def _apply_wt_updates(decoder: Any, lr: float, grads: Dict[str, np.ndarray]) -> None:
        """Apply all six weight updates at once."""
        decoder._W_hidden -= lr * grads["W_hidden"]
        decoder._b_hidden -= lr * grads["b_hidden"]
        decoder._W_wavetable -= lr * grads["W_wavetable"]
        decoder._b_wavetable -= lr * grads["b_wavetable"]
        decoder._W_noise -= lr * grads["W_noise"]
        decoder._b_noise -= lr * grads["b_noise"]

    def train_wavetable_step(
        self, latents: np.ndarray, target_waveforms: np.ndarray, lr: float = 0.001
    ) -> float:
        """Train AudioWaveformDecoder wavetable + hidden weights via waveform MSE.

        Takes a batch of (latent, target_waveform) pairs, runs the full decoder
        (projection + wavetable + noise + envelope), and updates the 6 non-projection
        weight arrays (W_hidden, b_hidden, W_wavetable, b_wavetable, W_noise, b_noise).

        The projection branch weights (W, b) are FROZEN during this step.

        Args:
            latents: (B, 64) latent vectors
            target_waveforms: (B, N) target waveform arrays, where N = SAMPLE_RATE * DURATION
            lr: Learning rate for wavetable + hidden weights

        Returns:
            Average waveform MSE loss before update
        """
        decoder = self._audio_decoder
        if decoder is None or latents.size == 0:
            return 0.0

        B = latents.shape[0]
        z = latents.astype(np.float32)
        targets = target_waveforms.astype(np.float32)
        n_samples = int(decoder.SAMPLE_RATE * decoder.DURATION)

        total_loss = 0.0
        grads = self._init_wt_grads(decoder)

        for b in range(B):
            latent = z[b]
            target = targets[b]

            cache = self._wavetable_forward(decoder, latent, n_samples)
            diff = cache["output"] - target
            total_loss += 0.5 * float(np.mean(diff**2))

            # Backward (unscaled MSE → envelope → peak norm)
            d_output = diff / n_samples
            d_pre_norm = d_output / cache["peak"]
            d_pre_env = d_pre_norm * cache["envelope"]
            self._wavetable_backward(decoder, latent, cache, d_pre_env, grads)

        n = max(B, 1)
        for g in grads.values():
            g /= n

        self._clip_wt_gradients(grads)
        self._apply_wt_updates(decoder, lr, grads)

        return float(total_loss / n)


class CrossModalSynthesizer:
    """Cross-modal latent blending and generation.

    Takes latents from different modalities, blends them, and decodes
    into any target modality.
    """

    def __init__(
        self,
        latent_space: SharedLatentSpace,
        visual_decoder: Optional[VisualDecoder] = None,
        audio_decoder: Optional[AudioWaveformDecoder] = None,
    ):
        self._ls = latent_space
        self._visual_decoder = visual_decoder
        self._audio_decoder = audio_decoder

    def blend_latents(
        self, modalities: List[Tuple[str, np.ndarray]], weights: Optional[List[float]] = None
    ) -> np.ndarray:
        """Blend multiple modality latents into a single latent vector.

        Args:
            modalities: List of (modality_name, feature_vector) pairs
            weights: Optional blend weights (default: equal)

        Returns:
            Blended 64-dim latent vector
        """
        n = len(modalities)
        if n == 0:
            return np.zeros(self._ls._latent_dim, dtype=np.float32)
        if weights is None:
            weights = [1.0 / n] * n
        w_sum = sum(weights)
        weights = [w / w_sum for w in weights]

        blended = np.zeros(self._ls._latent_dim, dtype=np.float32)
        for (mod, feat), w in zip(modalities, weights):
            z = self._ls.project(mod, feat)
            blended += w * z
        return blended

    def generate_image(self, latent: np.ndarray) -> np.ndarray:
        """Generate an image from a latent vector (or blended latent)."""
        if self._visual_decoder is None:
            return np.zeros((128, 128, 3), dtype=np.uint8)
        return self._visual_decoder.decode(latent)

    def generate_audio(self, latent: np.ndarray) -> np.ndarray:
        """Generate audio waveform from a latent vector (or blended latent)."""
        if self._audio_decoder is None:
            return np.array([], dtype=np.float32)
        return self._audio_decoder.decode(latent)

    def cross_generate(
        self, source_modality: str, source_features: np.ndarray, target_modality: str
    ) -> np.ndarray:
        """Encode source modality and decode into target modality.

        E.g., encode an image → decode as audio (vision→audio).
        """
        z = self._ls.project(source_modality, source_features)
        if target_modality == "vision" or target_modality == "image":
            return self.generate_image(z)
        elif target_modality == "audio" or target_modality == "waveform":
            return self.generate_audio(z)
        return np.array([])
