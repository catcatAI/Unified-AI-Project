import unittest
import os
import sys

# Add src directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..")) # Unified-AI-Project/
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from services.llm_interface import LLMInterface

class TestLLMInterface(unittest.TestCase):

    def test_01_initialization_placeholder(self):
        interface = LLMInterface()
        self.assertIsNotNone(interface)
        print("TestLLMInterface.test_01_initialization_placeholder PASSED")

    def test_02_generate_response_placeholder(self):
        interface = LLMInterface()
        response = interface.generate_response("test prompt")
        self.assertIn("Placeholder response", response)
        self.assertIn("test prompt", response)
        print("TestLLMInterface.test_02_generate_response_placeholder PASSED")

    def test_03_list_models_placeholder(self):
        interface = LLMInterface()
        models = interface.list_available_models()
        self.assertIsInstance(models, list)
        if models: # If list is not empty
            self.assertIn("id", models[0]) # Check for expected key in first model dict
        print("TestLLMInterface.test_03_list_models_placeholder PASSED")

if __name__ == '__main__':
    unittest.main(verbosity=2)
