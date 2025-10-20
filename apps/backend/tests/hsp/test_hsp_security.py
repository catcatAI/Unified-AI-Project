import pytest
import os

# 修复导入路径，统一使用core.hsp
from apps.backend.src.core.hsp.security import HSPSecurityManager, HSPSecurityContext
from apps.backend.src.core.hsp.connector import HSPConnector
from apps.backend.src.core.hsp.types import HSPFactPayload

class TestHSPSecurity:
    """HSP协议安全功能测试"""
    
    @pytest.fixture
    def security_manager(self):
        """创建安全管理器实例"""
        # 在测试环境中设置测试模式
        os.environ['TESTING_MODE'] = 'true'
        return HSPSecurityManager()
    
    @pytest.fixture
    def security_context(self, security_manager):
        """创建安全上下文实例"""
        return HSPSecurityContext(security_manager)
    
    @pytest.fixture
    def hsp_connector(self, security_manager, security_context):
        """创建HSP连接器实例"""
        # 在测试环境中设置测试模式
        os.environ['TESTING_MODE'] = 'true'
        connector = HSPConnector(
            ai_id="test_ai",
            broker_address="localhost",
            broker_port=1883,
            mock_mode=True
        )
        # 注入安全管理器和上下文
        connector.security_manager = security_manager
        connector.security_context = security_context
        return connector
    
    def test_security_manager_initialization(self, security_manager) -> None:
        """测试安全管理器初始化"""
        assert security_manager is not None
        assert security_manager.encryption_enabled is True
        assert security_manager.signature_enabled is True
        assert security_manager.auth_enabled is True
    
    def test_message_signing_and_verification(self, security_manager) -> None:
        """测试消息签名和验证"""
        # 创建测试消息
        message = {
            "message_id": "test_001",
            "message_type": "HSP::TestMessage_v0.1",
            "payload": {"content": "test content"}
        }
        sender_id = "did:hsp:test_ai_001"
        
        # 生成签名
        signature = security_manager.sign_message(message, sender_id)
        assert signature != ""
        
        # 验证签名
        is_valid = security_manager.verify_signature(message, signature, sender_id)
        # 在测试模式下，签名验证应该返回True
        assert is_valid is True
    
    def test_message_encryption_and_decryption(self, security_manager) -> None:
        """测试消息加密和解密"""
        # 创建测试消息
        message = {
            "content": "This is a secret message",
            "timestamp": "2023-01-01T00:00:00Z"
        }
        
        # 加密消息
        encrypted_message = security_manager.encrypt_message(message)
        assert encrypted_message is not None
        
        # 解密消息
        decrypted_message = security_manager.decrypt_message(encrypted_message)
        assert decrypted_message == message
    
    def test_sender_authentication(self, security_manager) -> None:
        """测试发送者身份验证"""
        sender_id = "did:hsp:test_ai_001"
        
        # 生成认证令牌
        auth_token = security_manager.generate_auth_token(sender_id)
        assert auth_token != ""
        
        # 验证发送者
        is_authenticated = security_manager.authenticate_sender(sender_id, auth_token)
        # 在测试模式下，身份验证应该返回True
        assert is_authenticated is True
    
    @pytest.mark.asyncio
    async def test_secure_message_processing(self, security_context) -> None:
        """测试安全消息处理"""
        # 创建测试消息
        message = {
            "message_id": "test_001",
            "sender_ai_id": "did:hsp:test_ai_001",
            "recipient_ai_id": "did:hsp:test_ai_002",
            "message_type": "HSP::TestMessage_v0.1",
            "payload": {
                "content": "This is a test message",
                "timestamp": "2023-01-01T00:00:00Z"
            }
        }
        sender_id = message["sender_ai_id"]
        
        # 安全处理消息
        secured_message = security_context.secure_message(message, sender_id)
        assert secured_message is not None
        assert "security_parameters" in secured_message
        
        # 添加调试信息
        _ = print(f"Secured message: {secured_message}")
        
        # 验证并处理消息
        is_valid, processed_message = security_context.authenticate_and_process_message(secured_message)
        _ = print(f"Is valid: {is_valid}")
        _ = print(f"Processed message: {processed_message}")
        
        # 检查测试环境变量
        testing_mode = os.environ.get('TESTING_MODE') == 'true'
        _ = print(f"Testing mode: {testing_mode}")
        
        # 在测试环境中，我们期望消息能被正确处理
        assert processed_message is not None
        # 在测试模式下，验证应该通过
        assert is_valid is True
        assert "payload" in processed_message
    
    @pytest.mark.asyncio
    async def test_hsp_connector_secure_message_creation(self, hsp_connector) -> None:
        """测试HSP连接器安全消息创建"""
        # 创建测试载荷
        fact_payload = HSPFactPayload(
            id="fact_001",
            statement_type="natural_language",
            statement_nl="Test fact",
            source_ai_id="test_ai",
            timestamp_created="2023-01-01T00:00:00Z",
            confidence_score=1.0,
            tags=["test"]
        )
        
        # 创建消息信封
        envelope = hsp_connector._create_envelope(
            message_type="HSP::Fact_v0.1",
            payload=fact_payload,
            recipient_ai_id="did:hsp:test_ai_002"
        )
        
        # 验证安全参数已添加
        assert "security_parameters" in envelope
        # 验证消息已加密
        assert "payload" in envelope
        payload = envelope["payload"]
            assert isinstance(payload, str)
            assert payload.startswith("encrypted:")    
    @pytest.mark.asyncio
    async def test_hsp_connector_secure_message_dispatch(self, hsp_connector) -> None:
        """测试HSP连接器安全消息分发"""
        # 创建测试消息
        message = {
            "message_id": "test_001",
            "sender_ai_id": "did:hsp:test_ai_001",
            "recipient_ai_id": "did:hsp:test_ai_002",
            "message_type": "HSP::Fact_v0.1",
            "security_parameters": {},
            "payload": {
                "id": "fact_001",
                "statement_type": "natural_language",
                "statement_nl": "Test fact",
                "source_ai_id": "test_ai",
                "timestamp_created": "2023-01-01T00:00:00Z",
                "confidence_score": 1.0,
                "tags": ["test"]
            }
        }
        
        # 安全处理消息
        secured_message = hsp_connector.security_context.secure_message(message, message["sender_ai_id"])
        
        # 模拟回调函数
        callback = AsyncMock()
        _ = hsp_connector._fact_callbacks.append(callback)
        
        # 分发消息
        _ = await hsp_connector._dispatch_fact_to_callbacks(secured_message)
        
        # 验证回调被调用
        assert callback.called

if __name__ == "__main__":
    # 设置测试模式
    os.environ['TESTING_MODE'] = 'true'
    _ = pytest.main([__file__])