"""
Test the default agents system to ensure agents are automatically available.
"""
import pytest
import asyncio
from src.core_services import initialize_services, get_services, shutdown_services


@pytest.mark.asyncio
async def test_default_data_analysis_agent_available():
    """Test that DataAnalysisAgent is automatically available after service initialization."""
    # Initialize services with default agents
    await initialize_services(use_mock_ham=True)
    
    try:
        services = get_services()
        service_discovery = services.get("service_discovery")
        
        # Check that data_analysis_v1 capability is available
        assert service_discovery is not None
        capabilities = service_discovery.known_capabilities
        assert "data_analysis_v1" in capabilities
        
        capability_info, _ = capabilities["data_analysis_v1"]
        assert capability_info["name"] == "CSV Data Analyzer"
        assert capability_info["ai_id"] == "did:hsp:default_data_analysis_agent"
        
    finally:
        await shutdown_services()


@pytest.mark.asyncio
async def test_project_coordinator_with_default_agents():
    """Test that ProjectCoordinator can find and use default agents."""
    # Initialize services with default agents
    await initialize_services(use_mock_ham=True)
    
    try:
        services = get_services()
        dialogue_manager = services.get("dialogue_manager")
        project_coordinator = dialogue_manager.project_coordinator
        
        # Test project request that should use DataAnalysisAgent
        project_query = "Analyze this CSV data: a,b\n1,2\n3,4"
        
        # Mock the LLM decomposition to return a task for data_analysis_v1
        async def mock_decompose(query, capabilities):
            return [
                {
                    "capability_needed": "data_analysis_v1",
                    "task_parameters": {"csv_content": "a,b\n1,2\n3,4"},
                    "task_description": "Analyze CSV data"
                }
            ]
        
        # Mock the LLM integration
        async def mock_integrate(query, results):
            return "The CSV data has been analyzed successfully. It contains 2 rows of data."
        
        # Apply mocks
        project_coordinator._decompose_user_intent_into_subtasks = mock_decompose
        project_coordinator._integrate_subtask_results = mock_integrate
        
        # Execute the project
        result = await project_coordinator.handle_project(project_query, "test_session", "test_user")
        
        # Verify the result
        assert "TestCoordinator" in result or "Here's the result" in result
        assert "analyzed successfully" in result
        
    finally:
        await shutdown_services()


@pytest.mark.asyncio
async def test_data_analysis_agent_task_handling():
    """Test that DataAnalysisAgent correctly handles task requests."""
    # Initialize services with default agents
    await initialize_services(use_mock_ham=True)
    
    try:
        services = get_services()
        hsp_connector = services.get("hsp_connector")
        
        # Create a task request payload
        task_payload = {
            "request_id": "test_req_001",
            "capability_id_filter": "data_analysis_v1",
            "parameters": {"csv_content": "name,age\nAlice,30\nBob,25"},
            "callback_address": "hsp/results/test_requester/req_001"
        }
        
        # Mock the send_task_result method to capture the result
        sent_results = []
        original_send_task_result = hsp_connector.send_task_result
        
        async def mock_send_task_result(payload, topic, request_id):
            sent_results.append((payload, topic, request_id))
            return True
        
        hsp_connector.send_task_result = mock_send_task_result
        
        # Get the default agent manager and trigger task handling
        from src.core_ai.default_agents import get_default_agent_manager
        default_manager = get_default_agent_manager()
        
        # Simulate receiving a task request
        envelope = {"message_id": "msg_001", "sender_ai_id": "test_sender"}
        await default_manager._handle_task_request(task_payload, "test_sender", envelope)
        
        # Verify the result was sent
        assert len(sent_results) == 1
        result_payload, result_topic, result_request_id = sent_results[0]
        
        assert result_payload["request_id"] == "test_req_001"
        assert result_payload["status"] == "success"
        assert "Dummy analysis: Summarized 2 lines of CSV data" in result_payload["payload"]
        assert result_topic == "hsp/results/test_requester/req_001"
        
        # Restore original method
        hsp_connector.send_task_result = original_send_task_result
        
    finally:
        await shutdown_services()


if __name__ == "__main__":
    pytest.main([__file__])