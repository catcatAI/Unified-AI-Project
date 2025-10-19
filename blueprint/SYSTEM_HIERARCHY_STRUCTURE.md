# Unified AI Project 系统层级结构文档

## 1. 核心系统 (Core Systems)

### 1.1 AI代理系统 (AI Agent System)
**位置**: `apps/backend/src/ai/agents/`

**子系统**:
- BaseAgent子系统 (`base_agent.py`)
- 专门化代理子系统:
  - CreativeWritingAgent (`creative_writing_agent.py`)
  - WebSearchAgent (`web_search_agent.py`)
  - ImageGenerationAgent (`image_generation_agent.py`)
  - CodeUnderstandingAgent (`code_understanding_agent.py`)
  - DataAnalysisAgent (`data_analysis_agent.py`)
  - VisionProcessingAgent (`vision_processing_agent.py`)
  - AudioProcessingAgent (`audio_processing_agent.py`)
  - KnowledgeGraphAgent (`knowledge_graph_agent.py`)
  - NLPProcessingAgent (`nlp_processing_agent.py`)
  - PlanningAgent (`planning_agent.py`)

**下位子系统**:
- 任务分发下位子系统
- HSP连接下位子系统
- 协作管理下位子系统
- 监控管理下位子系统
- 动态注册下位子系统

### 1.2 HSP协议系统 (HSP Protocol System)
**位置**: `apps/backend/src/core/hsp/`

**子系统**:
- 注册机制子系统 (`connector.py`)
- 消息桥接子系统 (`bridge/`)
- 协议转换子系统 (`extensibility.py`)
- 安全子系统 (`security.py`)
- 性能优化子系统 (`performance_optimizer.py`)
- 版本管理子系统 (`versioning.py`)

**下位子系统**:
- 内部协议处理下位子系统 (`internal/`)
- 外部协议适配下位子系统 (`external/`)
- 工具函数下位子系统 (`utils/`)

### 1.3 记忆管理系统 (Memory Management System)
**位置**: `apps/backend/src/ai/memory/`

**子系统**:
- HAMMemoryManager子系统 (`ham_memory_manager.py`)
- DeepMapper子系统 (`../deep_mapper/`)
- VectorStore子系统 (`vector_store.py`)
- 重要性评分子系统 (`importance_scorer.py`)

**下位子系统**:
- 数据库接口下位子系统 (`ham_db_interface.py`)
- 配置管理下位子系统 (`ham_config.py`)
- 错误处理下位子系统 (`ham_errors.py`)
- 类型定义下位子系统 (`ham_types.py`)
- 工具函数下位子系统 (`ham_utils.py`)

### 1.4 概念模型系统 (Concept Model System)
**位置**: `apps/backend/src/ai/concept_models/`

**子系统**:
- EnvironmentSimulator子系统 (`environment_simulator.py`)
- CausalReasoningEngine子系统 (`causal_reasoning_engine.py`)
- AdaptiveLearningController子系统 (`adaptive_learning_controller.py`)
- AlphaDeepModel子系统 (`alpha_deep_model.py`)
- UnifiedSymbolicSpace子系统 (`unified_symbolic_space.py`)

**下位子系统**:
- 压缩模块下位子系统 (`../compression/`)
- 符号空间下位子系统 (`../symbolic_space/`)

## 2. 应用系统 (Application Systems)

### 2.1 后端服务系统 (Backend Service System)
**位置**: `apps/backend/`

**子系统**:
- API服务子系统 (`src/api/`)
- 核心服务子系统 (`src/core/`)
- 服务管理子系统 (`src/services/`)
- 配置管理子系统 (`src/configs/`)
- 数据管理子系统 (`src/data/`)
- 安全认证子系统 (`src/core/security/`)
- 监控管理子系统 (`src/core/monitoring/`)
- 日志管理子系统 (`src/core/logging/`)
- 错误处理子系统 (`src/core/error/`)
- 缓存管理子系统 (`src/core/cache/`)

**下位子系统**:
- 数据库接口下位子系统 (`src/core/database/`)
- 知识管理下位子系统 (`src/core/knowledge/`)
- 工具管理下位子系统 (`src/core/tools/`)
- 内存管理下位子系统 (`src/core/memory/`)
- 同步管理下位子系统 (`src/core/sync/`)
- 共享资源下位子系统 (`src/core/shared/`)
- 管理器下位子系统 (`src/core/managers/`)
- 认知处理下位子系统 (`src/core/cognitive/`)
- 配置管理下位子系统 (`src/core/config/`)
- 创新处理下位子系统 (`src/core/creativity/`)
- 输入输出处理下位子系统 (`src/core/io/`)
- 进化处理下位子系统 (`src/core/evolution/`)
- 融合处理下位子系统 (`src/core/fusion/`)

### 2.2 桌面应用系统 (Desktop Application System)
**位置**: `apps/desktop-app/`

**子系统**:
- Electron应用子系统 (`electron_app/`)
- 游戏引擎子系统
- 用户界面子系统
- 输入处理子系统
- 日志管理子系统 (`logs/`)

