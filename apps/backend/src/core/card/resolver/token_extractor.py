"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
Token extractor — extracts Token objects from unstructured text.
"""

import logging
import re
from typing import List

from core.card.card_types import Token

logger = logging.getLogger(__name__)

TOKEN_LINE = re.compile(
    r"(?:Token|特質|trait|屬性|attribute|特徵)\s*[：:]\s*"
    r"(.+?)\s*[（(]?\s*([\d.]+)\s*[)）]?"
)
STRENGTH_WORD = re.compile(
    r"\b(高|強|中|低|弱|very|strong|medium|low|weak|expert|skilled|novice)\b",
    re.IGNORECASE,
)
STRENGTH_MAP = {
    "高": 0.9, "強": 0.8, "中": 0.5, "低": 0.3, "弱": 0.2,
    "very": 0.9, "strong": 0.8, "medium": 0.5, "low": 0.3, "weak": 0.2,
    "expert": 0.95, "skilled": 0.75, "novice": 0.25,
}


class TokenExtractor:
    """
    Extracts tokens from unstructured text.
    Supports explicit 'Token: name (strength)' format and keyword inference.
    """

    def extract(self, text: str) -> List[Token]:
        """Extract information from input."""
        tokens = self._extract_explicit(text)
        if not tokens:
            tokens = self._extract_implicit(text)
        return tokens

    def _extract_explicit(self, text: str) -> List[Token]:
        tokens: List[Token] = []
        for match in TOKEN_LINE.finditer(text):
            name = match.group(1).strip()
            try:
                strength = float(match.group(2))
            except (ValueError, TypeError):
                logger.warning("Failed to parse token strength '%s', defaulting to 1.0", match.group(2), exc_info=True)
                strength = 1.0
            tokens.append(Token(category="trait", name=name, strength=strength))
        return tokens

    def _extract_implicit(self, text: str) -> List[Token]:
        tokens: List[Token] = []
        seen: set = set()
        for match in STRENGTH_WORD.finditer(text):
            word = match.group(1).lower()
            if word not in seen:
                seen.add(word)
                strength = STRENGTH_MAP.get(word, 0.5)
                tokens.append(Token(category="inferred", name=word, strength=strength))
        return tokens


__all__ = ["TokenExtractor"]
