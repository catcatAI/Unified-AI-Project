# 工具调用链追踪机制设计

## 1. 概述

本设计文档详细描述Unified AI Project中工具调用链追踪机制的设计方案，包括调用链数据结构、追踪实现、存储方案、查询机制等。

## 2. 设计目标

1. 实现工具调用链的完整追踪
2. 支持调用关系的可视化展示
3. 提供调用性能分析功能
4. 支持调用链的查询和过滤
5. 保证追踪机制的低性能开销

## 3. 调用链数据结构设计

### 3.1 调用链根对象 (ToolCallChain)

```python
class ToolCallChain:
    """工具调用链"""
    
    def __init__(self, chain_id: str, root_tool_id: str):
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
```

**字段说明：**
- `chain_id`: 调用链的唯一标识符
- `root_tool_id`: 根工具的ID
- `root_call_id`: 根调用的ID
- `calls`: 调用节点字典，以call_id为键
- `created_at`: 调用链创建时间
- `completed_at`: 调用链完成时间
- `duration`: 调用链总耗时
- `success`: 调用链是否成功执行
- `error_message`: 错误信息(如果有的话)
- `metadata`: 调用链的元数据

### 3.2 调用节点对象 (ToolCallNode)

```python
class ToolCallNode:
    """工具调用节点"""
    
    def __init__(self, tool_id: str, call_id: str):
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
```

**字段说明：**
- `call_id`: 调用的唯一标识符
- `tool_id`: 被调用工具的ID
- `parent_id`: 父调用的ID(根调用没有父调用)
- `child_calls`: 子调用ID列表
- `parameters`: 调用时传入的参数
- `result`: 调用的执行结果
- `duration`: 调用耗时
- `success`: 调用是否成功
- `error_message`: 错误信息(如果有的话)
- `started_at`: 调用开始时间
- `completed_at`: 调用完成时间
- `metadata`: 调用的元数据

## 4. 追踪机制实现

### 4.1 调用链上下文管理器

```python
class ToolCallChainContext:
    """工具调用链上下文管理器"""
    
    def __init__(self):
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
            self.current_chain.duration = (
                self.current_chain.completed_at - self.current_chain.created_at
            ).total_seconds()
        chain = self.current_chain
        self.current_chain = None
        self.current_call_stack = []
        return chain
        
    def start_call(self, tool_id: str, parameters: Dict[str, Any]) -> ToolCallNode:
        """开始一个工具调用"""
        if not self.current_chain:
            raise RuntimeError("No active call chain")
            
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
            parent_call.child_calls.append(call_id)
        else:
            # 根调用
            self.current_chain.root_call_id = call_id
            
        # 添加到调用链和调用栈
        self.current_chain.calls[call_id] = call_node
        self.current_call_stack.append(call_node)
        
        return call_node
        
    def end_call(self, result: Any = None, success: bool = True, error_message: Optional[str] = None) -> ToolCallNode:
        """结束当前工具调用"""
        if not self.current_call_stack:
            raise RuntimeError("No active call to end")
            
        # 获取当前调用节点
        call_node = self.current_call_stack.pop()
        call_node.result = result
        call_node.success = success
        call_node.error_message = error_message
        call_node.completed_at = datetime.now()
        call_node.duration = (
            call_node.completed_at - call_node.started_at
        ).total_seconds()
        
        # 更新调用链的成功状态
        if not success and self.current_chain:
            self.current_chain.success = False
            if error_message and not self.current_chain.error_message:
                self.current_chain.error_message = error_message
                
        return call_node
```

### 4.2 工具调用链追踪器

```python
class ToolCallChainTracker:
    """工具调用链追踪器"""
    
    def __init__(self, context_manager: 'ContextManager'):
        self.context_manager = context_manager
        self.chain_context = ToolCallChainContext()
        self.stored_chains: Dict[str, ToolCallChain] = {}  # 存储的调用链
        
    def start_tool_chain(self, root_tool_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """开始工具调用链追踪"""
        chain_id = f"chain-{int(datetime.now().timestamp() * 1000000)}"
        chain = self.chain_context.start_chain(chain_id, root_tool_id)
        if metadata:
            chain.metadata.update(metadata)
        return chain_id
        
    def end_tool_chain(self) -> Optional[str]:
        """结束工具调用链追踪"""
        chain = self.chain_context.end_chain()
        if chain:
            # 存储调用链到上下文管理器
            self._store_chain_to_context(chain)
            # 保存到本地存储
            self.stored_chains[chain.chain_id] = chain
            return chain.chain_id
        return None
        
    def start_tool_call(self, tool_id: str, parameters: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        """开始工具调用追踪"""
        call_node = self.chain_context.start_call(tool_id, parameters)
        if metadata:
            call_node.metadata.update(metadata)
        return call_node.call_id
        
    def end_tool_call(self, result: Any = None, success: bool = True, error_message: Optional[str] = None) -> str:
        """结束工具调用追踪"""
        call_node = self.chain_context.end_call(result, success, error_message)
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
                        "started_at": call.started_at.isoformat(),
                        "completed_at": call.completed_at.isoformat() if call.completed_at else None,
                        "metadata": call.metadata
                    }
                    for call_id, call in chain.calls.items()
                },
                "created_at": chain.created_at.isoformat(),
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
            logger.error(f"Failed to store tool call chain {chain.chain_id}: {e}")
```

