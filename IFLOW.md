# Unified AI Project - iFlow CLI 上下文文档

## 项目概述

Unified AI Project 是一个面向 AGI（Level 3-4）的混合式 AI 生态系统，采用 monorepo 架构。项目的核心设计理念是"数据生命"（Data Life），通过持续认知循环实现真正的 AI 自主学习与进化。

### 项目状态
- **版本**: 1.0.0 已发布
- **总体进度**: 100% 完成 (275/275 任务)
- **核心功能**: 全部实现并通过测试
- **AGI 等级**: 当前 Level 2-3，目标 Level 3-4
- **测试状态**: 测试用例收集完成，所有主要错误已修复，测试稳定性优化
- **代码质量**: 核心架构稳定，所有导入路径、语法问题和代理结构不一致性已修复
- **核心功能验证**: 所有AI代理创建和功能测试通过，包括专门化代理的完整功能验证

### 核心特色
- **分层与闭环架构**: 采用"大模型（推理层）+ 行动子模型（操作层）"的分层设计，构建"感知-决策-行动-回饋"的完整行动闭环
- **统一模态表示**: 将多模态数据压缩映射到统一的符号空间，降低跨模态处理的复杂度
- **持续学习**: 以时间分割的在线学习取代一次性大规模训练，让模型能够在使用过程中持续进化
- **低资源部署**: 专为资源受限环境（如个人电脑）设计，通过轻量化模型与高效架构实现高阶 AGI 能力
- **HSP 协议**: 高速同步协议支持内部模块与外部 AI 协作，包含注册机制、信誉系统和热更新功能
- **语义级安全**: 基于 UID/Key 机制的深度资料保护，确保数据安全性

## 项目结构

### 主要目录结构
```
Unified-AI-Project/
├── apps/                  # 应用程序目录
│   ├── backend/           # 核心后端服务 (Python/FastAPI)
│   ├── desktop-app/       # 桌面游戏客户端 (Electron)
│   └── frontend-dashboard/ # Web 仪表板 (Next.js)
├── packages/              # 共享包
│   ├── cli/               # 命令行工具
│   └── ui/                # 共享 UI 组件
├── training/              # 训练系统
├── tools/                 # 工具脚本
├── scripts/               # 脚本目录
├── docs/                  # 文档目录
├── data/                  # 数据目录
├── tests/                 # 测试目录
└── venv/                  # Python 虚拟环境
```

### 核心组件

#### AI 代理系统 (`apps/backend/src/ai/agents/`)
- **BaseAgent**: 所有专门化代理的基础类，处理 HSP 连接与任务分发
- **CreativeWritingAgent**: 创意写作与内容生成代理
- **ImageGenerationAgent**: 图像生成代理
- **WebSearchAgent**: 网络搜索代理
- **CodeUnderstandingAgent**: 代码理解代理
- **DataAnalysisAgent**: 数据分析代理
- **VisionProcessingAgent**: 视觉处理代理
- **AudioProcessingAgent**: 音频处理代理
- **KnowledgeGraphAgent**: 知识图谱代理
- **NLPProcessingAgent**: 自然语言处理代理
- **PlanningAgent**: 规划代理

**实现状态**: ✅ 全部完成，所有代理导入和创建测试通过，功能验证成功

#### HSP 高速同步协议 (`apps/backend/src/core/hsp/`)
- 注册机制：新模块/AI 加入网络
- 信誉系统：评估协作实体可信度
- 热更新：动态载入新功能模块
- 消息桥接：实现不同模块间的消息传递
- 协议转换：支持不同协议间的转换和适配

**实现状态**: ✅ 核心功能完成，MQTT连接稳定性已优化

#### 记忆管理系统 (`apps/backend/src/core/memory/`)
- **DeepMapper**: 语义映射与资料核生成
- **HAMMemoryManager**: 分层语义记忆管理
- **VectorStore**: 基于 ChromaDB 的向量数据库接口

**实现状态**: ✅ 全部完成，测试通过

#### 概念模型 (`apps/backend/src/ai/concept_models/`)
- **EnvironmentSimulator**: 环境模拟器，实现状态预测、动作效果模型和不确定性估计
- **CausalReasoningEngine**: 因果推理引擎，实现因果图、干预规划器和反事实推理
- **AdaptiveLearningController**: 自适应学习控制器，实现性能跟踪、策略选择和参数优化
- **AlphaDeepModel**: Alpha 深度模型，实现数据压缩和学习机制
- **UnifiedSymbolicSpace**: 统一符号空间，实现符号管理和关系管理

**实现状态**: ✅ 全部完成，AlphaDeepModel测试9/9通过

## 技术栈

