"""Tests for ai.memory.importance_scorer — matches actual calculate() behavior

NOTE: ImportanceScorer.calculate() is SYNCHRONOUS (returns float),
not async. Tests call it directly without asyncio.run().
"""
import pytest


class TestImportanceScorer:
    def test_import(self):
        from ai.memory.importance_scorer import ImportanceScorer
        assert hasattr(ImportanceScorer, 'calculate')

    def test_instantiation(self):
        from ai.memory.importance_scorer import ImportanceScorer
        instance = ImportanceScorer()
        assert isinstance(instance, ImportanceScorer)

    def test_calculate_returns_float(self):
        from ai.memory.importance_scorer import ImportanceScorer
        instance = ImportanceScorer()
        result = instance.calculate("hello", {"source": "user"})
        assert isinstance(result, float)

    def test_calculate_returns_float_in_range(self):
        from ai.memory.importance_scorer import ImportanceScorer
        instance = ImportanceScorer()
        score = instance.calculate("test content", {"key": "value"})
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_calculate_accepts_various_content_types(self):
        from ai.memory.importance_scorer import ImportanceScorer
        instance = ImportanceScorer()
        score1 = instance.calculate(42, {})
        assert 0.0 <= score1 <= 1.0
        score2 = instance.calculate([1, 2, 3], {"tag": "list"})
        assert 0.0 <= score2 <= 1.0
        score3 = instance.calculate({"nested": True}, {"ctx": "dict"})
        assert 0.0 <= score3 <= 1.0

    def test_calculate_returns_float_with_empty_metadata(self):
        from ai.memory.importance_scorer import ImportanceScorer
        instance = ImportanceScorer()
        score = instance.calculate("data", {})
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
