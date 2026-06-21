"""Visual encoder — real pixel-to-feature-vector extraction using numpy."""

import io
import logging
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class VisualEncoder:
    """Encodes image pixels into a fixed-size feature vector using numpy.

    Extracts multi-level visual features:
      - Color histogram (per-channel, 32 bins × 3 = 96)
      - Edge orientation histogram (8 bins)
      - Texture statistics (contrast, energy, homogeneity)
      - Spatial layout (4-region color means, 4×3×3 = 36)
      Total: ~148 dimensions, optionally PCA-reduced to 128.
    """

    INPUT_SIZE: int = 128
    FEATURE_DIM: int = 128
    COLOR_BINS: int = 32
    EDGE_BINS: int = 8
    SPATIAL_REGIONS: int = 4

    def __init__(self, feature_dim: Optional[int] = None):
        self._feature_dim = feature_dim or self.FEATURE_DIM
        self._projection: Optional[np.ndarray] = None
        self._count = 0

    def encode(self, image_data: bytes) -> np.ndarray:
        """Encode raw image bytes into a feature vector."""
        try:
            img = Image.open(io.BytesIO(image_data)).convert("RGB")
            return self.encode_from_pil(img)
        except Exception as e:
            logger.debug("VisualEncoder failed: %s", e)
            return np.zeros(self._feature_dim, dtype=np.float32)

    def encode_from_pil(self, img: Image.Image) -> np.ndarray:
        """Encode a PIL Image into a feature vector."""
        img = img.resize((self.INPUT_SIZE, self.INPUT_SIZE), Image.LANCZOS)
        arr = np.asarray(img, dtype=np.float32)

        features = []
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
        mag = np.sqrt(gx ** 2 + gy ** 2)
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
                block = arr[r * region_h:(r + 1) * region_h,
                            c_ * region_w:(c_ + 1) * region_w]
                features.extend(block.mean(axis=(0, 1)).tolist())
        return features

    def _project_if_needed(self, raw: np.ndarray) -> np.ndarray:
        """Project to FEATURE_DIM or pad if raw is smaller."""
        if len(raw) == self._feature_dim:
            return raw
        if len(raw) < self._feature_dim:
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

    def reset_projection(self) -> None:
        self._projection = None
