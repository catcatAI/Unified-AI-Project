"""Tests for core.utils — hash, text, json, timing utilities"""
import time
from typing import Any, Dict

import pytest
from core.utils import (
    Timer,
    chunk_list,
    deep_merge,
    extract_emails,
    extract_urls,
    format_duration,
    md5_hash,
    now_timestamp,
    safe_json_parse,
    sha256_hash,
    truncate_text,
)


class TestHashFunctions:
    def test_sha256_hash_string(self):
        result = sha256_hash("hello")
        assert isinstance(result, str)
        assert len(result) == 64

    def test_sha256_hash_bytes(self):
        result = sha256_hash(b"hello")
        assert result == sha256_hash("hello")

    def test_sha256_hash_different(self):
        assert sha256_hash("a") != sha256_hash("b")

    def test_md5_hash_string(self):
        result = md5_hash("hello")
        assert isinstance(result, str)
        assert len(result) == 32

    def test_md5_hash_bytes(self):
        result = md5_hash(b"hello")
        assert result == md5_hash("hello")


class TestTextFunctions:
    def test_truncate_text_short(self):
        assert truncate_text("hello", 10) == "hello"

    def test_truncate_text_long(self):
        result = truncate_text("hello world", 5)
        assert result == "he..." or result == "hello..."

    def test_truncate_text_custom_suffix(self):
        result = truncate_text("hello world", 5, " [..]")
        assert result == "hello [..]"

    def test_truncate_text_exact(self):
        assert truncate_text("hello", 5) == "hello"


class TestJsonFunctions:
    def test_safe_json_parse_valid(self):
        assert safe_json_parse('{"a": 1}') == {"a": 1}

    def test_safe_json_parse_invalid(self):
        assert safe_json_parse("not json") is None

    def test_safe_json_parse_custom_default(self):
        assert safe_json_parse("not json", {}) == {}

    def test_safe_json_parse_int(self):
        assert safe_json_parse("42") == 42

    def test_safe_json_parse_list(self):
        assert safe_json_parse("[1,2,3]") == [1, 2, 3]


class TestExtractionFunctions:
    def test_extract_urls_simple(self):
        urls = extract_urls("visit https://example.com/path?q=1#frag")
        assert "https://example.com/path?q=1#frag" in urls

    def test_extract_urls_none(self):
        assert extract_urls("no urls here") == []

    def test_extract_emails_simple(self):
        emails = extract_emails("contact test@example.com for info")
        assert "test@example.com" in emails

    def test_extract_emails_none(self):
        assert extract_emails("no emails here") == []


class TestTimeFunctions:
    def test_now_timestamp(self):
        ts = now_timestamp()
        assert isinstance(ts, float)
        assert ts > 1_600_000_000

    def test_format_duration_seconds(self):
        assert format_duration(30) == "30.0s"

    def test_format_duration_minutes(self):
        assert format_duration(150) == "2.5m"

    def test_format_duration_hours(self):
        assert format_duration(7200) == "2.0h"

    def test_format_duration_zero(self):
        assert format_duration(0) == "0.0s"


class TestDictFunctions:
    def test_deep_merge_simple(self):
        assert deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    def test_deep_merge_nested(self):
        result = deep_merge({"a": {"x": 1}}, {"a": {"y": 2}})
        assert result == {"a": {"x": 1, "y": 2}}

    def test_deep_merge_override(self):
        result = deep_merge({"a": 1, "b": 2}, {"b": 3})
        assert result == {"a": 1, "b": 3}

    def test_deep_merge_overwrite_nested(self):
        result = deep_merge({"a": {"x": 1}}, {"a": "string"})
        assert result == {"a": "string"}

    def test_deep_merge_empty(self):
        assert deep_merge({}, {"a": 1}) == {"a": 1}
        assert deep_merge({"a": 1}, {}) == {"a": 1}

    def test_deep_merge_immutability(self):
        base = {"a": 1}
        deep_merge(base, {"b": 2})
        assert base == {"a": 1}


class TestListFunctions:
    def test_chunk_list_normal(self):
        assert chunk_list([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]

    def test_chunk_list_exact(self):
        assert chunk_list([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]

    def test_chunk_list_smaller(self):
        assert chunk_list([1, 2], 5) == [[1, 2]]

    def test_chunk_list_empty(self):
        assert chunk_list([]) == []

    def test_chunk_list_default_size(self):
        items = list(range(250))
        chunks = chunk_list(items)
        assert len(chunks) == 3
        assert len(chunks[0]) == 100
        assert len(chunks[1]) == 100
        assert len(chunks[2]) == 50


class TestTimer:
    def test_timer_context_manager(self):
        with Timer() as t:
            time.sleep(0.01)
        assert t.elapsed >= 0.01

    def test_timer_get_elapsed_ms(self):
        t = Timer()
        t.elapsed = 0.5
        assert t.get_elapsed_ms() == 500.0

    def test_timer_label(self):
        t = Timer("test_op")
        assert t.label == "test_op"

    def test_timer_no_label(self):
        t = Timer()
        assert t.label == ""
