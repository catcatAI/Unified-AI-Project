# =============================================================================
# ANGELA-MATRIX: L1-L6[全層] αβγδεθζη [A] L2+
# =============================================================================
#
# 職責: 安全層掛載（§11.3 #10 步驟 C5）— AuthMiddleware + ContentFilter
#       以 ASGI middleware 形式掛到 setup_middleware() 下層入口。
# 維度: η 執行維度（資源入口安全）+ δ 精神維度（內容健康）
# 安全: Key A (後端控制)
#
# =============================================================================

"""安全層掛載（步驟 C5 / §11.3 #10）。

`SecurityFilterMiddleware` 是一個 Starlette/ASGI middleware，在請求進入
路由前（下層入口）做兩件事：

1. **Auth guard**：當 `AUTH_REQUIRED_PREFIXES` 命中且 config 啟用 auth 時，
   校驗 Authorization header（Bearer token / API key）；未授權回 401。
   —— 預設 **關閉**（`enable_auth` 預設 False），不破壞現有公開行為。
2. **內容過濾**：對回傳給客戶端的文字欄位（`text/plain`、JSON 的 string
   values 深層）跑 `ContentFilter.filter_content`，命中的風險內容被遮罩。

掛載方式（由 `setup_middleware()` 呼叫）：

    from core.backbone.security import SecurityFilterMiddleware, build_security_layer
    layer = build_security_layer()
    app.add_middleware(SecurityFilterMiddleware, layer=layer)
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 需要 auth 校驗的路由前綴（僅當 enable_auth 時生效）
AUTH_REQUIRED_PREFIXES: tuple = ("/api/v1/auth", "/api/v1/user", "/api/v1/account")

# 遮罩敏感 token 欄位（ContentFilter 補充，防響應外洩 token）
SENSITIVE_RESPONSE_FIELDS: tuple = (
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "secret",
    "client_secret",
)


class SecurityLayer:
    """組合 AuthMiddleware + ContentFilter 的安全層。

    Attributes:
        auth: AuthMiddleware 實例（可 None = 停用）。
        content_filter: ContentFilter 實例（可 None = 停用）。
        enable_auth: 是否啟用 auth guard（預設 False，公開模式）。
        mask_sensitive: 是否遮罩響應中的 token 欄位。
    """

    def __init__(
        self,
        auth: Any = None,
        content_filter: Any = None,
        enable_auth: bool = False,
        mask_sensitive: bool = True,
    ) -> None:
        self.auth = auth
        self.content_filter = content_filter
        self.enable_auth = enable_auth
        self.mask_sensitive = mask_sensitive
        self.stats: Dict[str, int] = {
            "requests": 0,
            "auth_checked": 0,
            "auth_rejected": 0,
            "content_filtered": 0,
            "masked_fields": 0,
        }

    # ------------------------------------------------------------------
    # Auth guard
    # ------------------------------------------------------------------
    def auth_header(self, scope: Dict[str, Any]) -> Optional[str]:
        """從 scope headers 提取 Authorization 值。"""
        headers = scope.get("headers") or []
        for key, value in headers:
            if key.lower() == b"authorization":
                return value.decode("utf-8", errors="ignore")
        return None

    def check_authorization(self, scope: Dict[str, Any], path: str) -> Optional[int]:
        """校驗授權；回傳 None=允許，int=HTTP 拒絕狀態碼。

        僅當 `enable_auth` 且 path 命中 `AUTH_REQUIRED_PREFIXES` 時檢查。
        """
        self.stats["requests"] += 1
        if not self.enable_auth or not path.startswith(AUTH_REQUIRED_PREFIXES):
            return None
        if self.auth is None:
            return None
        self.stats["auth_checked"] += 1
        authorization = self.auth_header(scope)
        if not authorization:
            self.stats["auth_rejected"] += 1
            return 401
        token = authorization
        if authorization.lower().startswith("bearer "):
            token = authorization[len("bearer ") :].strip()
        # 嘗試 JWT 驗證；失敗再試 API key
        try:
            payload = self.auth.verify_token(token)
            if payload is not None:
                return None
        except Exception as exc:
            logger.debug("SecurityLayer auth verify failed: %s", exc)
        try:
            if self.auth.verify_api_key(token) is not None:
                return None
        except Exception as exc:
            logger.debug("SecurityLayer api-key verify failed: %s", exc)
        self.stats["auth_rejected"] += 1
        return 401

    # ------------------------------------------------------------------
    # 內容過濾
    # ------------------------------------------------------------------
    def filter_text(self, text: str) -> str:
        """對單段文字跑 ContentFilter；風險內容以案由摘要遮罩。"""
        if not self.content_filter or not text:
            return text
        try:
            result = self.content_filter.filter_content(text)
            action = getattr(result, "action", None)
            action_value = getattr(action, "value", None) or str(action or "")
            if action_value in ("block", "sanitize"):
                self.stats["content_filtered"] += 1
                issues = result.issues or []
                reasons = list({str(i.get("type", "risk")) for i in issues})
                masked = getattr(result, "sanitized_content", None)
                if masked:
                    return masked
                return f"[風險內容已阻擋:{','.join(reasons)}]"
        except Exception as exc:
            logger.debug("SecurityLayer filter failed: %s", exc, exc_info=True)
        return text

    def filter_json(self, data: Any) -> Any:
        """深層過濾 JSON 結構中的字串值（掩飾/sanitize）。"""
        if isinstance(data, dict):
            out: Dict[str, Any] = {}
            for key, value in data.items():
                if isinstance(value, str):
                    if self.mask_sensitive and any(
                        s in key.lower() for s in SENSITIVE_RESPONSE_FIELDS
                    ):
                        self.stats["masked_fields"] += 1
                        out[key] = "[MASKED]"
                    else:
                        out[key] = self.filter_text(value)
                else:
                    out[key] = self.filter_json(value)
            return out
        if isinstance(data, list):
            return [self.filter_json(item) for item in data]
        return data

    def filter_response_bytes(self, body: bytes, content_type: str) -> bytes:
        """對回應 body 做文字過濾。回傳過濾後 bytes。"""
        try:
            if not body:
                return body
            ctype = content_type.split(";")[0].strip().lower()
            if ctype == "application/json":
                text = body.decode("utf-8", errors="ignore")
                try:
                    parsed = json.loads(text)
                    filtered = self.filter_json(parsed)
                    return json.dumps(filtered, ensure_ascii=False).encode("utf-8")
                except ValueError:
                    return self.filter_text(text).encode("utf-8", errors="ignore")
            if ctype in ("text/plain", "text/html", "text/markdown", "text/xml"):
                text = body.decode("utf-8", errors="ignore")
                return self.filter_text(text).encode("utf-8", errors="ignore")
        except Exception as exc:
            logger.debug("SecurityLayer response filter failed: %s", exc, exc_info=True)
        return body


def build_security_layer(
    config: Optional[Dict[str, Any]] = None,
    enable_auth: Optional[bool] = None,
) -> SecurityLayer:
    """建立安全層（惰性載入 AuthMiddleware + ContentFilter）。

    Args:
        config: 安全配置 dict。支援 `enable_auth`。
        enable_auth: 覆寫 auth 開關（優先於 config）。
    """
    cfg = config or {}
    auth_enabled = cfg.get("enable_auth", False) if enable_auth is None else enable_auth
    auth_instance = None
    content_instance = None
    try:
        from core.security.auth_middleware import get_auth_middleware

        auth_instance = get_auth_middleware(cfg.get("auth_config"))
    except Exception as exc:
        logger.debug("SecurityLayer auth unavailable: %s", exc)
    try:
        from security.content_filter import ContentFilter

        content_instance = ContentFilter(cfg.get("content_config") or {})
    except Exception as exc:
        logger.debug("SecurityLayer content filter unavailable: %s", exc)
    return SecurityLayer(
        auth=auth_instance,
        content_filter=content_instance,
        enable_auth=auth_enabled,
        mask_sensitive=cfg.get("mask_sensitive", True),
    )


class SecurityFilterMiddleware:
    """Starlette/ASGI 安全層 middleware。

    掛在 `setup_middleware()` 中（作為最內層，路由前執行）。

        app.add_middleware(SecurityFilterMiddleware, layer=security_layer)
    """

    def __init__(self, app: Any, layer: SecurityLayer) -> None:
        self.app = app
        self.layer = layer

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        reject = self.layer.check_authorization(scope, path)
        if reject is not None:
            body = json.dumps({"detail": "Unauthorized"}).encode("utf-8")
            await send(
                {
                    "type": "http.response.start",
                    "status": reject,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return

        # 包裝 send 以過濾回應 body
        wrapped_send = self._wrap_send(send)
        await self.app(scope, receive, wrapped_send)

    def _wrap_send(self, send: Any) -> Any:
        layer = self.layer

        async def wrapped(message: Dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                self._response_content_type = _content_type_from_message(message)
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                if body and layer.content_filter is not None:
                    ctype = getattr(self, "_response_content_type", "application/octet-stream")
                    filtered = layer.filter_response_bytes(body, ctype)
                    await send({**message, "body": filtered})
                    return
            await send(message)

        return wrapped


def _content_type_from_message(message: Dict[str, Any]) -> str:
    for key, value in message.get("headers", []):
        if key.lower() == b"content-type":
            return value.decode("utf-8", errors="ignore")
    return "application/octet-stream"


__all__ = ["SecurityLayer", "SecurityFilterMiddleware", "build_security_layer"]
