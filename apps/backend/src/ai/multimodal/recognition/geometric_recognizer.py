"""Geometric Recognizer — image classification using geometric vocabulary.

Phase 9: Uses the same geometric vocabulary for recognition.

Pipeline:
    Image → Extract geometric features → Match vocabulary → Classify

This is the recognition path — same vocabulary as generation, but bottom-up.
"""

import numpy as np
import time
from typing import Dict, List, Optional, Tuple
from PIL import Image

from ..primitives.primitive_types import DrawingInstructions, TOTAL_DIM
from ..primitives.differentiable_renderer import DifferentiableRenderer
from ..primitives.primitive_renderer import PrimitiveRenderer
from ..primitives.primitive_encoder import PrimitiveEncoder
from ..primitives.geometric_vocabulary import GeometricVocabulary


class GeometricRecognizer:
    """Image classifier using geometric vocabulary.

    Architecture:
        Image → Optimize primitives → Extract features → Match vocabulary → Classify

    Uses the SAME vocabulary as generation — dual-use representation.

    The key insight: the optimized primitive vector IS a feature representation.
    It captures the geometric structure of the image in a compact form.
    """

    def __init__(self, vocabulary: GeometricVocabulary,
                 encoder: Optional[PrimitiveEncoder] = None,
                 canvas_size: Tuple[int, int] = (128, 128)):
        self._vocabulary = vocabulary
        self._encoder = encoder
        self._diff_renderer = DifferentiableRenderer(canvas_size)
        self._pil_renderer = PrimitiveRenderer(canvas_size)
        self._canvas_size = canvas_size

    def recognize(self, image: np.ndarray, n_iterations: int = 20,
                   verbose: bool = False) -> Dict:
        """Recognize an image using geometric vocabulary.

        Uses a two-stage approach:
        1. Quick feature extraction via differentiable rendering
        2. Match against vocabulary

        Args:
            image: (H, W, 3) uint8 or float32 [0, 1] image
            n_iterations: optimization iterations for feature extraction
            verbose: print progress

        Returns:
            {
                "predicted_class": str,
                "confidence": float,
                "class_scores": {class_name: score},
                "vector": (263,) optimized primitive vector,
                "visual_word_id": int,
                "elapsed": time in seconds,
            }
        """
        t0 = time.time()

        # Normalize image
        if image.dtype == np.uint8:
            img_float = image.astype(np.float32) / 255.0
        else:
            img_float = image.astype(np.float32)

        # Resize to target size if needed
        if img_float.shape[0] != self._canvas_size[1] or img_float.shape[1] != self._canvas_size[0]:
            pil = Image.fromarray((img_float * 255).astype(np.uint8))
            pil = pil.resize(self._canvas_size, Image.LANCZOS)
            img_float = np.array(pil, dtype=np.float32) / 255.0

        # Step 1: Extract features via optimization
        init_vec = np.full(TOTAL_DIM, 0.5, dtype=np.float32)
        init_vec[0:3] = img_float.mean(axis=(0, 1))
        opt_vec = self._extract_features(img_float, init_vec, n_iterations)

        # Step 2: Find nearest visual word
        word_id, word_dist = self._vocabulary.find_nearest_word(opt_vec)

        # Step 3: Compute class scores based on visual word distribution
        class_scores = self._compute_class_scores(opt_vec)

        # Step 4: Predict
        predicted_class = max(class_scores, key=class_scores.get)
        confidence = class_scores[predicted_class]

        elapsed = time.time() - t0

        return {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "class_scores": class_scores,
            "vector": opt_vec,
            "visual_word_id": word_id,
            "visual_word_distance": word_dist,
            "elapsed": elapsed,
        }

    def _extract_features(self, target: np.ndarray, init_vec: np.ndarray,
                           n_iterations: int) -> np.ndarray:
        """Extract geometric features from image via optimization."""
        vec = init_vec.copy()
        eps = 0.015
        n_probes = 10
        best_vec = vec.copy()
        best_loss = float('inf')

        for it in range(n_iterations):
            rendered = self._diff_renderer.render(vec)
            loss = float(np.mean((rendered - target) ** 2))

            if loss < best_loss:
                best_loss = loss
                best_vec = vec.copy()

            # Finite differences
            d_vec = np.zeros(TOTAL_DIM, dtype=np.float32)
            probe_dims = np.random.choice(TOTAL_DIM, size=n_probes, replace=False)

            for dim in probe_dims:
                v_plus = vec.copy()
                v_plus[dim] = min(1.0, v_plus[dim] + eps)
                r_plus = self._diff_renderer.render(v_plus)
                l_plus = np.mean((r_plus - target) ** 2)

                v_minus = vec.copy()
                v_minus[dim] = max(0.0, v_minus[dim] - eps)
                r_minus = self._diff_renderer.render(v_minus)
                l_minus = np.mean((r_minus - target) ** 2)

                d_vec[dim] = (l_plus - l_minus) / (2 * eps)

            vec -= 0.008 * d_vec
            vec = np.clip(vec, 0, 1)

        return best_vec

    def _compute_class_scores(self, params: np.ndarray) -> Dict[str, float]:
        """Compute similarity scores for each concept class.

        Uses visual word distribution matching — how similar is the image's
        visual word distribution to each concept's distribution.
        """
        scores = {}

        # Find which visual word this image maps to
        word_id, word_dist = self._vocabulary.find_nearest_word(params)

        for name, concept in self._vocabulary._concept_distributions.items():
            # Score based on visual word distribution overlap
            # Higher score if the image's word is commonly used by this concept
            if word_id >= 0 and word_id < len(concept.word_frequencies):
                word_score = float(concept.word_frequencies[word_id])
            else:
                word_score = 0.0

            # Parameter distance to concept mean (closer = better)
            param_dist = float(np.sqrt(((params - concept.param_means) ** 2).mean()))
            param_score = 1.0 / (1.0 + param_dist * 10)

            # Combined score
            scores[name] = word_score * 0.7 + param_score * 0.3

        return scores

    def recognize_from_vector(self, params: np.ndarray) -> Dict:
        """Recognize directly from an optimized vector (faster, no re-optimization).

        This is the preferred method when you already have optimized vectors.
        """
        # Find nearest visual word
        word_id, word_dist = self._vocabulary.find_nearest_word(params)

        # Compute class scores
        class_scores = self._compute_class_scores(params)

        # Predict
        predicted_class = max(class_scores, key=class_scores.get)
        confidence = class_scores[predicted_class]

        return {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "class_scores": class_scores,
            "vector": params,
            "visual_word_id": word_id,
            "visual_word_distance": word_dist,
        }

    def batch_recognize(self, images: List[np.ndarray], n_iterations: int = 10) -> List[Dict]:
        """Batch recognition of multiple images."""
        results = []
        for i, img in enumerate(images):
            result = self.recognize(img, n_iterations=n_iterations)
            results.append(result)
            if (i + 1) % 10 == 0:
                print(f"  Recognized {i+1}/{len(images)} images")
        return results
