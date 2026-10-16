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
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from .semantic_block import SemanticBlock

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
        blocks: Dict[str, "SemanticBlock"],
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
        warmed: bool = bool(coordinator.is_warmed)
        return warmed

    def _try_engine(
        self, engine: Any, input_projection: Dict[str, float], label: str
    ) -> Optional[Dict[str, float]]:
        """嘗試單一 fallback engine；dict 輸出回 float 鍵值，否則 None。"""
        if engine is None:
            return None
        try:
            output = engine.forward(input_projection)
            if isinstance(output, dict):
                return {k: float(v) for k, v in output.items()}
        except Exception as e:
            logger.debug("%s fallback failed: %s", label, e)
        return None

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
            result: Dict[str, float] = dict(coordinator.compute(input_projection))
            return result

        # Fallback: try CoreNetwork
        core_result = self._try_engine(self.core_network, input_projection, "CoreNetwork")
        if core_result is not None:
            return core_result

        # Fallback: try TensorSNNCore
        snn_result = self._try_engine(self.tensor_snn, input_projection, "TensorSNNCore")
        if snn_result is not None:
            return snn_result

        # Final degradation: pass-through
        return input_projection

    def get_warmup_status(self) -> Dict[str, bool]:
        """Get warmup status for all blocks."""
        return {bid: self.is_warmed(bid) for bid in self.blocks}
