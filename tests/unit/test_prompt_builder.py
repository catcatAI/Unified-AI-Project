"""Tests for services.llm.prompt_builder"""

import json
from unittest.mock import mock_open, patch

import pytest


class TestGetBiologicalState:
    @patch("services.llm.prompt_builder._get_llm_config", return_value={})
    @patch("services.llm.prompt_builder.os.path.exists", return_value=False)
    def test_returns_empty_when_no_status_file(self, mock_exists, mock_cfg):
        from services.llm.prompt_builder import get_biological_state

        result = get_biological_state()
        assert result == ""

    @patch("services.llm.prompt_builder._get_llm_config")
    def test_returns_status_with_valid_data(self, mock_cfg):
        mock_cfg.return_value = {
            "energy_low": 30,
            "energy_moderate": 60,
            "stress_high_desc": 0.8,
            "stress_high_threshold": 0.5,
            "stress_max": 70,
            "energy_high": 0.8,
            "default_certainty": 0.5,
            "stress_default": 0.0,
            "default_mood": "calm",
            "caffeine_sensitivity": 0.8,
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


class TestEstimateTokens:
    """CJK 感知的 token 估算。"""

    def test_cjk_one_char_one_token(self):
        from services.llm.prompt_builder import estimate_tokens

        assert estimate_tokens("中文測試") == 4
        assert estimate_tokens("中" * 100) == 100

    def test_ascii_four_chars_per_token(self):
        from services.llm.prompt_builder import estimate_tokens

        assert estimate_tokens("abcd" * 25) == 25

    def test_empty(self):
        from services.llm.prompt_builder import estimate_tokens

        assert estimate_tokens("") == 0
        assert estimate_tokens("  ") == 0


class TestPromptBudgetGate:
    """總量守門：token 估算制＋三階段裁剪（區塊→歷史→截斷）。"""

    def _build(self, n_blocks=5, block_chars=6000, history=None):
        messages = [{"role": "system", "content": "核心提示" * 10}]
        for i in range(n_blocks):
            messages.append({"role": "user", "content": f"[Block {i}] " + "x" * block_chars})
        for h in history or []:
            messages.append(h)
        messages.append({"role": "user", "content": "<user_message>請回答</user_message>"})
        return messages

    @patch("services.llm.prompt_builder._get_llm_config", return_value=None)
    def test_eviction_oldest_first_keeps_newest_block(self, mock_cfg):
        from services.llm.prompt_builder import _enforce_prompt_budget

        messages = self._build(n_blocks=6)
        with patch(
            "services.llm.context_scheduler.get_context_scheduler",
            side_effect=ImportError("disabled"),
        ):
            stats = _enforce_prompt_budget(messages, {"_prompt_token_budget": 3000})
        assert stats["budget_tokens"] == 3000
        assert stats["dropped_messages"] > 0
        # 最舊的 Block0 先被驅逐
        assert not any("[Block 0]" in m["content"] for m in messages[1:-1])
        # 最新的補充區塊（與當前問題最相關）存留
        assert any("[Block 5]" in m["content"] for m in messages[1:-1])
        assert messages[-1]["content"] == "<user_message>請回答</user_message>"
        assert "[Context Budget Note]" in messages[0]["content"]

    @patch("services.llm.prompt_builder._get_llm_config", return_value=None)
    def test_history_dropped_oldest_first(self, mock_cfg):
        from services.llm.prompt_builder import _enforce_prompt_budget

        history = [{"role": "user", "content": f"舊訊息{i}" + "y" * 900} for i in range(4)]
        messages = self._build(n_blocks=0, history=history)
        with patch(
            "services.llm.context_scheduler.get_context_scheduler",
            side_effect=ImportError("disabled"),
        ):
            stats = _enforce_prompt_budget(messages, {"_prompt_token_budget": 600})
        assert stats["dropped_messages"] >= 1
        # 存留下來的歷史應是最新的
        remaining = [m["content"] for m in messages[1:-1]]
        assert any("舊訊息3" in c for c in remaining)
        assert not any("舊訊息0" in c for c in remaining)

    @patch("services.llm.prompt_builder._get_llm_config", return_value=None)
    def test_final_message_halved_as_last_resort(self, mock_cfg):
        from services.llm.prompt_builder import _enforce_prompt_budget

        # 無中間訊息可驅逐——超長的最終 user 訊息（貼大文件情境）被砍半
        messages = [
            {"role": "system", "content": "S" * 200},
            {"role": "user", "content": "z" * 8000},
        ]
        stats = _enforce_prompt_budget(messages, {"_prompt_token_budget": 700})
        assert stats["truncated_messages"] >= 1
        assert "…（已截斷）" in messages[-1]["content"]
        # system 原文完整保留（不被砍），僅附加稽核註記
        assert messages[0]["content"].startswith("S" * 200)
        assert "[Context Budget Note]" in messages[0]["content"]

    @patch("services.llm.prompt_builder._get_llm_config", return_value=None)
    def test_system_never_evicted_under_extreme_budget(self, mock_cfg):
        from services.llm.prompt_builder import _enforce_prompt_budget

        messages = [
            {"role": "system", "content": "核心" * 300},
            {"role": "user", "content": "x" * 3000},
            {"role": "user", "content": "final"},
        ]
        _enforce_prompt_budget(messages, {"_prompt_token_budget": 10})
        assert messages[0]["role"] == "system"  # system 永遠在場

    @patch("services.llm.prompt_builder._get_llm_config", return_value=None)
    def test_under_budget_no_drops_no_note(self, mock_cfg):
        from services.llm.prompt_builder import _enforce_prompt_budget

        messages = self._build(n_blocks=2)
        stats = _enforce_prompt_budget(messages, {"_prompt_token_budget": 6000})
        assert stats["dropped_messages"] == 0
        assert stats["truncated_messages"] == 0
        assert "[Context Budget Note]" not in messages[0]["content"]

    def test_env_override_budget(self):
        from services.llm.prompt_builder import _resolve_prompt_token_budget

        with patch.dict("os.environ", {"ANGELA_PROMPT_TOKEN_BUDGET": "1234"}):
            assert _resolve_prompt_token_budget({}) == 1234

    @patch("services.llm.prompt_builder._get_llm_config", return_value=None)
    def test_model_window_dynamic_budget(self, mock_cfg):
        from services.llm.prompt_builder import _resolve_prompt_token_budget

        # 2048 窗 × 0.55 ≈ 1126；env 未設、無明確指定時按模型動態
        budget = _resolve_prompt_token_budget({"_model_context_window": 2048})
        assert budget == int(2048 * 0.55)

    def test_completion_reserve_caps_explicit_budget(self):
        from services.llm.prompt_builder import _resolve_prompt_token_budget

        with patch.dict("os.environ", {}, clear=True):
            budget = _resolve_prompt_token_budget(
                {
                    "_model_context_window": 4096,
                    "_completion_token_reserve": 1024,
                    "_prompt_token_budget": 6000,
                }
            )
        assert budget == 4096 - 1024 - 128

    @patch("services.llm.prompt_builder._get_llm_config", return_value={})
    def test_construct_enforces_budget_after_final_user_message(self, mock_cfg):
        from services.llm.prompt_builder import construct_angela_prompt, estimate_tokens

        context = {
            "state_for_llm": None,
            "history": [{"role": "user", "content": "歷" * 800} for _ in range(10)],
            "_model_context_window": 4096,
        }
        with patch.dict("os.environ", {}, clear=True):
            with patch(
                "services.llm.context_scheduler.get_context_scheduler",
                side_effect=ImportError("disabled"),
            ):
                result = construct_angela_prompt("喵？", context)
        total = sum(estimate_tokens(m["content"]) for m in result)
        assert total <= int(4096 * 0.55)
        assert result[-1]["role"] == "user"
        assert "喵？" in result[-1]["content"]

    @patch("services.llm.prompt_builder._get_llm_config", return_value=None)
    def test_small_window_model_trims_aggressively(self, mock_cfg):
        from services.llm.prompt_builder import _enforce_prompt_budget

        messages = self._build(n_blocks=4)
        with patch(
            "services.llm.context_scheduler.get_context_scheduler",
            side_effect=ImportError("disabled"),
        ):
            stats = _enforce_prompt_budget(messages, {"_model_context_window": 2048})
        assert stats["budget_tokens"] == int(2048 * 0.55)
        assert stats["dropped_messages"] > 0

    @patch("services.llm.prompt_builder._get_llm_config", return_value=None)
    def test_telemetry_counts_events(self, mock_cfg):
        from services.llm.prompt_builder import (
            _enforce_prompt_budget,
            get_prompt_budget_stats,
        )

        before = get_prompt_budget_stats()["events"]
        messages = self._build(n_blocks=5)
        _enforce_prompt_budget(messages, {"_prompt_token_budget": 1500})
        after = get_prompt_budget_stats()
        assert after["events"] == before + 1
        assert after["dropped_messages"] >= 1

    @patch("services.llm.prompt_builder._get_llm_config", return_value=None)
    def test_invalid_budget_config_ignored(self, mock_cfg):
        from services.llm.prompt_builder import _resolve_prompt_token_budget

        mock_cfg.return_value = "not-a-number"
        assert _resolve_prompt_token_budget({}) == 6000

    def test_history_single_message_capped_at_source(self):
        from services.llm.prompt_builder import construct_angela_prompt

        context = {
            "state_for_llm": None,
            "history": [{"role": "user", "content": "h" * 5000}],
        }
        with patch("services.llm.prompt_builder._get_llm_config", return_value={}):
            result = construct_angela_prompt("hi", context)
        history_msg = result[1]
        assert len(history_msg["content"]) == 800


class TestModelWindowResolution:
    def test_known_model_prefixes(self):
        from services.llm.prompt_builder import resolve_model_window

        assert resolve_model_window("phi:latest") == 2048
        assert resolve_model_window("qwen2.5-coder:latest") == 4096
        assert resolve_model_window("deepseek-r1:latest") == 8192

    def test_unknown_model_conservative_default(self):
        from services.llm.prompt_builder import resolve_model_window

        assert resolve_model_window("mystery-model") == 8192
        assert resolve_model_window("") == 8192


class TestSystemSectionTrimming:
    """system 本身超額時：保護核心與安全指令，其餘區段由大至小捨。"""

    def _trim(self, system_content, budget):
        from services.llm.prompt_builder import _enforce_prompt_budget

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": "final"},
        ]
        stats = _enforce_prompt_budget(messages, {"_prompt_token_budget": budget})
        return messages, stats

    @patch("services.llm.prompt_builder._get_llm_config", return_value=None)
    def test_oversized_system_trims_sections_keeps_safety(self, mock_cfg):
        from services.llm.prompt_builder import estimate_tokens

        system = (
            "核心提示\n\n"
            "[Context Overview]\n" + "o" * 4000 + "\n\n"
            "[Verified Knowledge]\n" + "k" * 4000 + "\n\n"
            "[SAFETY INSTRUCTION — MANDATORY]\n保持安全\n\n"
            "[Web Search Results]\n" + "w" * 4000
        )
        messages, stats = self._trim(system, 3000)
        assert stats["trimmed_system_sections"] >= 1
        assert "[SAFETY INSTRUCTION" in messages[0]["content"]
        assert "[Context Budget Note]" in messages[0]["content"]
        total = sum(estimate_tokens(m["content"]) for m in messages)
        assert total <= 3000  # 註記預扣後仍不超預算

    @patch("services.llm.prompt_builder._get_llm_config", return_value=None)
    def test_note_reserve_keeps_total_within_budget(self, mock_cfg):
        from services.llm.prompt_builder import _enforce_prompt_budget, estimate_tokens

        messages = [{"role": "system", "content": "核心提示" * 10}]
        for i in range(3):
            messages.append({"role": "user", "content": f"[Block {i}] " + "x" * 6000})
        messages.append({"role": "user", "content": "<user_message>請回答</user_message>"})
        stats = _enforce_prompt_budget(messages, {"_prompt_token_budget": 2000})
        assert stats["total_tokens"] <= 2000

    @patch("services.llm.prompt_builder._get_llm_config", return_value=None)
    def test_small_window_end_to_end_fits(self, mock_cfg):
        """煙霧測試回歸：2048 窗小模型不再收到 4 倍超額的提示。"""
        from services.llm.prompt_builder import construct_angela_prompt, estimate_tokens

        context = {
            "state_for_llm": None,
            "history": [{"role": "user", "content": "h" * 800} for _ in range(10)],
            "grounded_context": "知" * 1500,
            "web_search_context": "網" * 1200,
            "workspace_overview": "🔒 全貌 [root]" + "\n  🔒 節點" * 30,
            "_model_context_window": 2048,
        }
        with patch("services.llm.prompt_builder._get_llm_config", return_value={}):
            result = construct_angela_prompt("q", context)
        total = sum(estimate_tokens(m["content"]) for m in result)
        assert total <= int(2048 * 0.55)


