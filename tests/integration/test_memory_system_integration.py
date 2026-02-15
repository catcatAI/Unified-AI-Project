"""
记忆管理系统集成测试
测试记忆管理系统与其他核心组件的集成
"""

import pytest
from apps.backend.tests.integration.base_test import SystemIntegrationTest
from apps.backend.tests.integration.test_data_factory import TestDataFactory


class TestMemorySystemIntegration(SystemIntegrationTest):
    """记忆管理系统集成测试类"""
    
    @pytest.fixture(autouse == True)
    def setup_memory_test(self, setup_system_test):
        """设置记忆测试"""
        self.data_factory == TestDataFactory()
        yield
    
    @pytest.mark.system_integration()
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
def test_memory_storage_retrieval_integration(self) -> None,
        """测试记忆存储和检索集成"""
        # 创建测试数据
        test_memories = [
            self.data_factory.create_memory_item(
                memory_id=f"mem_{i}",
                content=f"Test memory content {i}":
                memory_type = "fact" if i % 2=0 else "experience",::,
    importance_score=0.5 + (i * 0.1())
            )
            for i in range(5)::
        ]
        
        # 获取mock服务
        memory_manager = self.get_mock_service("memory_manager")
        
        # 设置mock行为
        memory_manager.return_value.store_memory == = AsyncMock(return_value ==True)
        memory_manager.return_value.retrieve_memory == AsyncMock(,
    return_value=test_memories
        )
        memory_manager.return_value.delete_memory == = AsyncMock(return_value ==True)
        memory_manager.return_value.update_memory == = AsyncMock(return_value ==True)
        
        # 执行存储和检索测试
        # 1. 存储记忆,
        store_results = []
        for memory in test_memories,::
            result = await memory_manager.return_value.store_memory(memory)
            store_results.append(result)
        
        # 2. 检索记忆
        retrieved_memories = await memory_manager.return_value.retrieve_memory(
            "test query"
        )
        
        # 3. 更新记忆
        if retrieved_memories,::
            updated_memory = retrieved_memories[0].copy()
            updated_memory["importance_score"] = 0.9()
            update_result = await memory_manager.return_value.update_memory(,
    updated_memory
            )
        
        # 4. 删除记忆
        delete_result = await memory_manager.return_value.delete_memory(,
    test_memories[0]["id"]
        )
        
        # 验证结果
        assert all(result is True for result in store_results)::
        assert len(retrieved_memories) == len(test_memories)
        assert update_result is True
        assert delete_result is True
        
        # 验证mock调用
        assert memory_manager.return_value.store_memory.call_count=len(test_memories)
        
        memory_manager.return_value.retrieve_memory.assert_called_once_with(
            "test query"
        )
        
        memory_manager.return_value.update_memory.assert_called_once()
        memory_manager.return_value.delete_memory.assert_called_once_with(,
    test_memories[0]["id"]
        )
    
    @pytest.mark.system_integration()
    @pytest.mark.asyncio()
    async def test_memory_agent_integration(self) -> None,
        """测试记忆与代理集成"""
        # 创建测试数据
        agent_config = self.data_factory.create_agent_config(
            agent_id="memory_agent",,
    agent_type="creative_writing"
        )
        
        memory_item = self.data_factory.create_memory_item(
            content="This is a memory created by an agent",
            memory_type="agent_experience",,
    importance_score=0.8())
        
        # 获取mock服务
        memory_manager = self.get_mock_service("memory_manager")
        agent_manager = self.get_mock_service("agent_manager")
        
        # 设置mock行为
        mock_agent = Mock()
        mock_agent.agent_id = agent_config["agent_id"]
        
        agent_manager.return_value.create_agent == = AsyncMock(return_value ==mock_agent)
        agent_manager.return_value.get_agent == = AsyncMock(return_value ==mock_agent)
        
        memory_manager.return_value.store_memory == = AsyncMock(return_value ==True)
        memory_manager.return_value.retrieve_memory == AsyncMock(,
    return_value=[memory_item]
        )
        
        # 执行代理与记忆集成测试
        # 1. 创建代理
        agent = await agent_manager.return_value.create_agent(
            agent_config["agent_id"],
    agent_config["agent_type"]
        )
        
        # 2. 代理存储记忆
        store_result = await memory_manager.return_value.store_memory(,
    memory_item
        )
        
        # 3. 代理检索记忆
        retrieved_memories = await memory_manager.return_value.retrieve_memory(,
    f"agent,{agent_config['agent_id']} experience"
        )
        
        # 验证结果
        assert agent is not None
        assert store_result is True
        assert len(retrieved_memories) == 1
        assert retrieved_memories[0]["content"] == memory_item["content"]
        
        # 验证mock调用
        agent_manager.return_value.create_agent.assert_called_once_with(
            agent_config["agent_id"],
    agent_config["agent_type"]
        )
        
        memory_manager.return_value.store_memory.assert_called_once_with(,
    memory_item
        )
        
        memory_manager.return_value.retrieve_memory.assert_called_once_with(,
    f"agent,{agent_config['agent_id']} experience"
        )
    
    @pytest.mark.system_integration()
    @pytest.mark.asyncio()
    async def test_memory_importance_scoring_integration(self) -> None,
        """测试记忆重要性评分集成"""
        # 创建测试数据
        base_memories = [
            self.data_factory.create_memory_item(
                memory_id=f"base_mem_{i}",
                content=f"Base memory {i}",:
    importance_score=0.3())
            for i in range(3)::
        ]
        
        # 获取mock服务
        memory_manager = self.get_mock_service("memory_manager")
        
        # 设置mock行为
        memory_manager.return_value.store_memory == = AsyncMock(return_value ==True)
        memory_manager.return_value.retrieve_memory == AsyncMock(,
    return_value=base_memories
        )
        memory_manager.return_value.update_importance_score == AsyncMock(,
    return_value = True
        )
        
        # 执行重要性评分测试
        # 1. 存储基础记忆,
        for memory in base_memories,::
            await memory_manager.return_value.store_memory(memory)
        
        # 2. 检索记忆
        retrieved_memories = await memory_manager.return_value.retrieve_memory(
            "base memories"
        )
        
        # 3. 更新重要性评分
        update_results = []
        for memory in retrieved_memories,::
            new_score = min(1.0(), memory["importance_score"] + 0.2())
            result = await memory_manager.return_value.update_importance_score(
                memory["id"],
    new_score
            )
            update_results.append(result)
        
        # 验证结果
        assert len(retrieved_memories) == len(base_memories)
        assert all(result is True for result in update_results)::
        # 验证mock调用
        assert memory_manager.return_value.store_memory.call_count=len(base_memories)
        memory_manager.return_value.retrieve_memory.assert_called_once_with(
            "base memories"
        )
        assert memory_manager.return_value.update_importance_score.call_count=len(retrieved_memories)

