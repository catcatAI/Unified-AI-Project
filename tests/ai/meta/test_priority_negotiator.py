"""Tests for PriorityNegotiator — weighted fusion of routing preferences."""

import pytest

from ai.meta.priority_negotiator import (
    PriorityNegotiator,
    VoterVote,
    angela_emotion_voter,
    causal_voter,
    emotional_voter,
    intent_voter,
    lifecycle_voter,
    meta_calibration_voter,
)


class TestVoterVote:
    """Test VoterVote dataclass."""

    def test_default_construction(self):
        vote = VoterVote()
        assert vote.routing_mode is None
        assert vote.response_style is None
        assert vote.temperature_bias == 0.0
        assert vote.tokens_bias == 0
        assert vote.confidence == 0.0

    def test_full_construction(self):
        vote = VoterVote(
            routing_mode="conservative",
            response_style="cautious",
            temperature_bias=-0.1,
            tokens_bias=-100,
            confidence=0.8,
        )
        assert vote.routing_mode == "conservative"
        assert vote.temperature_bias == -0.1
        assert vote.tokens_bias == -100


class TestPriorityNegotiator:
    """Test PriorityNegotiator core logic."""

    def setup_method(self):
        self.negotiator = PriorityNegotiator()

    def test_no_voters_returns_defaults(self):
        result = self.negotiator.resolve({})
        assert result["routing_mode"] is None
        assert result["response_style"] is None
        assert result["temperature_bias"] == 0.0
        assert result["tokens_bias"] == 0
        assert result["resolved_by"] == "no_voters"

    def test_single_voter(self):
        def vote(ctx):
            return VoterVote(routing_mode="exploratory", response_style="curious", confidence=0.9)
        self.negotiator.register_voter("test", vote)
        result = self.negotiator.resolve({})
        assert result["routing_mode"] == "exploratory"
        assert result["response_style"] == "curious"

    def test_weighted_plurality(self):
        def v1(ctx):
            return VoterVote(routing_mode="conservative", confidence=0.9)
        def v2(ctx):
            return VoterVote(routing_mode="exploratory", confidence=0.5)
        self.negotiator.register_voter("v1", v1)
        self.negotiator.register_voter("v2", v2)
        result = self.negotiator.resolve({})
        assert result["routing_mode"] == "conservative"

    def test_weight_fn_scales_confidence(self):
        def low_conf(ctx):
            return VoterVote(routing_mode="exploratory", confidence=0.9)
        def high_conf(ctx):
            return VoterVote(routing_mode="conservative", confidence=0.3)
        self.negotiator.register_voter("v1", low_conf, weight_fn=lambda ctx: 0.1)
        self.negotiator.register_voter("v2", high_conf, weight_fn=lambda ctx: 1.0)
        result = self.negotiator.resolve({})
        # v2 (conservative) has weight=1.0*0.3=0.3, v1 has weight=0.1*0.9=0.09
        assert result["routing_mode"] == "conservative"

    def test_abstain_returns_none(self):
        def always_none(ctx):
            return None
        self.negotiator.register_voter("abstainer", always_none)
        result = self.negotiator.resolve({})
        assert result["routing_mode"] is None
        assert result["resolved_by"] == "no_voters"

    def test_voter_error_does_not_crash(self):
        def broken(ctx):
            raise RuntimeError("voter crashed")
        def good(ctx):
            return VoterVote(routing_mode="neutral", confidence=1.0)
        self.negotiator.register_voter("broken", broken)
        self.negotiator.register_voter("good", good)
        result = self.negotiator.resolve({})
        assert result["routing_mode"] == "neutral"

    def test_temperature_bias_weighted_average(self):
        def v1(ctx):
            return VoterVote(temperature_bias=-0.2, confidence=0.8)
        def v2(ctx):
            return VoterVote(temperature_bias=0.1, confidence=0.2)
        self.negotiator.register_voter("v1", v1)
        self.negotiator.register_voter("v2", v2)
        result = self.negotiator.resolve({})
        expected = (-0.2 * 0.8 + 0.1 * 0.2) / (0.8 + 0.2)
        assert result["temperature_bias"] == round(expected, 3)

    def test_tokens_bias_weighted_average(self):
        def v1(ctx):
            return VoterVote(tokens_bias=-50, confidence=0.9)
        def v2(ctx):
            return VoterVote(tokens_bias=100, confidence=0.1)
        self.negotiator.register_voter("v1", v1)
        self.negotiator.register_voter("v2", v2)
        result = self.negotiator.resolve({})
        # (-50 * 0.9 + 100 * 0.1) / (0.9 + 0.1) = (-45 + 10) / 1.0 = -35
        assert result["tokens_bias"] == -35

    def test_unregister_voter(self):
        def v(ctx):
            return VoterVote(routing_mode="test", confidence=1.0)
        self.negotiator.register_voter("v", v)
        assert self.negotiator.unregister_voter("v") is True
        assert self.negotiator.unregister_voter("nonexistent") is False
        result = self.negotiator.resolve({})
        assert result["routing_mode"] is None

    def test_voter_contributions_in_result(self):
        def v1(ctx):
            return VoterVote(routing_mode="a", confidence=0.7)
        def v2(ctx):
            return VoterVote(routing_mode="b", confidence=0.3)
        self.negotiator.register_voter("v1", v1)
        self.negotiator.register_voter("v2", v2)
        result = self.negotiator.resolve({})
        assert "voter_contributions" in result
        assert result["voter_contributions"]["v1"] == 0.7
        assert result["voter_contributions"]["v2"] == 0.3

    def test_resolved_by_highest_contribution(self):
        def low(ctx):
            return VoterVote(routing_mode="a", confidence=0.2)
        def high(ctx):
            return VoterVote(routing_mode="b", confidence=0.9)
        self.negotiator.register_voter("low", low)
        self.negotiator.register_voter("high", high)
        result = self.negotiator.resolve({})
        assert result["resolved_by"] == "high"


