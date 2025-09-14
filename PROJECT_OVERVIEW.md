# Unified AI Project 全貌文档

## 1. 项目概述

### 1.1 项目背景与目标
Unified AI Project 是一个面向 AGI（Level 3-4）的混合式 AI 生态系统，采用 monorepo 架构。项目的核心设计理念是"数据生命"（Data Life），通过持续认知循环实现真正的 AI 自主学习与进化。

项目旨在以"架构优先"的理念，在低资源、低成本的条件下，探索一条通往 Level 4 自主学习 AGI 的可行路径。

### 1.1.1 项目完成状态
- **总体进度**: 100% 完成 (275/275 任务)
- **核心功能**: 全部实现并通过测试
- **训练系统**: 完整实现，支持多场景训练
- **AI代理系统**: 8个专业代理全部完成，结构一致性已修复
- **CLI工具**: 统一命令行界面完成
- **桌面应用**: "Angela's World" 游戏客户端完成
- **文档系统**: 完整文档体系建立
- **测试覆盖**: 测试用例收集完成，所有主要错误已修复，测试稳定性优化
- **代码质量**: 核心架构稳定，所有导入路径、语法问题和代理结构不一致性已解决
- **核心功能验证**: 所有AI代理创建和功能测试通过，包括专门化代理的完整功能验证

### 1.2 核心特色
- **分层与闭環架构**：采用"大模型（推理层）+ 行动子模型（操作层）"的分层设计，构建"感知-决策-行动-回饋"的完整行动闭環，实现真正的自主学习。
- **統一模態表示**：探索将多模态数据（文本、音頻、圖像）压缩映射到統一的符號空間，降低跨模態處理的複雜度。
- **持續學習**：以時間分割的線性學習取代一次性大规模訓練，讓模型能在使用過程中持續進化，有效分摊訓練成本。
- **低資源部署**：專為資源受限環境（如個人電腦）設計，通過輕量化模型與高效架構，在低成本下實現高階 AGI 能力。
- **HSP 協議**：高速同步協議支援內部模塊與外部 AI 協作。
- **語義級安全**：基於 UID/Key 機制的深度資料保護。

### 1.3 AGI 等级评估
- **当前状态**：Level 2-3（推理 AI 到初步自主学习）
- **设计目标**：Level 3-4（胜任到专家级 AGI）
- **理论上限**：Level 5（超人类 AGI，通过群体智慧）
- **实现进展**：核心架构完成，训练系统就绪，准备进入 Level 3 测试阶段
- **技术挑战**：HSP连接稳定性、测试覆盖率、增量学习效果优化

## 2. 系统架构

### 2.1 整体架构
项目采用 monorepo 架构，组织成应用程序和包，围绕一个独特的 AI 驱动模拟游戏"Angela's World"构建。

```
Unified-AI-Project/
├── apps/                  # 应用程序目录
│   ├── backend/           # 核心后端服务
│   ├── desktop-app/       # 桌面游戏客户端
│   └── frontend-dashboard/ # Web 仪表板
├── packages/              # 共享包
│   ├── cli/               # 命令行工具
│   └── ui/                # 共享 UI 组件
├── training/              # 训练系统
├── tools/                 # 工具脚本
├── scripts/               # 脚本目录
└── docs/                  # 文档目录
```

### 2.2 核心组件

#### 2.2.1 AI 代理系统 (`apps/backend/src/agents/`)
- **BaseAgent**：所有专门化代理的基础类，处理 HSP 连接与任务分发
- **CreativeWritingAgent**：创意写作与内容生成代理
- **ImageGenerationAgent**：图像生成代理
- **WebSearchAgent**：网络搜索代理
- **DataAnalysisAgent**：数据分析与处理代理

**实现状态**: ✅ 已实现并通过创建与功能测试；其他专门化能力由 ai 模块提供（如代码理解、音频处理等）

#### 2.2.2 HSP 高速同步协议 (`apps/backend/src/hsp/`)
支持内部模块与外部 AI 实体的可信协作，包含：
- 注册机制：新模块/AI 加入网络
- 信譽系统：评估协作实体可信度
- 热更新：动态载入新功能模块

**实现状态**: ✅ 核心功能完成，MQTT连接稳定性已优化

#### 2.2.3 记忆管理系统 (`apps/backend/src/ai/memory/`)
- **DeepMapper / importance_scorer**：语义映射与资料核生成与重要性评估
- **HAMMemoryManager**：分层语义记忆管理
- **VectorStore**：基于 ChromaDB 的向量数据库接口

**实现状态**: ✅ 全部完成，测试通过

#### 2.2.4 概念模型与推理组件（`apps/backend/src/ai/`）
- **EnvironmentSimulator**：环境模拟器（`ai/world_model/environment_simulator.py`）
- **CausalReasoningEngine**：因果推理引擎（`ai/reasoning/causal_reasoning_engine.py`）
- **AdaptiveLearningController**：自适应学习控制器（`ai/meta/adaptive_learning_controller.py`）
- **AlphaDeepModel**：Alpha 深度模型（`ai/compression/alpha_deep_model.py`）

