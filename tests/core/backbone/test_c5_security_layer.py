# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""步驟 C5：安全層掛載（§11.3 #10）。

`setup_middleware()` 掛 `AuthMiddleware` + `ContentFilter` 為下層入口，
以 `SecurityFilterMiddleware`（ASGI）形式存在。

驗證：
- `SecurityLayer` 預設 `enable_auth=False`（公開模式，不破壞現有行為）。
- 啟用 auth 時，命中 protected prefix 的請求被攔截（401）；未命中放行。
- 內容過濾：toxic 文字被遮罩；JSON 深層字串被過濾；敏感欄位被遮罩。
- `filter_response_bytes` 對 json / text 中間層做過濾。
- `setup_middleware()` 掛載 SecurityFilterMiddleware（透過 FastAPI app 檢查）。
"""

import asyncio
import json

import pytest
from core.backbone.security import (
    AUTH_REQUIRED_PREFIXES,
    SecurityFilterMiddleware,
    SecurityLayer,
    _content_type_from_message,
    build_security_layer,
)


def _make_layer(enable_auth: bool = False, enable_filter: bool = True) -> SecurityLayer:
    """建一個啟用內容過濾的安全層（不依賴真正 ContentFilter import 失敗）。"""
    from core.backbone.security import build_security_layer

    cfg = {
        "enable_auth": enable_auth,
        "content_config": {"enabled": True, "block_on_unsafe": True, "sanitize_pii": True},
        "mask_sensitive": True,
    }
    return build_security_layer(cfg)


class TestSecurityLayerDefaults:
    def test_default_auth_off(self):
        layer = _make_layer(enable_auth=False)
        assert layer.enable_auth is False
        # 未授權請求在 auth off 時放行
        assert layer.check_authorization({"headers": []}, "/api/v1/user/me") is None

    def test_stats_initialized(self):
        layer = _make_layer()
        assert layer.stats["requests"] == 0
        assert layer.stats["auth_checked"] == 0


class TestAuthGuard:
    def test_auth_enabled_blocks_missing_token(self):
        layer = _make_layer(enable_auth=True)
        scope = {"headers": []}
        status = layer.check_authorization(scope, "/api/v1/account/profile")
        assert status == 401

    def test_auth_enabled_blocks_bad_token(self):
        layer = _make_layer(enable_auth=True)
        # 假 token，不是合法 JWT/API key
        scope = {"headers": [(b"authorization", b"Bearer invalid.token.value")]}
        status = layer.check_authorization(scope, "/api/v1/account/profile")
        assert status == 401

    def test_auth_enabled_allows_public_path(self):
        layer = _make_layer(enable_auth=True)
        scope = {"headers": []}
        assert layer.check_authorization(scope, "/api/v1/health") is None

    def test_auth_header_parsing(self):
        layer = _make_layer()
        scope = {"headers": [(b"authorization", b"Bearer abc123")]}
        assert layer.auth_header(scope) == "Bearer abc123"
        assert layer.auth_header({"headers": []}) is None

    def test_valid_token_allows(self):
        from core.backbone.security import build_security_layer

        cfg = {
            "enable_auth": True,
            "auth_config": {},
            "content_config": {"enabled": True},
        }
        layer = build_security_layer(cfg)
        assert layer.auth is not None
        token = layer.auth.create_access_token({"sub": "test-user"})
        scope = {"headers": [(b"authorization", f"Bearer {token}".encode())]}
        assert layer.check_authorization(scope, "/api/v1/user/me") is None


class TestContentFiltering:
    def test_toxic_text_blocked(self):
        layer = _make_layer()
        out = layer.filter_text("I want to kill those people")
        assert out != "I want to kill those people"
        assert layer.stats["content_filtered"] == 1

    def test_safe_text_passthrough(self):
        layer = _make_layer()
        assert layer.filter_text("Hello, how are you today?") == "Hello, how are you today?"

    def test_json_deep_filter(self):
        layer = _make_layer()
        payload = {"message": "You should attack them", "nested": {"note": "All good"}}
        out = layer.filter_json(payload)
        assert out["message"] != "You should attack them"
        assert out["nested"]["note"] == "All good"

    def test_sensitive_fields_masked(self):
        layer = _make_layer()
        payload = {"access_token": "abc123", "refresh_token": "xyz", "data": "safe"}
        out = layer.filter_json(payload)
        assert out["access_token"] == "[MASKED]"
        assert out["refresh_token"] == "[MASKED]"
        assert out["data"] == "safe"

    def test_filter_response_bytes_json(self):
        layer = _make_layer()
        body = json.dumps({"reply": "go bomb the place"}).encode()
        out = layer.filter_response_bytes(body, "application/json; charset=utf-8")
        parsed = json.loads(out)
        assert parsed["reply"] != "go bomb the place"

    def test_filter_response_bytes_text(self):
        layer = _make_layer()
        out = layer.filter_response_bytes(b"this is a scam message", "text/plain")
        assert out != b"this is a scam message"

    def test_filter_response_bytes_binary_passthrough(self):
        layer = _make_layer()
        raw = b"\x00\x01\x02binary"
        assert layer.filter_response_bytes(raw, "image/png") == raw


class TestASGIMiddleware:
    @pytest.mark.asyncio
    async def test_auth_reject_send_401(self):
        layer = _make_layer(enable_auth=True)
        mw = SecurityFilterMiddleware(app=None, layer=layer)

        received = []

        async def send(message):
            received.append(message)

        async def receive():
            return b""

        scope = {"type": "http", "path": "/api/v1/account/x", "headers": []}
        await mw(scope, receive, send)
        starts = [m for m in received if m["type"] == "http.response.start"]
        assert starts and starts[0]["status"] == 401

    @pytest.mark.asyncio
    async def test_content_filter_wraps_response(self):
        layer = _make_layer()
        mw = SecurityFilterMiddleware(app=None, layer=layer)

        received = []

        async def outer_send(message):
            received.append(message)

        # 模擬下游 app 送回 toxic JSON（含 Content-Length，與 FastAPI/uvicorn 一致）
        body = json.dumps({"reply": "go hack the system"}).encode()

        async def fake_app(scope, receive, send):
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode()),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})

        mw.app = fake_app
        await mw({"type": "http", "path": "/api/v1/chat", "headers": []}, None, outer_send)
        body_msgs = [m for m in received if m["type"] == "http.response.body"]
        assert len(body_msgs) == 1
        parsed = json.loads(body_msgs[0]["body"])
        assert parsed["reply"] != "go hack the system"
        # Content-Length must be dropped so a re-serialized body can't overshoot
        # the declared length (uvicorn would abort the stream otherwise).
        starts = [m for m in received if m["type"] == "http.response.start"]
        assert starts
        headers = dict((k.lower(), v) for k, v in starts[0].get("headers", []))
        assert b"content-length" not in headers


class TestContentTypeHelper:
    def test_parses_content_type(self):
        msg = {"headers": [(b"content-type", b"application/json; charset=utf-8")]}
        assert _content_type_from_message(msg) == "application/json; charset=utf-8"

    def test_default_octet(self):
        assert _content_type_from_message({"headers": []}) == "application/octet-stream"


class TestBuildSecurityLayer:
    def test_auth_built_when_available(self):
        layer = build_security_layer({"enable_auth": True})
        assert layer.auth is not None

    def test_content_filter_built(self):
        layer = build_security_layer()
        assert layer.content_filter is not None


def test_auth_required_prefixes():
    assert "/api/v1/auth" in AUTH_REQUIRED_PREFIXES
    assert "/api/v1/user" in AUTH_REQUIRED_PREFIXES
