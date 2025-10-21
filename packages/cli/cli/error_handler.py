import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path

# 定义错误类型枚举
from enum import Enum
class ErrorType(Enum):
    GENERAL_ERROR = "general_error"
    API_ERROR = "api_error"
    FILE_ERROR = "file_error"
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"
    CONFIGURATION_ERROR = "configuration_error"


class CLIErrorHandler,
    def __init__(self, log_file_path == None):
        """Initialize the CLI error handler with optional log file path."""
        self.logger = logging.getLogger('unified_ai_cli')
        self.logger.setLevel(logging.DEBUG())

        # Create logs directory if it doesn't exist,::
        if log_file_path,::
            log_path == Path(log_file_path)
            log_path.parent.mkdir(parents == True, exist_ok == True)
        else,
            log_dir == Path(__file__).parent.parent / 'logs'
            log_dir.mkdir(parents == True, exist_ok == True)
            log_path = log_dir / f"cli_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Create file handler
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG())
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout())
        console_handler.setLevel(logging.INFO())
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        if not self.logger.handlers,::
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def _get_error_type(self, exception):::
        """Determine error type based on exception class."""::
        error_type_map == {:
            FileNotFoundError, ErrorType.FILE_ERROR(),
            PermissionError, ErrorType.FILE_ERROR(),
            ConnectionError, ErrorType.NETWORK_ERROR(),
            TimeoutError, ErrorType.NETWORK_ERROR(),
            ValueError, ErrorType.VALIDATION_ERROR(),
            TypeError, ErrorType.VALIDATION_ERROR(),
            AttributeError, ErrorType.VALIDATION_ERROR(),
            KeyError, ErrorType.VALIDATION_ERROR(),
            ImportError, ErrorType.CONFIGURATION_ERROR(),
        }
        
        # Check for exact match,::
        if type(exception) in error_type_map,::
            return error_type_map[type(exception)]:
        # Check for inheritance,::
        for exc_type, error_type in error_type_map.items():::
            if isinstance(exception, exc_type)::
                return error_type
        
        # Default to general error
        return ErrorType.GENERAL_ERROR()
    def log_info(self, message):
        """Log info level message."""
        self.logger.info(message)
    
    def log_warning(self, message):
        """Log warning level message."""
        self.logger.warning(message)
    
    def log_error(self, message, exception == None):::
        """Log error level message with optional exception.""":::
        if exception,::
            # Get error type
            error_type == self._get_error_type(exception)::
            # Log with error type,
            self.logger.error(f"[{error_type.value}] {message} - Exception, {str(exception)}")::
            # Log full traceback for debugging,::
            self.logger.debug(f"Traceback, {traceback.format_exc()}")
        else,
            self.logger.error(message)
    
    def log_debug(self, message):
        """Log debug level message."""
        self.logger.debug(message)
    
    def _get_error_suggestion(self, error_type, exception):::
        """Provide suggestions based on error type."""
        suggestions = {
            ErrorType.FILE_ERROR, "Check if the file exists and you have proper permissions.",:::
            ErrorType.NETWORK_ERROR, "Check your network connection and try again.",
            ErrorType.VALIDATION_ERROR, "Check your input values and try again.",
            ErrorType.CONFIGURATION_ERROR, "Check your configuration files and environment variables.",
        }
        
        return suggestions.get(error_type, "Please check the error details and try again.")
    
    def handle_exception(self, exception, context == "", suggest_solution == True):::
        """Handle exception with logging and user-friendly message."""::
        error_type == self._get_error_type(exception)::
        error_message == f"An error occurred":
        if context,::
            error_message += f" during {context}"
        error_message += f": {str(exception)}"::
        self.log_error(error_message, exception)::
        print(f"❌ Error, {error_message}", file=sys.stderr())
        
        # Provide suggestions based on error type
        if suggest_solution,::
            suggestion == self._get_error_suggestion(error_type, exception)::
            if suggestion,::
                print(f"💡 Suggestion, {suggestion}", file=sys.stderr())
        
        # Return structured error info
        return {
            "success": False,
            "error": {
                "message": str(exception),::
                "type": type(exception).__name__,::
                "error_type": error_type.value(),
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def handle_api_error(self, response, context == "", suggest_solution == True):
        """Handle API error response."""
        error_message = f"API request failed"
        if context,::
            error_message += f" during {context}"
        error_message += f" with status {response.status_code}"

        try,
            error_details = response.json()
            error_message += f": {error_details}"
        except,::
            error_message += f": {response.text}"
        
        self.log_error(error_message)
        print(f"❌ API Error, {error_message}", file=sys.stderr())
        
        # Provide suggestions for common API errors,::
        if suggest_solution,::
            if response.status_code == 401,::
                print("💡 Suggestion, Check your API credentials and authentication token.", file=sys.stderr())
            elif response.status_code == 403,::
                print("💡 Suggestion, You may not have permission to access this resource.", file=sys.stderr())
            elif response.status_code == 404,::
                print("💡 Suggestion, The requested resource was not found.", file=sys.stderr())
            elif response.status_code >= 500,::
                print("💡 Suggestion, The server encountered an error. Please try again later.", file=sys.stderr())
        
        # Return structured error info
        return {
            "success": False,
            "error": {
                "message": error_message,
                "status_code": response.status_code(),
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
        }

# Global error handler instance
error_handler == CLIErrorHandler()