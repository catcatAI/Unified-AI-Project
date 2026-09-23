import pytest

pytest.importorskip("ai.agents.specialized.knowledge_graph_agent")
from ai.agents.specialized.knowledge_graph_agent import KnowledgeGraphAgent


class TestKnowledgeUpdate:
    @pytest.mark.asyncio
    async def test_knowledge_graph_agent_instantiation(self):
        agent = KnowledgeGraphAgent()
        assert agent is not None
        assert len(agent._entities) == 0

    @pytest.mark.asyncio
    async def test_knowledge_graph_add_query(self):
        agent = KnowledgeGraphAgent()
        entity_id = agent.add_entity("test_entity", {"key": "value"})
        assert entity_id is not None
        result = agent.query_graph(query="test_entity")
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_entity_linking_capability_executes(self):
        """R87 死路徑 #12 回歸：capability "entity_linking" 已對外註冊，
        此前處理函式不存在 → 一執行就 AttributeError。必須閉環成功。"""
        agent = KnowledgeGraphAgent()
        agent.add_entity("Angela", {"type": "ai"})
        agent.add_entity("Luanti", {"type": "game"})
        sent = {}

        class _FakeHSP:
            async def send_task_result(self, payload, address):
                sent["payload"] = payload
                sent["address"] = address

        agent.hsp_connector = _FakeHSP()
        await agent.handle_task_request(
            {
                "capability_id_filter": "entity_linking",
                "parameters": {"text": "Angela plays Luanti"},
                "request_id": "r1",
                "callback_address": "cb",
            },
            "sender",
            None,
        )
        assert sent["payload"]["status"] == "success"
        mentions = sent["payload"]["payload"]["mentions"]
        assert [m["entity"] for m in mentions] == ["Angela", "Luanti"]

    @pytest.mark.asyncio
    async def test_relationship_extraction_capability_executes(self):
        """R87 死路徑 #12 回歸：capability "relationship_extraction" 同上。"""
        agent = KnowledgeGraphAgent()
        agent.add_entity("A", {})
        agent.add_entity("B", {})
        agent._relations.append({"source": "A", "target": "B", "type": "friend"})
        sent = {}

        class _FakeHSP:
            async def send_task_result(self, payload, address):
                sent["payload"] = payload

        agent.hsp_connector = _FakeHSP()
        await agent.handle_task_request(
            {
                "capability_id_filter": "relationship_extraction",
                "parameters": {"text": "A met B"},
                "request_id": "r2",
                "callback_address": "cb",
            },
            "sender",
            None,
        )
        assert sent["payload"]["status"] == "success"
        rels = sent["payload"]["payload"]["relationships"]
        assert any(r.get("type") == "friend" for r in rels)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
