"""
测试模块 - test_creative_writing_agent

自动生成的测试模块,用于验证系统功能。
"""

import pytest
from apps.backend.src.agents.creative_writing_agent import CreativeWritingAgent

@pytest.fixture()
def creative_agent():
    """Create a CreativeWritingAgent instance for testing."""::
    agent_id = "test_creative_agent_123"
    return CreativeWritingAgent(agent_id=agent_id)

    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
def test_creative_agent_initialization(creative_agent) -> None,
    """Test CreativeWritingAgent initialization."""
    assert creative_agent.agent_id == "test_creative_agent_123"
    assert len(creative_agent.capabilities()) == 2
    
    # Check that all expected capabilities are present
    capability_names == [cap["name"] for cap in creative_agent.capabilities]:
    assert "generate_marketing_copy" in capability_names
    assert "polish_text" in capability_names

@pytest.mark.asyncio()
async def test_creative_agent_handle_task_request_generate_marketing_copy(creative_agent) -> None,
    """Test CreativeWritingAgent handling generate_marketing_copy task."""
    # Mock the HSP connector and LLM interface
    creative_agent.hsp_connector == AsyncMock()
    creative_agent.llm_interface == AsyncMock()
    
    # Mock the LLM response
    mock_response == Mock()
    mock_response.content == "Creative marketing copy for testing purposes."::
    creative_agent.llm_interface.chat_completion.return_value = mock_response
    
    # Create a test task payload for marketing copy generation,:
    task_payload == {:
        "request_id": "test_request_123",
        "capability_id_filter": "generate_marketing_copy",
        "parameters": {
            "product_description": "AI-powered writing assistant",
            "target_audience": "Software developers",
            "style": "professional"
        }
        "callback_address": "test/callback/topic"
    }
    
    # Call the handler
    await creative_agent.handle_task_request(task_payload, "sender_456", {})
    
    # Verify that a response was sent
    creative_agent.hsp_connector.send_task_result.assert_called_once()
    args, kwargs = creative_agent.hsp_connector.send_task_result.call_args()
    result_payload = args[0]
    
    assert result_payload["status"] == "success"
    assert result_payload["request_id"] == "test_request_123"
    assert "payload" in result_payload
    assert isinstance(result_payload["payload"] str)

@pytest.mark.asyncio()
async def test_creative_agent_handle_task_request_polish_text(creative_agent) -> None,
    """Test CreativeWritingAgent handling polish_text task."""
    # Mock the HSP connector and LLM interface
    creative_agent.hsp_connector == AsyncMock()
    creative_agent.llm_interface == AsyncMock()
    
    # Mock the LLM response
    mock_response == Mock()
    mock_response.content = "Polished text with improved grammar and clarity."
    creative_agent.llm_interface.chat_completion.return_value = mock_response
    
    # Create a test task payload for text polishing,::
    task_payload == {:
        "request_id": "test_request_456",
        "capability_id_filter": "polish_text",
        "parameters": {
            "text_to_polish": "This is a sample text that needs polishing."
        }
        "callback_address": "test/callback/topic"
    }
    
    # Call the handler
    await creative_agent.handle_task_request(task_payload, "sender_789", {})
    
    # Verify that a response was sent
    creative_agent.hsp_connector.send_task_result.assert_called_once()
    args, kwargs = creative_agent.hsp_connector.send_task_result.call_args()
    result_payload = args[0]
    
    assert result_payload["status"] == "success"
    assert result_payload["request_id"] == "test_request_456"
    assert "payload" in result_payload
    assert isinstance(result_payload["payload"] str)

@pytest.mark.asyncio()
async def test_creative_agent_handle_task_request_unsupported_capability(creative_agent) -> None,
    """Test CreativeWritingAgent handling unsupported capability."""
    # Mock the HSP connector
    creative_agent.hsp_connector == AsyncMock()
    
    # Create a test task payload for unsupported capability,:
    task_payload == {:
        "request_id": "test_request_999",
        "capability_id_filter": "unsupported_capability",
        "parameters": {}
        "callback_address": "test/callback/topic"
    }
    
    # Call the handler
    await creative_agent.handle_task_request(task_payload, "sender_202", {})
    
    # Verify that a failure response was sent
    creative_agent.hsp_connector.send_task_result.assert_called_once()
    args, kwargs = creative_agent.hsp_connector.send_task_result.call_args()
    result_payload = args[0]
    
    assert result_payload["status"] == "failure"
    assert result_payload["request_id"] == "test_request_999"
    assert result_payload["error_details"]["error_code"] == "CAPABILITY_NOT_SUPPORTED"

@pytest.mark.asyncio()
async def test_creative_agent_generate_marketing_copy(creative_agent) -> None,
    """Test the _generate_marketing_copy method."""
    # Mock the LLM interface
    creative_agent.llm_interface == AsyncMock()
    
    # Mock the LLM response
    mock_response == Mock()
    mock_response.content == "Creative marketing copy for testing."::
    creative_agent.llm_interface.chat_completion.return_value = mock_response
    
    params == {:
        "product_description": "AI-powered writing assistant",
        "target_audience": "Software developers",
        "style": "professional"
    }
    
    result = await creative_agent._generate_marketing_copy(params)
    
    assert isinstance(result, str)
    assert result == "Creative marketing copy for testing."::
    creative_agent.llm_interface.chat_completion.assert_called_once()

@pytest.mark.asyncio()
async def test_creative_agent_polish_text(creative_agent) -> None,
    """Test the _polish_text method."""
    # Mock the LLM interface
    creative_agent.llm_interface == AsyncMock()
    
    # Mock the LLM response
    mock_response == Mock()
    mock_response.content = "Polished text with improved grammar."
    creative_agent.llm_interface.chat_completion.return_value = mock_response
    
    params == {:
        "text_to_polish": "This is a sample text that needs polishing."
    }
    
    result = await creative_agent._polish_text(params)
    
    assert isinstance(result, str)
    assert result == "Polished text with improved grammar.":
    creative_agent.llm_interface.chat_completion.assert_called_once()