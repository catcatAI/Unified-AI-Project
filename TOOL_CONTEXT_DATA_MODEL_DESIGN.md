# 工具上下文数据模型设计

## 1. 概述

本设计文档详细描述Unified AI Project中工具上下文数据模型的设计方案，包括数据结构、存储方案、查询机制等。

## 2. 设计目标

1. 支持工具使用历史记录的完整存储
2. 支持工具性能指标的实时更新和查询
3. 支持工具调用链的追踪和分析
4. 提供高效的上下文检索机制
5. 支持工具使用模式分析和推荐

## 3. 数据模型设计

### 3.1 工具分类数据模型 (ToolCategory)

```python
class ToolCategory:
    """工具分类"""
    
    def __init__(self, category_id: str, name: str, description: str = "", parent_id: Optional[str] = None):
        self.category_id: str = category_id  # 分类唯一标识
        self.name: str = name  # 分类名称
        self.description: str = description  # 分类描述
        self.parent_id: Optional[str] = parent_id  # 父分类ID
        self.sub_categories: List['ToolCategory'] = []  # 子分类列表
        self.tools: List['Tool'] = []  # 包含的工具列表
        self.created_at: datetime = datetime.now()  # 创建时间
        self.updated_at: datetime = datetime.now()  # 更新时间
```

**字段说明：**
- `category_id`: 分类的唯一标识符
- `name`: 分类名称
- `description`: 分类的详细描述
- `parent_id`: 父分类的ID，用于构建分类树结构
- `sub_categories`: 子分类列表
- `tools`: 属于该分类的工具列表
- `created_at`: 分类创建时间
- `updated_at`: 分类最后更新时间

### 3.2 工具数据模型 (Tool)

```python
class Tool:
    """工具定义"""
    
    def __init__(self, tool_id: str, name: str, description: str = "", category_id: str = ""):
        self.tool_id: str = tool_id  # 工具唯一标识
        self.name: str = name  # 工具名称
        self.description: str = description  # 工具描述
        self.category_id: str = category_id  # 所属分类ID
        self.usage_history: List['ToolUsageRecord'] = []  # 使用历史记录
        self.performance_metrics: 'ToolPerformanceMetrics' = ToolPerformanceMetrics()  # 性能指标
        self.created_at: datetime = datetime.now()  # 创建时间
        self.updated_at: datetime = datetime.now()  # 更新时间
```

**字段说明：**
- `tool_id`: 工具的唯一标识符
- `name`: 工具名称
- `description`: 工具的详细描述
- `category_id`: 工具所属分类的ID
- `usage_history`: 工具使用历史记录列表
- `performance_metrics`: 工具性能指标对象
- `created_at`: 工具创建时间
- `updated_at`: 工具最后更新时间

### 3.3 工具使用记录数据模型 (ToolUsageRecord)

```python
class ToolUsageRecord:
    """工具使用记录"""
    
    def __init__(self, parameters: Dict[str, Any], result: Any, duration: float, success: bool):
        self.timestamp: datetime = datetime.now()  # 使用时间戳
        self.parameters: Dict[str, Any] = parameters  # 调用参数
        self.result: Any = result  # 执行结果
        self.duration: float = duration  # 执行耗时(秒)
        self.success: bool = success  # 执行是否成功
        self.context_id: str = ""  # 关联的上下文ID
        self.session_id: str = ""  # 会话ID
        self.user_id: str = ""  # 用户ID
```

**字段说明：**
- `timestamp`: 工具使用的时间戳
- `parameters`: 工具调用时传入的参数
- `result`: 工具执行的结果
- `duration`: 工具执行的耗时(秒)
- `success`: 工具执行是否成功
- `context_id`: 关联的上下文ID
- `session_id`: 会话ID
- `user_id`: 用户ID

### 3.4 工具性能指标数据模型 (ToolPerformanceMetrics)

```python
class ToolPerformanceMetrics:
    """工具性能指标"""
    
    def __init__(self):
        self.total_calls: int = 0  # 总调用次数
        self.success_rate: float = 0.0  # 成功率
        self.average_duration: float = 0.0  # 平均执行时间
        self.min_duration: float = float('inf')  # 最小执行时间
        self.max_duration: float = 0.0  # 最大执行时间
        self.last_used: Optional[datetime] = None  # 最后使用时间
        self.error_count: int = 0  # 错误次数
        self.updated_at: datetime = datetime.now()  # 更新时间
```

**字段说明：**
- `total_calls`: 工具被调用的总次数
- `success_rate`: 工具调用的成功率
- `average_duration`: 工具执行的平均耗时
- `min_duration`: 工具执行的最小耗时
- `max_duration`: 工具执行的最大耗时
- `last_used`: 工具最后被使用的时间
- `error_count`: 工具调用出错的次数
- `updated_at`: 性能指标最后更新时间

