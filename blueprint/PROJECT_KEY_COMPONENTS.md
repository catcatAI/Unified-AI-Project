# Unified AI Project 关键组件清单

## 1. 启动器 (Launchers)

### 1.1 主应用启动器
- **文件**: `apps/backend/main.py`
- **功能**: Level 5 AGI后端服务主程序，包含完整的应用生命周期管理
- **特点**: 
  - 使用FastAPI框架
  - 支持健康检查和系统状态监控
  - 包含Level 5 AGI状态端点
  - 支持命令行参数配置

### 1.2 服务器启动器
- **文件**: `apps/backend/start_server.py`
- **功能**: 启动后端API服务器
- **特点**: 绑定到127.0.0.1:8000

- **文件**: `apps/backend/start_server_all_interfaces.py`
- **功能**: 启动后端API服务器（监听所有网络接口）
- **特点**: 绑定到0.0.0.0:8000，支持键盘中断处理

- **文件**: `apps/backend/start_chroma_server.py`
- **功能**: 启动ChromaDB服务端
- **特点**: 使用标准ChromaDB命令启动服务器

### 1.3 自动修复工作区启动器
- **文件**: `auto_fix_workspace/launcher.py`
- **功能**: 提供对所有自动修复系统的访问
- **特点**: 设置工作区路径，导出路径变量

## 2. 管理器 (Managers)

### 2.1 核心管理器
- **文件**: `apps/backend/src/core/managers/system_manager.py`
- **功能**: 系统管理器，负责系统初始化和关闭
- **特点**: 简单的状态管理

- **文件**: `apps/backend/src/ai/agent_manager.py`
- **功能**: AI代理管理器，管理AI代理的生命周期
- **特点**: 支持代理注册、启动、停止和健康检查

- **文件**: `apps/backend/src/ai/agent_collaboration_manager.py`
- **功能**: AI代理协作管理器，处理代理间的任务委托和结果聚合
- **特点**: 支持多代理任务编排

- **文件**: `apps/backend/src/ai/agent_monitoring_manager.py`
- **功能**: AI代理监控管理器，监控代理的健康状态
- **特点**: 支持心跳检测和性能指标收集

### 2.2 内存管理器
- **文件**: `apps/backend/src/ai/memory/ham_memory_manager.py`
- **功能**: 分层抽象记忆管理器，管理AI的记忆存储和检索
- **特点**: 支持加密、压缩和向量存储

### 2.3 依赖管理器
- **文件**: `apps/backend/src/ai/dependency_manager.py`
- **功能**: 依赖管理器，管理项目依赖
- **特点**: 支持依赖检查和版本管理

## 3. 设置和配置 (Settings & Configuration)

### 3.1 系统配置
- **文件**: `apps/backend/src/core/config/system_config.py`
- **功能**: 系统配置管理
- **特点**: 提供系统配置加载和管理功能

### 3.2 Level 5配置
- **文件**: `apps/backend/src/core/config/level5_config.py`
- **功能**: Level 5 AGI配置管理
- **特点**: 提供动态状态监控和静态能力配置

## 4. 其他关键组件

### 4.1 HSP连接器
- **文件**: `apps/backend/src/core/hsp/connector.py`
- **功能**: 高速同步协议连接器，处理AI间的通信
- **特点**: 支持MQTT协议，包含安全管理和性能优化

### 4.2 工具调度器
- **文件**: `apps/backend/src/tools/tool_dispatcher.py`
- **功能**: 工具调度器，分发工具请求到相应的工具
- **特点**: 支持多种工具类型，包含RAG查询功能

### 4.3 因果推理引擎
- **文件**: `apps/backend/src/ai/concept_models/causal_reasoning_engine.py`
- **功能**: 因果推理引擎，实现因果图、干预规划和反事实推理
- **特点**: 基于PyTorch实现，支持模型训练

### 4.4 数学工具
- **文件**: `apps/backend/src/tools/math_tool.py`
- **功能**: 数学计算工具
- **特点**: 支持自然语言数学问题解析和计算

### 4.5 逻辑工具
- **文件**: `apps/backend/src/tools/logic_tool.py`
- **功能**: 逻辑表达式评估工具
- **特点**: 支持逻辑表达式解析和评估