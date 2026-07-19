"""
Input enrichment layer for ED3N.

Sits between DictionaryLayer.encode() and CoreNetwork.forward().
Algorithmically enriches the input representation using:
  - Unicode normalization variants
  - Cross-key coherence scoring
  - Ambiguity detection

Zero external dependencies — uses only Python stdlib + ai.core.unicode_utils.
Safe on all platforms (CPU/GPU, Windows/Linux/macOS, Python >= 3.10).
"""

# =============================================================================
# ANGELA-MATRIX: [L2-L3] [αβγδ] [A] [L1]
# =============================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ai.core.unicode_utils import is_japanese, normalize_text, to_romaji

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# EnrichedInput — structured result of enrichment
# ---------------------------------------------------------------------------


@dataclass
class EnrichedInput:
    """
    Rich representation of user input after algorithmic processing.

    Fields
    ------
    raw_text : str
        Original unmodified input text.

    normalized_text : str
        NFKC-normalized + fullwidth-to-halfwidth version of the input.

    text_variants : List[str]
        Alternate forms of the input: transliterations (romaji),
        lowercased forms, etc.  The first element is always normalized_text.

    matched_keys : List[str]
        Concept keys returned by DictionaryLayer.encode().

    key_scores : Dict[str, float]
        Per-key algorithmic score (0.0 – 1.0, normalized to sum to 1.0).

    ambiguity : float
        0.0 = clear single intent; 1.0 = highly ambiguous input.

    coherence : float
        1.0 = all matched keys are well-connected via dictionary relations;
        0.0 = completely unrelated keys.

    confidence : float
        Combined quality score = avg(key_scores) * (1 - 0.5*ambiguity) * coherence.
        Replaces raw ``_compute_confidence()``.
    """

    raw_text: str = ""
    normalized_text: str = ""
    text_variants: List[str] = field(default_factory=list)
    matched_keys: List[str] = field(default_factory=list)
    key_scores: Dict[str, float] = field(default_factory=dict)
    ambiguity: float = 0.0
    coherence: float = 1.0
    confidence: float = 0.0


# ---------------------------------------------------------------------------
# InputEnricher
# ---------------------------------------------------------------------------


