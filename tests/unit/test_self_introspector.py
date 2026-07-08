"""Smoke tests for SelfIntrospector"""
from core.life.self_introspector import SelfIntrospector


class TestSelfIntrospector:
    """Basic smoke tests for SelfIntrospector"""

    def test_import(self):
        assert SelfIntrospector is not None

    def test_instantiation_default(self):
        instance = SelfIntrospector()
        assert instance is not None
        assert instance.config == {}
        assert instance.dissonance_threshold == 0.6

    def test_instantiation_with_config(self):
        instance = SelfIntrospector(config={"dissonance_threshold": 0.8})
        assert instance is not None
        assert instance.dissonance_threshold == 0.8

    def test_perform_mental_health_check_returns_coroutine(self):
        instance = SelfIntrospector()
        result = instance.perform_mental_health_check(combined_state={})
        import asyncio
        assert asyncio.iscoroutine(result)

    def test_get_introspection_prompt_injection_returns_string(self):
        instance = SelfIntrospector()
        prompt = instance.get_introspection_prompt_injection(combined_state={})
        assert isinstance(prompt, str)
        assert len(prompt) > 0
