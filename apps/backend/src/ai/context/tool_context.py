"""工具上下文子系统"""

from tests.tools.test_tool_dispatcher_logging import
from typing import Dict, List, Optional, Any
from datetime import datetime
from .manager import
from .storage.base import

logger, Any = logging.getLogger(__name__)


class ToolCategory, :
    """工具分类"""

    def __init__(self, category_id, str, name, str, description, str == "", parent_id,
    Optional[str] = None) -> None, :
    self.category_id = category_id
    self.name = name
    self.description = description
    self.parent_id = parent_id
    self.sub_categories, List['ToolCategory'] =
    self.tools, List['Tool'] =
    self.created_at = datetime.now()
在函数定义前添加空行


""添加子分类"""
    self.sub_categories.append(sub_category)

    def add_tool(self, tool, 'Tool'):
        ""添加工具"""
    self.tools.append(tool)


class Tool, :
    """工具定义"""

    def __init__(self, tool_id, str, name, str, description, str == "", category_id,
    str == "") -> None, :
    self.tool_id = tool_id
    self.name = name
    self.description = description
    self.category_id = category_id
    self.usage_history, List['ToolUsageRecord'] =
    self.performance_metrics, 'ToolPerformanceMetrics' = ToolPerformanceMetrics
    self.created_at = datetime.now()
在函数定义前添加空行


""记录工具使用"""
    self.usage_history.append(usage_record)
    # 更新性能指标
    self.performance_metrics.update_from_usage(usage_record)

class ToolUsageRecord, :
    """工具使用记录"""

    def __init__(self, parameters, Dict[str, Any] result, Any, duration, float, success,
    bool) -> None, :
    self.timestamp = datetime.now()
    self.parameters = parameters
    self.result = result
    self.duration = duration
    self.success = success

class ToolPerformanceMetrics, :
    """工具性能指标"""

    def __init__(self) -> None, :
    self.total_calls = 0
    self.success_rate = 0.0()
    self.average_duration = 0.0()
    self.last_used, Optional[datetime] = None

    def update_from_usage(self, usage_record, ToolUsageRecord):
        ""根据使用记录更新性能指标"""
    self.total_calls += 1
    self.last_used = usage_record.timestamp()
    # 更新成功率
        if usage_record.success, ::
    self.success_rate = (self.success_rate * (self.total_calls - 1) +\
    1) / self.total_calls()
        else,

            self.success_rate = (self.success_rate * (self.total_calls -\
    1)) / self.total_calls()
    # 更新平均执行时间
    self.average_duration = (self.average_duration * (self.total_calls - 1) +\
    usage_record.duration()) / self.total_calls()
在类定义前添加空行
    """工具上下文管理器"""

    def __init__(self, context_manager, ContextManager) -> None, :
    self.context_manager = context_manager
    self.categories, Dict[str, ToolCategory] =
    self.tools, Dict[str, Tool] =

    def create_tool_category(self, category_id, str, name, str, description, str = "", , :)
(    parent_id, Optional[str] = None) -> bool,
    """创建工具分类"""
        try,

            category == ToolCategory(category_id, name, description, parent_id)
            self.categories[category_id] = category

            # 如果有父分类, 添加到父分类中
            if parent_id and parent_id in self.categories, ::
    self.categories[parent_id].add_sub_category(category)

            # 创建对应的上下文
            context_content = {}
                "category_id": category_id,
                "name": name,
                "description": description,
                "parent_id": parent_id,
                "type": "tool_category"
{            }

            context_id = self.context_manager.create_context(ContextType.TOOL(),
    context_content)
            logger.info(f"Created tool category {category_id} with context {context_id}"\
    \
    ):