### 前端技术
- **桌面应用**: Electron
- **Web 仪表板**: Next.js 15, TypeScript 5, Tailwind CSS 4, shadcn/ui
- **共享 UI 组件**: React, TypeScript

### 后端技术
- **主要语言**: Python 3.8+
- **Web 框架**: FastAPI
- **AI 框架**: TensorFlow, PyTorch, NumPy, Scikit-learn
- **数据库**: ChromaDB（向量数据库）
- **消息队列**: MQTT

### 工具与构建
- **包管理**: pnpm
- **构建工具**: concurrently, cross-env
- **测试框架**: pytest
- **部署工具**: Electron-builder

## 构建和运行

### 环境要求
- Python >= 3.8
- Node.js >= 16
- pnpm
- Electron
- ChromaDB

### 快速开始

#### 使用统一管理脚本（推荐）
```bash
# 1. 设置环境
double-click unified-ai.bat -> 选择 "Setup Environment"

# 2. 启动开发环境
double-click unified-ai.bat -> 选择 "Start Development" -> "Start Full Development Environment"
```

#### 使用传统命令
```bash
# 1. 安装 pnpm
npm install -g pnpm

# 2. 安装依赖
pnpm install

# 3. 启动开发服务器
pnpm dev
```

### 可用脚本

#### 根目录脚本 (package.json)
```bash
# 安装所有依赖
pnpm install:all

# 启动特定服务
pnpm dev:dashboard    # 前端仪表板
pnpm dev:backend      # 后端服务
pnpm dev:desktop      # 桌面应用
pnpm dev              # 后端 + 前端
pnpm dev:all          # 后端 + 前端 + 桌面

# 运行测试
pnpm test             # 所有测试
pnpm test:backend     # 后端测试
pnpm test:frontend    # 前端测试
pnpm test:desktop     # 桌面应用测试
pnpm test:coverage    # 测试覆盖率

# 其他
pnpm build            # 构建所有包
pnpm clean            # 清理 node_modules
pnpm health-check     # 健康检查
```

#### 统一管理脚本 (unified-ai.bat)
```bash
# 双击 unified-ai.bat 可访问以下功能：
1. Health Check - 检查开发环境
2. Setup Environment - 安装依赖和设置
3. Start Development - 启动开发服务器
4. Run Tests - 执行测试套件
5. Git Management - Git状态和清理
6. Training Setup - 准备AI训练
7. Training Manager - 管理训练数据和过程
8. CLI Tools - 访问Unified AI CLI工具
9. Model Management - 管理AI模型和DNA链
10. Data Analysis - 分析项目数据和统计
11. Data Pipeline - 运行自动化数据处理流水线
12. Emergency Git Fix - 从Git问题中恢复
13. Fix Dependencies - 解决依赖问题
14. System Information - 显示系统信息
15. Unified Auto Fix - 增强自动修复系统
```

## 训练系统

### 训练场景预设
项目提供多种训练配置文件以满足不同需求：

1. **快速开始**: 使用模拟数据快速训练测试
2. **全面训练**: 使用所有可用数据完整训练
3. **完整数据集训练**: 使用完整数据集进行长期训练
4. **视觉专注**: 专注训练视觉相关模型
5. **音频专注**: 专注训练音频相关模型
6. **数学模型训练**: 专门训练数学计算模型
7. **逻辑模型训练**: 专门训练逻辑推理模型
8. **概念模型训练**: 训练所有概念模型
9. **协作式训练**: 多模型协作训练
10. **代码模型训练**: 训练代码理解和生成模型
11. **数据分析模型训练**: 训练数据分析和处理模型

### 自动训练系统
```bash
# 使用批处理脚本
training\auto_train.bat

# 或使用Python命令
python training\run_auto_training.py

# 或在主训练脚本中启用自动模式
python training\train_model.py --auto
```

### 增量学习系统
```bash
# 启动数据监控
training\incremental_train.bat monitor

# 触发增量训练
training\incremental_train.bat train

# 查看系统状态
training\incremental_train.bat status

# 清理旧模型版本
training\incremental_train.bat cleanup --keep 3
```

## CLI 工具

### CLI 工具组件
1. **Unified CLI** - 通用AI交互工具
2. **AI Models CLI** - AI模型管理与交互工具
3. **HSP CLI** - 超结构协议工具

### 使用方法
```bash
# 使用统一管理脚本
double-click unified-ai.bat -> 选择 "CLI Tools"

# 使用CLI运行器
tools\cli-runner.bat
tools\cli-runner.bat unified-cli health
tools\cli-runner.bat ai-models-cli list
tools\cli-runner.bat hsp-cli query "Hello"

# 安装为系统命令
tools\cli-runner.bat install-cli
# 安装后可直接使用
unified-ai health
unified-ai chat "Hello"
```

## 开发约定