### 2.3 Web仪表板系统 (Web Dashboard System)
**位置**: `apps/frontend-dashboard/`

**子系统**:
- 前端界面子系统 (`src/app/`, `src/components/`)
- 数据可视化子系统
- 用户交互子系统 (`src/hooks/`)
- 类型定义子系统 (`src/types/`)
- 库支持子系统 (`src/lib/`)

## 3. 支持系统 (Support Systems)

### 3.1 训练系统 (Training System)
**位置**: `training/`

**子系统**:
- 自动训练管理子系统 (`auto_training_manager.py`)
- 协作式训练子系统 (`collaborative_training_manager.py`)
- 增量学习子系统 (`incremental_learning_manager.py`)
- 分布式优化子系统 (`distributed_optimizer.py`)
- 数据管理子系统 (`data_manager.py`)
- 模型版本控制子系统 (`model_version_controller.py`)
- 资源管理子系统 (`resource_manager.py`)
- 训练监控子系统 (`training_monitor.py`)
- 错误处理子系统 (`error_handling_framework.py`)
- GPU优化子系统 (`gpu_optimizer.py`)
- 任务优先级评估子系统 (`task_priority_evaluator.py`)
- 任务迁移子系统 (`task_migrator.py`)
- 统一执行框架子系统 (`unified_execution_framework.py`)
- 知识共享子系统 (`model_knowledge_sharing.py`)
- 训练状态管理子系统 (`training_state_manager.py`)
- 训练可视化子系统 (`training_visualizer.py`)
- 增强检查点管理子系统 (`enhanced_checkpoint_manager.py`)
- 增强分布式训练容错子系统 (`enhanced_distributed_training_fault_tolerance.py`)

**下位子系统**:
- 配置管理下位子系统 (`configs/`)
- 数据管理下位子系统 (`data/`)
- 模型管理下位子系统 (`models/`)
- 报告生成下位子系统 (`reports/`)
- 状态管理下位子系统 (`states/`)
- 训练执行下位子系统 (`training/`)
- 可视化下位子系统 (`visualizations/`)
- 自适应学习控制器下位子系统 (`adaptive_learning_controller/`)
- 检查点管理下位子系统 (`checkpoints/`)

### 3.2 工具系统 (Tool System)
**位置**: `apps/backend/src/tools/` 和 `tools/`

**子系统**:
- 工具调度器子系统 (`tool_dispatcher.py`)
- 数学工具子系统 (`math_tool.py`)
- 逻辑工具子系统 (`logic_tool.py`)
- Web搜索工具子系统 (`web_search_tool.py`)
- 文件系统工具子系统 (`file_system_tool.py`)
- 计算器工具子系统 (`calculator_tool.py`)
- 代码理解工具子系统 (`code_understanding_tool.py`)
- CSV工具子系统 (`csv_tool.py`)
- 图像生成工具子系统 (`image_generation_tool.py`)
- 图像识别工具子系统 (`image_recognition_tool.py`)
- 自然语言生成工具子系统 (`natural_language_generation_tool.py`)
- 语音转文本工具子系统 (`speech_to_text_tool.py`)
- 翻译工具子系统 (`translation_tool.py`)
- 依赖检查工具子系统 (`dependency_checker.py`)
- JS工具调度器子系统 (`js_tool_dispatcher/`)
- 逻辑模型子系统 (`logic_model/`)
- 数学模型子系统 (`math_model/`)
- 参数提取器子系统 (`parameter_extractor/`)
- 翻译模型子系统 (`translation_model/`)

**下位子系统**:
- 工具调度器下位子系统 (`js_tool_dispatcher/`)

### 3.3 测试系统 (Testing System)
**位置**: `tests/`

**子系统**:
- 单元测试子系统 (`unit/`)
- 集成测试子系统 (`integration/`)
- 端到端测试子系统 (`e2e/`)
- 性能测试子系统 (`performance/`)
- AI测试子系统 (`ai/`)
- 核心AI测试子系统 (`core_ai/`)
- 代理测试子系统 (`agents/`)
- HSP测试子系统 (`hsp/`)
- 工具测试子系统 (`tools/`)
- 训练测试子系统 (`training/`)
- 服务测试子系统 (`services/`)
- 系统测试子系统 (`system/`)
- 数据测试子系统 (`data/`)
- 共享测试子系统 (`shared/`)
- 接口测试子系统 (`interfaces/`)
- 搜索测试子系统 (`search/`)
- 经济测试子系统 (`economy/`)
- 评估测试子系统 (`evaluation/`)
- 元测试子系统 (`meta/`)
- Fragmenta测试子系统 (`fragmenta/`)
- 模块测试子系统 (`modules_fragmenta/`)
- MCP测试子系统 (`mcp/`)
- 宠物测试子系统 (`pet/`)
- 游戏测试子系统 (`game/`)
- CLI测试子系统 (`cli/`)
- 桌面应用测试子系统 (`desktop-app/`)
- 集成测试子系统 (`integrations/`)

**下位子系统**:
- 测试数据管理下位子系统 (`test_data/`)
- 测试输出数据管理下位子系统 (`test_output_data/`)