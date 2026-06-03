"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
CardRegistry — manages card instances and integrates with ServiceRegistry.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.card.card_types import (
    Card, CardType, Conflict, ConflictType, Event, IntentFlag,
    Relation, SourceFile, Token, Visual,
)

logger = logging.getLogger(__name__)


class CardRegistry:
    """
    Registry for Card objects keyed by qualified_id (card_id@world_line).
    Supports JSON persistence via save() / load().
    """

    def __init__(self):
        self._cards: Dict[str, Card] = {}

    def add(self, card: Card) -> None:
        """Log a diagnostic message."""
        key = card.qualified_id or f"{card.card_id}@{card.world_line}"
        self._cards[key] = card
        logger.info(f"CardRegistry: added {key}")

    def get(self, qualified_id: str) -> Optional[Card]:
        """Execute the get operation."""
        return self._cards.get(qualified_id)

    def get_by_card_id(self, card_id: str, world_line: str) -> Optional[Card]:
        """Get the by card id by self."""
        return self._cards.get(f"{card_id}@{world_line}")

    def remove(self, qualified_id: str) -> bool:
        """Execute the remove operation."""
        return self._cards.pop(qualified_id, None) is not None

    def list_all(self) -> List[Card]:
        """List all items."""
        return list(self._cards.values())

    def list_by_world_line(self, world_line: str) -> List[Card]:
        """List by world line items."""
        return [
            card for card in self._cards.values()
            if card.world_line == world_line
        ]

    def clear(self) -> None:
        """Clear all entries."""
        self._cards.clear()

    @property
    def count(self) -> int:
        return len(self._cards)

    def save(self, path: Path) -> None:
        """Save the current state."""
        data = {key: _card_to_dict(card) for key, card in self._cards.items()}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"CardRegistry: saved {len(data)} cards to {path}")

    def load(self, path: Path) -> None:
        """Load state from storage."""
        if not path.exists():
            logger.warning(f"CardRegistry: {path} not found, starting empty")
            return
        raw = json.loads(path.read_text(encoding="utf-8"))
        for key, d in raw.items():
            self._cards[key] = _dict_to_card(d)
        logger.info(f"CardRegistry: loaded {len(self._cards)} cards from {path}")


def _card_to_dict(card: Card) -> Dict[str, Any]:
    return {
        "card_id": card.card_id,
        "world_line": card.world_line,
        "qualified_id": card.qualified_id,
        "alternate_selves": card.alternate_selves,
        "card_type": card.card_type.name,
        "name": card.name,
        "core_trait": card.core_trait,
        "meta_data": card.meta_data,
        "custom_fields": card.custom_fields,
        "tokens": [_token_to_dict(t) for t in card.tokens],
        "social_distance": [_relation_to_dict(r) for r in card.social_distance],
        "history_events": [_event_to_dict(e) for e in card.history_events],
        "source_files": [_source_file_to_dict(sf) for sf in card.source_files],
        "conflicts": [_conflict_to_dict(c) for c in card.conflicts],
        "visual_data": _visual_to_dict(card.visual_data),
    }


def _dict_to_card(d: Dict[str, Any]) -> Card:
    return Card(
        card_id=d.get("card_id", ""),
        world_line=d.get("world_line", ""),
        qualified_id=d.get("qualified_id", ""),
        alternate_selves=d.get("alternate_selves", []),
        card_type=CardType[d.get("card_type", "CHARACTER")],
        name=d.get("name", ""),
        core_trait=d.get("core_trait", ""),
        meta_data=d.get("meta_data", {}),
        custom_fields=d.get("custom_fields", {}),
        tokens=[_dict_to_token(t) for t in d.get("tokens", [])],
        social_distance=[_dict_to_relation(r) for r in d.get("social_distance", [])],
        history_events=[_dict_to_event(e) for e in d.get("history_events", [])],
        source_files=[_dict_to_source_file(sf) for sf in d.get("source_files", [])],
        conflicts=[_dict_to_conflict(c) for c in d.get("conflicts", [])],
        visual_data=_dict_to_visual(d.get("visual_data")),
    )


def _token_to_dict(t: Token) -> Dict[str, Any]:
    return {"category": t.category, "name": t.name, "strength": t.strength}


def _dict_to_token(d: Dict[str, Any]) -> Token:
    return Token(category=d["category"], name=d["name"], strength=d.get("strength", 1.0))


def _relation_to_dict(r: Relation) -> Dict[str, Any]:
    return {"target_id": r.target_id, "grid": r.grid, "nature": r.nature}


def _dict_to_relation(d: Dict[str, Any]) -> Relation:
    return Relation(target_id=d["target_id"], grid=d["grid"], nature=d["nature"])


def _event_to_dict(e: Event) -> Dict[str, Any]:
    return {
        "timestamp": e.timestamp.isoformat(),
        "title": e.title,
        "description": e.description,
    }


def _dict_to_event(d: Dict[str, Any]) -> Event:
    return Event(
        timestamp=datetime.fromisoformat(d["timestamp"]),
        title=d["title"],
        description=d.get("description", ""),
    )


def _source_file_to_dict(sf: SourceFile) -> Dict[str, Any]:
    return {
        "path": sf.path,
        "doc_id": sf.doc_id,
        "last_write_time": sf.last_write_time.isoformat(),
        "raw_text": sf.raw_text,
    }


def _dict_to_source_file(d: Dict[str, Any]) -> SourceFile:
    return SourceFile(
        path=d["path"],
        doc_id=d["doc_id"],
        last_write_time=datetime.fromisoformat(d["last_write_time"]),
        raw_text=d.get("raw_text", ""),
    )


def _conflict_to_dict(c: Conflict) -> Dict[str, Any]:
    return {
        "type": c.type.name,
        "dimension": c.dimension,
        "description": c.description,
        "resolution": c.resolution,
        "user_intent": c.user_intent.name,
        "suppressed": c.suppressed,
    }


def _dict_to_conflict(d: Dict[str, Any]) -> Conflict:
    return Conflict(
        type=ConflictType[d.get("type", "HARD_ERROR")],
        dimension=d.get("dimension", ""),
        description=d.get("description", ""),
        resolution=d.get("resolution"),
        user_intent=IntentFlag[d.get("user_intent", "PENDING")],
        suppressed=d.get("suppressed", False),
    )


def _visual_to_dict(v: Optional[Visual]) -> Optional[Dict[str, Any]]:
    """Visual to dict."""
    if v is None:
        return None
    return {"image_path": v.image_path, "prompt": v.prompt, "style": v.style}


def _dict_to_visual(d: Optional[Dict[str, Any]]) -> Optional[Visual]:
    """Dict to visual."""
    if d is None:
        return None
    return Visual(
        image_path=d.get("image_path"),
        prompt=d.get("prompt"),
        style=d.get("style"),
    )


__all__ = ["CardRegistry"]
