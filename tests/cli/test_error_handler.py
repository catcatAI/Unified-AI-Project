"""
测试模块 - test_error_handler

自动生成的测试模块，用于验证系统功能。
"""

import sys
import os
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime
import pytest

# Add the cli directory to the path so we can import the error handler
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'cli'))

from cli.error_handler import CLIErrorHandler

class TestCLIErrorHandler:
    
    
    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
def test_init_with_default_log_path(self):
        """Test CLIErrorHandler initialization with default log path."""
        handler = CLIErrorHandler()
        assert handler.logger is not None
        assert len(handler.logger.handlers) >= 2  # File and console handlers
        
    def test_init_with_custom_log_path(self):
        """Test CLIErrorHandler initialization with custom log path."""
        custom_path = os.path.join(os.path.dirname(__file__), 'test_logs', 'custom.log')
        handler = CLIErrorHandler(custom_path)
        assert handler.logger is not None
        
    def test_log_info(self, caplog):
        """Test logging info messages."""
        handler = CLIErrorHandler()
        with caplog.at_level(logging.INFO):
            handler.log_info("Test info message")
            
        # Check if message was logged
        assert "Test info message" in caplog.text
        
    def test_log_warning(self, caplog):
        """Test logging warning messages."""
        handler = CLIErrorHandler()
        with caplog.at_level(logging.WARNING):
            handler.log_warning("Test warning message")
            
        # Check if message was logged
        assert "Test warning message" in caplog.text
        
    def test_log_error(self, caplog):
        """Test logging error messages."""
        handler = CLIErrorHandler()
        with caplog.at_level(logging.ERROR):
            handler.log_error("Test error message")
            
        # Check if message was logged
        assert "Test error message" in caplog.text
        
    def test_log_error_with_exception(self, caplog):
        """Test logging error messages with exception."""
        handler = CLIErrorHandler()
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            with caplog.at_level(logging.ERROR):
                handler.log_error("Test error with exception", e)
            
        # Check if message was logged
        assert "Test error with exception" in caplog.text
        assert "Test exception" in caplog.text
        
    def test_log_debug(self, caplog):
        """Test logging debug messages."""
        handler = CLIErrorHandler()
        with caplog.at_level(logging.DEBUG):
            handler.log_debug("Test debug message")
            
        # Check if message was logged
        assert "Test debug message" in caplog.text
        
    def test_handle_exception(self, caplog):
        """Test handling exceptions with user-friendly messages."""
        handler = CLIErrorHandler()
        try:
            raise RuntimeError("Test runtime error")
        except RuntimeError as e:
            with caplog.at_level(logging.ERROR):
                result = handler.handle_exception(e, "test operation")
        
        # Check the returned result structure
        assert result["success"] is False
        assert "error" in result
        assert result["error"]["message"] == "Test runtime error"
        assert result["error"]["type"] == "RuntimeError"
        assert result["error"]["context"] == "test operation"
        
        # Check if message was logged
        assert "Test runtime error" in caplog.text
        assert "test operation" in caplog.text
        
    @patch('requests.Response')
    def test_handle_api_error(self, mock_response, caplog):
        """Test handling API errors."""
        handler = CLIErrorHandler()
        
        # Mock response with JSON error details
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Not found", "message": "Resource not found"}
        mock_response.text = "Resource not found"
        
        with caplog.at_level(logging.ERROR):
            result = handler.handle_api_error(mock_response, "test API call")
        
        # Check the returned result structure
        assert result["success"] is False
        assert "error" in result
        assert "status_code" in result["error"]
        assert result["error"]["status_code"] == 404
        assert result["error"]["context"] == "test API call"
        
        # Check if message was logged
        assert "API request failed" in caplog.text
        assert "404" in caplog.text