"""Tests for async_io.py — async-safe file I/O helpers."""

import json
import tempfile
from pathlib import Path

import pytest

from core.system.config.async_io import (
    async_json_dump,
    async_json_load,
    async_read_text,
    async_write_file,
    async_write_text,
)


class TestAsyncWriteText:
    async def test_writes_text_content(self, tmp_path):
        path = tmp_path / "hello.txt"
        await async_write_text(path, "Hello World")
        assert path.read_text(encoding="utf-8") == "Hello World"

    async def test_overwrites_existing_file(self, tmp_path):
        path = tmp_path / "overwrite.txt"
        await async_write_text(path, "First")
        await async_write_text(path, "Second")
        assert path.read_text(encoding="utf-8") == "Second"


class TestAsyncReadText:
    async def test_reads_text_content(self, tmp_path):
        path = tmp_path / "readme.txt"
        path.write_text("Line1\nLine2", encoding="utf-8")
        content = await async_read_text(path)
        assert content == "Line1\nLine2"

    async def test_file_not_found_read_text(self, tmp_path):
        path = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            await async_read_text(path)


class TestAsyncJsonDump:
    async def test_dumps_dict(self, tmp_path):
        path = tmp_path / "data.json"
        data = {"name": "Angela", "version": 7.5}
        await async_json_dump(data, str(path))
        with open(path, "r", encoding="utf-8") as f:
            assert json.load(f) == data

    async def test_dumps_list(self, tmp_path):
        path = tmp_path / "list.json"
        data = [1, 2, 3]
        await async_json_dump(data, str(path))
        with open(path, "r", encoding="utf-8") as f:
            assert json.load(f) == data

    async def test_dumps_with_kwargs(self, tmp_path):
        path = tmp_path / "pretty.json"
        data = {"key": "value"}
        await async_json_dump(data, str(path), indent=2)
        content = path.read_text(encoding="utf-8")
        assert '"key"' in content
        assert '  ' in content


class TestAsyncJsonLoad:
    async def test_loads_dict(self, tmp_path):
        path = tmp_path / "load.json"
        data = {"a": 1, "b": 2}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        result = await async_json_load(str(path))
        assert result == data

    async def test_file_not_found(self, tmp_path):
        path = tmp_path / "missing.json"
        with pytest.raises(FileNotFoundError):
            await async_json_load(str(path))

    async def test_invalid_json(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            await async_json_load(str(path))


class TestAsyncWriteFile:
    async def test_writes_binary_content(self, tmp_path):
        path = tmp_path / "binary.bin"
        content = b"\x00\x01\x02\xff"
        await async_write_file(str(path), content)
        assert path.read_bytes() == content

    async def test_empty_bytes(self, tmp_path):
        path = tmp_path / "empty.bin"
        await async_write_file(str(path), b"")
        assert path.read_bytes() == b""
