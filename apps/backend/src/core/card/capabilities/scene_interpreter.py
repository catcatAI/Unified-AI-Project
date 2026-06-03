"""
ANGELA-MATRIX: [L5] [β] [B] [L0]
Scene interpreter — interprets Card tokens + social_distance as a dramatic scene.
"""

import logging
from typing import Any, Dict, List, Optional

from core.card.card_types import Card, Relation
from core.card.resolver.text_gravity import TextGravityField

logger = logging.getLogger(__name__)


class SceneInterpreter:
    """
    Interprets card traits and relationships as a scene description.
    Uses TextGravityField to ensure tone consistency.
    """

    def __init__(self, gravity: Optional[TextGravityField] = None):
        self.gravity = gravity or TextGravityField()

    def interpret(self, card: Card) -> Dict[str, Any]:
        """Interpret the incoming request."""
        scene: Dict[str, Any] = {
            "scene_type": self._detect_scene_type(card),
            "tone": self._determine_tone(card),
            "key_traits": self._extract_key_traits(card),
            "relationships": self._summarize_relations(card.social_distance),
            "nucleus": self._find_nucleus(card),
        }
        return scene

    def _detect_scene_type(self, card: Card) -> str:
        """Detect scene type."""
        if not card.tokens:
            return "general"
        high_strength = [t for t in card.tokens if t.strength >= 0.8]
        if any(t.name in ("戰鬥", "combat", "conflict") for t in high_strength):
            return "conflict"
        if any(t.name in ("談判", "negotiation", "social") for t in high_strength):
            return "social"
        if any(t.name in ("探索", "explore", "mystery") for t in high_strength):
            return "exploration"
        return "general"

    def _determine_tone(self, card: Card) -> str:
        """Determine tone."""
        if card.core_trait:
            candidates = ["serious", "lighthearted", "dramatic", "contemplative"]
            scored = self.gravity.compute_gravity(card.core_trait, candidates)
            return scored[0][0] if scored else "neutral"
        return "neutral"

    def _extract_key_traits(self, card: Card) -> List[Dict[str, Any]]:
        """Extract key traits."""
        sorted_tokens = sorted(card.tokens, key=lambda t: t.strength, reverse=True)
        return [
            {"name": t.name, "strength": t.strength, "category": t.category}
            for t in sorted_tokens[:5]
        ]

    def _summarize_relations(self, relations: List[Relation]) -> List[Dict[str, str]]:
        return [
            {"target": r.target_id, "grid": r.grid, "nature": r.nature}
            for r in relations
        ]

    def _find_nucleus(self, card: Card) -> str:
        """Find nucleus."""
        if card.core_trait:
            return card.core_trait
        if card.tokens:
            return max(card.tokens, key=lambda t: t.strength).name
        return card.name or "unknown"


__all__ = ["SceneInterpreter"]
