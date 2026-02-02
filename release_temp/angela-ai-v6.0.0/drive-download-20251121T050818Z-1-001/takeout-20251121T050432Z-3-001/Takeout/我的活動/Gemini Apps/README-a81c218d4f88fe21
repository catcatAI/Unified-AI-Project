# Unified AI Project

Unified AI Project 是一个综合性的AI系统项目，旨在构建一个完整的AI代理框架，包含多个子系统和组件。

## 快速开始

要启动完整的Unified AI Project系统，请执行以下步骤：

1. 确保已安装所有依赖：
   ```bash
   # 安装前端依赖
   pnpm install
   
   # 安装后端依赖
   cd apps/backend
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. 启动完整系统：
   ```bash
   # 在项目根目录下执行
   pnpm dev
   ```

3. 或者分别启动各个服务：
   ```bash
   # 启动后端服务
   pnpm dev:backend
   
   # 启动前端服务
   pnpm dev:dashboard
   ```

4. 访问应用：
   - 前端界面: http://localhost:3000
   - 后端API: http://localhost:8000
   - API文档: http://localhost:8000/docs

## 项目概述

Unified AI Project是一个基于monorepo的混合式AI生态系统，整合了多种AI技术和组件。项目采用多智能体协作设计理念，通过HSP协议实现内部模块与外部AI实体的可信协作。

项目目标是实现Level 3-4的自主学习AGI（人工通用智能），采用"大模型(推理层) + 行动子模型(操作层)"的分层与闭环架构设计。系统具备持续学习能力，能在运行过程中持续学习和优化。

### 核心价值
- **多模态处理能力**：支持视觉、音频、文本等多种数据类型的处理
- **协作式训练系统**：多个模型之间共享知识、协同训练的机制
- **增量学习机制**：系统能够在运行过程中持续学习和优化
- **自动训练系统**：能够自动识别数据、创建配置并执行训练
- **上下文管理**：完整的上下文管理系统，包括工具、模型与代理、对话、记忆等上下文管理
- **HSP协议**：高速同步协议支援内部模块与外部AI协作
- **智能测试与调试**：完善的测试框架和缺陷检测系统

## 项目结构

```
Unified-AI-Project/
├── apps/
│   ├── backend/
│   │   ├── src/
│   │   │   ├── agents/
│   │   │   │   ├── base_agent.py
│   │   │   │   ├── collaboration_demo_agent.py
│   │   │   │   └── ...
│   │   │   ├── ai/
│   │   │   │   ├── memory/
│   │   │   │   │   ├── ham_memory_manager.py
│   │   │   │   │   └── ...
│   │   │   │   ├── dialogue/
│   │   │   │   ├── learning/
│   │   │   │   ├── trust/
│   │   │   │   ├── lm/
│   │   │   │   └── ...
│   │   │   ├── core_services/
│   │   │   │   ├── ham_memory_service.py
│   │   │   │   ├── multi_llm_service.py
│   │   │   │   ├── hsp_connector.py
│   │   │   │   └── ...
│   │   │   ├── managers/
│   │   │   │   ├── agent_collaboration_manager.py
│   │   │   │   ├── agent_monitoring_manager.py
│   │   │   │   ├── dynamic_agent_registry.py
│   │   │   │   └── ...
│   │   │   ├── tools/
│   │   │   │   └── ...
│   │   │   └── core/
│   │   │       └── hsp/
│   │   │           └── bridge/
│   │   │               └── message_bridge.py
│   │   └── scripts/
│   │       ├── training_integration.py
│   │       └── ...
│   ├── frontend-dashboard/
│   │   └── ...
│   └── desktop-app/
│       └── ...
├── packages/
│   ├── cli/
│   │   └── ...
│   └── ui/
│       └── ...
├── training/
│   ├── auto_training_manager.py
│   ├── collaborative_training_manager.py
│   ├── incremental_learning_manager.py
│   ├── data_manager.py
│   ├── train_model.py
│   ├── error_handling_framework.py
│   ├── training_monitor.py
│   ├── resource_manager.py
│   ├── smart_resource_allocator.py
│   ├── optimized_data_scanner.py
│   ├── parallel_optimized_data_scanner.py
│   ├── configs/
│   ├── models/
│   ├── checkpoints/
│   ├── logs/
│   ├── project_completion_report.md
│   ├── integration_test_report.md
│   ├── enhancement_summary.md
│   ├── collaborative_training_implementation_summary.md
│   ├── collaborative_training_completion_report.md
│   ├── incremental_learning_summary.md
│   └── incremental_learning_final_report.md
├── docs/
│   ├── 00-overview/
│   ├── 01-summaries-and-reports/
│   ├── 02-game-design/
│   ├── 03-technical-architecture/
│   ├── 04-advanced-concepts/
│   ├── 05-development/
│   ├── 06-project-management/
│   ├── 09-archive/
│   ├── api/
│   ├── developer-guide/
│   ├── planning/
│   ├── user-guide/
│   └── ...
├── scripts/
├── tools/
├── tool_context_manager.py
├── tool_call_chain_tracker.py
├── coverage_analyzer.py
├── performance_benchmark.py
├── intelligent_test_generator.py
├── automated_defect_detector.py
├── test_*.py
└── *.md
```

## 核心子系统和组件

### 1. AI代理系统
AI代理系统是项目的核心组件之一，负责实现多智能体协作功能。

- **BaseAgent类**：所有专用代理的基类，提供HSP连接、任务处理和生命周期管理功能
- **代理协作管理器**：管理多个AI代理之间的协作关系
- **代理状态监控和健康检查机制**：实时监控代理的运行状态和健康状况
- **动态代理注册和发现功能**：支持代理的动态注册和发现
- **协作演示代理**：展示代理间协作能力的示例实现

### 2. 上下文管理系统
上下文管理系统负责管理AI系统运行过程中的各种上下文信息。

- **工具上下文管理器**：管理工具调用的上下文信息
- **工具调用链追踪机制**：追踪工具调用的完整链路
- **模型与代理上下文管理**：管理模型和代理的上下文信息
- **对话上下文管理**：管理对话过程中的上下文信息
- **记忆上下文管理**：管理记忆相关的上下文信息

### 3. HSP协议实现
HSP（高速同步协议）是项目内部模块与外部AI实体协作的核心协议。

- **消息桥接功能**：实现不同模块之间的消息传递
- **协议转换和适配**：支持不同协议之间的转换和适配
- **HSP连接器**：提供HSP协议的核心连接功能

### 4. 核心服务
项目包含多个核心服务，提供基础功能支持。

- **音频服务**：处理音频数据的输入和输出
- **视觉服务**：处理视觉数据的输入和输出
- **推理引擎**：提供AI推理能力
- **记忆系统**：
  - **HAM记忆系统**：分层抽象记忆管理器，实现信息的压缩、抽象、向量存储和语义检索
  - **记忆服务**：提供记忆管理的核心服务

### 5. 测试和质量保证
项目具备完善的测试和质量保证体系。

- **工具调用链追踪机制**：追踪工具调用的完整链路
- **测试覆盖率分析器**：分析测试的覆盖率
- **性能基准测试器**：进行性能基准测试
- **智能化测试用例生成器**：自动生成测试用例
- **自动化缺陷检测器**：自动检测系统缺陷

### 6. 训练系统
训练系统是项目的重要组成部分，包含三大核心功能。

- **自动训练系统**：
  - 自动识别训练数据
  - 自动建立训练配置
  - 自动执行训练过程
- **协作式训练系统**：
  - 多个模型之间共享知识
  - 协同训练机制
- **增量学习系统**：
  - 系统能够在运行过程中持续学习和优化
  - 支持在线学习和模型更新

## 系统架构模式

### 整体架构
采用 monorepo 架构组织项目，包含三个主要应用程序和多个共享包：
- **后端 (apps/backend)**：Python 实现的核心 AI 后端，包含所有 AI 模型、API 和游戏逻辑
- **前端仪表板 (apps/frontend-dashboard)**：基于 Web 的开发者管理界面
- **桌面应用 (apps/desktop-app)**：基于 Electron 的 "Angela's World" 游戏客户端
- **共享包**：
  - CLI 工具包 (packages/cli)
  - UI 组件库 (packages/ui)

### 关键技术决策
- **分层与闭环架构**：采用"大模型(推理层) + 行动子模型(操作层)"的分层设计
- **统一模态表示**：将多模态数据(文本、音频、图像)压缩映射到统一的符号空间
- **持续学习**：以时间分割的在线学习取代一次性大规模训练
- **低资源部署**：专为资源受限环境(如个人电脑)设计
- **HSP 协议**：高速同步协议支持内部模块与外部 AI 协作
- **语义级安全**：基于 UID/Key 机制的深度数据保护

### 架构模式和设计模式
- **分层架构**：清晰的分层设计，分离推理层和操作层
- **闭环架构**：构建"感知-决策-行动-反馈"的完整行动闭环
- **模块化设计**：通过 monorepo 结构实现模块化开发和管理
- **工厂模式**：用于 AI 代理的创建(BaseAgent 作为所有代理的基础类)
- **策略模式**：用于不同训练场景的实现
- **观察者模式**：用于训练过程的监控和日志记录

## 技术选型

- **前端**：基于 Web 的前端仪表板，使用 React
- **桌面应用**：Electron 框架
- **后端**：Python，使用 TensorFlow、NumPy、scikit-learn 等库
- **数据库**：ChromaDB 实现向量数据库功能
- **构建工具**：pnpm 作为包管理工具
- **并发执行**：使用 concurrently 库
- **环境变量管理**：cross-env 库
- **文件操作**：rimraf 库

## 安装和使用

### 环境要求
- Python 3.7+
- Node.js
- pnpm
- 相关依赖包

### 搭建开发环境
```bash
# 安装 pnpm
npm install -g pnpm

