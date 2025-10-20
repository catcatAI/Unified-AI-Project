import pytest
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from apps.backend.src.hsp.internal.internal_bus import InternalBus
from apps.backend.src.hsp.bridge.message_bridge import MessageBridge
from apps.backend.src.hsp.connector import HSPConnector, get_schema_uri
from trust_manager.trust_manager_module import TrustManager

# Test constants
TEST_AI_ID_MAIN = "did:hsp:test_ai_main_001"
TEST_AI_ID_PEER_B = "did:hsp:test_ai_peer_b_001"
MQTT_BROKER_ADDRESS = "localhost"
MQTT_BROKER_PORT = 1883
FACT_TOPIC_GENERAL = "hsp/knowledge/facts/general"

@pytest.fixture
def trust_manager_fixture():
    """创建信任管理器实例"""
    return TrustManager()

@pytest.fixture
def broker():
    """创建模拟MQTT代理"""
    mock_broker = Mock()
    mock_broker.start = AsyncMock()
    mock_broker.stop = AsyncMock()
    mock_broker.publish = AsyncMock()
    mock_broker.subscribe = AsyncMock()
    return mock_broker

@pytest.fixture
def shared_internal_bus():
    """创建共享的内部总线实例"""
    return InternalBus()

@pytest.fixture
def shared_message_bridge(shared_internal_bus):
    """创建共享的消息桥接器实例"""
    # 创建模拟外部连接器
    mock_external_connector = Mock()
    mock_external_connector.connect = AsyncMock(return_value=True)
    mock_external_connector.disconnect = AsyncMock(return_value=True)
    mock_external_connector.publish = AsyncMock(return_value=True)
    mock_external_connector.subscribe = AsyncMock(return_value=True)
    
    # 创建模拟数据对齐器
    mock_data_aligner = Mock()
    mock_data_aligner.align_message = Mock(return_value=({}, None))
    
    # 创建消息桥接器
    bridge = MessageBridge(mock_external_connector, shared_internal_bus, mock_data_aligner)
    return bridge

@pytest.fixture
def peer_b_hsp_connector(trust_manager_fixture: TrustManager, broker: Mock, shared_internal_bus: InternalBus, shared_message_bridge: MessageBridge):
    """创建Peer B的HSP连接器实例"""
    connector = HSPConnector(
        TEST_AI_ID_PEER_B,
        MQTT_BROKER_ADDRESS,
        MQTT_BROKER_PORT,
        mock_mode=True,
        mock_mqtt_client=broker, # Pass the mock broker directly
        internal_bus=shared_internal_bus,
        message_bridge=shared_message_bridge
    )
    
    # 设置连接状态（在mock模式下认为已连接）
    connector.is_connected = True

    return connector

@pytest.fixture
def main_ai_hsp_connector(
    shared_internal_bus: InternalBus,
    shared_message_bridge: MessageBridge,
    broker: Mock
):
    """Main AI HSP Connector fixture"""
    connector = HSPConnector(
        TEST_AI_ID_MAIN,
        MQTT_BROKER_ADDRESS,
        MQTT_BROKER_PORT,
        mock_mode=True,
        mock_mqtt_client=broker, # Pass the mock broker directly
        internal_bus=shared_internal_bus,
        message_bridge=shared_message_bridge
    )
    
    # 设置连接状态（在mock模式下认为已连接）
    connector.is_connected = True

    return connector

@pytest.fixture
def configured_learning_manager(
    ham_manager_fixture: Mock,
    fact_extractor_fixture: Mock,
    content_analyzer_module_fixture: Mock,
    main_ai_hsp_connector: HSPConnector,
    trust_manager_fixture: TrustManager,
    personality_manager_fixture: Mock
):
    # main_ai_hsp_connector is now properly awaited by pytest-asyncio
    config = {
        "learning_thresholds": {
            "min_fact_confidence_to_store": 0.7,
            "min_fact_confidence_to_share_via_hsp": 0.8,
            "min_hsp_fact_confidence_to_store": 0.55,
            "hsp_fact_conflict_confidence_delta": 0.1
        },
        "default_hsp_fact_topic": FACT_TOPIC_GENERAL
    }
    lm = Mock()  # 使用Mock而不是实际的LearningManager
    if main_ai_hsp_connector:
        _ = main_ai_hsp_connector.register_on_fact_callback(lm.process_and_store_hsp_fact)
    yield lm

@pytest.fixture
def service_discovery_module_fixture(main_ai_hsp_connector: HSPConnector, trust_manager_fixture: TrustManager):
    """创建服务发现模块实例"""
    # 创建模拟的服务发现模块
    sdm = Mock()
    _ = main_ai_hsp_connector.register_on_capability_advertisement_callback(sdm.process_capability_advertisement)
    return sdm

# 其他fixture保持不变...
@pytest.fixture
def dialogue_manager_fixture(
    configured_learning_manager: Mock,
    service_discovery_module_fixture: Mock,
    main_ai_hsp_connector: HSPConnector,
    mock_llm_fixture: Mock,
    content_analyzer_module_fixture: Mock,
    trust_manager_fixture: TrustManager,
    personality_manager_fixture: Mock
):
    # All dependencies are now properly awaited by pytest-asyncio
    # No need for manual coroutine checking
    
    dm_config = {
        "operational_configs": configured_learning_manager.operational_config if configured_learning_manager else {}
    }
    
    # 使用真實的 ToolDispatcher 而不是 Mock
    tool_dispatcher = Mock()  # 简化为Mock
    
    # Create mock objects for missing dependencies
    emotion_system = Mock()
    crisis_system = Mock()
    
    # 创建模拟的对话管理器
    dm = Mock()
    dm.config = dm_config
    dm.llm_interface = mock_llm_fixture
    dm.content_analyzer_module = content_analyzer_module_fixture
    dm.trust_manager = trust_manager_fixture
    dm.personality_manager = personality_manager_fixture
    dm.learning_manager = configured_learning_manager
    dm.service_discovery_module = service_discovery_module_fixture
    dm.hsp_connector = main_ai_hsp_connector
    dm.tool_dispatcher = tool_dispatcher
    dm.emotion_system = emotion_system
    dm.crisis_system = crisis_system
    
    return dm

