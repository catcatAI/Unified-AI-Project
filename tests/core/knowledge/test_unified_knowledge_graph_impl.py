"""Tests for UnifiedKnowledgeGraph."""
import pytest
from core.knowledge.unified_knowledge_graph_impl import UnifiedKnowledgeGraph


class TestUnifiedKnowledgeGraph:
    def test_init_default(self):
        kg = UnifiedKnowledgeGraph()
        assert kg.config == {}
        assert kg.initialized is False

    def test_init_with_config(self):
        kg = UnifiedKnowledgeGraph(config={"name": "test"})
        assert kg.config["name"] == "test"

    @pytest.mark.asyncio
    async def test_initialize(self):
        kg = UnifiedKnowledgeGraph()
        assert kg.initialized is False
        await kg.initialize()
        assert kg.initialized is True

    @pytest.mark.asyncio
    async def test_is_initialized_after_init(self):
        kg = UnifiedKnowledgeGraph()
        assert kg.is_initialized() is False
        await kg.initialize()
        assert kg.is_initialized() is True

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self):
        kg = UnifiedKnowledgeGraph()
        await kg.initialize()
        assert kg.initialized is True
        await kg.initialize()
        assert kg.initialized is True

    def test_is_initialized_before_init(self):
        kg = UnifiedKnowledgeGraph(config={})
        assert kg.is_initialized() is False
