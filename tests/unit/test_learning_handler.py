"""Tests for LearningHandler"""
import pytest


class TestLearningHandler:
    """Tests for LearningHandler"""

    def test_import(self):
        from services.handlers.learning_handler import LearningHandler
        assert LearningHandler is not None

    def test_instantiation(self):
        from services.handlers.learning_handler import LearningHandler
        instance = LearningHandler()
        assert instance is not None
        assert instance._anchor is None

    def test_handle_no_fact(self):
        import asyncio

        from services.handlers.learning_handler import LearningHandler
        instance = LearningHandler()
        result = asyncio.run(instance.handle("", "learning"))
        assert "記住" in result

    def test_handle_with_fact(self):
        import asyncio

        from services.handlers.learning_handler import LearningHandler
        instance = LearningHandler()
        result = asyncio.run(instance.handle("記住 2+2=4", "learning"))
        assert "記住" in result
        assert isinstance(result, str)
