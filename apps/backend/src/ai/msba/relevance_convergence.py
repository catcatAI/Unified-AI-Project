# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
RelevanceConvergence — cross-attention + graded fusion.

Fuses block hit results into a multi-dimensional representation.
Cross-attention learning via 3 sources:
  1. Manual prior (initial weights)
  2. Co-occurrence statistics
  3. Feedback learning
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

from .types import (
    BlockHitResult,
    FusedRepresentation,
    SeedResult,
)

logger = logging.getLogger(__name__)


class RelevanceConvergence:
    """
    Fuses multi-block hit results into a unified representation.

    Uses 9x9 cross-attention matrix for inter-block influence.
    """

    BLOCK_ORDER = [
        "temporal",
        "biological",
        "emotional",
        "cognitive",
        "social",
        "mathematical",
        "knowledge",
        "causal",
        "linguistic",
    ]

    # Manual prior cross-attention: (source, target, weight)
    PRIOR_CROSS_ATTENTION: List[Tuple[str, str, float]] = [
        ("emotional", "biological", 0.30),
        ("emotional", "social", 0.25),
        ("causal", "knowledge", 0.20),
        ("mathematical", "causal", 0.15),
        ("cognitive", "knowledge", 0.15),
        ("temporal", "causal", 0.10),
        ("biological", "emotional", 0.15),
        ("social", "cognitive", 0.10),
    ]

    # Tier thresholds
    PRIMARY_THRESHOLD = 0.7
    AUXILIARY_THRESHOLD = 0.3
    LATENT_THRESHOLD = 0.15

    # Context budget
    MAX_TOTAL_ENTRIES = 30
    BUDGET_PRIMARY = 0.6
    BUDGET_AUXILIARY = 0.3
    BUDGET_LATENT = 0.1

    def __init__(self, blocks: Dict[str, object]):
        self.blocks = blocks
        n = len(self.BLOCK_ORDER)
        self.cross_attention = np.ones((n, n)) * 0.05
        np.fill_diagonal(self.cross_attention, 1.0)
        # Apply manual priors
        for src, tgt, w in self.PRIOR_CROSS_ATTENTION:
            if src in self.BLOCK_ORDER and tgt in self.BLOCK_ORDER:
                i = self.BLOCK_ORDER.index(src)
                j = self.BLOCK_ORDER.index(tgt)
                self.cross_attention[j, i] = w

    def converge(
        self,
        block_hits: Dict[str, BlockHitResult],
        seed: SeedResult,
        state_ctx: object = None,
    ) -> FusedRepresentation:
        """
        Fuse all block hit results into a multi-dimensional representation.

        Steps:
          1. Extract hit vectors from each block
          2. Apply cross-attention
          3. Grade into primary/auxiliary/latent tiers
          4. Fuse seed influence
          5. Apply context budget
        """
        # 1. Extract vectors
        vectors: Dict[str, Dict[str, float]] = {}
        for bid, hit in block_hits.items():
            vectors[bid] = hit.hit_sources

        # 2. Cross-attention
        enhanced = self._apply_cross_attention(vectors)

        # 3. Grade into tiers
        primary: Dict[Tuple[str, str, float], float] = {}
        auxiliary: Dict[Tuple[str, str, float], float] = {}
        latent: Dict[Tuple[str, str, float], float] = {}

        for bid, hits in enhanced.items():
            for sid, act in hits.items():
                entry = (bid, sid, act)
                if act > self.PRIMARY_THRESHOLD:
                    primary[entry] = act
                elif act > self.AUXILIARY_THRESHOLD:
                    auxiliary[entry] = act
                elif act > self.LATENT_THRESHOLD:
                    latent[entry] = act

        # 4. Budget
        primary, auxiliary, latent = self._apply_budget(primary, auxiliary, latent)

        # 5. Seed influence
        seed_influence = self._fuse_seed(seed, primary)

        # 6. Confidence
        all_acts = [a for hits in enhanced.values() for a in hits.values()]
        avg_conf = float(np.mean(all_acts)) if all_acts else 0.0

        return FusedRepresentation(
            primary=primary,
            auxiliary=auxiliary,
            latent=latent,
            seed_influence=seed_influence,
            seed_verdicts={b.block_id: b.seed_verdict for b in block_hits.values()},
            dimensions=list(vectors.keys()),
            confidence=avg_conf,
        )

    def _apply_cross_attention(
        self, vectors: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, float]]:
        """Apply inter-block cross-attention."""
        enhanced: Dict[str, Dict[str, float]] = {}
        for target_id, target_vec in vectors.items():
            if target_id not in self.BLOCK_ORDER:
                enhanced[target_id] = dict(target_vec)
                continue
            ti = self.BLOCK_ORDER.index(target_id)
            enhanced[target_id] = {}
            for src_id, src_vec in vectors.items():
                if src_id not in self.BLOCK_ORDER:
                    continue
                si = self.BLOCK_ORDER.index(src_id)
                w = self.cross_attention[ti, si]
                for key, val in src_vec.items():
                    enhanced[target_id][key] = enhanced[target_id].get(key, 0.0) + val * w
        return enhanced

    def _fuse_seed(
        self,
        seed: SeedResult,
        primary: Dict[Tuple[str, str, float], float],
    ) -> Dict[str, float]:
        """Compute seed influence on primary tier."""
        if not seed.has_seed:
            return {}
        influence = {}
        for bid, sid, act in primary:
            influence[f"{bid}:{sid}"] = act * seed.confidence
        return influence

    def _apply_budget(self, primary, auxiliary, latent):
        """Apply context budget to limit total entries."""
        total = len(primary) + len(auxiliary) + len(latent)
        if total <= self.MAX_TOTAL_ENTRIES:
            return primary, auxiliary, latent

        max_p = int(self.MAX_TOTAL_ENTRIES * self.BUDGET_PRIMARY)
        max_a = int(self.MAX_TOTAL_ENTRIES * self.BUDGET_AUXILIARY)
        max_l = int(self.MAX_TOTAL_ENTRIES * self.BUDGET_LATENT)

        primary = dict(sorted(primary.items(), key=lambda x: -x[1])[:max_p])
        auxiliary = dict(sorted(auxiliary.items(), key=lambda x: -x[1])[:max_a])
        latent = dict(sorted(latent.items(), key=lambda x: -x[1])[:max_l])
        return primary, auxiliary, latent

    def update_from_cooccurrence(self, block_hits: Dict[str, BlockHitResult]) -> None:
        """Update cross-attention based on co-occurrence statistics."""
        high_blocks = [bid for bid, h in block_hits.items() if h.confidence > 0.7]
        for a in high_blocks:
            for b in high_blocks:
                if a != b and a in self.BLOCK_ORDER and b in self.BLOCK_ORDER:
                    ai = self.BLOCK_ORDER.index(a)
                    bi = self.BLOCK_ORDER.index(b)
                    self.cross_attention[bi, ai] = min(
                        0.5,
                        self.cross_attention[bi, ai] + 0.005,
                    )

    def update_from_feedback(
        self,
        block_a: str,
        block_b: str,
        improved: bool,
    ) -> None:
        """Update cross-attention based on feedback."""
        if block_a not in self.BLOCK_ORDER or block_b not in self.BLOCK_ORDER:
            return
        ai = self.BLOCK_ORDER.index(block_a)
        bi = self.BLOCK_ORDER.index(block_b)
        if improved:
            self.cross_attention[bi, ai] = min(0.5, self.cross_attention[bi, ai] + 0.01)
        else:
            self.cross_attention[bi, ai] = max(0.01, self.cross_attention[bi, ai] - 0.005)
