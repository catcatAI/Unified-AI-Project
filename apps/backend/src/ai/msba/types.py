# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
MSBA type definitions — all dataclasses for the pipeline.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class SeedResult:
    """Deterministic engine output — a hypothesis, not final answer."""

    answer: str = ""
    confidence: float = 0.0
    source: str = "none"
    reasoning_chain: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def has_seed(self) -> bool:
        return self.confidence > 0.0 and self.answer != ""


@dataclass
class HitSource:
    """A sub-computation unit within a semantic block."""

    source_id: str
    source_name: str
    weight: Any = None  # np.ndarray, lazy-loaded
    threshold: float = 0.15
    activation: float = 0.0
    connections: Dict[str, float] = field(default_factory=dict)


@dataclass
class BlockSelection:
    """Block selector output."""

    scores: Dict[str, float] = field(default_factory=dict)
    selected: List[str] = field(default_factory=list)
    seed_confidence: float = 0.0
    inject_keys: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class BlockHitResult:
    """Single block hit computation result."""

    block_id: str = ""
    hit_sources: Dict[str, float] = field(default_factory=dict)
    seed_verdict: str = "neutral"
    confidence: float = 0.0


@dataclass
class FusedRepresentation:
    """Multi-dimensional fused representation after convergence."""

    primary: Dict[Tuple[str, str, float], float] = field(default_factory=dict)
    auxiliary: Dict[Tuple[str, str, float], float] = field(default_factory=dict)
    latent: Dict[Tuple[str, str, float], float] = field(default_factory=dict)
    seed_influence: Dict[str, float] = field(default_factory=dict)
    seed_verdicts: Dict[str, str] = field(default_factory=dict)
    dimensions: List[str] = field(default_factory=list)
    confidence: float = 0.0

    @property
    def all_entries(self) -> Dict:
        """Merge all tiers into a single dict."""
        result = {}
        result.update(self.primary)
        result.update(self.auxiliary)
        result.update(self.latent)
        return result


@dataclass
class BlockHistory:
    """Tracks block selection history for signal 2."""

    total: int = 0
    confirm_count: int = 0
    question_count: int = 0
    supplement_count: int = 0
    neutral_count: int = 0

    def record(self, verdict: str) -> None:
        self.total += 1
        if verdict == "confirm":
            self.confirm_count += 1
        elif verdict == "question":
            self.question_count += 1
        elif verdict == "supplement":
            self.supplement_count += 1
        else:
            self.neutral_count += 1

    def to_dict(self) -> Dict:
        return {
            "total": self.total,
            "confirm": self.confirm_count,
            "question": self.question_count,
            "supplement": self.supplement_count,
            "neutral": self.neutral_count,
        }
