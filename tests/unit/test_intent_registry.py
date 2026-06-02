"""Tests for core/intent_registry.py"""
import pytest


class TestIntentRegistry:
    """Tests for IntentRegistry"""

    def test_import(self):
        """Verify module can be imported"""
        from core.intent_registry import IntentRegistry, IntentPattern
        assert hasattr(IntentRegistry, 'detect')
        assert hasattr(IntentRegistry, 'register')
        assert hasattr(IntentRegistry, 'detect_task_intent')
        assert hasattr(IntentRegistry, 'detect_complex_task')
        assert hasattr(IntentRegistry, 'detect_task_type')
        assert hasattr(IntentRegistry, 'get_keywords')
        assert hasattr(IntentPattern, 'name')
        assert hasattr(IntentPattern, 'keywords')
        assert hasattr(IntentPattern, 'category')
        assert hasattr(IntentPattern, 'priority')

    def test_instantiation(self):
        """Verify no-arg instantiation"""
        from core.intent_registry import IntentRegistry
        instance = IntentRegistry()
        assert instance._initialized is True
        assert len(instance.patterns) > 0
        assert len(instance._keyword_to_patterns) > 0

    def test_detect_method(self):
        """Verify detect() method works"""
        from core.intent_registry import IntentRegistry
        instance = IntentRegistry()

        name, confidence = instance.detect("生成一个角色卡")
        assert name is not None
        assert confidence > 0.0

        name, confidence = instance.detect("計算 1+1")
        assert name is not None
        assert confidence > 0.0

        name, confidence = instance.detect("你好世界")
        assert name is None
        assert confidence == 0.0

    def test_register_pattern(self):
        """Verify register() method works"""
        from core.intent_registry import IntentRegistry, IntentPattern
        instance = IntentRegistry()
        pattern = IntentPattern(
            name="sports_query",
            keywords=["籃球", "棒球", "足球"],
            category="general",
            priority=8,
        )
        instance.register(pattern)
        assert pattern in instance.patterns

        name, confidence = instance.detect("我想看籃球比賽")
        assert name == "sports_query"
        assert confidence > 0.0
