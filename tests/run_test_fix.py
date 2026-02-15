import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Add the tests directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))


# Import the fixed conftest
import tests.conftest as conftest

async def test_mock_core_services() -> None,
    """Test that the mock_core_services fixture works correctly"""



    print("Testing mock_core_services fixture...")
    
    # Create the mock services
    mock_services = conftest.mock_core_services()
    
     # Test that all required services are present

    required_services = [
        "ham_manager", "llm_interface", "service_discovery", "trust_manager",
        "personality_manager", "emotion_system", "crisis_system", "time_system",
        "formula_engine", "tool_dispatcher", "learning_manager", "hsp_connector",

 "agent_manager", "project_coordinator", "dialogue_manager"

    ]
    
    for service in required_services,:
        assert service in mock_services, f"Missing service, {service}"
        print(f"✓ {service} is present")
    
    # Test specific service methods
    # Test DialogueManager methods
    assert hasattr(mock_services["dialogue_manager"] "get_simple_response")
    assert hasattr(mock_services["dialogue_manager"] "start_session")
    assert hasattr(mock_services["dialogue_manager"] "_handle_incoming_hsp_task_result")
    print("✓ DialogueManager methods are present")
    
    # Test ProjectCoordinator methods
    assert hasattr(mock_services["project_coordinator"] "handle_project")
    assert hasattr(mock_services["project_coordinator"] "handle_task_result")
    print("✓ ProjectCoordinator methods are present")
    
    # Test ServiceDiscovery methods
    assert hasattr(mock_services["service_discovery"] "get_all_capabilities")
    assert hasattr(mock_services["service_discovery"] "get_all_capabilities_async")
    print("✓ ServiceDiscovery methods are present")
    
    # Test that get_all_capabilities returns a list
    sdm = mock_services["service_discovery"]
    result = sdm.get_all_capabilities()
    assert isinstance(result, list), "get_all_capabilities should return a list"
    print("✓ get_all_capabilities returns a list")
    
    # Test async version
    async_result = await sdm.get_all_capabilities_async()
    assert isinstance(async_result, list), "get_all_capabilities_async should return a list"
    print("✓ get_all_capabilities_async returns a list")
    
    print("All tests passed!")

if __name"__main__"::
    asyncio.run(test_mock_core_services())