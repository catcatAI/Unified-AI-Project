import pytest

from apps.backend.src.core.intent_registry import IntentPattern, IntentRegistry


class TestIntentRegistry:
    @pytest.fixture
    def registry(self):
        r = IntentRegistry()
        r.patterns = []
        r._keyword_to_patterns = {}
        r._initialized = True
        return r

    def test_detect_returns_none_for_empty_text(self, registry):
        intent, conf = registry.detect("")
        assert intent is None
        assert conf == 0.0

    def test_detect_unmatched_text(self, registry):
        intent, conf = registry.detect("no keywords here")
        assert intent is None
        assert conf == 0.0

    def test_single_keyword_match(self, registry):
        registry.register(IntentPattern("greeting", ["hello", "hi"], "general", priority=5))
        intent, conf = registry.detect("hello world")
        assert intent == "greeting"
        assert conf > 0.0

    def test_priority_based_matching(self, registry):
        registry.register(IntentPattern("low", ["test"], "general", priority=1))
        registry.register(IntentPattern("high", ["test"], "general", priority=10))
        intent, conf = registry.detect("test keyword")
        assert intent is not None

    def test_category_filter(self, registry):
        registry.register(IntentPattern("a", ["keyword"], "cat_a", priority=5))
        registry.register(IntentPattern("b", ["keyword"], "cat_b", priority=5))
        intent, conf = registry.detect("keyword", category="cat_a")
        assert intent == "a"

    def test_category_filter_excludes_other(self, registry):
        registry.register(IntentPattern("a", ["keyword"], "cat_a", priority=5))
        registry.register(IntentPattern("b", ["keyword"], "cat_b", priority=5))
        intent, conf = registry.detect("keyword", category="nonexistent")
        assert intent is None
        assert conf == 0.0

    def test_register_dynamic_pattern(self, registry):
        new_pattern = IntentPattern("test_intent", ["test_kw"], "test_cat", priority=10)
        registry.register(new_pattern)
        assert len(registry.patterns) == 1
        intent, conf = registry.detect("test_kw here")
        assert intent == "test_intent"

    def test_get_keywords_existing(self, registry):
        registry.register(IntentPattern("test_intent", ["kw1", "kw2"], "cat", priority=5))
        kws = registry.get_keywords("test_intent")
        assert kws == ["kw1", "kw2"]

    def test_get_keywords_nonexistent(self, registry):
        kws = registry.get_keywords("nonexistent_intent")
        assert kws == []

    def test_detect_task_intent_interface(self, registry):
        registry.register(IntentPattern("task", ["生成"], "task", priority=5))
        result = registry.detect_task_intent("生成文件")
        assert result is not None

    def test_detect_task_intent_low_confidence(self, registry):
        registry.register(IntentPattern("task", ["生成"], "task", priority=1))
        result = registry.detect_task_intent("no trigger")
        assert result is None

    def test_detect_complex_task_true(self, registry):
        registry.register(IntentPattern("task", ["生成"], "task", priority=5))
        result = registry.detect_complex_task("生成一份報告")
        assert result is True

    def test_detect_complex_task_long_text(self, registry):
        registry.register(IntentPattern("task", ["生成"], "task", priority=5))
        result = registry.detect_complex_task("x" * 100)
        assert result is True

    def test_detect_complex_task_false(self, registry):
        registry.register(IntentPattern("task", ["生成"], "task", priority=5))
        result = registry.detect_complex_task("short")
        assert result is False

    def test_detect_task_type_known(self, registry):
        registry.register(IntentPattern("character_card", ["角色", "角色卡"], "character_card", priority=6))
        result = registry.detect_task_type("生成角色")
        assert result == "character_card"

    def test_detect_task_type_default(self, registry):
        result = registry.detect_task_type("hello world")
        assert result == "general"

    def test_detect_multiple_keywords_increases_confidence(self, registry):
        registry.register(IntentPattern("task", ["生成", "建立", "創建"], "task", priority=5))
        intent, conf_many = registry.detect("生成建立創建")
        intent, conf_one = registry.detect("生成")
        assert conf_many > conf_one

    def test_register_preserves_existing_patterns(self, registry):
        registry.register(IntentPattern("p1", ["kw1"], "cat", priority=5))
        registry.register(IntentPattern("p2", ["kw2"], "cat", priority=5))
        assert len(registry.patterns) == 2

    def test_detect_task_type_prioritizes_order(self, registry):
        registry.register(IntentPattern("character_card", ["角色"], "character_card", priority=6))
        result = registry.detect_task_type("角色")
        assert result == "character_card"

    def test_detect_handles_empty_patterns(self, registry):
        intent, conf = registry.detect("anything")
        assert intent is None
        assert conf == 0.0
