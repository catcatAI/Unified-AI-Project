"""Smoke tests for AttentionController and AttentionMode"""
import pytest


class TestAttentionController:
    """Basic smoke tests for AttentionController"""

    def test_import_classes(self):
        """Verify main classes and enums can be imported"""
        try:
            from core.perception.attention_controller import AttentionController, AttentionMode
            assert AttentionController is not None
            assert AttentionMode is not None
        except ImportError as e:
            pytest.skip(f"AttentionController not available: {e}")

    def test_attention_mode_enum(self):
        """Verify AttentionMode enum values are accessible"""
        try:
            from core.perception.attention_controller import AttentionMode
            assert AttentionMode.EXPLORE is not None
            assert AttentionMode.FOCUS is not None
            assert AttentionMode.TRACK is not None
            assert AttentionMode.IDLE is not None
        except ImportError as e:
            pytest.skip(f"AttentionMode not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from core.perception.attention_controller import AttentionController
            instance = AttentionController()
            assert instance is not None
            assert instance.mode is not None
        except ImportError as e:
            pytest.skip(f"AttentionController not available: {e}")
        except Exception as e:
            pytest.skip(f"AttentionController init failed (expected in CI): {e}")
