import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
import asyncio
import json
import os

from src.core_ai.dialogue.project_coordinator import ProjectCoordinator

@pytest.fixture
def project_coordinator():
    """Provides a ProjectCoordinator instance with mocked dependencies."""
    mock_llm_interface = AsyncMock()
    mock_service_discovery = MagicMock()
    mock_hsp_connector = MagicMock()
    mock_agent_manager = MagicMock()
    mock_memory_manager = MagicMock()
    mock_learning_manager = AsyncMock()
    mock_personality_manager = MagicMock()
    mock_personality_manager.get_current_personality_trait.return_value = "TestAI"

    # Mock the config dictionary
    mock_config = {
        "turn_timeout_seconds": 30
    }

    pc = ProjectCoordinator(
        llm_interface=mock_llm_interface,
        service_discovery=mock_service_discovery,
        hsp_connector=mock_hsp_connector,
        agent_manager=mock_agent_manager,
        memory_manager=mock_memory_manager,
        learning_manager=mock_learning_manager,
        personality_manager=mock_personality_manager,
        dialogue_manager_config=mock_config
    )
    return pc

@pytest.mark.asyncio
async def test_handle_project_happy_path(project_coordinator):
    """
    Tests the full, successful execution of a project from query to final response.
    This replaces the previous, overly mocked test.
    """
    # Arrange
    pc = project_coordinator
    user_query = "Build a website for me."
    decomposed_tasks = [
        {"capability_needed": "create_files_v1", "task_parameters": {"files": ["index.html"]}, "task_description": "Create a homepage."}
    ]
    execution_results = {0: {"status": "success", "result": "index.html created."}}
    final_integrated_response = "I have successfully created the index.html file for your website."

    # Mock the three main phases of the project
    pc._decompose_user_intent_into_subtasks = AsyncMock(return_value=decomposed_tasks)
    pc._execute_task_graph = AsyncMock(return_value=execution_results)
    pc._integrate_subtask_results = AsyncMock(return_value=final_integrated_response)

    # Act
    response = await pc.handle_project(user_query, "session123", "user456")

    # Assert
    pc._decompose_user_intent_into_subtasks.assert_awaited_once_with(user_query, pc.service_discovery.get_all_capabilities())
    pc._execute_task_graph.assert_awaited_once_with(decomposed_tasks)
    pc._integrate_subtask_results.assert_awaited_once_with(user_query, execution_results)

    # Verify learning manager was called
    pc.learning_manager.learn_from_project_case.assert_awaited_once()

    # Verify the final response is correctly formatted
    expected_response = f"TestAI: Here's the result of your project request:\n\n{final_integrated_response}"
    assert response == expected_response

@pytest.mark.asyncio
async def test_handle_project_decomposition_fails(project_coordinator):
    """
    Tests that if task decomposition fails, a user-friendly message is returned.
    """
    # Arrange
    pc = project_coordinator
    pc._decompose_user_intent_into_subtasks = AsyncMock(return_value=[]) # Simulate LLM failing to decompose

    # Patch the methods to check they were not called
    with patch.object(pc, '_execute_task_graph', new_callable=AsyncMock) as mock_execute:
        with patch.object(pc, '_integrate_subtask_results', new_callable=AsyncMock) as mock_integrate:
            # Act
            response = await pc.handle_project("An impossible task.", "s1", "u1")

            # Assert
            assert response == "TestAI: I couldn't break down your request into a clear plan."
            mock_execute.assert_not_called()
            mock_integrate.assert_not_called()

@pytest.mark.asyncio
async def test_execute_task_graph_with_dependencies(project_coordinator):
    """
    Tests that _execute_task_graph correctly handles dependencies between tasks.
    """
    # Arrange
    pc = project_coordinator
    # Mock the actual dispatching logic
    pc._dispatch_single_subtask = AsyncMock(side_effect=[
        {"result": "Task 0 was successful"},
        {"result": "Task 1 was successful"}
    ])

    subtasks = [
        {"capability_needed": "task0_v1", "task_parameters": {"param": "A"}},
        {"capability_needed": "task1_v1", "task_parameters": {"input_data": "Some static data and <output_of_task_0>"}}
    ]

    # Act
    results = await pc._execute_task_graph(subtasks)

    # Assert
    assert len(results) == 2
    assert results[0] == {"result": "Task 0 was successful"}
    assert results[1] == {"result": "Task 1 was successful"}

    # Verify that the substitution happened correctly before dispatching the second task
    expected_call_for_task1 = call({
        'capability_needed': 'task1_v1',
        'task_parameters': {'input_data': 'Some static data and {"result": "Task 0 was successful"}'}
    })
    pc._dispatch_single_subtask.assert_has_calls([
        call(subtasks[0]),
        expected_call_for_task1
    ])

@pytest.mark.asyncio
async def test_dispatch_single_subtask_agent_not_found(project_coordinator):
    """
    Tests that if an agent cannot be found or launched, an error is returned.
    """
    # Arrange
    pc = project_coordinator
    pc.service_discovery.find_capabilities.return_value = [] # No agent available
    pc.agent_manager.launch_agent.return_value = None # Launching fails

    subtask = {"capability_needed": "non_existent_capability_v1"}

    # Act
    result = await pc._dispatch_single_subtask(subtask)

    # Assert
    assert result == {"error": "Could not find or launch an agent with capability 'non_existent_capability_v1'."}

