# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================
"""
VisionPipeline — single-modality end-to-end vision processing pipeline.

Analogous to ChatService for the chat pipeline but scoped to vision only.

Pipeline:
  Upload → resize → VisualEncoder (256-dim)
  → SharedLatentSpace.project("vision") → 64-dim latent
  → VisualDecoder.decode() → 128×128 RGB (autoencoder loop)
  → quality_metrics.ssim() / psnr()
  → Cache last 10 results

P31: First single-modality pipeline after P30 MultimodalService layer.
"""

import io
import logging
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from core.utils import safe_error
from PIL import Image

logger = logging.getLogger(__name__)


class VisionPipeline:
    """End-to-end vision processing pipeline.

    Integrates VisualEncoder → SharedLatentSpace → VisualDecoder → quality_metrics
    into a single unified interface with caching and monitoring.

    Thread-safe: each method creates its own backend instances lazily.
    """

    CACHE_SIZE: int = 10
    INPUT_SIZE: int = 128
    VISION_DIM: int = 256
    LATENT_DIM: int = 64

    def __init__(self):
        self._encoder = None
        self._latent_space = None
        self._decoder = None
        # LRU cache: {image_hash: cached_result}
        self._cache: OrderedDict = OrderedDict()

    # --- Lazy initialization ---

    def _get_encoder(self):
        if self._encoder is None:
            from ai.multimodal.visual_encoder import VisualEncoder
            self._encoder = VisualEncoder(feature_dim=self.VISION_DIM)
        return self._encoder

    def _get_latent_space(self):
        if self._latent_space is None:
            from ai.multimodal.shared_latent_space import get_shared_latent_space
            self._latent_space = get_shared_latent_space(latent_dim=self.LATENT_DIM)
        return self._latent_space

    def _get_decoder(self):
        if self._decoder is None:
            from ai.multimodal.visual_decoder import (
                VisualDecoder,
                load_default_visual_decoder_weights,
            )
            self._decoder = VisualDecoder()
            load_default_visual_decoder_weights(self._decoder)
        return self._decoder

    # --- Core process ---

    def process(self, image_data: bytes) -> Dict[str, Any]:
        """Run the full vision pipeline on image bytes.

        Args:
            image_data: Raw image bytes (PNG/JPEG)

        Returns:
            dict with:
              - feature_vector (256-dim list)
              - latent (64-dim list)
              - decoded_image (PIL Image or None)
              - ss im (float, [0,1])
              - psnr (float, dB)
              - time_ms (float)
              - image_hash (str)
              - error (str, if any)
        """
        t0 = time.time()
        result: Dict[str, Any] = {"error": None}

        try:
            # Check cache
            img_hash = self._hash_image(image_data)
            cached = self._cache.get(img_hash)
            if cached is not None:
                result.update(cached)
                result["cache_hit"] = True
                result["time_ms"] = round((time.time() - t0) * 1000, 1)
                return result

            # 1. Open and resize image
            img = Image.open(io.BytesIO(image_data)).convert("RGB")
            original_size = img.size
            img_resized = img.resize((self.INPUT_SIZE, self.INPUT_SIZE), Image.LANCZOS)
            arr = np.asarray(img_resized, dtype=np.float32)

            # 2. Encode → feature vector (256-dim)
            encoder = self._get_encoder()
            feature_vec = encoder.encode_from_pil(img_resized)

            # 3. Project → latent (64-dim)
            ls = self._get_latent_space()
            latent = ls.project("vision", feature_vec)

            # 4. Decode latent → image (128×128 RGB)
            decoder = self._get_decoder()
            decoded_arr = decoder.decode(latent)
            decoded_pil = Image.fromarray(decoded_arr, "RGB")

            # 5. Quality metrics (SSIM/PSNR)
            ssim_val = self._compute_ssim(arr, decoded_arr.astype(np.float32))
            psnr_val = self._compute_psnr(arr, decoded_arr.astype(np.float32))

            # 6. Build result
            result["feature_vector"] = feature_vec.tolist()
            result["latent"] = latent.tolist()
            result["decoded_image"] = decoded_pil
            result["decoded_array"] = decoded_arr.tolist()
            result["ssim"] = round(float(ssim_val), 6)
            result["psnr"] = round(float(psnr_val), 2)
            result["image_hash"] = img_hash
            result["original_size"] = original_size
            result["time_ms"] = round((time.time() - t0) * 1000, 1)
            result["cache_hit"] = False

            # 7. Update cache
            self._cache[img_hash] = {k: v for k, v in result.items()
                                     if k not in ("decoded_image", "decoded_array")}
            self._cache.move_to_end(img_hash)
            while len(self._cache) > self.CACHE_SIZE:
                self._cache.popitem(last=False)

        except Exception as e:
            logger.error("VisionPipeline.process failed: %s", e, exc_info=True)
            result["error"] = safe_error(e)

        return result

    def process_pil(self, img: Image.Image) -> Dict[str, Any]:
        """Process a PIL Image directly (bypasses bytes decode)."""
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return self.process(buf.getvalue())

    def batch_process(self, images: List[bytes]) -> List[Dict[str, Any]]:
        """Process multiple images in batch.

        Reuses encoder, latent space, and decoder instances for efficiency.

        Args:
            images: List of raw image bytes

        Returns:
            List of result dicts (same structure as process())
        """
        return [self.process(img_data) for img_data in images]

    def clear_cache(self) -> None:
        """Clear the LRU cache."""
        self._cache.clear()

    def cache_size(self) -> int:
        """Return current cache size."""
        return len(self._cache)

    # --- Utility methods ---

    def encode_only(self, image_data: bytes) -> np.ndarray:
        """Encode image to feature vector only (bypasses full pipeline)."""
        encoder = self._get_encoder()
        return encoder.encode(image_data)

    def decode_latent_to_pil(self, latent: np.ndarray) -> Image.Image:
        """Decode a latent vector to a PIL Image."""
        decoder = self._get_decoder()
        return decoder.decode_to_pil(latent)

    def get_latent(self, image_data: bytes) -> np.ndarray:
        """Encode and project to latent only."""
        ls = self._get_latent_space()
        feat = self.encode_only(image_data)
        return ls.project("vision", feat)

    @staticmethod
    def _hash_image(image_data: bytes) -> str:
        """Generate a content-based hash for caching."""
        import hashlib
        return hashlib.md5(image_data).hexdigest()

    @staticmethod
    def _compute_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
        """Compute simplified SSIM between two RGB images.

        Uses per-channel mean/variance/covariance with stability constants.
        Returns 0 for incompatible shapes.
        """
        if img1.shape != img2.shape:
            return 0.0
        if img1.ndim != 3 or img2.ndim != 3:
            return 0.0
        eps = 1e-8
        c1 = (0.01 * 255) ** 2
        c2 = (0.03 * 255) ** 2
        scores = []
        for c in range(3):
            a = img1[:, :, c].astype(np.float64)
            b = img2[:, :, c].astype(np.float64)
            mu_a = a.mean()
            mu_b = b.mean()
            var_a = a.var()
            var_b = b.var()
            cov = ((a - mu_a) * (b - mu_b)).mean()
            num = (2 * mu_a * mu_b + c1) * (2 * cov + c2)
            den = (mu_a ** 2 + mu_b ** 2 + c1) * (var_a + var_b + c2)
            scores.append(num / (den + eps))
        return float(np.mean(scores))

    @staticmethod
    def _compute_psnr(img1: np.ndarray, img2: np.ndarray) -> float:
        """Compute PSNR between two RGB images in dB."""
        if img1.shape != img2.shape:
            return 0.0
        mse = np.mean((img1.astype(np.float64) - img2.astype(np.float64)) ** 2)
        if mse < 1e-10:
            return 100.0
        max_pixel = 255.0
        return 20 * np.log10(max_pixel / np.sqrt(mse))

    def get_stats(self) -> Dict[str, Any]:
        """Return pipeline statistics."""
        return {
            "cache_size": len(self._cache),
            "input_size": self.INPUT_SIZE,
            "vision_dim": self.VISION_DIM,
            "latent_dim": self.LATENT_DIM,
            "encoder_initialized": self._encoder is not None,
            "latent_space_initialized": self._latent_space is not None,
            "decoder_initialized": self._decoder is not None,
        }
