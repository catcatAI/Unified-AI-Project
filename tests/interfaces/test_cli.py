import unittest
import os
import sys
from io import StringIO
from unittest.mock import patch

# Add src directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..")) # Unified-AI-Project/
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Assuming main.py is in src.interfaces.cli
from interfaces.cli import main as cli_main

class TestCLI(unittest.TestCase):

    def test_01_cli_no_args(self):
        """Test CLI response when no arguments are provided."""
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with patch('sys.argv', ['main.py']): # Simulate calling script with no arguments
                with self.assertRaises(SystemExit) as cm:
                    cli_main.main()
                self.assertEqual(cm.exception.code, 1)
            # stderr check is a bit tricky due to argparse's own help message.
            # We are checking our custom message and the exit code primarily.
            self.assertIn("No command provided. Try 'query \"Your question\"' or 'config get some_key'.", mock_stderr.getvalue())
        print("TestCLI.test_01_cli_no_args PASSED")


    def test_02_cli_query_with_emotion(self):
        """Test the 'query' command with LLM and Emotion integration."""
        ai_name = "Miko (Base)" # From miko_base.json
        llm_model_name = "generic-llm-placeholder" # From LLMInterface placeholder

        test_cases = [
            {
                "input": "This is a neutral statement.",
                "emotion_suffix": "", # Neutral
                "expected_emotion_in_dm": "neutral" # Default personality tone
            },
            {
                "input": "I am so sad today.",
                "emotion_suffix": " (gently)", # Empathetic
                "expected_emotion_in_dm": "empathetic"
            },
            {
                "input": "This is great and I am happy!",
                "emotion_suffix": " (playfully) ✨", # Playful
                "expected_emotion_in_dm": "playful"
            }
        ]

        for case in test_cases:
            test_query = case["input"]
            expected_llm_response_part = f"Placeholder response from {llm_model_name} for: {test_query}"
            expected_full_ai_output = f"AI: {ai_name}: {expected_llm_response_part}{case['emotion_suffix']}"

            with patch('sys.argv', ['main.py', 'query', test_query]):
                captured_output = StringIO()
                with patch('sys.stdout', new=captured_output):
                    # We might want to mock DialogueManager's internal EmotionSystem for more control,
                    # but for now, we test the integrated behavior.
                    cli_main.main()

                output = captured_output.getvalue()
                self.assertIn(f"CLI: Received query: '{test_query}'", output)
                self.assertIn(expected_full_ai_output, output)
        print("TestCLI.test_02_cli_query_with_emotion PASSED")

    def test_03_cli_config_get_placeholder(self):
        """Test the placeholder 'config get' command."""
        key = "some.setting"
        with patch('sys.argv', ['main.py', 'config', 'get', key]):
            captured_output = StringIO()
            with patch('sys.stdout', new=captured_output):
                cli_main.main()

            output = captured_output.getvalue()
            self.assertIn(f"CLI: Managing configuration. Action: get, Key: {key}, Value: None (Placeholder)", output)
        print("TestCLI.test_03_cli_config_get_placeholder PASSED")

    def test_04_cli_config_set_placeholder(self):
        """Test the placeholder 'config set' command."""
        key = "another.setting"
        value = "new_value"
        with patch('sys.argv', ['main.py', 'config', 'set', key, value]):
            captured_output = StringIO()
            with patch('sys.stdout', new=captured_output):
                cli_main.main()

            output = captured_output.getvalue()
            self.assertIn(f"CLI: Managing configuration. Action: set, Key: {key}, Value: {value} (Placeholder)", output)
        print("TestCLI.test_04_cli_config_set_placeholder PASSED")

    def test_05_cli_query_crisis_response(self):
        """Test the 'query' command for crisis response."""
        # Uses default CrisisSystem keywords like "emergency"
        test_query_crisis = "Help, this is an emergency!"
        ai_name = "Miko (Base)" # From miko_base.json

        # Expected default crisis response from DialogueManager
        expected_crisis_output = f"AI: {ai_name}: I sense this is a sensitive situation. If you need help, please reach out to appropriate support channels."

        with patch('sys.argv', ['main.py', 'query', test_query_crisis]):
            captured_output = StringIO()
            with patch('sys.stdout', new=captured_output):
                cli_main.main()

            output = captured_output.getvalue()
            self.assertIn(f"CLI: Received query: '{test_query_crisis}'", output)
            self.assertIn(expected_crisis_output, output)
            # Also check that the normal LLM response part is NOT there
            self.assertNotIn("Placeholder response from", output)
        print("TestCLI.test_05_cli_query_crisis_response PASSED")


if __name__ == '__main__':
    # This allows running tests directly using `python path/to/test_cli.py`
    # For sys.argv patching to work as expected when run directly,
    # it's often better to run via `python -m unittest discover` or `pytest`.
    # However, the patches should work if this file is the entry point.
    unittest.main(verbosity=2)