class InputEnricher:
    """
    Algorithmic enrichment layer for the ED3N pipeline.

    This is a **stateless** processor — no mutable instance state.
    Safe to share across threads without locks.

    Usage::

        enricher = InputEnricher()
        enriched = enricher.enrich("ｎｉｈａｏ", ["g1", "p1"], dictionary)
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enrich(
        self,
        text: str,
        matched_keys: List[str],
        dictionary: Optional[Any] = None,
    ) -> EnrichedInput:
        """
        Produce an enriched representation of *text* given *matched_keys*.

        Parameters
        ----------
        text : str
            Raw input text (before any normalization).

        matched_keys : List[str]
            Concept keys returned by ``DictionaryLayer.encode(text)``.

        dictionary : DictionaryLayer or None
            Reference to the ED3N dictionary (for cross-key scoring).
            If *None*, key_scores / coherence will be based on text-only
            heuristics.

        Returns
        -------
        EnrichedInput
        """
        normalized = normalize_text(text) if text else ""
        variants = self._build_variants(normalized, text)
        scores, raw_score_avg = self._score_keys(normalized, matched_keys, dictionary)
        ambiguity = self._compute_ambiguity(scores)
        coherence = self._compute_coherence(matched_keys, dictionary)
        confidence = self._combine_confidence(raw_score_avg, ambiguity, coherence)

        return EnrichedInput(
            raw_text=text,
            normalized_text=normalized,
            text_variants=variants,
            matched_keys=matched_keys,
            key_scores=scores,
            ambiguity=ambiguity,
            coherence=coherence,
            confidence=confidence,
        )

    # ------------------------------------------------------------------
    # Text variant generation
    # ------------------------------------------------------------------

    @staticmethod
    def _build_variants(normalized: str, raw: str) -> List[str]:
        """Generate alternate text forms of the input."""
        variants = [normalized] if normalized else []

        # Japanese kana → romaji
        if any(is_japanese(ch) for ch in normalized):
            r = to_romaji(normalized)
            if r and r != normalized:
                variants.append(r)

        # Fallback: raw lowercased if different from normalized
        lower = raw.lower().strip()
        if lower and lower != normalized:
            variants.append(lower)

        return list(dict.fromkeys(variants))  # deduplicate while preserving order

    # ------------------------------------------------------------------
    # Algorithmic key scoring
    # ------------------------------------------------------------------

    @staticmethod
    def _score_keys(
        normalized_text: str,
        keys: List[str],
        dictionary: Optional[Any],
    ) -> Tuple[Dict[str, float], float]:
        """
        Score each matched key by surface-form overlap with input.

        Returns
        -------
        (normalized_scores, raw_average)
            normalized_scores : dict[str, float]  — distribution summing to 1.0
            raw_average       : float              — pre-normalization mean
        """
        if not keys:
            return {}, 0.0
        if not dictionary:
            n = len(keys)
            return {k: 1.0 / n for k in keys}, 1.0 / n

        raw_scores: Dict[str, float] = {}
        for key in keys:
            entry = dictionary.entries.get(key)
            if entry is None:
                raw_scores[key] = 0.0
                continue

            base = getattr(entry, "confidence", 1.0)
            best = 0.0
            for sf in entry.surface_forms.values():
                sf_norm = normalize_text(sf).lower()
                text_lower = normalized_text.lower()

                if sf_norm == text_lower:
                    best = max(best, 1.0)
                elif sf_norm and sf_norm in text_lower:
                    best = max(best, len(sf_norm) / max(len(text_lower), 1) * 0.85)
                elif text_lower and text_lower in sf_norm:
                    best = max(best, len(text_lower) / max(len(sf_norm), 1) * 0.6)

            raw_scores[key] = base * max(best, 0.1)

        raw_avg = sum(raw_scores.values()) / max(len(raw_scores), 1)

        # Normalise to sum = 1.0
        total = sum(raw_scores.values())
        if total > 0:
            return {k: v / total for k, v in raw_scores.items()}, raw_avg
        return {k: 1.0 / max(len(keys), 1) for k in keys}, raw_avg

    # ------------------------------------------------------------------
    # Ambiguity
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_ambiguity(scores: Dict[str, float]) -> float:
        """
        Ambiguity = how evenly probability mass is distributed.

        Low (≈ 0.0):  one key dominates  (clear intent).
        High (≈ 1.0): many keys have similar scores  (unclear intent).
        """
        if len(scores) < 2:
            return 0.0
        sorted_scores = sorted(scores.values(), reverse=True)
        if sorted_scores[0] <= 0:
            return 1.0
        top2_ratio = sorted_scores[1] / sorted_scores[0]
        return min(1.0, top2_ratio * len(scores) * 0.25)

    # ------------------------------------------------------------------
    # Coherence
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_coherence(
        keys: List[str],
        dictionary: Optional[Any],
    ) -> float:
        """
        Coherence = how densely the matched keys are connected via
        dictionary relations (synonym / mapping / analogy).

        1.0 = all keys directly inter-connected.
        0.0 = no relations between any matched keys.
        """
        if not dictionary or len(keys) < 2:
            return 1.0

        key_set = set(keys)
        pairs = len(keys) * (len(keys) - 1) / 2.0
        if pairs <= 0:
            return 1.0

        connections = 0
        for key in keys:
            entry = dictionary.entries.get(key)
            if entry is None:
                continue
            for targets in entry.relations.values():
                connections += len(key_set & set(targets))

        # Each directed relation between two keys counts once per pair
        return min(1.0, connections / (pairs * 2))

    # ------------------------------------------------------------------
    # Combined confidence
    # ------------------------------------------------------------------

    @staticmethod
    def _combine_confidence(
        raw_avg: float,
        ambiguity: float,
        coherence: float,
    ) -> float:
        """
        Combined confidence = raw_score_avg × (1 – 0.5 × ambiguity) × coherence.

        Uses the **pre-normalization** raw average so that a single
        poorly-matching key gets a proportionally low confidence.
        """
        return raw_avg * (1.0 - ambiguity * 0.5) * coherence
