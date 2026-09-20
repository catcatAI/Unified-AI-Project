"""Tests for the game behavior library + bridge chat channel.

The behavior library is the user-demanded decision surface: LLM composes
(behavior_id + params) from the catalog, the runner expands to poller
actions, feedback edits params via adjust().
"""

import math

import pytest

from ai.multimodal.game_behaviors import (
    BEHAVIORS,
    BehaviorFeedback,
    BehaviorOrder,
    ChatDecision,
    behavior_catalog_text,
    expand_behavior,
)
from ai.multimodal.game_structs import GameState, Proprioception


def _state(inv):
    return GameState(proprioception=Proprioception(inventory=dict(inv)))


class TestBehaviorRegistry:
    def test_all_behaviors_registered(self):
        assert set(BEHAVIORS) == {
            "walk",
            "turn",
            "dig_burst",
            "place_one",
            "look_scan",
            "speak",
            "wait",
            "goto",
            "scout",
            "look_at",
            "dig_at",
            "place_at",
            "look_vision",
            "craft_one",
            "surface",
        }

    def test_walk_is_coordinate_step_ahead(self):
        acts = expand_behavior("walk", {"steps": 3})
        assert acts == [{"type": "step_ahead", "dist": 4.5, "backward": False}]

    def test_goto_needs_xyz(self):
        assert expand_behavior("goto", {"pos": {"x": 1, "y": 2, "z": 3}}) == [
            {"type": "goto", "pos": {"x": 1.0, "y": 2.0, "z": 3.0}}
        ]
        assert expand_behavior("goto", {}) == []
        assert expand_behavior("goto", {"pos": "1,2,3"}) == [
            {"type": "goto", "pos": {"x": 1.0, "y": 2.0, "z": 3.0}}
        ]

    def test_scout_normalizes_node_names(self):
        acts = expand_behavior("scout", {"node": "tree", "radius": 16})
        assert acts == [{"type": "scan", "nodes": ["default:tree"], "radius": 16}]
        acts = expand_behavior("scout", {"node": "default:stone", "radius": 99})
        assert acts[0]["radius"] == 24

    def test_dig_at_and_look_at(self):
        p = {"x": 0, "y": 0, "z": 0}
        assert expand_behavior("dig_at", {"pos": p}) == [{"type": "dig_at", "pos": p}]
        assert expand_behavior("look_at", {"pos": p}) == [{"type": "look_at", "pos": p}]
        assert expand_behavior("place_at", {"pos": p}) == [{"type": "place_at", "pos": p}]

    def test_scout_waits_for_scan(self):
        assert BEHAVIORS["scout"].wait_for == "scan"
        assert BEHAVIORS["goto"].success_criteria == "arrived"

    def test_aim_subset_catalog(self):
        from ai.multimodal.game_behaviors import AIM_BEHAVIORS, behavior_catalog_text

        assert set(AIM_BEHAVIORS) == {"look_at", "goto", "dig_at", "turn", "walk"}
        small = behavior_catalog_text(only=AIM_BEHAVIORS)
        assert "scout" not in small and "goto" in small
        assert len(small) < len(behavior_catalog_text())

    def test_look_vision(self):
        acts = expand_behavior("look_vision", {"range": 24})
        assert acts == [{"type": "vision", "range": 24}]
        assert expand_behavior("look_vision", {"range": 99}) == [{"type": "vision", "range": 32}]
        assert BEHAVIORS["look_vision"].wait_for == "vision"
        assert BEHAVIORS["look_vision"].success_criteria == "vision_done"

    def test_catalog_lists_everything(self):
        text = behavior_catalog_text()
        for bid in BEHAVIORS:
            assert bid in text

    def test_unknown_behavior_expands_empty(self):
        assert expand_behavior("nope", {}) == []


class TestBehaviorExpansion:
    def test_walk_steps_bounded(self):
        acts = expand_behavior("walk", {"steps": 3})
        assert acts == [{"type": "step_ahead", "dist": 4.5, "backward": False}]
        assert expand_behavior("walk", {"steps": 99}) == [
            {"type": "step_ahead", "dist": 15.0, "backward": False}
        ]
        back = expand_behavior("walk", {"steps": 2, "backward": True})
        assert back == [{"type": "step_ahead", "dist": 3.0, "backward": True}]

    def test_turn_degrees(self):
        acts = expand_behavior("turn", {"degrees": 90})
        assert len(acts) == 1
        assert acts[0]["type"] == "look"
        assert acts[0]["yaw_delta"] == pytest.approx(math.radians(90))

    def test_dig_burst_with_turn_first(self):
        acts = expand_behavior("dig_burst", {"n": 2, "turn_first": True})
        assert acts[0]["type"] == "look"
        assert [a["type"] for a in acts[1:]] == ["dig", "dig"]

    def test_speak_empty_text_expands_empty(self):
        assert expand_behavior("speak", {"text": ""}) == []
        acts = expand_behavior("speak", {"text": "嗨"})
        assert acts == [{"type": "chat", "message": "嗨"}]

    def test_scan_is_full_circle(self):
        acts = expand_behavior("look_scan", {})
        assert len(acts) == 4
        assert sum(a["yaw_delta"] for a in acts) == pytest.approx(math.radians(360))


