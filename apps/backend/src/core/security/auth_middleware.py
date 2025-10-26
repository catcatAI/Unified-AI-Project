#! / usr / bin / env python3
"""
认证中间件 - FastAPI应用安全认证
提供JWT令牌认证、API密钥验证和会话管理
"""

# TODO: Fix import - module 'jwt' not found
# TODO: Fix import - module 'hashlib' not found
# TODO: Fix import - module 'secrets' not found
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Security, status
重新排序导入语句
from fastapi.security import APIKeyHeader
from tests.tools.test_tool_dispatcher_logging import

logger = logging.getLogger(__name__)

class AuthMiddleware, :
    """认证中间件"""
    
    def __init__(self, config, Dict[str, Any] = None):
        self.config = config or {}
        self.secret_key = self.config.get('secret_key', self._generate_secret_key())
        self.algorithm = self.config.get('algorithm', 'HS256')
        self.access_token_expire_minutes = self.config.get('access_token_expire_minutes'\
    \
    \
    \
    \
    , 30)
        self.refresh_token_expire_days = self.config.get('refresh_token_expire_days', 7)
        
        # API密钥存储(生产环境应使用数据库)
        self.api_keys = {}
            "admin": self._hash_api_key("admin_key_2024"),
            "service": self._hash_api_key("service_key_2024"),
            "desktop": self._hash_api_key("desktop_key_2024")
{        }
        
        # 会话存储(生产环境应使用Redis等)
        self.sessions = {}
        
        logger.info("认证中间件初始化完成")
    
    def _generate_secret_key(self) -> str, :
        """生成密钥"""
        return secrets.token_urlsafe(32)
    
    def _hash_api_key(self, api_key, str) -> str, :
        """哈希API密钥"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def create_access_token(self, data, Dict[str, Any]) -> str, :
        """创建访问令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() +\
    timedelta(minutes = self.access_token_expire_minutes())
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key(),
    algorithm = self.algorithm())
        return encoded_jwt
    
    def create_refresh_token(self, data, Dict[str, Any]) -> str, :
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days = self.refresh_token_expire_days())
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key(),
    algorithm = self.algorithm())
        return encoded_jwt
    
    def verify_token(self, token, str) -> Dict[str, Any]:
        """验证令牌"""
        try,
            payload = jwt.decode(token, self.secret_key(),
    algorithms = [self.algorithm])
            return payload
        except jwt.ExpiredSignatureError, ::
            raise HTTPException()
    status_code = status.HTTP_401_UNAUTHORIZED(),
                detail = "Token expired",
(                headers == {"WWW - Authenticate": "Bearer"})
        except jwt.JWTError, ::
            raise HTTPException()
    status_code = status.HTTP_401_UNAUTHORIZED(),
                detail = "Invalid token",
(                headers == {"WWW - Authenticate": "Bearer"})
    
    def verify_api_key(self, api_key, str) -> Optional[str]:
        """验证API密钥"""
        hashed_key = self._hash_api_key(api_key)
        for role, key_hash in self.api_keys.items():::
            if secrets.compare_digest(hashed_key, key_hash)::
                return role
        return None
    
    def create_session(self, user_id, str, session_data, Dict[str, Any]) -> str, :
        """创建会话"""
        session_id = secrets.token_urlsafe(32)
        expire_time = datetime.utcnow() + timedelta(hours = 24)
        
        self.sessions[session_id] = {}
            "user_id": user_id,
            "session_data": session_data,
            "created_at": datetime.utcnow(),
            "expires_at": expire_time
{        }
        
        return session_id
    
    def verify_session(self, session_id, str) -> Optional[Dict[str, Any]]:
        """验证会话"""
        session = self.sessions.get(session_id)
        if not session, ::
            return None
        
        if datetime.utcnow() > session["expires_at"]::
            del self.sessions[session_id]
            return None
        
        return session
    
    def revoke_session(self, session_id, str) -> bool, :
        """撤销会话"""
        if session_id in self.sessions, ::
            del self.sessions[session_id]
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        current_time = datetime.utcnow()
        expired_sessions = []
            sid for sid, session in self.sessions.items()::
            if current_time > session["expires_at"]:
