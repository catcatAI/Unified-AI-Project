"""
Tests for the command-line interface (CLI).
"""

import pytest
from io import StringIO
from unittest.mock import patch, MagicMock, AsyncMock

# Corrected import path
from packages.cli.main import main_cli_logic

@pytest.mark.asyncio
async def test_cli_no_args():
    """Test CLI response when no arguments are provided."""
    with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
         patch('sys.argv', ['main.py']):
        await main_cli_logic()
        # We expect some form of help or usage message to be printed to stderr
        assert "usage:" in mock_stderr.getvalue().lower()

@pytest.mark.asyncio
@patch('packages.cli.main.initialize_services', new_callable=AsyncMock)
@patch('packages.cli.main.get_services')
@patch('packages.cli.main.shutdown_services', new_callable=AsyncMock)
async def test_cli_query_with_emotion(mock_shutdown, mock_get, mock_init):
    """Test the 'query' command with LLM and Emotion integration."""
    mock_dm = MagicMock()
    mock_get.return_value = {"dialogue_manager": mock_dm}
    ai_name = "Miko (Base)"
    llm_model_name = "generic-llm-placeholder"

    test_cases = [
        {"input": "This is a neutral statement.", "dm_response": f"{ai_name}: Hello! How can I help you?", "expected_substring": "How can I help you?"},
        {"input": "I am so sad today.", "dm_response": f"{ai_name}: (gently) I hear that.", "expected_substring": "(gently)"},
        {"input": "This is great and I am happy!", "dm_response": f"{ai_name}: (playfully) That's awesome! ✨", "expected_substring": "(playfully) ✨"},
    ]

    for case in test_cases:
        mock_dm.get_simple_response = AsyncMock(return_value=case["dm_response"])

        with patch('sys.argv', ['main.py', 'query', case["input"]]), \
             patch('sys.stdout', new_callable=StringIO) as captured_output:
            
            await main_cli_logic()
            
            output = captured_output.getvalue()
            assert case["expected_substring"] in output

@pytest.mark.asyncio
@patch('packages.cli.main.initialize_services', new_callable=AsyncMock)
@patch('packages.cli.main.get_services')
@patch('packages.cli.main.shutdown_services', new_callable=AsyncMock)
async def test_cli_query_crisis_response(mock_shutdown, mock_get, mock_init):
    """Test the 'query' command for crisis response."""
    mock_dm = MagicMock()
    mock_get.return_value = {"dialogue_manager": mock_dm}
    ai_name = "Miko (Base)"
    test_query_crisis = "Help, this is an emergency!"
    expected_crisis_output = f"AI, {ai_name}: I sense this is a sensitive situation. Please reach out to support."
    expected_substring = "appropriate support channels"

    mock_dm.get_simple_response = AsyncMock(return_value=expected_crisis_output)

    with patch('sys.argv', ['main.py', 'query', test_query_crisis]), \
         patch('sys.stdout', new_callable=StringIO) as captured_output:
        
        await main_cli_logic()
        
        output = captured_output.getvalue()
        # The actual check might be for a substring if the full response is dynamic
        assert "sensitive situation" in output or "support" in output