# 安装所有依赖
pnpm install

# 安装 Python 依赖
cd apps/backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 构建、部署和运维

```bash
# 启动开发服务器(后端和前端仪表板)
pnpm dev

# 启动所有开发服务器(后端、前端仪表板和桌面应用)
pnpm dev:all

# 运行所有测试
pnpm test

# 运行带覆盖率报告的测试
pnpm test:coverage

# 构建所有项目
pnpm build

# 清理项目
pnpm clean
```

## 项目文档

项目的完整文档位于 [docs](docs/) 目录中，包含以下主要部分：

### 文档结构
- **[概览](docs/00-overview/)**：项目高层次的愿景、目标和路线图
- **[游戏设计](docs/02-game-design/)**：关于集成游戏组件的详细信息
- **[技术架构](docs/03-technical-architecture/)**：系统架构、通信协议(HSP)、记忆系统(HAM)和AI组件的深入文档
- **[高级概念](docs/04-advanced-concepts/)**：探讨代理协作、元公式和语言免疫系统等高级主题
- **[开发指南](docs/05-development/)**：关于调试、测试和开发工作流程的信息
- **[项目管理](docs/06-project-management/)**：项目规划、状态报告和管理见解
- **[归档文档](docs/09-archive/)**：旧版或已弃用的文档，供历史参考

