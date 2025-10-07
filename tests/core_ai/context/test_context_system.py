"""上下文系统测试"""

import pytest
import tempfile
import shutil
from context.storage.memory import MemoryStorage
from context.storage.disk import DiskStorage
from context.tool_context import ToolContextManager
from context.model_context import ModelContextManager, AgentContextManager
from context.dialogue_context import DialogueContextManager
from context.memory_context import MemoryContextManager

class TestContextSystem:
    """上下文系统测试"""
    
    def setup_method(self):
        """测试前准备"""
        # 创建临时目录用于磁盘存储测试
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """测试后清理"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    
    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
def test_context_manager_initialization(self) -> None:
        """测试上下文管理器初始化"""
        context_manager = ContextManager()
        assert context_manager is not None
        assert isinstance(context_manager.memory_storage, MemoryStorage)
        assert isinstance(context_manager.disk_storage, DiskStorage)
    
    def test_create_and_get_context(self) -> None:
        """测试创建和获取上下文"""
        context_manager = ContextManager()
        
        # 创建上下文
        context_id = context_manager.create_context(
            ContextType.TOOL, 
            {"test": "data"}
        )
        assert context_id is not None
        assert isinstance(context_id, str)
        
        # 获取上下文
        context = context_manager.get_context(context_id)
        assert context is not None
        assert context.context_id == context_id
        assert context.context_type == ContextType.TOOL
        assert context.content == {"test": "data"}
    
    def test_update_context(self) -> None:
        """测试更新上下文"""
        context_manager = ContextManager()
        
        # 创建上下文
        context_id = context_manager.create_context(
            ContextType.MODEL, 
            {"initial": "data"}
        )
        
        # 更新上下文
        success = context_manager.update_context(
            context_id, 
            {"updated": "data", "new_field": "value"}
        )
        assert success is True
        
        # 验证更新
        context = context_manager.get_context(context_id)
        assert context is not None
        assert context.content["initial"] == "data"
        assert context.content["updated"] == "data"
        assert context.content["new_field"] == "value"
    
    def test_delete_context(self) -> None:
        """测试删除上下文"""
        context_manager = ContextManager()
        
        # 创建上下文
        context_id = context_manager.create_context(
            ContextType.DIALOGUE, 
            {"test": "data"}
        )
        
        # 删除上下文
        success = context_manager.delete_context(context_id)
        assert success is True
        
        # 验证删除
        context = context_manager.get_context(context_id)
        assert context is None
    
    def test_search_contexts(self) -> None:
        """测试搜索上下文"""
        context_manager = ContextManager()
        
        # 创建多个上下文
        context_manager.create_context(
            ContextType.TOOL, 
            {"name": "工具A", "description": "测试工具"}
        )
        context_manager.create_context(
            ContextType.TOOL, 
            {"name": "工具B", "description": "另一个测试工具"}
        )
        context_manager.create_context(
            ContextType.MODEL, 
            {"name": "模型A", "description": "测试模型"}
        )
        
        # 搜索工具上下文
        tool_contexts = context_manager.search_contexts("测试", [ContextType.TOOL])
        assert len(tool_contexts) == 2
        
        # 搜索模型上下文
        model_contexts = context_manager.search_contexts("测试", [ContextType.MODEL])
        assert len(model_contexts) == 1
        
        # 搜索所有上下文
        all_contexts = context_manager.search_contexts("测试")
        assert len(all_contexts) == 3
    
    def test_tool_context_manager(self) -> None:
        """测试工具上下文管理器"""
        context_manager = ContextManager()
        tool_manager = ToolContextManager(context_manager)
        
        # 创建工具分类
        success = tool_manager.create_tool_category("cat_001", "测试分类", "测试描述")
        assert success is True
        
        # 注册工具
        success = tool_manager.register_tool("tool_001", "测试工具", "测试工具描述", "cat_001")
        assert success is True
        
        # 记录工具使用
        success = tool_manager.record_tool_usage(
            "tool_001", 
            {"input": "test"}, 
            "result", 
            0.5, 
            True
        )
        assert success is True
        
        # 获取工具上下文
        tool_context = tool_manager.get_tool_context("tool_001")
        assert tool_context is not None
    
    def test_model_context_manager(self) -> None:
        """测试模型上下文管理器"""
        context_manager = ContextManager()
        model_manager = ModelContextManager(context_manager)
        
        # 记录模型调用
        success = model_manager.record_model_call(
            "model_A", 
            "model_B", 
            {"task": "test"}, 
            "result", 
            1.0, 
            True
        )
        assert success is True
        
        # 获取模型上下文
        model_context = model_manager.get_model_context("model_A")
        assert model_context is not None
        
        # 获取模型调用历史
        call_history = model_manager.get_model_call_history("model_A")
        assert len(call_history) == 1
    
    def test_agent_context_manager(self) -> None:
        """测试代理上下文管理器"""
        context_manager = ContextManager()
        agent_manager = AgentContextManager(context_manager)
        
        # 开始协作
        collaboration_id = agent_manager.start_collaboration(
            "task_001", 
            ["agent_001", "agent_002"]
        )
        assert collaboration_id is not None
        
        # 记录协作步骤
        success = agent_manager.record_collaboration_step(
            collaboration_id,
            "agent_001",
            "test_action",
            "input",
            "output",
            0.5
        )
        assert success is True
        
        # 完成协作
        success = agent_manager.complete_collaboration(collaboration_id)
        assert success is True
        
        # 获取协作上下文
        collab_context = agent_manager.get_collaboration_context(collaboration_id)
        assert collab_context is not None
    
    def test_dialogue_context_manager(self) -> None:
        """测试对话上下文管理器"""
        context_manager = ContextManager()
        dialogue_manager = DialogueContextManager(context_manager)
        
        # 开始对话
        conversation_id = "test_conv_001"
        success = dialogue_manager.start_conversation(conversation_id, ["user", "ai"])
        assert success is True
        
        # 添加消息
        success = dialogue_manager.add_message(conversation_id, "user", "测试消息")
        assert success is True
        
        # 生成上下文摘要
        summary = dialogue_manager.generate_context_summary(conversation_id)
        assert summary is not None
        
        # 获取对话上下文
        conv_context = dialogue_manager.get_conversation_context(conversation_id)
        assert conv_context is not None
    
    def test_memory_context_manager(self) -> None:
        """测试记忆上下文管理器"""
        context_manager = ContextManager()
        memory_manager = MemoryContextManager(context_manager)
        
        # 创建记忆
        memory_id = memory_manager.create_memory(
            "测试记忆内容", 
            "short_term",
            {"test": "metadata"}
        )
        assert memory_id is not None
        
        # 访问记忆
        memory_data = memory_manager.access_memory(memory_id)
        assert memory_data is not None
        assert memory_data["access_count"] == 1
        
        # 更新记忆向量表示
        success = memory_manager.update_memory_embedding(memory_id, [0.1, 0.2, 0.3])
        assert success is True
        
        # 获取记忆上下文
        mem_context = memory_manager.get_memory_context(memory_id)
        assert mem_context is not None
        
        # 转移记忆
        new_memory_id = memory_manager.transfer_memory(memory_id, "long_term")
        assert new_memory_id is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])