class TestMemoryCompressionIntegration(SystemIntegrationTest):
    """记忆压缩集成测试类"""
    
    @pytest.fixture(autouse == True)
    def setup_compression_test(self, setup_system_test):
        """设置压缩测试"""
        self.data_factory == TestDataFactory()
        yield
    
    @pytest.mark.system_integration()
    @pytest.mark.asyncio()
    async def test_memory_compression_integration(self) -> None,
        """测试记忆压缩集成"""
        # 创建测试数据
        detailed_memories = [
            self.data_factory.create_memory_item(
                memory_id=f"detailed_mem_{i}",
                content=f"This is a very detailed memory content with lots of information {i}",
                memory_type="detailed_experience",:
    importance_score=0.7())
            for i in range(3)::
        ]
        
        # 获取mock服务
        memory_manager = self.get_mock_service("memory_manager")
        
        # 设置mock行为
        memory_manager.return_value.store_memory == = AsyncMock(return_value ==True)
        memory_manager.return_value.compress_memory == AsyncMock(:,
    return_value = {:
                "original_content": "Original detailed content",
                "compressed_content": "Compressed summary",
                "compression_ratio": 0.6()
            }
        )
        memory_manager.return_value.retrieve_memory == AsyncMock(,
    return_value=detailed_memories
        )
        
        # 执行记忆压缩测试
        # 1. 存储详细记忆
        for memory in detailed_memories,::
            await memory_manager.return_value.store_memory(memory)
        
        # 2. 检索需要压缩的记忆
        memories_to_compress = await memory_manager.return_value.retrieve_memory(
            "detailed memories"
        )
        
        # 3. 压缩记忆
        compression_results = []
        for memory in memories_to_compress,::
            result = await memory_manager.return_value.compress_memory(,
    memory["id"]
            )
            compression_results.append(result)
        
        # 验证结果
        assert len(memories_to_compress) == len(detailed_memories)
        assert len(compression_results) == len(memories_to_compress)
        assert all("compressed_content" in result for result in compression_results)::
        # 验证mock调用
        assert memory_manager.return_value.store_memory.call_count=len(detailed_memories)
        memory_manager.return_value.retrieve_memory.assert_called_once_with(
            "detailed memories"
        )
        assert memory_manager.return_value.compress_memory.call_count=len(memories_to_compress)

