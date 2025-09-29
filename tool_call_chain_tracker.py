"""
工具调用链追踪器实现
基于TOOL_CALL_CHAIN_TRACKING_DESIGN.md设计文档
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from apps.backend.src.core_ai.context.manager import ContextManager
from apps.backend.src.core_ai.context.storage.base import ContextType

logger: Any = logging.getLogger(__name__)


class ToolCallChain:
    """工具调用链"""
    
    def __init__(self, chain_id: str, root_tool_id: str) -> None:
        self.chain_id: str = chain_id  # 调用链唯一标识
        self.root_tool_id: str = root_tool_id  # 根工具ID
        self.root_call_id: str = ""  # 根调用ID
        self.calls: Dict[str, 'ToolCallNode'] = {}  # 调用节点字典，key为call_id
        self.created_at: datetime = datetime.now()  # 创建时间
        self.completed_at: Optional[datetime] = None  # 完成时间
        self.duration: float = 0.0  # 总耗时(秒)
        self.success: bool = True  # 是否成功
        self.error_message: Optional[str] = None  # 错误信息
        self.metadata: Dict[str, Any] = {}  # 元数据


class ToolCallNode:
    """工具调用节点"""
    
    def __init__(self, tool_id: str, call_id: str) -> None:
        self.call_id: str = call_id  # 调用唯一标识
        self.tool_id: str = tool_id  # 工具ID
        self.parent_id: Optional[str] = None  # 父调用ID
        self.child_calls: List[str] = []  # 子调用ID列表
        self.parameters: Dict[str, Any] = {}  # 调用参数
        self.result: Any = None  # 调用结果
        self.duration: float = 0.0  # 调用耗时(秒)
        self.success: bool = True  # 是否成功
        self.error_message: Optional[str] = None  # 错误信息
        self.started_at: datetime = datetime.now()  # 开始时间
        self.completed_at: Optional[datetime] = None  # 完成时间
        self.metadata: Dict[str, Any] = {}  # 元数据


class ToolCallChainContext:
    """工具调用链上下文管理器"""
    
    def __init__(self) -> None:
        self.current_chain: Optional[ToolCallChain] = None
        self.current_call_stack: List[ToolCallNode] = []  # 当前调用栈
        self.call_id_counter: int = 0  # 调用ID计数器
        
    def start_chain(self, chain_id: str, root_tool_id: str) -> ToolCallChain:
        """开始一个新的调用链"""
        self.current_chain = ToolCallChain(chain_id, root_tool_id)
        return self.current_chain
        
    def end_chain(self) -> Optional[ToolCallChain]:
        """结束当前调用链"""
        if self.current_chain:
            self.current_chain.completed_at = datetime.now()
            if self.current_chain.created_at:
                self.current_chain.duration = (
                    self.current_chain.completed_at - self.current_chain.created_at
                _ = ).total_seconds()
        chain = self.current_chain
        self.current_chain = None
        self.current_call_stack = []
        return chain
        
    def start_call(self, tool_id: str, parameters: Dict[str, Any]) -> ToolCallNode:
        """开始一个工具调用"""
        if not self.current_chain:
            _ = raise RuntimeError("No active call chain")
            
        # 生成调用ID
        self.call_id_counter += 1
        call_id = f"{self.current_chain.chain_id}-{self.call_id_counter}"
        
        # 创建调用节点
        call_node = ToolCallNode(tool_id, call_id)
        call_node.parameters = parameters
        call_node.started_at = datetime.now()
        
        # 设置父子关系
        if self.current_call_stack:
            parent_call = self.current_call_stack[-1]
            call_node.parent_id = parent_call.call_id
            _ = parent_call.child_calls.append(call_id)
        else:
            # 根调用
            self.current_chain.root_call_id = call_id
            
        # 添加到调用链和调用栈
        self.current_chain.calls[call_id] = call_node
        _ = self.current_call_stack.append(call_node)
        
        return call_node
        
    def end_call(self, result: Any = None, success: bool = True, error_message: Optional[str] = None) -> ToolCallNode:
        """结束当前工具调用"""
        if not self.current_call_stack:
            _ = raise RuntimeError("No active call to end")
            
        # 获取当前调用节点
        call_node = self.current_call_stack.pop()
        call_node.result = result
        call_node.success = success
        call_node.error_message = error_message
        call_node.completed_at = datetime.now()
        if call_node.started_at:
            call_node.duration = (
                call_node.completed_at - call_node.started_at
            _ = ).total_seconds()
        
        # 更新调用链的成功状态
        if not success and self.current_chain:
            self.current_chain.success = False
            if error_message and not self.current_chain.error_message:
                self.current_chain.error_message = error_message
                
        return call_node


class ToolCallChainTracker:
    """工具调用链追踪器"""
    
    def __init__(self, context_manager: ContextManager) -> None:
        self.context_manager = context_manager
        self.chain_context = ToolCallChainContext()
        self.stored_chains: Dict[str, ToolCallChain] = {}  # 存储的调用链
        
    def start_tool_chain(self, root_tool_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """开始工具调用链追踪"""
        chain_id = f"chain-{int(datetime.now().timestamp() * 1000000)}"
        chain = self.chain_context.start_chain(chain_id, root_tool_id)
        if metadata:
            _ = chain.metadata.update(metadata)
        logger.info(f"Started tool call chain {chain_id} for tool {root_tool_id}")
        return chain_id
        
    def end_tool_chain(self) -> Optional[str]:
        """结束工具调用链追踪"""
        chain = self.chain_context.end_chain()
        if chain:
            # 存储调用链到上下文管理器
            _ = self._store_chain_to_context(chain)
            # 保存到本地存储
            self.stored_chains[chain.chain_id] = chain
            _ = logger.info(f"Ended tool call chain {chain.chain_id}")
            return chain.chain_id
        return None
        
    def start_tool_call(self, tool_id: str, parameters: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        """开始工具调用追踪"""
        call_node = self.chain_context.start_call(tool_id, parameters)
        if metadata:
            _ = call_node.metadata.update(metadata)
        logger.debug(f"Started tool call {call_node.call_id} for tool {tool_id}")
        return call_node.call_id
        
    def end_tool_call(self, result: Any = None, success: bool = True, error_message: Optional[str] = None) -> str:
        """结束工具调用追踪"""
        call_node = self.chain_context.end_call(result, success, error_message)
        logger.debug(f"Ended tool call {call_node.call_id} with success={success}")
        return call_node.call_id
        
    def _store_chain_to_context(self, chain: ToolCallChain):
        """将调用链存储到上下文管理器"""
        try:
            # 创建调用链上下文
            context_content = {
                "chain_id": chain.chain_id,
                "root_tool_id": chain.root_tool_id,
                "root_call_id": chain.root_call_id,
                "calls": {
                    call_id: {
                        "call_id": call.call_id,
                        "tool_id": call.tool_id,
                        "parent_id": call.parent_id,
                        "child_calls": call.child_calls,
                        "parameters": call.parameters,
                        "result": str(call.result)[:1000] if call.result else None,  # 限制结果长度
                        "duration": call.duration,
                        "success": call.success,
                        "error_message": call.error_message,
                        "started_at": call.started_at.isoformat() if call.started_at else None,
                        "completed_at": call.completed_at.isoformat() if call.completed_at else None,
                        "metadata": call.metadata
                    }
                    for call_id, call in chain.calls.items()
                },
                "created_at": chain.created_at.isoformat() if chain.created_at else None,
                "completed_at": chain.completed_at.isoformat() if chain.completed_at else None,
                "duration": chain.duration,
                "success": chain.success,
                "error_message": chain.error_message,
                "metadata": chain.metadata,
                "type": "tool_call_chain"
            }
            
            context_id = self.context_manager.create_context(ContextType.TOOL, context_content)
            logger.info(f"Stored tool call chain {chain.chain_id} with context {context_id}")
        except Exception as e:
            _ = logger.error(f"Failed to store tool call chain {chain.chain_id}: {e}")

    def get_call_chain_by_id(self, chain_id: str) -> Optional[ToolCallChain]:
        """根据调用链ID获取调用链"""
        return self.stored_chains.get(chain_id)

    def get_chains_by_tool_id(self, tool_id: str) -> List[ToolCallChain]:
        """根据工具ID获取相关调用链"""
        result = []
        for chain in self.stored_chains.values():
            if chain.root_tool_id == tool_id:
                _ = result.append(chain)
            else:
                # 检查是否有调用节点使用了该工具
                for call in chain.calls.values():
                    if call.tool_id == tool_id:
                        _ = result.append(chain)
                        break
        return result

    def get_slow_chains(self, threshold: float) -> List[ToolCallChain]:
        """获取执行时间超过阈值的调用链"""
        result = []
        for chain in self.stored_chains.values():
            if chain.duration > threshold:
                _ = result.append(chain)
        return result

    def get_error_chains(self) -> List[ToolCallChain]:
        """获取执行失败的调用链"""
        result = []
        for chain in self.stored_chains.values():
            if not chain.success:
                _ = result.append(chain)
        return result