class TestWorkspaceOverviewInjection:
    """內外一致性：Angela 的提示應呈現系統實際持有的上下文全貌。"""

    def test_context_snapshot_overrides_lazy_fetch(self):
        from services.llm.prompt_builder import construct_angela_prompt

        context = {
            "state_for_llm": None,
            "workspace_overview": "🔒 AI 系統上下文 [root]\n  🔒 記憶上下文 [ctx:memory] — 3 則記憶",
        }
        with patch("services.llm.prompt_builder._get_llm_config", return_value={}):
            result = construct_angela_prompt("你好", context)
        system = result[0]["content"]
        assert "[System Context Overview — read-only]" in system
        assert "ctx:memory" in system
        assert "唯讀" in system

    def test_absent_overview_adds_no_noise(self):
        from services.llm.prompt_builder import construct_angela_prompt

        context = {"state_for_llm": None, "workspace_overview": None}
        with patch("services.llm.prompt_builder._get_llm_config", return_value={}):
            with patch("services.llm.prompt_builder._get_workspace_overview", return_value=""):
                result = construct_angela_prompt("你好", context)
        assert "[System Context Overview" not in result[0]["content"]

    def test_empty_snapshot_falls_back_to_lazy_fetch(self):
        from services.llm.prompt_builder import construct_angela_prompt

        context = {"state_for_llm": None, "workspace_overview": "   "}
        with patch("services.llm.prompt_builder._get_llm_config", return_value={}):
            with patch(
                "services.llm.prompt_builder._get_workspace_overview",
                return_value="🔒 全貌 [root]",
            ):
                result = construct_angela_prompt("你好", context)
        assert "🔒 全貌 [root]" in result[0]["content"]


