"""Tests for apps.backend.src.ai.alignment.alignment_manager"""

import pytest

from ai.alignment.alignment_manager import AlignmentManager


class TestAlignmentManager:
    def test_default_init(self):
        am = AlignmentManager()
        assert am.config == {}
        assert am.constraints["max_risk_score"] == 0.7
        assert am.constraints["required_value_alignment"] == 0.8
        assert am.constraints["ethical_boundaries"] == ["no_harm", "honesty", "fairness"]

    def test_init_with_config(self):
        am = AlignmentManager({"custom": True})
        assert am.config["custom"] is True

    def test_check_alignment_high_score(self):
        am = AlignmentManager()
        result = am.check_alignment({"risk": 0.0})
        assert result is True

    def test_check_alignment_high_risk(self):
        am = AlignmentManager()
        result = am.check_alignment({"risk": 0.9})
        assert result is True  # risk * 0.2 adjustment: 0.8 + (1-0.9)*0.2 = 0.82

    def test_check_alignment_very_high_risk(self):
        am = AlignmentManager()
        result = am.check_alignment({"risk": 2.0})
        # risk=2.0: adjustment = (1-2)*0.2 = -0.2, score = 0.8 + (-0.2) = 0.6
        assert result is False

    def test_get_alignment_score_default(self):
        am = AlignmentManager()
        score = am.get_alignment_score({})
        assert score == 1.0  # no risk: 0.8 + 0.2 = 1.0

    def test_get_alignment_score_with_risk(self):
        am = AlignmentManager()
        score = am.get_alignment_score({"risk": 0.5})
        assert score == 0.9  # 0.8 + 0.5*0.2 = 0.9

    def test_get_alignment_score_non_dict(self):
        am = AlignmentManager()
        score = am.get_alignment_score("hello")
        assert score == 1.0  # converted to {"action": "hello"}, no risk

    def test_get_alignment_score_clamped_to_1(self):
        am = AlignmentManager()
        score = am.get_alignment_score({"risk": -1.0})
        assert score == 1.0  # min(1.0, 0.8 + 2.0*0.2) = min(1.0, 1.2) = 1.0

    def test_get_constraints(self):
        am = AlignmentManager()
        c = am.get_constraints()
        assert c == am.constraints
        assert c is not am.constraints  # should be a copy

    def test_alignment_history_tracks(self):
        am = AlignmentManager()
        assert am.alignment_history == []
        am.get_alignment_score({"risk": 0.3})
        assert len(am.alignment_history) == 1
        assert abs(am.alignment_history[0]["score"] - 0.94) < 1e-9
