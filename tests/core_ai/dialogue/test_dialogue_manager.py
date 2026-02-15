"""
Tests for the DialogueManager, covering various dialogue flows.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# Add project root to path to allow absolute imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from ai.dialogue.dialogue_manager import DialogueManager
from ai.shared.types.common_types import ToolDispatcherResponse

@pytest.fixture
def mock_core_services_fixture():
    """Provides a dictionary of mocked core services for the DialogueManager."""
    return {
        "dialogue_manager": None, # Will be replaced by the actual instance
        "project_coordinator": AsyncMock(),
        "llm_interface": AsyncMock(),
        "ham_manager": MagicMock(),
        "tool_dispatcher": AsyncMock(),
        "personality_manager": MagicMock(),
        "time_system": MagicMock(),
    }

@pytest.fixture
def dialogue_manager_fixture(mock_core_services_fixture):
    """Provides a DialogueManager instance initialized with mocked services."""
    dm = DialogueManager(core_services=mock_core_services_fixture)
    mock_core_services_fixture["dialogue_manager"] = dm
    return dm

@pytest.mark.asyncio
async def test_get_simple_response_project_trigger(dialogue_manager_fixture, mock_core_services_fixture):
    """Test that input with a project trigger correctly calls the ProjectCoordinator."""
    project_coordinator = mock_core_services_fixture["project_coordinator"]
    project_coordinator.handle_project.return_value = "Project handled."

    user_input = "project, build me a website"
    session_id = "test_session_project"
    user_id = "test_user_project"

    response = await dialogue_manager_fixture.get_simple_response(user_input, session_id, user_id)

    project_coordinator.handle_project.assert_awaited_once_with(
        "build me a website", session_id, user_id
    )
    assert response == "Project handled."
    mock_core_services_fixture["llm_interface"].generate_response.assert_not_called()

@pytest.mark.asyncio
async def test_get_simple_response_standard_flow(dialogue_manager_fixture, mock_core_services_fixture):
    """Test the standard dialogue flow without tool or project triggers."""
    tool_dispatcher = mock_core_services_fixture["tool_dispatcher"]
    tool_dispatcher.dispatch.return_value = ToolDispatcherResponse(status="no_tool_found")
    
    personality_manager = mock_core_services_fixture["personality_manager"]
    personality_manager.get_current_personality_trait.return_value = "TestAI"

    llm_interface = mock_core_services_fixture["llm_interface"]
    expected_response = "TestAI: This is a simple response."
    llm_interface.generate_response.return_value = expected_response

    user_input = "Hello, how are you?"
    response = await dialogue_manager_fixture.get_simple_response(user_input)

    assert response == expected_response
    mock_core_services_fixture["ham_manager"].store_experience.assert_called()