### 重要技术文档
- [PORT_MANAGEMENT_STRATEGY.md](docs/PORT_MANAGEMENT_STRATEGY.md) - 端口管理策略和实现细节
- [UNIFIED_DOCUMENTATION_INDEX.md](docs/UNIFIED_DOCUMENTATION_INDEX.md) - 统一文档索引
- [03-technical-architecture/agents/README.md](docs/03-technical-architecture/agents/README.md) - AI代理系统概述

### 主要计划文档
- [COMPLETE_CONTEXT_SYSTEM_UPGRADE_PLAN.md](COMPLETE_CONTEXT_SYSTEM_UPGRADE_PLAN.md) - 完整上下文系统升级计划
- [CONTEXT_MANAGER_FRAMEWORK_DESIGN.md](CONTEXT_MANAGER_FRAMEWORK_DESIGN.md) - 上下文管理器框架设计
- [CONTEXT_MANAGER_IMPLEMENTATION_PLAN.md](CONTEXT_MANAGER_IMPLEMENTATION_PLAN.md) - 上下文管理器实现计划
- [EXECUTION_PLAN_AI_AGENT_SYSTEM.md](EXECUTION_PLAN_AI_AGENT_SYSTEM.md) - AI代理系统执行计划
- [EXECUTION_PLAN_ADVANCED_TESTING_DEBUGGING.md](EXECUTION_PLAN_ADVANCED_TESTING_DEBUGGING.md) - 高级测试和调试执行计划
- [EXECUTION_PLAN_SYSTEM_INTEGRATION_TEST.md](EXECUTION_PLAN_SYSTEM_INTEGRATION_TEST.md) - 系统集成测试执行计划
- [EXECUTION_PLAN_TEST_INFRASTRUCTURE.md](EXECUTION_PLAN_TEST_INFRASTRUCTURE.md) - 测试基础设施执行计划
- [SYSTEM_INTEGRATION_TEST_IMPROVEMENT_PLAN.md](SYSTEM_INTEGRATION_TEST_IMPROVEMENT_PLAN.md) - 系统集成测试改进计划
- [UNIFIED_AI_IMPROVEMENT_PLAN.md](UNIFIED_AI_IMPROVEMENT_PLAN.md) - 统一AI改进计划

