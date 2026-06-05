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

__all__ = [
    "FileOperationHandler",
    "GoogleDriveHandler",
]
