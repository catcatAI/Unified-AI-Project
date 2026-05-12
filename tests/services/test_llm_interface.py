"""
测试模块 - test_llm_interface

自动生成的测试模块,用于验证系统功能。
"""

import unittest
import pytest

from core.services.multi_llm_service import MultiLLMService


class TestLLMInterface(unittest.TestCase):
    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}

    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()

    def test_01_initialization(self) -> None:
        """Test LLM interface initialization."""
        interface = MultiLLMService()
        self.assertIsNotNone(interface)
        self.assertTrue(hasattr(interface, 'model_configs'))
        print("TestLLMInterface.test_01_initialization PASSED")

    @pytest.mark.asyncio()
    @pytest.mark.timeout(15)
    async def test_02_generate_response(self) -> None:
        """Test LLM response generation."""
        interface = MultiLLMService()
        response = await interface.generate_response("test prompt")
        self.assertIn("generic mock response from mock-generic-v1", response)
        self.assertIn("test prompt", response)
        print("TestLLMInterface.test_02_generate_response PASSED")

    @pytest.mark.asyncio()
    @pytest.mark.timeout(15)
    async def test_03_list_models(self) -> None:
        """Test listing available models."""
        interface = MultiLLMService()
        models = await interface.list_available_models()
        self.assertIsInstance(models, list)
        if models:
            first_model = models[0]
            if hasattr(first_model, '__dict__'):
                self.assertIn('id', first_model.__dict__)
            elif isinstance(first_model, dict):
                self.assertIn('id', first_model)
        print("TestLLMInterface.test_03_list_models PASSED")


if __name__ == "__main__":
    unittest.main(verbosity=2)