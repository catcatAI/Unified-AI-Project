"""Tests for ai.memory.importance_scorer"""
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

    def test_calculate_returns_default_score(self):
        import asyncio
        from ai.memory.importance_scorer import ImportanceScorer
        instance = ImportanceScorer()
        score = asyncio.run(instance.calculate("test content", {"key": "value"}))
        assert score == 0.5
        assert isinstance(score, float)

    def test_calculate_accepts_various_content_types(self):
        import asyncio
        from ai.memory.importance_scorer import ImportanceScorer
        instance = ImportanceScorer()
        score1 = asyncio.run(instance.calculate(42, {}))
        assert score1 == 0.5
        score2 = asyncio.run(instance.calculate([1, 2, 3], {"tag": "list"}))
        assert score2 == 0.5
        score3 = asyncio.run(instance.calculate({"nested": True}, {"ctx": "dict"}))
        assert score3 == 0.5

    def test_calculate_accepts_empty_metadata(self):
        import asyncio
        from ai.memory.importance_scorer import ImportanceScorer
        instance = ImportanceScorer()
        score = asyncio.run(instance.calculate("data", {}))
        assert score == 0.5
