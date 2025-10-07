"""
HSP协议系统集成测试
测试HSP协议系统与其他核心组件的集成
"""

import pytest
from apps.backend.tests.integration.base_test import SystemIntegrationTest
from apps.backend.tests.integration.test_data_factory import TestDataFactory


class TestHSPProtocolIntegration(SystemIntegrationTest):
    """HSP协议系统集成测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_hsp_test(self, setup_system_test):
        """设置HSP测试"""
        self.data_factory = TestDataFactory()
        yield
    
    @pytest.mark.system_integration
    @pytest.mark.asyncio
    async 
    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
def test_hsp_connection_integration(self) -> None:
        """测试HSP连接集成"""
        # 创建测试数据
        connection_config = {
            "broker_host": "localhost",
            "broker_port": 1883,
            "client_id": "test_hsp_client"
        }
        
        # 获取mock服务
        hsp_connector = self.get_mock_service("hsp_connector")
        
        # 设置mock行为
        hsp_connector.return_value.connect = AsyncMock(return_value=True)
        hsp_connector.return_value.disconnect = AsyncMock(return_value=True)
        hsp_connector.return_value.is_connected = Mock(return_value=True)
        
        # 执行HSP连接测试
        # 1. 建立连接
        connect_result = await hsp_connector.return_value.connect(
            connection_config["broker_host"],
            connection_config["broker_port"]
        )
        
        # 2. 验证连接状态
        is_connected = hsp_connector.return_value.is_connected()
        
        # 3. 断开连接
        disconnect_result = await hsp_connector.return_value.disconnect()
        
        # 验证结果
        assert connect_result is True
        assert is_connected is True
        assert disconnect_result is True
        
        # 验证mock调用
        hsp_connector.return_value.connect.assert_called_once_with(
            connection_config["broker_host"],
            connection_config["broker_port"]
        )
        
        hsp_connector.return_value.disconnect.assert_called_once()
    
    @pytest.mark.system_integration
    @pytest.mark.asyncio
    async def test_hsp_message_publish_subscribe_integration(self) -> None:
        """测试HSP消息发布订阅集成"""
        # 创建测试数据
        test_fact = self.data_factory.create_hsp_message(
            message_type="fact",
            content="This is a test fact for HSP integration"
        )
        
        test_opinion = self.data_factory.create_hsp_message(
            message_type="opinion",
            content="This is a test opinion for HSP integration"
        )
        
        # 获取mock服务
        hsp_connector = self.get_mock_service("hsp_connector")
        
        # 设置mock行为
        hsp_connector.return_value.publish = AsyncMock(return_value=True)
        hsp_connector.return_value.subscribe = AsyncMock(return_value=True)
        hsp_connector.return_value.unsubscribe = AsyncMock(return_value=True)
        
        # 执行消息发布订阅测试
        # 1. 订阅主题
        subscribe_result = await hsp_connector.return_value.subscribe(
            "hsp/test/facts"
        )
        
        # 2. 发布事实消息
        publish_fact_result = await hsp_connector.return_value.publish(
            test_fact,
            "hsp/test/facts"
        )
        
        # 3. 发布观点消息
        publish_opinion_result = await hsp_connector.return_value.publish(
            test_opinion,
            "hsp/test/opinions"
        )
        
        # 4. 取消订阅
        unsubscribe_result = await hsp_connector.return_value.unsubscribe(
            "hsp/test/facts"
        )
        
        # 验证结果
        assert subscribe_result is True
        assert publish_fact_result is True
        assert publish_opinion_result is True
        assert unsubscribe_result is True
        
        # 验证mock调用
        hsp_connector.return_value.subscribe.assert_called_once_with(
            "hsp/test/facts"
        )
        
        hsp_connector.return_value.publish.assert_any_call(
            test_fact,
            "hsp/test/facts"
        )
        
        hsp_connector.return_value.publish.assert_any_call(
            test_opinion,
            "hsp/test/opinions"
        )
        
        hsp_connector.return_value.unsubscribe.assert_called_once_with(
            "hsp/test/facts"
        )
    
    @pytest.mark.system_integration
    @pytest.mark.asyncio
    async def test_hsp_agent_communication_integration(self) -> None:
        """测试HSP代理通信集成"""
        # 创建测试数据
        sender_agent_config = self.data_factory.create_agent_config(
            agent_id="sender_agent_hsp",
            agent_type="creative_writing"
        )
        
        receiver_agent_config = self.data_factory.create_agent_config(
            agent_id="receiver_agent_hsp",
            agent_type="data_analysis"
        )
        
        task_request = self.data_factory.create_hsp_message(
            message_type="request",
            content="Please analyze this dataset",
            source=sender_agent_config["agent_id"],
            target=receiver_agent_config["agent_id"]
        )
        
        task_response = self.data_factory.create_hsp_message(
            message_type="response",
            content="Analysis complete. Key insights: ...",
            source=receiver_agent_config["agent_id"],
            target=sender_agent_config["agent_id"]
        )
        
        # 获取mock服务
        hsp_connector = self.get_mock_service("hsp_connector")
        agent_manager = self.get_mock_service("agent_manager")
        
        # 设置mock行为
        mock_sender_agent = Mock()
        mock_receiver_agent = Mock()
        
        agent_manager.return_value.create_agent = AsyncMock(side_effect=[
            mock_sender_agent,
            mock_receiver_agent
        ])
        
        hsp_connector.return_value.publish = AsyncMock(return_value=True)
        hsp_connector.return_value.subscribe = AsyncMock(return_value=True)
        
        # 执行代理通信测试
        # 1. 创建代理
        sender_agent = await agent_manager.return_value.create_agent(
            sender_agent_config["agent_id"],
            sender_agent_config["agent_type"]
        )
        
        receiver_agent = await agent_manager.return_value.create_agent(
            receiver_agent_config["agent_id"],
            receiver_agent_config["agent_type"]
        )
        
        # 2. 发送任务请求
        request_result = await hsp_connector.return_value.publish(
            task_request,
            f"hsp/agents/{receiver_agent_config['agent_id']}/requests"
        )
        
        # 3. 订阅响应
        response_subscribe_result = await hsp_connector.return_value.subscribe(
            f"hsp/agents/{sender_agent_config['agent_id']}/responses"
        )
        
        # 4. 发送任务响应
        response_result = await hsp_connector.return_value.publish(
            task_response,
            f"hsp/agents/{sender_agent_config['agent_id']}/responses"
        )
        
        # 验证结果
        assert sender_agent is not None
        assert receiver_agent is not None
        assert request_result is True
        assert response_subscribe_result is True
        assert response_result is True
        
        # 验证mock调用
        assert agent_manager.return_value.create_agent.call_count == 2
        
        hsp_connector.return_value.publish.assert_any_call(
            task_request,
            f"hsp/agents/{receiver_agent_config['agent_id']}/requests"
        )
        
        hsp_connector.return_value.subscribe.assert_called_with(
            f"hsp/agents/{sender_agent_config['agent_id']}/responses"
        )
        
        hsp_connector.return_value.publish.assert_any_call(
            task_response,
            f"hsp/agents/{sender_agent_config['agent_id']}/responses"
        )


class TestHSPMessageRoutingIntegration(SystemIntegrationTest):
    """HSP消息路由集成测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_routing_test(self, setup_system_test):
        """设置路由测试"""
        self.data_factory = TestDataFactory()
        yield
    
    @pytest.mark.system_integration
    @pytest.mark.asyncio
    async def test_hsp_message_routing_integration(self) -> None:
        """测试HSP消息路由集成"""
        # 创建测试数据
        routing_messages = [
            self.data_factory.create_hsp_message(
                message_id=f"msg_{i}",
                message_type="fact",
                content=f"Test fact message {i}"
            )
            for i in range(5)
        ]
        
        # 获取mock服务
        hsp_connector = self.get_mock_service("hsp_connector")
        
        # 设置mock行为
        hsp_connector.return_value.publish = AsyncMock(return_value=True)
        hsp_connector.return_value.subscribe = AsyncMock(return_value=True)
        
        # 执行消息路由测试
        # 1. 订阅多个主题
        topics = [
            "hsp/routing/test1",
            "hsp/routing/test2",
            "hsp/routing/test3"
        ]
        
        subscribe_results = []
        for topic in topics:
            result = await hsp_connector.return_value.subscribe(topic)
            subscribe_results.append(result)
        
        # 2. 发布消息到不同主题
        publish_results = []
        for i, message in enumerate(routing_messages):
            topic = topics[i % len(topics)]
            result = await hsp_connector.return_value.publish(message, topic)
            publish_results.append(result)
        
        # 验证结果
        assert all(result is True for result in subscribe_results)
        assert all(result is True for result in publish_results)
        
        # 验证mock调用
        for topic in topics:
            hsp_connector.return_value.subscribe.assert_any_call(topic)
        
        for i, message in enumerate(routing_messages):
            topic = topics[i % len(topics)]
            hsp_connector.return_value.publish.assert_any_call(message, topic)
    
    @pytest.mark.system_integration
    @pytest.mark.asyncio
    async def test_hsp_broadcast_integration(self) -> None:
        """测试HSP广播集成"""
        # 创建测试数据
        broadcast_message = self.data_factory.create_hsp_message(
            message_type="broadcast",
            content="This is a broadcast message to all agents"
        )
        
        agent_configs = [
            self.data_factory.create_agent_config(
                agent_id=f"broadcast_agent_{i}",
                agent_type="base_agent"
            )
            for i in range(3)
        ]
        
        # 获取mock服务
        hsp_connector = self.get_mock_service("hsp_connector")
        agent_manager = self.get_mock_service("agent_manager")
        
        # 设置mock行为
        mock_agents = [Mock() for _ in agent_configs]
        agent_manager.return_value.create_agent = AsyncMock(side_effect=mock_agents)
        hsp_connector.return_value.publish = AsyncMock(return_value=True)
        hsp_connector.return_value.subscribe = AsyncMock(return_value=True)
        
        # 执行广播测试
        # 1. 创建代理
        created_agents = []
        for config in agent_configs:
            agent = await agent_manager.return_value.create_agent(
                config["agent_id"],
                config["agent_type"]
            )
            created_agents.append(agent)
        
        # 2. 订阅广播主题
        subscribe_result = await hsp_connector.return_value.subscribe(
            "hsp/broadcast/all"
        )
        
        # 3. 发送广播消息
        broadcast_result = await hsp_connector.return_value.publish(
            broadcast_message,
            "hsp/broadcast/all"
        )
        
        # 验证结果
        assert len(created_agents) == len(agent_configs)
        assert subscribe_result is True
        assert broadcast_result is True
        
        # 验证mock调用
        assert agent_manager.return_value.create_agent.call_count == len(agent_configs)
        hsp_connector.return_value.subscribe.assert_called_once_with(
            "hsp/broadcast/all"
        )
        hsp_connector.return_value.publish.assert_called_once_with(
            broadcast_message,
            "hsp/broadcast/all"
        )


