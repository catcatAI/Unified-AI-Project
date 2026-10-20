"""
ANGELA-MATRIX: [L3] [β] [B] [L2]
The declared file-operation limits must actually apply.

``file_ops.default.yaml`` declares four limits. Two of them were read
(``max_file_size_mb``); the other two were configuration nobody consumed:
``move_to_trash`` (a *recoverable* delete — every delete path called
``unlink()``) and ``require_confirmation_over_mb`` (a big write went
straight through).

These tests pin the wired behaviour.
"""

import json
from pathlib import Path

import pytest
from core.system.config.magic_numbers import (
    file_ops_confirm_over_mb,
    file_ops_move_to_trash,
    max_file_write_mb,
)

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "apps/backend/configs/standard/behavior/file_ops.default.yaml"


class TestLimitsAreRead:
    def test_the_config_declares_the_limits_we_consume(self):
        text = CONFIG.read_text(encoding="utf-8")
        for key in (
            "max_file_size_mb",
            "require_confirmation_over_mb",
            "move_to_trash",
        ):
            assert f"{key}:" in text, f"{key} is not declared"

    def test_the_accessors_return_sane_values(self):
        assert max_file_write_mb() > 0
        assert file_ops_confirm_over_mb() > 0
        assert file_ops_move_to_trash() is True


class TestTrashIsRecoverable:
    def test_a_delete_moves_the_file_to_the_trash(self, tmp_path, monkeypatch):
        from core.system import trash

        trash_root = tmp_path / "trash"
        monkeypatch.setattr(trash, "trash_dir", lambda: trash_root)

        target = tmp_path / "note.txt"
        target.write_text("keep me", encoding="utf-8")

        from services.handlers.file_operation_handler import FileOperationHandler

        handler = FileOperationHandler()
        message = handler._delete(target)

        assert not target.exists(), "the file was destroyed instead of moved"
        moved = list((trash_root / "files").glob("note.txt"))
        assert moved, f"the file is not in the trash: {message}"
        assert moved[0].read_text(encoding="utf-8") == "keep me"

    def test_a_trash_failure_falls_back_to_a_hard_delete(self, tmp_path, monkeypatch):
        from core.system import trash

        monkeypatch.setattr(trash, "move_to_trash", lambda target: None, raising=True)
        target = tmp_path / "gone.txt"
        target.write_text("x", encoding="utf-8")

        from services.handlers.file_operation_handler import FileOperationHandler

        handler = FileOperationHandler()
        handler._delete(target)
        assert not target.exists()


class TestBigWritesNeedConfirmation:
    def test_a_write_above_the_threshold_asks_first(self, tmp_path, monkeypatch):
        from services.handlers.file_operation_handler import FileOperationHandler

        monkeypatch.setattr(
            "services.handlers.file_operation_handler.file_ops_confirm_over_mb",
            lambda: 0,
        )
        target = tmp_path / "big.txt"
        handler = FileOperationHandler()
        message = handler._write(target, content="x" * 2048)
        assert not target.exists(), "the oversized write went through unconfirmed"
        # The default locale is Chinese (zh-CN) — accept either script.
        assert "confirm" in message.lower() or "确认" in message or "確認" in message

    def test_a_confirmed_write_goes_through(self, tmp_path, monkeypatch):
        from services.handlers.file_operation_handler import FileOperationHandler

        monkeypatch.setattr(
            "services.handlers.file_operation_handler.file_ops_confirm_over_mb",
            lambda: 0,
        )
        target = tmp_path / "big.txt"
        handler = FileOperationHandler()
        handler._write(target, content="x" * 2048, confirmed=True)
        assert target.exists()

    def test_a_small_write_needs_no_confirmation(self, tmp_path):
        from services.handlers.file_operation_handler import FileOperationHandler

        target = tmp_path / "small.txt"
        handler = FileOperationHandler()
        handler._write(target, content="hello")
        assert target.read_text(encoding="utf-8") == "hello"


class TestLocaleParity:
    def test_both_locales_have_the_new_strings(self):
        en = json.loads(
            (ROOT / "apps/backend/src/core/i18n/locales/en-US.json").read_text(encoding="utf-8")
        )
        zh = json.loads(
            (ROOT / "apps/backend/src/core/i18n/locales/zh-CN.json").read_text(encoding="utf-8")
        )
        for key in ("moved_to_trash", "confirm_required"):
            assert key in en["file_ops"]
            assert key in zh["file_ops"]


class TestDesktopDeleteIsRecoverableToo:
    """The agent's desktop delete must be recoverable as well.

    The desktop interaction is how the *AI* deletes a file on the user's
    behalf — exactly the case where a hard delete is unrecoverable.
    """

    def test_the_desktop_delete_moves_to_the_trash(self, tmp_path, monkeypatch):
        import asyncio

        from core.engine.desktop_interaction import DesktopInteraction
        from core.system import trash

        monkeypatch.setattr(trash, "trash_dir", lambda: tmp_path / "trash")

        from core.engine import desktop_interaction

        # The desktop interaction only touches its own allowed roots — the
        # temp dir becomes one of them for the test.
        monkeypatch.setattr(desktop_interaction, "_ALLOWED_ROOTS", [tmp_path], raising=False)
        interaction = desktop_interaction.DesktopInteraction()
        target = tmp_path / "note.txt"
        target.write_text("keep me", encoding="utf-8")

        result = asyncio.run(interaction.delete_file(target))
        assert result is True
        assert not target.exists(), "the file was destroyed instead of moved"
        moved = list((tmp_path / "trash" / "files").glob("note.txt"))
        assert moved, "the file is not in the trash"
        assert moved[0].read_text(encoding="utf-8") == "keep me"
