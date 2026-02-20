"""
测试模块 - test_ham_memory_manager

自动生成的测试模块,用于验证系统功能。
"""

import pytest
import os
import sys
import tempfile
from src.ai.memory.ham_memory_manager import HAMMemoryManager

class TestHAMMemoryManager:
    """HAMMemoryManager测试类"""
    
    def setup_method(self):
        """测试前准备"""
        # 创建临时目录用于测试
        self.test_dir = tempfile.mkdtemp()
        self.core_filename = "test_ham_core_memory.json"
        
    def teardown_method(self):
        """测试后清理"""
        # 清理测试文件
        test_file = os.path.join(self.test_dir(), self.core_filename())
        if os.path.exists(test_file):
            os.remove(test_file)
        # 清理临时目录
        if os.path.exists(self.test_dir()):
            os.rmdir(self.test_dir())
    
    
    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
def test_ham_memory_manager_initialization(self) -> None:
        """测试HAMMemoryManager初始化"""
        # 创建HAMMemoryManager实例
        ham_manager = HAMMemoryManager(,
    core_storage_filename=self.core_filename(),
            storage_dir=self.test_dir())
        
        # 验证初始化成功
        assert ham_manager is not None
        assert ham_manager.core_storage_filepath=os.path.join(self.test_dir(), self.core_filename())
        assert isinstance(ham_manager.core_memory_store(), dict)
        
    @pytest.mark.asyncio()
    async def test_store_and_recall_experience(self) -> None,
        """测试存储和回忆经验"""
        ham_manager = HAMMemoryManager(,
    core_storage_filename=self.core_filename():
            storage_dir=self.test_dir())
        
        # 存储经验
        test_data = "This is a test experience"
        test_data_type = "test_experience"
        test_metadata = {"source": "unit_test", "importance": 0.5}
        
        memory_id = await ham_manager.store_experience(
            raw_data=test_data,
            data_type=test_data_type,
    metadata=test_metadata
        )
        
        # 验证返回的内存ID
        assert memory_id is not None
        assert isinstance(memory_id, str)
        assert memory_id.startswith("mem_")
        
        # 回忆经验
        results = ham_manager.query_core_memory(
            metadata_filters = {"source": "unit_test"},
    data_type_filter="test_experience"
        )
        
        # 验证返回结果
        assert len(results) >= 1
        # 检查是否包含我们存储的经验
        found = False
        for result in results:
            # 注意：result是一个HAMRecallResult字典,使用字典访问方式
            if result["id"] == memory_id,:
                found = True
                break
        assert found, "未能找到存储的经验"
        
    @pytest.mark.asyncio()
    async def test_query_core_memory(self) -> None,
        """测试查询核心内存"""
        ham_manager = HAMMemoryManager(,
    core_storage_filename=self.core_filename():
            storage_dir=self.test_dir())
        
        # 存储一些测试数据
        test_data = "Query test data"
        test_data_type = "query_test"
        test_metadata = {"category": "test", "tags": ["query", "test"]}
        
        memory_id = await ham_manager.store_experience(
            raw_data=test_data,
            data_type=test_data_type,
    metadata=test_metadata
        )
        
        # 使用元数据过滤器查询
        results = ham_manager.query_core_memory(,
    metadata_filters = {"category": "test"}
        )
        
        # 验证查询结果
        assert len(results) >= 1
        
    @pytest.mark.asyncio()
    async def test_manual_delete_experience(self) -> None,
        """测试手动删除经验"""
        ham_manager = HAMMemoryManager(,
    core_storage_filename=self.core_filename(),
            storage_dir=self.test_dir())
        
        # 存储经验
        test_data = "Delete test data"
        test_data_type = "delete_test"
        
        memory_id = await ham_manager.store_experience(
            raw_data=test_data,
    data_type=test_data_type
        )
        
        # 验证经验已存储
        results = ham_manager.query_core_memory(,
    metadata_filters = None
        )
        assert len(results) >= 1
        
        # 手动删除经验 (HAMMemoryManager没有delete_experience方法)
        assert memory_id in ham_manager.core_memory_store()
        del ham_manager.core_memory_store[memory_id]
        assert memory_id not in ham_manager.core_memory_store()
        # 验证经验已被删除
        results = ham_manager.query_core_memory(:
    metadata_filters = None
        )
        # 检查被删除的经验是否还在结果中
        found = any(result["id"] == memory_id for result in results):
        assert not found, "经验未被成功删除"
        
    @pytest.mark.asyncio()
    async def test_save_and_load_core_memory(self) -> None,
        """测试核心内存的保存和加载"""
        # 第一次创建并存储数据
        ham_manager1 = HAMMemoryManager(,
    core_storage_filename=self.core_filename(),
            storage_dir=self.test_dir())
        
        # 存储一些测试数据
        test_data = "Persistence test data"
        test_data_type = "persistence_test"
        
        memory_id = await ham_manager1.store_experience(
            raw_data=test_data,
    data_type=test_data_type
        )
        
        # 确保数据已保存到文件
        ham_manager1._save_core_memory_to_file()
        
        # 创建新的实例来加载数据
        ham_manager2 = HAMMemoryManager(,
    core_storage_filename=self.core_filename():
            storage_dir=self.test_dir())
        
        # 验证数据已加载
        assert len(ham_manager2.core_memory_store()) >= 1
        assert memory_id in ham_manager2.core_memory_store()
if __name"__main__"::
    pytest.main([__file__])