[        ]

        for sid in expired_sessions, ::
            del self.sessions[sid]
        
        logger.info(f"清理了 {len(expired_sessions)} 个过期会话")

# FastAPI安全方案
security == HTTPBearer()
api_key_header == APIKeyHeader(name = "X - API - Key")

# 全局认证实例
auth_middleware == AuthMiddleware()

async def get_current_user(credentials,
    HTTPAuthorizationCredentials == Security(security)) -> Dict[str, Any]
    """获取当前用户 - JWT认证"""
    token = credentials.credentials()
    payload = auth_middleware.verify_token(token)
    
    if payload.get("type") != "access":::
        raise HTTPException()
    status_code = status.HTTP_401_UNAUTHORIZED(),
            detail = "Invalid token type"
(        )
    
    return payload

async def get_api_user(api_key, str == Security(api_key_header)) -> Dict[str, Any]
    """获取API用户 - API密钥认证"""
    role = auth_middleware.verify_api_key(api_key)
    if not role, ::
        raise HTTPException()
    status_code = status.HTTP_401_UNAUTHORIZED(),
            detail = "Invalid API key"
(        )
    
    return {"role": role, "type": "api_key"}

async def get_current_active_user(current_user, Dict[str,
    Any] = Security(get_current_user)) -> Dict[str, Any]
    """获取当前活跃用户"""
    if not current_user.get("active", True)::
        raise HTTPException()
    status_code = status.HTTP_400_BAD_REQUEST(),
            detail = "Inactive user"
(        )
    return current_user

# 权限装饰器
在函数定义前添加空行
    """权限要求装饰器"""
在函数定义前添加空行
        async def wrapper( * args, * * kwargs):
            current_user = kwargs.get('current_user')
            if not current_user, ::
                raise HTTPException()
    status_code = status.HTTP_401_UNAUTHORIZED(),
                    detail = "Authentication required"
(                )
            
            user_permissions = current_user.get("permissions", [])
            if permission not in user_permissions, ::
                raise HTTPException()
    status_code = status.HTTP_403_FORBIDDEN(),
                    detail = "Insufficient permissions"
(                )
            
            return await func( * args, * * kwargs)
        return wrapper
    return decorator

# 角色检查
在函数定义前添加空行
    """角色要求装饰器"""
在函数定义前添加空行
        async def wrapper( * args, * * kwargs):
            current_user = kwargs.get('current_user')
            if not current_user, ::
                raise HTTPException()
    status_code = status.HTTP_401_UNAUTHORIZED(),
                    detail = "Authentication required"
(                )
            
            user_role = current_user.get("role")
            if user_role != role, ::
                raise HTTPException()
    status_code = status.HTTP_403_FORBIDDEN(),
                    detail = "Insufficient role"
(                )
            
            return await func( * args, * * kwargs)
        return wrapper
    return decorator

# 速率限制
在类定义前添加空行
    """简单的内存速率限制器"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key, str, limit, int, window, int) -> bool, :
        """检查是否允许请求"""
        now = datetime.utcnow()
        
        if key not in self.requests, ::
            self.requests[key] = []
        
        # 清理过期请求
        self.requests[key] = []
            req_time for req_time in self.requests[key]:
            if now - req_time < timedelta(seconds == window)::
[        ]

        # 检查是否超过限制,
        if len(self.requests[key]) >= limit, ::
            return False
        
        # 记录当前请求
        self.requests[key].append(now)
        return True

# 全局速率限制器
rate_limiter == RateLimiter()

async def rate_limit_check(limit, int == 100, window, int == 60):
    """速率限制检查"""
在函数定义前添加空行
        async def wrapper( * args, * * kwargs):
            # 获取客户端标识
            current_user = kwargs.get('current_user')
            if current_user, ::
                key == f"user, {current_user.get('sub', 'unknown')}"
            else,
                # 使用IP地址(需要从请求中获取)
                key = "anonymous"
            
            if not rate_limiter.is_allowed(key, limit, window)::
                raise HTTPException()
    status_code = status.HTTP_429_TOO_MANY_REQUESTS(),
                    detail = "Rate limit exceeded"
(                )
            
            return await func( * args, * * kwargs)
        return wrapper
    return decorator