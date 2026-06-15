"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
Intent handlers — classes that process specific intents detected by ChatService.
"""

try:
    from services.handlers.file_operation_handler import FileOperationHandler
except ImportError:
    FileOperationHandler = None

try:
    from services.handlers.google_drive_handler import GoogleDriveHandler
except ImportError:
    GoogleDriveHandler = None

try:
    from services.handlers.web_search_handler import WebSearchHandler
except ImportError:
    WebSearchHandler = None

try:
    from services.handlers.code_execution_handler import CodeExecutionHandler
except ImportError:
    CodeExecutionHandler = None

try:
    from services.handlers.system_command_handler import SystemCommandHandler
except ImportError:
    SystemCommandHandler = None

try:
    from services.handlers.task_manager_handler import TaskManagerHandler
except ImportError:
    TaskManagerHandler = None

try:
    from services.handlers.vision_handler import VisionHandler
except ImportError:
    VisionHandler = None

try:
    from services.handlers.learning_handler import LearningHandler
except ImportError:
    LearningHandler = None

__all__ = [
    "FileOperationHandler",
    "GoogleDriveHandler",
    "WebSearchHandler",
    "CodeExecutionHandler",
    "SystemCommandHandler",
    "TaskManagerHandler",
    "VisionHandler",
    "LearningHandler",
]
