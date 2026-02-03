# 上下文系统 (Context System)

## 概述

上下文系统是Unified AI Project的核心组件之一，负责管理AI系统中的各种上下文信息，包括工具上下文、模型与代理上下文、对话上下文和记忆上下文。该系统提供了结构化的上下文组织、高效的检索机制和智能的上下文传递功能。

## 系统架构

```
上下文系统
├── 上下文管理器 (ContextManager)
├── 存储层 (Storage)
│   ├── 内存存储 (MemoryStorage)
│   ├── 磁盘存储 (DiskStorage)
│   └── 数据库存储 (DatabaseStorage)
├── 工具上下文子系统 (ToolContextManager)
├── 模型与代理上下文子系统 (ModelContextManager, AgentContextManager)
├── 对话上下文子系统 (DialogueContextManager)
└── 记忆上下文子系统 (MemoryContextManager)
```

## 核心组件

### 1. 上下文管理器 (ContextManager)

上下文管理器是系统的核心，负责协调所有上下文操作。

#### 主要功能：
- 创建和管理上下文
- 上下文的增删改查操作
- 上下文检索和搜索
- 上下文传递和共享

#### 使用示例：

```python
from context.manager import ContextManager
from context.storage.base import ContextType

# 创建上下文管理器
context_manager = ContextManager()

# 创建上下文
context_id = context_manager.create_context(
    ContextType.TOOL, 
    {"name": "测试工具", "version": "1.0"}
)

# 获取上下文
context = context_manager.get_context(context_id)

# 更新上下文
context_manager.update_context(context_id, {"status": "active"})

# 搜索上下文
contexts = context_manager.search_contexts("测试", [ContextType.TOOL])
```

### 2. 存储层 (Storage)

存储层提供了多种存储后端支持，包括内存存储、磁盘存储和数据库存储。

#### 内存存储 (MemoryStorage)
- 用于高频访问的热数据
- 使用LRU缓存策略
- 支持快速读写操作

#### 磁盘存储 (DiskStorage)
- 用于中频访问的温数据
- 使用结构化文件存储
- 支持事务操作

#### 数据库存储 (DatabaseStorage)
- 用于低频访问的冷数据
- 使用向量数据库存储
- 支持复杂查询和检索

### 3. 工具上下文子系统 (ToolContextManager)

管理所有工具的上下文信息，支持工具分类、使用历史记录和性能分析。

#### 主要功能：
- 工具分类管理
- 工具注册和使用记录
- 工具性能指标分析

#### 使用示例：

```python
from context.tool_context import ToolContextManager

# 创建工具上下文管理器
tool_manager = ToolContextManager(context_manager)

# 创建工具分类
tool_manager.create_tool_category("cat_001", "代码工具", "代码相关的工具")

# 注册工具
tool_manager.register_tool("tool_001", "代码生成器", "生成代码片段", "cat_001")

# 记录工具使用
tool_manager.record_tool_usage(
    "tool_001", 
    {"input": "生成一个Python函数"}, 
    "def hello():\n    print('Hello World')", 
    0.5, 
    True
)
```

### 4. 模型与代理上下文子系统 (ModelContextManager, AgentContextManager)

管理模型和代理之间的调用关系及协作机制。

#### 主要功能：
- 模型调用记录和性能分析
- 代理协作管理和状态跟踪
- 调用链追踪和可视化

#### 使用示例：

```python
from context.model_context import ModelContextManager, AgentContextManager

# 创建模型上下文管理器
model_manager = ModelContextManager(context_manager)

# 记录模型调用
model_manager.record_model_call(
    "model_A", 
    "model_B", 
    {"task": "文本摘要"}, 
    "这是摘要内容", 
    1.2, 
    True
)

# 创建代理上下文管理器
agent_manager = AgentContextManager(context_manager)

# 开始代理协作
collaboration_id = agent_manager.start_collaboration(
    "task_001", 
    ["agent_001", "agent_002"]
)
```

### 5. 对话上下文子系统 (DialogueContextManager)

管理对话历史，通过整理和提取重点信息实现高效的上下文传递。

#### 主要功能：
- 对话历史记录和管理
- 关键信息提取和摘要生成
- 对话上下文传递优化

#### 使用示例：

```python
from context.dialogue_context import DialogueContextManager

# 创建对话上下文管理器
dialogue_manager = DialogueContextManager(context_manager)

# 开始对话
conversation_id = "conv_001"
dialogue_manager.start_conversation(conversation_id, ["user", "ai"])

# 添加消息
dialogue_manager.add_message(conversation_id, "user", "你好，我想了解AI技术")

# 生成上下文摘要
summary = dialogue_manager.generate_context_summary(conversation_id)
```

### 6. 记忆上下文子系统 (MemoryContextManager)

管理短期和长期记忆，优化记忆检索效率。

#### 主要功能：
- 分层记忆管理（短期/长期）
- 记忆访问统计和分析
- 记忆转移和清理机制

#### 使用示例：

```python
from context.memory_context import MemoryContextManager

# 创建记忆上下文管理器
memory_manager = MemoryContextManager(context_manager)

# 创建记忆
memory_id = memory_manager.create_memory(
    "用户对AI技术表现出浓厚兴趣", 
    "short_term",
    {"importance": 0.8}
)

# 访问记忆
memory_data = memory_manager.access_memory(memory_id)

# 转移记忆
new_memory_id = memory_manager.transfer_memory(memory_id, "long_term")
```

## 安装和使用

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行演示

```python
python demo_context_system.py
```

### 运行测试

```bash
pytest tests/core_ai/context/test_context_system.py -v
```

## 配置

上下文系统的配置可以通过环境变量或配置文件进行：

```python
# 存储配置
CONTEXT_STORAGE_DIR = "./context_storage"
CONTEXT_MEMORY_MAX_SIZE = 1000

# 性能配置
CONTEXT_CACHE_ENABLED = True
CONTEXT_COMPRESSION_ENABLED = False
```

## API参考

### ContextManager API

- `create_context(context_type, initial_content)` - 创建新的上下文
- `get_context(context_id)` - 获取指定上下文
- `update_context(context_id, updates)` - 更新上下文内容
- `delete_context(context_id)` - 删除上下文
- `search_contexts(query, context_types)` - 搜索上下文
- `transfer_context(source_id, target_id, filter_criteria)` - 传递上下文

### 各子系统API

每个子系统都提供了专门的API来管理特定类型的上下文，详细信息请参考各模块的文档。

## 性能优化

1. **缓存策略**：使用多级缓存架构，提高访问速度
2. **索引优化**：为常用查询字段建立索引
3. **压缩机制**：对大体积上下文数据进行压缩存储
4. **异步处理**：对非关键操作采用异步处理方式

## 安全考虑

1. **数据加密**：敏感上下文数据进行加密存储
2. **访问控制**：实现基于角色的访问控制机制
3. **审计日志**：记录所有上下文操作日志
4. **数据脱敏**：对敏感信息进行脱敏处理

## 扩展性

上下文系统设计具有良好的扩展性：

1. **插件化架构**：支持自定义存储后端和检索算法
2. **模块化设计**：各子系统可以独立扩展和替换
3. **API标准化**：提供标准化的接口便于集成

## 贡献

欢迎提交Issue和Pull Request来改进上下文系统。

## 许可证

本项目采用MIT许可证。