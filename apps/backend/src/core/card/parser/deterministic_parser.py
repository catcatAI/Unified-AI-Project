"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
Deterministic regex parser for card content.
Extracts structured fields with confidence scores.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from core.card.card_types import Card, CardType, Conflict, Token

logger = logging.getLogger(__name__)

CARD_ID_PATTERN = re.compile(r"(CC|SL|E|RC)[-\s]?(\d+)")
WORLD_LINE_PATTERN = re.compile(r"(?:世界線|world.line|WL)[:\s]*(W\d+|迴廊|[\w\u4e00-\u9fff]+)")
KEY_VALUE_PATTERN = re.compile(r"^\s*(.+?)\s*[：:]\s*(.+?)\s*$", re.MULTILINE)
TOKEN_PATTERN = re.compile(
    r"(?:Token|特質|trait)\s*[：:]\s*(\w+[\w\u4e00-\u9fff]*)\s*[（(]?\s*([\d.]+)\s*[)）]?"
)
CONFLICT_RESOLUTION_THRESHOLD = 0.85
AUTO_CONFIDENCE_CUTOFF = 0.70


class DeterministicParser:
    """
    Deterministic card parser using regex patterns.
    Each extracted field includes a confidence score.
    """

    def __init__(self):
        self._card_type_map = {
            "CC": CardType.CHARACTER,
            "SL": CardType.STORY_LINE,
            "E": CardType.EVENT,
            "RC": CardType.RULE,
        }

    def parse(self, text: str) -> Tuple[Card, Dict[str, float]]:
        card = Card()
        confidences: Dict[str, float] = {}

        self._parse_card_id(text, card, confidences)
        self._parse_world_line(text, card, confidences)
        self._parse_key_values(text, card, confidences)
        self._parse_tokens(text, card, confidences)

        if not card.qualified_id and card.card_id:
            card.qualified_id = f"{card.card_id}@{card.world_line}" if card.world_line else card.card_id

        return card, confidences

    def _parse_card_id(self, text: str, card: Card, confidences: Dict[str, float]) -> None:
        match = CARD_ID_PATTERN.search(text)
        if match:
            prefix, num = match.group(1), match.group(2)
            card.card_id = f"{prefix}-{num}"
            card.card_type = self._card_type_map.get(prefix, CardType.CHARACTER)
            confidences["card_id"] = 0.98
            confidences["card_type"] = 0.95
        else:
            confidences["card_id"] = 0.0
            confidences["card_type"] = 0.0

    def _parse_world_line(self, text: str, card: Card, confidences: Dict[str, float]) -> None:
        match = WORLD_LINE_PATTERN.search(text)
        if match:
            card.world_line = match.group(1).strip()
            confidences["world_line"] = 0.95
        else:
            confidences["world_line"] = 0.0

    def _parse_key_values(self, text: str, card: Card, confidences: Dict[str, float]) -> None:
        matches = KEY_VALUE_PATTERN.findall(text)
        field_map: Dict[str, str] = {
            "name": "name",
            "姓名": "name",
            "名稱": "name",
            "core_trait": "core_trait",
            "核心特質": "core_trait",
            "核心": "core_trait",
        }
        parsed_count = 0
        for key, value in matches:
            key_stripped = key.strip().lower()
            value_stripped = value.strip()
            mapped = field_map.get(key_stripped) or field_map.get(key.strip())
            if mapped == "name" and not card.name:
                card.name = value_stripped
                confidences["name"] = 0.95
                parsed_count += 1
            elif mapped == "core_trait" and not card.core_trait:
                card.core_trait = value_stripped
                confidences["core_trait"] = 0.90
                parsed_count += 1
            else:
                card.custom_fields[key.strip()] = value_stripped

        confidences["key_values"] = min(0.95, 0.5 + parsed_count * 0.1) if parsed_count > 0 else 0.0

    def _parse_tokens(self, text: str, card: Card, confidences: Dict[str, float]) -> None:
        matches = TOKEN_PATTERN.findall(text)
        card.tokens = []
        for name, strength_str in matches:
            try:
                strength = float(strength_str)
            except ValueError:
                strength = 1.0
            card.tokens.append(Token(category="trait", name=name.strip(), strength=strength))
        confidences["tokens"] = 0.95 if card.tokens else 0.0

    def classify_confidence(self, confidences: Dict[str, float]) -> Dict[str, Any]:
        overall = sum(confidences.values()) / max(len(confidences), 1)
        return {
            "overall": overall,
            "fields": confidences,
            "stage": "auto" if overall >= CONFLICT_RESOLUTION_THRESHOLD else "angela",
            "needs_llm": overall < AUTO_CONFIDENCE_CUTOFF,
        }


__all__ = ["DeterministicParser"]
