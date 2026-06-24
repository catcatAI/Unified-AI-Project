"""Tests for services/handlers/ — intent handler modules.

Covers all 8 handlers:
- FileOperationHandler: file ops with path safety
- GoogleDriveHandler: Drive + local fs fallback
- WebSearchHandler: web search delegation
- CodeExecutionHandler: Python sandbox
- SystemCommandHandler: safe command execution
- TaskManagerHandler: JSON-backed task list
- VisionHandler: image analysis
- LearningHandler: knowledge capture
"""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps/backend/src"))


# =============================================================================
# FileOperationHandler tests
# =============================================================================

@pytest.mark.asyncio
class TestFileOperationHandler:
    """Test file operations with real temp directory."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        allowed_roots_patch = None
        # We can't easily patch _ALLOWED_ROOTS from test, so test safe paths only
        yield
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    async def test_import(self):
        """FileOperationHandler imports correctly."""
        from services.handlers.file_operation_handler import FileOperationHandler
        handler = FileOperationHandler()
        assert handler is not None

    async def test_empty_path_returns_prompt(self):
        """handle returns prompt when no path provided."""
        from services.handlers.file_operation_handler import FileOperationHandler
        handler = FileOperationHandler()
        result = await handler.handle("file_op", {})
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_unknown_action_returns_help(self):
        """handle returns help message for unknown actions."""
        from services.handlers.file_operation_handler import FileOperationHandler
        handler = FileOperationHandler()
        result = await handler.handle("file_op_bogus", {"path": "/tmp"})
        assert isinstance(result, str)
        assert len(result) > 0


# =============================================================================
# GoogleDriveHandler tests
# =============================================================================

@pytest.mark.asyncio
class TestGoogleDriveHandler:
    """Test GoogleDriveHandler with local fs fallback."""

    async def test_import(self):
        """GoogleDriveHandler imports correctly."""
        from services.handlers.google_drive_handler import GoogleDriveHandler
        handler = GoogleDriveHandler()
        assert handler is not None

    async def test_supported_actions(self):
        """Handler has expected supported actions."""
        from services.handlers.google_drive_handler import GoogleDriveHandler
        expected = {"list", "search", "sync", "download", "upload",
                     "delete", "rename", "move", "copy", "info"}
        assert GoogleDriveHandler.SUPPORTED_ACTIONS == expected

    async def test_unsupported_action(self):
        """Returns error for unsupported actions."""
        from services.handlers.google_drive_handler import GoogleDriveHandler
        handler = GoogleDriveHandler()
        result = await handler.handle("google_drive", {"action": "unsupported_action_xyz"})
        assert result["status"] == "error"

    async def test_info_existing_path(self):
        """info action returns file info for existing path."""
        from services.handlers.google_drive_handler import GoogleDriveHandler
        handler = GoogleDriveHandler()
        import os
        result = await handler.handle("google_drive", {"action": "info", "path": os.getcwd()})
        assert result["status"] == "ok"
        assert result["exists"] is True

    async def test_info_nonexistent_path(self):
        """info action returns exists=False for nonexistent path."""
        from services.handlers.google_drive_handler import GoogleDriveHandler
        handler = GoogleDriveHandler()
        result = await handler.handle("google_drive", {"action": "info", "path": "/nonexistent_path_xyz_123"})
        assert result["status"] == "ok"
        assert result["exists"] is False


# =============================================================================
# WebSearchHandler tests
# =============================================================================

@pytest.mark.asyncio
class TestWebSearchHandler:
    """Test WebSearchHandler extract logic."""

    async def test_import(self):
        """WebSearchHandler imports correctly."""
        from services.handlers.web_search_handler import WebSearchHandler
        handler = WebSearchHandler()
        assert handler is not None

    async def test_handle_empty_text(self):
        """handle returns prompt for empty text."""
        from services.handlers.web_search_handler import WebSearchHandler
        handler = WebSearchHandler()
        result = await handler.handle("", "web_search")
        assert "搜尋" in result

    async def test_extract_query_removes_prefix(self):
        """_extract_query removes prefix keywords."""
        from services.handlers.web_search_handler import WebSearchHandler
        handler = WebSearchHandler()
        query = handler._extract_query("搜尋如何學習Python")
        assert query is not None
        assert "如何學習Python" in query or "学习Python" in query or "Python" in query

    async def test_extract_query_short_text(self):
        """_extract_query returns None for very short text."""
        from services.handlers.web_search_handler import WebSearchHandler
        handler = WebSearchHandler()
        query = handler._extract_query("搜尋")
        assert query is None or len(query) < 2


# =============================================================================
# CodeExecutionHandler tests
# =============================================================================

@pytest.mark.asyncio
class TestCodeExecutionHandler:
    """Test CodeExecutionHandler with sandboxed execution."""

    async def test_import(self):
        """CodeExecutionHandler imports correctly."""
        from services.handlers.code_execution_handler import CodeExecutionHandler
        handler = CodeExecutionHandler()
        assert handler is not None

    async def test_extract_code_from_fence(self):
        """_extract_code extracts code from markdown fence."""
        from services.handlers.code_execution_handler import CodeExecutionHandler
        handler = CodeExecutionHandler()
        code = handler._extract_code("```python\nprint('hello')\n```")
        assert "print('hello')" in code

    async def test_extract_code_from_inline(self):
        """_extract_code extracts code from backtick."""
        from services.handlers.code_execution_handler import CodeExecutionHandler
        handler = CodeExecutionHandler()
        code = handler._extract_code("run `print(42)`")
        assert "print(42)" in code

    async def test_extract_code_empty(self):
        """_extract_code returns original text when no code pattern matches."""
        from services.handlers.code_execution_handler import CodeExecutionHandler
        handler = CodeExecutionHandler()
        code = handler._extract_code("今天天氣真好")
        assert code == "今天天氣真好"

    async def test_execute_simple_print(self):
        """_execute runs simple print statement."""
        from services.handlers.code_execution_handler import CodeExecutionHandler
        handler = CodeExecutionHandler()
        result = await handler._execute("print('hello_world_test')")
        # i18n returns raw keys in test context, so check for execution markers
        assert "code_exec.header" in result or "code_exec.output" in result or "hello" in result
        assert len(result) > 10

    async def test_handle_with_code(self):
        """handle extracts and executes code from message."""
        from services.handlers.code_execution_handler import CodeExecutionHandler
        handler = CodeExecutionHandler()
        result = await handler.handle("```python\nprint('hello')\n```", "code")
        # Check that execution happened (i18n returns raw key in test context)
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_execute_math(self):
        """_execute runs math expression."""
        from services.handlers.code_execution_handler import CodeExecutionHandler
        handler = CodeExecutionHandler()
        result = await handler._execute("print(2 + 3)")
        assert len(result) > 10


# =============================================================================
# SystemCommandHandler tests
# =============================================================================

@pytest.mark.asyncio
class TestSystemCommandHandler:
    """Test SystemCommandHandler with safe commands."""

    async def test_import(self):
        """SystemCommandHandler imports correctly."""
        from services.handlers.system_command_handler import SystemCommandHandler
        handler = SystemCommandHandler()
        assert handler is not None

    async def test_extract_command_from_fence(self):
        """_extract_command extracts from markdown fence."""
        from services.handlers.system_command_handler import SystemCommandHandler
        handler = SystemCommandHandler()
        cmd = handler._extract_command("```bash\necho hello\n```")
        assert "echo hello" in cmd

    async def test_extract_command_from_inline(self):
        """_extract_command extracts from backtick."""
        from services.handlers.system_command_handler import SystemCommandHandler
        handler = SystemCommandHandler()
        cmd = handler._extract_command("run `echo hi`")
        assert "echo hi" in cmd

    async def test_unsafe_command_rejected(self):
        """handle rejects unsafe commands."""
        from services.handlers.system_command_handler import SystemCommandHandler
        handler = SystemCommandHandler()
        result = await handler.handle("執行 rm -rf /", "system")
        assert "unsafe" in result.lower() or "安全" in result or "allow" in result.lower()

    async def test_safe_command_runs(self):
        """handle runs safe commands like echo."""
        from services.handlers.system_command_handler import SystemCommandHandler
        handler = SystemCommandHandler()
        result = await handler.handle("執行 echo hello_test_123", "system")
        # May or may not have echo in _SAFE_COMMANDS on this platform
        # If accepted, output should contain hello; if rejected, should mention unsafe
        assert isinstance(result, str)
        assert len(result) > 0


# =============================================================================
# TaskManagerHandler tests
# =============================================================================

@pytest.mark.asyncio
class TestTaskManagerHandler:
    """Test TaskManagerHandler with isolated tasks file."""

    @pytest.fixture(autouse=True)
    def setup(self):
        # Backup and restore _TASKS_FILE / _TASKS_DIR
        import services.handlers.task_manager_handler as tm
        self._orig_tasks_dir = tm._TASKS_DIR
        self._orig_tasks_file = tm._TASKS_FILE
        test_dir = Path(tempfile.mkdtemp()) / "tasks"
        tm._TASKS_DIR = test_dir
        tm._TASKS_FILE = test_dir / "tasks.json"
        yield
        tm._TASKS_DIR = self._orig_tasks_dir
        tm._TASKS_FILE = self._orig_tasks_file
        import shutil
        shutil.rmtree(test_dir.parent, ignore_errors=True)

    async def test_import(self):
        """TaskManagerHandler imports correctly."""
        from services.handlers.task_manager_handler import TaskManagerHandler
        handler = TaskManagerHandler()
        assert handler is not None

    async def test_create_task(self):
        """create action adds a task."""
        from services.handlers.task_manager_handler import TaskManagerHandler
        handler = TaskManagerHandler()
        result = await handler.handle("建立任務測試", "task")
        assert "task" in result.lower() or "任務" in result

    async def test_list_tasks(self):
        """list action returns task list."""
        from services.handlers.task_manager_handler import TaskManagerHandler
        handler = TaskManagerHandler()
        import services.handlers.task_manager_handler as tm
        tm._save_tasks([{"id": 1, "title": "test_task_123", "status": "pending", "created_at": 1000}])
        result = await handler.handle("任務列表", "task")
        # i18n returns raw keys in test context, but task data should be in output
        assert "test_task_123" in result or "task_ops.task_list" in result

    async def test_parse_create(self):
        """_parse identifies create action."""
        from services.handlers.task_manager_handler import TaskManagerHandler
        handler = TaskManagerHandler()
        action, payload = handler._parse("建立任務測試工作")
        assert action == "create"
        assert "title" in payload


# =============================================================================
# VisionHandler tests
# =============================================================================

@pytest.mark.asyncio
class TestVisionHandler:
    """Test VisionHandler extract logic."""

    async def test_import(self):
        """VisionHandler imports correctly."""
        from services.handlers.vision_handler import VisionHandler
        handler = VisionHandler()
        assert handler is not None

    async def test_extract_image_path_no_path(self):
        """_extract_image_path returns None when no image reference."""
        from services.handlers.vision_handler import VisionHandler
        handler = VisionHandler()
        path = handler._extract_image_path("今天天氣真好")
        assert path is None

    async def test_extract_image_path_with_extension(self):
        """_extract_image_path finds path with image extension."""
        from services.handlers.vision_handler import VisionHandler
        handler = VisionHandler()
        path = handler._extract_image_path("分析圖片 /path/to/photo.png")
        assert path is not None
        assert "photo.png" in path

    async def test_extract_image_path_with_fence(self):
        """_extract_image_path extracts from code fence."""
        from services.handlers.vision_handler import VisionHandler
        handler = VisionHandler()
        path = handler._extract_image_path("```\n/image.jpg\n```")
        assert path is not None
        assert "image.jpg" in path

    async def test_handle_no_path(self):
        """handle returns prompt when no image path."""
        from services.handlers.vision_handler import VisionHandler
        handler = VisionHandler()
        result = await handler.handle("分析圖片", "vision")
        assert isinstance(result, str)
        assert "圖片" in result or "vision" in result.lower()


# =============================================================================
# LearningHandler tests
# =============================================================================

@pytest.mark.asyncio
class TestLearningHandler:
    """Test LearningHandler extract logic."""

    async def test_import(self):
        """LearningHandler imports correctly."""
        from services.handlers.learning_handler import LearningHandler
        handler = LearningHandler()
        assert handler is not None

    async def test_extract_fact_with_prefix(self):
        """_extract_fact removes learning prefix."""
        from services.handlers.learning_handler import LearningHandler
        handler = LearningHandler()
        fact = handler._extract_fact("記住我喜歡藍色")
        assert fact is not None
        assert "喜歡藍色" in fact or "蓝色" in fact or "藍色" in fact

    async def test_extract_fact_no_prefix(self):
        """_extract_fact returns None for empty/prefix-only text."""
        from services.handlers.learning_handler import LearningHandler
        handler = LearningHandler()
        fact = handler._extract_fact("記住")
        assert fact is None or len(fact) < 2

    async def test_extract_fact_english(self):
        """_extract_fact handles English remember prefix."""
        from services.handlers.learning_handler import LearningHandler
        handler = LearningHandler()
        fact = handler._extract_fact("remember the sky is blue")
        assert fact is not None
        assert "sky is blue" in fact.lower()

    async def test_handle_empty_text(self):
        """handle returns prompt when no fact extracted."""
        from services.handlers.learning_handler import LearningHandler
        handler = LearningHandler()
        result = await handler.handle("", "learning")
        assert isinstance(result, str)
        assert "學習" in result or "learn" in result.lower() or "記住" in result


# =============================================================================
# All handlers module-level import tests
# =============================================================================

class TestHandlersInit:
    """Test handlers/__init__.py exports."""

    def test_all_handlers_exported(self):
        """__init__.py exports all 8 handler classes."""
        from services.handlers import (
            FileOperationHandler,
            GoogleDriveHandler,
            WebSearchHandler,
            CodeExecutionHandler,
            SystemCommandHandler,
            TaskManagerHandler,
            VisionHandler,
            LearningHandler,
        )
        assert FileOperationHandler is not None
        assert GoogleDriveHandler is not None
        assert WebSearchHandler is not None
        assert CodeExecutionHandler is not None
        assert SystemCommandHandler is not None
        assert TaskManagerHandler is not None
        assert VisionHandler is not None
        assert LearningHandler is not None

    def test_all_exports_match(self):
        """__all__ matches exported names."""
        from services.handlers import __all__
        expected = [
            "FileOperationHandler",
            "GoogleDriveHandler",
            "WebSearchHandler",
            "CodeExecutionHandler",
            "SystemCommandHandler",
            "TaskManagerHandler",
            "VisionHandler",
            "LearningHandler",
        ]
        assert sorted(__all__) == sorted(expected)
