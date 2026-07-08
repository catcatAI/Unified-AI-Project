"""Tests for shared.security_middleware.SignedCommunicationMiddleware."""

import pytest


class TestSignedCommunicationMiddleware:
    """Verify the security middleware class identity, import, and expected API."""

    def test_class_name_is_signed_not_encrypted(self):
        from shared.security_middleware import SignedCommunicationMiddleware
        assert SignedCommunicationMiddleware.__name__ == "SignedCommunicationMiddleware"

    def test_import_success(self):
        from shared.security_middleware import SignedCommunicationMiddleware
        assert SignedCommunicationMiddleware.__name__ == "SignedCommunicationMiddleware"

    def test_middleware_inherits_base_http_middleware(self):
        from shared.security_middleware import SignedCommunicationMiddleware
        from starlette.middleware.base import BaseHTTPMiddleware
        assert issubclass(SignedCommunicationMiddleware, BaseHTTPMiddleware)

    def test_constructor_accepts_app_and_key_b(self):
        from unittest.mock import MagicMock

        from shared.security_middleware import SignedCommunicationMiddleware
        app = MagicMock()
        instance = SignedCommunicationMiddleware(app, key_b="test-key-b")
        assert instance.key_b == "test-key-b"
        assert hasattr(instance, "dispatch")
