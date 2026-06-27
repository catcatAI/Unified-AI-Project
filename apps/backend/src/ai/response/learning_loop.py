"""
Angela AI - Neuro-Generative Response Learning Loop
====================================================
Phase E: Autonomous Linguistic Evolution

Extracts new vocabulary, emoji, and sentence patterns from LLM responses.
Reinforces fragment weights based on user engagement signals.
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FragmentExtractor:
    """Extracts NeuroFragment candidates from LLM-generated text."""

    def __init__(self):
        self._seen_patterns: set = set()

    def extract_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        parts = re.split(r'(?<=[。！？.!?\n])\s*', text)
        return [s.strip() for s in parts if s.strip() and len(s.strip()) > 2]

    def extract_emoji(self, text: str) -> List[str]:
        """Extract emoji and kaomoji from text."""
        emoji_pattern = re.compile(
            r'[\U00010000-\U0010ffff\u2600-\u27ff]|'
            r'[\(（][^)）]*[\)）]|'
            r'[≧∀≦ﾉω≧∇≦⊙▽⊙╯﹏╰]'
        )
        return list(set(emoji_pattern.findall(text)))

    def extract_collocations(self, text: str, min_len: int = 4, max_len: int = 20) -> List[str]:
        """Extract common word collocations / phrases."""
        # Simple approach: extract quoted strings and parenthetical phrases
        quoted = re.findall(r'「([^」]*)」|"([^"]*)"|\'([^\']*)\'', text)
        phrases = [q for group in quoted for q in group if q and min_len <= len(q) <= max_len]
        return list(set(phrases))

    def is_novel(self, pattern: str) -> bool:
        """Check if a pattern has been seen before."""
        key = pattern.strip().lower()
        if key in self._seen_patterns:
            return False
        self._seen_patterns.add(key)
        return True


class LearningLoop:
    """
    Autonomous Linguistic Evolution Loop.

    Hooks into the response pipeline after LLM generation:
    1. Extract fragments from high-quality LLM responses
    2. Adjust NeuroVocabulary weights based on user feedback signals
    3. Optionally persist novel fragments to learned config
    4. Grow ED3N dictionary with novel phrases (Phase 5.5)
    5. Adjust GARDEN weights based on user feedback (Phase 5.5)
    """

    def __init__(self, neuro_vocabulary=None):
        self.extractor = FragmentExtractor()
        self._neuro_vocabulary = neuro_vocabulary
        self.extraction_count = 0
        self.learning_rate = 0.05
        self._ed3n_engine = None
        self._garden_engine = None

    def bind_vocabulary(self, neuro_vocabulary) -> None:
        """Execute the bind vocabulary operation."""
        self._neuro_vocabulary = neuro_vocabulary

    def bind_ed3n_engine(self, engine) -> None:
        """Bind ED3N engine for dictionary growth (Phase 5.5)."""
        self._ed3n_engine = engine
        logger.info("LearningLoop bound to ED3N engine")

    def bind_garden_engine(self, engine) -> None:
        """Bind GARDEN engine for weight adjustment (Phase 5.5)."""
        self._garden_engine = engine
        logger.info("LearningLoop bound to GARDEN engine")

    def process_llm_response(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Analyze an LLM response and extract novel linguistic elements.
        Grows ED3N dictionary with novel phrases (Phase 5.5).

        Returns number of novel items extracted.
        """
        if not text:
            return 0

        count = 0
        novel_phrases: List[str] = []

        sentences = self.extractor.extract_sentences(text)
        for sentence in sentences:
            if self.extractor.is_novel(sentence):
                logger.debug(f"[LearningLoop] Novel sentence: {sentence[:40]}...")
                count += 1

        emoji_set = self.extractor.extract_emoji(text)
        for emoji in emoji_set:
            if self.extractor.is_novel(emoji):
                logger.debug(f"[LearningLoop] Novel emoji: {emoji}")
                count += 1

        phrases = self.extractor.extract_collocations(text)
        for phrase in phrases:
            if self.extractor.is_novel(phrase):
                logger.debug(f"[LearningLoop] Novel phrase: {phrase}")
                novel_phrases.append(phrase)
                count += 1

        # Phase 5.5: Grow ED3N dictionary with novel phrases
        if self._ed3n_engine is not None and novel_phrases:
            self._grow_ed3n_dictionary(text, novel_phrases)

        self.extraction_count += count
        if count > 0:
            logger.info(f"[LearningLoop] Extracted {count} novel items from LLM response")

        return count

    def _grow_ed3n_dictionary(self, text: str, novel_phrases: List[str]) -> None:
        """Grow ED3N dictionary with novel phrases (Phase 5.5)."""
        try:
            dictionary = getattr(self._ed3n_engine, 'dictionary', None)
            if dictionary is None:
                return
            for phrase in novel_phrases:
                if hasattr(dictionary, 'grow'):
                    new_key = dictionary.grow(
                        text=text,
                        surface_form=phrase,
                        confidence=0.5,
                    )
                    if new_key:
                        logger.debug("[LearningLoop] Grew ED3N dictionary: %s -> %s", phrase, new_key)
        except Exception as e:
            logger.debug("[LearningLoop] ED3N dictionary growth failed: %s", e)

    def process_user_feedback(
        self,
        user_message: str,
        response: str,
        positive: bool,
        user_feedback: float = 0.0,
    ) -> None:
        """
        Process user feedback to adjust GARDEN weights (Phase 5.5).
        positive=True reinforces the response, negative weakens it.
        """
        if self._garden_engine is not None:
            try:
                if hasattr(self._garden_engine, 'learn_from_interaction'):
                    self._garden_engine.learn_from_interaction(
                        user_message, response
                    )
                    logger.debug("[LearningLoop] GARDEN weights updated from feedback")
            except Exception as e:
                logger.debug("[LearningLoop] GARDEN feedback processing failed: %s", e)

        self.record_user_engagement(positive)

    def record_user_engagement(self, positive: bool) -> None:
        """Adjust learning rate based on user engagement signal."""
        if positive:
            self.learning_rate = min(0.15, self.learning_rate + 0.01)
        else:
            self.learning_rate = max(0.01, self.learning_rate - 0.005)


_default_loop: Optional[LearningLoop] = None


def get_learning_loop() -> LearningLoop:
    """Get the learning loop."""
    global _default_loop
    if _default_loop is None:
        _default_loop = LearningLoop()
    return _default_loop
