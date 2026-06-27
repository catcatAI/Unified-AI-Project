"""
ANGELA-MATRIX: [L4] [β] [B] [L0]
Pipeline orchestrator — three-stage card import pipeline.
Chains Auto → Angela → LLM stages, following CognitivePipeline pattern.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.card.card_store import CardRegistry
from core.card.card_types import Card
from core.card.parser.conflict_detector import ConflictDetector
from core.card.parser.deterministic_parser import DeterministicParser
from core.card.parser.merge_engine import MergeEngine
from core.card.parser.timeline_resolver import TimelineResolver
from core.card.resolver.llm_fallback import LLMFallback
from core.card.resolver.text_gravity import TextGravityField
from core.card.resolver.token_extractor import TokenExtractor

logger = logging.getLogger(__name__)

RESOLUTION_THRESHOLD = 0.85
ANGELA_THRESHOLD = 0.70


@dataclass
class PipelineResult:
    card: Card
    stage: str  # "auto" | "angela" | "llm"
    confidence: float
    conflicts_resolved: int = 0
    conflicts_total: int = 0
    unresolved_fields: List[str] = field(default_factory=list)
    stage_log: List[Dict[str, Any]] = field(default_factory=list)


class CardImportPipeline:
    """
    Three-stage card import pipeline.
    Stage 1 (Auto): regex parse, merge, conflict detect
    Stage 2 (Angela): text gravity, token extraction
    Stage 3 (LLM): final adjudication
    """

    def __init__(
        self,
        registry: Optional[CardRegistry] = None,
        memory_adapter: Any = None,
        llm_service: Any = None,
    ):
        self.registry = registry or CardRegistry()
        self.memory_adapter = memory_adapter
        self.llm_service = llm_service
        self.parser = DeterministicParser()
        self.merge_engine = MergeEngine()
        self.conflict_detector = ConflictDetector()
        self.timeline_resolver = TimelineResolver()
        self.text_gravity = TextGravityField()
        self.token_extractor = TokenExtractor()
        self.llm_fallback = LLMFallback()

    def process(self, raw_text: str, source_label: str = "unknown") -> PipelineResult:
        """Process incoming data."""
        stage_log: List[Dict[str, Any]] = []
        card, confidences = self.parser.parse(raw_text)
        stage_log.append({"stage": "parse", "card_id": card.card_id, "confidence": confidences})

        conflicts = self.conflict_detector.detect(card)
        stage_log.append({"stage": "detect", "conflicts": len(conflicts)})
        card.conflicts.extend(conflicts)

        card = self.timeline_resolver.resolve([card])
        stage_log.append({"stage": "resolve_timeline"})

        classification = self.parser.classify_confidence(confidences)
        overall = classification["overall"]

        if overall >= RESOLUTION_THRESHOLD:
            result = self._finalize(card, stage_log, "auto", overall, confidences)
            logger.info(f"Pipeline: auto stage resolved {card.qualified_id} ({overall:.3f})")
            return result

        card = self._run_angela_stage(card)
        stage_log.append({"stage": "angela", "gravity_applied": True})

        remaining = [c for c in card.conflicts if not c.suppressed]
        if not remaining or overall >= ANGELA_THRESHOLD:
            result = self._finalize(card, stage_log, "angela", overall, confidences)
            logger.info(f"Pipeline: angela stage resolved {card.qualified_id}")
            return result

        card.conflicts = self.llm_fallback.resolve(card, remaining)
        stage_log.append({"stage": "llm", "conflicts_resolved": len(remaining)})
        result = self._finalize(card, stage_log, "llm", overall, confidences)
        logger.info(f"Pipeline: llm stage resolved {card.qualified_id}")
        return result

    def _run_angela_stage(self, card: Card) -> Card:
        """Run angela stage."""
        unresolved_texts = [c.description for c in card.conflicts if not c.suppressed]
        if card.core_trait and unresolved_texts:
            scored = self.text_gravity.compute_gravity(card.core_trait, unresolved_texts)
            for conflict in card.conflicts:
                match = next(
                    (s for s in scored if s[0] == conflict.description), None
                )
                if match and match[1] >= ANGELA_THRESHOLD:
                    conflict.resolution = (
                        f"Gravity toward '{card.core_trait}': {match[1]:.3f}"
                    )
        if not card.tokens:
            combined = " ".join(unresolved_texts) if unresolved_texts else ""
            card.tokens = self.token_extractor.extract(combined or card.name)
        return card

    def _finalize(
        self,
        card: Card,
        stage_log: List[Dict[str, Any]],
        stage: str,
        overall: float,
        confidences: Dict[str, float],
    ) -> PipelineResult:
        """Finalize."""
        total = len(card.conflicts)
        resolved = sum(1 for c in card.conflicts if c.resolution or c.suppressed)
        unresolved = [k for k, v in confidences.items() if v < 0.5]
        if card.qualified_id:
            existing = self.registry.get(card.qualified_id)
            card = self.merge_engine.merge(existing, card)
            self.registry.add(card)
        return PipelineResult(
            card=card,
            stage=stage,
            confidence=overall,
            conflicts_resolved=resolved,
            conflicts_total=total,
            unresolved_fields=unresolved,
            stage_log=stage_log,
        )


__all__ = ["CardImportPipeline", "PipelineResult"]