class TestHSPQualityOfServiceIntegration(SystemIntegrationTest):
    """HSP服务质量集成测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_qos_test(self, setup_system_test):
        """设置QoS测试"""
        self.data_factory = TestDataFactory()
        yield
    
    @pytest.mark.system_integration
    @pytest.mark.asyncio
    async def test_hsp_qos_integration(self) -> None:
        """测试HSP服务质量集成"""
        # 创建测试数据
        high_priority_message = self.data_factory.create_hsp_message(
            message_type="critical",
            content="High priority critical message",
            metadata={"priority": "high", "qos": 2}
        )
        
        normal_priority_message = self.data_factory.create_hsp_message(
            message_type="info",
            content="Normal priority information message",
            metadata={"priority": "normal", "qos": 1}
        )
        
        # 获取mock服务
        hsp_connector = self.get_mock_service("hsp_connector")
        
        # 设置mock行为
        hsp_connector.return_value.publish = AsyncMock(return_value=True)
        hsp_connector.return_value.set_qos_level = Mock(return_value=True)
        
        # 执行QoS测试
        # 1. 设置QoS级别
        qos_result = hsp_connector.return_value.set_qos_level(2)
        
        # 2. 发布高优先级消息
        high_priority_result = await hsp_connector.return_value.publish(
            high_priority_message,
            "hsp/qos/critical",
            qos=2
        )
        
        # 3. 发布普通优先级消息
        normal_priority_result = await hsp_connector.return_value.publish(
            normal_priority_message,
            "hsp/qos/info",
            qos=1
        )
        
        # 验证结果
        assert qos_result is True
        assert high_priority_result is True
        assert normal_priority_result is True
        
        # 验证mock调用
        hsp_connector.return_value.set_qos_level.assert_called_once_with(2)
        
        hsp_connector.return_value.publish.assert_any_call(
            high_priority_message,
            "hsp/qos/critical",
            qos=2
        )
        
        hsp_connector.return_value.publish.assert_any_call(
            normal_priority_message,
            "hsp/qos/info",
            qos=1
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])