### 执行总结报告
- [AI_AGENT_SYSTEM_EXECUTION_SUMMARY.md](AI_AGENT_SYSTEM_EXECUTION_SUMMARY.md) - AI代理系统执行总结
- [CONTEXT_SYSTEM_IMPLEMENTATION_SUMMARY.md](CONTEXT_SYSTEM_IMPLEMENTATION_SUMMARY.md) - 上下文系统实现总结
- [PROJECT_CONTEXT_SYSTEM_COMPLETION_REPORT.md](PROJECT_CONTEXT_SYSTEM_COMPLETION_REPORT.md) - 项目上下文系统完成报告
- [SYSTEM_INTEGRATION_TEST_ENHANCEMENT_PLAN.md](SYSTEM_INTEGRATION_TEST_ENHANCEMENT_PLAN.md) - 系统集成测试增强计划

### 训练系统报告
- [collaborative_training_completion_report.md](training/collaborative_training_completion_report.md) - 协作式训练完成报告
- [collaborative_training_implementation_summary.md](training/collaborative_training_implementation_summary.md) - 协作式训练实现总结
- [incremental_learning_final_report.md](training/incremental_learning_final_report.md) - 增量学习最终报告
- [incremental_learning_summary.md](training/incremental_learning_summary.md) - 增量学习总结
- [integration_test_report.md](training/integration_test_report.md) - 集成测试报告
- [project_completion_report.md](training/project_completion_report.md) - 项目完成报告

### 其他重要文档
- [FINAL_PROJECT_SUMMARY.md](FINAL_PROJECT_SUMMARY.md) - 项目最终总结报告
- [PROJECT_STATUS_REPORT.md](PROJECT_STATUS_REPORT.md) - 项目状态报告
- [AUDIO_SERVICE_FIX_REPORT.md](AUDIO_SERVICE_FIX_REPORT.md) - 音频服务修复报告
- [AUTO_FIX_EVALUATION_REPORT.md](AUTO_FIX_EVALUATION_REPORT.md) - 自动修复评估报告

## 项目状态

项目已完成所有计划任务，达到发布标准。系统具备完整的AI代理框架、上下文管理系统、HSP协议实现、核心服务和训练系统。项目文档齐全，测试覆盖率高，具备良好的可维护性和扩展性。

## 许可证

本项目仅供学习和研究使用。

## 联系方式

如有问题，请联系项目维护者。