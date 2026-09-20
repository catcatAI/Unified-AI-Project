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
        }

    def test_catalog_lists_everything(self):
        text = behavior_catalog_text()
        for bid in BEHAVIORS:
            assert bid in text

    def test_unknown_behavior_expands_empty(self):
        assert expand_behavior("nope", {}) == []


class TestBehaviorExpansion:
    def test_walk_steps_bounded(self):
        acts = expand_behavior("walk", {"steps": 3})
        assert len(acts) == 3
        assert all(a["type"] == "move" and a["forward"] == 1.0 for a in acts)
        assert len(expand_behavior("walk", {"steps": 99})) == 10
        back = expand_behavior("walk", {"steps": 2, "backward": True})
        assert all(a["forward"] == -1.0 for a in back)

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
