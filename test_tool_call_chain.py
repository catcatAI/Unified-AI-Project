"""
工具调用链追踪测试用例
"""

import unittest
import logging
from unittest.mock import Mock, patch
from tool_call_chain_tracker import ToolCallChainTracker, ToolCallChainContext, ToolCallChain, ToolCallNode
from apps.backend.src.core_ai.context.manager import ContextManager
from apps.backend.src.core_ai.context.storage.base import ContextType

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestToolCallChainTracker(unittest.TestCase):
    """工具调用链追踪器测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.context_manager = Mock(spec=ContextManager)
        self.context_manager.create_context.return_value = "test_context_id"
        self.tracker = ToolCallChainTracker(self.context_manager)
        
    def test_start_tool_chain(self):
        """测试开始工具调用链"""
        root_tool_id = "test_tool_1"
        chain_id = self.tracker.start_tool_chain(root_tool_id)
        
        # 验证返回的chain_id不为空
        self.assertIsNotNone(chain_id)
        self.assertTrue(chain_id.startswith("chain-"))
        
        # 验证当前链已创建
        self.assertIsNotNone(self.tracker.chain_context.current_chain)
        self.assertEqual(self.tracker.chain_context.current_chain.root_tool_id, root_tool_id)
        
    def test_end_tool_chain(self):
        """测试结束工具调用链"""
        root_tool_id = "test_tool_1"
        chain_id = self.tracker.start_tool_chain(root_tool_id)
        
        # 结束调用链
        ended_chain_id = self.tracker.end_tool_chain()
        
        # 验证返回的chain_id正确
        self.assertEqual(ended_chain_id, chain_id)
        
        # 验证当前链已清空
        self.assertIsNone(self.tracker.chain_context.current_chain)
        
        # 验证链已存储
        self.assertIn(chain_id, self.tracker.stored_chains)
        
    def test_start_tool_call(self):
        """测试开始工具调用"""
        root_tool_id = "test_tool_1"
        chain_id = self.tracker.start_tool_chain(root_tool_id)
        
        tool_id = "test_tool_2"
        parameters = {"param1": "value1", "param2": "value2"}
        call_id = self.tracker.start_tool_call(tool_id, parameters)
        
        # 验证返回的call_id不为空
        self.assertIsNotNone(call_id)
        self.assertTrue(call_id.startswith(f"{chain_id}-"))
        
        # 验证调用节点已创建
        self.assertIn(call_id, self.tracker.chain_context.current_chain.calls)
        call_node = self.tracker.chain_context.current_chain.calls[call_id]
        self.assertEqual(call_node.tool_id, tool_id)
        self.assertEqual(call_node.parameters, parameters)
        
    def test_end_tool_call(self):
        """测试结束工具调用"""
        root_tool_id = "test_tool_1"
        self.tracker.start_tool_chain(root_tool_id)
        
        tool_id = "test_tool_2"
        parameters = {"param1": "value1"}
        call_id = self.tracker.start_tool_call(tool_id, parameters)
        
        result = {"output": "test_result"}
        ended_call_id = self.tracker.end_tool_call(result, success=True)
        
        # 验证返回的call_id正确
        self.assertEqual(ended_call_id, call_id)
        
        # 验证调用节点已更新
        call_node = self.tracker.chain_context.current_chain.calls[call_id]
        self.assertEqual(call_node.result, result)
        self.assertTrue(call_node.success)
        self.assertIsNotNone(call_node.completed_at)
        self.assertGreaterEqual(call_node.duration, 0)
        
    def test_tool_call_chain_structure(self):
        """测试工具调用链结构"""
        root_tool_id = "root_tool"
        chain_id = self.tracker.start_tool_chain(root_tool_id)
        
        # 创建根调用
        root_parameters = {"input": "root_input"}
        root_call_id = self.tracker.start_tool_call(root_tool_id, root_parameters)
        
        # 创建子调用1
        child1_tool_id = "child_tool_1"
        child1_parameters = {"param": "value1"}
        child1_call_id = self.tracker.start_tool_call(child1_tool_id, child1_parameters)
        self.tracker.end_tool_call({"result": "child1_result"}, success=True)
        
        # 创建子调用2
        child2_tool_id = "child_tool_2"
        child2_parameters = {"param": "value2"}
        child2_call_id = self.tracker.start_tool_call(child2_tool_id, child2_parameters)
        self.tracker.end_tool_call({"result": "child2_result"}, success=True)
        
        # 结束根调用
        self.tracker.end_tool_call({"result": "root_result"}, success=True)
        
        # 结束调用链
        self.tracker.end_tool_chain()
        
        # 验证调用链结构
        chain = self.tracker.stored_chains[chain_id]
        self.assertEqual(chain.root_tool_id, root_tool_id)
        self.assertEqual(chain.root_call_id, root_call_id)
        self.assertEqual(len(chain.calls), 3)
        
        # 验证根调用
        root_call = chain.calls[root_call_id]
        self.assertEqual(root_call.tool_id, root_tool_id)
        self.assertEqual(root_call.parameters, root_parameters)
        self.assertEqual(len(root_call.child_calls), 2)
        self.assertIn(child1_call_id, root_call.child_calls)
        self.assertIn(child2_call_id, root_call.child_calls)
        self.assertIsNone(root_call.parent_id)
        
        # 验证子调用1
        child1_call = chain.calls[child1_call_id]
        self.assertEqual(child1_call.tool_id, child1_tool_id)
        self.assertEqual(child1_call.parameters, child1_parameters)
        self.assertEqual(child1_call.parent_id, root_call_id)
        self.assertEqual(len(child1_call.child_calls), 0)
        
        # 验证子调用2
        child2_call = chain.calls[child2_call_id]
        self.assertEqual(child2_call.tool_id, child2_tool_id)
        self.assertEqual(child2_call.parameters, child2_parameters)
        self.assertEqual(child2_call.parent_id, root_call_id)
        self.assertEqual(len(child2_call.child_calls), 0)
        
    def test_get_call_chain_by_id(self):
        """测试根据ID获取调用链"""
        root_tool_id = "test_tool"
        chain_id = self.tracker.start_tool_chain(root_tool_id)
        self.tracker.end_tool_chain()
        
        # 获取调用链
        chain = self.tracker.get_call_chain_by_id(chain_id)
        self.assertIsNotNone(chain)
        self.assertEqual(chain.chain_id, chain_id)
        self.assertEqual(chain.root_tool_id, root_tool_id)
        
        # 获取不存在的调用链
        non_existent_chain = self.tracker.get_call_chain_by_id("non_existent")
        self.assertIsNone(non_existent_chain)
        
    def test_get_chains_by_tool_id(self):
        """测试根据工具ID获取相关调用链"""
        # 创建使用特定工具的调用链
        tool_id = "specific_tool"
        chain_id = self.tracker.start_tool_chain(tool_id)
        self.tracker.end_tool_chain()
        
        # 获取相关调用链
        chains = self.tracker.get_chains_by_tool_id(tool_id)
        self.assertEqual(len(chains), 1)
        self.assertEqual(chains[0].chain_id, chain_id)
        
        # 获取不存在工具的调用链
        non_existent_chains = self.tracker.get_chains_by_tool_id("non_existent_tool")
        self.assertEqual(len(non_existent_chains), 0)
        
    def test_error_handling_in_chain(self):
        """测试调用链中的错误处理"""
        root_tool_id = "root_tool"
        chain_id = self.tracker.start_tool_chain(root_tool_id)
        
        # 创建调用并模拟错误
        tool_id = "error_tool"
        call_id = self.tracker.start_tool_call(tool_id, {})
        error_message = "Test error occurred"
        self.tracker.end_tool_call(None, success=False, error_message=error_message)
        
        # 结束调用链
        self.tracker.end_tool_chain()
        
        # 验证错误信息被正确记录
        chain = self.tracker.stored_chains[chain_id]
        self.assertFalse(chain.success)
        self.assertEqual(chain.error_message, error_message)


class TestToolCallChainContext(unittest.TestCase):
    """工具调用链上下文管理器测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.context = ToolCallChainContext()
        
    def test_start_chain(self):
        """测试开始调用链"""
        chain_id = "test_chain"
        root_tool_id = "root_tool"
        chain = self.context.start_chain(chain_id, root_tool_id)
        
        self.assertEqual(chain.chain_id, chain_id)
        self.assertEqual(chain.root_tool_id, root_tool_id)
        self.assertIsNotNone(chain.created_at)
        
    def test_end_chain_without_active_chain(self):
        """测试在没有活动调用链时结束调用链"""
        chain = self.context.end_chain()
        self.assertIsNone(chain)
        
    def test_start_call_without_active_chain(self):
        """测试在没有活动调用链时开始调用"""
        with self.assertRaises(RuntimeError):
            self.context.start_call("test_tool", {})
            
    def test_end_call_without_active_call(self):
        """测试在没有活动调用时结束调用"""
        # 先开始一个调用链
        self.context.start_chain("test_chain", "root_tool")
        
        # 尝试结束不存在的调用
        with self.assertRaises(RuntimeError):
            self.context.end_call()


if __name__ == "__main__":
    unittest.main()