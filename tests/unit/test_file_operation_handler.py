"""Tests for FileOperationHandler"""
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
        assert instance._desktop is None

    def test_handle_organize_intent(self):
        from services.handlers.file_operation_handler import FileOperationHandler
        import asyncio
        instance = FileOperationHandler()
        result = asyncio.run(instance.handle("整理桌面", "file_op"))
        assert result is not None
        assert isinstance(result, str)

    def test_handle_cleanup_intent(self):
        from services.handlers.file_operation_handler import FileOperationHandler
        import asyncio
        instance = FileOperationHandler()
        result = asyncio.run(instance.handle("清理舊檔案", "file_op"))
        assert result is not None

    def test_handle_create_intent(self):
        from services.handlers.file_operation_handler import FileOperationHandler
        import asyncio
        instance = FileOperationHandler()
        result = asyncio.run(instance.handle("創建檔案", "file_op"))
        assert result is not None

    def test_handle_unknown_intent(self):
        from services.handlers.file_operation_handler import FileOperationHandler
        import asyncio
        instance = FileOperationHandler()
        result = asyncio.run(instance.handle("其他事情", "file_op"))
        assert result is not None
        assert "檔案操作" in result
