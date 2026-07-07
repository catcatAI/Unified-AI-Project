import pytest

pytest.importorskip("ai.agents.specialized.knowledge_graph_agent")
from ai.agents.specialized.knowledge_graph_agent import KnowledgeGraphAgent


class TestKnowledgeUpdate:
    async def test_knowledge_graph_agent_instantiation(self):
        agent = KnowledgeGraphAgent()
        assert agent is not None
        assert len(agent._entities) == 0

    async def test_knowledge_graph_add_query(self):
        agent = KnowledgeGraphAgent()
        entity_id = agent.add_entity("test_entity", {"key": "value"})
        assert entity_id is not None
        result = agent.query_graph(query="test_entity")
        assert len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
