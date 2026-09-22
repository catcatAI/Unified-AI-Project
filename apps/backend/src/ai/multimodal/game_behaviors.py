"""
Game Behavior Library - 可組合行為庫（v2：意圖→座標）

使用者要求：不是寫死腳本/模板當 AI，而是專案內的行為庫，由
狀態＋記憶＋LLM 來決策、編排、編輯參數，並在遊戲中即時執行。
v2 架構原則：意圖在 library 落成遊戲可接收的座標
（goto x,y,z / dig_at / look_at …），poller 只走引擎認的路
（find_path＋執行期精確朝向）。Python 端不做 yaw 數學、不盲走，
不跟客戶端搶方向盤。
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
    expand: Callable[[Dict[str, Any], Any], List[Action]]  # (params, state) -> actions
    success_criteria: str = "steps_done"  # steps_done | any_pickup | arrived | scan_done
    wait_for: str = ""  # "scan": 動作發完後等掃描結果再由 LLM 二段編排
    trigger: Optional[Callable[[Any], bool]] = None  # 反射觸發條件（每 tick 評估）
    adjust: Optional[Callable[[Dict[str, Any], BehaviorFeedback], Dict[str, Any]]] = None

    def with_defaults(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        merged = {k: v.get("default") for k, v in self.params_schema.items()}
        if params:
            merged.update({k: v for k, v in params.items() if k in self.params_schema})
        return merged


# 口語/短名 -> Minetest 節點名（scout 用；LLM 輸出哪種都接得住）
NODE_ALIASES = {
    "tree": "default:tree",
    "wood": "default:tree",
    "stone": "default:stone",
    "cobble": "default:cobble",
    "cobblestone": "default:cobble",
    "coal": "default:coal_ore",
    "sand": "default:sand",
    "dirt": "default:dirt",
    "water": "default:water_source",
    "grass": "default:dirt_with_grass",
    "flower": "default:dandelion_yellow",
}


def _pos_of(state: Any) -> Tuple[float, float, float]:
    try:
        prop = state.proprioception if state else None
        p = prop.position if prop else (0, 0, 0)
        return (float(p[0]), float(p[1]), float(p[2]))
    except Exception:
        return (0.0, 0.0, 0.0)


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


def _walk_expand(params: Dict[str, Any], _state: Any = None) -> List[Action]:
    # 意圖「往前走 N 步」落成座標語義：沿面朝走 steps*1.5 米。
    # 朝向數學在 poller（step_ahead 精確用自身 yaw），此處只給距離。
    steps = max(1, min(int(params.get("steps", 3)), 10))
    return [
        {
            "type": "step_ahead",
            "dist": steps * 1.5,
            "backward": bool(params.get("backward", False)),
        }
    ]


def _turn_expand(params: Dict[str, Any], _state: Any = None) -> List[Action]:
    import math

    degrees = float(params.get("degrees", 45))
    return [{"type": "look", "yaw_delta": math.radians(degrees), "pitch_delta": 0.0}]


def _dig_expand(params: Dict[str, Any], _state: Any = None) -> List[Action]:
    n = max(1, min(int(params.get("n", 5)), 20))
    actions: List[Action] = []
    if params.get("turn_first"):
        import math

        actions.append({"type": "look", "yaw_delta": math.radians(45), "pitch_delta": 0.0})
    actions.extend([{"type": "dig"} for _ in range(n)])
    return actions


def _xyz(params: Dict[str, Any], key: str = "pos") -> Optional[Dict[str, float]]:
    p = params.get(key)
    if isinstance(p, dict) and all(k in p for k in ("x", "y", "z")):
        try:
            return {"x": float(p["x"]), "y": float(p["y"]), "z": float(p["z"])}
        except (TypeError, ValueError):
            return None
    if isinstance(p, (list, tuple)) and len(p) == 3:
        try:
            return {"x": float(p[0]), "y": float(p[1]), "z": float(p[2])}
        except (TypeError, ValueError):
            return None
    for sep in (",", " "):
        if isinstance(p, str) and sep in p:
            try:
                x, y, z = [float(v) for v in p.split(sep) if v.strip() != ""]
                return {"x": x, "y": y, "z": z}
            except (TypeError, ValueError):
                continue
    return None


def _goto_expand(params: Dict[str, Any], _state: Any = None) -> List[Action]:
    pos = _xyz(params)
    return [{"type": "goto", "pos": pos}] if pos else []


def _look_at_expand(params: Dict[str, Any], _state: Any = None) -> List[Action]:
    pos = _xyz(params)
    return [{"type": "look_at", "pos": pos}] if pos else []


def _dig_at_expand(params: Dict[str, Any], _state: Any = None) -> List[Action]:
    pos = _xyz(params)
    return [{"type": "dig_at", "pos": pos}] if pos else []


def _place_at_expand(params: Dict[str, Any], _state: Any = None) -> List[Action]:
    pos = _xyz(params)
    return [{"type": "place_at", "pos": pos}] if pos else []


def _scout_expand(params: Dict[str, Any], _state: Any = None) -> List[Action]:
    raw = str(params.get("node", "default:tree"))
    node = NODE_ALIASES.get(raw, raw)
    if ":" not in node:
        node = f"default:{node}"
    radius = max(4, min(int(params.get("radius", 16)), 24))
    return [{"type": "scan", "nodes": [node], "radius": radius}]


def _dig_adjust(params: Dict[str, Any], fb: BehaviorFeedback) -> Dict[str, Any]:
    """沒挖到東西就先轉 45° 再挖；連續失敗則加長連挖次數。"""
    new = dict(params)
    if not fb.completed and not fb.pickups:
        new["turn_first"] = True
        new["n"] = min(int(new.get("n", 5)) + 2, 20)
    return new


def _place_expand(_params: Dict[str, Any], _state: Any = None) -> List[Action]:
    return [{"type": "place"}]


def _scan_expand(_params: Dict[str, Any], _state: Any = None) -> List[Action]:
    import math

    return [{"type": "look", "yaw_delta": math.radians(90), "pitch_delta": 0.0} for _ in range(4)]


def _speak_expand(params: Dict[str, Any], _state: Any = None) -> List[Action]:
    text = str(params.get("text", ""))[:300]
    return [{"type": "chat", "message": text}] if text else []


BEHAVIORS: Dict[str, Behavior] = {}


def _register(b: Behavior) -> Behavior:
    BEHAVIORS[b.behavior_id] = b
    return b


_register(
    Behavior(
        behavior_id="walk",
        description="沿面朝走 N*1.5 米（落成座標由引擎尋路走，有牆繞、落水浮）。轉彎用 turn，去指定地點用 goto。",
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
        expand=lambda params, state: [],
    )
)


def behavior_catalog_text(only: Optional[List[str]] = None) -> str:
    """給 LLM 的行為目錄（compose/adjust 提示詞用）。

    only: 只列需要的子集。高頻调用（15s 瞄準）用小目錄——prefill
    token 直接決定本地小模型的延遲，13 行全目錄太貴。
    """
    lines = []
    for b in BEHAVIORS.values():
        if only and b.behavior_id not in only:
            continue
        params = ", ".join(
            f"{k}({v.get('type')}, 預設 {v.get('default')}): {v.get('desc')}"
            for k, v in b.params_schema.items()
        )
        lines.append(f"- {b.behavior_id}: {b.description} 參數: {params or '無'}")
    return "\n".join(lines)


# 高頻瞄準用的小目錄（移動＋注視，不含掃描/對話/等待）
AIM_BEHAVIORS = ["look_at", "goto", "dig_at", "turn", "walk"]


def expand_behavior(
    behavior_id: str, params: Optional[Dict[str, Any]] = None, state: Any = None
) -> List[Action]:
    b = BEHAVIORS.get(behavior_id)
    if not b:
        logger.warning(f"Unknown behavior: {behavior_id}")
        return []
    return b.expand(b.with_defaults(params), state)


_register(
    Behavior(
        behavior_id="goto",
        description="走到世界座標 pos（x,y,z）。引擎尋路＋逐格推進，有牆繞、到不了就回報。",
        params_schema={
            "pos": {"type": "xyz", "default": None, "desc": "目的地座標 {x,y,z}"},
        },
        preconditions=_no_preconditions,
        expand=_goto_expand,
        success_criteria="arrived",
    )
)

_register(
    Behavior(
        behavior_id="scout",
        description="掃描周圍 node（如 default:tree），結果回傳後由 LLM 二段選點再走過去。找東西（樹/石/煤）都用它開頭。",
        params_schema={
            "node": {
                "type": "str",
                "default": "default:tree",
                "desc": "節點名（tree/stone/coal 可寫短名）",
            },
            "radius": {"type": "int", "default": 16, "desc": "掃描半徑 4-24"},
        },
        preconditions=_no_preconditions,
        expand=_scout_expand,
        success_criteria="scan_done",
        wait_for="scan",
    )
)

_register(
    Behavior(
        behavior_id="craft_one",
        description="按配方合成一次（recipe_id 或 auto）。材料夠不夠由上游判斷。",
        params_schema={
            "recipe_id": {"type": "str", "default": "auto", "desc": "配方短名或 auto"},
        },
        preconditions=_no_preconditions,
        expand=lambda params, state: [
            {"type": "craft", "recipe": str(params.get("recipe_id", "auto") or "auto")}
        ],
    )
)


def _surface_trigger(state: Any) -> bool:
    """缺氧或灼傷：身體訊號，不是世界預測。"""
    try:
        prop = state.proprioception if state else None
        if prop is None:
            return False
        if int(getattr(prop, "breath", 10) or 10) < 10:
            return True
        return bool(getattr(prop, "is_in_lava", False))
    except Exception:
        return False


_register(
    Behavior(
        behavior_id="surface",
        description="【反射】缺氧或站在岩漿里時上浮 1.5 米。保命用，不用選它（觸發自動開火）。",
        params_schema={},
        preconditions=_no_preconditions,
        expand=lambda params, state: [{"type": "rise"}],
        trigger=_surface_trigger,
    )
)

_register(
    Behavior(
        behavior_id="look_vision",
        description="睜眼看：15 條視線掃描視錐（5 方向×3 俯仰，有遮擋、看得到水和樹）。想瞄準東西、確認前面是什麼都用它開頭。",
        params_schema={
            "range": {"type": "int", "default": 24, "desc": "視距 4-32"},
        },
        preconditions=_no_preconditions,
        expand=lambda params, state: [
            {"type": "vision", "range": max(4, min(int(params.get("range", 24)), 32))}
        ],
        success_criteria="vision_done",
        wait_for="vision",
    )
)

_register(
    Behavior(
        behavior_id="look_at",
        description="轉頭注視世界座標 pos（執行期精確計算朝向）。",
        params_schema={
            "pos": {"type": "xyz", "default": None, "desc": "注視點座標 {x,y,z}"},
        },
        preconditions=_no_preconditions,
        expand=_look_at_expand,
    )
)

_register(
    Behavior(
        behavior_id="dig_at",
        description="面朝世界座標 pos 並挖掉那格（6 米內、非空氣）。指哪打哪。",
        params_schema={
            "pos": {"type": "xyz", "default": None, "desc": "目標格座標 {x,y,z}"},
        },
        preconditions=_no_preconditions,
        expand=_dig_at_expand,
        success_criteria="any_pickup",
    )
)

_register(
    Behavior(
        behavior_id="place_at",
        description="在世界座標 pos 放一個方塊（該格須為空且下方實心）。",
        params_schema={
            "pos": {"type": "xyz", "default": None, "desc": "目標格座標 {x,y,z}"},
        },
        preconditions=_needs_placeable,
        expand=_place_at_expand,
    )
)


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


# 舊迴圈（executor/L1 SkillContext）進遊戲的唯一翻譯器。
# 意圖（skill＋params）只能翻成行為庫的語言；翻不出來（place/build/
# eat／做不出的 craft）就禁排——此前三處 abstain 補丁都是在這裡
# 漏水的症狀，現在由翻譯器從架構上保證：沒有「亂放」這個動詞。
def skill_to_behavior(
    skill: str,
    params: Optional[Dict[str, Any]] = None,
    craftable: Optional[Callable[[str], bool]] = None,
) -> Tuple[str, Dict[str, Any]]:
    """(skill, params) -> (behavior_id, params)，翻不出回 ("", {})."""
    params = params or {}
    if skill in ("move", "navigate"):
        try:
            fwd = float(params.get("forward", 1.0))
        except (TypeError, ValueError):
            fwd = 1.0
        return "walk", {"steps": 3, "backward": bool(fwd < 0)}
    if skill in ("dig", "combat"):
        return "dig_burst", {"n": 1}
    if skill == "look":
        # 只有 yaw 轉得出來（turn）；pitch 抬頭低頭沒有對應動詞，
        # 真瞄準走 look_at。零轉動直接禁排（此前全是空轉）。
        try:
            yaw = float(params.get("yaw", 0.0) or 0.0)
        except (TypeError, ValueError):
            yaw = 0.0
        if yaw == 0.0:
            return "", {}
        import math

        return "turn", {"degrees": math.degrees(yaw)}
    if skill == "craft":
        rid = str(params.get("recipe_id", "auto") or "auto")
        if craftable is not None and not craftable(rid):
            return "", {}
        return "craft_one", {"recipe_id": rid}
    # place/build/eat: 沒有無目的的動詞。定向放置走 place_one/place_at
    # （runner/chat/plan），吃東西缺 use 動作（poller 待補），藍圖缺執行器。
    return "", {}
