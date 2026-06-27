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