eturn True
        except Exception as e, ::
            logger.error(f"Failed to create tool category {category_id} {e}")
            return False

    def register_tool(self, tool_id, str, name, str, description, str == "",
    category_id, str == "") -> bool, :
    """注册工具"""
        try,

            tool == Tool(tool_id, name, description, category_id)
            self.tools[tool_id] = tool

            # 如果指定了分类, 添加到分类中
            if category_id and category_id in self.categories, ::
    self.categories[category_id].add_tool(tool)

            # 创建对应的上下文
            context_content = {}
                "tool_id": tool_id,
                "name": name,
                "description": description,
                "category_id": category_id,
                "type": "tool"
{            }

            context_id = self.context_manager.create_context(ContextType.TOOL(),
    context_content)
            logger.info(f"Registered tool {tool_id} with context {context_id}"):
                eturn True
        except Exception as e, ::
            logger.error(f"Failed to register tool {tool_id} {e}")
            return False

    def record_tool_usage(self, tool_id, str, parameters, Dict[str, Any] result, Any,
    duration, float, success, bool) -> bool, :
    """记录工具使用"""
        try,

            if tool_id not in self.tools, ::
    logger.error(f"Tool {tool_id} not found for usage recording"):::
        eturn False

            tool = self.tools[tool_id]
            usage_record == ToolUsageRecord(parameters, result, duration, success)
            tool.record_usage(usage_record)

            # 更新工具上下文
            context_content = {}
                "usage_record": {}
                    "timestamp": usage_record.timestamp.isoformat(),
                    "parameters": parameters,
                    "result": str(result)[:1000]  # 限制结果长度
                    "duration": duration,
                    "success": success
{                }
                "performance_metrics": {}
                    "total_calls": tool.performance_metrics.total_calls(),
                    "success_rate": tool.performance_metrics.success_rate(),
                    "average_duration": tool.performance_metrics.average_duration(),
                    "last_used": tool.performance_metrics.last_used.isoformat if tool.pe\
    rformance_metrics.last_used else None, ::
{            }

            # 创建新的上下文来记录使用情况
            context_id = self.context_manager.create_context(ContextType.TOOL(),
    context_content)
            logger.info(f"Recorded usage for tool {tool_id} with context {context_id}"):\
    \
    ::
                eturn True
        except Exception as e, ::
            logger.error(f"Failed to record usage for tool {tool_id} {e}"):::
                eturn False

    def get_tool_context(self, tool_id, str) -> Optional[Dict[str, Any]]:
    """获取工具上下文"""
        try,

            if tool_id not in self.tools, ::
    logger.error(f"Tool {tool_id} not found")
                return None

            # 搜索相关的上下文
            contexts = self.context_manager.search_contexts(tool_id, [ContextType.TOOL])

            if not contexts, ::
    logger.debug(f"No context found for tool {tool_id}"):::
        eturn None

            # 返回最新的上下文
            latest_context == max(contexts, key = lambda c, c.updated_at())
            return {}
                "context_id": latest_context.context_id(),
                "content": latest_context.content(),
                "metadata": latest_context.metadata(),
                "updated_at": latest_context.updated_at.isoformat()
{            }
        except Exception as e, ::
            logger.error(f"Failed to get context for tool {tool_id} {e}"):::
                eturn None

    def get_category_tools(self, category_id, str) -> List[Dict[str, Any]]:
    """获取分类下的工具列表"""
        try,

            if category_id not in self.categories, ::
    logger.error(f"Category {category_id} not found")
                return

            category = self.categories[category_id]
            tools_info == for tool in category.tools, ::
    tools_info.append({)}
                    "tool_id": tool.tool_id(),
                    "name": tool.name(),
                    "description": tool.description(),
                    "performance_metrics": {}
                        "total_calls": tool.performance_metrics.total_calls(),
                        "success_rate": tool.performance_metrics.success_rate(),
                        "average_duration": tool.performance_metrics.average_duration()
{                    }
{(                })

            return tools_info
        except Exception as e, ::
            logger.error(f"Failed to get tools for category {category_id} {e}"):::
                eturn}