@pytest.mark.asyncio
async def test_dispatch_single_subtask_agent_launch_and_discovery(project_coordinator):
    """
    Tests the logic for launching a new agent when a capability is not initially found.
    """
    # Arrange
    pc = project_coordinator
    capability_name = "needed_capability_v1"
    agent_name_to_launch = "needed_capability_agent"
    subtask = {"capability_needed": capability_name, "task_parameters": {}}

    # Mock the return value for the launched agent's capability
    new_capability_payload = {
        "capability_id": "cap_123",
        "ai_id": "agent_xyz",
        # ... other fields
    }

    # Simulate finding no capabilities initially, then finding one after launch
    pc.service_discovery.find_capabilities.side_effect = [
        [], # First call: not found
        [new_capability_payload] # Second call: found
    ]

    # Mock a successful agent launch that returns a future
    mock_future = asyncio.Future()
    mock_future.set_result(True) # Simulate the agent becoming ready
    pc.agent_manager.launch_agent.return_value = mock_future

    # Mock the downstream HSP request and result waiting
    pc._send_hsp_request = AsyncMock(return_value=("Request sent.", "corr_123"))
    pc._wait_for_task_result = AsyncMock(return_value={"status": "success"})

    # Act
    result = await pc._dispatch_single_subtask(subtask)

    # Assert
    # Verify agent manager was called to launch the correct agent
    pc.agent_manager.launch_agent.assert_called_once_with(agent_name_to_launch)

@pytest.mark.asyncio
async def test_wait_for_task_result_timeout(project_coordinator):
    """
    Tests that _wait_for_task_result correctly returns an error on timeout.
    """
    # Arrange
    pc = project_coordinator
    pc.turn_timeout_seconds = 0.01 # Set a very short timeout for the test

    # Act
    result = await pc._wait_for_task_result("corr_timeout", "timeout_capability")

    # Assert
    assert result == {"error": "Task for 'timeout_capability' timed out."}

# --- Lightweight Instantiated Test ---

@pytest.fixture
def instantiated_pc_fixture():
    """
    Provides a ProjectCoordinator with some real child components
    for lightweight integration testing.
    """
    from src.core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule
    from src.core_ai.trust_manager.trust_manager_module import TrustManager
    from src.core_ai.agent_manager import AgentManager
    import sys

    # Real Components
    trust_manager = TrustManager()
    service_discovery = ServiceDiscoveryModule(trust_manager=trust_manager)
    agent_manager = AgentManager(python_executable=sys.executable)

    # Mocked Components
    mock_llm = AsyncMock()
    mock_hsp = MagicMock()
    mock_ham = MagicMock()
    mock_learning = AsyncMock()
    mock_personality = MagicMock()
    mock_personality.get_current_personality_trait.return_value = "TestAI_Instantiated"

    pc = ProjectCoordinator(
        llm_interface=mock_llm,
        service_discovery=service_discovery,
        hsp_connector=mock_hsp,
        agent_manager=agent_manager,
        memory_manager=mock_ham,
        learning_manager=mock_learning,
        personality_manager=mock_personality,
        dialogue_manager_config={}
    )

    return pc, service_discovery, agent_manager

@pytest.mark.asyncio
async def test_dispatch_launches_and_discovers_with_real_components(instantiated_pc_fixture):
    """
    A lightweight integration test to verify the interaction between a real
    ProjectCoordinator, ServiceDiscoveryModule, and AgentManager.
    """
    # Arrange
    pc, sdm, am = instantiated_pc_fixture
    capability_name = "new_capability_v1"
    agent_name = "new_capability_agent"
    subtask = {"capability_needed": capability_name, "task_parameters": {}}

    # Manually add the agent to the agent manager's script map for this test
    am.agent_script_map[agent_name] = os.path.join(os.path.dirname(__file__), "..", "agents", "data_analysis_agent.py")

    # Mock the subprocess creation to avoid real processes
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value.pid = 12345

        # Mock the HSP parts since we are not testing the broker here
        pc._send_hsp_request = AsyncMock(return_value=("Request sent.", "corr_real_123"))
        pc._wait_for_task_result = AsyncMock(return_value={"status": "success from real components"})

        # --- Act ---
        # 1. First dispatch fails, triggering agent launch
        # To simulate this properly, we need to bypass the full handle_project
        # and call the dispatch method directly.

        # We need to manually simulate the agent advertising its capability after launch
        async def delayed_advertisement():
            await asyncio.sleep(0.1) # Simulate time for agent to "start"
            from src.hsp.types import HSPCapabilityAdvertisementPayload
            cap_payload = HSPCapabilityAdvertisementPayload(
                capability_id=capability_name,
                ai_id="launched_agent_id",
                name="New Capability",
                description="A dynamically launched capability.",
                version="1.0",
                availability_status="online",
            )
            sdm.process_capability_advertisement(cap_payload, "launched_agent_id", MagicMock())

        # Run the advertisement in the background
        advertisement_task = asyncio.create_task(delayed_advertisement())

        # Call the dispatch method
        result = await pc._dispatch_single_subtask(subtask)

        # --- Assert ---
        # Verify that launch_agent was called on the real AgentManager
        mock_popen.assert_called_once()

        # Verify that the capability is now in the real ServiceDiscoveryModule
        assert sdm.is_capability_available(capability_name) is True

        # Verify the final result
        assert result == {"status": "success from real components"}

        await advertisement_task # Ensure the background task completes
