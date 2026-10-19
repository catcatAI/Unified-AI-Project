"""Test Phase 7 P2: PromptManager."""

import json
import os
import tempfile

import pytest

from apps.backend.src.core.prompt_manager import (
    PromptManager,
    PromptTemplate,
    get_prompt_manager,
    prompt,
)


class TestPromptManager:
    def test_register_and_get(self):
        """Register a template and retrieve it."""
        mgr = PromptManager()
        template = PromptTemplate(
            key="test.greeting",
            templates={"en": "Hello {name}", "zh": "你好 {name}"},
        )
        mgr.register(template)

        result = mgr.get("test.greeting", name="World")
        assert result == "Hello World"

    def test_language_selection(self):
        """Select template by language."""
        mgr = PromptManager()
        template = PromptTemplate(
            key="test.greeting",
            templates={"en": "Hello", "zh": "你好"},
        )
        mgr.register(template)

        assert mgr.get("test.greeting", "en") == "Hello"
        assert mgr.get("test.greeting", "zh") == "你好"

    def test_fallback_to_english(self):
        """Fall back to English if language not available."""
        mgr = PromptManager()
        template = PromptTemplate(
            key="test.greeting",
            templates={"en": "Hello"},
        )
        mgr.register(template)

        assert mgr.get("test.greeting", "ja") == "Hello"

    def test_missing_template(self):
        """Missing template returns key."""
        mgr = PromptManager()
        assert mgr.get("nonexistent.key") == "nonexistent.key"

    def test_set_language(self):
        """Set default language."""
        mgr = PromptManager()
        template = PromptTemplate(
            key="test.greeting",
            templates={"en": "Hello", "zh": "你好"},
        )
        mgr.register(template)

        mgr.set_language("zh")
        assert mgr.get("test.greeting") == "你好"

    def test_render_with_variables(self):
        """Render template with variable substitution."""
        mgr = PromptManager()
        template = PromptTemplate(
            key="test.msg",
            templates={"en": "{greeting}, {name}!"},
        )
        mgr.register(template)

        result = mgr.get("test.msg", greeting="Hi", name="Alice")
        assert result == "Hi, Alice!"

    def test_load_from_json(self):
        """Load templates from JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "test.prompt1": {
                        "templates": {"en": "Test {x}", "zh": "測試 {x}"},
                        "variables": ["x"],
                        "description": "Test prompt",
                        "tags": ["test"],
                    }
                },
                f,
            )
            tmp = f.name

        try:
            mgr = PromptManager()
            count = mgr.load_from_json(tmp)
            assert count == 1
            assert mgr.get("test.prompt1", x="123") == "Test 123"
        finally:
            os.unlink(tmp)

    def test_load_from_json_missing(self):
        mgr = PromptManager()
        count = mgr.load_from_json("/nonexistent/file.json")
        assert count == 0

    def test_list_templates(self):
        mgr = PromptManager()
        mgr.register(PromptTemplate(key="a", templates={"en": "A"}))
        mgr.register(PromptTemplate(key="b", templates={"en": "B"}))
        keys = mgr.list_templates()
        assert "a" in keys
        assert "b" in keys

    def test_default_angela_identity(self):
        """Default Angela identity template is registered."""
        mgr = get_prompt_manager()
        result = mgr.get("angela.identity", "en")
        assert "Angela" in result
        assert "digital life" in result

    def test_flat_locale_prompts_are_loaded(self):
        mgr = PromptManager()
        count = mgr.load_flat_locales()
        assert count > 0
        assert mgr.get("angela.current_state", "en") == "Current state"
        assert mgr.get("angela.rule_greet_idle", "zh")

    def test_default_angela_identity_zh(self):
        """Default Angela identity template has Chinese version."""
        mgr = get_prompt_manager()
        result = mgr.get("angela.identity", "zh")
        assert "Angela" in result
        assert "數字生命" in result

    def test_prompt_convenience_function(self):
        """The prompt() convenience function works."""
        result = prompt("angela.fallback", "en")
        assert "Sorry" in result

    def test_prompt_zh(self):
        """The prompt() convenience function works with Chinese."""
        result = prompt("angela.fallback", "zh")
        assert "抱歉" in result


class TestLanguageDetection:
    """detect_response_language + zh-TW fallback（語言層稽核發現：繁中使用者拿到簡體/英文）。"""

    def test_detect_chinese_traditional(self):
        from apps.backend.src.core.prompt_manager import detect_response_language

        assert detect_response_language("你好呀，今天過得怎樣？") == "zh"

    def test_detect_chinese_simplified(self):
        from apps.backend.src.core.prompt_manager import detect_response_language

        assert detect_response_language("你好呀，今天过得怎么样？") == "zh"

    def test_detect_english(self):
        from apps.backend.src.core.prompt_manager import detect_response_language

        assert detect_response_language("What is the capital of Australia?") == "en"

    def test_detect_mixed_mostly_english(self):
        from apps.backend.src.core.prompt_manager import detect_response_language

        assert detect_response_language("OK done, thanks") == "en"

    def test_detect_empty(self):
        from apps.backend.src.core.prompt_manager import detect_response_language

        assert detect_response_language("") == "en"

    def test_zh_tw_falls_back_to_zh_template(self):
        from apps.backend.src.core.prompt_manager import PromptManager, PromptTemplate

        mgr = PromptManager()
        mgr.register(
            PromptTemplate(
                key="test.fallback_chain",
                templates={"en": "EN", "zh": "ZH"},
            )
        )
        assert mgr.get("test.fallback_chain", "zh-TW") == "ZH"

    def test_zh_locale_is_traditional(self):
        """zh 身份模板不得含簡體專用字。"""
        from apps.backend.src.core.prompt_manager import get_prompt_manager

        simplified_only = set("见说样吗过来还这进间谢帮点电岁两严专业脏")
        result = get_prompt_manager().get("angela.identity", "zh")
        assert not (simplified_only & set(result))

    def test_construct_angela_prompt_sets_language(self):
        """繁中輸入 → identity 為中文；英文輸入 → identity 為英文。"""
        from apps.backend.src.core.prompt_manager import get_prompt_manager
        from apps.backend.src.services.llm.prompt_builder import construct_angela_prompt

        msgs = construct_angela_prompt("你好嗎？", {})
        system = msgs[0]["content"]
        assert "數字生命" in system
        assert "Respond briefly and naturally in English" not in system

        msgs = construct_angela_prompt("What is 2+2?", {})
        system = msgs[0]["content"]
        assert "Respond briefly and naturally in English" in system
