# =============================================================================
# ANGELA-MATRIX: L6[执行层] 全层级 [A/B/C] L3+
# =============================================================================
#
# 职责: 加密工具模块，提供数据加密、解密和哈希功能
# 维度: 涉及所有维度
# 安全: 使用 Key A (后端控制)、Key B (移动通信)、Key C (桌面同步)
# 成熟度: L3+ 等级
#
# =============================================================================

"""加密工具模块 - 提供数据加密、解密和哈希功能
"""

import base64
import hashlib
import logging
import secrets
from typing import Optional, Dict, Any, Union

try:
    from cryptography.fernet import Fernet
    FERNET_AVAILABLE = True
except ImportError:
    FERNET_AVAILABLE = False
    logging.warning("cryptography module not available")

logger = logging.getLogger("encryption")

class EncryptionUtils:
    """加密工具类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # 初始化加密密钥
        self._setup_encryption_keys()

        logger.info("加密工具初始化完成")

    def _setup_encryption_keys(self):
        """设置加密密钥"""
        # 从环境变量或配置获取密钥
        encryption_key = self.config.get('encryption_key')
        if not encryption_key:
            # 生成新密钥(生产环境应该从安全存储获取)
            if FERNET_AVAILABLE:
                encryption_key = Fernet.generate_key()
            else:
                encryption_key = secrets.token_bytes(32)
            logger.warning("生成了新的加密密钥, 生产环境应该使用预定义的密钥")

        # 设置Fernet加密器
        if FERNET_AVAILABLE:
            self.fernet = Fernet(encryption_key)
        else:
            self.fernet = None

    def encrypt(self, data: Union[str, bytes]) -> bytes:
        """加密数据(使用Fernet)"""
        if not FERNET_AVAILABLE:
            raise ValueError("Fernet not available")

        if isinstance(data, str):
            data = data.encode('utf-8')

        return self.fernet.encrypt(data)

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """解密数据(使用Fernet)"""
        if not FERNET_AVAILABLE:
            raise ValueError("Fernet not available")

        return self.fernet.decrypt(encrypted_data)

    def hash_password(self, password: str, salt: Optional[str] = None) -> Dict[str, str]:
        """安全的密码哈希"""
        if salt is None:
            salt = secrets.token_hex(32)

        # 使用 PBKDF2 进行密码哈希
        kdf = hashlib.pbkdf2_hmac(
            sha256,
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )

        hash_hex = kdf.hex()

        return {
            'hash': hash_hex,
            'salt': salt
        }

    def verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """验证密码"""
        hash_result = self.hash_password(password, salt)
        return secrets.compare_digest(hash_result['hash'], stored_hash)

    def generate_secure_token(self, length: int = 32) -> str:
        """生成安全令牌"""
        return secrets.token_urlsafe(length)

    def hash_data(self, data: Union[str, bytes], algorithm: str = 'sha256') -> str:
        """数据哈希"""
        if isinstance(data, str):
            data = data.encode('utf-8')

        if algorithm == 'sha256':
            hash_obj = hashlib.sha256(data)
        elif algorithm == 'sha512':
            hash_obj = hashlib.sha512(data)
        elif algorithm == 'md5':
            hash_obj = hashlib.md5(data)
        else:
            raise ValueError(f"不支持的哈希算法: {algorithm}")

        return hash_obj.hexdigest()

    def hmac_sign(self, data: Union[str, bytes], key: Union[str, bytes]) -> str:
        """HMAC签名"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        if isinstance(key, str):
            key = key.encode('utf-8')

        hmac_obj = hmac.new(key, data, hashlib.sha256)
        return hmac_obj.hexdigest()

    def verify_hmac(self, data: Union[str, bytes], signature: str, key: Union[str, bytes]) -> bool:
        """验证HMAC签名"""
        expected_signature = self.hmac_sign(data, key)
        return secrets.compare_digest(signature, expected_signature)

# 全局加密工具实例
encryption_utils = EncryptionUtils()

# 安全配置
SECURITY_CONFIG = {
    'password_min_length': 8,
    'password_require_special_chars': True,
    'session_timeout_minutes': 30,
    'max_login_attempts': 5,
    'lockout_duration_minutes': 15
}

def validate_password_strength(password: str) -> Dict[str, Any]:
    """验证密码强度"""
    result = {
        'valid': True,
        'errors': [],
        'score': 0
    }

    # 长度检查
    if len(password) < SECURITY_CONFIG['password_min_length']:
        result['valid'] = False
        result['errors'].append(f'密码长度至少需要{SECURITY_CONFIG["password_min_length"]}位')
    else:
        result['score'] += 1

    # 特殊字符检查
    if SECURITY_CONFIG['password_require_special_chars']:
        special_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        if not any(char in special_chars for char in password):
            result['valid'] = False
            result['errors'].append('密码必须包含特殊字符')
        else:
            result['score'] += 1

    # 数字检查
    if not any(char.isdigit() for char in password):
        result['valid'] = False
        result['errors'].append('密码必须包含数字')
    else:
        result['score'] += 1

    # 大写字母检查
    if not any(char.isupper() for char in password):
        result['valid'] = False
        result['errors'].append('密码必须包含大写字母')
    else:
        result['score'] += 1

    # 小写字母检查
    if not any(char.islower() for char in password):
        result['valid'] = False
        result['errors'].append('密码必须包含小写字母')
    else:
        result['score'] += 1

    return result

def sanitize_input(input_data: str) -> str:
    """清理输入数据"""
    if not input_data:
        return ""

    # 移除潜在的危险字符
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
    sanitized = input_data

    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')

    return sanitized.strip()

def generate_csrf_token() -> str:
    """生成CSRF令牌"""
    return encryption_utils.generate_secure_token(32)

def verify_csrf_token(token: str, expected_token: str) -> bool:
    """验证CSRF令牌"""
    return secrets.compare_digest(token, expected_token)