class TestBehaviorPreconditions:
    def test_place_needs_placeable(self):
        ok, _ = BEHAVIORS["place_one"].preconditions(_state({"default:stick": 4}))
        assert not ok
        ok, _ = BEHAVIORS["place_one"].preconditions(_state({"default:cobble": 8}))
        assert ok

    def test_walk_has_no_preconditions(self):
        ok, _ = BEHAVIORS["walk"].preconditions(_state({}))
        assert ok


class TestBehaviorAdjust:
    def test_dig_adjust_turns_and_extends_on_empty(self):
        b = BEHAVIORS["dig_burst"]
        fb = BehaviorFeedback("dig_burst", {"n": 5}, 100, {}, False, "no_pickup")
        new = b.adjust({"n": 5}, fb)
        assert new["turn_first"] is True
        assert new["n"] == 7

    def test_dig_adjust_keeps_params_on_success(self):
        b = BEHAVIORS["dig_burst"]
        fb = BehaviorFeedback("dig_burst", {"n": 5}, 40, {"default:sand": 2}, True, "")
        assert b.adjust({"n": 5}, fb) == {"n": 5}


class TestNameAliases:
    def test_normalize_folds_itemstrings(self):
        from ai.multimodal.game_memory_bridge import normalize_inventory

        norm = normalize_inventory({"default:cobble": 8, "default:stick": 4, "default:sand": 3})
        assert norm == {"cobblestone": 8, "stick": 4, "sand": 3}

    def test_craftable_matches_real_inventory(self):
        from ai.multimodal.game_memory_bridge import GameMemoryBridge

        bridge = GameMemoryBridge()
        # Real poller itemstrings: stick needs wood×2
        assert any(r.recipe_id == "stick" for r in bridge.get_craftable_recipes({"default:wood": 4}))
        assert bridge.get_craftable_recipes({"default:cobble": 1}) == []

    def test_short_names_still_work(self):
        from ai.multimodal.game_memory_bridge import GameMemoryBridge

        bridge = GameMemoryBridge()
        assert any(r.recipe_id == "stick" for r in bridge.get_craftable_recipes({"wood": 2}))


class TestSkillTranslator:
    def test_move_walks_forward(self):
        from ai.multimodal.game_behaviors import skill_to_behavior

        assert skill_to_behavior("move", {"forward": 1.0}) == (
            "walk",
            {"steps": 3, "backward": False},
        )
        assert skill_to_behavior("navigate", {"forward": -1.0}) == (
            "walk",
            {"steps": 3, "backward": True},
        )

    def test_dig_and_combat_dig(self):
        from ai.multimodal.game_behaviors import skill_to_behavior

        assert skill_to_behavior("dig", {}) == ("dig_burst", {"n": 1})
        assert skill_to_behavior("combat", {}) == ("dig_burst", {"n": 1})

    def test_look_translates_yaw_only(self):
        from ai.multimodal.game_behaviors import skill_to_behavior

        import math

        bid, params = skill_to_behavior("look", {"yaw": 0.5})
        assert bid == "turn"
        assert params["degrees"] == pytest.approx(math.degrees(0.5))
        assert skill_to_behavior("look", {"yaw": 0.0}) == ("", {})
        assert skill_to_behavior("look", {"pitch": -0.3}) == ("", {})

    def test_craft_gate(self):
        from ai.multimodal.game_behaviors import skill_to_behavior

        assert skill_to_behavior("craft", {"recipe_id": "stick"}, craftable=lambda r: True) == (
            "craft_one",
            {"recipe_id": "stick"},
        )
        assert skill_to_behavior("craft", {"recipe_id": "auto"}, craftable=lambda r: False) == (
            "",
            {},
        )

    def test_no_undirected_verbs(self):
        from ai.multimodal.game_behaviors import skill_to_behavior

        for skill in ("place", "build", "eat", "dance"):
            assert skill_to_behavior(skill, {}) == ("", {})

    def test_craft_one_expands(self):
        assert expand_behavior("craft_one", {"recipe_id": "stick"}) == [
            {"type": "craft", "recipe": "stick"}
        ]


