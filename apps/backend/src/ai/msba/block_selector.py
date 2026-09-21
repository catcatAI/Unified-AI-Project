# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
BlockSelector — 4-signal fusion block selection.

Signals:
  1. Semantic similarity (cosine, weight 0.5)
  2. Historical hit rate (confirm rate, weight 0.2)
  3. Inter-block exclusion (penalty, weight 0.1)
  4. StateMatrix context (state boost, weight 0.2)
"""

import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from .types import BlockHistory, BlockSelection, SeedResult

if TYPE_CHECKING:
    from .semantic_block import SemanticBlock

logger = logging.getLogger(__name__)


class BlockSelector:
    """
    Selects which semantic blocks to activate for a given input.

    All inputs go through selection — lightweight inputs (social/reflex)
    simply select fewer blocks (2-3) instead of skipping.
    """

    # Inter-block exclusion pairs: (block_a, block_b, penalty)
    EXCLUSION_PAIRS: List[Tuple[str, str, float]] = [
        ("mathematical", "emotional", 0.15),
        ("mathematical", "social", 0.10),
        ("causal", "emotional", 0.05),
    ]

    def __init__(self, blocks: Dict[str, "SemanticBlock"]):
        """
        Args:
            blocks: Dict mapping block_id -> SemanticBlock.
        """
        self.blocks = blocks
        self.block_history: Dict[str, BlockHistory] = {}
        self._embedder: Optional[object] = None

    def _get_embedder(self) -> object:
        """Lazy-load embedder."""
        if self._embedder is None:
            try:
                from ai.garden.dictionary import VectorDictionary

                embedder: object = VectorDictionary()
            except ImportError:
                embedder = _SimpleEmbedder()
            self._embedder = embedder
        return self._embedder

    def select(
        self,
        input_text: str,
        seed: SeedResult,
        lightweight: bool = False,
    ) -> BlockSelection:
        """
        Select blocks for a given input.

        Args:
            input_text: User input.
            seed: Deterministic seed result.
            lightweight: If True, select fewer blocks (social/reflex).

        Returns:
            BlockSelection with scores and selected block IDs.
        """
        # Signal 1 (cosine similarity) only matters when at least one block
        # declares a semantic_anchor. Anchors default to None (factory never
        # sets them yet), so loading the heavy SentenceTransformer embedder
        # just to compare against None anchors stalls the first request for
        # seconds inside the event loop. Embed only when anchors exist.
        anchors_present = any(
            getattr(block, "semantic_anchor", None) is not None for block in self.blocks.values()
        )
        input_emb = self._embed_text(input_text, self._get_embedder()) if anchors_present else None

        scores: Dict[str, float] = {}
        for block_id, block in self.blocks.items():
            scores[block_id] = self._compute_block_score(
                block_id, block, input_text, input_emb, seed
            )

        # Determine how many blocks to select
        if lightweight:
            top_k = 3
        elif seed.confidence > 0.95:
            top_k = 3
        elif seed.confidence > 0.7:
            top_k = 5
        else:
            top_k = 7

        sorted_blocks = sorted(scores.items(), key=lambda x: -x[1])
        selected = [bid for bid, score in sorted_blocks[:top_k] if score > 0.15]

        return BlockSelection(
            scores=scores,
            selected=selected,
            seed_confidence=seed.confidence,
        )

    def _compute_block_score(
        self,
        block_id: str,
        block: object,
        text: str,
        input_emb: object,
        seed: SeedResult,
    ) -> float:
        """
        Compute block relevance score using 4 signals.

        Signal 1: Semantic similarity (0.5)
        Signal 2: Historical confirm rate (0.2)
        Signal 3: Inter-block exclusion (0.1)
        Signal 4: StateMatrix context boost (0.2)
        """
        # Signal 1: Semantic similarity
        semantic = self._cosine_similarity(input_emb, getattr(block, "semantic_anchor", None))

        # Signal 2: Historical hit rate
        hist = self.block_history.get(block_id)
        if hist and hist.total > 0:
            confirm_rate = hist.confirm_count / hist.total
        else:
            confirm_rate = 0.5  # Neutral prior

        # Signal 3: Inter-block exclusion
        exclusion = 0.0
        for a, b, penalty in self.EXCLUSION_PAIRS:
            if block_id == a or block_id == b:
                other_id = b if block_id == a else a
                if other_id in self.blocks:
                    exclusion += penalty

        # Signal 4: StateMatrix context (placeholder for Phase 1)
        state_boost = 0.0

        score = semantic * 0.5 + confirm_rate * 0.2 + (1.0 - exclusion) * 0.1 + state_boost * 0.2
        return max(0.0, min(1.0, score))

    def _embed_text(self, text: str, embedder) -> object:
        """Embed text using available embedder."""
        if hasattr(embedder, "encode"):
            try:
                return embedder.encode(text)
            except Exception:
                pass
        # Fallback: simple hash-based embedding
        return _SimpleEmbedder().encode(text)

    def _cosine_similarity(self, a: object, b: object) -> float:
        """Compute cosine similarity between two vectors."""
        if a is None or b is None:
            return 0.0
        try:
            import numpy as np

            a_arr = np.asarray(a, dtype=float)
            b_arr = np.asarray(b, dtype=float)
            norm_a = np.linalg.norm(a_arr)
            norm_b = np.linalg.norm(b_arr)
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))
        except Exception:
            return 0.0

    def record_verdict(self, block_id: str, verdict: str) -> None:
        """Record a seed verdict for historical tracking."""
        if block_id not in self.block_history:
            self.block_history[block_id] = BlockHistory()
        self.block_history[block_id].record(verdict)


class _SimpleEmbedder:
    """Fallback embedder using character-level hashing."""

    def encode(self, text: str) -> list:
        """Simple 64-dim hash embedding."""
        import hashlib

        result = [0.0] * 64
        for i, ch in enumerate(text):
            h = int(hashlib.md5(ch.encode()).hexdigest(), 16)
            idx = h % 64
            result[idx] += 1.0
        # Normalize
        norm = sum(x * x for x in result) ** 0.5
        if norm > 0:
            result = [x / norm for x in result]
        return result
