# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
BlockCoordinator — bridges existing SNN engines to MSBA blocks.

Layer hierarchy:
  BlockCoordinator (new: inter-block coordination)
    -> CoreNetwork / TensorSNNCore (existing: intra-block computation)
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BlockCoordinator:
    """
    Coordinates computation between MSBA blocks and existing SNN engines.

    Does NOT replace CoreNetwork or TensorSNNCore.
    It wraps them as computation backends for each block.
    """

    def __init__(self, engine: Any, block_id: str):
        """
        Args:
            engine: Existing SNN engine (CoreNetwork, TensorSNNCore,
                    or any object with a forward() method).
            block_id: Identifier for the block this coordinator serves.
        """
        self.engine = engine
        self.block_id = block_id
        self._warmed = False

    @property
    def is_warmed(self) -> bool:
        """Whether the underlying engine has trained weights."""
        if self._warmed:
            return True
        if self.engine is None:
            return False
        # Check if engine has non-zero weights
        if hasattr(self.engine, "W"):
            import numpy as np

            if self.engine.W is None:
                self._warmed = False
            else:
                self._warmed = bool(np.any(self.engine.W != 0))
        elif hasattr(self.engine, "connections"):
            self._warmed = bool(self.engine.connections)
        return self._warmed

    def compute(
        self,
        input_projection: Dict[str, float],
        seed_projection: Optional[Dict[str, float]] = None,
    ) -> Dict[str, float]:
        """
        Coordinate computation: project input -> SNN -> hit activations.

        Args:
            input_projection: Input mapped to this block's space.
            seed_projection: Seed answer mapped to this block's space.

        Returns:
            Dict mapping hit_source_id -> activation score.
        """
        if self.engine is None:
            return input_projection  # Degradation: pass through

        try:
            input_result = self._call_engine(input_projection)
        except Exception as e:
            logger.debug(
                "BlockCoordinator[%s] engine failed: %s",
                self.block_id,
                e,
            )
            return input_projection  # Degradation

        if seed_projection:
            try:
                seed_result = self._call_engine(seed_projection)
            except Exception:
                seed_result = {}
        else:
            seed_result = {}

        return self._to_hit_activations(input_result)

    def _call_engine(self, projection: Dict[str, float]) -> Any:
        """Call the underlying SNN engine's forward method."""
        if hasattr(self.engine, "forward"):
            return self.engine.forward(projection)
        elif callable(self.engine):
            return self.engine(projection)
        return projection

    def _to_hit_activations(self, snn_output: Any) -> Dict[str, float]:
        """Convert SNN output to hit_source activations."""
        if isinstance(snn_output, dict):
            return {k: float(v) for k, v in snn_output.items()}
        elif isinstance(snn_output, (list, tuple)):
            return {f"hit_{i}": float(v) for i, v in enumerate(snn_output)}
        return {"default": 1.0}

    def hebbian_update(
        self,
        input_keys: Dict[str, float],
        output_keys: Dict[str, float],
        learning_rate: float = 0.01,
    ) -> None:
        """Propagate Hebbian learning to the underlying engine."""
        if self.engine is None:
            return
        if hasattr(self.engine, "hebbian_update"):
            try:
                self.engine.hebbian_update(input_keys, output_keys)
            except Exception as e:
                logger.debug(
                    "BlockCoordinator[%s] hebbian failed: %s",
                    self.block_id,
                    e,
                )