class TestDefaultVoterFunctions:
    """Test the default voter functions provided by priority_negotiator."""

    def test_lifecycle_voter_present(self):
        ctx = {"lifecycle_behavior": {"routing_mode": "conservative", "response_style": "cautious", "confidence": 0.7}}
        vote = lifecycle_voter(ctx)
        assert vote is not None
        assert vote.routing_mode == "conservative"
        assert vote.response_style == "cautious"
        assert vote.confidence == 0.7

    def test_lifecycle_voter_absent(self):
        assert lifecycle_voter({}) is None

    def test_emotional_voter_present(self):
        ctx = {"emotional_behavior": {"routing_mode": "exploratory", "confidence": 0.8}}
        vote = emotional_voter(ctx)
        assert vote.routing_mode == "exploratory"
        assert vote.confidence == 0.8

    def test_emotional_voter_absent(self):
        assert emotional_voter({}) is None

    def test_intent_voter_present(self):
        ctx = {"intent_routing": {"routing_mode": "empathetic", "response_style": "warm", "intent_strength": 0.6}}
        vote = intent_voter(ctx)
        assert vote.routing_mode == "empathetic"
        assert vote.response_style == "warm"
        assert vote.confidence == 0.6

    def test_intent_voter_absent(self):
        assert intent_voter({}) is None

    def test_angela_emotion_voter_present(self):
        ctx = {"angela_emotion": {"routing_mode": "conservative", "response_style": "soothing", "emotion_intensity": 0.9}}
        vote = angela_emotion_voter(ctx)
        assert vote.routing_mode == "conservative"
        assert vote.response_style == "soothing"
        assert vote.confidence == 0.9

    def test_angela_emotion_voter_absent(self):
        assert angela_emotion_voter({}) is None

    def test_causal_voter_above_threshold(self):
        ctx = {"causal_routing": {"temperature_bias": -0.15, "max_tokens_bias": -50, "causal_confidence": 0.8}}
        vote = causal_voter(ctx)
        assert vote is not None
        assert vote.temperature_bias == -0.15
        assert vote.tokens_bias == -50
        assert vote.confidence == 0.8

    def test_causal_voter_below_threshold(self):
        ctx = {"causal_routing": {"causal_confidence": 0.2}}
        assert causal_voter(ctx) is None

    def test_causal_voter_absent(self):
        assert causal_voter({}) is None

    def test_all_five_voters_integration(self):
        """Verify all 5 default voters work together in a negotiator."""
        negotiator = PriorityNegotiator()
        negotiator.register_voter("lifecycle", lifecycle_voter, weight_fn=lambda ctx: 0.8)
        negotiator.register_voter("emotional", emotional_voter, weight_fn=lambda ctx: 0.7)
        negotiator.register_voter("intent", intent_voter, weight_fn=lambda ctx: 0.6)
        negotiator.register_voter("angela_emotion", angela_emotion_voter, weight_fn=lambda ctx: 0.9)
        negotiator.register_voter("causal", causal_voter, weight_fn=lambda ctx: 0.5)

        ctx = {
            "lifecycle_behavior": {"routing_mode": "neutral", "response_style": "thoughtful", "confidence": 0.6},
            "emotional_behavior": {"routing_mode": "exploratory", "confidence": 0.5},
            "intent_routing": {"routing_mode": "empathetic", "response_style": "warm", "intent_strength": 0.4},
            "angela_emotion": {"routing_mode": "conservative", "response_style": "calming", "emotion_intensity": 0.7},
            "causal_routing": {"temperature_bias": -0.1, "max_tokens_bias": -50, "causal_confidence": 0.6},
        }

        result = negotiator.resolve(ctx)

        # angela_emotion has highest weight (0.9 * 0.7 = 0.63)
        # Explanatory: 0.7*0.5=0.35 emotional, conservative: 0.9*0.7=0.63 angela
        # So conservative should win
        assert result["routing_mode"] == "conservative"
        assert result["response_style"] == "calming"
        assert result["temperature_bias"] != 0.0
        assert result["tokens_bias"] != 0
        assert result["resolved_by"] == "angela_emotion"


