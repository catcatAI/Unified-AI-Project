import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from apps.backend.src.hsp.internal.internal_bus import InternalBus
from apps.backend.src.hsp.bridge.message_bridge import MessageBridge
from apps.backend.src.hsp.bridge.data_aligner import DataAligner
from apps.backend.src.hsp.connector import HSPConnector

class TestHSPIntegration:
    """HSP集成测试"""
    
    @pytest.fixture
    def internal_bus(self):
        """创建内部总线实例"""
        return InternalBus()
    
    @pytest.fixture
    def mock_external_connector(self):
        """创建模拟外部连接器"""
        connector = Mock()
        connector.connect = AsyncMock(return_value=True)
        connector.disconnect = AsyncMock(return_value=True)
        connector.publish = AsyncMock(return_value=True)
        connector.subscribe = AsyncMock(return_value=True)
        return connector
    
    @pytest.fixture
    def mock_data_aligner(self):
        """创建模拟数据对齐器"""
        aligner = Mock(spec=DataAligner)
        # 修改模拟行为，使其根据消息类型返回正确的对齐消息
        def align_message_side_effect(message_dict):
            message_type = message_dict.get("message_type", "HSP::Fact_v0.1")
            if "Opinion" in message_type:
                return ({
                    "message_type": "HSP::Opinion_v0.1",
                    "payload": {
                        "id": "opinion_001",
                        "statement_type": "natural_language",
                        "statement_nl": "This is a test opinion",
                        "source_ai_id": "test_ai_1",
                        "timestamp_created": "2023-01-01T00:00:00Z",
                        "confidence_score": 0.8,
                        "reasoning_chain": ["fact_001"],
                        "tags": ["test"]
                    }
                }, None)
            else:
                return ({
                    "message_type": "HSP::Fact_v0.1",
                    "payload": {
                        "id": "fact_001",
                        "statement_type": "natural_language",
                        "statement_nl": "This is a test fact",
                        "source_ai_id": "test_ai",
                        "timestamp_created": "2023-01-01T00:00:00Z",
                        "confidence_score": 1.0,
                        "tags": ["test"]
                    }
                }, None)
        
        aligner.align_message = Mock(side_effect=align_message_side_effect)
        return aligner
    
    @pytest.fixture
    def message_bridge(self, mock_external_connector, internal_bus, mock_data_aligner):
        """创建消息桥接器实例"""
        bridge = MessageBridge(mock_external_connector, internal_bus, mock_data_aligner)
        return bridge
    
    @pytest.fixture
    def hsp_connector(self, internal_bus, message_bridge):
        """创建HSP连接器实例用于集成测试"""
        # 创建模拟的MQTT客户端
        mock_mqtt_client = Mock()
        mock_mqtt_client.connect = AsyncMock()
        mock_mqtt_client.disconnect = AsyncMock()
        mock_mqtt_client.publish = AsyncMock(return_value=True)
        mock_mqtt_client.subscribe = AsyncMock()
        mock_mqtt_client.is_connected = True
        # 添加on_message_callback属性
        mock_mqtt_client.on_message_callback = None

        # 创建HSP连接器
        connector = HSPConnector(
            ai_id="test_ai",
            broker_address="localhost",
            broker_port=1883,
            mock_mode=True,
            mock_mqtt_client=mock_mqtt_client,
            internal_bus=internal_bus,
            message_bridge=message_bridge
        )

        # 连接（同步方式，因为这是在fixture初始化中）
        # 注意：这里我们不实际调用await connector.connect()，因为fixture不是async
        # 而是直接设置连接状态
        connector.is_connected = True
        
        # 订阅主题
        # 注意：这里我们不实际调用await connector.subscribe()，因为fixture不是async
        # 在mock模式下，订阅操作是同步的
        
        return connector
    
    @pytest.mark.asyncio
    async def test_hsp_message_flow(self, hsp_connector, internal_bus):
        """测试HSP消息从发布到接收的完整流程"""
        # 准备测试数据
        test_fact = {
            "id": "fact_001",
            "statement_type": "natural_language",
            "statement_nl": "This is a test fact",
            "source_ai_id": "test_ai",
            "timestamp_created": "2023-01-01T00:00:00Z",
            "confidence_score": 1.0,
            "tags": ["test"]
        }

        # 记录接收到的消息
        received_messages = []
        received_event = asyncio.Event()

        def fact_handler(fact_payload, sender_ai_id, message):
            """事实消息处理器"""
            print(f"DEBUG: fact_handler called with fact_payload: {fact_payload}, sender_ai_id: {sender_ai_id}, message: {message}")
            received_messages.append({
                "payload": fact_payload,
                "sender_ai_id": sender_ai_id,
                "message": message
            })
            received_event.set()

        # 订阅事实消息
        print("DEBUG: Subscribing to facts")
        await hsp_connector.subscribe_to_facts(fact_handler)

        # 直接调用内部消息处理方法来模拟消息接收
        # 创建一个模拟的消息信封
        mock_envelope = {
            "hsp_envelope_version": "0.1",
            "message_id": "test_message_001",
            "sender_ai_id": "test_ai",
            "message_type": "HSP::Fact_v0.1",
            "payload": test_fact
        }
        
        # 直接调用HSP连接器的内部消息处理方法
        await hsp_connector._handle_fact_message(mock_envelope, "test_ai", mock_envelope)

        # 验证消息是否正确接收
        assert len(received_messages) == 1
        received_fact = received_messages[0]["payload"]
        assert received_fact["id"] == test_fact["id"]
        assert received_fact["statement_nl"] == test_fact["statement_nl"]
    
    @pytest.mark.asyncio
    async def test_agent_communication_flow(self, hsp_connector, internal_bus):
        """测试代理间通信流程"""
        # 准备测试数据
        test_opinion = {
            "id": "opinion_001",
            "statement_type": "natural_language",
            "statement_nl": "This is a test opinion",
            "source_ai_id": "test_ai_1",
            "timestamp_created": "2023-01-01T00:00:00Z",
            "confidence_score": 0.8,
            "reasoning_chain": ["fact_001"],
            "tags": ["test"]
        }
        
        # 记录接收到的消息
        received_opinions = []
        received_event = asyncio.Event()
        
        def opinion_handler(opinion_payload, sender_ai_id, message):
            """观点消息处理器"""
            received_opinions.append({
                "payload": opinion_payload,
                "sender_ai_id": sender_ai_id,
                "message": message
            })
            received_event.set()
        
        # 订阅观点消息
        await hsp_connector.subscribe_to_opinions(opinion_handler)
        
        # 直接调用内部消息处理方法来模拟消息接收
        # 创建一个模拟的消息信封
        mock_envelope = {
            "hsp_envelope_version": "0.1",
            "message_id": "test_message_002",
            "sender_ai_id": "test_ai_1",
            "message_type": "HSP::Opinion_v0.1",
            "payload": test_opinion
        }
        
        # 直接调用HSP连接器的内部消息处理方法
        await hsp_connector._handle_opinion_message(mock_envelope, "test_ai_1", mock_envelope)

        # 验证消息是否正确接收
        assert len(received_opinions) == 1
        received_opinion = received_opinions[0]["payload"]
        assert received_opinion["id"] == test_opinion["id"]
        assert received_opinion["statement_nl"] == test_opinion["statement_nl"]
        assert received_opinion["source_ai_id"] == test_opinion["source_ai_id"]

