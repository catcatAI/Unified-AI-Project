import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from system_integration import UnifiedAISystem

class TestUnifiedAISystem(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.config = {
            'agent_manager': {},
            'execution_manager': {},
            'ham_memory': {},
            'learning': {},
            'dialogue': {},
            'llm_service': {},
            'ai_editor': {},
            'virtual_input': {},
            'resource_awareness': {},
            'atlassian': {},
            'rovo_dev': {}
        }

    def test_initialization(self):
        """Test UnifiedAISystem initialization."""
        # Create system instance
        system = UnifiedAISystem(self.config)
        
        # Verify components were initialized
        self.assertIsInstance(system, UnifiedAISystem)

    def test_start_system(self):
        """Test starting the system."""
        # Create system instance
        system = UnifiedAISystem(self.config)
        
        # Start the system
        system.start_system()
        
        # If we get here without exception, the test passes

    def test_stop_system(self):
        """Test stopping the system."""
        # Create system instance
        system = UnifiedAISystem(self.config)
        
        # Stop the system
        system.stop_system()
        
        # If we get here without exception, the test passes

    def test_process_dialogue_request(self):
        """Test processing a dialogue request."""
        # Create system instance
        system = UnifiedAISystem(self.config)
        
        # Process a request
        result = system.process_request("user123", {
            "type": "dialogue",
            "message": "Hello, AI!",
            "context": {}
        })
        
        # Verify the result
        self.assertEqual(result["status"], "success")
        self.assertIn("message", result)

if __name__ == '__main__':
    unittest.main()