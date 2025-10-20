import pytest

@pytest.fixture
def code_agent():
    """Create a CodeUnderstandingAgent instance for testing."""
    agent_id = "test_code_agent_123"
    return CodeUnderstandingAgent(agent_id=agent_id)

def test_code_agent_initialization(code_agent) -> None:
    """Test CodeUnderstandingAgent initialization."""
    assert code_agent.agent_id == "test_code_agent_123"
    assert len(code_agent.capabilities) == 3
    
    # Check that all expected capabilities are present
    capability_names = [cap["name"] for cap in code_agent.capabilities]
    assert "analyze_code" in capability_names
    assert "generate_documentation" in capability_names
    assert "code_review" in capability_names

@pytest.mark.asyncio
async def test_code_agent_handle_task_request_analyze_code(code_agent) -> None:
    """Test CodeUnderstandingAgent handling analyze_code task."""
    # Mock the HSP connector
    code_agent.hsp_connector = AsyncMock()
    
    # Create a test task payload for code analysis
    task_payload = {
        "request_id": "test_request_123",
        "capability_id_filter": "analyze_code",
        "parameters": {
            "code": "def hello():\n    print('Hello, World!')",
            "language": "python"
        },
        "callback_address": "test/callback/topic"
    }
    
    # Call the handler
    _ = await code_agent.handle_task_request(task_payload, "sender_456", {})
    
    # Verify that a response was sent
    _ = code_agent.hsp_connector.send_task_result.assert_called_once()
    args, kwargs = code_agent.hsp_connector.send_task_result.call_args
    result_payload = args[0]
    
    assert result_payload["status"] == "success"
    assert result_payload["request_id"] == "test_request_123"
    assert "payload" in result_payload
    assert "language" in result_payload["payload"]
    assert "lines_of_code" in result_payload["payload"]

@pytest.mark.asyncio
async def test_code_agent_handle_task_request_generate_documentation(code_agent) -> None:
    """Test CodeUnderstandingAgent handling generate_documentation task."""
    # Mock the HSP connector
    code_agent.hsp_connector = AsyncMock()
    
    # Create a test task payload for documentation generation
    task_payload = {
        "request_id": "test_request_456",
        "capability_id_filter": "generate_documentation",
        "parameters": {
            "code": "def hello():\n    print('Hello, World!')",
            "style": "technical"
        },
        "callback_address": "test/callback/topic"
    }
    
    # Call the handler
    _ = await code_agent.handle_task_request(task_payload, "sender_789", {})
    
    # Verify that a response was sent
    _ = code_agent.hsp_connector.send_task_result.assert_called_once()
    args, kwargs = code_agent.hsp_connector.send_task_result.call_args
    result_payload = args[0]
    
    assert result_payload["status"] == "success"
    assert result_payload["request_id"] == "test_request_456"
    assert "payload" in result_payload
            assert isinstance(result_payload["payload"], str)    assert "# Technical Documentation" in result_payload["payload"]

@pytest.mark.asyncio
async def test_code_agent_handle_task_request_code_review(code_agent) -> None:
    """Test CodeUnderstandingAgent handling code_review task."""
    # Mock the HSP connector
    code_agent.hsp_connector = AsyncMock()
    
    # Create a test task payload for code review
    task_payload = {
        "request_id": "test_request_789",
        "capability_id_filter": "code_review",
        "parameters": {
            "code": "def hello():\n    print('Hello, World!')\n    # TODO: Add more functionality",
            "review_criteria": []
        },
        "callback_address": "test/callback/topic"
    }
    
    # Call the handler
    _ = await code_agent.handle_task_request(task_payload, "sender_101", {})
    
    # Verify that a response was sent
    _ = code_agent.hsp_connector.send_task_result.assert_called_once()
    args, kwargs = code_agent.hsp_connector.send_task_result.call_args
    result_payload = args[0]
    
    assert result_payload["status"] == "success"
    assert result_payload["request_id"] == "test_request_789"
    assert "payload" in result_payload
    assert "findings" in result_payload["payload"]
    assert "score" in result_payload["payload"]

@pytest.mark.asyncio
async def test_code_agent_handle_task_request_unsupported_capability(code_agent) -> None:
    """Test CodeUnderstandingAgent handling unsupported capability."""
    # Mock the HSP connector
    code_agent.hsp_connector = AsyncMock()
    
    # Create a test task payload for unsupported capability
    task_payload = {
        "request_id": "test_request_999",
        "capability_id_filter": "unsupported_capability",
        "parameters": {},
        "callback_address": "test/callback/topic"
    }
    
    # Call the handler
    _ = await code_agent.handle_task_request(task_payload, "sender_202", {})
    
    # Verify that a failure response was sent
    _ = code_agent.hsp_connector.send_task_result.assert_called_once()
    args, kwargs = code_agent.hsp_connector.send_task_result.call_args
    result_payload = args[0]
    
    assert result_payload["status"] == "failure"
    assert result_payload["request_id"] == "test_request_999"
    assert result_payload["error_details"]["error_code"] == "CAPABILITY_NOT_SUPPORTED"

def test_analyze_code_python(code_agent) -> None:
    """Test the _analyze_code method with Python code."""
    params = {
        "code": "def hello():\n    print('Hello, World!')",
        "language": "python"
    }
    
    result = code_agent._analyze_code(params)
    
    assert result["language"] == "python"
    assert result["lines_of_code"] == 2
    assert result["syntax_valid"] is True
    assert result["function_count"] == 1

def test_generate_documentation(code_agent) -> None:
    """Test the _generate_documentation method."""
    params = {
        "code": "def hello():\n    print('Hello, World!')",
        "style": "technical"
    }
    
    result = code_agent._generate_documentation(params)
    
    _ = assert isinstance(result, str)
    assert "# Technical Documentation" in result
    assert "## Functions" in result
    assert "`hello`" in result

def test_perform_code_review(code_agent) -> None:
    """Test the _perform_code_review method."""
    params = {
        "code": "def hello():\n    print('Hello, World!')\n    # TODO: Add more functionality",
        "review_criteria": []
    }
    
    result = code_agent._perform_code_review(params)
    
    assert "findings" in result
    assert "score" in result
    assert result["score"] <= 100  # Score should be 100 or less