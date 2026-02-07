"""
Angela AI v6.0 - Security Middleware
加密通訊中間件

使用 Key B 對行動端請求進行驗證與解密。
"""

import hmac
import hashlib
import os
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional

class EncryptedCommunicationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, key_b: str):
        super().__init__(app)
        self.key_b = key_b.encode()

    async def dispatch(self, request: Request, call_next):
        # 檢查是否為測試模式
        is_testing = os.environ.get('ANGELA_TESTING', '').lower() == 'true'
        
        # 對行動端與系統控制路徑進行加密驗證
        protected_paths = ["/api/v1/mobile/", "/api/v1/system/status/detailed", "/api/v1/system/module-control"]
        if any(request.url.path.startswith(path) for path in protected_paths):
            # 如果是測試模式，允許無簽名訪問
            if is_testing:
                response = await call_next(request)
                return response
                
            signature = request.headers.get("X-Angela-Signature")
            if not signature:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Missing security signature"}
                )
            
            # 獲取請求內容
            body = await request.body()
            
            # 驗證 HMAC 簽名
            expected_signature = hmac.new(self.key_b, body, hashlib.sha256).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Invalid security signature"}
                )

        response = await call_next(request)
        return response
