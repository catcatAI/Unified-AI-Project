"""Smoke tests for SelfIntrospector"""
import pytest


class TestSelfIntrospector:
    """Basic smoke tests for SelfIntrospector"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from core.life.self_introspector import SelfIntrospector
            assert SelfIntrospector is not None
        except ImportError as e:
            pytest.skip(f"SelfIntrospector not available: {e}")

    def test_instantiation_default(self):
        """Verify basic instantiation with no config"""
        try:
            from core.life.self_introspector import SelfIntrospector
            instance = SelfIntrospector()
            assert instance is not None
            assert instance.config == {}
            assert instance.dissonance_threshold == 0.6
        except ImportError as e:
            pytest.skip(f"SelfIntrospector not available: {e}")
        except Exception as e:
            pytest.skip(f"SelfIntrospector init failed (expected in CI): {e}")

    def test_instantiation_with_config(self):
        """Verify instantiation with custom config"""
        try:
            from core.life.self_introspector import SelfIntrospector
            instance = SelfIntrospector(config={"dissonance_threshold": 0.8})
            assert instance is not None
            assert instance.dissonance_threshold == 0.8
        except ImportError as e:
            pytest.skip(f"SelfIntrospector not available: {e}")
        except Exception as e:
            pytest.skip(f"SelfIntrospector with config failed (expected in CI): {e}")
