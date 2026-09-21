# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
NeuroBlenderBridge — maps MSBA FusedRepresentation to NeuroBlender 9D vector.

短期: Bridge 函數 (FusedRepresentation -> 9D)
長期: 9D 向量取代 NeuroBlender 8D
"""

import logging
from typing import Any, Dict, Optional

import numpy as np

from .types import FusedRepresentation

logger = logging.getLogger(__name__)

# MSBA block -> NeuroBlender 9D dimension mapping
FUSED_TO_BLENDER_MAP = {
    "biological": "alpha_energy",
    "cognitive": "beta_curiosity",
    "emotional": "gamma_valence",
    "social": "delta_intimacy",
    "mathematical": "epsilon_precision",
    "temporal": "zeta_temporal",
    "causal": "theta_meta",
    "knowledge": "eta_execution",
    "linguistic": "iota_linguistic",
}

# NeuroBlender 9D dimension names
BLENDER_DIMS = [
    "alpha_energy",
    "beta_curiosity",
    "gamma_valence",
    "delta_intimacy",
    "epsilon_precision",
    "zeta_temporal",
    "theta_meta",
    "eta_execution",
    "iota_linguistic",
]


class NeuroBlenderBridge:
    """
    Bridge between MSBA and NeuroBlender.

    Converts MSBA's FusedRepresentation to NeuroBlender's 9D vector.
    """

    def __init__(self):
        """Initialize the bridge."""
        self.dim_names = BLENDER_DIMS
        self.dim_count = len(BLENDER_DIMS)

    def fused_to_blender_vector(self, fused: FusedRepresentation) -> np.ndarray:
        """
        Convert MSBA FusedRepresentation to NeuroBlender 9D vector.

        Args:
            fused: MSBA's FusedRepresentation.

        Returns:
            9D numpy array for NeuroBlender.
        """
        vec = np.zeros(self.dim_count, dtype=np.float32)

        # Process primary tier (highest weight)
        for (bid, sid, act), weight in fused.primary.items():
            blender_key = FUSED_TO_BLENDER_MAP.get(bid)
            if blender_key and blender_key in BLENDER_DIMS:
                idx = BLENDER_DIMS.index(blender_key)
                vec[idx] = max(vec[idx], act * weight)

        # Process auxiliary tier (lower weight)
        for (bid, sid, act), weight in fused.auxiliary.items():
            blender_key = FUSED_TO_BLENDER_MAP.get(bid)
            if blender_key and blender_key in BLENDER_DIMS:
                idx = BLENDER_DIMS.index(blender_key)
                # Auxiliary gets half weight
                vec[idx] = max(vec[idx], act * weight * 0.5)

        # Normalize to [0, 1]
        max_val = np.max(np.abs(vec))
        if max_val > 0:
            vec = vec / max_val

        return vec

    def blender_to_context(self, vec: np.ndarray) -> Dict[str, Any]:
        """
        Convert NeuroBlender 9D vector to context dict for LLM.

        Args:
            vec: 9D numpy array.

        Returns:
            Dict with dimension names and values.
        """
        context = {}
        for i, name in enumerate(BLENDER_DIMS):
            if i < len(vec):
                context[name] = float(vec[i])
        return context

    def get_dominant_dimension(self, vec: np.ndarray) -> Optional[str]:
        """Get the dominant dimension from 9D vector."""
        if len(vec) == 0:
            return None
        idx = int(np.argmax(np.abs(vec)))
        if idx < len(BLENDER_DIMS):
            return BLENDER_DIMS[idx]
        return None

    def get_dimension_weights(self, fused: FusedRepresentation) -> Dict[str, float]:
        """
        Get dimension weights from FusedRepresentation.

        Returns:
            Dict mapping dimension name -> weight.
        """
        weights = {}
        for bid in FUSED_TO_BLENDER_MAP:
            blender_key = FUSED_TO_BLENDER_MAP[bid]
            if blender_key:
                # Count activations for this block
                count = sum(1 for (b, s, a), w in fused.primary.items() if b == bid)
                weights[blender_key] = count / max(1, len(fused.primary))
        return weights
