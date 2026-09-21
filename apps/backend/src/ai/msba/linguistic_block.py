# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
LinguisticBlock — POS tagging + dependency parsing for MSBA.

Phase 1: Rule-based (regex patterns)
Phase 2: spaCy integration (if available)
"""

import logging
import re
from typing import Dict, List, Optional

from .types import HitSource

logger = logging.getLogger(__name__)

# POS tag patterns (Phase 1 rule-based)
POS_PATTERNS = {
    "tense_past": [
        r"\b(was|were|had|did|went|said|made|took|gave|found)\b",
        r"\b(\w+ed)\b",  # past tense verbs
    ],
    "tense_present": [
        r"\b(is|are|am|have|has|do|does)\b",
        r"\b(\w+s)\b",  # 3rd person singular
    ],
    "tense_future": [
        r"\b(will|shall|would|could|should|might|may)\b",
        r"\b(gonna|gonna|going to)\b",
    ],
    "aspect_progressive": [
        r"\b(\w+ing)\b",  # present progressive
    ],
    "aspect_perfect": [
        r"\b(have|has|had)\s+(\w+ed)\b",
    ],
    "modality_modal": [
        r"\b(can|could|may|might|must|shall|should|will|would)\b",
    ],
    "modality_imperative": [
        r"^(do|please|let|make)\b",
    ],
    "discourse_question": [
        r"\?$",
        r"\b(what|who|where|when|why|how|which)\b",
    ],
    "discourse_exclamation": [
        r"!$",
    ],
    "register_formal": [
        r"\b(therefore|however|moreover|furthermore|consequently)\b",
        r"\b(hence|thus|accordingly)\b",
    ],
    "register_informal": [
        r"\b(gonna|wanna|gotta|kinda|sorta|dunno)\b",
        r"\b(hey|hi|yo|sup|cool|awesome)\b",
    ],
}


class LinguisticBlock:
    """
    Linguistic analysis block for MSBA.

    Provides POS tagging and dependency features
    via rule-based patterns (Phase 1) or spaCy (Phase 2).
    """

    def __init__(self, use_spacy: bool = False):
        """
        Args:
            use_spacy: If True, try to use spaCy for POS tagging.
        """
        self.use_spacy = use_spacy
        self._nlp = None

        # Create hit sources from POS patterns
        self.hit_sources = [HitSource(source_id=k, source_name=k) for k in POS_PATTERNS.keys()]

        # Try to load spaCy if requested
        if use_spacy:
            self._load_spacy()

    def _load_spacy(self) -> None:
        """Try to load spaCy model."""
        try:
            import spacy

            self._nlp = spacy.load("en_core_web_sm")
            logger.info("LinguisticBlock: spaCy loaded successfully")
        except ImportError:
            logger.warning("LinguisticBlock: spaCy not available, " "using rule-based POS tagging")
            self._nlp = None
        except OSError:
            logger.warning(
                "LinguisticBlock: spaCy model not found, " "using rule-based POS tagging"
            )
            self._nlp = None

    def get_hit_activations(
        self,
        input_text: str,
        seed_answer: str = "",
    ) -> Dict[str, float]:
        """
        Compute linguistic hit source activations.

        Returns dict mapping source_id -> activation score.
        """
        if self._nlp is not None:
            return self._spacy_activations(input_text)
        return self._rule_activations(input_text)

    def _rule_activations(self, text: str) -> Dict[str, float]:
        """Phase 1: Rule-based POS tagging."""
        result = {}
        text_lower = text.lower().strip()

        for source_id, patterns in POS_PATTERNS.items():
            score = 0.0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    # Score based on number of matches
                    score = min(1.0, len(matches) * 0.3)
                    break
            result[source_id] = score

        return result

    def _spacy_activations(self, text: str) -> Dict[str, float]:
        """Phase 2: spaCy-based POS tagging."""
        result = {}

        try:
            doc = self._nlp(text)

            # Extract POS tags
            pos_counts = {}
            for token in doc:
                pos = token.pos_
                pos_counts[pos] = pos_counts.get(pos, 0) + 1

            # Map to hit sources
            result["tense_past"] = 1.0 if "VBD" in pos_counts else 0.0
            result["tense_present"] = (
                1.0 if any(p in pos_counts for p in ["VBP", "VBZ", "VB"]) else 0.0
            )
            result["tense_future"] = 1.0 if "MD" in pos_counts else 0.0
            result["aspect_progressive"] = 1.0 if "VBG" in pos_counts else 0.0
            result["aspect_perfect"] = 1.0 if "VBN" in pos_counts else 0.0
            result["modality_modal"] = 1.0 if "MD" in pos_counts else 0.0
            result["discourse_question"] = 1.0 if doc.text.rstrip().endswith("?") else 0.0
            result["discourse_exclamation"] = 1.0 if doc.text.rstrip().endswith("!") else 0.0

            # Dependency-based features
            dep_counts = {}
            for token in doc:
                dep = token.dep_
                dep_counts[dep] = dep_counts.get(dep, 0) + 1

            result["register_formal"] = 1.0 if dep_counts.get("mark", 0) > 1 else 0.0
            result["register_informal"] = 0.0  # Hard to detect

        except Exception as e:
            logger.debug("spaCy POS tagging failed: %s", e)
            # Fallback to rule-based
            return self._rule_activations(text)

        # Ensure all sources have values
        for hs in self.hit_sources:
            if hs.source_id not in result:
                result[hs.source_id] = 0.0

        return result
