"""
Tests for the CLI Error Handler.
"""

import os
import logging
import pytest
from unittest.mock import patch, MagicMock

# Corrected import path
from packages.cli.error_handler import CLIErrorHandler

@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary directory for logs."""
    log_dir = tmp_path / "test_logs"
    log_dir.mkdir()
    return log_dir

def test_init_with_custom_log_path(temp_log_dir):
    """Test CLIErrorHandler initialization with a custom log path."""
    custom_path = temp_log_dir / 'custom.log'
    handler = CLIErrorHandler(str(custom_path))
    assert handler.logger is not None
    # Verify that the file handler is pointing to the correct file
    found_file_handler = False
    for h in handler.logger.handlers:
        if isinstance(h, logging.FileHandler):
            assert h.baseFilename == str(custom_path)
            found_file_handler = True
    assert found_file_handler, "File handler not configured with custom path."

def test_log_info(caplog):
    """Test logging info messages."""
    handler = CLIErrorHandler()
    with caplog.at_level(logging.INFO):
        handler.log_info("Test info message")
    assert "Test info message" in caplog.text

def test_log_warning(caplog):
    """Test logging warning messages."""
    handler = CLIErrorHandler()
    with caplog.at_level(logging.WARNING):
        handler.log_warning("Test warning message")
    assert "Test warning message" in caplog.text

def test_log_error(caplog):
    """Test logging error messages."""
    handler = CLIErrorHandler()
    with caplog.at_level(logging.ERROR):
        handler.log_error("Test error message")
    assert "Test error message" in caplog.text

def test_log_error_with_exception(caplog):
    """Test logging an error message with an exception."""
    handler = CLIErrorHandler()
    try:
        raise ValueError("Test exception")
    except ValueError as e:
        with caplog.at_level(logging.ERROR):
            handler.log_error("Test error with exception", e)
    
    assert "Test error with exception" in caplog.text
    assert "Test exception" in caplog.text

def test_handle_exception(caplog):
    """Test handling exceptions with user-friendly messages."""
    handler = CLIErrorHandler()
    try:
        raise RuntimeError("Test runtime error")
    except RuntimeError as e:
        with caplog.at_level(logging.ERROR):
            result = handler.handle_exception(e, "test operation")

    assert not result["success"]
    assert "error" in result
    assert result["error"]["message"] == "Test runtime error"
    assert result["error"]["type"] == "RuntimeError"
    assert result["error"]["context"] == "test operation"
    
    assert "Test runtime error" in caplog.text
    assert "test operation" in caplog.text

@patch('requests.Response')
def test_handle_api_error(mock_response, caplog):
    """Test handling of API errors."""
    handler = CLIErrorHandler()
    
    mock_response.status_code = 404
    mock_response.json.return_value = {"error": "Not Found", "message": "The requested resource was not found."}
    mock_response.text = "Not Found"

    with caplog.at_level(logging.ERROR):
        result = handler.handle_api_error(mock_response, "test API call")

    assert not result["success"]
    assert "error" in result
    assert result["error"]["status_code"] == 404
    assert "The requested resource was not found" in result["error"]["details"]
    assert result["error"]["context"] == "test API call"
    
    assert "API request failed" in caplog.text
    assert "404" in caplog.text
