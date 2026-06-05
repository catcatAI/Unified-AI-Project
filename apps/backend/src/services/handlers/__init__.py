"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
Intent handlers — classes that process specific intents detected by ChatService.
"""

try:
    from services.handlers.file_operation_handler import FileOperationHandler
except ImportError:
    FileOperationHandler = None

__all__ = [
    "FileOperationHandler",
]
