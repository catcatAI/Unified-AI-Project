# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
MultiDirectionalDecoder — attention-weighted fusion + drift validation.

Decodes multi-dimensional fused representation into final output.
Fusion strategy:
  1. Primary tier as main sequence
  2. Auxiliary tier via attention-weighted merge
  3. LLM fallback for severe conflicts
  4. Drift validation (preserves existing mechanism)
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

from .types import FusedRepresentation, SeedResult

if TYPE_CHECKING:
    from .semantic_block import SemanticBlock

logger = logging.getLogger(__name__)


class MultiDirectionalDecoder:
    """
    Decodes fused multi-dimensional representation into text output.

    Uses primary as main path, auxiliary as context, and
    handles seed integration and conflict resolution.
    """

    MAX_DRIFT = 0.5

    def __init__(
        self,
        dictionary: object = None,
        blocks: Optional[Dict[str, "SemanticBlock"]] = None,
        llm_service: object = None,
    ):
        self.dictionary = dictionary
        self.blocks = blocks or {}
        self.llm_service = llm_service

    def decode(
        self,
        fused: FusedRepresentation,
        seed: SeedResult,
        extra_context: str = "",
    ) -> str:
        """
        Decode fused representation into final output.

        Steps:
          1. Decode primary dimension
          2. Decode auxiliary dimension
          3. Integrate seed
          4. Validate drift
          5. LLM conflict resolution if needed
        """
        # 1. Primary sequence
        primary_seq = self._decode_dimension(fused.primary)

        # 2. Auxiliary sequence
        auxiliary_seq = self._decode_dimension(fused.auxiliary)

        # 3. Seed integration
        if seed.confidence > 0.95:
            result = self._merge_high_confidence(seed, primary_seq)
        elif any(v == "question" for v in fused.seed_verdicts.values()):
            result = self._merge_block_priority(primary_seq, auxiliary_seq)
        else:
            result = self._merge_standard(primary_seq, auxiliary_seq, seed)

        # 4. Extra context (from handlers)
        if extra_context:
            result = self._merge_extra(result, extra_context)

        # 5. Drift validation
        drift = self._compute_drift(fused, result)
        if drift > self.MAX_DRIFT:
            fallback = self._fallback_decode(fused, seed)
            if fallback:
                result = fallback

        # 6. LLM conflict resolution
        if self._has_severe_conflict(fused) and self.llm_service:
            llm_result = self._llm_resolve(fused, result)
            if llm_result:
                result = llm_result

        return result if result else self._empty_response(seed)

    def _decode_dimension(self, activations: Dict[tuple, float]) -> str:
        """Decode a single dimension's activations into text."""
        if not activations:
            return ""
        sorted_entries = sorted(activations.items(), key=lambda x: -x[1])
        parts = []
        for (bid, sid, act), weight in sorted_entries[:10]:
            parts.append(sid.replace("_", " "))
        return " ".join(parts)

    def _merge_high_confidence(self, seed: SeedResult, primary_seq: str) -> str:
        """High-confidence seed: seed as base, blocks enrich."""
        if primary_seq:
            return f"{seed.answer} ({primary_seq})"
        return seed.answer

    def _merge_block_priority(self, primary_seq: str, auxiliary_seq: str) -> str:
        """Blocks question the seed: blocks take priority."""
        parts = [p for p in [primary_seq, auxiliary_seq] if p]
        return " ".join(parts) if parts else ""

    def _merge_standard(
        self,
        primary_seq: str,
        auxiliary_seq: str,
        seed: SeedResult,
    ) -> str:
        """Standard merge: all sources contribute."""
        parts = []
        if seed.has_seed:
            parts.append(seed.answer)
        if primary_seq:
            parts.append(primary_seq)
        if auxiliary_seq and auxiliary_seq != primary_seq:
            parts.append(auxiliary_seq)
        return " ".join(parts) if parts else ""

    def _merge_extra(self, result: str, extra: str) -> str:
        """Merge handler result."""
        if not result:
            return extra
        if not extra:
            return result
        return f"{result} {extra}"

    def _compute_drift(self, fused: FusedRepresentation, result: str) -> float:
        """Compute semantic drift (0=no drift, 1=complete drift)."""
        if not result or not fused.dimensions:
            return 0.0
        # Simple overlap check
        result_lower = result.lower()
        matches = sum(1 for dim in fused.dimensions if dim.lower() in result_lower)
        if not fused.dimensions:
            return 0.0
        return 1.0 - (matches / len(fused.dimensions))

    def _fallback_decode(self, fused: FusedRepresentation, seed: SeedResult) -> str:
        """Fallback when drift is too high."""
        if seed.has_seed:
            return seed.answer
        # Return most activated primary entry
        if fused.primary:
            top = max(fused.primary.items(), key=lambda x: -x[1])
            return f"{top[0][1]} ({top[0][0]})"
        return ""

    def _has_severe_conflict(self, fused: FusedRepresentation) -> bool:
        """Detect severe multi-dimensional conflict."""
        dims = fused.dimensions
        if len(dims) < 2:
            return False
        questions = sum(1 for v in fused.seed_verdicts.values() if v == "question")
        return questions >= len(dims) * 0.4

    def _llm_resolve(self, fused: FusedRepresentation, current: str) -> Optional[str]:
        """LLM conflict resolution."""
        if self.llm_service is None:
            return None
        context = self._build_conflict_context(fused)
        prompt = (
            f"Based on these semantic dimensions:\n{context}\n"
            f"Current answer: {current}\n"
            f"Provide a concise corrected answer:"
        )
        try:
            if hasattr(self.llm_service, "generate_sync"):
                synced: Any = self.llm_service.generate_sync(prompt)
                return str(synced) if synced is not None else None
            elif hasattr(self.llm_service, "generate"):
                import asyncio

                loop = asyncio.get_event_loop()
                if loop.is_running():
                    return None
                generated: Any = loop.run_until_complete(self.llm_service.generate(prompt))
                return str(generated) if generated is not None else None
        except Exception as e:
            logger.debug("LLM resolve failed: %s", e)
        return None

    def _build_conflict_context(self, fused: FusedRepresentation) -> str:
        """Build context string for LLM conflict resolution."""
        lines = []
        for dim in fused.dimensions:
            lines.append(f"- {dim}")
        for (bid, sid, act), weight in list(fused.primary.items())[:5]:
            lines.append(f"  {bid}/{sid}: {act:.2f}")
        return "\n".join(lines)

    def _empty_response(self, seed: SeedResult) -> str:
        """Generate empty response."""
        if seed.has_seed:
            return seed.answer
        return "I'm not sure how to respond to that."
