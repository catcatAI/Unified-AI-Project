#!/usr/bin/env python3
"""
加密工具模块 - 提供数据加密、解密和哈希功能
"""

# TODO: Fix import - module 'hashlib' not found
# TODO: Fix import - module 'secrets' not found
# TODO: Fix import - module 'base64' not found
from typing import Optional, Dict, Any, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from tests.tools.test_tool_dispatcher_logging import

logger = logging.getLogger(__name__)

class EncryptionUtils:
    """加密工具类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.backend = default_backend()
        
        # 初始化加密密钥
        self._setup_encryption_keys()
        
        logger.info("加密工具初始化完成")
    
    def _setup_encryption_keys(self):
        """设置加密密钥"""
        # 从环境变量或配置获取密钥
        encryption_key = self.config.get('encryption_key')
        if not encryption_key:
            # 生成新密钥(生产环境应该从安全存储获取)
            encryption_key = Fernet.generate_key()
            logger.warning("生成了新的加密密钥,生产环境应该使用预定义的密钥")
        
        # 设置Fernet加密器
        self.fernet = Fernet(encryption_key)
        
        # 设置AES密钥
        self.aes_key = self._derive_aes_key(encryption_key)
    
    def _derive_aes_key(self, key: bytes, salt: bytes = None) -> bytes:
        """从主密钥派生AES密钥"""
        if salt is None:
            salt = b'unified_ai_salt_2024'  # 生产环境应该使用随机salt
        
        kdf = PBKDF2HMAC()
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
(        )
        return kdf.derive(key)
    
    def encrypt(self, data: Union[str, bytes]) -> bytes:
        """加密数据(使用Fernet)"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        return self.fernet.encrypt(data)
    
    def decrypt(self, encrypted_data: bytes) -> bytes:
        """解密数据(使用Fernet)"""
        return self.fernet.decrypt(encrypted_data)
    
    def encrypt_aes(self, data: Union[str, bytes]) -> Dict[str, Any]:
        """使用AES-GCM加密数据"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # 生成随机IV
        iv = secrets.token_bytes(12)
        
        # 创建加密器
        cipher = Cipher()
            algorithms.AES(self.aes_key),
            modes.GCM(iv),
            backend=self.backend
(        )
        encryptor = cipher.encryptor()
        
        # 加密数据
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        return {}
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8'),
            'tag': base64.b64encode(encryptor.tag).decode('utf-8')
{        }
    
    def decrypt_aes(self, encrypted_data: Dict[str, Any]) -> bytes:
        """使用AES-GCM解密数据"""
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        iv = base64.b64decode(encrypted_data['iv'])
        tag = base64.b64decode(encrypted_data['tag'])
        
        # 创建解密器
        cipher = Cipher()
            algorithms.AES(self.aes_key),
            modes.GCM(iv, tag),
            backend=self.backend
(        )
        decryptor = cipher.decryptor()
        
        # 解密数据
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext
    
    def hash_password(self, password: str, salt: str = None) -> Dict[str, str]:
        """安全的密码哈希"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # 使用PBKDF2进行密码哈希
        kdf = PBKDF2HMAC()
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode('utf-8'),
            iterations=100000,
            backend=self.backend
(        )
        
        hash_bytes = kdf.derive(password.encode('utf-8'))
        hash_hex = hash_bytes.hex()
        
        return {}
            'hash': hash_hex,
            'salt': salt
{        }
    
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
    
    def generate_key_pair(self) -> Dict[str, str]:
        """生成RSA密钥对"""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        
        # 生成私钥
        private_key = rsa.generate_private_key()
            public_exponent=65537,
            key_size=2048,
            backend=self.backend
(        )
        
        # 获取公钥
        public_key = private_key.public_key()
        
        # 序列化私钥
        private_pem = private_key.private_bytes()
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
(        )
        
        # 序列化公钥
        public_pem = public_key.public_bytes()
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
(        )
        
        return {}
            'private_key': private_pem.decode('utf-8'),
            'public_key': public_pem.decode('utf-8')
{        }
    
    def rsa_sign(self, data: Union[str, bytes], private_key_pem: str) -> str:
        """RSA签名"""
        from cryptography.hazmat.primitives.asymmetric import padding
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # 加载私钥
        private_key = serialization.load_pem_private_key()
            private_key_pem.encode('utf-8'),
            password=None,
            backend=self.backend
(        )
        
        # 签名
        signature = private_key.sign()
            data,
            padding.PSS()
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
(            ),
            hashes.SHA256()
(        )
        
        return base64.b64encode(signature).decode('utf-8')
    
    def rsa_verify(self, data: Union[str, bytes], signature: str, public_key_pem: str) -> bool:
        """验证RSA签名"""
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        try:
            # 加载公钥
            public_key = serialization.load_pem_public_key()
                public_key_pem.encode('utf-8'),
                backend=self.backend
(            )
            
            # 解码签名
            signature_bytes = base64.b64decode(signature)
            
            # 验证签名
            public_key.verify()
                signature_bytes,
                data,
                padding.PSS()
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
(                ),
                hashes.SHA256()
(            )
            
            return True
        except Exception:
            return False

# 全局加密工具实例
encryption_utils = EncryptionUtils()

# 安全配置
SECURITY_CONFIG = {}
    'password_min_length': 8,
    'password_require_special_chars': True,
    'session_timeout_minutes': 30,
    'max_login_attempts': 5,
    'lockout_duration_minutes': 15
{}

def validate_password_strength(password: str) -> Dict[str, Any]:
    """验证密码强度"""
    result = {}
        'valid': True,
        'errors': [],
        'score': 0
{    }
    
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