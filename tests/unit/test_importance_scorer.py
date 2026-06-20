"""Tests for ai.memory.importance_scorer — matches actual calculate() behavior"""
import pytest


class TestImportanceScorer:
    def test_import(self):
        from ai.memory.importance_scorer import ImportanceScorer
        assert hasattr(ImportanceScorer, 'calculate')

    def test_instantiation(self):
        from ai.memory.importance_scorer import ImportanceScorer
        instance = ImportanceScorer()
        assert isinstance(instance, ImportanceScorer)

    def test_calculate_is_coroutine(self):
        from ai.memory.importance_scorer import ImportanceScorer
        instance = ImportanceScorer()
        coro = instance.calculate("hello", {"source": "user"})
        assert hasattr(coro, "__await__")

    def test_calculate_returns_float_in_range(self):
        import asyncio
        from ai.memory.importance_scorer import ImportanceScorer
        instance = ImportanceScorer()
        score = asyncio.run(instance.calculate("test content", {"key": "value"}))
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_calculate_accepts_various_content_types(self):
        import asyncio
        from ai.memory.importance_scorer import ImportanceScorer
        instance = ImportanceScorer()
        score1 = asyncio.run(instance.calculate(42, {}))
        assert 0.0 <= score1 <= 1.0
        score2 = asyncio.run(instance.calculate([1, 2, 3], {"tag": "list"}))
        assert 0.0 <= score2 <= 1.0
        score3 = asyncio.run(instance.calculate({"nested": True}, {"ctx": "dict"}))
        assert 0.0 <= score3 <= 1.0

    def test_calculate_returns_float_with_empty_metadata(self):
        import asyncio
        from ai.memory.importance_scorer import ImportanceScorer
        instance = ImportanceScorer()
        score = asyncio.run(instance.calculate("data", {}))
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
