"""Tests for core/security/auth_middleware.py"""
from unittest.mock import MagicMock, patch

import pytest


class TestAuthMiddleware:
    """Tests for AuthMiddleware"""

    def test_import(self):
        from core.security.auth_middleware import AuthMiddleware
        assert AuthMiddleware is not None

    def test_instantiation_defaults(self):
        from core.security.auth_middleware import AuthMiddleware
        instance = AuthMiddleware(config={})
        assert instance is not None
        assert instance.secret_key is not None
        assert instance.algorithm == "HS256"
        assert instance.access_token_expire_minutes == 30

    def test_instantiation_with_config(self):
        from core.security.auth_middleware import AuthMiddleware
        instance = AuthMiddleware(config={"secret_key": "mykey", "algorithm": "HS512"})
        assert instance.secret_key == "mykey"
        assert instance.algorithm == "HS512"

    def test_generate_api_key(self):
        from core.security.auth_middleware import AuthMiddleware
        instance = AuthMiddleware(config={})
        key = instance.generate_api_key("user123")
        assert key.startswith("ak_")
        assert len(key) > 30

    def test_verify_api_key_valid(self):
        from core.security.auth_middleware import AuthMiddleware
        instance = AuthMiddleware(config={})
        key = instance.generate_api_key("user123", scopes=["read"])
        info = instance.verify_api_key(key)
        assert info is not None
        assert info["user_id"] == "user123"
        assert "read" in info["scopes"]

    def test_verify_api_key_invalid(self):
        from core.security.auth_middleware import AuthMiddleware
        instance = AuthMiddleware(config={})
        info = instance.verify_api_key("invalid_key")
        assert info is None

    def test_revoke_api_key(self):
        from core.security.auth_middleware import AuthMiddleware
        instance = AuthMiddleware(config={})
        key = instance.generate_api_key("user123")
        assert instance.revoke_api_key(key) is True
        assert instance.revoke_api_key("nonexistent") is False

    def test_create_session(self):
        from core.security.auth_middleware import AuthMiddleware
        instance = AuthMiddleware(config={})
        session_id = instance.create_session("user123")
        assert len(session_id) > 20

    def test_verify_session_valid(self):
        from core.security.auth_middleware import AuthMiddleware
        instance = AuthMiddleware(config={})
        session_id = instance.create_session("user123")
        info = instance.verify_session(session_id)
        assert info is not None
        assert info["user_id"] == "user123"

    def test_verify_session_invalid(self):
        from core.security.auth_middleware import AuthMiddleware
        instance = AuthMiddleware(config={})
        info = instance.verify_session("invalid_session")
        assert info is None

    def test_revoke_session(self):
        from core.security.auth_middleware import AuthMiddleware
        instance = AuthMiddleware(config={})
        session_id = instance.create_session("user123")
        assert instance.revoke_session(session_id) is True
        assert instance.revoke_session("nonexistent") is False

    def test_get_stats(self):
        from core.security.auth_middleware import AuthMiddleware
        instance = AuthMiddleware(config={})
        stats = instance.get_stats()
        assert "active_sessions" in stats
        assert "active_api_keys" in stats
        assert stats["algorithm"] == "HS256"
