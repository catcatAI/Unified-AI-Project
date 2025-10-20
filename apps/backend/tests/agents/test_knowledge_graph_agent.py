import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from apps.backend.src.ai.agents.specialized.knowledge_graph_agent import KnowledgeGraphAgent

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
def knowledge_graph_agent():
    """Fixture to provide a KnowledgeGraphAgent instance."""
    agent = KnowledgeGraphAgent(
        agent_id="did:hsp:knowledge_graph_agent_test"
    )
    return agent

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
@pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_knowledge_graph_agent_init(knowledge_graph_agent) -> None:
    """Test that the KnowledgeGraphAgent initializes correctly."""
    assert knowledge_graph_agent.agent_id == "did:hsp:knowledge_graph_agent_test"
    assert len(knowledge_graph_agent.capabilities) == 3
    capability_names = [cap['name'] for cap in knowledge_graph_agent.capabilities]
    assert "entity_linking" in capability_names
    assert "relationship_extraction" in capability_names
    assert "graph_query" in capability_names

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
async def test_knowledge_graph_agent_perform_entity_linking(knowledge_graph_agent) -> None:
    """Test the entity linking functionality."""
    params = {
        "text": "Apple Inc. is a technology company based in Cupertino, California."
    }
    
    result = knowledge_graph_agent._perform_entity_linking(params)
    
    assert "entities" in result
    assert "total_entities" in result
    assert result["total_entities"] >= 2  # Should find at least "Apple" and "Cupertino"
    
    # Check that entities have the expected structure
    entities = result["entities"]
    for entity in entities:
        assert "text" in entity
        assert "start" in entity
        assert "end" in entity
        assert "kb_id" in entity
        assert "confidence" in entity

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
async def test_knowledge_graph_agent_extract_relationships(knowledge_graph_agent) -> None:
    """Test the relationship extraction functionality."""
    params = {
        "text": "John is a software engineer. Mary has a cat."
    }
    
    result = knowledge_graph_agent._extract_relationships(params)
    
    assert "relationships" in result
    assert "total_relationships" in result
    assert result["total_relationships"] >= 1  # Should find at least one relationship
    
    # Check that relationships have the expected structure
    relationships = result["relationships"]
    for rel in relationships:
        assert "subject" in rel
        assert "predicate" in rel
        assert "object" in rel
        assert "confidence" in rel

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
async def test_knowledge_graph_agent_query_knowledge_graph(knowledge_graph_agent) -> None:
    """Test the knowledge graph query functionality."""
    params = {
        "query": "What is the capital of France?"
    }
    
    result = knowledge_graph_agent._query_knowledge_graph(params)
    
    assert "results" in result
    assert "total_results" in result
    assert result["total_results"] >= 1  # Should find at least one result
    
    # Check that results have the expected structure
    results = result["results"]
    for res in results:
        assert "entity" in res or "query" in res
        assert "property" in res or "result" in res
        assert "value" in res or "result" in res
        assert "confidence" in res

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
async def test_knowledge_graph_agent_handle_task_request_entity_linking(knowledge_graph_agent, mock_hsp_connector) -> None:
    """Test handling an entity linking task request."""
    with patch('apps.backend.src.core_services.initialize_services', new_callable=AsyncMock) as mock_init_services:
        with patch('apps.backend.src.core_services.get_services') as mock_get_services:
            mock_get_services.return_value = {
                'hsp_connector': mock_hsp_connector,
                _ = 'llm_interface': MagicMock(),
                _ = 'ham_manager': MagicMock(),
                _ = 'personality_manager': MagicMock(),
                _ = 'trust_manager': MagicMock(),
                _ = 'service_discovery': MagicMock(),
                _ = 'fact_extractor': MagicMock(),
                _ = 'content_analyzer': MagicMock(),
                _ = 'learning_manager': MagicMock(),
                _ = 'emotion_system': MagicMock(),
                _ = 'crisis_system': MagicMock(),
                _ = 'time_system': MagicMock(),
                _ = 'formula_engine': MagicMock(),
                _ = 'tool_dispatcher': MagicMock(),
                _ = 'dialogue_manager': MagicMock(),
                _ = 'agent_manager': MagicMock(),
                _ = 'ai_virtual_input_service': MagicMock(),
                _ = 'audio_service': MagicMock(),
                _ = 'vision_service': MagicMock(),
                _ = 'resource_awareness_service': MagicMock(),
            }
            _ = await knowledge_graph_agent._ainit()
            
            task_payload = {
                "request_id": "test_request_1",
                "capability_id_filter": "entity_linking_v1.0",
                "parameters": {
                    "text": "Microsoft is headquartered in Redmond, Washington."
                },
                "callback_address": "test_callback_1"
            }
            envelope = {"sender_ai_id": "test_sender"}
            
            _ = await knowledge_graph_agent.handle_task_request(task_payload, "test_sender", envelope)
            
            # Verify that send_task_result was called
            assert mock_hsp_connector.send_task_result.called
            call_args = mock_hsp_connector.send_task_result.call_args
            result_payload = call_args[0][0]
            callback_topic = call_args[0][1]
            
            assert result_payload["status"] == "success"
            assert "payload" in result_payload
            assert callback_topic == "test_callback_1"

@pytest.mark.asyncio
# 添加重试装饰器以处理不稳定的测试
async def test_knowledge_graph_agent_handle_task_request_unsupported_capability(knowledge_graph_agent, mock_hsp_connector) -> None:
    """Test handling a task request with an unsupported capability."""
    with patch('apps.backend.src.core_services.initialize_services', new_callable=AsyncMock) as mock_init_services:
        with patch('apps.backend.src.core_services.get_services') as mock_get_services:
            mock_get_services.return_value = {
                'hsp_connector': mock_hsp_connector,
                _ = 'llm_interface': MagicMock(),
                _ = 'ham_manager': MagicMock(),
                _ = 'personality_manager': MagicMock(),
                _ = 'trust_manager': MagicMock(),
                _ = 'service_discovery': MagicMock(),
                _ = 'fact_extractor': MagicMock(),
                _ = 'content_analyzer': MagicMock(),
                _ = 'learning_manager': MagicMock(),
                _ = 'emotion_system': MagicMock(),
                _ = 'crisis_system': MagicMock(),
                _ = 'time_system': MagicMock(),
                _ = 'formula_engine': MagicMock(),
                _ = 'tool_dispatcher': MagicMock(),
                _ = 'dialogue_manager': MagicMock(),
                _ = 'agent_manager': MagicMock(),
                _ = 'ai_virtual_input_service': MagicMock(),
                _ = 'audio_service': MagicMock(),
                _ = 'vision_service': MagicMock(),
                _ = 'resource_awareness_service': MagicMock(),
            }
            _ = await knowledge_graph_agent._ainit()
            
            task_payload = {
                "request_id": "test_request_2",
                "capability_id_filter": "unsupported_capability_v1.0",
                "parameters": {},
                "callback_address": "test_callback_2"
            }
            envelope = {"sender_ai_id": "test_sender"}
            
            _ = await knowledge_graph_agent.handle_task_request(task_payload, "test_sender", envelope)
            
            # Verify that send_task_result was called with failure
            assert mock_hsp_connector.send_task_result.called
            call_args = mock_hsp_connector.send_task_result.call_args
            result_payload = call_args[0][0]
            callback_topic = call_args[0][1]
            
            assert result_payload["status"] == "failure"
            assert "error_details" in result_payload
            assert result_payload["error_details"]["error_code"] == "CAPABILITY_NOT_SUPPORTED"
            assert callback_topic == "test_callback_2"