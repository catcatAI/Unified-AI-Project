import asyncio
import logging
import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch, AsyncMock

# 修复导入路径
from src.ai.memory.ham_memory_manager import HAMMemoryManager
from src.ai.memory.ham_types import DialogueMemoryEntryMetadata
from src.ai.memory.importance_scorer import ImportanceScorer

class TestHAMMemoryManager:
    """HAMMemoryManager单元测试"""
    
    @pytest.fixture
    def memory_manager(self):
        """创建HAMMemoryManager实例"""
        # 设置环境变量以禁用向量存储
        os.environ["HAM_DISABLE_VECTOR_STORE"] = "1"
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = HAMMemoryManager(storage_dir=temp_dir)
            yield manager
    
    @pytest.fixture
    def sample_memory_metadata(self):
        """创建示例记忆元数据"""
        from datetime import datetime
        return DialogueMemoryEntryMetadata(
            timestamp=datetime.fromisoformat("2023-01-01T00:00:00"),
            speaker="test_user",
            dialogue_id="test_dialogue_001",
            turn_id=1,
            language="en",
            tags=["test", "sample"]
        )
    
    def test_init(self, memory_manager):
        """测试初始化"""
        assert memory_manager is not None
        assert hasattr(memory_manager, 'storage_dir')
        assert hasattr(memory_manager, 'vector_store')
        assert hasattr(memory_manager, 'importance_scorer')
    
    def test_generate_id(self, memory_manager):
        """测试ID生成"""
        id1 = memory_manager._generate_memory_id()
        id2 = memory_manager._generate_memory_id()
        assert id1 != id2
        assert len(id1) > 0
    
    @pytest.mark.asyncio
    async def test_store_memory(self, memory_manager, sample_memory_metadata):
        """测试存储记忆"""
        result = await memory_manager.store_experience(
            "This is a test memory item", 
            "text", 
            sample_memory_metadata
        )
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_recall_gist(self, memory_manager, sample_memory_metadata):
        """测试回忆记忆"""
        # 先存储一个记忆
        memory_id = await memory_manager.store_experience(
            "This is a test memory item", 
            "text", 
            sample_memory_metadata
        )
        
        # 然后回忆它
        result = memory_manager.recall_gist(memory_id)
        assert result is not None
        assert result["id"] == memory_id
    
    @pytest.mark.asyncio
    async def test_query_core_memory(self, memory_manager, sample_memory_metadata):
        """测试查询核心记忆"""
        # 先存储一个记忆
        await memory_manager.store_experience(
            "This is a test memory item", 
            "text", 
            sample_memory_metadata
        )
        
        # 然后查询它
        results = memory_manager.query_core_memory(keywords=["test"])
        assert isinstance(results, list)