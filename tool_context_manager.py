"""
工具上下文管理器实现
基于TOOL_CONTEXT_DATA_MODEL_DESIGN.md设计文档
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from tool_call_chain_tracker import ToolCallChainTracker

logger: Any = logging.getLogger(__name__)


class ToolCategory:
    """工具分类"""
    
    def __init__(self, category_id: str, name: str, description: str = "", parent_id: Optional[str] = None) -> None:
        self.category_id: str = category_id  # 分类唯一标识
        self.name: str = name  # 分类名称
        self.description: str = description  # 分类描述
        self.parent_id: Optional[str] = parent_id  # 父分类ID
        self.sub_categories: List['ToolCategory'] = []  # 子分类列表
        self.tools: List['Tool'] = []  # 包含的工具列表
        self.created_at: datetime = datetime.now()  # 创建时间
        self.updated_at: datetime = datetime.now()  # 更新时间
        
    def add_sub_category(self, sub_category: 'ToolCategory'):
        """添加子分类"""
        _ = self.sub_categories.append(sub_category)
        
    def add_tool(self, tool: 'Tool'):
        """添加工具"""
        _ = self.tools.append(tool)


class ToolPerformanceMetrics:
    """工具性能指标"""
    
    def __init__(self) -> None:
        self.total_calls: int = 0  # 总调用次数
        self.success_rate: float = 0.0  # 成功率
        self.average_duration: float = 0.0  # 平均执行时间
        self.min_duration: float = float('inf')  # 最小执行时间
        self.max_duration: float = 0.0  # 最大执行时间
        self.last_used: Optional[datetime] = None  # 最后使用时间
        self.error_count: int = 0  # 错误次数
        self.updated_at: datetime = datetime.now()  # 更新时间


class ToolUsageRecord:
    """工具使用记录"""
    
    def __init__(self, parameters: Dict[str, Any], result: Any, duration: float, success: bool) -> None:
        self.timestamp: datetime = datetime.now()  # 使用时间戳
        self.parameters: Dict[str, Any] = parameters  # 调用参数
        self.result: Any = result  # 执行结果
        self.duration: float = duration  # 执行耗时(秒)
        self.success: bool = success  # 执行是否成功
        self.context_id: str = ""  # 关联的上下文ID
        self.session_id: str = ""  # 会话ID
        self.user_id: str = ""  # 用户ID


class Tool:
    """工具定义"""
    
    def __init__(self, tool_id: str, name: str, description: str = "", category_id: str = "") -> None:
        self.tool_id: str = tool_id  # 工具唯一标识
        self.name: str = name  # 工具名称
        self.description: str = description  # 工具描述
        self.category_id: str = category_id  # 所属分类ID
        self.usage_history: List[ToolUsageRecord] = []  # 使用历史记录
        self.performance_metrics: ToolPerformanceMetrics = ToolPerformanceMetrics()  # 性能指标
        self.created_at: datetime = datetime.now()  # 创建时间
        self.updated_at: datetime = datetime.now()  # 更新时间


class ToolContextManager:
    """工具上下文管理器"""
    
    def __init__(self, context_manager: 'ContextManager') -> None:
        self.context_manager = context_manager
        self.call_chain_tracker = ToolCallChainTracker(context_manager)
        self.categories: Dict[str, ToolCategory] = {}
        self.tools: Dict[str, Tool] = {}
        
    def create_category(self, category_id: str, name: str, description: str = "", parent_id: Optional[str] = None) -> bool:
        """创建分类"""
        try:
            category = ToolCategory(category_id, name, description, parent_id)
            self.categories[category_id] = category
            
            # 如果有父分类，添加到父分类的子分类列表中
            if parent_id and parent_id in self.categories:
                _ = self.categories[parent_id].add_sub_category(category)
                
            _ = logger.info(f"Created tool category {category_id}: {name}")
            return True
        except Exception as e:
            _ = logger.error(f"Failed to create tool category {category_id}: {e}")
            return False
            
    def get_category(self, category_id: str) -> Optional[ToolCategory]:
        """获取分类"""
        return self.categories.get(category_id)
        
    def update_category(self, category_id: str, name: Optional[str] = None, description: Optional[str] = None) -> bool:
        """更新分类"""
        if category_id not in self.categories:
            return False
            
        category = self.categories[category_id]
        if name is not None:
            category.name = name
        if description is not None:
            category.description = description
        category.updated_at = datetime.now()
        
        _ = logger.info(f"Updated tool category {category_id}")
        return True
        
    def delete_category(self, category_id: str) -> bool:
        """删除分类"""
        if category_id not in self.categories:
            return False
            
        # 检查是否有子分类或工具，如果有则不能删除
        category = self.categories[category_id]
        if category.sub_categories or category.tools:
            _ = logger.warning(f"Cannot delete category {category_id} because it has sub-categories or tools")
            return False
            
        # 从父分类中移除
        if category.parent_id and category.parent_id in self.categories:
            parent_category = self.categories[category.parent_id]
            if category in parent_category.sub_categories:
                _ = parent_category.sub_categories.remove(category)
                
        # 从分类字典中删除
        del self.categories[category_id]
        _ = logger.info(f"Deleted tool category {category_id}")
        return True
        
    def get_category_tools(self, category_id: str) -> List[Tool]:
        """获取分类下的工具"""
        if category_id not in self.categories:
            return []
        return self.categories[category_id].tools
        
    def move_tool_to_category(self, tool_id: str, target_category_id: str) -> bool:
        """移动工具到指定分类"""
        if tool_id not in self.tools:
            _ = logger.warning(f"Tool {tool_id} not found")
            return False
            
        if target_category_id not in self.categories:
            _ = logger.warning(f"Category {target_category_id} not found")
            return False
            
        tool = self.tools[tool_id]
        old_category_id = tool.category_id
        
        # 从原分类中移除
        if old_category_id and old_category_id in self.categories:
            old_category = self.categories[old_category_id]
            if tool in old_category.tools:
                _ = old_category.tools.remove(tool)
                
        # 添加到新分类
        target_category = self.categories[target_category_id]
        _ = target_category.tools.append(tool)
        tool.category_id = target_category_id
        tool.updated_at = datetime.now()
        
        _ = logger.info(f"Moved tool {tool_id} from category {old_category_id} to {target_category_id}")
        return True
        
    def register_tool(self, tool_id: str, name: str, description: str = "", category_id: str = "") -> bool:
        """注册工具"""
        try:
            # 检查工具是否已存在
            if tool_id in self.tools:
                _ = logger.warning(f"Tool {tool_id} already exists")
                return False
                
            # 创建工具对象
            tool = Tool(tool_id, name, description, category_id)
            self.tools[tool_id] = tool
            
            # 如果指定了分类，添加到分类中
            if category_id and category_id in self.categories:
                category = self.categories[category_id]
                _ = category.tools.append(tool)
                
            _ = logger.info(f"Registered tool {tool_id}: {name}")
            return True
        except Exception as e:
            _ = logger.error(f"Failed to register tool {tool_id}: {e}")
            return False
            
    def get_tool(self, tool_id: str) -> Optional[Tool]:
        """获取工具"""
        return self.tools.get(tool_id)
        
    def update_tool(self, tool_id: str, name: Optional[str] = None, description: Optional[str] = None, category_id: Optional[str] = None) -> bool:
        """更新工具"""
        if tool_id not in self.tools:
            return False
            
        tool = self.tools[tool_id]
        if name is not None:
            tool.name = name
        if description is not None:
            tool.description = description
        if category_id is not None:
            # 从原分类中移除
            if tool.category_id and tool.category_id in self.categories:
                old_category = self.categories[tool.category_id]
                if tool in old_category.tools:
                    _ = old_category.tools.remove(tool)
                    
            # 添加到新分类
            if category_id in self.categories:
                new_category = self.categories[category_id]
                _ = new_category.tools.append(tool)
                
            tool.category_id = category_id
            
        tool.updated_at = datetime.now()
        _ = logger.info(f"Updated tool {tool_id}")
        return True
        
    def record_tool_usage(self, tool_id: str, parameters: Dict[str, Any], result: Any, duration: float, success: bool) -> bool:
        """记录工具使用"""
        if tool_id not in self.tools:
            _ = logger.warning(f"Tool {tool_id} not found")
            return False
            
        try:
            tool = self.tools[tool_id]
            
            # 创建使用记录
            usage_record: ToolUsageRecord = ToolUsageRecord(parameters, result, duration, success)
            _ = tool.usage_history.append(usage_record)
            
            # 更新性能指标
            metrics = tool.performance_metrics
            metrics.total_calls += 1
            metrics.last_used = datetime.now()
            
            # 更新耗时统计（无论成功与否都应该更新耗时）
            if duration < metrics.min_duration:
                metrics.min_duration = duration
            if duration > metrics.max_duration:
                metrics.max_duration = duration
                
            # 更新平均耗时
            if metrics.total_calls > 1:
                metrics.average_duration = (metrics.average_duration * (metrics.total_calls - 1) + duration) / metrics.total_calls
            else:
                metrics.average_duration = duration
                
            if success:
                # 更新成功率
                if metrics.total_calls > 1:
                    metrics.success_rate = (metrics.success_rate * (metrics.total_calls - 1) + 1) / metrics.total_calls
                else:
                    metrics.success_rate = 1.0
            else:
                metrics.error_count += 1
                # 更新成功率
                if metrics.total_calls > 1:
                    metrics.success_rate = (metrics.success_rate * (metrics.total_calls - 1)) / metrics.total_calls
                else:
                    metrics.success_rate = 0.0
                    
            metrics.updated_at = datetime.now()
            
            logger.debug(f"Recorded usage for tool {tool_id}, total calls: {metrics.total_calls}")
            return True
        except Exception as e:
            logger.error(f"Failed to record usage for tool {tool_id}: {e}")
            return False
            
    def get_tool_usage_history(self, tool_id: str, limit: int = 100) -> List[ToolUsageRecord]:
        """获取工具使用历史"""
        if tool_id not in self.tools:
            return []
            
        tool = self.tools[tool_id]
        # 返回最近的使用记录
        return tool.usage_history[-limit:] if len(tool.usage_history) > limit else tool.usage_history
        
    def get_top_performing_tools(self, limit: int = 10) -> List[Tool]:
        """获取性能最好的工具列表"""
        # 按成功率和平均耗时排序
        sorted_tools = sorted(
            _ = self.tools.values(),
            key=lambda tool: (tool.performance_metrics.success_rate, -tool.performance_metrics.average_duration),
            reverse=True
        )
        return sorted_tools[:limit]
        
    def get_most_used_tools(self, limit: int = 10) -> List[Tool]:
        """获取使用最频繁的工具列表"""
        # 按总调用次数排序
        sorted_tools = sorted(
            _ = self.tools.values(),
            key=lambda tool: tool.performance_metrics.total_calls,
            reverse=True
        )
        return sorted_tools[:limit]
        
    def search_tools_by_category(self, category_id: str) -> List[Tool]:
        """根据分类ID搜索工具"""
        return self.get_category_tools(category_id)
        
    def search_tools_by_name(self, name_pattern: str) -> List[Tool]:
        """根据名称模式搜索工具"""
        result = []
        for tool in self.tools.values():
            if name_pattern.lower() in tool.name.lower():
                _ = result.append(tool)
        return result
        
    def start_tool_chain(self, root_tool_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """开始工具调用链追踪"""
        return self.call_chain_tracker.start_tool_chain(root_tool_id, metadata)
        
    def end_tool_chain(self) -> Optional[str]:
        """结束工具调用链追踪"""
        return self.call_chain_tracker.end_tool_chain()
        
    def start_tool_call(self, tool_id: str, parameters: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        """开始工具调用追踪"""
        return self.call_chain_tracker.start_tool_call(tool_id, parameters, metadata)
        
    def end_tool_call(self, result: Any = None, success: bool = True, error_message: Optional[str] = None) -> str:
        """结束工具调用追踪"""
        return self.call_chain_tracker.end_tool_call(result, success, error_message)