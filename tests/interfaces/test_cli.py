import unittest
import pytest
import os
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

from src.interfaces.cli import main as cli_main

class TestCLI(unittest.TestCase):

    @pytest.mark.timeout(5)
    def test_01_cli_no_args(self):
        """Test CLI response when no arguments are provided."""
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with patch('sys.argv', ['main.py']): # Simulate calling script with no arguments
                with patch('asyncio.run') as mock_run:
                    cli_main.main_cli_logic()

    @patch('src.interfaces.cli.main.initialize_services')
    @patch('src.interfaces.cli.main.get_services')
    @patch('src.interfaces.cli.main.shutdown_services')
    @patch('asyncio.run')
    @pytest.mark.timeout(5)
    def test_02_cli_query_with_emotion(self, mock_async_run, mock_shutdown, mock_get, mock_init):
        """Test the 'query' command with LLM and Emotion integration."""
        mock_dm = MagicMock()
        mock_get.return_value = {"dialogue_manager": mock_dm}
        ai_name = "Miko (Base)"
        llm_model_name = "generic-llm-placeholder"

        test_cases = [
            {"input": "This is a neutral statement.", "dm_response": f"{ai_name}: Hello! I am {ai_name}. How can I help you today?", "expected_substring": "How can I help you today?"},
            {"input": "I am so sad today.", "dm_response": f"{ai_name}: Placeholder response from {llm_model_name} for: I am so sad today. (gently)", "expected_substring": "(gently)"},
            {"input": "This is great and I am happy!", "dm_response": f"{ai_name}: Placeholder response from {llm_model_name} for: This is great and I am happy! (playfully) ✨", "expected_substring": "(playfully) ✨"},
        ]

        for case in test_cases:
            # The mock_dm.get_simple_response is now what's being awaited inside the new async wrapper
            mock_async_run.return_value = case["dm_response"]

            with patch('sys.argv', ['main.py', 'query', case["input"]]):
                captured_output = StringIO()
                with patch('sys.stdout', new=captured_output):
                    cli_main.main_cli_logic()
                output = captured_output.getvalue()
                self.assertIn(case["expected_substring"], output)

    @patch('src.interfaces.cli.main.initialize_services')
    @patch('src.interfaces.cli.main.get_services')
    @patch('src.interfaces.cli.main.shutdown_services')
    @patch('asyncio.run')
    @pytest.mark.timeout(5)
    def test_05_cli_query_crisis_response(self, mock_async_run, mock_shutdown, mock_get, mock_init):
        """Test the 'query' command for crisis response."""
        mock_dm = MagicMock()
        mock_get.return_value = {"dialogue_manager": mock_dm}

        test_query_crisis = "Help, this is an emergency!"
        ai_name = "Miko (Base)"
        expected_crisis_output = f"AI: {ai_name}: I sense this is a sensitive situation. If you need help, please reach out to appropriate support channels."
        expected_substring = "appropriate support channels"

        # Mock the return value of asyncio.run which wraps the DM call
        mock_async_run.return_value = expected_crisis_output

        with patch('sys.argv', ['main.py', 'query', test_query_crisis]):
            captured_output = StringIO()
            with patch('sys.stdout', new=captured_output):
                cli_main.main_cli_logic()
            output = captured_output.getvalue()
            self.assertIn(expected_substring, output)


if __name__ == '__main__':
    unittest.main(verbosity=2)
