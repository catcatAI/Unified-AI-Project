"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
Async-safe file I/O helpers for use inside async functions.
Wraps synchronous open/json.dump/json.load/Path I/O in asyncio.to_thread
to avoid blocking the event loop.
"""

import asyncio
import json
from pathlib import Path
from typing import Any


async def async_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Write text content to a file without blocking the event loop."""
    await asyncio.to_thread(path.write_text, content, encoding=encoding)


async def async_read_text(path: Path, encoding: str = "utf-8") -> str:
    """Read text content from a file without blocking the event loop."""
    return await asyncio.to_thread(path.read_text, encoding=encoding)


async def async_json_dump(data: Any, path: str, **kwargs) -> None:
    """Serialize data as JSON and write to a file without blocking."""
    def _dump():
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, **kwargs)
    await asyncio.to_thread(_dump)


async def async_json_load(path: str) -> Any:
    """Read and deserialize a JSON file without blocking the event loop."""
    def _load():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return await asyncio.to_thread(_load)


async def async_write_file(path: str, content: bytes) -> None:
    """Write binary content to a file without blocking the event loop."""
    def _write():
        with open(path, "wb") as f:
            f.write(content)
    await asyncio.to_thread(_write)


__all__ = [
    "async_write_text",
    "async_read_text",
    "async_json_dump",
    "async_json_load",
    "async_write_file",
]