**实现状态**: ✅ 相关核心能力可用，AlphaDeepModel测试 9/9 通过

#### 2.2.5 核心服务 (`apps/backend/src/core_services.py`)
- **MultiLLMService**：多语言模型服务
- **HAMMemoryManager**：分层抽象记忆管理器
- **AgentManager**：代理管理器
- **DialogueManager**：对话管理器
- **LearningManager**：学习管理器

## 3. 训练系统

### 3.1 系统组成
训练系统包含多个核心组件：

1. **ModelTrainer** (`training/train_model.py`)：模型训练器，支持多种预设训练场景和协作式训练
2. **CollaborativeTrainingManager** (`training/collaborative_training_manager.py`)：协作式训练管理器，负责协调所有模型的训练过程
3. **AutoTrainingManager** (`training/auto_training_manager.py`)：自动训练管理器，实现自动识别训练数据、自动建立训练和自动训练的功能
4. **IncrementalLearningManager** (`training/incremental_learning_manager.py`)：增量学习管理器，实现增量数据识别、增量模型训练、智能训练触发和自动模型整理功能

### 3.2 训练场景预设
预设配置包含多种训练场景：
1. **快速开始**：使用模拟数据快速训练测试
2. **全面训练**：使用所有可用数据完整训练
3. **完整数据集训练**：使用完整数据集进行长期训练，支持自动暂停和恢复
4. **视觉专注**：专注训练视觉相关模型
5. **音频专注**：专注训练音频相关模型
6. **数学模型训练**：专门训练数学计算模型
7. **逻辑模型训练**：专门训练逻辑推理模型
8. **概念模型训练**：训练所有概念模型
9. **协作式训练**：多模型协作训练
10. **代码模型训练**：训练代码理解和生成模型
11. **数据分析模型训练**：训练数据分析和处理模型

### 3.3 增强型自动训练系统
项目包含一个增强型的完整自动训练系统，可以自动识别训练数据、自动建立训练配置并自动执行训练：

1. **智能数据识别**：系统会自动扫描数据目录，识别和分类可用的训练数据，支持更多数据类型
2. **高级质量评估**：对识别的数据进行质量评估，自动筛选高价值训练数据
3. **智能配置生成**：根据识别的数据和质量评估结果，自动生成最优的训练配置和参数
4. **多场景训练执行**：根据配置自动执行多场景训练
5. **协作式训练**：支持多模型间的知识共享和协作训练
6. **实时监控和日志**：提供训练过程的实时监控和详细日志记录
7. **智能结果分析**：自动分析训练结果，生成详细的性能报告

## 4. 技术栈

### 4.1 前端技术
- **桌面应用**：Electron
- **Web 仪表板**：Next.js 15, TypeScript 5, Tailwind CSS 4, shadcn/ui
- **共享 UI 组件**：React, TypeScript

### 4.2 后端技术
- **主要语言**：Python 3.8+
- **Web 框架**：FastAPI
- **AI 框架**：TensorFlow, PyTorch, NumPy, Scikit-learn
- **数据库**：ChromaDB（向量数据库）
- **消息队列**：MQTT

### 4.3 工具与构建
- **包管理**：pnpm
- **构建工具**：concurrently, cross-env
- **测试框架**：pytest
- **部署工具**：Electron-builder

## 5. 项目目录结构

```
Unified-AI-Project/
├── apps/
│   ├── backend/
│   │   ├── src/
│   │   │   ├── agents/              # AI 代理系统
│   │   │   ├── ai/                  # 核心 AI 组件（memory、reasoning、world_model 等）
│   │   │   ├── hsp/                 # HSP 协议
│   │   │   ├── services/            # 核心服务
│   │   │   └── ...
│   │   ├── configs/                 # 配置文件
│   │   └── README.md
│   ├── desktop-app/                 # 桌面应用
│   │   └── README.md
│   └── frontend-dashboard/          # Web 仪表板
│       └── README.md
├── packages/
│   ├── cli/                         # 命令行工具
│   │   └── README.md
│   └── ui/                          # 共享 UI 组件
│       └── README.md
├── training/                        # 训练系统
│   ├── configs/                     # 训练配置
│   ├── models/                      # 模型文件
│   ├── reports/                     # 训练报告
│   └── ...
├── tools/                           # 工具脚本
├── scripts/                         # 脚本目录
├── docs/                            # 文档目录
├── README.md                        # 项目主文档
└── package.json                     # 项目配置
```

## 6. CLI 工具

项目提供了一套完整的命令行界面(CLI)工具，用于与AI系统进行交互：

### 6.1 CLI 工具组件
1. **Unified CLI** - 通用AI交互工具
2. **AI Models CLI** - AI模型管理与交互工具
3. **HSP CLI** - 超结构协议工具

### 6.2 使用方法
可以通过以下方式使用CLI工具：

