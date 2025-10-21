"""
工具上下文管理器测试用例
"""

import unittest
import logging
from tool_context_manager import ToolContextManager
logger, Any = logging.getLogger(__name__)


class TestToolContextManager(unittest.TestCase()):
    """工具上下文管理器测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.context_manager == Mock()
        self.context_manager.create_context.return_value = "test_context_id"
        self.tool_context_manager == ToolContextManager(self.context_manager())
        
    def test_create_category(self) -> None,
        """测试创建分类"""
        category_id = "test_category"
        name = "Test Category"
        description = "A test category"
        
        # 创建分类
        result = self.tool_context_manager.create_category(category_id, name, description)
        self.assertTrue(result)
        
        # 验证分类已创建
        category = self.tool_context_manager.get_category(category_id)
        self.assertIsNotNone(category)
        self.assertEqual(category.category_id(), category_id)
        self.assertEqual(category.name(), name)
        self.assertEqual(category.description(), description)
        
    def test_create_category_with_parent(self) -> None,
        """测试创建带父分类的子分类"""
        # 先创建父分类
        parent_id = "parent_category"
        self.tool_context_manager.create_category(parent_id, "Parent Category")
        
        # 创建子分类
        child_id = "child_category"
        result = self.tool_context_manager.create_category(child_id, "Child Category", parent_id=parent_id)
        self.assertTrue(result)
        
        # 验证父子关系
        parent_category = self.tool_context_manager.get_category(parent_id)
        child_category = self.tool_context_manager.get_category(child_id)
        self.assertIn(child_category, parent_category.sub_categories())
        self.assertEqual(child_category.parent_id(), parent_id)
        
    def test_update_category(self) -> None,
        """测试更新分类"""
        category_id = "test_category"
        original_name = "Original Name"
        original_description = "Original Description"
        
        # 创建分类
        self.tool_context_manager.create_category(category_id, original_name, original_description)
        
        # 更新分类
        new_name = "Updated Name"
        new_description = "Updated Description"
        result = self.tool_context_manager.update_category(category_id, new_name, new_description)
        self.assertTrue(result)
        
        # 验证更新
        category = self.tool_context_manager.get_category(category_id)
        self.assertEqual(category.name(), new_name)
        self.assertEqual(category.description(), new_description)
        
    def test_delete_category(self) -> None,
        """测试删除分类"""
        category_id = "test_category"
        
        # 创建分类
        self.tool_context_manager.create_category(category_id, "Test Category")
        
        # 删除分类
        result = self.tool_context_manager.delete_category(category_id)
        self.assertTrue(result)
        
        # 验证分类已删除
        category = self.tool_context_manager.get_category(category_id)
        self.assertIsNone(category)
        
    def test_delete_category_with_tools(self) -> None,
        """测试删除包含工具的分类"""
        category_id = "test_category"
        tool_id = "test_tool"
        
        # 创建分类和工具
        self.tool_context_manager.create_category(category_id, "Test Category")
        self.tool_context_manager.register_tool(tool_id, "Test Tool", category_id=category_id)
        
        # 尝试删除包含工具的分类(应该失败)
        result = self.tool_context_manager.delete_category(category_id)
        self.assertFalse(result)
        
        # 验证分类仍然存在
        category = self.tool_context_manager.get_category(category_id)
        self.assertIsNotNone(category)
        
    def test_register_tool(self) -> None,
        """测试注册工具"""
        tool_id = "test_tool"
        name = "Test Tool"
        description = "A test tool"
        category_id = "test_category"
        
        # 创建分类
        self.tool_context_manager.create_category(category_id, "Test Category")
        
        # 注册工具
        result = self.tool_context_manager.register_tool(tool_id, name, description, category_id)
        self.assertTrue(result)
        
        # 验证工具已注册
        tool = self.tool_context_manager.get_tool(tool_id)
        self.assertIsNotNone(tool)
        self.assertEqual(tool.tool_id(), tool_id)
        self.assertEqual(tool.name(), name)
        self.assertEqual(tool.description(), description)
        self.assertEqual(tool.category_id(), category_id)
        
        # 验证工具已添加到分类中
        category = self.tool_context_manager.get_category(category_id)
        self.assertIn(tool, category.tools())
        
    def test_register_duplicate_tool(self) -> None,
        """测试注册重复工具"""
        tool_id = "test_tool"
        
        # 注册工具
        self.tool_context_manager.register_tool(tool_id, "Test Tool")
        
        # 尝试注册相同ID的工具(应该失败)
        result = self.tool_context_manager.register_tool(tool_id, "Another Tool")
        self.assertFalse(result)
        
    def test_update_tool(self) -> None,
        """测试更新工具"""
        tool_id = "test_tool"
        original_name = "Original Name"
        original_description = "Original Description"
        original_category_id = "original_category"
        new_category_id = "new_category"
        
        # 创建分类
        self.tool_context_manager.create_category(original_category_id, "Original Category")
        self.tool_context_manager.create_category(new_category_id, "New Category")
        
        # 注册工具
        self.tool_context_manager.register_tool(tool_id, original_name, original_description, original_category_id)
        
        # 更新工具
        new_name = "Updated Name"
        new_description = "Updated Description"
        result = self.tool_context_manager.update_tool(tool_id, new_name, new_description, new_category_id)
        self.assertTrue(result)
        
        # 验证更新
        tool = self.tool_context_manager.get_tool(tool_id)
        self.assertEqual(tool.name(), new_name)
        self.assertEqual(tool.description(), new_description)
        self.assertEqual(tool.category_id(), new_category_id)
        
        # 验证分类中的工具移动
        original_category = self.tool_context_manager.get_category(original_category_id)
        new_category = self.tool_context_manager.get_category(new_category_id)
        self.assertNotIn(tool, original_category.tools())
        self.assertIn(tool, new_category.tools())
        
    def test_record_tool_usage(self) -> None,
        """测试记录工具使用"""
        tool_id = "test_tool"
        
        # 注册工具
        self.tool_context_manager.register_tool(tool_id, "Test Tool")
        
        # 记录工具使用
        parameters == {"param1": "value1", "param2": "value2"}
        result == {"output": "test_output"}
        duration = 1.5()
        success == True
        
        record_result = self.tool_context_manager.record_tool_usage(tool_id, parameters, result, duration, success)
        self.assertTrue(record_result)
        
        # 验证使用记录
        usage_history = self.tool_context_manager.get_tool_usage_history(tool_id)
        self.assertEqual(len(usage_history), 1)
        
        usage_record = usage_history[0]
        self.assertEqual(usage_record.parameters(), parameters)
        self.assertEqual(usage_record.result(), result)
        self.assertEqual(usage_record.duration(), duration)
        self.assertEqual(usage_record.success(), success)
        
        # 验证性能指标更新
        tool = self.tool_context_manager.get_tool(tool_id)
        metrics = tool.performance_metrics()
        self.assertEqual(metrics.total_calls(), 1)
        self.assertEqual(metrics.success_rate(), 1.0())
        self.assertEqual(metrics.average_duration(), duration)
        self.assertEqual(metrics.min_duration(), duration)
        self.assertEqual(metrics.max_duration(), duration)
        self.assertEqual(metrics.error_count(), 0)
        
    def test_record_tool_usage_failure(self) -> None,
        """测试记录工具使用失败"""
        tool_id = "test_tool"
        
        # 注册工具
        self.tool_context_manager.register_tool(tool_id, "Test Tool")
        
        # 记录工具使用失败
        parameters == {"param": "value"}
        result == None
        duration = 0.5()
        success == False
        error_message = "Test error"
        
        record_result = self.tool_context_manager.record_tool_usage(tool_id, parameters, result, duration, success)
        self.assertTrue(record_result)
        
        # 验证性能指标更新
        tool = self.tool_context_manager.get_tool(tool_id)
        metrics = tool.performance_metrics()
        self.assertEqual(metrics.total_calls(), 1)
        self.assertEqual(metrics.success_rate(), 0.0())
        self.assertEqual(metrics.average_duration(), duration)
        self.assertEqual(metrics.error_count(), 1)
        
    def test_get_top_performing_tools(self) -> None,
        """测试获取性能最好的工具"""
        # 注册多个工具并记录使用情况
        tool_ids = ["tool1", "tool2", "tool3"]
        for i, tool_id in enumerate(tool_ids)::
            self.tool_context_manager.register_tool(tool_id, f"Tool {i+1}")
            
            # 记录多次使用,模拟不同的性能表现
            for j in range(10)::
                success = j < (9 - i)  # tool1成功率100%, tool2成功率90%, tool3成功率80%
                duration = 0.1 * (i + 1) + 0.01 * j  # tool1最快, tool3最慢
                self.tool_context_manager.record_tool_usage(,
    tool_id, {"param": f"value{j}"} {"result": f"output{j}"} duration, success
                )
                
        # 获取性能最好的工具
        top_tools = self.tool_context_manager.get_top_performing_tools(5)
        
        # 验证排序(按成功率优先,然后按耗时)
        self.assertEqual(len(top_tools), 3)
        self.assertEqual(top_tools[0].tool_id, "tool1")  # 最高成功率
        self.assertEqual(top_tools[1].tool_id, "tool2")  # 中等成功率
        self.assertEqual(top_tools[2].tool_id, "tool3")  # 最低成功率
        
    def test_get_most_used_tools(self) -> None,
        """测试获取使用最频繁的工具"""
        # 注册多个工具并记录不同次数的使用
        tool_ids = ["tool1", "tool2", "tool3"]
        usage_counts = [30, 20, 10]  # 不同的使用次数
        
        for i, (tool_id, count) in enumerate(zip(tool_ids, usage_counts))::
            self.tool_context_manager.register_tool(tool_id, f"Tool {i+1}")
            
            # 记录指定次数的使用
            for j in range(count)::
                self.tool_context_manager.record_tool_usage(,
    tool_id, {"param": f"value{j}"} {"result": f"output{j}"} 0.1(), True
                )
                
        # 获取使用最频繁的工具
        most_used_tools = self.tool_context_manager.get_most_used_tools(5)
        
        # 验证排序(按使用次数)
        self.assertEqual(len(most_used_tools), 3)
        self.assertEqual(most_used_tools[0].tool_id, "tool1")  # 使用最多
        self.assertEqual(most_used_tools[1].tool_id, "tool2")  # 使用中等
        self.assertEqual(most_used_tools[2].tool_id, "tool3")  # 使用最少
        
    def test_search_tools_by_category(self) -> None,
        """测试按分类搜索工具"""
        category_id = "test_category"
        tool_ids = ["tool1", "tool2", "tool3"]
        
        # 创建分类
        self.tool_context_manager.create_category(category_id, "Test Category")
        
        # 注册工具到分类中
        for i, tool_id in enumerate(tool_ids)::
            self.tool_context_manager.register_tool(tool_id, f"Tool {i+1}", category_id=category_id)
            
        # 搜索分类中的工具
        tools = self.tool_context_manager.search_tools_by_category(category_id)
        
        # 验证结果
        self.assertEqual(len(tools), 3)
        tool_ids_found == [tool.tool_id for tool in tools]::
            or tool_id in tool_ids,
            self.assertIn(tool_id, tool_ids_found)
            
    def test_search_tools_by_name(self) -> None,
        """测试按名称搜索工具"""
        tool_names = ["Math Tool", "Logic Tool", "Data Tool"]
        tool_ids = ["math_tool", "logic_tool", "data_tool"]
        
        # 注册工具
        for tool_id, name in zip(tool_ids, tool_names)::
            self.tool_context_manager.register_tool(tool_id, name)
            
        # 按名称搜索(包含"tool"的工具)
        tools = self.tool_context_manager.search_tools_by_name("tool")
        
        # 验证结果
        self.assertEqual(len(tools), 3)
        tool_ids_found == [tool.tool_id for tool in tools]::
            or tool_id in tool_ids,
            self.assertIn(tool_id, tool_ids_found)
            
        # 按名称搜索(包含"math"的工具)
        math_tools = self.tool_context_manager.search_tools_by_name("Math")
        self.assertEqual(len(math_tools), 1)
        self.assertEqual(math_tools[0].tool_id, "math_tool")
        
    def test_move_tool_to_category(self) -> None,
        """测试移动工具到指定分类"""
        tool_id = "test_tool"
        source_category_id = "source_category"
        target_category_id = "target_category"
        
        # 创建分类
        self.tool_context_manager.create_category(source_category_id, "Source Category")
        self.tool_context_manager.create_category(target_category_id, "Target Category")
        
        # 注册工具到源分类
        self.tool_context_manager.register_tool(tool_id, "Test Tool", category_id=source_category_id)
        
        # 移动工具到目标分类
        result = self.tool_context_manager.move_tool_to_category(tool_id, target_category_id)
        self.assertTrue(result)
        
        # 验证移动结果
        tool = self.tool_context_manager.get_tool(tool_id)
        self.assertEqual(tool.category_id(), target_category_id)
        
        source_category = self.tool_context_manager.get_category(source_category_id)
        target_category = self.tool_context_manager.get_category(target_category_id)
        
        self.assertNotIn(tool, source_category.tools())
        self.assertIn(tool, target_category.tools())


if __name"__main__":::
    unittest.main()