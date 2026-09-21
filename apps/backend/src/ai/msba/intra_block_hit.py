# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
IntraBlockHitEngine — parallel block hit computation.

Each selected block computes its own hit sources independently.
Seed verdicts are verified by comparing input vs seed activations.
"""

import asyncio
import logging
from typing import Dict, List, Optional

import numpy as np

from .types import BlockHitResult, SeedResult

logger = logging.getLogger(__name__)


class IntraBlockHitEngine:
    """
    Computes hit source activations for all selected blocks in parallel.

    Each block receives input + seed, outputs hit activations + seed verdict.
    """

    def __init__(self, blocks: Dict[str, object]):
        self.blocks = blocks
        self._partial_results: Dict[str, BlockHitResult] = {}

    async def hit_all(
        self,
        input_text: str,
        seed: SeedResult,
        selected_blocks: List[str],
        state_ctx: object = None,
    ) -> Dict[str, BlockHitResult]:
        """
        Compute hits for all selected blocks in parallel.

        Args:
            input_text: Original user input.
            seed: Deterministic seed result.
            selected_blocks: List of block IDs to compute.
            state_ctx: Optional StateMatrix context.

        Returns:
            Dict mapping block_id -> BlockHitResult.
        """
        self._partial_results.clear()
        tasks = []
        for block_id in selected_blocks:
            block = self.blocks.get(block_id)
            if block is None:
                continue
            tasks.append(self._hit_block(block, input_text, seed, state_ctx))

        if not tasks:
            return {}

        results = await asyncio.gather(*tasks, return_exceptions=True)
        output = {}
        for result in results:
            if isinstance(result, BlockHitResult):
                output[result.block_id] = result
                self._partial_results[result.block_id] = result
            elif isinstance(result, Exception):
                logger.debug("Block hit failed: %s", result)
        return output

    def get_partial_results(self) -> Dict[str, BlockHitResult]:
        """Get results computed so far (for timeout fallback)."""
        return dict(self._partial_results)

    async def _hit_block(
        self,
        block,
        input_text: str,
        seed: SeedResult,
        state_ctx: object,
    ) -> BlockHitResult:
        """Compute hit for a single block."""
        # Get block's hit activations for input
        input_hits = block.get_hit_activations(input_text, seed.answer)

        # Get block's hit activations for seed alone
        seed_hits = {}
        if seed.has_seed:
            seed_hits = block.get_hit_activations(seed.answer)

        # Verify seed
        verdict = self._verify_seed(input_hits, seed_hits)

        # Compute confidence
        if input_hits:
            confidence = float(np.mean(list(input_hits.values())))
        else:
            confidence = 0.0

        return BlockHitResult(
            block_id=block.block_id,
            hit_sources=input_hits,
            seed_verdict=verdict,
            confidence=confidence,
        )

    def _verify_seed(
        self,
        input_hits: Dict[str, float],
        seed_hits: Dict[str, float],
    ) -> str:
        """
        Compare input vs seed activations.

        Returns:
            "confirm" if they agree (corr > 0.7)
            "question" if they disagree (corr < 0.3)
            "supplement" if partially aligned
            "neutral" if no seed or no overlap
        """
        if not seed_hits:
            return "neutral"

        common_keys = set(input_hits.keys()) & set(seed_hits.keys())
        if not common_keys:
            return "neutral"

        correlations = [input_hits[k] * seed_hits[k] for k in common_keys]
        avg_corr = float(np.mean(correlations))

        if avg_corr > 0.7:
            return "confirm"
        elif avg_corr < 0.3:
            return "question"
        return "supplement"