class TestMetaCalibrationVoter:
    """Tests for meta_calibration_voter."""

    def test_no_meta_calibration_returns_none(self):
        result = meta_calibration_voter({})
        assert result is None

    def test_zero_adjustment_returns_none(self):
        result = meta_calibration_voter({"meta_calibration": {"weighted_adjustment": 0.0}})
        assert result is None

    def test_positive_adjustment_increases_temperature(self):
        result = meta_calibration_voter({"meta_calibration": {"weighted_adjustment": 0.05}})
        assert result is not None
        assert result.routing_mode is None  # abstain on mode
        assert result.temperature_bias > 0  # 0.05 * 3.0 = 0.15
        assert result.tokens_bias > 0
        assert result.confidence > 0

    def test_negative_adjustment_decreases_temperature(self):
        result = meta_calibration_voter({"meta_calibration": {"weighted_adjustment": -0.05}})
        assert result is not None
        assert result.routing_mode is None
        assert result.temperature_bias < 0
        assert result.tokens_bias < 0

    def test_small_adjustment_below_threshold_returns_none(self):
        result = meta_calibration_voter({"meta_calibration": {"weighted_adjustment": 0.0005}})
        assert result is None

    def test_large_adjustment_capped_confidence(self):
        result = meta_calibration_voter({"meta_calibration": {"weighted_adjustment": 2.0}})
        assert result is not None
        assert result.confidence == 1.0  # capped at 1.0

    def test_adjustment_integrated_in_negotiator_resolve(self):
        negotiator = PriorityNegotiator()
        negotiator.register_voter("meta_calibration", meta_calibration_voter,
                                  weight_fn=lambda ctx: 0.4)

        ctx = {"meta_calibration": {"weighted_adjustment": 0.05}}
        result = negotiator.resolve(ctx)

        assert result["temperature_bias"] > 0
        assert result["tokens_bias"] > 0
        assert result["resolved_by"] == "meta_calibration"
