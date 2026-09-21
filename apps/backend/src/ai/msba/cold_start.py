# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
ColdStartManager — handles BlockSNN untrained state.

When BlockCoordinator's engine has no trained weights,
falls back to CoreNetwork or TensorSNNCore output.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ColdStartManager:
    """
    Manages cold start for blocks whose SNN engines are untrained.

    Strategy:
    1. If block's coordinator is warmed -> use it directly
    2. If not warmed -> fallback to CoreNetwork/TensorSNNCore
    3. If no fallback -> pass-through input projection
    """

    def __init__(
        self,
        blocks: Dict[str, object],
        core_network: Any = None,
        tensor_snn: Any = None,
    ):
        self.blocks = blocks
        self.core_network = core_network
        self.tensor_snn = tensor_snn

    def is_warmed(self, block_id: str) -> bool:
        """Check if a block's engine has trained weights."""
        block = self.blocks.get(block_id)
        if block is None:
            return False
        coordinator = getattr(block, "coordinator", None)
        if coordinator is None:
            return False
        return coordinator.is_warmed

    def fallback_compute(
        self, block_id: str, input_projection: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Compute with fallback for cold-start blocks.

        Returns hit activations using the best available engine.
        """
        block = self.blocks.get(block_id)
        if block is None:
            return input_projection

        coordinator = getattr(block, "coordinator", None)
        if coordinator is not None and coordinator.is_warmed:
            return coordinator.compute(input_projection)

        # Fallback: try CoreNetwork
        if self.core_network is not None:
            try:
                output = self.core_network.forward(input_projection)
                if isinstance(output, dict):
                    return {k: float(v) for k, v in output.items()}
            except Exception as e:
                logger.debug("CoreNetwork fallback failed: %s", e)

        # Fallback: try TensorSNNCore
        if self.tensor_snn is not None:
            try:
                output = self.tensor_snn.forward(input_projection)
                if isinstance(output, dict):
                    return {k: float(v) for k, v in output.items()}
            except Exception as e:
                logger.debug("TensorSNNCore fallback failed: %s", e)

        # Final degradation: pass-through
        return input_projection

    def get_warmup_status(self) -> Dict[str, bool]:
        """Get warmup status for all blocks."""
        return {bid: self.is_warmed(bid) for bid in self.blocks}
