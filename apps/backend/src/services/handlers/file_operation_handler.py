"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
FileOperationHandler — processes file_op intents from ChatService dispatch.
Supports: create, read, write, delete, list, rename, copy, exists, size, append.
"""

import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from core.i18n.i18n_manager import t

logger = logging.getLogger(__name__)

_ALLOWED_ROOTS = [
    Path.home() / "Documents",
    Path.home() / "Desktop",
    Path.home() / "Downloads",
    Path.home() / "Projects",
    Path(tempfile.gettempdir()),
    Path(os.environ.get("ANGELA_WORKSPACE", os.getcwd())),
]

def _is_safe_path(target: Path) -> bool:
    try:
        resolved = target.resolve()
    except Exception as e:
        logger.debug("Path resolution failed: %s", e)
        return False
    for root in _ALLOWED_ROOTS:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


class FileOperationHandler:
    """Handles file operation intents with real filesystem operations."""

    def __init__(self, desktop_interaction: Any = None):
        self._desktop_interaction = desktop_interaction

    async def handle(self, intent: str, params: Optional[Dict[str, Any]] = None) -> str:
        operation = params or {}
        action = operation.get("action", intent.replace("file_op_", "")).lower()
        path_str = operation.get("path", operation.get("file", ""))
        content = operation.get("content", "")
        new_name = operation.get("new_name", operation.get("rename_to", ""))

        if not path_str:
            return t("file_ops.specify_path")

        target = Path(path_str)
        if not _is_safe_path(target):
            return t("file_ops.unsafe_path", path=path_str)

        handlers = {
            "create": self._create,
            "read": self._read,
            "write": self._write,
            "delete": self._delete,
            "remove": self._delete,
            "list": self._list_dir,
            "ls": self._list_dir,
            "rename": self._rename,
            "move": self._rename,
            "copy": self._copy,
            "exists": self._exists,
            "size": self._size,
            "append": self._append,
        }
        handler_fn = handlers.get(action)
        if not handler_fn:
            return t("file_ops.unsupported_action", action=action, actions=", ".join(handlers.keys()))

        try:
            return await asyncio.to_thread(handler_fn, target, content=content, new_name=new_name)
        except PermissionError:
            return t("file_ops.permission_denied", path=path_str)
        except Exception as e:
            logger.error(f"FileOperationHandler error: {e}", exc_info=True)
            return t("file_ops.operation_failed", error=str(e))

    def _create(self, target: Path, **kw) -> str:
        if target.exists():
            return t("file_ops.file_exists", path=str(target))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
        return t("file_ops.file_created", path=str(target))

    def _read(self, target: Path, **kw) -> str:
        if not target.exists():
            return t("file_ops.file_not_found", path=str(target))
        if target.is_dir():
            items = [f"  {'📁' if p.is_dir() else '📄'} {p.name}" for p in sorted(target.iterdir())[:50]]
            return t("file_ops.dir_contents", path=str(target)) + "\n" + "\n".join(items)
        try:
            text = target.read_text(encoding="utf-8", errors="replace")
            if len(text) > 4000:
                text = text[:4000] + "\n... (已截斷)"
            return t("file_ops.file_contents", path=str(target)) + "\n" + text
        except Exception as e:
            return t("file_ops.read_failed", error=str(e))

    def _write(self, target: Path, content: str = "", **kw) -> str:
        if target.is_dir():
            return t("file_ops.cannot_write_dir", path=str(target))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return t("file_ops.written", chars=len(content), path=str(target))

    def _append(self, target: Path, content: str = "", **kw) -> str:
        if target.is_dir():
            return t("file_ops.cannot_append_dir", path=str(target))
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a", encoding="utf-8") as f:
            f.write(content)
        return t("file_ops.appended", chars=len(content), path=str(target))

    def _delete(self, target: Path, **kw) -> str:
        if not target.exists():
            return t("file_ops.file_not_found", path=str(target))
        if target.is_dir():
            shutil.rmtree(target)
            return t("file_ops.dir_deleted", path=str(target))
        target.unlink()
        return t("file_ops.file_deleted", path=str(target))

    def _list_dir(self, target: Path, **kw) -> str:
        if not target.exists():
            return t("file_ops.dir_not_found", path=str(target))
        if not target.is_dir():
            return t("file_ops.not_a_dir", path=str(target))
        items = []
        for p in sorted(target.iterdir())[:50]:
            prefix = "📁" if p.is_dir() else "📄"
            size = ""
            if p.is_file():
                s = p.stat().st_size
                size = f" ({s} bytes)" if s < 1024 else f" ({s // 1024}KB)"
            items.append(f"  {prefix} {p.name}{size}")
        return t("file_ops.dir_contents", path=str(target)) + "\n" + "\n".join(items)

    def _rename(self, target: Path, new_name: str = "", **kw) -> str:
        if not target.exists():
            return t("file_ops.file_not_found", path=str(target))
        if not new_name:
            return t("file_ops.specify_new_name")
        dest = target.parent / new_name
        if dest.exists():
            return t("file_ops.target_name_exists", path=str(dest))
        target.rename(dest)
        return t("file_ops.renamed", old=str(target), new=str(dest))

    def _copy(self, target: Path, new_name: str = "", **kw) -> str:
        if not target.exists():
            return t("file_ops.file_not_found", path=str(target))
        dest_name = new_name or f"{target.name}.copy"
        dest = target.parent / dest_name
        if dest.exists():
            return t("file_ops.target_exists", path=str(dest))
        if target.is_dir():
            shutil.copytree(target, dest)
        else:
            shutil.copy2(target, dest)
        return t("file_ops.copied", old=str(target), new=str(dest))

    def _exists(self, target: Path, **kw) -> str:
        if target.exists():
            kind = t("file_ops.dir") if target.is_dir() else t("file_ops.file")
            return t("file_ops.exists", kind=kind, path=str(target))
        return t("file_ops.file_not_found", path=str(target))

    def _size(self, target: Path, **kw) -> str:
        if not target.exists():
            return t("file_ops.file_not_found", path=str(target))
        if target.is_dir():
            total = sum(f.stat().st_size for f in target.rglob("*") if f.is_file())
            return t("file_ops.dir_size", path=str(target), size=f"{total} bytes ({total // 1024}KB)")
        s = target.stat().st_size
        return t("file_ops.file_size", path=str(target), size=f"{s} bytes ({s // 1024}KB)")


__all__ = ["FileOperationHandler"]