class TestUnboundedBlockTruncation:
    """曾經完全未截斷的三個區塊，現在有上限。"""

    def _system_content(self, context):
        from services.llm.prompt_builder import construct_angela_prompt

        with patch("services.llm.prompt_builder._get_llm_config", return_value={}):
            result = construct_angela_prompt("hi", {"state_for_llm": None, **context})
        return result[0]["content"]

    def test_grounded_context_truncated(self):
        content = self._system_content({"grounded_context": "知" * 9000})
        assert "知" * 9000 not in content
        assert "知" * 1500 in content

    def test_web_search_truncated(self):
        content = self._system_content({"web_search_context": "網" * 9000})
        assert "網" * 9000 not in content

    def test_dictionary_truncated(self):
        content = self._system_content({"dictionary_context": "詞" * 9000})
        assert "詞" * 9000 not in content


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
                "theta": {
                    "novelty": 0.7,
                    "theta_negativity": 0.1,
                    "creation_urge": 0.3,
                    "correction_urge": 0.2,
                },
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


class TestGroundingContextInjection:
    """Grounded / web-search context must actually reach the LLM prompt (no dead injection)."""

    @patch("services.llm.prompt_builder.get_biological_state", return_value="")
    @patch("services.llm.prompt_builder.get_formula_summaries", return_value="")
    def test_grounded_context_reaches_prompt(self, mock_formula, mock_bio):
        from services.llm.prompt_builder import construct_angela_prompt

        context = {
            "state_for_llm": None,
            "user_profile": {},
            "drive_files": [],
            "history": [],
            "grounded_context": "VERIFIED: Taipei is the capital of Taiwan.",
        }
        result = construct_angela_prompt("test", context)
        assert "VERIFIED: Taipei is the capital of Taiwan." in result[0]["content"]

    @patch("services.llm.prompt_builder.get_biological_state", return_value="")
    @patch("services.llm.prompt_builder.get_formula_summaries", return_value="")
    def test_web_search_context_reaches_prompt(self, mock_formula, mock_bio):
        from services.llm.prompt_builder import construct_angela_prompt

        context = {
            "state_for_llm": None,
            "user_profile": {},
            "drive_files": [],
            "history": [],
            "web_search_context": "- Wikipedia: Taipei (https://en.wikipedia.org/wiki/Taipei)",
        }
        result = construct_angela_prompt("test", context)
        assert "Wikipedia: Taipei" in result[0]["content"]

    @patch("services.llm.prompt_builder.get_biological_state", return_value="")
    @patch("services.llm.prompt_builder.get_formula_summaries", return_value="")
    def test_dictionary_and_memory_context_reach_prompt(self, mock_formula, mock_bio):
        from services.llm.prompt_builder import construct_angela_prompt

        context = {
            "state_for_llm": None,
            "user_profile": {},
            "drive_files": [],
            "history": [],
            "dictionary_context": "WORD: 貓 = cat (noun)",
            "conversation_memory": "PREVIOUS: You asked about cats.",
        }
        result = construct_angela_prompt("test", context)
        content = result[0]["content"]
        assert "WORD: 貓 = cat (noun)" in content
        assert "PREVIOUS: You asked about cats." in content


