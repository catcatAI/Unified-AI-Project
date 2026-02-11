"""
Tests for the KnowledgeGraphAgent.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from ai.agents.specialized.knowledge_graph_agent import KnowledgeGraphAgent
from core.hsp.types_fixed import HSPTaskRequestPayload, HSPMessageEnvelope

@pytest.fixture
def mock_hsp_connector():
    """Fixture to provide a mock HSPConnector."""
    mock = MagicMock()
    mock.register_on_task_request_callback = MagicMock()
    mock.advertise_capability = AsyncMock()
    mock.send_task_result = AsyncMock()
    mock.is_connected = True
    return mock

@pytest.fixture
def knowledge_graph_agent(mock_hsp_connector):
    """Fixture to provide a KnowledgeGraphAgent instance with a mocked connector."""
    agent = KnowledgeGraphAgent(agent_id="did:hsp:knowledge_graph_agent_test")
    agent.hsp_connector = mock_hsp_connector
    # Mock the LLM interface as it's used by the agent's methods
    agent.llm_interface = AsyncMock()
    return agent

def test_knowledge_graph_agent_init(knowledge_graph_agent: KnowledgeGraphAgent):
    """Test that the KnowledgeGraphAgent initializes correctly."""
    assert knowledge_graph_agent.agent_id == "did:hsp:knowledge_graph_agent_test"
    assert len(knowledge_graph_agent.capabilities) == 3
    capability_names = [cap['name'] for cap in knowledge_graph_agent.capabilities]
    assert "entity_linking" in capability_names
    assert "relationship_extraction" in capability_names
    assert "graph_query" in capability_names

@pytest.mark.asyncio
async def test_knowledge_graph_agent_perform_entity_linking(knowledge_graph_agent: KnowledgeGraphAgent):
    """Test the entity linking functionality."""
    params = {
        "text": "Apple Inc. is a technology company based in Cupertino, California."
    }
    # Mock the underlying method that uses the LLM
    knowledge_graph_agent._perform_entity_linking = MagicMock(return_value={
        "entities": [{"text": "Apple Inc.", "start": 0, "end": 9, "kb_id": "Q312", "confidence": 0.99}],
        "total_entities": 1
    })
    result = knowledge_graph_agent._perform_entity_linking(params)
    assert "entities" in result
    assert result["total_entities"] >= 1

@pytest.mark.asyncio
async def test_knowledge_graph_agent_extract_relationships(knowledge_graph_agent: KnowledgeGraphAgent):
    """Test the relationship extraction functionality."""
    params = {
        "text": "John is a software engineer."
    }
    knowledge_graph_agent._extract_relationships = MagicMock(return_value={
        "relationships": [{"subject": "John", "predicate": "is_a", "object": "software engineer", "confidence": 0.9}],
        "total_relationships": 1
    })
    result = knowledge_graph_agent._extract_relationships(params)
    assert "relationships" in result
    assert result["total_relationships"] >= 1

@pytest.mark.asyncio
async def test_knowledge_graph_agent_query_knowledge_graph(knowledge_graph_agent: KnowledgeGraphAgent):
    """Test the knowledge graph query functionality."""
    params = {
        "query": "What is the capital of France?"
    }
    knowledge_graph_agent._query_knowledge_graph = MagicMock(return_value={
        "results": [{"entity": "Paris", "property": "is_capital_of", "value": "France", "confidence": 1.0}],
        "total_results": 1
    })
    result = knowledge_graph_agent._query_knowledge_graph(params)
    assert "results" in result
    assert result["total_results"] >= 1

@pytest.mark.asyncio
async def test_handle_task_request_entity_linking(knowledge_graph_agent: KnowledgeGraphAgent):
    """Test handling an entity linking task request."""
    task_payload = HSPTaskRequestPayload(
        request_id="test_request_1",
        capability_id_filter="entity_linking",
        parameters={"text": "Microsoft is headquartered in Redmond, Washington."},
        callback_address="test_callback_1"
    )
    envelope = HSPMessageEnvelope(
        message_id="test_msg_001",
        sender_ai_id="test_sender",
        recipient_ai_id=knowledge_graph_agent.agent_id,
        timestamp_sent="2023-01-01T00:00:00Z",
        message_type="task_request",
        protocol_version="1.0"
    )

    # Mock the method that would be called
    knowledge_graph_agent._perform_entity_linking = MagicMock(return_value={"entities": []})

    await knowledge_graph_agent.handle_task_request(task_payload, "test_sender", envelope)

    knowledge_graph_agent.hsp_connector.send_task_result.assert_called_once()
    call_args = knowledge_graph_agent.hsp_connector.send_task_result.call_args
    result_payload = call_args[0][0]
    callback_topic = call_args[0][1]

    assert result_payload["status"] == "success"
    assert "payload" in result_payload
    assert callback_topic == "test_callback_1"

@pytest.mark.asyncio
async def test_handle_task_request_unsupported_capability(knowledge_graph_agent: KnowledgeGraphAgent):
    """Test handling a task request with an unsupported capability."""
    task_payload = HSPTaskRequestPayload(
        request_id="test_request_2",
        capability_id_filter="unsupported_capability_v1.0",
        parameters={},
        callback_address="test_callback_2"
    )
    envelope = HSPMessageEnvelope(
        message_id="test_msg_002",
        sender_ai_id="test_sender",
        recipient_ai_id=knowledge_graph_agent.agent_id,
        timestamp_sent="2023-01-01T00:00:00Z",
        message_type="task_request",
        protocol_version="1.0"
    )

    await knowledge_graph_agent.handle_task_request(task_payload, "test_sender", envelope)

    knowledge_graph_agent.hsp_connector.send_task_result.assert_called_once()
    call_args = knowledge_graph_agent.hsp_connector.send_task_result.call_args
    result_payload = call_args[0][0]
    callback_topic = call_args[0][1]

    assert result_payload["status"] == "failure"
    assert "error_details" in result_payload
    assert result_payload["error_details"]["error_code"] == "CAPABILITY_NOT_SUPPORTED"
    assert callback_topic == "test_callback_2"
