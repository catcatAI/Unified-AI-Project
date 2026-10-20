"""
ANGELA-MATRIX: [L2] [β] [C] [L1]
Move a file to the trash instead of destroying it.

WHY this exists
---------------
``file_ops.default.yaml`` declares ``limits.move_to_trash: true`` — a
recoverable delete — but every delete path (the file-operation handler and
the desktop interaction) called ``unlink()``/``rmtree()`` directly, so the
declared behaviour never happened: a mis-interpreted "delete this" destroyed
the file for good.

The trash locations are the platform conventions:

* Linux/BSD — ``~/.local/share/Trash/files`` (+ the ``.trashinfo`` record
  the freedesktop spec asks for)
* macOS — ``~/.Trash``
* Windows — the OS Recycle Bin needs a shell API; the file is moved to
  ``%LOCALAPPDATA%\\AngelaAI\\Trash`` instead, which is recoverable but is
  NOT the Recycle Bin. That difference is deliberate and reported.
"""

from __future__ import annotations

import logging
import os
import shutil
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def trash_dir() -> Path:
    """The platform's trash directory (created on demand)."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "AngelaAI" / "Trash"
    if sys.platform == "darwin":
        return Path.home() / ".Trash"
    return Path.home() / ".local" / "share" / "Trash"


def _unique_name(target: Path, directory: Path) -> Path:
    """A free name inside *directory* for *target* (``x.txt`` → ``x (1).txt``)."""
    candidate = directory / target.name
    if not candidate.exists():
        return candidate
    stem = target.stem
    suffix = target.suffix
    for index in range(1, 1000):
        candidate = directory / f"{stem} ({index}){suffix}"
        if not candidate.exists():
            return candidate
    return directory / f"{stem}-{os.getpid()}{suffix}"


def move_to_trash(target: Path) -> Path | None:
    """Move *target* to the trash; return its new location (None on failure).

    A failure is not fatal for the caller: it can fall back to a hard
    delete, which is what the previous behaviour was.
    """
    try:
        directory = trash_dir()
        files_dir = directory / "files"
        files_dir.mkdir(parents=True, exist_ok=True)
        destination = _unique_name(target, files_dir)
        shutil.move(str(target), str(destination))

        if sys.platform not in ("win32", "darwin"):
            # The freedesktop spec wants a .trashinfo record next to it.
            info_dir = directory / "info"
            info_dir.mkdir(parents=True, exist_ok=True)
            (info_dir / f"{destination.name}.trashinfo").write_text(
                "[Trash Info]\n"
                f"Path={target}\n"
                f"DeletionDate={__import__('datetime').datetime.now().isoformat(timespec='seconds')}\n",
                encoding="utf-8",
            )
        logger.info("Moved %s to trash: %s", target, destination)
        return destination
    except Exception as exc:
        logger.warning("Could not move %s to trash: %s", target, exc)
        return None


__all__ = ["move_to_trash", "trash_dir"]
