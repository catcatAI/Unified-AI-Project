# =============================================================================
# ANGELA-MATRIX: L6[执行层] 全层级 [A] L2+
# =============================================================================
#
# 职责: 认证中间件，提供 JWT 令牌认证和 API 密钥验证
# 维度: 涉及所有维度
# 安全: 使用 Key A (后端控制)
# 成熟度: L2+ 等级
#
# =============================================================================

"""认证中间件 - FastAPI应用安全认证
提供JWT令牌认证、API密钥验证和会话管理
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    logging.warning("jwt module not available")

logger = logging.getLogger("auth_middleware")

class AuthMiddleware:
    """认证中间件"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.secret_key = self.config.get('secret_key', self._generate_secret_key())
        self.algorithm = self.config.get('algorithm', 'HS256')
        self.access_token_expire_minutes = self.config.get('access_token_expire_minutes', 30)
        self.refresh_token_expire_days = self.config.get('refresh_token_expire_days', 7)
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def _generate_secret_key(self) -> str:
        """生成密钥"""
        return secrets.token_urlsafe(32)

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """创建访问令牌"""
        if not JWT_AVAILABLE:
            raise ValueError("JWT module not available")

        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode = data.copy()
        to_encode.update({
            'exp': expire,
            'iat': datetime.utcnow()
        })

        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return token

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """创建刷新令牌"""
        if not JWT_AVAILABLE:
            raise ValueError("JWT module not available")

        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode = data.copy()
        to_encode.update({
            'exp': expire,
            'iat': datetime.utcnow(),
            'type': 'refresh'
        })

        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        if not JWT_AVAILABLE:
            return None

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def generate_api_key(self, user_id: str, scopes: List[str] = None) -> str:
        """生成 API 密钥"""
        if scopes is None:
            scopes = ['read', 'write']

        api_key = f"ak_{secrets.token_urlsafe(24)}"

        self.api_keys[api_key] = {
            'user_id': user_id,
            'scopes': scopes,
            'created_at': datetime.utcnow().isoformat(),
            'last_used': None
        }

        logger.info(f"Generated API key for user {user_id}")
        return api_key

    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """验证 API 密钥"""
        if api_key not in self.api_keys:
            return None

        key_info = self.api_keys[api_key]
        key_info['last_used'] = datetime.utcnow().isoformat()

        return key_info

    def create_session(self, user_id: str) -> str:
        """创建会话"""
        session_id = secrets.token_urlsafe(32)

        self.sessions[session_id] = {
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }

        return session_id

    def verify_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """验证会话"""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        session['last_activity'] = datetime.utcnow().isoformat()

        # 检查是否过期
        expires_at = datetime.fromisoformat(session['expires_at'])
        if datetime.utcnow() > expires_at:
            del self.sessions[session_id]
            return None

        return session

    def revoke_session(self, session_id: str) -> bool:
        """撤销会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def revoke_api_key(self, api_key: str) -> bool:
        """撤销 API 密钥"""
        if api_key in self.api_keys:
            del self.api_keys[api_key]
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'active_sessions': len(self.sessions),
            'active_api_keys': len(self.api_keys),
            'algorithm': self.algorithm
        }

# 全局实例
_auth_middleware: Optional[AuthMiddleware] = None

def get_auth_middleware(config: Optional[Dict[str, Any]] = None) -> AuthMiddleware:
    """获取全局认证中间件实例"""
    global _auth_middleware
    if _auth_middleware is None:
        _auth_middleware = AuthMiddleware(config)
    return _auth_middleware