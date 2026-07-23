"""Visual encoder — real pixel-to-feature-vector extraction using numpy.

P17: Added CNN conv2d filter banks (Gabor-like edge detectors at multiple
orientations and scales) to enrich feature extraction before handcrafted
features. Dimension increased from 128 to 256.
"""

import io
import logging
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class VisualEncoder:
    """Encodes image pixels into a fixed-size feature vector using numpy.

    Feature pipeline:
      1. CNN filter banks (4 orientations × 2 scales = 8 filters) → 256-dim activation map stats
      2. Color histogram (per-channel, 32 bins × 3 = 96)
      3. Edge orientation histogram (8 bins)
      4. Texture statistics (contrast, energy, homogeneity)
      5. Spatial layout (4-region color means = 4×3 = 12)
      Total: 256-dim (CNN stats 128 + handcrafted 119 + padding)
    """

    INPUT_SIZE: int = 128
    FEATURE_DIM: int = 256
    COLOR_BINS: int = 32
    EDGE_BINS: int = 8
    SPATIAL_REGIONS: int = 4
    CNN_FILTER_SIZE: int = 7
    CNN_STRIDE: int = 4
    CNN_N_ORIENTATIONS: int = 4
    CNN_N_SCALES: int = 2
    CNN_FEATURE_DIM: int = 128

    def __init__(self, feature_dim: Optional[int] = None):
        self._feature_dim = feature_dim or self.FEATURE_DIM
        self._projection: Optional[np.ndarray] = None
        self._cnn_filters: Optional[np.ndarray] = None

    def _build_filters(self) -> np.ndarray:
        """Build Gabor-like filter bank: (N, H, W) where N = orientations × scales."""
        if self._cnn_filters is not None:
            return self._cnn_filters
        filters = []
        fs = self.CNN_FILTER_SIZE
        center = fs // 2
        for scale in range(1, self.CNN_N_SCALES + 1):
            sigma = scale * 2.0
            for orient in range(self.CNN_N_ORIENTATIONS):
                theta = orient * np.pi / self.CNN_N_ORIENTATIONS
                kernel = np.zeros((fs, fs), dtype=np.float32)
                for y in range(fs):
                    for x in range(fs):
                        dx = x - center
                        dy = y - center
                        rx = dx * np.cos(theta) + dy * np.sin(theta)
                        ry = -dx * np.sin(theta) + dy * np.cos(theta)
                        kernel[y, x] = np.exp(-0.5 * (rx**2 + ry**2) / sigma**2) * np.cos(
                            2 * np.pi * rx / (sigma * 2)
                        )
                kernel -= kernel.mean()
                kernel /= np.sqrt(np.sum(kernel**2)) + 1e-8
                filters.append(kernel)
        self._cnn_filters = np.stack(filters)
        return self._cnn_filters

    def _conv2d(self, img: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        """Vectorized 2D convolution using sliding window view."""
        k_h, k_w = kernel.shape
        s = self.CNN_STRIDE
        windows = np.lib.stride_tricks.sliding_window_view(img, (k_h, k_w))[::s, ::s]
        return np.tensordot(windows, kernel, axes=2)

    def _cnn_features(self, arr: np.ndarray) -> np.ndarray:
        """Apply CNN filter bank and return pooled statistics as feature vector.

        Vectorized: all filters applied simultaneously via batched convolution.
        """
        gray = np.mean(arr, axis=2)
        filters = self._build_filters()  # (N, fs, fs)
        k_h, k_w = filters.shape[1], filters.shape[2]
        s = self.CNN_STRIDE
        windows = np.lib.stride_tricks.sliding_window_view(gray, (k_h, k_w))[::s, ::s]
        n_win_h, n_win_w = windows.shape[0], windows.shape[1]
        flats = windows.reshape(n_win_h * n_win_w, k_h * k_w)
        flat_filters = filters.reshape(filters.shape[0], -1)  # (N, k_h*k_w)
        activations_2d = flats @ flat_filters.T  # (n_windows, N)
        activations_2d = activations_2d.reshape(n_win_h, n_win_w, -1)  # (H, W, N)

        activations = []
        for k in range(filters.shape[0]):
            fm = activations_2d[:, :, k]
            activations.extend(
                [
                    float(fm.mean()),
                    float(fm.std()),
                    float(np.max(fm)),
                    float(np.percentile(fm, 25)),
                    float(np.percentile(fm, 75)),
                    float(np.mean(np.abs(fm))),
                    float(np.sqrt(np.mean(fm**2))),
                    float(np.sum(fm > 0) / max(fm.size, 1)),
                ]
            )
        vec = np.array(activations, dtype=np.float32)
        target = self.CNN_FEATURE_DIM
        if len(vec) >= target:
            return vec[:target]
        padded = np.zeros(target, dtype=np.float32)
        padded[: len(vec)] = vec
        return padded

    def encode(self, image_data: bytes) -> np.ndarray:
        """Encode raw image bytes into a feature vector."""
        try:
            img = Image.open(io.BytesIO(image_data)).convert("RGB")
            return self.encode_from_pil(img)
        except Exception as e:
            logger.warning("VisualEncoder failed: %s", e, exc_info=True)
            return np.zeros(self._feature_dim, dtype=np.float32)

    def encode_from_pil(self, img: Image.Image) -> np.ndarray:
        """Encode a PIL Image into a feature vector."""
        img = img.resize((self.INPUT_SIZE, self.INPUT_SIZE), Image.LANCZOS)
        arr = np.asarray(img, dtype=np.float32)

        features = []
        features.extend(self._cnn_features(arr).tolist())
        features.extend(self._color_histogram(arr))
        features.extend(self._edge_histogram(arr))
        features.extend(self._texture_stats(arr))
        features.extend(self._spatial_layout(arr))

        raw = np.array(features, dtype=np.float32)
        return self._project_if_needed(raw)

    def _color_histogram(self, arr: np.ndarray) -> list:
        """Per-channel color histogram (32 bins per channel)."""
        hist = []
        for c in range(3):
            channel = arr[:, :, c]
            h, _ = np.histogram(channel, bins=self.COLOR_BINS, range=(0, 255))
            hist.extend(h.astype(np.float32) / h.sum() if h.sum() > 0 else h)
        return hist

    def _edge_histogram(self, arr: np.ndarray) -> list:
        """Edge orientation histogram via Sobel magnitude."""
        gray = np.mean(arr, axis=2)
        gx = np.gradient(gray, axis=1)
        gy = np.gradient(gray, axis=0)
        mag = np.sqrt(gx**2 + gy**2)
        ang = np.arctan2(gy, gx) + np.pi
        bin_idx = (ang / (2 * np.pi) * self.EDGE_BINS).astype(int) % self.EDGE_BINS
        hist = np.zeros(self.EDGE_BINS, dtype=np.float32)
        for b in range(self.EDGE_BINS):
            hist[b] = mag[bin_idx == b].sum()
        total = hist.sum()
        if total > 0:
            hist = hist / total
        else:
            hist[:] = 1.0 / self.EDGE_BINS
        return hist.tolist()

    def _texture_stats(self, arr: np.ndarray) -> list:
        """Simple texture statistics from co-occurrence approximation."""
        gray = np.mean(arr, axis=2).astype(np.uint8)
        diff_h = np.abs(np.diff(gray, axis=1)).astype(np.float32)
        diff_v = np.abs(np.diff(gray, axis=0)).astype(np.float32)
        contrast = float(np.mean(diff_h) + np.mean(diff_v)) / 2
        energy = float(np.mean(np.exp(-diff_h / 16)) + np.mean(np.exp(-diff_v / 16))) / 2
        homogeneity = float(np.mean(1 / (1 + diff_h)) + np.mean(1 / (1 + diff_v))) / 2
        return [contrast, energy, homogeneity]

    def _spatial_layout(self, arr: np.ndarray) -> list:
        """Divide image into SPATIAL_REGIONS blocks and compute mean color per block."""
        h, w, _ = arr.shape
        regions_per_side = int(np.sqrt(self.SPATIAL_REGIONS))
        region_h = h // regions_per_side
        region_w = w // regions_per_side
        features = []
        for r in range(regions_per_side):
            for c_ in range(regions_per_side):
                block = arr[r * region_h : (r + 1) * region_h, c_ * region_w : (c_ + 1) * region_w]
                features.extend(block.mean(axis=(0, 1)).tolist())
        return features

    def _project_if_needed(self, raw: np.ndarray) -> np.ndarray:
        """Project to FEATURE_DIM or pad if raw is smaller."""
        if len(raw) == self._feature_dim:
            return raw
        if len(raw) < self._feature_dim:
            padded = np.zeros(self._feature_dim, dtype=np.float32)
            padded[: len(raw)] = raw
            return padded
        if self._projection is None or self._projection.shape[1] != len(raw):
            rng = np.random.default_rng(42)
            self._projection = rng.normal(
                0, 1 / np.sqrt(len(raw)), (self._feature_dim, len(raw))
            ).astype(np.float32)
        return self._projection @ raw

    def train_step(self, image_data: bytes, target_latent: np.ndarray, lr: float = 0.001) -> float:
        """Train the projection matrix to map image features to target latent.

        Uses MSE loss between projected features and target latent vector.
        Updates self._projection via gradient descent.

        Args:
            image_data: Raw image bytes
            target_latent: Target latent vector (64-dim)
            lr: Learning rate

        Returns:
            Training loss (MSE)
        """
        # Encode image to get raw features
        features = self._extract_features(image_data)
        if features is None or np.all(features == 0):
            return 0.0

        # Project to feature space
        projected = self._project(features)

        # Compute loss: MSE between projected and target
        diff = projected - target_latent[: self._feature_dim]
        loss = float(np.mean(diff**2))

        # Gradient: d(loss)/d(projection) = 2 * diff @ features.T
        # Update projection: W -= lr * grad
        grad = 2.0 * np.outer(diff, features) / self._feature_dim
        self._projection -= lr * grad

        # Gradient clipping
        norm = np.linalg.norm(self._projection)
        if norm > 10.0:
            self._projection = self._projection / (norm / 10.0)

        return loss

    def reset_projection(self) -> None:
        self._projection = None
        self._cnn_filters = None
