"""Token effects system — tokens affect game mechanics."""
from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class TokenEffect:
    """A computed effect from a token."""
    category: str
    name: str
    stat_bonus: dict[str, int] = field(default_factory=dict)
    dice_bonus: int = 0
    resistance: float = 0.0
    special: str = ""


def compute_token_effects(tokens: list[dict]) -> list[TokenEffect]:
    """Convert raw token data into game-mechanical effects."""
    effects = []
    for t in tokens:
        cat = t.get("category", "")
        name = t.get("name", "")
        strength = t.get("strength", 0.5)
        bonus = int(strength * 10)

        if cat == "combat":
            effects.append(TokenEffect(category=cat, name=name, dice_bonus=bonus, special="combat_attack"))
        elif cat == "vitality":
            effects.append(TokenEffect(category=cat, name=name, stat_bonus={"hp": bonus * 3, "max_hp": bonus * 3}, resistance=min(strength * 0.3, 0.3), special="vitality"))
        elif cat == "energy":
            effects.append(TokenEffect(category=cat, name=name, stat_bonus={"spirit": bonus * 2, "max_spirit": bonus * 2}, special="energy"))
        elif cat == "skill":
            effects.append(TokenEffect(category=cat, name=name, stat_bonus={"skill": bonus * 2}, dice_bonus=bonus // 2, special="skill"))
        elif cat == "element":
            effects.append(TokenEffect(category=cat, name=name, dice_bonus=bonus, special="element"))
        elif cat == "craft":
            effects.append(TokenEffect(category=cat, name=name, dice_bonus=bonus // 2, special="craft"))
        elif cat == "knowledge":
            effects.append(TokenEffect(category=cat, name=name, dice_bonus=bonus // 2, special="knowledge"))
        elif cat in ("status", "mechanism", "relation", "social", "exploration", "lore"):
            effects.append(TokenEffect(category=cat, name=name, special=cat))
    return effects


def apply_token_hp(tokens: list[dict], base_hp: int = 100) -> tuple[int, int]:
    """Compute HP and maxHP from vitality tokens. Start slightly below max."""
    import random as _rnd
    max_hp = base_hp
    for t in tokens:
        if t.get("category") == "vitality":
            bonus = int(t.get("strength", 0.5) * 30)
            max_hp += bonus
    start_hp = int(max_hp * _rnd.uniform(0.85, 0.95))
    return max_hp, start_hp


def apply_token_spirit(tokens: list[dict], base_spirit: int = 50) -> tuple[int, int]:
    """Compute spirit and maxSpirit from energy tokens. Start slightly below max."""
    import random as _rnd
    max_spirit = base_spirit
    for t in tokens:
        if t.get("category") == "energy":
            bonus = int(t.get("strength", 0.5) * 20)
            max_spirit += bonus
    start_spirit = int(max_spirit * _rnd.uniform(0.80, 0.90))
    return max_spirit, start_spirit


def apply_token_skill_bonus(tokens: list[dict]) -> int:
    """Compute skill bonus from skill tokens."""
    bonus = 0
    for t in tokens:
        if t.get("category") == "skill":
            bonus += int(t.get("strength", 0.5) * 10)
    return bonus


def get_combat_dice_bonus(tokens: list[dict]) -> int:
    """Compute dice bonus from combat + element tokens."""
    bonus = 0
    for t in tokens:
        if t.get("category") in ("combat", "element"):
            bonus += int(t.get("strength", 0.5) * 5)
    return bonus


def get_damage_resistance(tokens: list[dict]) -> float:
    """Compute damage resistance from vitality tokens (0.0-0.5 max)."""
    resist = 0.0
    for t in tokens:
        if t.get("category") == "vitality":
            resist += t.get("strength", 0.5) * 0.1
    return min(resist, 0.5)


def get_token_descriptions(tokens: list[dict], max_count: int = 5) -> list[str]:
    """Get human-readable token descriptions for UI."""
    descs = []
    for t in tokens[:max_count]:
        cat = t.get("category", "")
        name = t.get("name", "")
        value = str(t.get("value", ""))[:60]
        if name and value:
            descs.append(f"[{cat}] {name}: {value}")
    return descs
