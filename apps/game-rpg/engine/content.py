# -*- coding: utf-8 -*-
"""萬物皆軸引擎 — M5 內容灌入（§6.3：351 卡→劇情群組 FSM 軸；
axis_system 譜系→離散軸字典；卡片→軸值轉換快照）。

- 劇情群組 ``story``：``card_type`` FSM（狀態=資料實際卡型）+
  ``story_role`` FSM（卡型→9 個劇情超類，M5 狀態機轉移的落點）。
- 譜系側：`axis_system.AXIS_SYSTEMS`（物種/AI/義體人/神話種）→
  ``AxisSpec(fsm)`` 離散軸字典群組；`resolve_card_axis` 權威解析掛載。
- `axis_system` 以函式內 import（engine 核心不硬綁該模組）。
- `load_cards()` 回唯讀快取（呼叫端不得改動卡 dict）。
"""

from __future__ import annotations

import importlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from engine.axes import AxisGroup, AxisSpec, Value
from engine.contracts import GroupContract, SignalSpec

STORY_GROUP = "story"
STORY_TICK_RATE = 30.0

# 卡型 → 劇情超類（20 卡型全覆盖；新卡型未列 → card_to_values 即 raise）
STORY_ROLE_BY_CARD_TYPE: Dict[str, str] = {
    "角色卡": "character",
    "角色補充卡": "character",
    "劇情節點卡": "plot",
    "事件卡": "plot",
    "故事線卡": "plot",
    "故事線合集卡": "plot",
    "故事線補充卡": "plot",
    "場景卡": "setting",
    "國家卡": "setting",
    "組織卡": "faction",
    "技能卡": "skill",
    "物品卡": "item",
    "世界觀核心卡": "world",
    "元設定卡": "world",
    "元公式卡": "world",
    "規則卡": "rule",
    "通用機制卡": "rule",
    "安全詞庫卡": "rule",
    "專案管理卡": "meta",
    "創作工具卡": "meta",
}
STORY_ROLES: Tuple[str, ...] = (
    "character",
    "plot",
    "setting",
    "faction",
    "skill",
    "item",
    "world",
    "rule",
    "meta",
)


def default_cards_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "game_cards.json"


@lru_cache(maxsize=4)
def _load_cards_cached(path_str: str) -> Tuple[dict, ...]:
    with open(path_str, encoding="utf-8") as fh:
        data = json.load(fh)
    return tuple(data["cards"])


def load_cards(path: Optional[Path] = None) -> List[dict]:
    """載入卡牌（預設真檔 data/game_cards.json）；回唯讀快取，勿改動。"""
    p = Path(path) if path is not None else default_cards_path()
    if not p.is_file():
        raise FileNotFoundError(f"game cards not found: {p}")
    return list(_load_cards_cached(str(p.resolve())))


# ---------------------------------------------------------------------------
# 351 卡 → 劇情群組 FSM 軸
# ---------------------------------------------------------------------------
def card_type_states(cards: Sequence[Mapping]) -> Tuple[str, ...]:
    """資料實際卡型集合（sorted：轉換確定性）。"""
    return tuple(sorted({str(c.get("card_type", "")) for c in cards}))


def story_group(cards: Optional[Sequence[Mapping]] = None) -> AxisGroup:
    """劇情群組：card_type FSM（依資料）+ story_role FSM（9 超類）。"""
    cards = load_cards() if cards is None else cards
    axes = {
        "card_type": AxisSpec("card_type", "fsm", states=card_type_states(cards)),
        "story_role": AxisSpec("story_role", "fsm", states=STORY_ROLES),
    }
    contract = GroupContract(
        group=STORY_GROUP,
        provides=(
            SignalSpec("card_type", "str", 0),
            SignalSpec("story_role", "str", 0),
        ),
    )
    return AxisGroup(name=STORY_GROUP, tick_rate=STORY_TICK_RATE, axes=axes, contract=contract)


