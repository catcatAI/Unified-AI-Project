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
        llm_interface_mock = self.dialogue_manager.llm_interface
        llm_interface_mock.generate_response.side_effect = [
            # First call is for decomposition
            str(mock_decomposed_plan).replace("'", '"'),
            # Second call is for integration
            mock_integration_response
        ]

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


if __name__ == '__main__':
    unittest.main()
