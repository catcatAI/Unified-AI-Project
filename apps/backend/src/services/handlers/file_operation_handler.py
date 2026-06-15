"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
FileOperationHandler — processes file_op intents from ChatService dispatch.
Supports: create, read, write, delete, list, rename, copy, exists, size, append.
"""

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

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
    except Exception:
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
            return "（檔案操作）請指定檔案路徑。"

        target = Path(path_str)
        if not _is_safe_path(target):
            return f"（檔案操作）路徑不安全或不在允許的目錄內：{path_str}"

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
            return f"（檔案操作）不支援的操作：{action}。可用操作：{', '.join(handlers.keys())}"

        try:
            return handler_fn(target, content=content, new_name=new_name)
        except PermissionError:
            return f"（檔案操作）權限不足：{path_str}"
        except Exception as e:
            logger.error(f"FileOperationHandler error: {e}", exc_info=True)
            return f"（檔案操作）操作失敗：{e}"

    def _create(self, target: Path, **kw) -> str:
        if target.exists():
            return f"（檔案操作）檔案已存在：{target}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
        return f"（檔案操作）已建立檔案：{target}"

    def _read(self, target: Path, **kw) -> str:
        if not target.exists():
            return f"（檔案操作）檔案不存在：{target}"
        if target.is_dir():
            items = [f"  {'📁' if p.is_dir() else '📄'} {p.name}" for p in sorted(target.iterdir())[:50]]
            return f"（檔案操作）目錄 {target} 內容：\n" + "\n".join(items)
        try:
            text = target.read_text(encoding="utf-8", errors="replace")
            if len(text) > 4000:
                text = text[:4000] + "\n... (已截斷)"
            return f"（檔案操作）{target} 內容：\n{text}"
        except Exception as e:
            return f"（檔案操作）讀取失敗：{e}"

    def _write(self, target: Path, content: str = "", **kw) -> str:
        if target.is_dir():
            return f"（檔案操作）不能寫入目錄：{target}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"（檔案操作）已寫入 {len(content)} 個字元到 {target}"

    def _append(self, target: Path, content: str = "", **kw) -> str:
        if target.is_dir():
            return f"（檔案操作）不能追加到目錄：{target}"
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a", encoding="utf-8") as f:
            f.write(content)
        return f"（檔案操作）已追加 {len(content)} 個字元到 {target}"

    def _delete(self, target: Path, **kw) -> str:
        if not target.exists():
            return f"（檔案操作）檔案不存在：{target}"
        if target.is_dir():
            shutil.rmtree(target)
            return f"（檔案操作）已刪除目錄：{target}"
        target.unlink()
        return f"（檔案操作）已刪除檔案：{target}"

    def _list_dir(self, target: Path, **kw) -> str:
        if not target.exists():
            return f"（檔案操作）目錄不存在：{target}"
        if not target.is_dir():
            return f"（檔案操作）不是目錄：{target}"
        items = []
        for p in sorted(target.iterdir())[:50]:
            prefix = "📁" if p.is_dir() else "📄"
            size = ""
            if p.is_file():
                s = p.stat().st_size
                size = f" ({s} bytes)" if s < 1024 else f" ({s // 1024}KB)"
            items.append(f"  {prefix} {p.name}{size}")
        return f"（檔案操作）{target} 內容：\n" + "\n".join(items)

    def _rename(self, target: Path, new_name: str = "", **kw) -> str:
        if not target.exists():
            return f"（檔案操作）檔案不存在：{target}"
        if not new_name:
            return "（檔案操作）請指定新名稱。"
        dest = target.parent / new_name
        if dest.exists():
            return f"（檔案操作）目標名稱已存在：{dest}"
        target.rename(dest)
        return f"（檔案操作）已重新命名：{target} → {dest}"

    def _copy(self, target: Path, new_name: str = "", **kw) -> str:
        if not target.exists():
            return f"（檔案操作）檔案不存在：{target}"
        dest_name = new_name or f"{target.name}.copy"
        dest = target.parent / dest_name
        if dest.exists():
            return f"（檔案操作）目標已存在：{dest}"
        if target.is_dir():
            shutil.copytree(target, dest)
        else:
            shutil.copy2(target, dest)
        return f"（檔案操作）已複製：{target} → {dest}"

    def _exists(self, target: Path, **kw) -> str:
        if target.exists():
            kind = "目錄" if target.is_dir() else "檔案"
            return f"（檔案操作）{kind}存在：{target}"
        return f"（檔案操作）檔案不存在：{target}"

    def _size(self, target: Path, **kw) -> str:
        if not target.exists():
            return f"（檔案操作）檔案不存在：{target}"
        if target.is_dir():
            total = sum(f.stat().st_size for f in target.rglob("*") if f.is_file())
            return f"（檔案操作）目錄 {target} 大小：{total} bytes ({total // 1024}KB)"
        s = target.stat().st_size
        return f"（檔案操作）檔案 {target} 大小：{s} bytes ({s // 1024}KB)"


__all__ = ["FileOperationHandler"]
