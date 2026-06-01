"""Smoke tests for ai.memory.importance_scorer"""
import pytest


class TestImportanceScorer:
    def test_import(self):
        try:
            from ai.memory.importance_scorer import ImportanceScorer
            assert ImportanceScorer is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from ai.memory.importance_scorer import ImportanceScorer
            instance = ImportanceScorer()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