class TestModalityState:
    """Test modality gateway state injection into prompt (C³ 3.0 — closed loop)."""

    def test_append_modality_state_active_exists(self):
        from core.life.digital_life_integrator import ModalityGateway
        from services.llm.prompt_builder import _append_modality_state

        mg = ModalityGateway()
        summary = mg.get_modality_summary()
        assert "active" in summary
        assert "inactive" in summary
        assert "all" in summary

    def test_append_modality_state_with_context(self):
        from services.llm.prompt_builder import _append_modality_state

        context = {
            "modality_state": {
                "active": ["TEXT", "AUDIO"],
                "inactive": ["VISUAL_3D", "CODE"],
                "all": {
                    "TEXT": {"active": True, "priority": 10},
                    "AUDIO": {"active": True, "priority": 5},
                    "VISUAL_3D": {"active": False, "priority": 8},
                    "CODE": {"active": False, "priority": 2},
                },
            }
        }
        messages = [{"role": "system", "content": "Base prompt"}]
        _append_modality_state(messages, context)
        content = messages[0]["content"]
        assert "[Modality State]" in content
        assert "TEXT" in content
        assert "AUDIO" in content
        assert "VISUAL_3D" in content
        assert "currently unavailable" in content or "disabled" in content

    def test_append_modality_state_no_context(self):
        from services.llm.prompt_builder import _append_modality_state

        messages = [{"role": "system", "content": "Base prompt"}]
        original = messages[0]["content"]
        _append_modality_state(messages, {})
        assert messages[0]["content"] == original


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


