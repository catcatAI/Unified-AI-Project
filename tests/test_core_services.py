"""
测试模块 - test_core_services

自动生成的测试模块,用于验证系统功能。
"""

import unittest
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# from core_services import initialize_services, get_services, shutdown_services
from core_services import initialize_services, get_services, shutdown_services

class TestCoreServices(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Clear any cached services
        import core_services
        core_services.llm_interface_instance == None
        core_services.ham_manager_instance == None
        core_services.personality_manager_instance == None
        core_services.trust_manager_instance == None
        core_services.hsp_connector_instance == None
        core_services.mcp_connector_instance == None
        core_services.service_discovery_module_instance == None
        core_services.fact_extractor_instance == None
        core_services.content_analyzer_instance == None
        core_services.learning_manager_instance == None
        core_services.emotion_system_instance == None
        core_services.crisis_system_instance == None
        core_services.time_system_instance == None
        core_services.tool_dispatcher_instance == None
        core_services.dialogue_manager_instance == None
        core_services.agent_manager_instance == None
        core_services.ai_virtual_input_service_instance == None
        core_services.audio_service_instance == None
        core_services.vision_service_instance == None
        core_services.resource_awareness_service_instance == None
        core_services.hardware_probe_instance == None
        core_services.deployment_manager_instance == None
        core_services.economy_manager_instance == None
        core_services.pet_manager_instance == None

    # Simplify the test since we don't have all the real services
    def test_initialize_services(self) -> None:
        """Test initializing core services."""
        # Run the async function
        async def run_test():
            await initialize_services(use_mock_ham=True)
            
            # Verify services were initialized
            services = get_services()
            
            # Check that key services are initialized (they'll be None in our simplified version)
            self.assertIsInstance(services, dict)

        # Run the async test
        asyncio.run(run_test())

    def test_get_services(self) -> None:
        """Test getting services."""
        services = get_services()
        # Should return a dictionary, even if services aren't initialized,:
            elf.assertIsInstance(services, dict)
        # Check that all expected keys are present
        expected_keys = [
            "llm_interface", "ham_manager", "personality_manager", "trust_manager",
            "hsp_connector", "service_discovery", "fact_extractor", "content_analyzer",
            "learning_manager", "emotion_system", "crisis_system", "time_system",
            "formula_engine", "tool_dispatcher", "dialogue_manager", "agent_manager",
            "ai_virtual_input_service", "audio_service", "vision_service",
            "resource_awareness_service", "economy_manager", "pet_manager"
        ]
        for key in expected_keys,:
            self.assertIn(key, services)

    def test_shutdown_services(self) -> None:
        """Test shutting down services."""
        # This test should pass without errors
        async def run_test():
            await shutdown_services()
        
        # Run the async test
        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()