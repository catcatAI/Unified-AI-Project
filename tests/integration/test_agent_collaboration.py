import unittest
import pytest
import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core_services import initialize_services, get_services, shutdown_services
from src.core_ai.dialogue.dialogue_manager import DialogueManager

class TestAgentCollaboration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize services once for all tests in this class."""
        # We use mock services to avoid real network/LLM calls
        initialize_services(use_mock_ham=True, llm_config={"default_provider": "mock"})
        cls.services = get_services()
        cls.dialogue_manager = cls.services.get("dialogue_manager")

    @classmethod
    def tearDownClass(cls):
        """Shutdown services after all tests."""
        shutdown_services()

    @pytest.mark.timeout(10)
    def test_handle_complex_project_with_dag(self):
        """
        End-to-end test for a complex project involving a DAG of tasks.
        """
        # 1. Mock the LLM's decomposition response to produce a plan with dependencies
        mock_decomposed_plan = [
            {
                "capability_needed": "analyze_csv_data",
                "task_parameters": { "query": "summarize", "csv_content": "header1,header2\nval1,val2" },
                "task_description": "First, get a statistical summary of the provided data."
            },
            {
                "capability_needed": "generate_marketing_copy",
                "task_parameters": { "product_description": "<output_of_task_0>", "target_audience": "data scientists" },
                "task_description": "Then, write marketing copy based on the data summary."
            }
        ]

        # 2. Mock the LLM's integration response
        mock_integration_response = "Based on the data summary, our new product is revolutionary for data scientists."

        # We need to patch the llm_interface used by the dialogue_manager
        with patch('src.services.multi_llm_service.MultiLLMService.generate_response', new_callable=AsyncMock) as mock_generate_response:
            mock_generate_response.side_effect = [
                str(mock_decomposed_plan).replace("'", '"'),
                mock_integration_response
            ]
            # The rest of the test logic that uses self.dialogue_manager.llm_interface
            # will now use the patched mock_generate_response.
            final_response = asyncio.run(self.dialogue_manager.get_simple_response(user_query))

        # Check that the LLM was called twice (decomposition and integration)
        self.assertEqual(mock_generate_response.call_count, 2)

        # Check the integration prompt
        integration_call_args = mock_generate_response.call_args_list[1]
        self.assertIn("User's Original Request", integration_call_args.kwargs['prompt'])
        self.assertIn("Collected Results from Sub-Agents", integration_call_args.kwargs['prompt'])
        self.assertIn("CSV has 2 columns", integration_call_args.kwargs['prompt'])

        # 5. Assertions
        # Check that the final response contains the integrated text
        self.assertIn("Based on the data summary", final_response)
        self.assertIn("revolutionary for data scientists", final_response)

        # Remove the original assertions that are now part of the patch block
        # self.assertEqual(llm_interface_mock.generate_response.call_count, 2)
        # integration_call_args = llm_interface_mock.generate_response.call_args_list[1]
        # self.assertIn("User's Original Request", integration_call_args.kwargs['prompt'])
        # self.assertIn("Collected Results from Sub-Agents", integration_call_args.kwargs['prompt'])
        # self.assertIn("CSV has 2 columns", integration_call_args.kwargs['prompt'])

        # 3. Mock the sub-agent responses (via _dispatch_single_subtask)
        # This is tricky as it's an internal async method. We can patch it.
        async def mock_dispatch_subtask(subtask):
            if subtask['capability_needed'] == 'analyze_csv_data':
                return {"summary": "CSV has 2 columns and 1 row of data."}
            elif subtask['capability_needed'] == 'generate_marketing_copy':
                # Check if the placeholder was replaced
                self.assertIn("CSV has 2 columns", subtask['task_parameters']['product_description'])
                return "Our new product, which has 2 columns and 1 row, is amazing for data scientists!"
            return {"error": "Unknown capability in mock"}

        patcher_dispatch = patch.object(self.dialogue_manager, '_dispatch_single_subtask', new=AsyncMock(side_effect=mock_dispatch_subtask))

        # 4. Run the complex project handler
        user_query = "project: Analyze this CSV and write marketing copy."

        with patcher_dispatch:
            final_response = asyncio.run(self.dialogue_manager.get_simple_response(user_query))

        # 5. Assertions
        # Check that the final response contains the integrated text
        self.assertIn("Based on the data summary", final_response)
        self.assertIn("revolutionary for data scientists", final_response)

        # Check that the LLM was called twice (decomposition and integration)
        self.assertEqual(llm_interface_mock.generate_response.call_count, 2)

        # Check the integration prompt
        integration_call_args = llm_interface_mock.generate_response.call_args_list[1]
        self.assertIn("User's Original Request", integration_call_args.kwargs['prompt'])
        self.assertIn("Collected Results from Sub-Agents", integration_call_args.kwargs['prompt'])
        self.assertIn("CSV has 2 columns", integration_call_args.kwargs['prompt'])

    @pytest.mark.timeout(10)
    def test_handle_project_no_dependencies(self):
        """
        Tests a project with two independent tasks.
        """
        # 1. Mock the LLM's decomposition response
        mock_decomposed_plan = [
            {"capability_needed": "task_a_v1", "task_parameters": {"p": 1}},
            {"capability_needed": "task_b_v1", "task_parameters": {"q": 2}},
        ]
        # 2. Mock the LLM's integration response
        mock_integration_response = "Both tasks completed."

        with patch('src.services.multi_llm_service.MultiLLMService.generate_response', new_callable=AsyncMock) as mock_generate_response:
            mock_generate_response.side_effect = [
                str(mock_decomposed_plan).replace("'", '"'),
                mock_integration_response
            ]

            # 3. Mock the sub-agent responses
            async def mock_dispatch_subtask(subtask):
                if subtask['capability_needed'] == 'task_a_v1':
                    return {"result_a": "A"}
                elif subtask['capability_needed'] == 'task_b_v1':
                    return {"result_b": "B"}
                return {}

            patcher_dispatch = patch.object(self.dialogue_manager.project_coordinator, '_dispatch_single_subtask', new=AsyncMock(side_effect=mock_dispatch_subtask))

            # 4. Run the project
            with patcher_dispatch:
                final_response = asyncio.run(self.dialogue_manager.get_simple_response("project: two tasks"))

            # 5. Assertions
            self.assertIn("Both tasks completed", final_response)
            self.assertEqual(mock_generate_response.call_count, 2)

    @pytest.mark.timeout(10)
    def test_handle_project_failing_subtask(self):
        """
        Tests how the system handles a failing subtask.
        """
        # 1. Mock the LLM's decomposition
        mock_decomposed_plan = [{"capability_needed": "failing_task_v1"}]
        # 2. Mock the LLM's integration
        mock_integration_response = "The project failed."

        with patch('src.services.multi_llm_service.MultiLLMService.generate_response', new_callable=AsyncMock) as mock_generate_response:
            mock_generate_response.side_effect = [
                str(mock_decomposed_plan).replace("'", '"'),
                mock_integration_response
            ]

            # 3. Mock a failing sub-agent
            patcher_dispatch = patch.object(self.dialogue_manager.project_coordinator, '_dispatch_single_subtask', new=AsyncMock(return_value={"error": "Task failed"}))

            # 4. Run the project
            with patcher_dispatch:
                final_response = asyncio.run(self.dialogue_manager.get_simple_response("project: failing task"))

            # 5. Assertions
            self.assertIn("The project failed", final_response)
            # Check that the integration prompt contains the error
            integration_call_args = mock_generate_response.call_args_list[1]
            self.assertIn("failing_task_v1", integration_call_args.kwargs['prompt'])
            self.assertIn("Task failed", integration_call_args.kwargs['prompt'])

    @pytest.mark.timeout(15)
    def test_handle_project_dynamic_agent_launch(self):
        """
        Tests that the system can dynamically launch an agent if a capability is not found.
        """
        # 1. Mock the LLM's decomposition
        mock_decomposed_plan = [{"capability_needed": "new_agent_v1"}]
        # 2. Mock the LLM's integration
        mock_integration_response = "Dynamically launched agent and it worked."

        with patch('src.services.multi_llm_service.MultiLLMService.generate_response', new_callable=AsyncMock) as mock_generate_response:
            mock_generate_response.side_effect = [
                str(mock_decomposed_plan).replace("'", '"'),
                mock_integration_response
            ]

            # 3. Mock service discovery to initially find nothing, then find the capability
            service_discovery_mock = self.dialogue_manager.project_coordinator.service_discovery
            service_discovery_mock.find_capabilities.side_effect = [
                [], # First call finds nothing
                [{"capability_id": "new_agent_v1_cap", "ai_id": "did:hsp:new_agent"}] # Second call finds it
            ]

            # 4. Mock the agent manager
            agent_manager_mock = self.dialogue_manager.project_coordinator.agent_manager
            agent_manager_mock.launch_agent.return_value = "pid_123"
            agent_manager_mock.wait_for_agent_ready = AsyncMock()

            # 5. Mock the dispatch
            patcher_dispatch = patch.object(self.dialogue_manager.project_coordinator, '_dispatch_single_subtask', new=AsyncMock(return_value={"result": "ok"}))


            # 6. Run the project
            with patcher_dispatch:
                final_response = asyncio.run(self.dialogue_manager.get_simple_response("project: new agent"))

            # 7. Assertions
            self.assertIn("Dynamically launched agent", final_response)
            agent_manager_mock.launch_agent.assert_called_once_with("new_agent_agent")
            agent_manager_mock.wait_for_agent_ready.assert_awaited_once_with("new_agent_agent")


if __name__ == '__main__':
    unittest.main()
