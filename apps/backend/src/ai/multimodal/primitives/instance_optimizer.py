"""Instance Optimizer — pixel-level parameter optimization for generation.

Phase 8: For a specific image, optimize primitive parameters at pixel level.

Loss = MSE(rendered, original) at pixel level (NOT CLIP similarity).
"""

import logging
import time
from typing import Optional, Tuple

import numpy as np
from PIL import Image

from .concept_mapper import ConceptMapper

logger = logging.getLogger(__name__)
from .differentiable_renderer import DifferentiableRenderer
from .geometric_vocabulary import GeometricVocabulary
from .primitive_renderer import PrimitiveRenderer
from .primitive_types import TOTAL_DIM, DrawingInstructions


class InstanceOptimizer:
    """Optimizes primitive parameters for a specific image.

    Pipeline:
        1. Concept lookup (from ConceptMapper)
        2. Initialize parameters from concept distribution
        3. Optimize to minimize pixel MSE
        4. Render final image

    This is the generation path — where pixel similarity is the training signal.
    """

    def __init__(self, vocabulary: GeometricVocabulary,
                 concept_mapper: ConceptMapper,
                 canvas_size: Tuple[int, int] = (128, 128)):
        self._vocabulary = vocabulary
        self._concept_mapper = concept_mapper
        self._diff_renderer = DifferentiableRenderer(canvas_size)
        self._pil_renderer = PrimitiveRenderer(canvas_size)
        self._canvas_size = canvas_size

    def optimize_from_text(self, text_embedding: np.ndarray,
                            n_iterations: int = 30,
                            lr: float = 0.008,
                            n_probes: int = 10,
                            verbose: bool = False) -> dict:
        """Optimize primitives from text CLIP embedding.

        Args:
            text_embedding: (512,) CLIP text embedding
            n_iterations: optimization iterations
            lr: learning rate for finite differences
            n_probes: number of params to probe per iteration
            verbose: print progress

        Returns:
            {
                "vector": (263,) optimized parameters,
                "rendered": PIL Image,
                "loss": final pixel MSE,
                "concept": matched concept name,
                "elapsed": time in seconds,
            }
        """
        # Step 1: Map text to concept
        mapping = self._concept_mapper.map_text_to_primitives(text_embedding)
        concept_name = mapping["concept"]

        if verbose:
            logger.info("Concept: %s (sim=%.3f)", concept_name, mapping['similarity'])

        # Step 2: Initialize from concept distribution
        init_vec = mapping["initialization"]

        # Step 3: Optimize (pixel MSE)
        t0 = time.time()
        opt_vec, opt_loss = self._optimize_pixel_mse(
            init_vec, target=None,  # no target image for text-only
            n_iterations=n_iterations, lr=lr, n_probes=n_probes
        )
        elapsed = time.time() - t0

        # Step 4: Render
        instructions = DrawingInstructions.from_vector(opt_vec, self._canvas_size)
        rendered = self._pil_renderer.render(instructions)

        return {
            "vector": opt_vec,
            "rendered": rendered,
            "loss": opt_loss,
            "concept": concept_name,
            "elapsed": elapsed,
        }

    def optimize_for_image(self, target_image: np.ndarray,
                            concept_name: Optional[str] = None,
                            n_iterations: int = 30,
                            lr: float = 0.008,
                            n_probes: int = 10,
                            verbose: bool = False) -> dict:
        """Optimize primitives to match a specific target image.

        This is the CORE optimization — pixel MSE between rendered and target.

        Args:
            target_image: (H, W, 3) float32 [0, 1] target image
            concept_name: optional concept to guide initialization
            n_iterations: optimization iterations
            lr: learning rate
            n_probes: probes per iteration
            verbose: print progress

        Returns:
            {
                "vector": (263,) optimized parameters,
                "rendered": PIL Image,
                "loss": final pixel MSE,
                "concept": concept name,
                "elapsed": time in seconds,
            }
        """
        # Step 1: Initialize
        if concept_name:
            init_vec = self._vocabulary.initialize_from_concept(concept_name)
        else:
            # Auto-detect concept from image features
            init_vec = np.full(TOTAL_DIM, 0.5, dtype=np.float32)
            init_vec[0:3] = target_image.mean(axis=(0, 1))

        # Step 2: Optimize (pixel MSE)
        t0 = time.time()
        opt_vec, opt_loss = self._optimize_pixel_mse(
            init_vec, target_image,
            n_iterations=n_iterations, lr=lr, n_probes=n_probes
        )
        elapsed = time.time() - t0

        # Step 3: Render
        instructions = DrawingInstructions.from_vector(opt_vec, self._canvas_size)
        rendered = self._pil_renderer.render(instructions)

        return {
            "vector": opt_vec,
            "rendered": rendered,
            "loss": opt_loss,
            "concept": concept_name or "unknown",
            "elapsed": elapsed,
        }

    def _optimize_pixel_mse(self, init_vec: np.ndarray,
                             target: Optional[np.ndarray],
                             n_iterations: int = 30,
                             lr: float = 0.008,
                             n_probes: int = 10) -> Tuple[np.ndarray, float]:
        """Optimize vector to minimize pixel MSE with target.

        Uses finite differences on the differentiable renderer.
        """
        vec = init_vec.copy()
        eps = 0.015
        best_vec = vec.copy()
        best_loss = float('inf')

        for it in range(n_iterations):
            # Render current vector
            rendered = self._diff_renderer.render(vec)

            if target is not None:
                loss = float(np.mean((rendered - target) ** 2))
            else:
                # No target — just return current
                loss = 0.0

            if loss < best_loss:
                best_loss = loss
                best_vec = vec.copy()

            if target is None:
                break

            # Finite differences gradient
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

            # Update
            vec -= lr * d_vec
            vec = np.clip(vec, 0, 1)

        return best_vec, best_loss

    def generate(self, text_embedding: np.ndarray,
                  target_image: Optional[np.ndarray] = None,
                  n_iterations: int = 30,
                  verbose: bool = False) -> dict:
        """End-to-end generation.

        If target_image is provided: optimize to match it (reconstruction).
        If not: generate from text concept only (text-to-image).
        """
        if target_image is not None:
            return self.optimize_for_image(
                target_image, n_iterations=n_iterations, verbose=verbose
            )
        else:
            return self.optimize_from_text(
                text_embedding, n_iterations=n_iterations, verbose=verbose
            )
