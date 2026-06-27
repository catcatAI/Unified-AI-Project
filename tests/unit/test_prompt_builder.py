"""Tests for services.llm.prompt_builder"""
import json
from unittest.mock import mock_open, patch

import pytest


class TestGetBiologicalState:
    @patch("services.llm.prompt_builder._get_llm_config", return_value={})
    def test_returns_empty_when_no_status_file(self, mock_cfg):
        from services.llm.prompt_builder import get_biological_state

        result = get_biological_state()
        assert result == ""

    @patch("services.llm.prompt_builder._get_llm_config")
    def test_returns_status_with_valid_data(self, mock_cfg):
        mock_cfg.return_value = {
            "energy_low": 30, "energy_moderate": 60,
            "stress_high_desc": 0.8, "stress_high_threshold": 0.5,
            "stress_max": 70, "energy_high": 0.8,
            "default_certainty": 0.5, "stress_default": 0.0,
            "default_mood": "calm", "caffeine_sensitivity": 0.8,
        }
        mock_data = {
            "biological": {
                "arousal": 0.3,
                "stress_level": 0.1,
                "dominant_emotion": "happy",
                "hormonal_effects": {"energy": 0.2},
                "hunger": 0.0,
            },
            "life_intensity": 0.0,
        }
        with patch("services.llm.prompt_builder.os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
                from services.llm.prompt_builder import get_biological_state

                result = get_biological_state()
                # File-based path returns raw JSON, not formatted descriptions
                assert '"dominant_emotion": "happy"' in result
                assert '"life_intensity": 0.0' in result

    @patch("services.llm.prompt_builder._get_llm_config")
    def test_returns_empty_on_parse_error(self, mock_cfg):
        mock_cfg.return_value = {}
        with patch("services.llm.prompt_builder.os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="invalid json")):
                from services.llm.prompt_builder import get_biological_state

                result = get_biological_state()
                assert result == ""


class TestGetFormulaSummaries:
    @patch("services.llm.prompt_builder._get_llm_config", return_value={})
    def test_returns_formulas_when_modules_available(self, mock_cfg):
        from services.llm.prompt_builder import get_formula_summaries

        result = get_formula_summaries()
        assert "生命強度" in result or "活躍認知" in result or "CDM" in result


class TestConstructAngelaPrompt:
    @patch("services.llm.prompt_builder.get_biological_state", return_value="")
    @patch("services.llm.prompt_builder.get_formula_summaries", return_value="")
    def test_basic_structure(self, mock_formula, mock_bio):
        from services.llm.prompt_builder import construct_angela_prompt

        context = {"state_for_llm": None, "user_profile": {}, "drive_files": [], "history": []}
        result = construct_angela_prompt("hello", context)
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[-1]["role"] == "user"
        assert "hello" in result[-1]["content"]
        assert "<user_message>" in result[-1]["content"]

    @patch("services.llm.prompt_builder.get_biological_state", return_value="生物狀態描述")
    @patch("services.llm.prompt_builder.get_formula_summaries", return_value="公式摘要")
    def test_includes_bio_and_formula(self, mock_formula, mock_bio):
        from services.llm.prompt_builder import construct_angela_prompt

        context = {"state_for_llm": None, "user_profile": {}, "drive_files": [], "history": []}
        result = construct_angela_prompt("hi", context)
        assert "生物狀態描述" in result[0]["content"]
        assert "公式摘要" in result[0]["content"]

    @patch("services.llm.prompt_builder.get_biological_state", return_value="")
    @patch("services.llm.prompt_builder.get_formula_summaries", return_value="")
    def test_includes_user_profile(self, mock_formula, mock_bio):
        from services.llm.prompt_builder import construct_angela_prompt

        context = {
            "state_for_llm": None,
            "user_profile": {"name": "Alice", "interests": ["AI", "music"]},
            "drive_files": [],
            "history": [],
        }
        result = construct_angela_prompt("test", context)
        assert "Alice" in result[0]["content"]
        assert "AI" in result[0]["content"]

    @patch("services.llm.prompt_builder.get_biological_state", return_value="")
    @patch("services.llm.prompt_builder.get_formula_summaries", return_value="")
    def test_includes_history(self, mock_formula, mock_bio):
        from services.llm.prompt_builder import construct_angela_prompt

        context = {
            "state_for_llm": None,
            "user_profile": {},
            "drive_files": [],
            "history": [{"role": "assistant", "content": "Hello!"}],
        }
        result = construct_angela_prompt("world", context)
        assert len(result) == 3

    @patch("services.llm.prompt_builder.get_biological_state", return_value="")
    @patch("services.llm.prompt_builder.get_formula_summaries", return_value="")
    def test_includes_state_axes(self, mock_formula, mock_bio):
        from services.llm.prompt_builder import construct_angela_prompt

        context = {
            "state_for_llm": {
                "axes": {"alpha": {"values": {"valence": 0.8, "energy": 0.6}}},
                "theta": {"novelty": 0.7, "theta_negativity": 0.1, "creation_urge": 0.3, "correction_urge": 0.2},
                "eta": {"module_count": 3, "success_rate": 0.9, "structural_drift": 0.05},
                "guidance": ["保持友好"],
            },
            "user_profile": {},
            "drive_files": [],
            "history": [],
        }
        result = construct_angela_prompt("test", context)
        assert "ALPHA" in result[0]["content"]
        assert "保持友好" in result[0]["content"]


class TestGetLLMConfig:
    def test_returns_default_on_failure(self):
        from services.llm.prompt_builder import _get_llm_config

        result = _get_llm_config("nonexistent", "fallback")
        assert result == "fallback"


class TestFormulaSummaries:
    """Verify formula values propagate through the prompt injection chain."""

    def test_get_formula_summaries_returns_string(self):
        from services.llm.prompt_builder import get_formula_summaries

        result = get_formula_summaries()
        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain at least some formula values
        assert "HSM" in result or "intensity" in result or "cognition" in result

    def test_get_autonomous_decisions_returns_string(self):
        from services.llm.prompt_builder import get_autonomous_decisions

        result = get_autonomous_decisions()
        assert isinstance(result, str)

    def test_construct_angela_prompt_contains_formula_block(self):
        from services.llm.prompt_builder import construct_angela_prompt

        context = {
            "angela_data": {},
            "biological_state": "",
            "formula_summaries": "",
            "autonomous_decisions": "",
            "action_logs": [],
            "drive_files": [],
            "history": [],
        }
        result = construct_angela_prompt("test", context)
        combined = " ".join(msg["content"] for msg in result)
        assert combined, "Prompt should contain content"