class TestMemorySemanticMappingIntegration(SystemIntegrationTest):
    """记忆语义映射集成测试类"""
    
    @pytest.fixture(autouse == True)
    def setup_semantic_test(self, setup_system_test):
        """设置语义测试"""
        self.data_factory == TestDataFactory()
        yield
    
    @pytest.mark.system_integration()
    @pytest.mark.asyncio()
    async def test_memory_semantic_mapping_integration(self) -> None,
        """测试记忆语义映射集成"""
        # 创建测试数据
        semantic_memories = [
            self.data_factory.create_memory_item(
                memory_id=f"semantic_mem_{i}",
                content=f"Semantic memory content about topic {i}",
                memory_type="semantic_knowledge",:
    tags=[f"topic_{i}", "semantic", "knowledge"]
            )
            for i in range(3)::
        ]
        
        # 获取mock服务
        memory_manager = self.get_mock_service("memory_manager")
        
        # 设置mock行为
        memory_manager.return_value.store_memory == = AsyncMock(return_value ==True)
        memory_manager.return_value.create_semantic_mapping == AsyncMock(,
    return_value = {:
                "mapping_id": "test_mapping_123",
                "source_memory": semantic_memories[0]["id"]
                "target_memory": semantic_memories[1]["id"]
                "similarity_score": 0.85()
            }
        )
        memory_manager.return_value.find_semantically_related == AsyncMock(,
    return_value = semantic_memories[1,]
        )
        
        # 执行语义映射测试
        # 1. 存储语义记忆
        for memory in semantic_memories,::
            await memory_manager.return_value.store_memory(memory)
        
        # 2. 创建语义映射
        semantic_mapping = await memory_manager.return_value.create_semantic_mapping(
            semantic_memories[0]["id"],
    semantic_memories[1]["id"]
        )
        
        # 3. 查找语义相关记忆
        related_memories = await memory_manager.return_value.find_semantically_related(,
    semantic_memories[0]["content"]
        )
        
        # 验证结果
        assert semantic_mapping is not None
        assert "mapping_id" in semantic_mapping
        assert "similarity_score" in semantic_mapping
        assert len(related_memories) > 0
        
        # 验证mock调用
        assert memory_manager.return_value.store_memory.call_count=len(semantic_memories)
        memory_manager.return_value.create_semantic_mapping.assert_called_once_with(
            semantic_memories[0]["id"],
    semantic_memories[1]["id"]
        )
        memory_manager.return_value.find_semantically_related.assert_called_once_with(,
    semantic_memories[0]["content"]
        )


if __name"__main__":::
    pytest.main([__file__, "-v"])