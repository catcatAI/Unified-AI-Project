# =============================================================================
# ANGELA-MATRIX: [L1] [β] [C] [L0]
# =============================================================================
"""
Live-status logger — one updating line for steady-state loops, errors inline.
"""

import sys
import time
import logging
from collections import deque
from typing import Optional

logger = logging.getLogger(__name__)

_last_status: str = ""
_status_ts: float = 0.0
_error_buffer: deque = deque(maxlen=5)
_suppressed: int = 0
_suppressed_key: str = ""


def _clear_line() -> None:
    sys.stderr.write("\r\033[K")


def status(text: str) -> None:
    """Update the single status line in place."""
    global _last_status, _status_ts
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    _clear_line()
    line = f"\r[{ts}] {text}"
    sys.stderr.write(line)
    sys.stderr.flush()
    _last_status = line.strip()
    _status_ts = time.time()


def status_interval(text: str, interval_s: float) -> None:
    """Like status() but shows the update cycle interval."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    _clear_line()
    line = f"\r⌊[{ts}][{interval_s:.1f}s] {text}"
    sys.stderr.write(line)
    sys.stderr.flush()
    global _last_status, _status_ts
    _last_status = line.strip()
    _status_ts = time.time()


def status_done(text: Optional[str] = None) -> None:
    """Finalize the status line and move cursor to next line."""
    global _last_status
    if text:
        _clear_line()
        sys.stderr.write(f"\r{text}\n")
    else:
        sys.stderr.write("\n")
    sys.stderr.flush()
    _last_status = ""


def err(msg: str, key: str = "") -> None:
    """Log an error inline. Suppresses duplicates, caps at 5 visible."""
    global _suppressed, _suppressed_key
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    if key and key == _suppressed_key:
        _suppressed += 1
        return

    if _suppressed > 0:
        _flush_suppressed()

    # Finalize current status line, show error
    if _last_status:
        sys.stderr.write("\n")

    _clear_line()
    sys.stderr.write(f"\r\x1b[31m⚠ [{now}] {msg}\x1b[0m\n")
    sys.stderr.flush()
    logger.error(msg)

    _error_buffer.append(msg)
    _suppressed = 0
    _suppressed_key = key

    # Restore status line if there was one
    if _last_status:
        _clear_line()
        sys.stderr.write(f"\r{_last_status}")
        sys.stderr.flush()


def _flush_suppressed() -> None:
    global _suppressed, _suppressed_key
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    sys.stderr.write(f"\r\x1b[33m  ⚠ [{now}] ... and {_suppressed} more suppressed ({_suppressed_key})\x1b[0m\n")
    _suppressed = 0
    _suppressed_key = ""


def warn(msg: str) -> None:
    """Log a warning inline (always shows)."""
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    if _last_status:
        sys.stderr.write("\n")
    _clear_line()
    sys.stderr.write(f"\r\x1b[33m⚠ [{now}] {msg}\x1b[0m\n")
    sys.stderr.flush()
    if _last_status:
        _clear_line()
        sys.stderr.write(f"\r{_last_status}")
        sys.stderr.flush()


def info(msg: str) -> None:
    """Log an informational message (moves past status line, restores it)."""
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    if _last_status:
        sys.stderr.write("\n")
    _clear_line()
    sys.stderr.write(f"\r[{now}] {msg}\n")
    sys.stderr.flush()
    if _last_status:
        _clear_line()
        sys.stderr.write(f"\r{_last_status}")
        sys.stderr.flush()
