"""P8-1a — GoogleDriveHandler unit tests"""


class TestGoogleDriveHandler:

    def setup_method(self):
        from services.handlers.google_drive_handler import GoogleDriveHandler
        self.handler = GoogleDriveHandler()

    def test_handler_instantiated(self):
        assert self.handler is not None
        assert hasattr(self.handler, "handle")

    def test_fmt_size_bytes(self):
        assert self.handler._fmt_size(500) == "500 B"

    def test_fmt_size_kb(self):
        assert "KB" in self.handler._fmt_size(2048)

    def test_fmt_size_mb(self):
        assert "MB" in self.handler._fmt_size(1048576 * 2)

    def test_fmt_size_gb(self):
        assert "GB" in self.handler._fmt_size(1073741824 * 3)
