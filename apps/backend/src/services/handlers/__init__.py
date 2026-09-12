"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
Intent handlers — classes that process specific intents detected by ChatService.
"""

from typing import Any

# 延遲降級綁定：先預聲明為 Any 再條件 import——直接 `X = None` 會觸
# mypy「不可賦值給 type」誤報；此寫法行為不變，呼叫方仍以 None 判斷可用性。
FileOperationHandler: Any
try:
    from services.handlers.file_operation_handler import FileOperationHandler
except ImportError:
    FileOperationHandler = None

GoogleDriveHandler: Any
try:
    from services.handlers.google_drive_handler import GoogleDriveHandler
except ImportError:
    GoogleDriveHandler = None

WebSearchHandler: Any
try:
    from services.handlers.web_search_handler import WebSearchHandler
except ImportError:
    WebSearchHandler = None

CodeExecutionHandler: Any
try:
    from services.handlers.code_execution_handler import CodeExecutionHandler
except ImportError:
    CodeExecutionHandler = None

SystemCommandHandler: Any
try:
    from services.handlers.system_command_handler import SystemCommandHandler
except ImportError:
    SystemCommandHandler = None

TaskManagerHandler: Any
try:
    from services.handlers.task_manager_handler import TaskManagerHandler
except ImportError:
    TaskManagerHandler = None

VisionHandler: Any
try:
    from services.handlers.vision_handler import VisionHandler
except ImportError:
    VisionHandler = None

LearningHandler: Any
try:
    from services.handlers.learning_handler import LearningHandler
except ImportError:
    LearningHandler = None

CivilModelHandler: Any
try:
    from services.handlers.civil_model_handler import CivilModelHandler
except ImportError:
    CivilModelHandler = None

__all__ = [
    "FileOperationHandler",
    "GoogleDriveHandler",
    "WebSearchHandler",
    "CodeExecutionHandler",
    "SystemCommandHandler",
    "TaskManagerHandler",
    "VisionHandler",
    "LearningHandler",
    "CivilModelHandler",
]
