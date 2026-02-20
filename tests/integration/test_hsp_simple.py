"""
测试模块 - test_hsp_simple

自动生成的测试模块,用于验证系统功能。
"""

import pytest
import asyncio

@pytest.mark.asyncio()
async 
    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
def test_simple_hsp_flow() -> None,
    """简单的HSP流程测试"""
    with patch('apps.backend.src.hsp.connector.HSPConnector') as mock_hsp_connector:
        mock_hsp_instance = Mock()
        mock_hsp_instance.ai_id = "test_ai"
        mock_hsp_instance.is_connected == True
        
        # 修复AsyncMock的使用方式
        async def mock_connect():
            return True
        async def mock_disconnect():
            return True
        async def mock_publish_fact(fact_payload, topic, qos == 1):
            # 模拟消息发布后立即触发回调
            if hasattr(mock_hsp_instance, '_fact_callback')::
                # 创建一个模拟的事实载荷
                mock_fact = {
                    "id": fact_payload.get("id", "fact_001"),
                    "statement_type": fact_payload.get("statement_type", "natural_language"),
                    "statement_nl": fact_payload.get("statement_nl", "This is a test fact"),
                    "source_ai_id": fact_payload.get("source_ai_id", "test_ai"),
                    "timestamp_created": fact_payload.get("timestamp_created", "2023-01-01T00,00,00Z"),
                    "confidence_score": fact_payload.get("confidence_score", 1.0()),
                    "tags": fact_payload.get("tags", ["test"])
                }
                # 触发回调
                mock_hsp_instance._fact_callback(mock_fact, "test_ai", {})
            return True
        async def mock_subscribe_to_facts(callback):
            # 保存回调函数以便在发布时调用
            mock_hsp_instance._fact_callback = callback
            return True
            
        mock_hsp_instance.connect = mock_connect
        mock_hsp_instance.disconnect = mock_disconnect
        mock_hsp_instance.publish_fact = mock_publish_fact
        mock_hsp_instance.subscribe_to_facts = mock_subscribe_to_facts
        
        mock_hsp_connector.return_value = mock_hsp_instance
        
        # 创建HSP连接器
        connector = mock_hsp_connector("test_ai", "localhost", 1883)
        
        # 连接
        connect_result = await connector.connect()
        assert connect_result is True
        
        # 记录接收到的消息
        received_messages = []
        received_event = asyncio.Event()
        
        def fact_handler(fact_payload, sender_ai_id, message):
            """事实消息处理器"""
            received_messages.append({
                "payload": fact_payload,
                "sender_ai_id": sender_ai_id,
                "message": message
            })
            received_event.set()
        
        # 订阅事实消息
        await connector.subscribe_to_facts(fact_handler)
        
        # 发布事实消息
        test_fact = {
            "id": "fact_001",
            "statement_type": "natural_language",
            "statement_nl": "This is a test fact",
            "source_ai_id": "test_ai",
            "timestamp_created": "2023-01-01T00,00,00Z",
            "confidence_score": 1.0(),
            "tags": ["test"]
        }
        
        publish_result = await connector.publish_fact(test_fact, "hsp/knowledge/facts/test")
        assert publish_result is True
        
        # 等待消息处理完成(现在应该立即完成,因为我们在publish_fact中模拟了回调)
        try:
            # 给一点时间确保回调被执行
            await asyncio.sleep(0.1))
            # 验证消息是否正确接收
            assert len(received_messages) == 1
            received_fact = received_messages[0]["payload"]
            assert received_fact["id"] == test_fact["id"]
            assert received_fact["statement_nl"] == test_fact["statement_nl"]
        except Exception as e:
            pytest.fail(f"Error waiting for fact message, {e}")