import unittest
import sys
import os
# Add the src directory to the path
_ = sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

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

    def test_initialization(self) -> None:
        """Test UnifiedAISystem initialization."""
        # Create system instance
        system = UnifiedAISystem(self.config)
        
        # Verify components were initialized
        _ = self.assertIsInstance(system, UnifiedAISystem)

    def test_start_system(self) -> None:
        """Test starting the system."""
        # Create system instance
        system = UnifiedAISystem(self.config)
        
        # Start the system
        _ = system.start_system()
        
        # If we get here without exception, the test passes

    def test_stop_system(self) -> None:
        """Test stopping the system."""
        # Create system instance
        system = UnifiedAISystem(self.config)
        
        # Stop the system
        _ = system.stop_system()
        
        # If we get here without exception, the test passes

    def test_process_dialogue_request(self) -> None:
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
        _ = self.assertEqual(result["status"], "success")
        _ = self.assertIn("message", result)

if __name__ == '__main__':
    _ = unittest.main()