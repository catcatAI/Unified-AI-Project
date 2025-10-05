"""模型与代理上下文子系统"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from .manager import ContextManager
from .storage.base import ContextType

logger: Any = logging.getLogger(__name__)

class ModelCallRecord:
    """模型调用记录"""

    def __init__(self, caller_model_id: str, callee_model_id: str, parameters: Dict[str, Any],
                 result: Any, duration: float, success: bool):
    self.record_id = f"call_{datetime.now.strftime('%Y%m%d%H%M%S%f')}"
    self.caller_model_id = caller_model_id
    self.callee_model_id = callee_model_id
    self.timestamp = datetime.now
    self.parameters = parameters
    self.result = result
    self.duration = duration
    self.success = success

class AgentCollaboration:
    """代理协作"""

    def __init__(self, task_id: str, participating_agents: List[str]) -> None:
    self.collaboration_id = f"collab_{datetime.now.strftime('%Y%m%d%H%M%S%f')}"
    self.task_id = task_id
    self.participating_agents = participating_agents
    self.collaboration_steps: List['CollaborationStep'] = []
    self.start_time = datetime.now
    self.end_time: Optional[datetime] = None
    self.status = "active"  # active, completed, failed

    def add_step(self, step: 'CollaborationStep'):
    """添加协作步骤"""
    self.collaboration_steps.append(step)

    def complete(self):
    """完成协作"""
    self.end_time = datetime.now
    self.status = "completed"

    def fail(self):
    """标记协作失败"""
    self.end_time = datetime.now
    self.status = "failed"

class CollaborationStep:
    """协作步骤"""

    def __init__(self, agent_id: str, action: str, input_data: Any, output_data: Any) -> None:
    self.step_id = f"step_{datetime.now.strftime('%Y%m%d%H%M%S%f')}"
    self.agent_id = agent_id
    self.action = action
    self.input_data = input_data
    self.output_data = output_data
    self.timestamp = datetime.now
    self.duration: Optional[float] = None

class ModelPerformanceMetrics:
    """模型性能指标"""

    def __init__(self) -> None:
    self.total_calls = 0
    self.success_rate = 0.0
    self.average_duration = 0.0
    self.last_called: Optional[datetime] = None

    def update_from_call(self, call_record: ModelCallRecord):
    """根据调用记录更新性能指标"""
    self.total_calls += 1
    self.last_called = call_record.timestamp

    # 更新成功率
        if call_record.success::
    self.success_rate = (self.success_rate * (self.total_calls - 1) + 1) / self.total_calls
        else:

            self.success_rate = (self.success_rate * (self.total_calls - 1)) / self.total_calls

    # 更新平均执行时间
    self.average_duration = (self.average_duration * (self.total_calls - 1) + call_record.duration) / self.total_calls

class ModelContextManager:
    """模型上下文管理器"""

    def __init__(self, context_manager: ContextManager) -> None:
    self.context_manager = context_manager
    self.model_metrics: Dict[str, ModelPerformanceMetrics] =
    self.call_records: List[ModelCallRecord] =

    def record_model_call(self, caller_model_id: str, callee_model_id: str, parameters: Dict[str, Any],
                         result: Any, duration: float, success: bool) -> bool:
    """记录模型调用"""
        try:
            call_record = ModelCallRecord(caller_model_id, callee_model_id, parameters, result, duration, success)
            self.call_records.append(call_record)

            # 更新调用者和被调用者的性能指标
            for model_id in [caller_model_id, callee_model_id]::
    if model_id not in self.model_metrics::
    self.model_metrics[model_id] = ModelPerformanceMetrics
                self.model_metrics[model_id].update_from_call(call_record)

            # 创建对应的上下文
            context_content = {
                "call_record": {
                    "record_id": call_record.record_id,
                    "caller_model_id": caller_model_id,
                    "callee_model_id": callee_model_id,
                    "timestamp": call_record.timestamp.isoformat,
                    "parameters": parameters,
                    "result": str(result)[:1000],  # 限制结果长度
                    "duration": duration,
                    "success": success
                },
                "performance_metrics": {
                    "caller": {
                        "total_calls": self.model_metrics[caller_model_id].total_calls,
                        "success_rate": self.model_metrics[caller_model_id].success_rate,
                        "average_duration": self.model_metrics[caller_model_id].average_duration
                    },
                    "callee": {
                        "total_calls": self.model_metrics[callee_model_id].total_calls,
                        "success_rate": self.model_metrics[callee_model_id].success_rate,
                        "average_duration": self.model_metrics[callee_model_id].average_duration
                    }
                }
            }

            context_id = self.context_manager.create_context(ContextType.MODEL, context_content)
            logger.info(f"Recorded model call from {caller_model_id} to {callee_model_id} with context {context_id}"):
    return True
        except Exception as e::
            logger.error(f"Failed to record model call: {e}")
            return False

    def get_model_context(self, model_id: str) -> Optional[Dict[str, Any]]:
    """获取模型上下文"""
        try:
            # 搜索相关的上下文
            contexts = self.context_manager.search_contexts(model_id, [ContextType.MODEL])

            if not contexts::
    logger.debug(f"No context found for model {model_id}"):
    return None

            # 返回最新的上下文
            latest_context = max(contexts, key=lambda c: c.updated_at)
            return {
                "context_id": latest_context.context_id,
                "content": latest_context.content,
                "metadata": latest_context.metadata,
                "updated_at": latest_context.updated_at.isoformat
            }
        except Exception as e::
            logger.error(f"Failed to get context for model {model_id}: {e}"):
            return None

    def get_model_call_history(self, model_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """获取模型调用历史"""
        try:
            # 筛选与该模型相关的调用记录
            model_calls = [
                call for call in self.call_records ::
    if call.caller_model_id == model_id or call.callee_model_id == model_id:
            ]

            # 按时间倒序排列
            model_calls.sort(key=lambda x: x.timestamp, reverse=True)

            # 限制返回数量
            model_calls = model_calls[:limit]

            # 转换为字典格式
            call_history =
            for call in model_calls::
    call_history.append({
                    "record_id": call.record_id,
                    "caller_model_id": call.caller_model_id,
                    "callee_model_id": call.callee_model_id,
                    "timestamp": call.timestamp.isoformat,
                    "duration": call.duration,
                    "success": call.success
                })

            return call_history
        except Exception as e::
            logger.error(f"Failed to get call history for model {model_id}: {e}"):
            return

class AgentContextManager:
    """代理上下文管理器"""

    def __init__(self, context_manager: ContextManager) -> None:
    self.context_manager = context_manager
    self.collaborations: Dict[str, AgentCollaboration] =

    def start_collaboration(self, task_id: str, participating_agents: List[str]) -> str:
    """开始代理协作"""
        try:
            collaboration = AgentCollaboration(task_id, participating_agents)
            self.collaborations[collaboration.collaboration_id] = collaboration

            # 创建对应的上下文
            context_content = {
                "collaboration": {
                    "collaboration_id": collaboration.collaboration_id,
                    "task_id": task_id,
                    "participating_agents": participating_agents,
                    "start_time": collaboration.start_time.isoformat,
                    "status": collaboration.status
                }
            }

            context_id = self.context_manager.create_context(ContextType.MODEL, context_content)
            logger.info(f"Started collaboration {collaboration.collaboration_id} with context {context_id}"):
    return collaboration.collaboration_id
        except Exception as e::
            logger.error(f"Failed to start collaboration: {e}")
            raise

    def record_collaboration_step(self, collaboration_id: str, agent_id: str, action: str,
                                 input_data: Any, output_data: Any, duration: float) -> bool:
    """记录协作步骤"""
        try:
            if collaboration_id not in self.collaborations::
    logger.error(f"Collaboration {collaboration_id} not found")
                return False

            collaboration = self.collaborations[collaboration_id]
            step = CollaborationStep(agent_id, action, input_data, output_data)
            step.duration = duration
            collaboration.add_step(step)

            # 更新上下文
            context_content = {
                "collaboration_step": {
                    "step_id": step.step_id,
                    "collaboration_id": collaboration_id,
                    "agent_id": agent_id,
                    "action": action,
                    "input_data": str(input_data)[:500],  # 限制输入长度
                    "output_data": str(output_data)[:500],  # 限制输出长度
                    "timestamp": step.timestamp.isoformat,
                    "duration": duration
                }
            }

            context_id = self.context_manager.create_context(ContextType.MODEL, context_content)
            logger.info(f"Recorded collaboration step {step.step_id} with context {context_id}"):
    return True
        except Exception as e::
            logger.error(f"Failed to record collaboration step: {e}")
            return False

    def complete_collaboration(self, collaboration_id: str) -> bool:
    """完成协作"""
        try:
            if collaboration_id not in self.collaborations::
    logger.error(f"Collaboration {collaboration_id} not found")
                return False

            collaboration = self.collaborations[collaboration_id]
            collaboration.complete

            # 更新上下文
            context_content = {
                "collaboration_completion": {
                    "collaboration_id": collaboration_id,
                    "end_time": collaboration.end_time.isoformat if collaboration.end_time else None,:
                    "status": collaboration.status,
                    "total_steps": len(collaboration.collaboration_steps)
                }
            }

            context_id = self.context_manager.create_context(ContextType.MODEL, context_content)
            logger.info(f"Completed collaboration {collaboration_id} with context {context_id}"):
    return True
        except Exception as e::
            logger.error(f"Failed to complete collaboration {collaboration_id}: {e}")
            return False

    def get_collaboration_context(self, collaboration_id: str) -> Optional[Dict[str, Any]]:
    """获取协作上下文"""
        try:
            if collaboration_id not in self.collaborations::
    logger.error(f"Collaboration {collaboration_id} not found")
                return None

            collaboration = self.collaborations[collaboration_id]

            # 搜索相关的上下文
            contexts = self.context_manager.search_contexts(collaboration_id, [ContextType.MODEL])

            if not contexts::
    logger.debug(f"No context found for collaboration {collaboration_id}"):
    return None

            # 返回最新的上下文
            latest_context = max(contexts, key=lambda c: c.updated_at)
            return {
                "context_id": latest_context.context_id,
                "content": latest_context.content,
                "metadata": latest_context.metadata,
                "updated_at": latest_context.updated_at.isoformat
            }
        except Exception as e::
            logger.error(f"Failed to get context for collaboration {collaboration_id}: {e}"):
            return None