# Unified AI Project 核心模块清单

## 1. 功能模块 (Function Modules)

### 1.1 AI代理功能
- **CreativeWritingAgent**: 创意写作与内容生成代理
  - 位置: `apps/backend/src/ai/agents/specialized/creative_writing_agent.py`
  - 功能: 生成营销文案、润色文本等

- **WebSearchAgent**: 网络搜索代理
  - 位置: `apps/backend/src/ai/agents/specialized/web_search_agent.py`
  - 功能: 搜索网络信息

- **ImageGenerationAgent**: 图像生成代理
  - 位置: `apps/backend/src/ai/agents/specialized/image_generation_agent.py`
  - 功能: 生成图像

- **CodeUnderstandingAgent**: 代码理解代理
  - 位置: `apps/backend/src/ai/agents/specialized/code_understanding_agent.py`
  - 功能: 理解和分析代码

- **DataAnalysisAgent**: 数据分析代理
  - 位置: `apps/backend/src/ai/agents/specialized/data_analysis_agent.py`
  - 功能: 分析数据

### 1.2 概念模型功能
- **EnvironmentSimulator**: 环境模拟器
  - 位置: `apps/backend/src/ai/concept_models/environment_simulator.py`
  - 功能: 实现状态预测、动作效果模型和不确定性估计

- **CausalReasoningEngine**: 因果推理引擎
  - 位置: `apps/backend/src/ai/concept_models/causal_reasoning_engine.py`
  - 功能: 实现因果图、干预规划器和反事实推理

- **AlphaDeepModel**: Alpha深度模型
  - 位置: `apps/backend/src/ai/concept_models/alpha_deep_model.py`
  - 功能: 实现数据压缩和学习机制

- **UnifiedSymbolicSpace**: 统一符号空间
  - 位置: `apps/backend/src/ai/concept_models/unified_symbolic_space.py`
  - 功能: 实现符号管理和关系管理

### 1.3 记忆管理功能
- **HAMMemoryManager**: 分层抽象记忆管理器
  - 位置: `apps/backend/src/ai/memory/ham_memory_manager.py`
  - 功能: 管理AI的记忆存储和检索

## 2. 模型模块 (Model Modules)

### 2.1 概念模型
- **AlphaDeepModel**: Alpha深度模型
  - 位置: `apps/backend/src/ai/concept_models/alpha_deep_model.py`
  - 类型: 深度学习模型
  - 功能: 数据压缩和符号空间处理

- **UnifiedSymbolicSpace**: 统一符号空间
  - 位置: `apps/backend/src/ai/concept_models/unified_symbolic_space.py`
  - 类型: 符号处理模型
  - 功能: 符号管理和关系管理

### 2.2 工具模型
- **ArithmeticSeq2Seq**: 算术序列到序列模型
  - 位置: `apps/backend/src/tools/math_model/model.py`
  - 类型: 神经网络模型
  - 功能: 数学计算

- **LogicNNModel**: 逻辑神经网络模型
  - 位置: `apps/backend/src/tools/logic_model/logic_model_nn.py`
  - 类型: 神经网络模型
  - 功能: 逻辑表达式评估

- **LightweightMathModel**: 轻量级数学模型
  - 位置: `apps/backend/src/tools/math_model/lightweight_math_model.py`
  - 类型: 轻量级模型
  - 功能: 基础数学计算

- **LightweightLogicModel**: 轻量级逻辑模型
  - 位置: `apps/backend/src/tools/logic_model/lightweight_logic_model.py`
  - 类型: 轻量级模型
  - 功能: 基础逻辑评估

### 2.3 语言模型
- **DailyLanguageModel**: 日常语言模型
  - 位置: `apps/backend/src/ai/language_models/daily_language_model.py`
  - 类型: 语言模型
  - 功能: 语言理解与生成

### 2.4 代码理解模型
- **LightweightCodeModel**: 轻量级代码模型
  - 位置: `apps/backend/src/ai/code_understanding/lightweight_code_model.py`
  - 类型: 代码理解模型
  - 功能: 代码分析和理解

## 3. 脚本模块 (Script Modules)

### 3.1 启动脚本
- **main.py**: 主启动脚本
  - 位置: `apps/backend/main.py`
  - 功能: 启动Level 5 AGI后端服务

- **start_server.py**: 服务器启动脚本
  - 位置: `apps/backend/start_server.py`
  - 功能: 启动后端API服务器

- **start_server_all_interfaces.py**: 全接口服务器启动脚本
  - 位置: `apps/backend/start_server_all_interfaces.py`
  - 功能: 启动监听所有网络接口的服务器

- **start_chroma_server.py**: ChromaDB服务器启动脚本
  - 位置: `apps/backend/start_chroma_server.py`
  - 功能: 启动ChromaDB向量数据库

### 3.2 训练脚本
- **train_model.py**: 训练模型脚本
  - 位置: `training/train_model.py`
  - 功能: 训练AI模型

- **auto_training_manager.py**: 自动训练管理脚本
  - 位置: `training/auto_training_manager.py`
  - 功能: 管理自动训练过程

- **collaborative_training_manager.py**: 协作训练管理脚本
  - 位置: `training/collaborative_training_manager.py`
  - 功能: 管理协作式训练

- **incremental_learning_manager.py**: 增量学习管理脚本
  - 位置: `training/incremental_learning_manager.py`
  - 功能: 管理增量学习过程

### 3.3 工具脚本
- **unified-fix.py**: 统一修复脚本
  - 位置: `tools/unified-fix.py`
  - 功能: 统一修复系统

- **cli-runner.bat**: CLI运行器脚本
  - 位置: `tools/cli-runner.bat`
  - 功能: 运行CLI工具

## 4. 工具模块 (Tool Modules)

### 4.1 基础工具
- **ToolDispatcher**: 工具调度器
  - 位置: `apps/backend/src/tools/tool_dispatcher.py`
  - 功能: 分发工具请求到相应的工具

- **MathTool**: 数学工具
  - 位置: `apps/backend/src/tools/math_tool.py`
  - 功能: 执行数学计算

- **LogicTool**: 逻辑工具
  - 位置: `apps/backend/src/tools/logic_tool.py`
  - 功能: 评估逻辑表达式

- **WebSearchTool**: 网络搜索工具
  - 位置: `apps/backend/src/tools/web_search_tool.py`
  - 功能: 搜索网络信息

### 4.2 专用工具
- **CodeUnderstandingTool**: 代码理解工具
  - 位置: `apps/backend/src/tools/code_understanding_tool.py`
  - 功能: 分析和理解代码

- **CsvTool**: CSV工具
  - 位置: `apps/backend/src/tools/csv_tool.py`
  - 功能: 分析CSV数据

- **ImageGenerationTool**: 图像生成工具
  - 位置: `apps/backend/src/tools/image_generation_tool.py`
  - 功能: 生成图像

- **TranslationTool**: 翻译工具
  - 位置: `apps/backend/src/tools/translation_tool.py`
  - 功能: 翻译文本

### 4.3 系统工具
- **CalculatorTool**: 计算器工具
  - 位置: `apps/backend/src/tools/calculator_tool.py`
  - 功能: 执行基本计算

- **FileSystemTool**: 文件系统工具
  - 位置: `apps/backend/src/tools/file_system_tool.py`
  - 功能: 操作文件系统

- **ImageRecognitionTool**: 图像识别工具
  - 位置: `apps/backend/src/tools/image_recognition_tool.py`
  - 功能: 识别图像内容

- **SpeechToTextTool**: 语音转文本工具
  - 位置: `apps/backend/src/tools/speech_to_text_tool.py`
  - 功能: 将语音转换为文本