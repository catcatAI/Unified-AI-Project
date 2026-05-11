"""
测试模块 - test_data_factory
"""

import pytest
from unittest.mock import Mock


class TestDataFactory:
    @pytest.fixture(autouse=True)
    def setup_test(self):
        yield

    def create_agent_config(self, agent_id, agent_type):
        return {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "config": {}
        }

    def create_mock_llm_response(self, content):
        return {"content": content, "role": "assistant"}

    def test_data_factory_basic(self):
        config = self.create_agent_config("test_agent", "test_type")
        assert config["agent_id"] == "test_agent"
        assert config["agent_type"] == "test_type"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])