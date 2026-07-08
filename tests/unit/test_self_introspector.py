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
