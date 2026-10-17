# -*- coding: utf-8 -*-
"""萬物皆軸引擎 M9 測試（§6.4「L0 動作寫入戰鬥/空間軸」遠期項落地驗收）。

- agent 群組形狀：10Hz（angela_agent 10Hz 主迴圈證據）、戰鬥側+空間側軸、
  契約 provides 全覆蓋
- SkillContext → 軸值映射：逐軸證據語義（walk 內建前進、turn 預設 0、
  enum 接受、戰鬥 engaged 路徑、未知技能響亮 raise、clip/壞值夾域）
- AgentAxisWriter：初值 idle、寫入後副本語意、失敗不改狀態
- 管線發布：handler 每 fire emit 全 provides（首 fire=idle 慣例值）
"""

from __future__ import annotations

import math
from enum import Enum
from types import SimpleNamespace

import pytest
from engine.agent_bridge import (
    ACTION_STATES,
    AGENT_GROUP,
    AGENT_TICK_RATE,
    AgentAxisWriter,
    agent_group,
    idle_values,
    skill_context_to_values,
)
from engine.pipeline import EnginePipeline


def ctx(skill="move", params=None, priority=1.0, triggers=None):
    """SkillContext 鴨子型別替身（engine 不依賴後端 ai.multimodal）。"""
    return SimpleNamespace(
        active_skill=skill,
        params=params or {},
        priority=priority,
        interrupt_on=[],
        continuous_bias=None,
        discrete_triggers=triggers,
    )


class TestAgentGroupShape:
    def test_group_metadata(self):
        g = agent_group()
        assert g.name == AGENT_GROUP
        assert g.tick_rate == AGENT_TICK_RATE == 10.0

    def test_axis_kinds_and_domains(self):
        g = agent_group()
        assert set(g.axes) == {"action", "move_forward", "move_yaw", "combat", "priority"}
        assert g.axes["action"].kind == "fsm"
        assert g.axes["action"].states == ACTION_STATES
        assert g.axes["combat"].kind == "fsm"
        assert g.axes["combat"].states == ("off", "engaged")
        mf = g.axes["move_forward"]
        assert (mf.kind, mf.lo, mf.hi) == ("continuous", -1.0, 1.0)
        my = g.axes["move_yaw"]
        assert (my.kind, my.lo, my.hi) == ("continuous", -math.pi, math.pi)

    def test_contract_provides_all_axes(self):
        g = agent_group()
        assert set(g.contract.provide_names()) == set(g.axes)
        dtypes = {s.name: s.dtype for s in g.contract.provides}
        assert dtypes == {
            "action": "str",
            "move_forward": "float",
            "move_yaw": "float",
            "combat": "str",
            "priority": "float",
        }

    def test_idle_values_cover_contract(self):
        assert set(idle_values()) == set(agent_group().contract.provide_names())
        assert idle_values() == {
            "action": "idle",
            "move_forward": 0.0,
            "move_yaw": 0.0,
            "combat": "off",
            "priority": 0.0,
        }


