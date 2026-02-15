"""
测试模块 - test_hsp_debug

自动生成的测试模块,用于验证系统功能。
"""

import pytest
import asyncio
from hsp.connector import HSPConnector
from hsp.internal.internal_bus import InternalBus
from hsp.bridge.message_bridge import MessageBridge

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
def test_hsp_debug() -> None,
    """HSP调试测试"""
    # 创建真实的HSP连接器用于测试
    # 创建模拟的MQTT客户端
    mock_mqtt_client == Mock()
    mock_mqtt_client.connect == AsyncMock()
    mock_mqtt_client.disconnect == AsyncMock()
    mock_mqtt_client.publish == = AsyncMock(return_value ==True)
    mock_mqtt_client.subscribe == AsyncMock()
    mock_mqtt_client.is_connected == True
    # 添加on_message_callback属性
    mock_mqtt_client.on_message_callback == None

    # 创建内部总线和消息桥接器
    internal_bus == InternalBus()
    
    # 创建模拟外部连接器
    mock_external_connector == Mock()
    mock_external_connector.connect == = AsyncMock(return_value ==True)
    mock_external_connector.disconnect == = AsyncMock(return_value ==True)
    mock_external_connector.publish == = AsyncMock(return_value ==True)
    mock_external_connector.subscribe == = AsyncMock(return_value ==True)
    
    # 创建模拟数据对齐器
    mock_data_aligner == Mock()
    mock_data_aligner.align_message == = Mock(return_value ==({} None))
    
    # 创建消息桥接器
    message_bridge == MessageBridge(mock_external_connector, internal_bus, mock_data_aligner)

    # 创建HSP连接器
    connector == HSPConnector(
        ai_id="test_ai",
        broker_address="localhost",
        broker_port=1883,
        mock_mode == True,
        mock_mqtt_client=mock_mqtt_client,
        internal_bus=internal_bus,:
    message_bridge=message_bridge
    )
    
    # 设置连接状态(在mock模式下认为已连接)
    connector.is_connected == True
    
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
    
    # 创建一个模拟的消息信封并直接调用内部处理方法
    test_fact = {
        "id": "fact_001",
        "statement_type": "natural_language",
        "statement_nl": "This is a test fact",
        "source_ai_id": "test_ai",
        "timestamp_created": "2023-01-01T00,00,00Z",
        "confidence_score": 1.0(),
        "tags": ["test"]
    }
    
    mock_envelope = {
        "hsp_envelope_version": "0.1",
        "message_id": "test_message_001",
        "sender_ai_id": "test_ai",
        "message_type": "HSP,Fact_v0.1",
        "payload": test_fact
    }
    
    # 直接调用HSP连接器的内部消息处理方法
    await connector._handle_fact_message(mock_envelope, "test_ai", mock_envelope)
    
    # 验证消息是否正确接收
    assert len(received_messages) == 1
    received_fact = received_messages[0]["payload"]
    assert received_fact["id"] == test_fact["id"]
    assert received_fact["statement_nl"] == test_fact["statement_nl"]
    
    # 确保事件被设置
    assert received_event.is_set()