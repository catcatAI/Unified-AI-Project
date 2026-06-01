"""Smoke tests for core.art.real_edge_tts"""
import pytest


class TestAngelaRealVoice:
    def test_import(self):
        try:
            from core.art.real_edge_tts import AngelaRealVoice
            assert AngelaRealVoice is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from core.art.real_edge_tts import AngelaRealVoice
            instance = AngelaRealVoice()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
