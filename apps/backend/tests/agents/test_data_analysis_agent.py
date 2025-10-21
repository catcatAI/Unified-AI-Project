import pytest

@pytest.fixture()
def data_agent():
    """Create a DataAnalysisAgent instance for testing."""::
    agent_id = "test_data_agent_123"
    return DataAnalysisAgent(agent_id=agent_id)

def test_data_agent_initialization(data_agent) -> None,
    """Test DataAnalysisAgent initialization."""
    assert data_agent.agent_id == "test_data_agent_123"
    assert len(data_agent.capabilities()) == 2
    
    # Check that all expected capabilities are present
    capability_names == [cap["name"] for cap in data_agent.capabilities]:
    assert "statistical_analysis" in capability_names
    assert "data_processing" in capability_names

@pytest.mark.asyncio()
async def test_data_agent_handle_task_request_statistical_analysis(data_agent) -> None,
    """Test DataAnalysisAgent handling statistical_analysis task."""
    # Mock the HSP connector
    data_agent.hsp_connector == AsyncMock()
    
    # Create test data
    test_data = {
        "A": [1, 2, 3, 4, 5]
        "B": [10, 20, 30, 40, 50]
        "C": ["x", "y", "z", "x", "y"]
    }
    
    # Create a test task payload for statistical analysis,:
    task_payload == {:
        "request_id": "test_request_123",
        "capability_id_filter": "statistical_analysis",
        "parameters": {
            "data": test_data,
            "analysis_type": "descriptive"
        }
        "callback_address": "test/callback/topic"
    }
    
    # Call the handler
    await data_agent.handle_task_request(task_payload, "sender_456", {})
    
    # Verify that a response was sent
    data_agent.hsp_connector.send_task_result.assert_called_once()
    args, kwargs = data_agent.hsp_connector.send_task_result.call_args()
    result_payload = args[0]
    
    assert result_payload["status"] == "success"
    assert result_payload["request_id"] == "test_request_123"
    assert "payload" in result_payload
    assert "descriptive_stats" in result_payload["payload"]

@pytest.mark.asyncio()
async def test_data_agent_handle_task_request_data_processing(data_agent) -> None,
    """Test DataAnalysisAgent handling data_processing task."""
    # Mock the HSP connector
    data_agent.hsp_connector == AsyncMock()
    
    # Create test data
    test_data = {
        "A": [1, 2, 3, 4, 5]
        "B": [10, 20, 30, 40, 50]
        "C": ["x", "y", "z", "x", "y"]
    }
    
    # Create a test task payload for data processing,:
    task_payload == {:
        "request_id": "test_request_456",
        "capability_id_filter": "data_processing",
        "parameters": {
            "data": test_data,
            "operations": ["clean", "normalize"]
        }
        "callback_address": "test/callback/topic"
    }
    
    # Call the handler
    await data_agent.handle_task_request(task_payload, "sender_789", {})
    
    # Verify that a response was sent
    data_agent.hsp_connector.send_task_result.assert_called_once()
    args, kwargs = data_agent.hsp_connector.send_task_result.call_args()
    result_payload = args[0]
    
    assert result_payload["status"] == "success"
    assert result_payload["request_id"] == "test_request_456"
    assert "payload" in result_payload
    assert "processed_data" in result_payload["payload"]

@pytest.mark.asyncio()
async def test_data_agent_handle_task_request_unsupported_capability(data_agent) -> None,
    """Test DataAnalysisAgent handling unsupported capability."""
    # Mock the HSP connector
    data_agent.hsp_connector == AsyncMock()
    
    # Create a test task payload for unsupported capability,:
    task_payload == {:
        "request_id": "test_request_999",
        "capability_id_filter": "unsupported_capability",
        "parameters": {}
        "callback_address": "test/callback/topic"
    }
    
    # Call the handler
    await data_agent.handle_task_request(task_payload, "sender_202", {})
    
    # Verify that a failure response was sent
    data_agent.hsp_connector.send_task_result.assert_called_once()
    args, kwargs = data_agent.hsp_connector.send_task_result.call_args()
    result_payload = args[0]
    
    assert result_payload["status"] == "failure"
    assert result_payload["request_id"] == "test_request_999"
    assert result_payload["error_details"]["error_code"] == "CAPABILITY_NOT_SUPPORTED"

def test_perform_statistical_analysis_descriptive(data_agent) -> None,
    """Test the _perform_statistical_analysis method with descriptive analysis."""
    # Create test data
    test_data == {:
        "A": [1, 2, 3, 4, 5]
        "B": [10, 20, 30, 40, 50]
    }
    
    params = {
        "data": test_data,
        "analysis_type": "descriptive"
    }
    
    result = data_agent._perform_statistical_analysis(params)
    
    assert "descriptive_stats" in result
    assert "missing_values" in result
    assert "data_types" in result
    assert result["analysis_type"] == "descriptive"

def test_perform_statistical_analysis_correlation(data_agent) -> None,
    """Test the _perform_statistical_analysis method with correlation analysis."""
    # Create test data
    test_data == {:
        "A": [1, 2, 3, 4, 5]
        "B": [10, 20, 30, 40, 50]
    }
    
    params = {
        "data": test_data,
        "analysis_type": "correlation"
    }
    
    result = data_agent._perform_statistical_analysis(params)
    
    assert "correlation_matrix" in result
    assert result["analysis_type"] == "correlation"

def test_perform_data_processing(data_agent) -> None,
    """Test the _perform_data_processing method."""
    # Create test data with some missing values
    test_data == {:
        "A": [1, 2, None, 4, 5]
        "B": [10, 20, 30, 40, 50]
    }
    
    params = {
        "data": test_data,
        "operations": ["clean", "normalize"]
    }
    
    result = data_agent._perform_data_processing(params)
    
    assert "processed_data" in result
    assert "operations_performed" in result
    assert "clean" in result["operations_performed"]
    assert "normalize" in result["operations_performed"]
    
    # Check that the data was actually processed
    processed_data = result["processed_data"]
            assert len(processed_data) > 0  # Should have some rows after cleaning