### 代码风格
- Python: 遵循 PEP 8 规范
- JavaScript/TypeScript: 使用 ESLint 配置
- 使用 .pre-commit-config.yaml 进行代码检查

### 测试实践
- 使用 pytest 进行 Python 测试
- 测试文件位于 tests/ 目录
- 支持覆盖率测试：`pnpm test:coverage`

### 项目管理
- 使用 Git 进行版本控制
- 使用 unified-ai.bat 进行统一管理
- 定期进行健康检查：`pnpm health-check`

## 代码现状与设计目标对比

### 架构实现
- ✅ **分层架构**: 已实现"大模型（推理层）+ 行动子模型（操作层）"
- ✅ **闭环架构**: 已实现"感知-决策-行动-回饋"的完整行动闭环
- ✅ **HSP协议**: 已实现高速同步协议，支持内部模块与外部AI协作
- ✅ **记忆管理**: 已实现HAMMemoryManager和DeepMapper等核心组件

### 功能实现
- ✅ **AI代理系统**: 11个专业代理全部完成，BaseAgent作为基础类
- ✅ **训练系统**: 完整实现，支持11种训练场景和增量学习
- ✅ **CLI工具**: 统一命令行界面完成，支持AI交互
- ✅ **桌面应用**: "Angela's World"游戏客户端完成

### 质量保证
- ✅ **测试覆盖率**: 测试用例收集完成，所有主要错误已修复，测试稳定性优化
- ✅ **集成稳定性**: HSP连接等主要组件集成问题已修复，MQTT连接稳定性已优化
- ✅ **核心功能**: 基础功能测试通过，AlphaDeepModel测试9/9通过，所有专门化代理功能验证通过
- ✅ **代码质量**: 所有导入路径、语法问题和代理结构不一致性已修复，代码结构优化完成
- ✅ **功能验证**: 所有AI代理创建和功能测试通过，包括CreativeWritingAgent和WebSearchAgent的完整实现

### AGI等级进展
- **当前状态**: Level 2-3（推理AI到初步自主学习）
- **设计目标**: Level 3-4（胜任到专家级AGI）
- **理论上限**: Level 5（超人类AGI，通过群体智慧）
- **实现进展**: 核心架构完成，训练系统就绪，准备进入Level 3测试阶段

## 常见问题

### 环境设置问题
- 使用 `unified-ai.bat` -> "Setup Environment" 自动设置
- 或手动运行：`pnpm install:all`

### Git 问题
- 使用 `unified-ai.bat` -> "Git Management" 解决
- 特别支持 Git 10K+ 文件问题修复

### 依赖问题
- 使用 `unified-ai.bat` -> "Fix Dependencies" 解决
- 或手动清理：`pnpm clean` -> `pnpm install`

### 测试问题
- **HSP连接失败**: 已修复HSP连接问题，相关测试现在通过，MQTT连接稳定性已优化
- **导入路径错误**: 已修复所有路径问题，包括专门化代理的导入路径、WebSearchAgent结构问题和测试文件中的导入路径
- **语法错误**: 已修复测试文件中的缩进和async/await语法错误，包括test_creative_writing_agent.py中的方法缩进问题
- **代理结构不一致**: 已完全重写WebSearchAgent以匹配标准代理结构，修复CreativeWritingAgent的占位符内容问题
- **配置文件缺失**: 已创建必要的配置文件，如multi_llm_config.json，确保所有代理都有正确的配置支持
- **测试稳定性**: 优化了测试的稳定性，修复了异步测试中的潜在竞态条件问题

## 文档资源

### 核心文档
- [README.md](README.md) - 项目主文档
- [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) - 项目全貌文档
- [CHANGELOG.md](CHANGELOG.md) - 版本历史

### 技术文档
- [docs/](docs/) - 完整文档目录
- [docs/api/](docs/api/) - API 文档
- [docs/architecture/](docs/architecture/) - 架构文档

### 指南文档
- [docs/user-guide/](docs/user-guide/) - 用户指南
- [docs/developer-guide/](docs/developer-guide/) - 开发者指南
- [docs/planning/](docs/planning/) - 项目规划

## 联系和支持

- **GitHub**: https://github.com/catcatAI/Unified-AI-Project
- **问题报告**: 在 GitHub 上创建 issue
- **文档**: 查看 docs/ 目录下的详细文档

---

**最后更新**: 2025年9月22日  
**项目状态**: 1.0.0 正式版发布  
**代码现状**: 核心架构完成，所有导入路径、语法问题和代理结构不一致性已修复，核心功能验证通过，测试稳定性优化  
**目标里程碑**: Level 3 AGI 实现  
**下一步重点**: 继续优化测试覆盖率，完善文档，准备Level 3测试，进一步优化AI代理的协作效率