## 5. 存储方案设计

### 5.1 内存存储
- 用于存储当前活跃的调用链
- 使用LRU缓存策略，限制存储数量
- 支持快速访问和更新

### 5.2 磁盘存储
- 用于持久化已完成的调用链
- 使用JSON格式存储，便于分析
- 定期归档历史数据

### 5.3 数据库存储
- 用于大规模调用链数据的存储和查询
- 使用向量数据库支持复杂查询
- 支持调用链的全文搜索

## 6. 查询机制设计

### 6.1 基于ID的精确查询
```python
def get_call_chain_by_id(chain_id: str) -> Optional[ToolCallChain]:
    """根据调用链ID获取调用链"""

def get_call_node_by_id(call_id: str) -> Optional[ToolCallNode]:
    """根据调用ID获取调用节点"""
```

### 6.2 基于工具的查询
```python
def get_chains_by_tool_id(tool_id: str) -> List[ToolCallChain]:
    """根据工具ID获取相关调用链"""

def get_calls_by_tool_id(tool_id: str) -> List[ToolCallNode]:
    """根据工具ID获取相关调用节点"""
```

### 6.3 基于时间范围的查询
```python
def get_chains_in_time_range(start_time: datetime, end_time: datetime) -> List[ToolCallChain]:
    """获取指定时间范围内的调用链"""
```

### 6.4 基于性能的查询
```python
def get_slow_chains(threshold: float) -> List[ToolCallChain]:
    """获取执行时间超过阈值的调用链"""

def get_error_chains() -> List[ToolCallChain]:
    """获取执行失败的调用链"""
```

## 7. 可视化展示

### 7.1 调用链树状图
- 展示调用链的层次结构
- 显示每个调用的耗时和状态
- 支持展开/折叠节点

### 7.2 调用时序图
- 展示调用的时间顺序
- 显示并行调用关系
- 标注关键时间点

### 7.3 性能统计图
- 展示各工具的调用次数和成功率
- 显示平均执行时间趋势
- 标识性能瓶颈

## 8. 集成方案

### 8.1 与工具上下文管理器集成
```python
class ToolContextManager:
    def __init__(self, context_manager: ContextManager):
        self.context_manager = context_manager
        self.call_chain_tracker = ToolCallChainTracker(context_manager)
        # ... 其他初始化代码
        
    def register_tool_with_tracking(self, tool_id: str, name: str, description: str = "", category_id: str = "") -> bool:
        """注册带追踪功能的工具"""
        # 先注册工具
        success = self.register_tool(tool_id, name, description, category_id)
        if success:
            # 初始化工具的追踪功能
            logger.info(f"Registered tool {tool_id} with tracking enabled")
        return success
        
    def record_tool_usage_with_tracking(self, tool_id: str, parameters: Dict[str, Any], result: Any, duration: float, success: bool) -> bool:
        """记录带追踪的工具使用"""
        # 记录工具使用
        success = self.record_tool_usage(tool_id, parameters, result, duration, success)
        if success:
            # 更新追踪信息
            logger.info(f"Recorded tool usage for {tool_id} with tracking")
        return success
```

### 8.2 与工具调度器集成
```python
class ToolDispatcher:
    def __init__(self, llm_service: Optional[MultiLLMService] = None):
        # ... 现有初始化代码
        self.call_chain_tracker = ToolCallChainTracker(self.context_manager)
        
    async def dispatch_tool_request_with_tracking(self, tool_name: str, parameters: dict) -> dict:
        """带追踪的工具调度"""
        # 开始工具调用追踪
        call_id = self.call_chain_tracker.start_tool_call(tool_name, parameters)
        
        try:
            # 执行工具调用
            result = await self.dispatch_tool_request(tool_name, parameters)
            
            # 结束工具调用追踪
            self.call_chain_tracker.end_tool_call(
                result=result.get("result"), 
                success=result.get("status") == "success"
            )
            
            return result
        except Exception as e:
            # 记录错误并结束追踪
            self.call_chain_tracker.end_tool_call(
                result=None, 
                success=False, 
                error_message=str(e)
            )
            raise
```

## 9. 性能优化

### 9.1 采样策略
- 对高频调用进行采样追踪
- 只追踪异常或慢速调用
- 支持动态调整采样率

### 9.2 异步处理
- 异步存储调用链数据
- 批量处理追踪信息
- 减少对主流程的影响

### 9.3 数据压缩
- 压缩调用链数据
- 只存储关键信息
- 支持数据归档和清理

## 10. 安全性设计

### 10.1 数据脱敏
- 对敏感参数进行脱敏处理
- 限制结果数据的存储长度
- 支持自定义脱敏规则

### 10.2 访问控制
- 基于角色的访问控制
- 审计日志记录
- 防止未授权访问

### 10.3 数据保护
- 数据加密存储
- 防止数据篡改
- 支持数据备份和恢复

## 11. 预期效果

1. 完整的工具调用链追踪机制，支持调用关系的完整记录
2. 高效的追踪实现，对系统性能影响最小
3. 完善的查询机制，支持多种查询场景
4. 可视化的调用链展示，便于问题分析和性能优化
5. 与现有工具上下文管理器和调度器的良好集成