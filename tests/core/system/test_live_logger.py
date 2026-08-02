"""core.system.live_logger 即時日誌測試"""

import io
import sys

from apps.backend.src.core.system.live_logger import (
    err,
    info,
    status,
    status_done,
    status_interval,
    warn,
)


def _capture_stderr(fn, *args):
    old = sys.stderr
    sys.stderr = io.StringIO()
    try:
        fn(*args)
        return sys.stderr.getvalue()
    finally:
        sys.stderr = old


class TestStatusFunctions:
    def test_status_writes_to_stderr(self):
        out = _capture_stderr(status, "hello")
        assert "hello" in out

    def test_status_interval_writes_interval(self):
        out = _capture_stderr(status_interval, "broadcast", 0.5)
        assert "broadcast" in out
        assert "0.5s" in out

    def test_status_done_writes_newline(self):
        out = _capture_stderr(status_done)
        assert "\n" in out

    def test_status_done_with_text(self):
        out = _capture_stderr(status_done, "completed")
        assert "completed" in out


class TestErrorFunctions:
    def test_err_writes_message(self):
        out = _capture_stderr(err, "some error")
        assert "some error" in out

    def test_warn_writes_message(self):
        out = _capture_stderr(warn, "warning text")
        assert "warning text" in out

    def test_info_writes_message(self):
        out = _capture_stderr(info, "info text")
        assert "info text" in out
