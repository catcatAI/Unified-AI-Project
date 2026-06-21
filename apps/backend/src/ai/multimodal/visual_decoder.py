"""Visual decoder — latent vector → RGB image generation using numpy.

P24: CNN texture detail via transposed convolution from hidden features.
"""

import logging
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class VisualDecoder:
    """Decodes a 64-dim latent vector into a 128×128 RGB image.

    Pipeline:
      1. Linear projection Wx+b → 256-dim (trained by ReconstructionCycle)
      2. CNN texture branch: tanh hidden → 4×4×16 feature map → transposed conv → 128×128 detail
      3. Split features: spatial layout (12) + color histogram (96) + reserved (148)
      4. Reconstruct image from layout → upscale → color → CNN texture detail
    """

    INPUT_SIZE: int = 128
    LATENT_DIM: int = 64
    FEATURE_DIM: int = 256
    OUTPUT_CHANNELS: int = 3
    SPATIAL_FEATURES: int = 12
    COLOR_FEATURES: int = 96
    HIDDEN_DIM: int = 64
    TEXTURE_MAP_SIZE: int = 4
    TEXTURE_CHANNELS: int = 16

    def __init__(self):
        rng = np.random.default_rng(42)
        scale = 1.0 / np.sqrt(self.LATENT_DIM)
        self._W = rng.normal(0, scale, (self.FEATURE_DIM, self.LATENT_DIM)).astype(np.float32)
        self._b = np.zeros(self.FEATURE_DIM, dtype=np.float32)
        # CNN texture branch: latent → hidden → 4×4×16 feature map
        h_scale = 1.0 / np.sqrt(self.LATENT_DIM)
        self._W_hidden = rng.normal(0, h_scale, (self.HIDDEN_DIM, self.LATENT_DIM)).astype(np.float32)
        self._b_hidden = np.zeros(self.HIDDEN_DIM, dtype=np.float32)
        self._W_featmap = rng.normal(0, 1.0 / np.sqrt(self.HIDDEN_DIM),
                                     (self.TEXTURE_MAP_SIZE * self.TEXTURE_MAP_SIZE * self.TEXTURE_CHANNELS,
                                      self.HIDDEN_DIM)).astype(np.float32)
        self._b_featmap = np.zeros(self.TEXTURE_MAP_SIZE * self.TEXTURE_MAP_SIZE * self.TEXTURE_CHANNELS,
                                   dtype=np.float32)
        # Transposed conv kernels (one per output channel × texture channel)
        self._tex_kernels = rng.normal(0, 0.1,
                                       (3, self.TEXTURE_CHANNELS, 5, 5)).astype(np.float32)

    def decode(self, latent: np.ndarray) -> np.ndarray:
        """Decode latent vector into 128×128×3 RGB uint8 array."""
        if len(latent) != self.LATENT_DIM:
            logger.warning("Expected latent dim %d, got %d", self.LATENT_DIM, len(latent))
            return np.zeros((self.INPUT_SIZE, self.INPUT_SIZE, 3), dtype=np.uint8)

        raw = self._W @ latent + self._b
        spatial_feats = raw[:self.SPATIAL_FEATURES]
        color_feats = raw[self.SPATIAL_FEATURES:self.SPATIAL_FEATURES + self.COLOR_FEATURES]

        img = self._layout_to_image(spatial_feats)
        img = self._apply_color_adjust(img, color_feats)
        texture = self._synthesize_texture(latent)
        img = img + texture
        img = np.clip(img, 0, 255).astype(np.uint8)
        return img

    def decode_to_pil(self, latent: np.ndarray) -> Image.Image:
        """Decode latent vector to PIL Image."""
        arr = self.decode(latent)
        return Image.fromarray(arr, "RGB")

    def _layout_to_image(self, spatial_feats: np.ndarray) -> np.ndarray:
        """Convert spatial layout features (12) to 128×128 image via grid upsampling."""
        grid_size = 2
        cell_h = self.INPUT_SIZE // grid_size
        cell_w = self.INPUT_SIZE // grid_size
        img = np.zeros((self.INPUT_SIZE, self.INPUT_SIZE, 3), dtype=np.float32)
        idx = 0
        for r in range(grid_size):
            for c in range(grid_size):
                rgb = spatial_feats[idx:idx + 3]
                rng = rgb.max() - rgb.min()
                rgb = (rgb - rgb.min()) / max(rng, 1e-8) * 255
                img[r * cell_h:(r + 1) * cell_h, c * cell_w:(c + 1) * cell_w] = rgb.reshape(1, 1, 3)
                idx += 3
        return img

    def _apply_color_adjust(self, img: np.ndarray, color_feats: np.ndarray) -> np.ndarray:
        """Apply per-channel contrast/brightness adjustment from histogram features."""
        for c in range(3):
            channel = img[:, :, c].astype(np.float32)
            mean_val = float(channel.mean())
            feat_slice = color_feats[c * 32:(c + 1) * 32]
            contrast = float(np.std(feat_slice))
            brightness = float(np.mean(feat_slice))
            contrast = np.clip(contrast * 0.3 + 0.7, 0.3, 2.0)
            brightness = np.clip(brightness * 0.1 + 0.5, 0.3, 0.9)
            channel = (channel - mean_val) * contrast + mean_val * brightness
            img[:, :, c] = channel
        return img

    def _synthesize_texture(self, latent: np.ndarray) -> np.ndarray:
        """Generate texture detail via transposed convolution on a 4×4 feature map.

        Creates structured spatial patterns (edges, gradients, blobs) from the
        hidden layer output, producing richer texture than random noise.
        """
        h = np.tanh(self._W_hidden @ latent + self._b_hidden)
        feat_map_flat = self._W_featmap @ h + self._b_featmap
        feat_map = feat_map_flat.reshape(self.TEXTURE_MAP_SIZE, self.TEXTURE_MAP_SIZE,
                                         self.TEXTURE_CHANNELS)

        # Transposed conv: upsample 4×4×16 → 128×128×3
        scale = self.INPUT_SIZE // self.TEXTURE_MAP_SIZE
        detail = np.zeros((self.INPUT_SIZE, self.INPUT_SIZE, 3), dtype=np.float32)
        for c_out in range(3):
            for c_in in range(self.TEXTURE_CHANNELS):
                kernel = self._tex_kernels[c_out, c_in]
                # Nearest-neighbor upsample + convolution
                up = np.repeat(np.repeat(feat_map[:, :, c_in], scale, axis=0), scale, axis=1)
                conv = self._conv2d_same(up, kernel)
                detail[:, :, c_out] += conv
        return detail

    @staticmethod
    def _conv2d_same(x: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        """Vectorized 2D convolution with 'same' output size via sliding_window_view."""
        k_h, k_w = kernel.shape
        pad_h = k_h // 2
        pad_w = k_w // 2
        padded = np.pad(x, ((pad_h, pad_h), (pad_w, pad_w)), mode='reflect')
        windows = np.lib.stride_tricks.sliding_window_view(padded, (k_h, k_w))
        return np.tensordot(windows, kernel, axes=((2, 3), (0, 1)))

    def get_projection(self) -> np.ndarray:
        return self._W.copy()

    def set_projection(self, W: np.ndarray) -> None:
        if W.shape == self._W.shape:
            self._W = W.astype(np.float32)