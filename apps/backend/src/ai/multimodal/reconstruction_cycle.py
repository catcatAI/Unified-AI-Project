"""Reconstruction cycle + cross-modal synthesis — autoencoder train loop and cross-modal generation.

P19: Closes the encoder→latent→decoder→encoder reconstruction loop with
feature-level MSE training, and enables cross-modal latent blending.
"""

import logging
from typing import Dict, List, Optional, Tuple

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

    def __init__(self, latent_space: SharedLatentSpace,
                 visual_decoder: Optional[VisualDecoder] = None,
                 audio_decoder: Optional[AudioWaveformDecoder] = None):
        self._ls = latent_space
        self._visual_decoder = visual_decoder
        self._audio_decoder = audio_decoder

    def train_step(self, modality: str, features: np.ndarray,
                   lr: float = 0.01) -> float:
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
            norm = np.sqrt(np.sum(g ** 2))
            if norm > max_norm:
                g *= max_norm / norm
        for g in [grad_b_d, grad_b_e]:
            norm = np.sqrt(np.sum(g ** 2))
            if norm > max_norm:
                g *= max_norm / norm

        W_d -= lr * grad_W_d
        b_d -= lr * grad_b_d
        W_e -= lr * grad_W_e
        b_e -= lr * grad_b_e

        return loss

    def train(self, modality: str, features_list: List[np.ndarray],
              epochs: int = 20, lr: float = 0.005) -> Dict:
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
        return f_hat

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

    def train_texture_step(self, latents: np.ndarray,
                           target_images: np.ndarray,
                           lr: float = 0.001) -> float:
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

        # Accumulate gradient buffers
        d_W_hidden = np.zeros_like(decoder._W_hidden)
        d_b_hidden = np.zeros_like(decoder._b_hidden)
        d_W_featmap = np.zeros_like(decoder._W_featmap)
        d_b_featmap = np.zeros_like(decoder._b_featmap)
        d_tex_kernels = np.zeros_like(decoder._tex_kernels)

        for b in range(B):
            latent = z[b]
            target = targets[b]  # (128, 128, 3)

            # 1. Forward: projection branch (frozen) → base image
            raw = decoder._W @ latent + decoder._b
            spatial_feats = raw[:decoder.SPATIAL_FEATURES]
            color_feats = raw[decoder.SPATIAL_FEATURES:
                              decoder.SPATIAL_FEATURES + decoder.COLOR_FEATURES]
            base_img = decoder._layout_to_image(spatial_feats)
            base_img = decoder._apply_color_adjust(base_img, color_feats)

            # 2. Forward: texture branch with gradient cache
            h = np.tanh(decoder._W_hidden @ latent + decoder._b_hidden)  # (64,)
            fm_flat = decoder._W_featmap @ h + decoder._b_featmap  # (256,)
            fm = fm_flat.reshape(decoder.TEXTURE_MAP_SIZE,
                                 decoder.TEXTURE_MAP_SIZE,
                                 decoder.TEXTURE_CHANNELS)  # (4, 4, 16)

            scale = decoder.INPUT_SIZE // decoder.TEXTURE_MAP_SIZE  # 32
            ms = decoder.TEXTURE_MAP_SIZE  # 4
            tc = decoder.TEXTURE_CHANNELS  # 16
            k_h, k_w = 5, 5
            pad_h, pad_w = k_h // 2, k_w // 2  # 2, 2

            detail = np.zeros((H, W, 3), dtype=dtype)
            cached_up = np.zeros((H, W, tc), dtype=dtype)
            cached_windows = {}  # (c_out, c_in) → windows for gradient
            for c_in in range(tc):
                up = np.repeat(np.repeat(fm[:, :, c_in], scale, axis=0), scale, axis=1)
                cached_up[:, :, c_in] = up

            for c_out in range(3):
                for c_in in range(tc):
                    kernel = decoder._tex_kernels[c_out, c_in]
                    padded = np.pad(cached_up[:, :, c_in],
                                    ((pad_h, pad_h), (pad_w, pad_w)), mode='reflect')
                    windows = np.lib.stride_tricks.sliding_window_view(padded, (k_h, k_w))
                    cached_windows[(c_out, c_in)] = windows
                    conv = np.tensordot(windows, kernel, axes=((2, 3), (0, 1)))
                    detail[:, :, c_out] += conv

            output_img = base_img + detail  # (128, 128, 3)
            output_img = np.clip(output_img, 0, 255)

            # 3. Pixel-level MSE loss
            diff = output_img - target
            loss = 0.5 * float(np.mean(diff ** 2))
            total_loss += loss

            # 4. Backward: gradient of loss wrt detail
            d_detail = diff / (H * W * 3)  # mean reduction: gradient = diff / N

            # 5. Backward through transposed conv for each (c_out, c_in)
            d_up_acc = np.zeros((H, W, tc), dtype=dtype)
            for c_out in range(3):
                for c_in in range(tc):
                    kernel = decoder._tex_kernels[c_out, c_in]
                    windows = cached_windows[(c_out, c_in)]
                    d_conv = d_detail[:, :, c_out]  # (128, 128)

                    # Gradient wrt kernel: dL/dkernel[c_out,c_in]
                    grad_k = np.tensordot(d_conv, windows, axes=((0, 1), (0, 1)))
                    d_tex_kernels[c_out, c_in] += grad_k

                    # Gradient wrt up (through conv): accumulate over c_out
                    dL_dpadded = np.zeros((H + 2 * pad_h, W + 2 * pad_w), dtype=dtype)
                    for di in range(k_h):
                        for dj in range(k_w):
                            dL_dpadded[di:di + H, dj:dj + W] += d_conv * kernel[di, dj]
                    d_up_acc[:, :, c_in] += dL_dpadded[pad_h:-pad_h, pad_w:-pad_w]

            # 6. Backward through nearest-neighbor upsample
            d_fm = np.zeros((ms, ms, tc), dtype=dtype)
            for c_in in range(tc):
                for i in range(ms):
                    for j in range(ms):
                        block = d_up_acc[i * scale:(i + 1) * scale,
                                         j * scale:(j + 1) * scale, c_in]
                        d_fm[i, j, c_in] = np.sum(block)
            d_fm_flat = d_fm.reshape(-1)  # (256,)

            # 7. Backward through linear: f = W_featmap @ h + b_featmap
            d_W_featmap += np.outer(d_fm_flat, h)
            d_b_featmap += d_fm_flat
            d_h = decoder._W_featmap.T @ d_fm_flat  # (64,)

            # 8. Backward through tanh: h = tanh(W_hidden @ z + b_hidden)
            d_pre_act = d_h * (1.0 - h ** 2)  # (64,)
            d_W_hidden += np.outer(d_pre_act, latent)
            d_b_hidden += d_pre_act

        # Average gradients over batch
        n = max(B, 1)
        d_W_hidden /= n
        d_b_hidden /= n
        d_W_featmap /= n
        d_b_featmap /= n
        d_tex_kernels /= n

        # Gradient clipping (norm-based)
        max_norm = 10.0
        for g in [d_W_hidden, d_W_featmap, d_tex_kernels.reshape(-1)]:
            norm = np.sqrt(np.sum(g ** 2))
            if norm > max_norm:
                g *= max_norm / norm
        for g in [d_b_hidden, d_b_featmap]:
            norm = np.sqrt(np.sum(g ** 2))
            if norm > max_norm:
                g *= max_norm / norm

        # Update texture weights
        decoder._W_hidden -= lr * d_W_hidden
        decoder._b_hidden -= lr * d_b_hidden
        decoder._W_featmap -= lr * d_W_featmap
        decoder._b_featmap -= lr * d_b_featmap
        decoder._tex_kernels -= lr * d_tex_kernels

        return total_loss / n


class CrossModalSynthesizer:
    """Cross-modal latent blending and generation.

    Takes latents from different modalities, blends them, and decodes
    into any target modality.
    """

    def __init__(self, latent_space: SharedLatentSpace,
                 visual_decoder: Optional[VisualDecoder] = None,
                 audio_decoder: Optional[AudioWaveformDecoder] = None):
        self._ls = latent_space
        self._visual_decoder = visual_decoder
        self._audio_decoder = audio_decoder

    def blend_latents(self, modalities: List[Tuple[str, np.ndarray]],
                      weights: Optional[List[float]] = None) -> np.ndarray:
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

    def cross_generate(self, source_modality: str, source_features: np.ndarray,
                       target_modality: str) -> np.ndarray:
        """Encode source modality and decode into target modality.

        E.g., encode an image → decode as audio (vision→audio).
        """
        z = self._ls.project(source_modality, source_features)
        if target_modality == "vision" or target_modality == "image":
            return self.generate_image(z)
        elif target_modality == "audio" or target_modality == "waveform":
            return self.generate_audio(z)
        return np.array([])