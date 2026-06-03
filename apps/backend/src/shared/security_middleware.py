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