### 3.5 工具调用链数据模型 (ToolCallChain)

```python
class ToolCallChain:
    """工具调用链"""
    
    def __init__(self, chain_id: str):
        self.chain_id: str = chain_id  # 调用链ID
        self.root_call: Optional['ToolCallNode'] = None  # 根调用节点
        self.calls: List['ToolCallNode'] = []  # 调用节点列表
        self.created_at: datetime = datetime.now()  # 创建时间
        self.completed_at: Optional[datetime] = None  # 完成时间
        self.duration: float = 0.0  # 总耗时
        self.success: bool = True  # 是否成功
```

```python
class ToolCallNode:
    """工具调用节点"""
    
    def __init__(self, tool_id: str, call_id: str):
        self.call_id: str = call_id  # 调用ID
        self.tool_id: str = tool_id  # 工具ID
        self.parent_id: Optional[str] = None  # 父调用ID
        self.child_calls: List[str] = []  # 子调用ID列表
        self.parameters: Dict[str, Any] = {}  # 调用参数
        self.result: Any = None  # 调用结果
        self.duration: float = 0.0  # 调用耗时
        self.success: bool = True  # 是否成功
        self.started_at: datetime = datetime.now()  # 开始时间
        self.completed_at: Optional[datetime] = None  # 完成时间
```

## 4. 存储方案设计

### 4.1 内存存储
- 用于高频访问的热数据
- 使用LRU缓存策略
- 支持快速读写操作

### 4.2 磁盘存储
- 用于中频访问的温数据
- 使用结构化文件存储(JSON格式)
- 支持事务操作

### 4.3 数据库存储
- 用于低频访问的冷数据
- 使用向量数据库存储(如Faiss或Pinecone)
- 支持复杂查询和检索

## 5. 查询机制设计

### 5.1 基于ID的精确查询
```python
def get_tool_by_id(tool_id: str) -> Optional[Tool]:
    """根据工具ID获取工具对象"""

def get_category_by_id(category_id: str) -> Optional[ToolCategory]:
    """根据分类ID获取分类对象"""
```

### 5.2 基于属性的过滤查询
```python
def search_tools_by_category(category_id: str) -> List[Tool]:
    """根据分类ID搜索工具"""

def search_tools_by_name(name_pattern: str) -> List[Tool]:
    """根据名称模式搜索工具"""
```

### 5.3 基于时间范围的查询
```python
def get_tool_usage_history(tool_id: str, start_time: datetime, end_time: datetime) -> List[ToolUsageRecord]:
    """获取指定时间范围内的工具使用历史"""
```

### 5.4 基于性能指标的排序查询
```python
def get_top_performing_tools(limit: int = 10) -> List[Tool]:
    """获取性能最好的工具列表"""

def get_most_used_tools(limit: int = 10) -> List[Tool]:
    """获取使用最频繁的工具列表"""
```

## 6. 数据同步机制

### 6.1 实时更新
- 工具使用记录实时写入内存
- 性能指标实时计算和更新
- 调用链实时构建和维护

### 6.2 批量持久化
- 定期将内存数据批量写入磁盘
- 异步写入数据库存储
- 支持数据恢复和回滚

### 6.3 数据一致性保证
- 使用事务机制保证数据一致性
- 实现数据版本控制
- 支持数据校验和修复

## 7. 扩展性设计

### 7.1 插件化扩展
- 支持自定义数据字段
- 支持自定义查询条件
- 支持自定义存储策略

### 7.2 分布式支持
- 支持分布式存储
- 支持数据分片
- 支持负载均衡

### 7.3 版本兼容性
- 支持数据模型版本管理
- 支持向后兼容
- 支持数据迁移工具

## 8. 安全性设计

### 8.1 数据加密
- 敏感数据加密存储
- 传输过程加密
- 访问权限控制

### 8.2 访问控制
- 基于角色的访问控制(RBAC)
- 细粒度权限管理
- 审计日志记录

### 8.3 数据保护
- 数据备份和恢复
- 防止数据篡改
- 数据完整性校验

## 9. 性能优化

### 9.1 索引优化
- 建立复合索引提高查询效率
- 使用全文索引支持文本搜索
- 使用向量索引支持语义检索

### 9.2 缓存策略
- 多级缓存架构
- 智能缓存预热
- 缓存失效机制

### 9.3 并发控制
- 读写锁机制
- 乐观锁控制
- 事务隔离级别

## 10. 预期效果

1. 完整的工具上下文数据模型，支持工具使用历史记录
2. 实时更新的性能指标，支持工具性能分析
3. 完善的工具调用链追踪机制，支持调用关系分析
4. 高效的查询机制，支持多种查询场景
5. 良好的扩展性设计，支持未来功能扩展