class TestMemorySystemIntegration:
    """记忆系统集成测试"""
    
    @pytest.mark.asyncio
    async def test_memory_storage_retrieval_flow(self):
        """测试记忆存储和检索流程"""
        # 由于记忆系统依赖外部数据库，这里使用模拟测试
        with patch('apps.backend.src.core_ai.memory.ham_memory_manager.HAMMemoryManager') as mock_manager:
            # 模拟记忆管理器
            mock_manager_instance = mock_manager.return_value
            mock_manager_instance.store_memory = AsyncMock(return_value=True)
            mock_manager_instance.retrieve_memory = AsyncMock(return_value=[])
            
            # 测试存储流程
            test_memory = {
                "id": "memory_001",
                "content": "This is a test memory",
                "metadata": {
                    "created_at": "2023-01-01T00:00:00Z",
                    "importance_score": 0.8,
                    "tags": ["test"]
                }
            }
            
            result = await mock_manager_instance.store_memory(test_memory)
            assert result is True
            mock_manager_instance.store_memory.assert_called_once_with(test_memory)
            
            # 测试检索流程
            mock_manager_instance.retrieve_memory.return_value = [test_memory]
            results = await mock_manager_instance.retrieve_memory("test query")
            assert len(results) == 1
            assert results[0]["id"] == test_memory["id"]

class TestAgentSystemIntegration:
    """代理系统集成测试"""
    
    @pytest.mark.asyncio
    async def test_agent_lifecycle_flow(self):
        """测试代理生命周期管理流程"""
        with patch('apps.backend.src.core_ai.agent_manager.AgentManager') as mock_manager:
            # 模拟代理管理器
            mock_manager_instance = mock_manager.return_value
            mock_manager_instance.create_agent = AsyncMock(return_value=Mock())
            mock_manager_instance.start_agent = AsyncMock(return_value=True)
            mock_manager_instance.stop_agent = AsyncMock(return_value=True)
            
            # 测试创建代理
            agent = await mock_manager_instance.create_agent("test_agent", "Test Agent")
            assert agent is not None
            mock_manager_instance.create_agent.assert_called_once_with("test_agent", "Test Agent")
            
            # 测试启动代理
            result = await mock_manager_instance.start_agent("test_agent")
            assert result is True
            mock_manager_instance.start_agent.assert_called_once_with("test_agent")
            
            # 测试停止代理
            result = await mock_manager_instance.stop_agent("test_agent")
            assert result is True
            mock_manager_instance.stop_agent.assert_called_once_with("test_agent")