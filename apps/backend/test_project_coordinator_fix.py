import asyncio
import json
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unittest.mock import AsyncMock, MagicMock
from apps.backend.src.core_ai.dialogue.project_coordinator import ProjectCoordinator
from apps.backend.src.hsp.types import HSPCapabilityAdvertisementPayload

async def test_project_coordinator_decomposition():
    """Test the project coordinator's decomposition functionality"""
    print("Testing ProjectCoordinator decomposition...")
    
    # Create mock dependencies
    mock_llm_interface = AsyncMock()
    mock_service_discovery = AsyncMock()
    mock_hsp_connector = MagicMock()
    mock_agent_manager = MagicMock()
    mock_memory_manager = MagicMock()
    mock_learning_manager = AsyncMock()
    mock_personality_manager = MagicMock()
    mock_personality_manager.get_current_personality_trait.return_value = "TestAI"
    
    # Mock config
    mock_config = {
        "turn_timeout_seconds": 30
    }
    
    # Create ProjectCoordinator instance
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
    
    # Test with mock response
    mock_llm_interface.generate_response = AsyncMock(return_value="Mock response (no API key)")
    
    # Test decomposition
    result = await pc._decompose_user_intent_into_subtasks("Test query", [])
    print(f"Decomposition result: {result}")
    print(f"Result type: {type(result)}")
    print(f"Result length: {len(result)}")
    
    # Verify we get the expected mock subtasks
    assert len(result) == 2
    assert result[0]["capability_needed"] == "data_analysis_v1"
    assert result[1]["capability_needed"] == "data_analysis_v1"
    
    print("Test passed!")
    
    # Test with valid JSON response
    mock_llm_interface.generate_response = AsyncMock(return_value='[{"capability_needed": "test_v1"}]')
    result2 = await pc._decompose_user_intent_into_subtasks("Test query", [])
    print(f"JSON decomposition result: {result2}")
    assert len(result2) == 1
    assert result2[0]["capability_needed"] == "test_v1"
    
    print("JSON test passed!")

if __name__ == "__main__":
    asyncio.run(test_project_coordinator_decomposition())