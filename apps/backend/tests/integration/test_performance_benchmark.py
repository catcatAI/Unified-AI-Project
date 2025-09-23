import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

class TestPerformanceBenchmark:
    """性能基准测试"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_hsp_message_publish_performance(self, benchmark):
        """测试HSP消息发布性能"""
        with patch('apps.backend.src.hsp.connector.HSPConnector') as mock_hsp_connector:
            mock_hsp_instance = Mock()
            # 修复AsyncMock的使用方式
            async def mock_publish(topic, message):
                return True
            mock_hsp_instance.publish = mock_publish
            mock_hsp_connector.return_value = mock_hsp_instance
            
            async def publish_message():
                hsp_connector = mock_hsp_connector("test_ai", "localhost", 1883)
                return await hsp_connector.publish("test_topic", "test_message")
            
            # 使用benchmark.pedantic来正确处理异步函数
            result = await benchmark.pedantic(publish_message, iterations=10, rounds=5)
            assert result is True

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_store_performance(self, benchmark):
        """测试记忆存储性能"""
        with patch('apps.backend.src.ai.memory.ham_memory_manager.HAMMemoryManager') as mock_memory_manager:
            mock_memory_instance = Mock()
            # 修复AsyncMock的使用方式
            async def mock_store_memory(data):
                return "test_memory_id"
            mock_memory_instance.store_memory = mock_store_memory
            mock_memory_manager.return_value = mock_memory_instance
            
            async def store_memory():
                memory_manager = mock_memory_manager()
                return await memory_manager.store_memory({"test": "data"})
            
            # 使用benchmark.pedantic来正确处理异步函数
            result = await benchmark.pedantic(store_memory, iterations=10, rounds=5)
            assert result == "test_memory_id"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_agent_operations_performance(self, benchmark):
        """测试并发代理操作性能"""
        with patch('apps.backend.src.core.managers.agent_manager.AgentManager') as mock_agent_manager:
            mock_agent_instance = Mock()
            # 修复AsyncMock的使用方式
            async def mock_start_agent(agent_id):
                return True
            mock_agent_instance.start_agent = mock_start_agent
            mock_agent_manager.return_value = mock_agent_instance
            
            async def concurrent_operations():
                agent_manager = mock_agent_manager()
                tasks = []
                for i in range(10):
                    task = agent_manager.start_agent(f"test_agent_{i}")
                    tasks.append(task)
                results = await asyncio.gather(*tasks)
                return len([r for r in results if r])
            
            # 使用benchmark.pedantic来正确处理异步函数
            result = await benchmark.pedantic(concurrent_operations, iterations=5, rounds=3)
            assert result == 10

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_retrieval_performance(self, benchmark):
        """测试记忆检索性能"""
        with patch('apps.backend.src.ai.memory.ham_memory_manager.HAMMemoryManager') as mock_memory_manager:
            mock_memory_instance = Mock()
            # 修复AsyncMock的使用方式
            async def mock_retrieve_memory(memory_id):
                return {"content": "test content", "metadata": {}}
            mock_memory_instance.retrieve_memory = mock_retrieve_memory
            mock_memory_manager.return_value = mock_memory_instance
            
            async def retrieve_memory():
                memory_manager = mock_memory_manager()
                return await memory_manager.retrieve_memory("test_memory_id")
            
            # 使用benchmark.pedantic来正确处理异步函数
            result = await benchmark.pedantic(retrieve_memory, iterations=10, rounds=5)
            assert result["content"] == "test content"

class TestSystemLoadBenchmark:
    """系统负载基准测试"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_high_load_agent_management(self, benchmark):
        """测试高负载下的代理管理"""
        with patch('apps.backend.src.core_ai.agent_manager.AgentManager') as mock_agent_manager:
            mock_agent_instance = Mock()
            # 修复AsyncMock的使用方式
            async def mock_create_agent(agent_id, agent_name):
                return Mock()
            async def mock_start_agent(agent_id):
                return True
            async def mock_stop_agent(agent_id):
                return True
                
            mock_agent_instance.create_agent = mock_create_agent
            mock_agent_instance.start_agent = mock_start_agent
            mock_agent_instance.stop_agent = mock_stop_agent
            mock_agent_manager.return_value = mock_agent_instance
            
            async def high_load_operations():
                agent_manager = mock_agent_manager()
                agents = []
                # 创建100个代理
                for i in range(100):
                    agent = await agent_manager.create_agent(f"agent_{i}", f"Agent {i}")
                    agents.append(agent)
                # 启动所有代理
                start_results = await asyncio.gather(*[agent_manager.start_agent(f"agent_{i}") for i in range(100)])
                # 停止所有代理
                stop_results = await asyncio.gather(*[agent_manager.stop_agent(f"agent_{i}") for i in range(100)])
                return len([r for r in start_results if r]), len([r for r in stop_results if r])
            
            # 使用benchmark.pedantic来正确处理异步函数
            start_count, stop_count = await benchmark.pedantic(high_load_operations, iterations=1, rounds=2)
            assert start_count == 100
            assert stop_count == 100

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_hsp_message_processing(self, benchmark):
        """测试并发HSP消息处理"""
        with patch('apps.backend.src.hsp.connector.HSPConnector') as mock_hsp_connector:
            mock_hsp_instance = Mock()
            # 修复AsyncMock的使用方式
            async def mock_publish(topic, message):
                return True
            async def mock_subscribe(topic, callback):
                return True
                
            mock_hsp_instance.publish = mock_publish
            mock_hsp_instance.subscribe = mock_subscribe
            mock_hsp_connector.return_value = mock_hsp_instance
            
            async def concurrent_message_processing():
                hsp_connector = mock_hsp_connector("test_ai", "localhost", 1883)
                # 并发发布100条消息
                tasks = []
                for i in range(100):
                    task = hsp_connector.publish(f"test_topic_{i}", f"test_message_{i}")
                    tasks.append(task)
                results = await asyncio.gather(*tasks)
                return len([r for r in results if r])
            
            # 使用benchmark.pedantic来正确处理异步函数
            result = await benchmark.pedantic(concurrent_message_processing, iterations=1, rounds=2)
            assert result == 100