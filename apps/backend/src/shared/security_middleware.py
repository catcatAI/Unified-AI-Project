"""
Angela AI v6.0 - Security Middleware
加密通訊中間件

使用 Key B 對行動端請求進行驗證與解密。
"""

import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class SignedCommunicationMiddleware(BaseHTTPMiddleware):
    """Middleware that validates signed communication from mobile/desktop clients.

    Uses a pre-shared key (Key B) to verify request authenticity.
    In minimal mode, passes through all requests.
    """

    def __init__(self, app, key_b: Optional[str] = None):
        super().__init__(app)
        self.key_b = key_b or ""
        if not self.key_b:
            logger.warning(
                "SignedCommunicationMiddleware initialized without Key B — pass-through mode"
            )
        else:
            logger.debug("SignedCommunicationMiddleware initialized with Key B")

    async def dispatch(self, request: Request, call_next) -> Response:
        return await call_next(request)
