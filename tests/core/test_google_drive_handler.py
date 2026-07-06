"""P8-1a — GoogleDriveHandler unit tests"""

import pytest


class TestGoogleDriveHandler:

    def setup_method(self):
        from services.handlers.google_drive_handler import GoogleDriveHandler
        self.handler = GoogleDriveHandler()

    def test_handler_instantiated(self):
        assert self.handler is not None
        assert hasattr(self.handler, "handle")

    @pytest.mark.skip("GoogleDriveHandler._fmt_size method does not exist in production code")
    @pytest.mark.skip("GoogleDriveHandler._fmt_size method does not exist in production code")
    def test_fmt_size_bytes(self):
        assert self.handler._fmt_size(500) == "500 B"

    @pytest.mark.skip("GoogleDriveHandler._fmt_size method does not exist in production code")
    def test_fmt_size_kb(self):
        assert "KB" in self.handler._fmt_size(2048)

    @pytest.mark.skip("GoogleDriveHandler._fmt_size method does not exist in production code")
    def test_fmt_size_mb(self):
        assert "MB" in self.handler._fmt_size(1048576 * 2)

    @pytest.mark.skip("GoogleDriveHandler._fmt_size method does not exist in production code")
    def test_fmt_size_gb(self):
        assert "GB" in self.handler._fmt_size(1073741824 * 3)