class TestReflexTriggers:
    def _state(self, breath=10, lava=False):
        from ai.multimodal.game_structs import GameState, Proprioception

        return GameState(proprioception=Proprioception(breath=breath, is_in_lava=lava))

    def test_surface_fires_on_low_breath(self):
        from ai.multimodal.game_behaviors import BEHAVIORS

        trig = BEHAVIORS["surface"].trigger
        assert trig is not None
        assert trig(self._state(breath=9)) is True
        assert trig(self._state(breath=10)) is False

    def test_surface_fires_on_lava(self):
        from ai.multimodal.game_behaviors import BEHAVIORS

        trig = BEHAVIORS["surface"].trigger
        assert trig(self._state(breath=10, lava=True)) is True

    def test_surface_expands_to_rise(self):
        assert expand_behavior("surface", {}) == [{"type": "rise"}]

    def test_plain_behaviors_have_no_trigger(self):
        assert BEHAVIORS["walk"].trigger is None
        assert BEHAVIORS["dig_burst"].trigger is None


class TestAffectAndRecovery:
    def test_apply_affect_maps_modes(self):
        from ai.autonomous.angela_agent import AngelaAutonomousAgent

        agent = AngelaAutonomousAgent()
        agent.selector = None

        class Emo:
            def __init__(self, mode):
                self._mode = mode

            def get_behavioral_adjustment(self):
                return {"routing_mode": self._mode}

        agent.emotion = Emo("conservative")
        agent.lifecycle = None
        agent._apply_affect()
        assert agent._affect_mode == "conservative"
        agent.emotion = Emo("exploratory")
        agent._apply_affect()
        assert agent._affect_mode == "exploratory"

    def test_apply_recovery_fallback(self):
        from types import SimpleNamespace

        from ai.autonomous.angela_agent import AngelaAutonomousAgent
        from ai.multimodal.game_task_executor import GameTaskExecutor

        agent = AngelaAutonomousAgent()
        agent.executor = GameTaskExecutor()
        psg = SimpleNamespace(
            id="t1", skill="move", params={}, preconditions=[],
            success_criteria="done", timeout=100,
        )
        strat = SimpleNamespace(
            immediate_action=SimpleNamespace(type="fallback_subgoal", subgoal=psg)
        )
        agent._apply_recovery(strat)
        ids = [s.subgoal.subgoal_id for s in agent.executor._queue]
        assert any("llm_t1" in i for i in ids)

    def test_apply_recovery_explore_walks(self):
        from types import SimpleNamespace

        from ai.autonomous.angela_agent import AngelaAutonomousAgent

        agent = AngelaAutonomousAgent()
        agent.tick_count = 99
        strat = SimpleNamespace(immediate_action=SimpleNamespace(type="explore"))
        agent._apply_recovery(strat)
        assert agent._active_behavior is not None
        assert agent._active_behavior["id"] == "walk"


class TestDecisionContracts:
    def test_behavior_order_validates(self):
        o = BehaviorOrder(behavior_id="walk", params={"steps": 3}, reasoning="go")
        assert o.behavior_id == "walk"

    def test_chat_decision_validates(self):
        d = ChatDecision(say="嗨", behavior_id="speak", params={"text": "嗨"}, reasoning="greet")
        assert d.say == "嗨"


class FakeRequest:
    def __init__(self, payload):
        self._payload = payload

    async def json(self):
        return self._payload


class TestBridgeChat:
    async def test_chat_post_and_drain(self):
        from integrations.luanti_polling_bridge import PollingBridge

        bridge = PollingBridge(http_port=39999)
        resp = await bridge.handle_chat_post(FakeRequest({"player": "zxc", "message": "嗨"}))
        assert resp.status == 200
        events = bridge.take_chat_events()
        assert len(events) == 1
        assert events[0]["player"] == "zxc"
        assert bridge.take_chat_events() == []

    async def test_chat_bounded(self):
        from integrations.luanti_polling_bridge import PollingBridge

        bridge = PollingBridge(http_port=39999)
        for i in range(60):
            await bridge.handle_chat_post(FakeRequest({"player": "p", "message": f"m{i}"}))
        assert len(bridge.chat_events) == 50

    async def test_speech_lane_survives_action_churn(self):
        """Chat replies must not be overwritten by latest-wins actions."""
        from integrations.luanti_polling_bridge import PollingBridge

        bridge = PollingBridge(http_port=39999)
        bridge.queue_action({"type": "chat", "message": "嗨"})
        for _ in range(10):
            bridge.queue_action({"type": "move", "forward": 1.0})
        assert len(bridge.outbox_chat) == 1
        assert len(bridge.pending_actions) == 1
        resp = await bridge.handle_poll(FakeRequest({}))
        assert resp.status == 200
        import json

        body = json.loads(resp.text)
        assert body["actions"][0]["type"] == "chat"
        assert body["actions"][0]["message"] == "嗨"
        assert bridge.outbox_chat == [] and bridge.pending_actions == []
