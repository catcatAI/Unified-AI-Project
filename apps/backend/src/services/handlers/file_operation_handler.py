"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
FileOperationHandler — processes file_op intents from ChatService dispatch.
Supports: create, read, write, delete, list, rename, move, copy, exists, size, append.

Note: "move" moves a file INTO a target directory. "rename" renames within the same directory.
"""

import asyncio
import logging
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from core.i18n.i18n_manager import t
from core.utils import safe_error as _safe_error

logger = logging.getLogger(__name__)

_ACTION_KEYWORDS = (
    ("read", ("讀取", "读取", "打開", "打开", "查看", "read", "open")),
    ("delete", ("刪除", "删除", "移除", "delete", "remove")),
    ("create", ("建立", "創建", "创建", "新建", "create")),
    ("write", ("寫入", "写入", "覆寫", "覆写", "保存", "write", "save")),
    ("append", ("附加", "追加", "append")),
    ("rename", ("重新命名", "重命名", "改名", "rename")),
    ("move", ("移動", "移动", "搬移", "move")),
    ("copy", ("複製", "复制", "copy")),
    ("list", ("列出", "列表", "查看目錄", "查看目录", "list", "ls")),
    ("size", ("大小", "size")),
    ("exists", ("存在", "exists")),
)


def _looks_like_path(tok: str) -> bool:
    """Heuristic: does this token look like a file path?"""
    if not tok:
        return False
    lower = tok.lower()
    if any(
        lower.startswith(k)
        for k in ("read", "write", "create", "delete", "remove", "copy", "move", "rename", "list", "append", "open", "save", "文件", "檔案", "目錄", "內容")
    ):
        return False
    return (
        "/" in tok
        or "\\" in tok
        or tok.startswith(".")
        or tok.startswith("~")
        or bool(re.search(r"\.\w{1,8}$", tok))
    )


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
        logger.warning("Path resolution failed: %s", e, exc_info=True)
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
        # Runtime dispatch (ModelBus adapter) passes the raw user text as
        # ``_text`` — parse action/path/content from it when no structured
        # params were supplied (C5: previously this crashed with
        # "'str' object has no attribute 'get'" on every chat dispatch).
        if "_text" in operation:
            parsed = self._parse_text_request(str(operation.get("_text", "")))
            for k, v in parsed.items():
                operation.setdefault(k, v)
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
            "move": self._move,
            "copy": self._copy,
            "exists": self._exists,
            "size": self._size,
            "append": self._append,
        }
        handler_fn = handlers.get(action)
        if not handler_fn:
            return t(
                "file_ops.unsupported_action", action=action, actions=", ".join(handlers.keys())
            )

        try:
            return await asyncio.to_thread(handler_fn, target, content=content, new_name=new_name)
        except PermissionError:
            return t("file_ops.permission_denied", path=path_str)
        except Exception as e:
            logger.error(f"FileOperationHandler error: {e}", exc_info=True)
            return t("file_ops.operation_failed", error=_safe_error(e))

    # ------------------------------------------------------------------
    # Natural-language request parsing (best-effort)
    # ------------------------------------------------------------------

    def _parse_text_request(self, text: str) -> Dict[str, str]:
        """Parse a natural-language file request into structured params.

        Understands common Chinese/English phrasings such as:
          "刪除 /tmp/a.txt" / "讀取 test.txt" / "寫入 hello.txt 內容是 ..."
          "建立 notes/hello.txt" / "重新命名 a.txt 為 b.txt" / "移動 a.txt 到 dir"
        """
        import re

        params: Dict[str, str] = {}
        if not text:
            return params
        lower = text.lower()

        # 1. Action keywords
        for action, kws in _ACTION_KEYWORDS:
            if any(k in lower for k in kws):
                params["action"] = action
                break

        # 2. Content (write/append): everything after a content marker
        content = None
        for sep in ("內容是", "内容是", "內容:", "内容:", "content:", "with content"):
            if sep in lower:
                _, after = text.split(sep, 1)
                if after.strip():
                    content = after.strip().strip('"\'')
                break
        if content is not None:
            params["content"] = content

        # 3. Path: first path-like token, excluding action keywords and the
        #    content portion.
        work = text
        if content is not None:
            for sep in ("內容是", "内容是", "內容:", "内容:", "content:", "with content"):
                if sep in work:
                    work = work.split(sep, 1)[0]
                    break
        for tok in re.findall(r"[^\s`'\"，。！？!?,;；]+(?:\.[^\s`'\"，。！？!?,;；]+)?", work):
            t = tok.strip("`'\"")
            if _looks_like_path(t):
                params["path"] = t
                break

        # 4. Target name (rename/move): token after 為/为/成/到/to
        if params.get("action") in ("rename", "move"):
            for sep in ("為", "为", "成", "到", " to "):
                if sep in text:
                    rest = text.split(sep, 1)[1].strip()
                    m = re.search(r"[^\s`'\"，。！？!?,;；]+", rest)
                    if m:
                        params["new_name"] = m.group(0).strip("`'\"")
                        break

        return params

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
            items = [
                f"  {'📁' if p.is_dir() else '📄'} {p.name}" for p in sorted(target.iterdir())[:50]
            ]
            return t("file_ops.dir_contents", path=str(target)) + "\n" + "\n".join(items)
        try:
            text = target.read_text(encoding="utf-8", errors="replace")
            if len(text) > 4000:
                text = text[:4000] + "\n... (已截斷)"
            return t("file_ops.file_contents", path=str(target)) + "\n" + text
        except Exception as e:
            logger.warning("File read failed: %s", _safe_error(e), exc_info=True)
            return t("file_ops.read_failed", error=_safe_error(e))

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

    def _move(self, target: Path, new_name: str = "", **kw) -> str:
        """Move a file INTO a target directory.

        Args:
            target: Source file path.
            new_name: Target directory path (the directory to move into).

        Returns:
            Status message string.
        """
        if not target.exists():
            return t("file_ops.file_not_found", path=str(target))
        if target.is_dir():
            return t("file_ops.cannot_move_dir", path=str(target))
        if not new_name:
            return t("file_ops.specify_target_dir")
        dest_dir = Path(new_name)
        if not dest_dir.is_dir():
            # Maybe the user gave a destination filename, not a directory
            dest = dest_dir
        else:
            dest = dest_dir / target.name
        if dest.exists():
            return t("file_ops.target_name_exists", path=str(dest))
        # Validate both source and destination are safe BEFORE creating dirs
        if not _is_safe_path(dest):
            return t("file_ops.unsafe_path", path=str(dest))
        # Only create parent dirs after validation
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(target), str(dest))
        return t("file_ops.moved", src=str(target), dst=str(dest))

    def _rename(self, target: Path, new_name: str = "", **kw) -> str:
        if not target.exists():
            return t("file_ops.file_not_found", path=str(target))
        if not new_name:
            return t("file_ops.specify_new_name")
        dest = target.parent / new_name
        if not _is_safe_path(dest):
            return t("file_ops.unsafe_path", path=str(dest))
        if dest.exists():
            return t("file_ops.target_name_exists", path=str(dest))
        target.rename(dest)
        return t("file_ops.renamed", old=str(target), new=str(dest))

    def _copy(self, target: Path, new_name: str = "", **kw) -> str:
        if not target.exists():
            return t("file_ops.file_not_found", path=str(target))
        dest_name = new_name or f"{target.name}.copy"
        dest = target.parent / dest_name
        if not _is_safe_path(dest):
            return t("file_ops.unsafe_path", path=str(dest))
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
            return t(
                "file_ops.dir_size", path=str(target), size=f"{total} bytes ({total // 1024}KB)"
            )
        s = target.stat().st_size
        return t("file_ops.file_size", path=str(target), size=f"{s} bytes ({s // 1024}KB)")


__all__ = ["FileOperationHandler"]
