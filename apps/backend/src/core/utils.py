#!/usr/bin/env python3
"""
Angela AI - Common Utilities
公共工具模块

提供项目中常用的工具函数和类，减少代码重复。
"""

import hashlib
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def safe_error(e: Exception, max_length: int = 200) -> str:
    """Sanitize exception message for user-facing output.

    Strips system file paths, truncates long messages, and removes
    potentially sensitive information from exception text.

    Args:
        e: The exception to sanitize.
        max_length: Maximum length of the returned message.

    Returns:
        A sanitized, user-safe error string.
    """
    msg = str(e)
    # Strip Windows drive-letter paths (C:\...)
    msg = re.sub(r'[A-Za-z]:\\[^\s,"\')]*', '<path>', msg)
    # Strip Unix absolute paths
    msg = re.sub(r'/[/A-Za-z0-9._-]+', '<path>', msg)
    # Strip potential API keys and tokens (hex strings > 20 chars)
    msg = re.sub(r'[A-Za-z0-9_-]{20,}', '<token>', msg)
    # Truncate long messages
    if len(msg) > max_length:
        msg = msg[:max_length] + '...'
    return msg


def sha256_hash(data: Union[str, bytes]) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def md5_hash(data: Union[str, bytes]) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.md5(data).hexdigest()


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + suffix


def safe_json_parse(text: str, default: Any = None) -> Any:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def extract_urls(text: str) -> List[str]:
    pattern = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[-\w/?%&=+#]*"
    return re.findall(pattern, text)


def extract_emails(text: str) -> List[str]:
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return re.findall(pattern, text)


def now_timestamp() -> float:
    return time.time()


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f}m"
    hours = minutes / 60
    return f"{hours:.1f}h"


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def chunk_list(items: List[Any], chunk_size: int = 100) -> List[List[Any]]:
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


class Timer:
    """Simple context manager / utility for timing operations."""

    def __init__(self, label: str = ""):
        self.label = label
        self.start_time: float = 0.0
        self.elapsed: float = 0.0

    def __enter__(self) -> Any:
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args) -> None:
        self.elapsed = time.perf_counter() - self.start_time
        if self.label:
            logger.debug(f"Timer [{self.label}]: {self.elapsed:.4f}s")

    def get_elapsed_ms(self) -> float:
        return self.elapsed * 1000


# ═══════════════════════════════════════════════
# Keyword matching (word-boundary-aware for English, density-gated)
# ═══════════════════════════════════════════════

_ENG_WORD_BOUNDARY = re.compile(r'(?<![a-zA-Z])|(?![a-zA-Z])')


def _match_english_kw(text: str, keyword: str) -> bool:
    """English keyword with word-boundary check: 'cat' won't match 'category'."""
    pattern = re.compile(rf'(?<![a-zA-Z]){re.escape(keyword)}(?![a-zA-Z])', re.IGNORECASE)
    return bool(pattern.search(text))


def _match_cjk_kw(text: str, keyword: str) -> bool:
    """CJK keyword: substring match (word boundaries don't apply)."""
    return keyword in text


def any_keyword(text: str, keywords: tuple) -> bool:
    """Match any keyword — English gets word boundaries, CJK uses substring."""
    for kw in keywords:
        if not kw:
            continue
        if kw.isascii() and kw.isalpha():
            if _match_english_kw(text, kw):
                return True
        else:
            if _match_cjk_kw(text, kw):
                return True
    return False


def all_keywords(text: str, keywords: tuple) -> bool:
    """All keywords must match — English gets word boundaries, CJK uses substring."""
    for kw in keywords:
        if not kw:
            continue
        if kw.isascii() and kw.isalpha():
            if not _match_english_kw(text, kw):
                return False
        else:
            if not _match_cjk_kw(text, kw):
                return False
    return True


__all__ = [
    "safe_error",
    "sha256_hash",
    "md5_hash",
    "truncate_text",
    "safe_json_parse",
    "extract_urls",
    "extract_emails",
    "now_timestamp",
    "format_duration",
    "deep_merge",
    "chunk_list",
    "Timer",
    "any_keyword",
    "all_keywords",
]