def card_to_values(card: Mapping) -> Dict[str, Value]:
    """單卡 → story 群組軸值（未知卡型 ValueError：資料漂移要響亮）。"""
    ct = str(card.get("card_type", ""))
    role = STORY_ROLE_BY_CARD_TYPE.get(ct)
    if role is None:
        raise ValueError(f"unknown card_type {ct!r}: add it to STORY_ROLE_BY_CARD_TYPE")
    return {"card_type": ct, "story_role": role}


def cards_to_axis_snapshot(cards: Iterable[Mapping]) -> Dict[str, Dict[str, Value]]:
    """全量卡 → 軸值轉換快照 ``{card_id: 軸值 dict}``（M5 驗收對象）。"""
    snap: Dict[str, Dict[str, Value]] = {}
    for card in cards:
        cid = str(card.get("card_id", ""))
        if not cid:
            raise ValueError(f"card missing card_id: name={card.get('name')!r}")
        if cid in snap:
            raise ValueError(f"duplicate card_id: {cid!r}")
        snap[cid] = card_to_values(card)
    return snap


# ---------------------------------------------------------------------------
# axis_system 譜系 → 離散軸字典
# ---------------------------------------------------------------------------
def _axis_systems() -> Any:
    # 動態載入（Any 綁定）：engine 核心不靜態綁 game 根模組，也不把
    # axis_system/sim_systems 舊碼拖進 engine 的型別檢查範圍（R85 同理）
    mod: Any = importlib.import_module("axis_system")
    return mod.AXIS_SYSTEMS


def lineage_states(lineage: str) -> Dict[str, Tuple[str, ...]]:
    """譜系 → 離散軸字典 ``{軸名: (合法碼...)}``（真源 AXIS_SYSTEMS）。"""
    systems = _axis_systems()
    if lineage not in systems:
        raise KeyError(f"unknown lineage {lineage!r}; expected {sorted(systems)}")
    return {axis: tuple(codes) for axis, codes in systems[lineage].items()}


def lineage_axis_group(lineage: str, tick_rate: float = STORY_TICK_RATE) -> AxisGroup:
    """譜系 → fsm 離散軸群組（每軸一 SignalSpec 提供）。"""
    states = lineage_states(lineage)
    axes = {name: AxisSpec(name, "fsm", states=codes) for name, codes in states.items()}
    contract = GroupContract(
        group=f"lineage_{lineage}",
        provides=tuple(SignalSpec(name, "str", 0) for name in axes),
    )
    return AxisGroup(name=f"lineage_{lineage}", tick_rate=tick_rate, axes=axes, contract=contract)


def card_to_lineage(card: Mapping) -> Optional[Tuple[str, Dict[str, Value]]]:
    """權威解析（axis_system.resolve_card_axis）→ (譜系, 軸值) 或 None。

    `parse_axis_code` 原生值是 ``(code, label)`` 元組；此處取純碼
    （如 ``"D1"``）作離散軸值，標籤仍由 axis_system 查表。
    """
    mod: Any = importlib.import_module("axis_system")
    lineage, _code, axes = mod.resolve_card_axis(dict(card))
    if lineage is None or axes is None:
        return None
    normalized: Dict[str, Value] = {}
    for axis, raw in axes.items():
        if isinstance(raw, tuple):
            raw = raw[0] if raw else ""
        normalized[axis] = raw
    return lineage, normalized


def lineage_axis_snapshot(
    cards: Iterable[Mapping],
) -> Dict[str, Tuple[str, Dict[str, Value]]]:
    """可解析卡 → ``{card_id: (譜系, 軸值)}``（不可解析者排除）。"""
    snap: Dict[str, Tuple[str, Dict[str, Value]]] = {}
    for card in cards:
        cid = str(card.get("card_id", ""))
        if not cid:
            raise ValueError(f"card missing card_id: name={card.get('name')!r}")
        resolved = card_to_lineage(card)
        if resolved is not None:
            snap[cid] = resolved
    return snap
