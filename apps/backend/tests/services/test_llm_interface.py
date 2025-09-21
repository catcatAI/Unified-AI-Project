import unittest
import pytest
import os
import sys
import asyncio

from services.multi_llm_service import MultiLLMService

class TestLLMInterface(unittest.TestCase):

    @pytest.mark.timeout(15)
    def test_01_initialization(self):
        """Test LLM interface initialization."""
        interface = MultiLLMService()
        self.assertIsNotNone(interface)
        # Check that interface has required attributes
        self.assertTrue(hasattr(interface, 'model_configs'))
        print("TestLLMInterface.test_01_initialization PASSED")

    @pytest.mark.asyncio
    @pytest.mark.timeout(15)
    @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_02_generate_response(self):
        """Test LLM response generation."""
        interface = MultiLLMService()
        response = await interface.generate_response("test prompt")
        # The default mock response is "This is a generic mock response from mock-generic-v1 to the prompt: \"{prompt}\""
        self.assertIn("generic mock response from mock-generic-v1", response)
        self.assertIn("test prompt", response) # This part should still be true
        print("TestLLMInterface.test_02_generate_response PASSED")

    @pytest.mark.asyncio
    @pytest.mark.timeout(15)
    async def test_03_list_models(self):
        """Test listing available models."""
        interface = MultiLLMService()
        models = await interface.list_available_models()
        self.assertIsInstance(models, list)
        if models: # If list is not empty
            # Assuming LLMModelInfo is a dict-like object or has 'id' attribute
            self.assertIn("id", models[0].__dict__ if hasattr(models[0], '__dict__') else models[0]) # Check for expected key in first model dict
        print("TestLLMInterface.test_03_list_models PASSED")

if __name__ == '__main__':
    unittest.main(verbosity=2)