```bash
# 使用统一管理脚本
unified-ai.bat  # Windows
./unified-ai.bat # 或在tools目录下运行

# 使用CLI运行器
tools\cli-runner.bat
tools\cli-runner.bat unified-cli health
tools\cli-runner.bat ai-models-cli list
tools\cli-runner.bat hsp-cli query "Hello"

# 安装为系统命令
tools\cli-runner.bat install-cli
```

## 7. 部署与运行

### 7.1 环境要求
- Python >= 3.8
- Node.js >= 16
- pnpm
- Electron
- ChromaDB

### 7.2 快速开始
```bash
# 安装依赖
pnpm install

# 启动开发环境
pnpm dev

# 运行测试
pnpm test
```

### 7.3 训练系统使用
```bash
# 使用自动训练系统
training\auto_train.bat
python training\run_auto_training.py

# 使用增量学习系统
training\incremental_train.bat monitor
training\incremental_train.bat train
```

## 8. 代码现状与设计目标对比

### 8.1 架构实现
- ✅ **分层架构**: 已实现"大模型（推理层）+ 行动子模型（操作层）"
- ✅ **闭环架构**: 已实现"感知-决策-行动-回饋"的完整行动闭环
- ✅ **HSP协议**: 已实现高速同步协议，支持内部模块与外部AI协作
- ✅ **记忆管理**: 已实现 HAMMemoryManager、DeepMapper、VectorStore 等核心组件

### 8.2 功能实现
- ✅ **AI代理系统**: 8个专业代理全部完成，BaseAgent作为基础类
- ✅ **训练系统**: 完整实现，支持11种训练场景和增量学习
- ✅ **CLI工具**: 统一命令行界面完成，支持AI交互
- ✅ **桌面应用**: "Angela's World"游戏客户端完成

### 8.3 质量保证
- ✅ **测试覆盖率**: 测试用例收集完成，所有主要错误已修复，测试稳定性优化
- ✅ **集成稳定性**: HSP连接等主要组件集成问题已修复，MQTT连接稳定性已优化
- ✅ **核心功能**: 基础功能测试通过，AlphaDeepModel测试9/9通过，所有专门化代理功能验证通过
- ✅ **代码质量**: 所有导入路径、语法问题和代理结构不一致性已修复，代码结构优化完成
- ✅ **功能验证**: 所有AI代理创建和功能测试通过，包括CreativeWritingAgent和WebSearchAgent的完整实现

### 8.4 AGI等级进展
- **当前状态**: Level 2-3（推理AI到初步自主学习）
- **设计目标**: Level 3-4（胜任到专家级AGI）
- **理论上限**: Level 5（超人类AGI，通过群体智慧）
- **实现进展**: 核心架构完成，训练系统就绪，准备进入Level 3测试阶段

## 9. 未来发展路线

### 9.1 阶段化推进路线图
1. **阶段一 (MVP / Level 3 初步实现)**：在 6-8 周内，完成一个以"桌面宠物精灵+经济系统"为场景的最小可行产品。
2. **阶段二 (封闭测试与迭代)**：在 4 周内，邀请小规模用户进行测试，收集真实世界数据，并根据反馈迭代经济AI模型与桌宠的互动逻辑。
3. **阶段三 (开放测试与生态起步)**：在 8 周内，扩大用户群体，验证经济系统的稳定性与社群驱动的可行性，并开始引入更复杂的多模态感知能力。
4. **阶段四 (挑战 Level 4)**：在系统稳定运行的基础上，引入"自我演化"机制，让 AI 在切断与外部大模型的连接后，仍能从与环境的互动中学习全新知识，并自主修正其核心逻辑。

### 9.2 技术实施重点
- **向量化记忆**：整合 ChromaDB 实现高效语义检索。
- **持续学习框架**：支持模型增量更新与知识保持。
- **多模态整合**：文本、图像、音频的统一处理。
- **自主学习能力**：摆脱对外部 LLM 的完全依赖，实现真正的自我演化。

### 9.3 当前重点任务
- **继续提高测试覆盖率**: 已修复所有主要测试错误，进一步提高测试稳定性
- **优化增量学习**: 改进增量学习效果，为Level 3测试做准备
- **完善文档**: 已更新主要文档，确保与代码现状一致，反映最新的修复和改进
- **准备Level 3测试**: 进行全面的功能验证和性能测试，所有核心功能已验证通过

## 10. 依赖關係總覽

### 10.1 後端（apps/backend/requirements.txt 主要）
- fastapi, uvicorn[standard], pydantic
- aiohttp, requests
- paho-mqtt, gmqtt
- chromadb
- numpy, pandas, PyYAML, psutil
- rich, click, tqdm, msgpack
- 測試：pytest, pytest-asyncio, pytest-cov, pytest-timeout
- 其他：codecarbon

### 10.2 根目錄（requirements.txt）
- tensorflow>=2.0.0
- numpy>=1.18.0
- scikit-learn>=0.22.0

### 10.3 前端與工具（package.json）
- dev：concurrently, cross-env, chokidar, rimraf
- 依賴：dompurify, electron-store, ses

以上依賴請根據實際環境需求選擇性安裝；建議優先在後端環境安裝 `apps/backend/requirements.txt`，再按需安裝根目錄與前端依賴。