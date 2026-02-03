# Unified AI Project - iFlow CLI 上下文文档

## 项目概述

Unified AI Project 是一个综合性的AI系统项目，旨在构建一个完整的AI代理框架，包含多个子系统和组件。该项目采用monorepo架构，整合了后端(Python/FastAPI)、前端仪表板(Next.js/React)和桌面应用(Electron)。

### 项目状态
- **版本**: 1.0.0 已发布
- **AGI等级**: Level 3 (专家级AGI) 达成
- **ASI等级**: Level 1 (基础ASI) 达成
- **企业级成熟度**: 95/100 分
- **代码质量**: A+级标准

### 核心特色
- **多模态处理能力**: 支持视觉、音频、文本等多种数据类型的处理
- **协作式训练系统**: 多个模型之间共享知识、协同训练的机制
- **增量学习机制**: 系统能够在运行过程中持续学习和优化
- **自动训练系统**: 能够自动识别数据、创建配置并执行训练
- **统一系统管理**: 全新的统一系统管理器，整合所有子系统
- **HSP协议**: 高速同步协议支持内部模块与外部AI协作
- **语义级安全**: 基于UID/Key机制的深度数据保护

## 技术栈

### 前端技术
- **桌面应用**: Electron
- **Web仪表板**: Next.js 15, TypeScript 5, Tailwind CSS 4, shadcn/ui
- **共享UI组件**: React, TypeScript

### 后端技术
- **主要语言**: Python 3.8+
- **Web框架**: FastAPI
- **AI框架**: TensorFlow, PyTorch, NumPy, Scikit-learn
- **数据库**: ChromaDB（向量数据库）
- **消息队列**: MQTT

### 工具与构建
- **包管理**: pnpm
- **构建工具**: concurrently, cross-env
- **测试框架**: pytest
- **部署工具**: Electron-builder

## 项目结构

```
Unified-AI-Project/
├── apps/                  # 应用程序目录
│   ├── backend/           # 核心后端服务 (Python/FastAPI)
│   │   ├── src/
│   │   │   ├── agents/    # AI代理系统 (15个专业代理)
│   │   │   ├── ai/        # AI核心组件
│   │   │   ├── core/      # 核心服务系统
│   │   │   ├── api/       # API路由系统
│   │   │   └── services/  # 业务服务系统
│   │   ├── main.py        # 后端主入口点
│   │   └── requirements.txt
│   ├── frontend-dashboard/ # Web仪表板 (Next.js/React)
│   │   ├── src/
│   │   │   ├── app/       # Next.js应用结构
│   │   │   ├── components/ # React组件库
│   │   │   └── lib/       # 工具函数
│   │   └── package.json
│   └── desktop-app/       # 桌面游戏客户端 (Electron)
│       ├── electron_app/
│       └── package.json
├── packages/              # 共享包
│   ├── cli/               # 命令行工具
│   └── ui/                # 共享UI组件
├── training/               # 训练系统
├── tools/                  # 工具脚本
├── scripts/                # 脚本目录
├── docs/                   # 文档目录
├── data/                   # 数据目录
├── tests/                  # 测试目录
├── auto_fix_workspace/     # 自动修复工作区
├── model_cache/           # AI模型缓存
├── context_storage/       # 上下文存储
└── checkpoints/            # 训练检查点
```

## 构建和运行

### 环境要求
- Python >= 3.8
- Node.js >= 16
- pnpm
- 相关依赖包

### 安装依赖

```bash
# 安装所有依赖
pnpm install:all

# 或分别安装
# 安装前端依赖
pnpm install

# 安装后端依赖
cd apps/backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 启动开发环境

```bash
# 启动完整开发环境(后端+前端仪表板)
pnpm dev

# 启动所有开发环境(后端+前端仪表板+桌面应用)
pnpm dev:all

# 分别启动各个服务
pnpm dev:backend     # 启动后端服务
pnpm dev:dashboard   # 启动前端仪表板
pnpm dev:desktop     # 启动桌面应用
```

### 运行测试

```bash
# 运行所有测试
pnpm test

# 运行后端测试
pnpm test:backend

# 运行前端测试
pnpm test:frontend

# 运行桌面应用测试
pnpm test:desktop

# 运行带覆盖率报告的测试
pnpm test:coverage
```

### 构建项目

```bash
# 构建所有包
pnpm build
```

## 开发约定

### 代码风格
- Python: 遵循PEP 8规范
- JavaScript/TypeScript: 使用ESLint配置
- 使用.pre-commit-config.yaml进行代码检查

### 测试实践
- 使用pytest进行Python测试
- 测试文件位于tests/目录
- 支持覆盖率测试：`pnpm test:coverage`

### 项目管理
- 使用Git进行版本控制
- 使用统一管理脚本进行项目管理
- 定期进行健康检查：`pnpm health-check`

## 统一管理脚本

项目提供了统一的管理脚本`unified-ai.bat`，可以通过以下方式访问：

```bash
# 双击执行或在命令行中运行
unified-ai.bat

# 或者
pnpm unified-ai
```

该脚本提供了以下功能：
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
16. Exit - 退出

## 故障排除

### 常见问题

1. **依赖安装问题**:
   - 运行`pnpm install:all`确保所有依赖都已安装
   - 如果仍有问题，可以尝试`pnpm clean`清理后再重新安装

2. **端口冲突**:
   - 使用`pnpm port-info`查看端口使用情况
   - 使用`pnpm port-kill-service`终止占用端口的服务

3. **Git问题**:
   - 使用`pnpm unified-ai`中的Git Management功能进行状态检查和清理
   - 对于严重的Git问题，可以使用Emergency Git Fix功能

4. **测试失败**:
   - 确保所有依赖已正确安装
   - 检查是否存在未解决的语法错误
   - 查看具体的错误信息以定位问题

### 日志和错误报告
- 错误日志通常位于`logs/`目录中
- 测试结果可以在`test_results/`目录中找到
- 系统状态报告在`reports/`目录中

## 联系和支持

- **GitHub**: https://github.com/catcatAI/Unified-AI-Project
- **问题报告**: 在GitHub上创建issue
- **文档**: 查看docs/目录下的详细文档