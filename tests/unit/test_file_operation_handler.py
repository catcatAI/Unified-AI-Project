"""Tests for FileOperationHandler — matches actual handle() signature"""
import pytest


class TestFileOperationHandler:
    """Tests for FileOperationHandler"""

    def test_import(self):
        from services.handlers.file_operation_handler import FileOperationHandler
        assert FileOperationHandler is not None

    def test_instantiation(self):
        from services.handlers.file_operation_handler import FileOperationHandler
        instance = FileOperationHandler()
        assert instance is not None
        assert instance._desktop_interaction is None

    def test_handle_with_params_dict(self):
        import asyncio

        from services.handlers.file_operation_handler import FileOperationHandler
        instance = FileOperationHandler()
        # handle() expects params as dict, not string
        result = asyncio.run(instance.handle("file_op_organize", {"action": "list", "path": "/tmp"}))
        assert result is not None
        assert isinstance(result, str)

    def test_handle_missing_path(self):
        import asyncio

        from services.handlers.file_operation_handler import FileOperationHandler
        instance = FileOperationHandler()
        result = asyncio.run(instance.handle("file_op_read", {"action": "read"}))
        assert result is not None
        assert isinstance(result, str)
