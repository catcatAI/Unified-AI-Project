import logging
import sys
from datetime import datetime
from pathlib import Path

class CLIErrorHandler:
    def __init__(self, log_file_path=None):
        """Initialize the CLI error handler with optional log file path."""
        self.logger = logging.getLogger('unified_ai_cli')
        self.logger.setLevel(logging.DEBUG)
        
        # Create logs directory if it doesn't exist
        if log_file_path:
            log_path = Path(log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            log_dir = Path(__file__).parent.parent / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / f"cli_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Create file handler
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def log_info(self, message):
        """Log info level message."""
        self.logger.info(message)
    
    def log_warning(self, message):
        """Log warning level message."""
        self.logger.warning(message)
    
    def log_error(self, message, exception=None):
        """Log error level message with optional exception."""
        if exception:
            self.logger.error(f"{message} - Exception: {str(exception)}")
        else:
            self.logger.error(message)
    
    def log_debug(self, message):
        """Log debug level message."""
        self.logger.debug(message)
    
    def handle_exception(self, exception, context=""):
        """Handle exception with logging and user-friendly message."""
        error_message = f"An error occurred"
        if context:
            error_message += f" during {context}"
        error_message += f": {str(exception)}"
        
        self.log_error(error_message, exception)
        print(f"❌ Error: {error_message}", file=sys.stderr)
        
        # Return structured error info
        return {
            "success": False,
            "error": {
                "message": str(exception),
                "type": type(exception).__name__,
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def handle_api_error(self, response, context=""):
        """Handle API error response."""
        error_message = f"API request failed"
        if context:
            error_message += f" during {context}"
        error_message += f" with status {response.status_code}"
        
        try:
            error_details = response.json()
            error_message += f": {error_details}"
        except:
            error_message += f": {response.text}"
        
        self.log_error(error_message)
        print(f"❌ API Error: {error_message}", file=sys.stderr)
        
        # Return structured error info
        return {
            "success": False,
            "error": {
                "message": error_message,
                "status_code": response.status_code,
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
        }

# Global error handler instance
error_handler = CLIErrorHandler()