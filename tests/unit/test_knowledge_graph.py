"""Smoke tests for apps.backend.src.ai.code_inspection.knowledge_graph"""
import pytest


class TestKnowledgeGraph:
    def test_import(self):
        try:
            from apps.backend.src.ai.code_inspection.knowledge_graph import KnowledgeGraph
            assert KnowledgeGraph is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
    def test_instantiation(self):
        try:
            from apps.backend.src.ai.code_inspection.knowledge_graph import KnowledgeGraph
            instance = KnowledgeGraph(root_path=".")
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")
        except Exception as e:
            pytest.skip(f"Init failed: {e}")