class TestCrisisSafety:
    def test_append_crisis_safety_no_context(self):
        from services.llm.prompt_builder import _append_crisis_safety

        messages = [{"role": "system", "content": "Base prompt"}]
        original = messages[0]["content"]
        _append_crisis_safety(messages, {})
        assert messages[0]["content"] == original

    def test_append_crisis_safety_with_context(self):
        from services.llm.prompt_builder import _append_crisis_safety

        context = {"crisis_instruction": "User input has crisis level 2. Respond with empathy."}
        messages = [{"role": "system", "content": "Base prompt"}]
        _append_crisis_safety(messages, context)
        content = messages[0]["content"]
        assert "[SAFETY INSTRUCTION" in content
        assert "Respond with empathy" in content
        assert "prioritize user safety" in content.lower()

    def test_construct_angela_prompt_includes_crisis_instruction(self):
        from services.llm.prompt_builder import construct_angela_prompt

        context = {
            "angela_data": {},
            "biological_state": "",
            "formula_summaries": "",
            "autonomous_decisions": "",
            "action_logs": [],
            "drive_files": [],
            "history": [],
            "crisis_instruction": "User input has crisis level 3. Prioritize safety.",
        }
        result = construct_angela_prompt("test", context)
        combined = " ".join(msg["content"] for msg in result)
        assert "[SAFETY INSTRUCTION" in combined
        assert "crisis level 3" in combined
