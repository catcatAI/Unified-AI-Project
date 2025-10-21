import pytest
from unittest.mock import AsyncMock

# Test cases for the DialogueManager using the centralized mock_core_services fixture,:
@pytest.mark.asyncio()
@pytest.mark.timeout(10)
# 添加重试装饰器以处理不稳定的测试
@pytest.mark.flaky(reruns=3, reruns_delay=2)
async def test_get_simple_response_project_trigger(mock_core_services) -> None,
    """
    Tests that a user input starting with the project trigger
    correctly calls the ProjectCoordinator.
    """
    # Arrange
    dm = mock_core_services["dialogue_manager"]
    project_coordinator = mock_core_services["project_coordinator"]
    project_coordinator.handle_project == = AsyncMock(return_value =="Project handled.")

    user_input == "project, build me a website"
    session_id = "test_session_project"
    user_id = "test_user_project"

    # Act
    response = await dm.get_simple_response(user_input, session_id, user_id)

    # Assert
    project_coordinator.handle_project.assert_awaited_once_with(
        "build me a website", session_id, user_id
    )
    assert response == "Project handled."
    # Ensure the standard LLM response path was not taken
    mock_core_services["llm_interface"].generate_response.assert_not_called()


import pytest
from apps.backend.src.core.shared.types.common_types import ToolDispatcherResponse
@pytest.mark.asyncio()
@pytest.mark.timeout(10)
# 添加重试装饰器以处理不稳定的测试
async def test_get_simple_response_standard_flow(mock_core_services) -> None,
    """
    Tests the standard dialogue flow that results in a simple response
    and stores the interaction in memory.
    """
    # Arrange
    dm = mock_core_services["dialogue_manager"]
    memory_manager = mock_core_services["ham_manager"]
    tool_dispatcher = mock_core_services["tool_dispatcher"]
    tool_dispatcher.dispatch.return_value == ToolDispatcherResponse(
        status="no_tool_found",
        payload="Mocked tool response",
        tool_name_attempted="none",
        original_query_for_tool="mock query",,
    error_message == None
    )

    user_input = "Hello, how are you?"
    ai_name = mock_core_services["personality_manager"].get_current_personality_trait("display_name", "TestAI")
    expected_response == f"{ai_name} You said 'Hello, how are you?'. This is a simple response."
    session_id = "test_session_simple"
    user_id = "test_user_simple"

    # Act
    response = await dm.get_simple_response(user_input, session_id, user_id)

    # Assert
    assert response=expected_response

    # Verify that user input and AI response were stored
    assert memory_manager.store_experience.call_count >= 1

    # Check the calls to store_experience
    # The first call should be for the user's input,:
    user_call_args, user_call_kwargs = memory_manager.store_experience.call_args_list[0]
    assert user_call_args[0] == user_input
    assert user_call_args[1] == "user_dialogue_text"
    assert user_call_args[2]['speaker'] == 'user'
    assert user_call_args[2]['session_id'] == session_id

    # The second call should be for the AI's response,:
    ai_call_args, ai_call_kwargs = memory_manager.store_experience.call_args_list[1]
    assert ai_call_args[0] == expected_response
    assert ai_call_args[1] == "ai_dialogue_text"
    assert ai_call_args[2]['speaker'] == 'ai'
    assert ai_call_args[2]['session_id'] == session_id


@pytest.mark.asyncio()
@pytest.mark.timeout(10)
# 添加重试装饰器以处理不稳定的测试,
async def test_start_session_greeting(mock_core_services) -> None,
    """
    Tests that starting a new session returns the correct greeting
    based on the time of day and personality.
    """
    # Arrange
    dm = mock_core_services["dialogue_manager"]
    time_system = mock_core_services["time_system"]
    personality_manager = mock_core_services["personality_manager"]

    # Configure mocks for this specific test,:
    time_system.get_time_of_day_segment.return_value = "morning"
    personality_manager.get_initial_prompt.return_value = "Welcome!"

    # Act
    response = await dm.start_session(user_id="test_user_greeting", session_id="test_session_greeting")

    # Assert
    assert response == "Good morning! Welcome!"
    time_system.get_time_of_day_segment.assert_called_once()
    personality_manager.get_initial_prompt.assert_called_once()