class TestSkillContextToValues:
    def test_move_with_params(self):
        v = skill_context_to_values(ctx("move", {"forward": -0.5, "yaw": 0.25}))
        assert v == {
            "action": "move",
            "move_forward": -0.5,
            "move_yaw": 0.25,
            "combat": "off",
            "priority": 1.0,
        }

    def test_move_and_navigate_default_forward_one(self):
        # walk 內建前進（_skill_to_walk 預設 fwd=1.0）
        for skill in ("move", "navigate"):
            assert skill_context_to_values(ctx(skill, {}))["move_forward"] == 1.0

    def test_non_locomotion_skill_forward_zero(self):
        assert skill_context_to_values(ctx("dig", {}))["move_forward"] == 0.0

    def test_look_yaw_param_written(self):
        # turn 預設 yaw=0.0、非零才排（_skill_to_turn）
        assert skill_context_to_values(ctx("look", {"yaw": 0.1}))["move_yaw"] == 0.1
        assert skill_context_to_values(ctx("look", {}))["move_yaw"] == 0.0

    def test_enum_skill_accepted(self):
        class SkillID(str, Enum):
            MOVE = "move"

        assert skill_context_to_values(ctx(SkillID.MOVE, {}))["action"] == "move"

    def test_combat_engaged_paths(self):
        assert skill_context_to_values(ctx("combat", {}))["combat"] == "engaged"
        triggers = {"attack": 1.0}
        assert skill_context_to_values(ctx("move", {}, triggers=triggers))["combat"] == ("engaged")
        # dig 不算戰鬥：行為語把二者都翻成 dig_burst 是 Luanti 動詞匱乏
        assert skill_context_to_values(ctx("dig", {}))["combat"] == "off"

    def test_unknown_skill_raises(self):
        with pytest.raises(ValueError, match="ACTION_STATES"):
            skill_context_to_values(ctx("fly"))

    def test_out_of_range_values_clipped(self):
        # 政策解碼 np.clip 先例（_decode_move_actions）
        assert skill_context_to_values(ctx("move", {"forward": 99.0}))["move_forward"] == 1.0
        assert skill_context_to_values(ctx("look", {"yaw": 100.0}))["move_yaw"] == math.pi
        assert skill_context_to_values(ctx("move", {}, priority=5.0))["priority"] == 1.0
        assert skill_context_to_values(ctx("move", {}, priority=-1.0))["priority"] == 0.0

    def test_bad_param_values_fall_back_to_default(self):
        # 壞值回 default＝walk/turn try/except 先例
        assert skill_context_to_values(ctx("move", {"yaw": "abc"}))["move_yaw"] == 0.0
        assert skill_context_to_values(ctx("move", {"forward": None}))["move_forward"] == 1.0
        assert skill_context_to_values(ctx("dig", {"forward": float("nan")}))["move_forward"] == (
            0.0
        )


class TestAgentAxisWriter:
    def test_initial_snapshot_is_idle(self):
        w = AgentAxisWriter()
        assert w.snapshot() == idle_values()

    def test_write_updates_and_returns_fresh_copy(self):
        w = AgentAxisWriter()
        out = w.write(ctx("combat", {}, priority=0.4))
        assert out["action"] == "combat"
        assert out["combat"] == "engaged"
        assert out["priority"] == 0.4
        snap = w.snapshot()
        snap["action"] = "move"  # 改副本不影響寫入器
        assert w.snapshot()["action"] == "combat"

    def test_failed_write_keeps_previous_state(self):
        w = AgentAxisWriter()
        w.write(ctx("move", {"forward": 0.7}))
        with pytest.raises(ValueError, match="ACTION_STATES"):
            w.write(ctx("fly"))
        assert w.snapshot()["action"] == "move"
        assert w.snapshot()["move_forward"] == 0.7


class TestPipelinePublish:
    def test_fire_publishes_written_values(self):
        w = AgentAxisWriter()
        p = EnginePipeline()
        p.register_group(w.group, w.handler())
        p.startup()
        p.tick()  # 首 fire：未寫 → idle 慣例值（契約全覆蓋）
        assert p.signal_snapshot()["agent"]["action"] == "idle"
        w.write(ctx("move", {"forward": 0.6, "yaw": -0.3}))
        p.tick()
        got = p.signal_snapshot()["agent"]
        assert got["action"] == "move"
        assert got["move_forward"] == 0.6
        assert got["move_yaw"] == -0.3
        assert got["combat"] == "off"
        assert got["priority"] == 1.0

    def test_publish_reflects_latest_write_without_new_write(self):
        w = AgentAxisWriter()
        p = EnginePipeline()
        p.register_group(w.group, w.handler())
        p.startup()
        w.write(ctx("combat", {"forward": 0.0}, priority=0.2))
        p.tick()
        p.tick()  # 第二 fire：無新寫入 → 維持同一軸值
        assert p.signal_snapshot()["agent"]["action"] == "combat"
        assert p.signal_snapshot()["agent"]["combat"] == "engaged"
