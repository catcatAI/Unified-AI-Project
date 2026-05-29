"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
Core card data structures for the Card Import Pipeline.
Defines Card, Token, SourceFile, Relation, Event, Visual, Conflict, and enums.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class CardType(Enum):
    CHARACTER = auto()
    STORY_LINE = auto()
    EVENT = auto()
    RULE = auto()
    PLAYER_TEMPLATE = auto()
    WORLD_CORE = auto()
    SCENE = auto()
    NATION = auto()
    ORGANIZATION = auto()
    SKILL = auto()
    ITEM = auto()
    UNIVERSAL_MECHANISM = auto()
    WORK_TOOL = auto()
    PROJECT_MANAGEMENT = auto()
    META_FORMULA = auto()
    SAFETY_LEXICON = auto()
    META_SETTING = auto()


class ConflictType(Enum):
    HARD_ERROR = auto()
    INTENTIONAL = auto()
    MULTIVERSE = auto()
    NARRATIVE_DEVICE = auto()


class IntentFlag(Enum):
    PENDING = auto()
    CONFIRMED_KEEP = auto()
    SUPPRESS_FUTURE = auto()


@dataclass
class SourceFile:
    path: str
    doc_id: str
    last_write_time: datetime
    raw_text: str = ""


@dataclass
class Token:
    category: str
    name: str
    strength: float = 1.0


@dataclass
class Relation:
    target_id: str
    grid: str
    nature: str


@dataclass
class Event:
    timestamp: datetime
    title: str
    description: str = ""


@dataclass
class Visual:
    image_path: Optional[str] = None
    prompt: Optional[str] = None
    style: Optional[str] = None


@dataclass
class Conflict:
    type: ConflictType = ConflictType.HARD_ERROR
    dimension: str = ""
    description: str = ""
    resolution: Optional[str] = None
    user_intent: IntentFlag = IntentFlag.PENDING
    suppressed: bool = False


@dataclass
class Card:
    card_id: str = ""
    world_line: str = ""
    qualified_id: str = ""
    alternate_selves: List[str] = field(default_factory=list)
    card_type: CardType = CardType.CHARACTER
    name: str = ""
    source_files: List[SourceFile] = field(default_factory=list)
    meta_data: Dict[str, Any] = field(default_factory=dict)
    tokens: List[Token] = field(default_factory=list)
    social_distance: List[Relation] = field(default_factory=list)
    history_events: List[Event] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    visual_data: Optional[Visual] = None
    core_trait: str = ""
    conflicts: List[Conflict] = field(default_factory=list)


__all__ = [
    "CardType",
    "ConflictType",
    "IntentFlag",
    "SourceFile",
    "Token",
    "Relation",
    "Event",
    "Visual",
    "Conflict",
    "Card",
]
