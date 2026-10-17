# -*- coding: utf-8 -*-
"""M9 angela_agent 閘道口寫入驗收（§6.4「L0 動作寫入戰鬥/空間軸」）。

- ACTION_STATES ↔ 後端 SkillID 九值守漂移（engine 字面量對齊檢查）
- _queue_skill 閘道口受理即寫 agent 軸群組（真實 AngelaAutonomousAgent）
- 未知技能：寫入失敗只記日誌、閘道口照常 abstain 不擋主流程
- get_agent_axis_snapshot 寫入器不可用時降級回 {}
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

_GAME_ROOT = Path(__file__).resolve().parents[3] / "apps" / "game-rpg"
if str(_GAME_ROOT) not in sys.path:
    sys.path.insert(0, str(_GAME_ROOT))


def _skill_ctx(skill, params=None, priority=1.0, triggers=None):
    """SkillContext 鴨子型別替身（與 dataclass 欄位同構）。"""
    return SimpleNamespace(
        active_skill=skill,
        params=params or {},
        priority=priority,
        interrupt_on=[],
        continuous_bias=None,
        discrete_triggers=triggers,
    )


class TestActionStatesSync:
    def test_action_states_match_skillid(self):
        from ai.multimodal.game_structs import SkillID

        from engine.agent_bridge import ACTION_STATES

        assert ACTION_STATES == ("idle",) + tuple(s.value for s in SkillID)


class TestQueueSkillWritesAxes:
    def test_move_intent_written_on_gateway_accept(self):
        from ai.autonomous.angela_agent import AngelaAutonomousAgent
        from ai.multimodal.game_structs import SkillID

        agent = AngelaAutonomousAgent()
        assert agent.get_agent_axis_snapshot()["action"] == "idle"
        agent._queue_skill(_skill_ctx(SkillID.MOVE, {"forward": 0.3}))
        snap = agent.get_agent_axis_snapshot()
        assert snap["action"] == "move"
        assert snap["move_forward"] == 0.3
        assert snap["move_yaw"] == 0.0

    def test_combat_intent_engages_combat_axis(self):
        from ai.autonomous.angela_agent import AngelaAutonomousAgent
        from ai.multimodal.game_structs import SkillID

        agent = AngelaAutonomousAgent()
        agent._queue_skill(_skill_ctx(SkillID.COMBAT, {}, priority=0.5))
        snap = agent.get_agent_axis_snapshot()
        assert snap["action"] == "combat"
        assert snap["combat"] == "engaged"
        assert snap["priority"] == 0.5

    def test_unknown_skill_logged_not_raised(self):
        from ai.autonomous.angela_agent import AngelaAutonomousAgent

        class BadSkill:
            value = "hax"

        agent = AngelaAutonomousAgent()
        # 寫入 ValueError → logger.debug；閘道口續行（無動詞→abstain return）
        agent._queue_skill(_skill_ctx(BadSkill()))
        assert agent.get_agent_axis_snapshot()["action"] == "idle"

    def test_snapshot_degrades_when_writer_unavailable(self, monkeypatch):
        from ai.autonomous.angela_agent import AngelaAutonomousAgent

        agent = AngelaAutonomousAgent()

        def boom():
            raise RuntimeError("engine missing")

        monkeypatch.setattr(agent, "_agent_writer", boom)
        assert agent.get_agent_axis_snapshot() == {}
