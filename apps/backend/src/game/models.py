"""Game data models — Character, Scene, GameState."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Character:
    card_id: str
    name: str
    hp: int = 100
    max_hp: int = 100
    spirit: int = 50
    max_spirit: int = 50
    skill: int = 50
    max_skill: int = 50
    inventory: list[str] = field(default_factory=list)
    equipment: dict[str, str] = field(default_factory=dict)
    tokens: list[dict] = field(default_factory=list)
    description: str = ""

    def bar(self, current: int, maximum: int, width: int = 10) -> str:
        if maximum <= 0:
            filled = 0
        else:
            filled = max(0, min(width, int(current / maximum * width)))
        return "█" * filled + "░" * (width - filled)

    @property
    def hp_bar(self) -> str:
        return self.bar(self.hp, self.max_hp)

    @property
    def spirit_bar(self) -> str:
        return self.bar(self.spirit, self.max_spirit)

    @property
    def skill_bar(self) -> str:
        return self.bar(self.skill, self.max_skill)


@dataclass
class Scene:
    card_id: str
    name: str
    description: str = ""
    spirit_density: float = 2.0
    temperature: str = ""
    characters: list[str] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    tokens: list[dict] = field(default_factory=list)


@dataclass
class Message:
    speaker: str
    text: str
    kind: str = "dialogue"  # dialogue / narration / system / action


@dataclass
class GameState:
    pc: Character
    scene: Scene
    messages: list[Message] = field(default_factory=list)
    choices: list[str] = field(default_factory=list)
    turn: int = 0
    pending_action: Optional[str] = None
    quit: bool = False
