# -*- coding: utf-8 -*-
"""萬物皆軸引擎 — SkillContext → agent 軸群組橋接（計畫 §6.4 M9）。

把五層遊戲 AI 的 ``game_structs.SkillContext``（L1 Selector／L2 Executor
產出、經 ``angela_agent._queue_skill`` 閘道口受理）轉寫成 agent 群組軸值
——「L0 動作寫入戰鬥/空間軸」（§6.4 遠期項）。

映射證據（不發明語義，逐軸附來源）：

- ``action``（fsm）← ``ctx.active_skill``。狀態域 = 9 個 SkillID 值 +
  ``"idle"``；SkillID 定義在後端 ``ai.multimodal.game_structs``，此處
  以字面量對齊（後端測試 ``test_action_states_match_skillid`` 守漂移）。
- ``move_forward``（continuous [-1,1]）← ``params["forward"]``。
  move/navigate 未帶參時內建前進 1.0（``game_behaviors._skill_to_walk``
  預設 fwd=1.0），其餘技能 0.0；越界夾域＝政策解碼先例
  （``game_policy._decode_move_actions`` ``np.clip(-1,1)``）。
- ``move_yaw``（continuous [-π,π]）← ``params["yaw"]``。缺省 0.0
  （``game_behaviors._skill_to_turn`` 預設 0.0 且零轉動禁排）；弧度制
  （``math.degrees(yaw)`` 先例）。
- ``combat``（fsm off/engaged）← skill=="combat" 或
  ``discrete_triggers`` 含 ``"attack"``（membership 判定＝
  ``game_agent._compose_actions`` 觸發鍵清單先例；dig 不算戰鬥——
  行為語把二者都翻成 dig_burst 是 Luanti 動詞匱乏，非語義等同）。
- ``priority``（continuous [0,1]）← ``ctx.priority``（SkillParams
  預設 1.0、selector 低優先 0.1）。

寫入時點＝閘道口**受理**（意圖），非「已送達 Luanti」：軸記錄當前
L0/L1 意圖，不論後續行為語動詞是否可翻譯或背壓丟棄。純 stdlib。
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Tuple

from engine.axes import AxisGroup, AxisSpec, Value
from engine.contracts import GroupContract, SignalSpec

if TYPE_CHECKING:  # pragma: no cover
    from engine.pipeline import Handler, TickContext

AGENT_GROUP = "agent"
# angela_agent AngelaConfig.tick_interval=0.1（10Hz 主迴圈；其
# _queue_skill 註解「executor's 10Hz writes」同源）。
AGENT_TICK_RATE = 10.0

# SkillID(str, Enum) 九值 + idle（後端測試守漂移）。
ACTION_STATES: Tuple[str, ...] = (
    "idle",
    "move",
    "dig",
    "place",
    "craft",
    "combat",
    "navigate",
    "eat",
    "build",
    "look",
)
COMBAT_STATES: Tuple[str, ...] = ("off", "engaged")


def agent_group() -> AxisGroup:
    """agent 群組：戰鬥側（action/combat/priority）+ 空間側（move_*）。"""
    axes = {
        "action": AxisSpec("action", "fsm", states=ACTION_STATES),
        "move_forward": AxisSpec("move_forward", "continuous", lo=-1.0, hi=1.0),
        "move_yaw": AxisSpec("move_yaw", "continuous", lo=-math.pi, hi=math.pi),
        "combat": AxisSpec("combat", "fsm", states=COMBAT_STATES),
        "priority": AxisSpec("priority", "continuous", lo=0.0, hi=1.0),
    }
    contract = GroupContract(
        group=AGENT_GROUP,
        provides=(
            SignalSpec("action", "str", 0),
            SignalSpec("move_forward", "float", 3),
            SignalSpec("move_yaw", "float", 3),
            SignalSpec("combat", "str", 0),
            SignalSpec("priority", "float", 3),
        ),
    )
    return AxisGroup(name=AGENT_GROUP, tick_rate=AGENT_TICK_RATE, axes=axes, contract=contract)


def idle_values() -> Dict[str, Value]:
    """未受理任何技能前的軸值（契約 provides 全覆蓋：handler 首 fire 即有值）。"""
    return {
        "action": "idle",
        "move_forward": 0.0,
        "move_yaw": 0.0,
        "combat": "off",
        "priority": 0.0,
    }


def _skill_value(active_skill: Any) -> str:
    """SkillID（enum 或字串）→ 軸值字串；未知技能響亮 raise（資料漂移）。"""
    raw = getattr(active_skill, "value", active_skill)
    name = str(raw)
    if name not in ACTION_STATES:
        raise ValueError(f"unknown skill {name!r}: add it to ACTION_STATES (SkillID drift)")
    return name


def _float_in(value: Any, lo: float, hi: float, default: float) -> float:
    """參數 → 夾域 float（壞值回 default＝walk/turn try/except 先例）。"""
    try:
        x = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(x):
        return default
    return min(max(x, lo), hi)


def skill_context_to_values(ctx: Any) -> Dict[str, Value]:
    """SkillContext → agent 軸值 dict（未知技能 raise；數值夾域不 raise）。"""
    skill = _skill_value(ctx.active_skill)
    params: Mapping[str, Any] = dict(getattr(ctx, "params", None) or {})
    fwd_default = 1.0 if skill in ("move", "navigate") else 0.0
    forward = _float_in(params.get("forward", fwd_default), -1.0, 1.0, fwd_default)
    yaw = _float_in(params.get("yaw", 0.0), -math.pi, math.pi, 0.0)
    triggers = getattr(ctx, "discrete_triggers", None)
    engaged = skill == "combat" or (isinstance(triggers, Mapping) and "attack" in triggers)
    priority = _float_in(getattr(ctx, "priority", 1.0), 0.0, 1.0, 1.0)
    return {
        "action": skill,
        "move_forward": forward,
        "move_yaw": yaw,
        "combat": "engaged" if engaged else "off",
        "priority": priority,
    }


class AgentAxisWriter:
    """agent 群組寫入器：受理 SkillContext → 驗域後存軸值（單一例項）。

    - ``write(ctx)``：轉換（未知技能 raise）+ 逐軸 ``contains`` 驗域
      （越界 raise，與 PackedGroup._encode 同律）後合入。
    - ``snapshot()``：軸值副本（M8 訊號表副本語意）。
    - ``handler()``：EnginePipeline 每 fire 發布閉包——provides 全覆蓋
      emit（未寫時為 idle 慣例值，同 story 心跳必備訊號全備）。
    """

    def __init__(self, group: Optional[AxisGroup] = None) -> None:
        self.group: AxisGroup = group or agent_group()
        self._values: Dict[str, Value] = idle_values()

    @property
    def values(self) -> Dict[str, Value]:
        """目前軸值（唯讀語意：回內部 dict 供 handler 發布；勿外部改）。"""
        return self._values

    def write(self, ctx: Any) -> Dict[str, Value]:
        """轉換+驗域+合入；回全量軸值副本。"""
        values = skill_context_to_values(ctx)
        for name, val in values.items():
            spec = self.group.axes.get(name)
            if spec is None:
                raise ValueError(f"agent group has no axis {name!r}")
            if not spec.contains(val):
                raise ValueError(f"agent axis {name!r} rejects {val!r} (out of domain)")
        self._values.update(values)
        return dict(self._values)

    def snapshot(self) -> Dict[str, Value]:
        """軸值副本。"""
        return dict(self._values)

    def handler(self) -> "Handler":
        """給 EnginePipeline 的發布閉包：每次本組 fire 即 emit 全部 provides。"""
        provides = self.group.contract.provide_names()

        def _publish(ctx: "TickContext") -> None:
            current = self._values
            for name in provides:
                ctx.emit(name, current[name])

        return _publish