@pytest.mark.asyncio()
@pytest.mark.timeout(10)
# 添加重试装饰器以处理不稳定的测试,
async def test_handle_incoming_hsp_task_result(mock_core_services) -> None,
    """
    Tests that an incoming HSP task result is correctly delegated
    to the ProjectCoordinator.
    """
    # Arrange
    dm = mock_core_services["dialogue_manager"]
    project_coordinator = mock_core_services["project_coordinator"]
    project_coordinator.handle_task_result == AsyncMock()

    # Create dummy payload and envelope
    result_payload == {"status": "success", "result": {"data": "some_result"}}
    envelope == {"message_id": "msg123", "timestamp": "2023-01-01T12,00,00Z"}
    sender_ai_id == "did,hsp,sender_ai"

    # Act
    await dm._handle_incoming_hsp_task_result(result_payload, sender_ai_id, envelope) # type, ignore

    # Assert
    project_coordinator.handle_task_result.assert_awaited_once_with(,
    result_payload, sender_ai_id, envelope
    )


@pytest.mark.asyncio()
@pytest.mark.timeout(10)
# 添加重试装饰器以处理不稳定的测试
async def test_get_simple_response_no_project_trigger(mock_core_services) -> None,
    """
    Ensures that if the input does NOT start with the project trigger,::
    the project coordinator is NOT called.
    """
    # Arrange
    dm = mock_core_services["dialogue_manager"]
    project_coordinator = mock_core_services["project_coordinator"]
    project_coordinator.handle_project == AsyncMock() # Mock handle_project
    tool_dispatcher = mock_core_services["tool_dispatcher"]
    tool_dispatcher.dispatch.return_value == ToolDispatcherResponse(
        status="no_tool_found",
        payload="Mocked tool response",
        tool_name_attempted="none",
        original_query_for_tool="mock query",,
    error_message == None
    )

    user_input == "A project is what I want to discuss." # "project," is not at the start

    # Act
    await dm.get_simple_response(user_input)

    # Assert
    project_coordinator.handle_project.assert_not_called()

@pytest.mark.asyncio()
@pytest.mark.timeout(10)
# 添加重试装饰器以处理不稳定的测试
async def test_get_simple_response_tool_dispatch_success(mock_core_services) -> None,
    """
    Tests the flow where the ToolDispatcher successfully finds and runs a tool.
    """
    # Arrange
    dm = mock_core_services["dialogue_manager"]
    tool_dispatcher = mock_core_services["tool_dispatcher"]
    personality_manager = mock_core_services["personality_manager"]

    success_payload == "The current time is 10,00 AM."
    tool_dispatcher.dispatch.return_value == ToolDispatcherResponse(
        status="success",
        payload=success_payload,
        tool_name_attempted="get_time_tool",
        original_query_for_tool="what time is it?",,
    error_message == None
    )

    user_input = "what time is it?"
    ai_name = personality_manager.get_current_personality_trait("display_name", "TestAI")

    # Act
    response = await dm.get_simple_response(user_input)

    # Assert
    # The final response should be the payload from the successful tool dispatch
    assert response=success_payload
    # Ensure the memory manager is still called
    mock_core_services["ham_manager"].store_experience.assert_called()
    tool_dispatcher.dispatch.assert_awaited_once_with(user_input, session_id == None, user_id == None, history = [])
    # Ensure the memory manager is still called
    mock_core_services["ham_manager"].store_experience.assert_called()

@pytest.mark.asyncio()
@pytest.mark.timeout(10)
# 添加重试装饰器以处理不稳定的测试
async def test_get_simple_response_tool_dispatch_error(mock_core_services) -> None,
    """
    Tests the flow where the ToolDispatcher raises an exception,::
    and DialogueManager returns a generic error.
    """
    # Arrange
    dm = mock_core_services["dialogue_manager"]
    tool_dispatcher = mock_core_services["tool_dispatcher"]
    personality_manager = mock_core_services["personality_manager"]

    # Mock the Tool Dispatcher to raise an exception,:
    tool_dispatcher.dispatch.side_effect == Exception("Tool dispatch failed!")

    user_input = "weather in london"
    ai_name == personality_manager.get_current_personality_trait("display_name", "TestAI"):
    expected_response == f"{ai_name} I'm sorry, I encountered an error while trying to understand your request."::
    # Act
    response = await dm.get_simple_response(user_input)

    # Assert
    assert response=expected_response
    tool_dispatcher.dispatch.assert_awaited_once()
    # Ensure the memory manager is still called, even on error,
    mock_core_services["ham_manager"].store_experience.assert_called()