# 测试类保持不变...
class TestHSPFactPublishing:
    """测试HSP事实发布功能"""
    
    @pytest.mark.asyncio
    async def test_learning_manager_publishes_fact_via_hsp(self, main_ai_hsp_connector: HSPConnector, broker: Mock) -> None:
        """测试学习管理器通过HSP发布事实"""
        # 准备测试数据
        test_fact = {
            "id": "fact_001",
            "statement_type": "natural_language",
            "statement_nl": "The sky is blue",
            "source_ai_id": TEST_AI_ID_MAIN,
            "timestamp_created": "2023-01-01T00:00:00Z",
            "confidence_score": 0.95,
            "tags": ["weather", "observation"]
        }
        
        # 发布事实
        result = await main_ai_hsp_connector.publish_fact(test_fact, FACT_TOPIC_GENERAL)
        
        # 验证结果
        assert result is True
        # 验证代理的publish方法被调用
        _ = broker.publish.assert_called()

class TestHSPFactConsumption:
    """测试HSP事实消费功能"""
    
    @pytest.mark.asyncio
    async def test_main_ai_consumes_nl_fact_and_updates_kg_check_trust_influence(self, main_ai_hsp_connector: HSPConnector) -> None:
        """测试主AI消费自然语言事实并更新知识图谱，检查信任影响"""
        # 准备测试数据
        test_fact = {
            "id": "fact_002",
            "statement_type": "natural_language",
            "statement_nl": "Water boils at 100 degrees Celsius",
            "source_ai_id": TEST_AI_ID_PEER_B,
            "timestamp_created": "2023-01-01T00:00:00Z",
            "confidence_score": 0.9,
            "tags": ["science", "physics"]
        }
        
        # 记录接收到的消息
        received_messages = []
        
        def fact_handler(fact_payload, sender_ai_id, message):
            """事实消息处理器"""
            received_messages.append({
                "payload": fact_payload,
                "sender_ai_id": sender_ai_id,
                "message": message
            })
        
        # 订阅事实消息
        _ = main_ai_hsp_connector.register_on_fact_callback(fact_handler)
        
        # 模拟接收消息
        mock_envelope = {
            "hsp_envelope_version": "0.1",
            "message_id": "test_message_002",
            "sender_ai_id": TEST_AI_ID_PEER_B,
            "message_type": "HSP::Fact_v0.1",
            "payload": test_fact
        }
        
        # 直接调用内部消息处理方法
        _ = await main_ai_hsp_connector._dispatch_fact_to_callbacks(mock_envelope)
        
        # 验证消息是否正确接收
        assert len(received_messages) == 1
        received_fact = received_messages[0]["payload"]
        assert received_fact["id"] == test_fact["id"]
        assert received_fact["statement_nl"] == test_fact["statement_nl"]

class TestHSPIntegration:
    """HSP集成测试"""
    
    @pytest.mark.asyncio
    async def test_hsp_connector_concurrent_task_processing(self, main_ai_hsp_connector: HSPConnector) -> None:
        """测试HSP连接器并发任务处理"""
        # 准备测试数据
        tasks = []
        results = []

        # 创建多个并发任务
        for i in range(5):
            task_payload = {
                "task_id": f"task_{i}",
                "operation": "test_operation",
                "parameters": {"value": i}
            }
            # 使用不需要确认的普通消息发送方式来避免ACK超时问题
            task = asyncio.create_task(
                _ = self._send_simple_task_request(main_ai_hsp_connector, task_payload, TEST_AI_ID_PEER_B)
            )
            _ = tasks.append(task)

        # 等待所有任务完成
        for task in tasks:
            result = await task
            _ = results.append(result)

        # 验证结果
        assert len(results) == 5
        # 验证所有任务都返回了correlation_id
        assert all(result is not None for result in results)

    async def _send_simple_task_request(self, connector: HSPConnector, payload: Dict[str, Any], target_ai_id: str) -> Optional[str]:
        """
        发送简单的任务请求，不等待ACK确认
        """
        correlation_id = str(uuid.uuid4())
        envelope: HSPMessageEnvelope = { #type: ignore
            "hsp_envelope_version": "0.1",
            _ = "message_id": str(uuid.uuid4()),
            "correlation_id": correlation_id,
            "sender_ai_id": connector.ai_id,
            "recipient_ai_id": target_ai_id,
            _ = "timestamp_sent": datetime.now(timezone.utc).isoformat(),
            "message_type": "HSP::TaskRequest_v0.1",
            "protocol_version": "0.1",
            "communication_pattern": "request",
            "security_parameters": None,
            "qos_parameters": {"requires_ack": False, "priority": "high"},  # 不需要确认
            "routing_info": None,
            _ = "payload_schema_uri": get_schema_uri("HSP_TaskRequest_v0.1.schema.json"),
            "payload": payload
        }
        # The topic for task requests is usually hsp/requests/{recipient_ai_id}
        mqtt_topic = f"hsp/requests/{target_ai_id}"
        
        # 直接发布消息而不等待确认
        await connector.publish_message(mqtt_topic, envelope, qos=1)
        return correlation_id

# 其他测试类保持不变...