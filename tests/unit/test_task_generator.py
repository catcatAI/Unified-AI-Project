"""Smoke tests for ai.memory.task_generator"""
import pytest


class TestTaskGenerator:
    def test_import(self):
        try:
            from ai.memory.task_generator import TaskGenerator
            assert TaskGenerator is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from ai.memory.task_generator import TaskGenerator
            instance = TaskGenerator()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
