"""Vocabulary Expander — organic vocabulary growth via residual analysis.

Phase 10: When existing primitives are insufficient, discover new types.

Algorithm:
1. Monitor generation quality (pixel error)
2. When error is high → extract residual (what's not captured)
3. Cluster residuals → find common patterns
4. Large clusters → new primitive types
5. Add to vocabulary → re-learn concepts
"""

import numpy as np
import json
import os
from typing import List, Dict, Tuple, Optional
from .primitive_types import TOTAL_DIM
from .geometric_vocabulary import GeometricVocabulary, VisualWord
from .differentiable_renderer import DifferentiableRenderer


class VocabularyExpander:
    """Expands vocabulary through residual analysis.

    When the current vocabulary can't represent certain images well,
    this module discovers new primitive types from the residuals.
    """

    def __init__(self, vocabulary: GeometricVocabulary,
                 canvas_size: Tuple[int, int] = (128, 128)):
        self._vocabulary = vocabulary
        self._diff_renderer = DifferentiableRenderer(canvas_size)
        self._residuals: List[np.ndarray] = []
        self._residual_images: List[np.ndarray] = []
        self._error_threshold = 0.02  # MSE threshold for "needs expansion"

    def analyze_generation(self, original: np.ndarray, optimized_vec: np.ndarray,
                            error: float):
        """Analyze a generation result for potential vocabulary expansion.

        Args:
            original: (H, W, 3) original image
            optimized_vec: (263,) optimized primitive vector
            error: pixel MSE between rendered and original
        """
        if error > self._error_threshold:
            # Compute residual
            rendered = self._diff_renderer.render(optimized_vec)
            residual = original - rendered
            self._residuals.append(residual)
            self._residual_images.append(original)

    def check_for_expansion(self, min_residuals: int = 10,
                             expansion_threshold: int = 5) -> List[Dict]:
        """Check if vocabulary should be expanded.

        Args:
            min_residuals: minimum residuals needed before analyzing
            expansion_threshold: minimum cluster size for new primitive

        Returns:
            List of expansion candidates
        """
        if len(self._residuals) < min_residuals:
            return []

        # Analyze residuals
        residual_arr = np.array(self._residuals)

        # Find common patterns in residuals
        candidates = []

        # Simple analysis: find dominant colors and positions in residuals
        for i, residual in enumerate(self._residuals):
            # Find high-error regions
            error_map = np.sqrt((residual ** 2).sum(axis=2))
            high_error = error_map > 0.3

            if high_error.sum() > 50:  # Significant error
                # Extract pattern
                coords = np.argwhere(high_error)
                if len(coords) > 10:
                    cy = coords[:, 0].mean() / residual.shape[0]
                    cx = coords[:, 1].mean() / residual.shape[1]
                    color = residual[coords[:, 0], coords[:, 1]].mean(axis=0)

                    candidates.append({
                        "position": (float(cx), float(cy)),
                        "color": color.tolist(),
                        "size": float(high_error.sum() / (residual.shape[0] * residual.shape[1])),
                        "residual_mse": float(np.mean(residual ** 2)),
                    })

        # Cluster candidates (simple: group by position)
        if len(candidates) >= expansion_threshold:
            return self._cluster_candidates(candidates)

        return []

    def _cluster_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Cluster residual patterns into new primitive types."""
        if not candidates:
            return []

        # Simple clustering: group by position proximity
        positions = np.array([c["position"] for c in candidates])
        colors = np.array([c["color"] for c in candidates])

        # Find clusters (simple: grid-based)
        clusters = {}
        for i, c in enumerate(candidates):
            px, py = c["position"]
            key = (int(px * 4), int(py * 4))  # 4x4 grid
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(c)

        # Filter by size
        new_types = []
        for key, cluster in clusters.items():
            if len(cluster) >= 3:  # At least 3 residuals agree
                avg_color = np.mean([c["color"] for c in cluster], axis=0)
                avg_pos = np.mean([c["position"] for c in cluster], axis=0)
                avg_size = np.mean([c["size"] for c in cluster])

                new_types.append({
                    "type": "learned_patch",
                    "position": avg_pos.tolist(),
                    "color": avg_color.tolist(),
                    "size": float(avg_size),
                    "support": len(cluster),
                })

        return new_types

    def expand_vocabulary(self, new_types: List[Dict]):
        """Add new primitive types to vocabulary."""
        # For now, we add new visual words based on the detected patterns
        # In a full implementation, this would add new primitive TYPES

        for nt in new_types:
            # Create a new visual word from the detected pattern
            center = np.full(TOTAL_DIM, 0.5, dtype=np.float32)
            cx, cy = nt["position"]
            color = nt["color"]

            # Set header
            center[0] = color[0] / 255.0
            center[1] = color[1] / 255.0
            center[2] = color[2] / 255.0

            # Set a point at the detected position
            center[5] = cx  # x
            center[6] = cy  # y
            center[7] = color[0] / 255.0  # r
            center[8] = color[1] / 255.0  # g
            center[9] = color[2] / 255.0  # b

            # Create visual word
            new_word = VisualWord(
                word_id=len(self._vocabulary._visual_words),
                center=center,
                count=nt["support"],
                primitive_signature={"learned_type": True, "source": "residual"},
            )
            self._vocabulary._visual_words.append(new_word)

        print(f"  Vocabulary expanded: +{len(new_types)} new visual words")

    def clear_residuals(self):
        """Clear accumulated residuals."""
        self._residuals = []
        self._residual_images = []
