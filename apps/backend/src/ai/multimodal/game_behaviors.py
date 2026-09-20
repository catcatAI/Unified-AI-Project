"""
Game Behavior Library - 可組合行為庫

使用者要求：不是寫死腳本/模板當 AI，而是專案內的行為庫
（走、轉、挖、放、看、說、等），由狀態＋記憶＋LLM 來
決策、編排、編輯參數，並在遊戲中即時執行。

設計：
- Behavior = 宣告式單位：id、給 LLM 看的 description、參數 schema、
  前置檢查、展開成 poller 動作、完成判準、反饋改參數（adjust）。
- LLM 做兩件事：compose（選行為＋填參數）與 adjust（失敗後改參數），
  都走 LLMGameInterface 的結構化輸出；規則只做保底。
- 執行由 agent 的 BehaviorRunner 驅動：一次一個動作餵給 bridge，
  按完成判準/超時結算，再把結果餵回 LLM 改參數。
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Poller 動作就是普通 dict（{"type": "move", ...}），此處只做型別別名。
Action = Dict[str, Any]


@dataclass
class BehaviorFeedback:
    """一次行為執行的結算，供 adjust 改參數用"""

    behavior_id: str
    params: Dict[str, Any]
    ticks_used: int
    pickups: Dict[str, int]  # 執行期間背包淨增長
    completed: bool
    fail_reason: str = ""  # "", "timeout", "blocked", "missing_item"


@dataclass
class Behavior:
    """單個可組合行為"""

    behavior_id: str
    description: str  # 給 LLM 看的用途說明
    params_schema: Dict[str, Dict[str, Any]]  # name -> {type, default, desc}
    preconditions: Callable[[Any], Tuple[bool, List[str]]]  # (state) -> (ok, missing)
    expand: Callable[[Dict[str, Any]], List[Action]]  # params -> poller actions
    success_criteria: str = "steps_done"
    adjust: Optional[Callable[[Dict[str, Any], BehaviorFeedback], Dict[str, Any]]] = None

    def with_defaults(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        merged = {k: v.get("default") for k, v in self.params_schema.items()}
        if params:
            merged.update({k: v for k, v in params.items() if k in self.params_schema})
        return merged


def _inventory_of(state: Any) -> Dict[str, Any]:
    try:
        prop = state.proprioception if state else None
        return dict((prop.inventory if prop else {}) or {})
    except Exception:
        return {}


def _has_placeable(inv: Dict[str, Any]) -> bool:
    non_nodes = ("pickaxe", "axe", "shovel", "sword", "stick", "coal_lump", "apple")
    for key, val in inv.items():
        try:
            if int(val) > 0 and not any(n in str(key) for n in non_nodes):
                return True
        except (TypeError, ValueError):
            continue
    return False


def _no_preconditions(_state: Any) -> Tuple[bool, List[str]]:
    return True, []


def _needs_placeable(state: Any) -> Tuple[bool, List[str]]:
    if _has_placeable(_inventory_of(state)):
        return True, []
    return False, ["placeable block"]


def _walk_expand(params: Dict[str, Any]) -> List[Action]:
    steps = max(1, min(int(params.get("steps", 3)), 10))
    backward = bool(params.get("backward", False))
    fwd = -1.0 if backward else 1.0
    return [{"type": "move", "forward": fwd, "strafe": 0.0} for _ in range(steps)]


def _turn_expand(params: Dict[str, Any]) -> List[Action]:
    import math

    degrees = float(params.get("degrees", 45))
    return [{"type": "look", "yaw_delta": math.radians(degrees), "pitch_delta": 0.0}]


def _dig_expand(params: Dict[str, Any]) -> List[Action]:
    n = max(1, min(int(params.get("n", 5)), 20))
    actions: List[Action] = []
    if params.get("turn_first"):
        import math

        actions.append({"type": "look", "yaw_delta": math.radians(45), "pitch_delta": 0.0})
    actions.extend([{"type": "dig"} for _ in range(n)])
    return actions


def _dig_adjust(params: Dict[str, Any], fb: BehaviorFeedback) -> Dict[str, Any]:
    """沒挖到東西就先轉 45° 再挖；連續失敗則加長連挖次數。"""
    new = dict(params)
    if not fb.completed and not fb.pickups:
        new["turn_first"] = True
        new["n"] = min(int(new.get("n", 5)) + 2, 20)
    return new


def _place_expand(_params: Dict[str, Any]) -> List[Action]:
    return [{"type": "place"}]


def _scan_expand(_params: Dict[str, Any]) -> List[Action]:
    import math

    return [
        {"type": "look", "yaw_delta": math.radians(90), "pitch_delta": 0.0} for _ in range(4)
    ]


def _speak_expand(params: Dict[str, Any]) -> List[Action]:
    text = str(params.get("text", ""))[:300]
    return [{"type": "chat", "message": text}] if text else []


BEHAVIORS: Dict[str, Behavior] = {}


def _register(b: Behavior) -> Behavior:
    BEHAVIORS[b.behavior_id] = b
    return b


_register(
    Behavior(
        behavior_id="walk",
        description="向前（或向後）走 N 步，每步約 1.5 米。走路只認面朝方向，轉彎用 turn。",
        params_schema={
            "steps": {"type": "int", "default": 3, "desc": "步數 1-10"},
            "backward": {"type": "bool", "default": False, "desc": "是否倒退"},
        },
        preconditions=_no_preconditions,
        expand=_walk_expand,
    )
)

_register(
    Behavior(
        behavior_id="turn",
        description="原地轉向。撞牆、換方向、環顧前先轉都用它。",
        params_schema={
            "degrees": {"type": "float", "default": 45, "desc": "轉幾度，正值右轉"},
        },
        preconditions=_no_preconditions,
        expand=_turn_expand,
    )
)

_register(
    Behavior(
        behavior_id="dig_burst",
        description="向前連挖 N 下。手上有什麼掉什麼；沒挖到會自動先轉向再試。",
        params_schema={
            "n": {"type": "int", "default": 5, "desc": "連挖次數 1-20"},
            "turn_first": {"type": "bool", "default": False, "desc": "先轉 45 再挖"},
        },
        preconditions=_no_preconditions,
        expand=_dig_expand,
        success_criteria="any_pickup",
        adjust=_dig_adjust,
    )
)

_register(
    Behavior(
        behavior_id="place_one",
        description="在身邊合適空位放一個方塊（手牌或背包第一個可放的）。",
        params_schema={},
        preconditions=_needs_placeable,
        expand=_place_expand,
    )
)

_register(
    Behavior(
        behavior_id="look_scan",
        description="原地轉一圈看四周（4×90°）。",
        params_schema={},
        preconditions=_no_preconditions,
        expand=_scan_expand,
    )
)

_register(
    Behavior(
        behavior_id="speak",
        description="在遊戲裡說一句話，玩家看得到。",
        params_schema={
            "text": {"type": "str", "default": "", "desc": "要說的話（300 字內）"},
        },
        preconditions=_no_preconditions,
        expand=_speak_expand,
    )
)

_register(
    Behavior(
        behavior_id="wait",
        description="原地待命 N tick（約 N/10 秒），什麼都不做。",
        params_schema={
            "ticks": {"type": "int", "default": 20, "desc": "等待 tick 數"},
        },
        preconditions=_no_preconditions,
        expand=lambda _p: [],
    )
)


def behavior_catalog_text() -> str:
    """給 LLM 的行為目錄（compose/adjust 提示詞用）"""
    lines = []
    for b in BEHAVIORS.values():
        params = ", ".join(
            f"{k}({v.get('type')}, 預設 {v.get('default')}): {v.get('desc')}"
            for k, v in b.params_schema.items()
        )
        lines.append(f"- {b.behavior_id}: {b.description} 參數: {params or '無'}")
    return "\n".join(lines)


def expand_behavior(behavior_id: str, params: Optional[Dict[str, Any]] = None) -> List[Action]:
    b = BEHAVIORS.get(behavior_id)
    if not b:
        logger.warning(f"Unknown behavior: {behavior_id}")
        return []
    return b.expand(b.with_defaults(params))


class BehaviorOrder(BaseModel):
    """LLM 的行為編排輸出契約"""

    behavior_id: str = Field(description="行為 id，必須是目錄中的一個")
    params: Dict[str, Any] = Field(default_factory=dict, description="行為參數")
    reasoning: str = Field(default="", description="一句話說明為什麼選它")


class ChatDecision(BaseModel):
    """LLM 的對話決策輸出契約：說什麼＋做什麼"""

    say: str = Field(default="", description="在遊戲裡說的話（可空）")
    behavior_id: str = Field(default="", description="順帶執行的行為 id（可空）")
    params: Dict[str, Any] = Field(default_factory=dict, description="行為參數")
    reasoning: str = Field(default="", description="一句話說明")
