"""Evaluation metrics for generated images.

Provides CLIP similarity scoring, primitive diversity metrics,
and image quality assessment for the compositional generation pipeline.
"""

import logging
from typing import Dict, List, Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class GenerationEvaluator:
    """Evaluates quality of generated images using CLIP and pixel metrics.

    Metrics:
        - clip_text_similarity: How well image matches text description
        - clip_image_similarity: How similar to reference image
        - primitive_diversity: Variety of primitives used
        - color_coverage: Range of colors in generated image
        - edge_density: Amount of edge detail
    """

    def __init__(self, semantic_encoder=None):
        """Initialize evaluator.

        Args:
            semantic_encoder: SemanticVisualEncoder for CLIP scoring
        """
        self._encoder = semantic_encoder

    def evaluate(
        self,
        generated: Image.Image,
        text: Optional[str] = None,
        reference: Optional[Image.Image] = None,
        primitives: Optional[List[np.ndarray]] = None,
    ) -> Dict:
        """Evaluate a generated image.

        Args:
            generated: Generated PIL Image
            text: Text description for CLIP similarity
            reference: Reference image for image similarity
            primitives: List of primitive embeddings used

        Returns:
            Dictionary of metrics
        """
        metrics = {}

        # Pixel-level metrics (always available)
        arr = np.array(generated).astype(np.float32)
        metrics["mean_brightness"] = float(arr.mean() / 255.0)
        metrics["color_coverage"] = self._color_coverage(arr)
        metrics["edge_density"] = self._edge_density(generated)

        # CLIP text similarity
        if text is not None:
            metrics["clip_text_similarity"] = self._clip_text_similarity(generated, text)

        # CLIP image similarity
        if reference is not None:
            metrics["clip_image_similarity"] = self._clip_image_similarity(generated, reference)

        # Primitive diversity
        if primitives is not None and len(primitives) > 0:
            metrics["primitive_diversity"] = self._primitive_diversity(primitives)
            metrics["n_primitives"] = len(primitives)

        return metrics

    def clip_text_similarity(self, image: Image.Image, text: str) -> float:
        """Compute CLIP similarity between image and text.

        Returns:
            Similarity score in [0, 1]
        """
        return self._clip_text_similarity(image, text)

    def _clip_text_similarity(self, image: Image.Image, text: str) -> float:
        """Internal CLIP text similarity."""
        if self._encoder is None:
            # Fallback: pixel-based heuristic
            return self._pixel_text_heuristic(image, text)

        try:
            import io

            buf = io.BytesIO()
            image.save(buf, format="PNG")
            img_bytes = buf.getvalue()

            img_emb = self._encoder.encode(img_bytes)
            text_embs = self._encoder.encode_text([text])

            if img_emb is None or text_embs is None or len(text_embs) == 0:
                return 0.0

            # Cosine similarity
            img_norm = img_emb / (np.linalg.norm(img_emb) + 1e-8)
            txt_norm = text_embs[0] / (np.linalg.norm(text_embs[0]) + 1e-8)
            sim = float(np.dot(img_norm, txt_norm))
            return max(0.0, min(1.0, (sim + 1) / 2))  # Map [-1,1] to [0,1]
        except Exception as e:
            logger.debug("CLIP text similarity failed: %s", e)
            return 0.0

    def _clip_image_similarity(self, img1: Image.Image, img2: Image.Image) -> float:
        """Internal CLIP image similarity."""
        if self._encoder is None:
            return self._pixel_image_similarity(img1, img2)

        try:
            import io

            buf1 = io.BytesIO()
            img1.save(buf1, format="PNG")
            emb1 = self._encoder.encode(buf1.getvalue())

            buf2 = io.BytesIO()
            img2.save(buf2, format="PNG")
            emb2 = self._encoder.encode(buf2.getvalue())

            if emb1 is None or emb2 is None:
                return 0.0

            norm1 = emb1 / (np.linalg.norm(emb1) + 1e-8)
            norm2 = emb2 / (np.linalg.norm(emb2) + 1e-8)
            sim = float(np.dot(norm1, norm2))
            return max(0.0, min(1.0, (sim + 1) / 2))
        except Exception as e:
            logger.debug("CLIP image similarity failed: %s", e)
            return 0.0

    def _pixel_text_heuristic(self, image: Image.Image, text: str) -> float:
        """Fallback pixel-based similarity when CLIP is not available.

        Uses color keyword matching and basic heuristics.
        """
        arr = np.array(image).astype(np.float32)
        text_lower = text.lower()

        # Simple color detection
        r_mean, g_mean, b_mean = arr[:, :, 0].mean(), arr[:, :, 1].mean(), arr[:, :, 2].mean()

        score = 0.5  # Base score

        if "red" in text_lower and r_mean > 150 and g_mean < 100:
            score += 0.2
        if "blue" in text_lower and b_mean > 150 and r_mean < 100:
            score += 0.2
        if "green" in text_lower and g_mean > 150 and r_mean < 100:
            score += 0.2
        if "yellow" in text_lower and r_mean > 150 and g_mean > 150:
            score += 0.2
        if "white" in text_lower and r_mean > 200 and g_mean > 200:
            score += 0.2
        if "black" in text_lower and r_mean < 50 and g_mean < 50:
            score += 0.2

        return min(1.0, score)

    def _pixel_image_similarity(self, img1: Image.Image, img2: Image.Image) -> float:
        """Fallback pixel-based image similarity."""
        # Resize both to same size
        size = (64, 64)
        arr1 = np.array(img1.resize(size)).astype(np.float32)
        arr2 = np.array(img2.resize(size)).astype(np.float32)

        # MSE-based similarity
        mse = float(np.mean((arr1 - arr2) ** 2))
        # Map MSE to similarity: 0 MSE → 1.0, high MSE → 0.0
        return max(0.0, 1.0 - mse / (255.0**2))

    def _primitive_diversity(self, primitives: List[np.ndarray]) -> float:
        """Measure diversity of primitive embeddings.

        Returns average pairwise cosine distance.
        """
        if len(primitives) < 2:
            return 0.0

        # Normalize
        norms = [p / (np.linalg.norm(p) + 1e-8) for p in primitives]

        # Compute average pairwise similarity
        sims = []
        for i in range(len(norms)):
            for j in range(i + 1, len(norms)):
                sim = float(np.dot(norms[i], norms[j]))
                sims.append(sim)

        # Diversity = 1 - average similarity
        avg_sim = np.mean(sims)
        return float(1.0 - avg_sim)

    def _color_coverage(self, arr: np.ndarray) -> float:
        """Measure range of colors in image.

        Returns fraction of color space covered.
        """
        # Quantize to 8 bins per channel
        quantized = (arr / 32).astype(int)
        quantized = np.clip(quantized, 0, 7)

        # Count unique colors
        pixels = quantized.reshape(-1, 3)
        unique_colors = len(set(map(tuple, pixels.tolist())))

        # Max possible = 8^3 = 512
        return unique_colors / 512.0

    def _edge_density(self, image: Image.Image) -> float:
        """Measure edge density using simple gradient.

        Returns fraction of pixels that are edges.
        """
        arr = np.array(image.convert("L")).astype(np.float32)

        # Simple gradient
        dx = np.abs(np.diff(arr, axis=1))
        dy = np.abs(np.diff(arr, axis=0))

        # Threshold
        threshold = 30.0
        edges_x = (dx > threshold).mean()
        edges_y = (dy > threshold).mean()

        return float((edges_x + edges_y) / 2)
