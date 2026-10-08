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
        result = asyncio.run(
            instance.handle("file_op_organize", {"action": "list", "path": "/tmp"})
        )
        assert result is not None
        assert isinstance(result, str)

    def test_handle_missing_path(self):
        import asyncio

        from services.handlers.file_operation_handler import FileOperationHandler

        instance = FileOperationHandler()
        result = asyncio.run(instance.handle("file_op_read", {"action": "read"}))
        assert result is not None
        assert isinstance(result, str)


class TestFileSizeLimits:
    """Configured max_file_size_mb is enforced, not just documented."""

    def test_configured_limit_is_read(self):
        from core.system.config.magic_numbers import max_file_write_mb

        assert max_file_write_mb() == 50

    def test_write_refuses_oversized(self, tmp_path, monkeypatch):
        import services.handlers.file_operation_handler as handler_mod
        from services.handlers.file_operation_handler import FileOperationHandler

        monkeypatch.setattr(handler_mod, "max_file_write_mb", lambda: 0)
        target = tmp_path / "big.txt"
        result = FileOperationHandler()._write(target, "x" * 100)
        assert "0" in result
        assert not target.exists()

    def test_write_allows_small(self, tmp_path):
        from services.handlers.file_operation_handler import FileOperationHandler

        target = tmp_path / "small.txt"
        result = FileOperationHandler()._write(target, "hello")
        assert target.read_text(encoding="utf-8") == "hello"
        assert "small.txt" in result

    def test_append_counts_existing_size(self, tmp_path, monkeypatch):
        import services.handlers.file_operation_handler as handler_mod
        from services.handlers.file_operation_handler import FileOperationHandler

        target = tmp_path / "grow.txt"
        target.write_text("abc", encoding="utf-8")
        monkeypatch.setattr(handler_mod, "max_file_write_mb", lambda: 0)
        before = target.read_text(encoding="utf-8")
        result = FileOperationHandler()._append(target, "x" * 100)
        assert "0" in result
        assert target.read_text(encoding="utf-8") == before
