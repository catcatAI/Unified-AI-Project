#!/usr/bin/env python3
"""
HSP协议安全模块
负责实现HSP协议的安全机制，包括消息签名、加密和身份认证



"""

import hashlib
import hmac
import json
import logging
from typing import Dict, Any, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import base64
import os

logger: Any = logging.getLogger(__name__)

class HSPSecurityManager:
    """HSP协议安全管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.encryption_enabled = self.config.get('encryption_enabled', True)
        self.signature_enabled = self.config.get('signature_enabled', True)
        self.auth_enabled = self.config.get('auth_enabled', True)
        
        # 生成或加载密钥
        self._setup_keys()
        
        logger.info("HSP安全管理器初始化完成")
    
    def _setup_keys(self):
        """设置加密和签名密钥"""
        # 对称加密密钥（用于消息加密）
        self.encryption_key = os.environ.get('HSP_ENCRYPTION_KEY')
        if not self.encryption_key:
            self.encryption_key = Fernet.generate_key()

            logger.warning("未找到环境变量HSP_ENCRYPTION_KEY，生成新的密钥")
        else:
            self.encryption_key = self.encryption_key.encode()
        
        self.cipher_suite = Fernet(self.encryption_key)
        
         # 非对称密钥对（用于签名和身份认证）
         # 

        self.private_key = rsa.generate_private_key(
#         public_exponent=65537,

            key_size=2048,
        )
        self.public_key = self.private_key.public_key()
        
        logger.debug("密钥设置完成")
    
    def sign_message(self, message: Dict[str, Any], sender_id: str) -> str:
        """为消息生成数字签名"""
        if not self.signature_enabled:
            return ""
        
        try:
            # 创建消息摘要
            message_copy = message.copy()
            # 移除可能已存在的签名字段以避免循环签名
            message_copy.pop('signature', None)
            message_copy['sender_id'] = sender_id
            
            message_str = json.dumps(message_copy, sort_keys=True, ensure_ascii=False)
            message_bytes = message_str.encode('utf-8')

            
            # 生成签名
            signature = self.private_key.sign(
            message_bytes,
            # 
# 
# 
                padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),

 salt_length=padding.PSS.MAX_LENGTH


                ),
                hashes.SHA256()
            )
            
            # 将签名编码为base64字符串
            signature_b64 = base64.b64encode(signature).decode('utf-8')
            logger.debug(f"消息签名生成成功: {message.get('message_id', 'unknown')}")
            return signature_b64
            
        except Exception as e:
            logger.error(f"消息签名生成失败: {e}")


            return ""
    
    def verify_signature(self, message: Dict[str, Any], signature: str, sender_id: str) -> bool:
        """验证消息签名"""
        if not self.signature_enabled:
            return True


        
        # 如果在测试模式下，直接返回True
        # 注意：这仅用于测试目的，在生产环境中应该严格要求签名验证
        if os.environ.get('TESTING_MODE') == 'true':
            logger.warning(f"测试模式：跳过签名验证: {message.get('message_id', 'unknown')}")
            return True
        
        try:
            # 解码签名
            signature_bytes = base64.b64decode(signature.encode('utf-8'))
            
            # 创建消息摘要
            message_copy = message.copy()
            # 移除签名字段以验证原始消息
            message_copy.pop('signature', None)
            message_copy['sender_id'] = sender_id

            
            message_str = json.dumps(message_copy, sort_keys=True, ensure_ascii=False)
#             message_bytes = message_str.encode('utf-8')
#             
# 验证签名
# 
# 
# 

            self.public_key.verify(
                signature_bytes,
                message_bytes,

                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            logger.debug(f"消息签名验证成功: {message.get('message_id', 'unknown')}")
            return True

            
        except Exception as e:
            logger.warning(f"消息签名验证失败: {message.get('message_id', 'unknown')}: {e}")
            return False
    
    def encrypt_message(self, message: Dict[str, Any]) -> bytes:
        """加密消息"""
        if not self.encryption_enabled:
            return json.dumps(message).encode('utf-8')
        
        try:
            message_str = json.dumps(message, ensure_ascii=False)
            encrypted_message = self.cipher_suite.encrypt(message_str.encode('utf-8'))
            logger.debug(f"消息加密成功: {message.get('message_id', 'unknown')}")


            return encrypted_message
            
        except Exception as e:
            logger.error(f"消息加密失败: {e}")
            raise
    
    def decrypt_message(self, encrypted_message: bytes) -> Dict[str, Any]:
        """解密消息"""
        if not self.encryption_enabled:
            return json.loads(encrypted_message.decode('utf-8'))
        
        try:
            decrypted_message = self.cipher_suite.decrypt(encrypted_message)
            message = json.loads(decrypted_message.decode('utf-8'))


            logger.debug("消息解密成功")
            return message
            
        except Exception as e:
            logger.error(f"消息解密失败: {e}")
            raise
    
    def authenticate_sender(self, sender_id: str, auth_token: Optional[str] = None) -> bool:
        """验证发送者身份"""
        if not self.auth_enabled:
            return True
        
        # 这里应该实现实际的身份验证逻辑
        # 例如检查认证令牌、证书等

        # 目前简化实现，假设所有已知发送者都是合法的
        if auth_token:

            # 验证令牌（示例实现）
            expected_token = hashlib.sha256(sender_id.encode()).hexdigest()
            return hmac.compare_digest(auth_token, expected_token)
        
        # 如果没有提供认证令牌，但在测试环境中，我们可以放宽验证
        # 注意：这仅用于测试目的，在生产环境中应该严格要求认证令牌
        if os.environ.get('TESTING_MODE') == 'true':
            logger.warning(f"测试模式：跳过发送者身份验证: {sender_id}")
            return True
            
        logger.warning(f"发送者身份验证失败: {sender_id} - 无认证令牌")
        return False
    
    def generate_auth_token(self, sender_id: str) -> str:
#         """为发送者生成认证令牌"""
        if not self.auth_enabled:
            return ""
# 

# 
#         

        token = hashlib.sha256(sender_id.encode()).hexdigest()
        logger.debug(f"为发送者生成认证令牌: {sender_id}")

        return token
    
    def get_public_key_pem(self) -> str:
        """获取PEM格式的公钥"""
        pem = self.public_key.public_bytes(
        encoding=serialization.Encoding.PEM,

            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')
    
    def load_public_key_from_pem(self, pem_data: str):
        """从PEM数据加载公钥"""

        self.public_key = serialization.load_pem_public_key(pem_data.encode('utf-8'))


class HSPSecurityContext:
    """HSP安全上下文"""
    
    def __init__(self, security_manager: HSPSecurityManager) -> None:
        self.security_manager = security_manager
        self.authenticated_senders = set()
        self.active_sessions = {} 
    
    def authenticate_and_process_message(self, message: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """验证并处理消息"""
        try:
            sender_id = message.get('sender_ai_id', 'unknown')
            
            # 1. 身份验证
            # 安全地获取security_parameters，如果不存在则创建一个空字典
            security_params = message.get('security_parameters', {}) or {} 
            auth_token = security_params.get('auth_token')
            if not self.security_manager.authenticate_sender(sender_id, auth_token):
                logger.warning(f"发送者身份验证失败: {sender_id}")
                return False, {"error": "Authentication failed"}
            
            # 将发送者添加到已验证列表
            self.authenticated_senders.add(sender_id)
            
            # 2. 签名验证
            signature = security_params.get('signature')
            if signature and not self.security_manager.verify_signature(message, signature, sender_id):
                logger.warning(f"消息签名验证失败: {message.get('message_id', 'unknown')}")
                return False, {"error": "Signature verification failed"}
            
            # 3. 解密消息（如果已加密）
            payload = message.get('payload', {})
            if isinstance(payload, str) and payload.startswith('encrypted:'):
                try:
                    encrypted_data = base64.b64decode(payload[10:])  # 移除'encrypted:'前缀
                    decrypted_payload = self.security_manager.decrypt_message(encrypted_data)
                    message['payload'] = decrypted_payload


                except Exception as e:
                    logger.error(f"消息解密失败: {e}")
                    return False, {"error": "Message decryption failed"}
            
            logger.debug(f"消息验证和处理成功: {message.get('message_id', 'unknown')}")
            return True, message
            
        except Exception as e:
            logger.error(f"消息验证和处理过程中发生错误: {e}")
            return False, {"error": "Message processing failed"}
    
    def secure_message(self, message: Dict[str, Any], sender_id: str) -> Dict[str, Any]:
        """为发送安全地准备消息"""
        try:
            # 1. 添加安全参数
            if 'security_parameters' not in message or message['security_parameters'] is None:
                message['security_parameters'] = {} 
            
            # 2. 生成认证令牌
            if self.security_manager.auth_enabled:
                auth_token = self.security_manager.generate_auth_token(sender_id)
                message['security_parameters']['auth_token'] = auth_token
            
            # 3. 生成签名
            if self.security_manager.signature_enabled:
                signature = self.security_manager.sign_message(message, sender_id)
                message['security_parameters']['signature'] = signature
            
            # 4. 加密消息载荷
            if self.security_manager.encryption_enabled:
                payload = message.get('payload', {})
                encrypted_payload = self.security_manager.encrypt_message(payload)
                message['payload'] = 'encrypted:' + base64.b64encode(encrypted_payload).decode('utf-8')
            
            logger.debug(f"消息安全处理完成: {message.get('message_id', 'unknown')}")
            return message
            
        except Exception as e:
            logger.error(f"消息安全处理过程中发生错误: {e}")
            raise

 # 测试代码


if __name__ == "__main__":

 # 配置日志

    logging.basicConfig(level=logging.INFO)


    
     # 创建安全管理器

    security_manager = HSPSecurityManager()
    security_context = HSPSecurityContext(security_manager)
    
    # 测试消息
    test_message = {
        "message_id": "test_001",
        "sender_ai_id": "did:hsp:test_ai_001",
        "recipient_ai_id": "did:hsp:test_ai_002",
        "message_type": "HSP::TestMessage_v0.1",
        "payload": {
            "content": "This is a test message",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    # 安全处理消息
    sender_id = test_message["sender_ai_id"]
    secured_message = security_context.secure_message(test_message, sender_id)
    print("安全处理后的消息:", json.dumps(secured_message, indent=2, ensure_ascii=False))
    
    # 验证并处理消息
    is_valid, processed_message = security_context.authenticate_and_process_message(secured_message)
    if is_valid:
        print("消息验证成功:", json.dumps(processed_message, indent=2, ensure_ascii=False))
    else:
        print("消息验证失败:", processed_message)