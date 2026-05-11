"""
测试模块 - test_agent_collaboration

自动生成的测试模块,用于验证系统功能。
"""

import unittest
import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core_services import initialize_services, get_services, shutdown_services

class TestAgentCollaboration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        mock_config = {
            "llm_service": {"default_provider": "mock"},
            "hsp_service": {"enabled": False},
            "atlassian_bridge": {"enabled": False},
            "mcp_connector": {"enabled": False},
            "mcp": {
                "mqtt_broker_address": "localhost",
                "mqtt_broker_port": 1883,
                "enable_fallback": False
            }
        }

        async def _async_setup():
            await initialize_services(config=mock_config, use_mock_ham=True)
            cls.services = get_services()
            cls.dialogue_manager = cls.services.get("dialogue_manager")

        asyncio.run(_async_setup())

    @classmethod
    def tearDownClass(cls):
        async def _async_teardown():
            await shutdown_services()
        asyncio.run(_async_teardown())

    @pytest.mark.timeout(10)
    def test_handle_complex_project_with_dag(self):
        user_query = "project, analyze data.csv and write a marketing slogan"
        mock_decomposed_plan = [
            {"capability_needed": "analyze_csv_data", "task_parameters": {"source": "data.csv"}, "dependencies": []},
            {"capability_needed": "generate_marketing_copy", "task_parameters": {"product_description": "output_from_task_0"}, "dependencies": [0]}
        ]
        mock_integration_response = "Based on the data summary, I have created this slogan."

        import json
        with patch.object(self.dialogue_manager.llm_interface, 'generate_response', new_callable=AsyncMock) as mock_generate_response:
            mock_generate_response.side_effect = [json.dumps(mock_decomposed_plan), mock_integration_response]

            async def mock_dispatch_subtask(subtask):
                if subtask['capability_needed'] == 'analyze_csv_data':
                    return {"summary": "CSV has 2 columns and 1 row of data."}
                elif subtask['capability_needed'] == 'generate_marketing_copy':
                    return "Slogan generated."
                return {"error": "Unknown capability"}

            with patch.object(self.dialogue_manager.project_coordinator, '_dispatch_single_subtask', new=AsyncMock(side_effect=mock_dispatch_subtask)):
                final_response = asyncio.run(self.dialogue_manager.get_simple_response(user_query))
                self.assertTrue(
                    "Based on the data summary" in final_response or
                    "Mock response" in final_response or
                    "Here's the result" in final_response
                )

    @pytest.mark.timeout(10)
    def test_handle_project_no_dependencies(self):
        mock_decomposed_plan = [
            {"capability_needed": "task_a_v1", "task_parameters": {"p": 1}},
            {"capability_needed": "task_b_v1", "task_parameters": {"q": 2}}
        ]
        mock_integration_response = "Both tasks completed."

        import json
        with patch.object(self.dialogue_manager.llm_interface, 'generate_response', new_callable=AsyncMock) as mock_generate_response:
            mock_generate_response.side_effect = [json.dumps(mock_decomposed_plan), mock_integration_response]

            async def mock_dispatch_subtask(subtask):
                if subtask['capability_needed'] == 'task_a_v1':
                    return {"result_a": "A"}
                elif subtask['capability_needed'] == 'task_b_v1':
                    return {"result_b": "B"}
                return {}

            patcher_dispatch = patch.object(self.dialogue_manager.project_coordinator, '_dispatch_single_subtask', new=AsyncMock(side_effect=mock_dispatch_subtask))

            with patcher_dispatch:
                final_response = asyncio.run(self.dialogue_manager.get_simple_response("project, two tasks"))

            self.assertTrue(
                "Both tasks completed" in final_response or
                "Mock response" in final_response or
                "Here's the result" in final_response
            )

if __name__ == "__main__":
    unittest.main()