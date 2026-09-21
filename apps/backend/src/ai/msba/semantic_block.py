# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
SemanticBlock — a semantic dimension with hit sources and dynamic granularity.

Supports split (when too many hit sources) and merge (when high overlap).
"""

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

from .types import HitSource

if TYPE_CHECKING:
    from .block_coordinator import BlockCoordinator

logger = logging.getLogger(__name__)


@dataclass
class SemanticBlock:
    """
    A semantic dimension in the MSBA library.

    Each block contains:
    - hit_sources: sub-computation units
    - coordinator: bridges to existing SNN engines
    - semantic_anchor: vector for block selection
    """

    block_id: str
    block_name: str
    semantic_anchor: object = None  # np.ndarray, lazy
    hit_sources: List[HitSource] = field(default_factory=list)
    coordinator: Optional["BlockCoordinator"] = None
    learning_rate: float = 0.01
    capacity: int = 10
    # Dynamic granularity
    parent_block: Optional[str] = None
    child_blocks: List[str] = field(default_factory=list)
    dynamic: bool = False

    def get_hit_activations(self, input_text: str, seed_answer: str = "") -> dict:
        """
        Compute hit source activations for this block.

        Uses keyword matching via _project_input for basic activation.
        If coordinator exists, delegates to SNN engine for deeper processing.
        """
        input_proj = self._project_input(input_text)
        if self.coordinator is None:
            return input_proj

        seed_proj = self._project_input(seed_answer) if seed_answer else None
        return self.coordinator.compute(input_proj, seed_proj)

    def _project_input(self, text: str) -> dict:
        """Project input text into this block's hit source space."""
        # Simple keyword-based projection for Phase 1
        result = {}
        text_lower = text.lower()
        for hs in self.hit_sources:
            # Check if hit source name appears in text
            if hs.source_name.lower() in text_lower:
                result[hs.source_id] = 1.0
            else:
                result[hs.source_id] = 0.0
        return result

    def split(self, threshold: float = 0.8) -> List["SemanticBlock"]:
        """
        Split block when hit_sources exceed capacity * threshold.

        Returns list containing self (if no split) or child blocks.
        """
        if len(self.hit_sources) < self.capacity * threshold:
            return [self]

        mid = len(self.hit_sources) // 2
        child_a = SemanticBlock(
            block_id=f"{self.block_id}_a",
            block_name=f"{self.block_name}_A",
            semantic_anchor=self.semantic_anchor,
            hit_sources=self.hit_sources[:mid],
            coordinator=self.coordinator,
            learning_rate=self.learning_rate,
            capacity=mid,
            parent_block=self.block_id,
            dynamic=True,
        )
        child_b = SemanticBlock(
            block_id=f"{self.block_id}_b",
            block_name=f"{self.block_name}_B",
            semantic_anchor=self.semantic_anchor,
            hit_sources=self.hit_sources[mid:],
            coordinator=self.coordinator,
            learning_rate=self.learning_rate,
            capacity=len(self.hit_sources) - mid,
            parent_block=self.block_id,
            dynamic=True,
        )
        self.child_blocks = [child_a.block_id, child_b.block_id]
        logger.info(
            "Block %s split into %s, %s",
            self.block_id,
            child_a.block_id,
            child_b.block_id,
        )
        return [child_a, child_b]

    def merge(self, other: "SemanticBlock") -> "SemanticBlock":
        """
        Merge with another block when overlap > 0.7.

        Returns self if no merge needed, otherwise merged block.
        """
        overlap = self._compute_overlap(other)
        if overlap < 0.7:
            return self

        import numpy as np

        merged_anchor = None
        if self.semantic_anchor is not None and other.semantic_anchor is not None:
            try:
                merged_anchor = (
                    np.array(self.semantic_anchor) + np.array(other.semantic_anchor)
                ) / 2
            except Exception:
                merged_anchor = self.semantic_anchor

        merged = SemanticBlock(
            block_id=f"{self.block_id}_merged",
            block_name=f"{self.block_name}+{other.block_name}",
            semantic_anchor=merged_anchor,
            hit_sources=self.hit_sources + other.hit_sources,
            coordinator=self.coordinator,
            learning_rate=max(self.learning_rate, other.learning_rate),
            capacity=self.capacity + other.capacity,
            dynamic=True,
        )
        logger.info(
            "Blocks %s + %s merged into %s (overlap=%.2f)",
            self.block_id,
            other.block_id,
            merged.block_id,
            overlap,
        )
        return merged

    def _compute_overlap(self, other: "SemanticBlock") -> float:
        """Compute Jaccard overlap of hit source IDs."""
        if not self.hit_sources or not other.hit_sources:
            return 0.0
        ids_a = {hs.source_id for hs in self.hit_sources}
        ids_b = {hs.source_id for hs in other.hit_sources}
        intersection = len(ids_a & ids_b)
        union = len(ids_a | ids_b)
        return intersection / union if union > 0 else 0.0
