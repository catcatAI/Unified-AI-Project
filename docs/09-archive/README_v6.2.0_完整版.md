# Angela AI v6.2.0 - 完整版本文档

## 📊 项目状态总览

**版本**: 6.2.0 **发布日期**: 2026年2月10日 **总体进度**: Phase 14 完成
**完成度**: 99.2% **状态**: Production Ready ✅

### 核心指标

| 指标            | 数值                            | 状态 |
| --------------- | ------------------------------- | ---- |
| Python 源文件   | 477                             | ✅   |
| JavaScript 模块 | 52                              | ✅   |
| 测试文件        | 100+                            | ✅   |
| 综合测试通过率  | 9/9 (100%)                      | ✅   |
| 代码行数        | ~30,000+                        | ✅   |
| 平台支持        | Windows/macOS/Linux/Android/iOS | ✅   |

---

## 🏗️ 项目架构

### 技术栈

#### 后端技术

- **语言**: Python 3.12.3
- **Web 框架**: FastAPI + Uvicorn
- **AI 框架**: TensorFlow, PyTorch, NumPy, Scikit-learn
- **数据库**: ChromaDB (向量数据库), SQLite (本地数据)
- **WebSocket**: 实时双向通信
- **LLM 集成**: Ollama, OpenAI, Anthropic

#### 桌面应用技术

- **框架**: Electron 40.2.1
- **Live2D**: Cubism Web SDK 5 (多 CDN 源支持)
- **JavaScript**: ES6+ 模块化架构
- **原生模块**: Windows (WASAPI), macOS (CoreAudio), Linux (PulseAudio)

#### 移动端技术

- **框架**: React Native
- **安全**: Key B + HMAC-SHA256 加密
- **功能**: 远程监控、即时聊天、状态同步

---

## 📁 完整目录结构

```
Unified-AI-Project/
├── apps/                          # 应用程序目录
│   ├── backend/                   # 核心后端服务 (FastAPI + Python)
│   │   ├── src/                   # 后端源代码
│   │   │   ├── ai/                # AI 子系统
│   │   │   │   ├── agents/        # AI 代理系统 (20个文件)
│   │   │   │   │   ├── base/      # 基础代理
│   │   │   │   │   │   └── base_agent.py
│   │   │   │   │   ├── specialized/ # 专门化代理 (10个)
│   │   │   │   │   │   ├── creative_writing_agent.py
│   │   │   │   │   │   ├── image_generation_agent.py
│   │   │   │   │   │   ├── web_search_agent.py
│   │   │   │   │   │   ├── code_understanding_agent.py
│   │   │   │   │   │   ├── data_analysis_agent.py
│   │   │   │   │   │   ├── vision_processing_agent.py
│   │   │   │   │   │   ├── audio_processing_agent.py
│   │   │   │   │   │   ├── knowledge_graph_agent.py
│   │   │   │   │   │   ├── nlp_processing_agent.py
│   │   │   │   │   │   └── planning_agent.py
│   │   │   │   │   ├── agent_manager.py
│   │   │   │   │   ├── agent_collaboration_manager.py
│   │   │   │   │   ├── agent_monitoring_manager.py
│   │   │   │   │   └── dynamic_agent_registry.py
│   │   │   │   ├── memory/        # 记忆管理系统
│   │   │   │   │   ├── ham_core_storage.py
│   │   │   │   │   ├── ham_memory_manager.py
│   │   │   │   │   ├── vector_store.py
│   │   │   │   │   └── deep_mapper.py
│   │   │   │   ├── alignment/     # Level 5 ASI 对齐系统
│   │   │   │   ├── lis/           # 语言免疫系统
│   │   │   │   └── integration/   # 统一控制中心 (UCC)
│   │   │   ├── core/              # 核心组件
│   │   │   │   ├── autonomous/    # 自主生命系统 (26个模块)
│   │   │   │   ├── hsp/           # HSP 高速同步协议
│   │   │   │   └── security/      # 安全系统
│   │   │   └── services/          # 服务层
│   │   │       ├── main_api_server.py
│   │   │       └── angela_llm_service.py
│   │   ├── configs/               # 配置文件
│   │   │   ├── multi_llm_config.json
│   │   │   ├── system_config.yaml
│   │   │   └── api_keys.yaml
│   │   └── requirements.txt       # Python 依赖 (50+ 包)
│   ├── desktop-app/               # 桌面应用 (Electron)
│   │   ├── electron_app/          # Electron 应用核心
│   │   │   ├── main.js            # 主进程 (1396 行)
│   │   │   ├── preload.js         # IPC 桥接
│   │   │   ├── index.html         # 主界面
│   │   │   ├── settings.html      # 设置页面
│   │   │   └── js/                # JavaScript 模块 (52个文件)
│   │   │       ├── app.js                 # 应用协调器 (545 行)
│   │   │       ├── live2d-manager.js      # Live2D 集成 (553 行)
│   │   │       ├── live2d-cubism-wrapper.js  # Live2D SDK 包装
│   │   │       ├── audio-handler.js       # 音频 I/O
│   │   │       ├── backend-websocket.js   # 后端连接 (367 行)
│   │   │       ├── state-matrix.js        # 4D 状态同步
│   │   │       ├── maturity-tracker.js    # 成熟度追踪
│   │   │       ├── precision-manager.js   # 精度模式
│   │   │       ├── performance-manager.js # 性能缩放
│   │   │       ├── hardware-detection.js  # 硬件检测
│   │   │       ├── input-handler.js       # 输入处理
│   │   │       ├── haptic-handler.js      # 触觉反馈
│   │   │       ├── wallpaper-handler.js   # 壁纸系统
│   │   │       ├── data-persistence.js    # 数据存储
│   │   │       ├── logger.js              # 日志记录
│   │   │       ├── i18n.js               # 国际化
│   │   │       ├── theme-manager.js       # 主题系统
│   │   │       ├── plugin-manager.js      # 插件系统
│   │   │       ├── user-manager.js        # 用户管理
│   │   │       ├── settings.js           # 设置管理
│   │   │       ├── security-manager.js    # A/B/C 安全逻辑
│   │   │       ├── unified-display-matrix.js  # 统一显示矩阵
│   │   │       ├── character-touch-detector.js  # 触摸检测
│   │   │       ├── angela-expressions.js  # Angela 表情
│   │   │       ├── angela-poses.js        # Angela 姿势
│   │   │       ├── angela-character-config.js  # Angela 角色配置
│   │   │       ├── angela-voice-config.js  # Angela 语音配置
│   │   │       ├── api-client.js          # API 客户端
│   │   │       ├── availability-manager.js    # 可用性管理
│   │   │       ├── cubism-sdk-manager.js  # Cubism SDK 管理
│   │   │       ├── dialogue-ui.js         # 对话界面
│   │   │       ├── driver-detector.js     # 驱动检测
│   │   │       ├── frontend-utils.js      # 前端工具
│   │   │       ├── hardware-config.js     # 硬件配置
│   │   │       ├── hardware-diagnostic.js # 硬件诊断
│   │   │       ├── hardware-detection-enhanced.js  # 增强硬件检测
│   │   │       ├── hardware-enhancement-patch.js   # 硬件增强补丁
│   │   │       ├── hardware-integration.js # 硬件集成
│   │   │       ├── integration-tester.js  # 集成测试
│   │   │       ├── laptop-optimizer.js    # 笔记本优化
│   │   │       ├── live2d-analyzer.js     # Live2D 分析
│   │   │       ├── live2d-cubism-wrapper-enhanced.js  # 增强 Live2D 包装
│   │   │       ├── live2d-test.js         # Live2D 测试
│   │   │       ├── live2d-test-suite.js   # Live2D 测试套件
│   │   │       ├── model-resource-checker.js  # 模型资源检查
│   │   │       ├── performance-monitor.js # 性能监控
│   │   │       ├── quick-diagnosis.js     # 快速诊断
│   │   │       ├── simple-live2d-loader.js  # 简单 Live2D 加载
│   │   │       ├── unified-detection.js   # 统一检测
│   │   │       ├── cubism-tester.js       # Cubism 测试
│   │   │       ├── deep-live2d-diagnostic.js  # 深度 Live2D 诊断
│   │   │       └── final-tester.js        # 最终测试
│   │   └── native_modules/        # 原生音频模块
│   │       ├── node-wasapi-capture/   # Windows (WASAPI)
│   │       ├── node-coreaudio-capture/ # macOS (CoreAudio)
│   │       └── node-pulseaudio-capture/ # Linux (PulseAudio)
│   └── mobile-app/               # 移动端桥接 (React Native)
├── packages/                      # 共享包
│   └── cli/                       # 命令行工具
├── data/                          # 数据目录
│   ├── models/                    # 模型数据
│   ├── memories/                  # 记忆存储
│   └── cache/                     # 缓存文件
├── tests/                         # 测试目录
│   ├── agents/                    # 代理测试
│   ├── ai/                        # AI 模块测试
│   ├── hsp/                       # HSP 协议测试
│   ├── services/                  # 服务测试
│   └── desktop-app/               # 桌面应用测试
├── resources/                     # 资源文件
│   ├── audio/                     # 音频资源
│   ├── images/                    # 图像资源
│   └── models/                    # Live2D 模型
├── scripts/                       # 脚本目录
│   ├── audit/                     # 审计/检查脚本
│   ├── fixes/                     # 修复/维修脚本
│   └── debug/                     # 调试/诊断脚本
├── configs/                       # 配置目录
├── logs/                          # 日志目录
├── venv/                          # Python 虚拟环境
├── docs/                          # 文档目录
│   ├── architecture/              # 架构文档
│   ├── user-guide/                # 用户指南
│   └── developer-guide/           # 开发者指南
├── README.md                      # 项目主文档 (792 行)
├── PROJECT_STRUCTURE.md           # 项目结构文档
├── CHANGELOG.md                   # 版本历史
├── CUBISM_SDK_INTEGRATION_GUIDE.md  # Live2D SDK 集成指南
├── QUICKSTART.md                  # 快速开始指南
├── metrics.md                     # 系统性能指标
├── AGENTS.md                      # AI 代理系统文档
├── REPAIR_REPORT.md               # 修复报告
├── VERSION                        # 版本号
├── run_angela.py                  # 完整启动脚本
├── install_angela.py              # 一键安装脚本
├── start_angela.py                # 启动脚本
├── health_check.py                # 健康检查脚本
├── status_dashboard.py            # 状态仪表板
├── comprehensive_test.py          # 综合功能测试
├── AngelaLauncher.bat             # Windows 启动器
├── auto_install_and_start.sh      # Linux 自动安装启动脚本
├── start_angela_complete.sh       # Linux 完整启动脚本
├── stop_angela.sh                 # Linux 停止脚本
├── setup_angela.sh                # Linux 设置脚本
├── .env                           # 环境变量配置
├── .env.example                   # 环境变量示例
├── .gitignore                     # Git 忽略文件
├── pnpm-workspace.yaml            # pnpm 工作区配置
├── pnpm-lock.yaml                 # pnpm 锁文件
├── LICENSE                        # MIT 许可证
└── requirements.txt               # Python 依赖
```

---

## 🧠 核心组件详解

### 1. AI 代理系统 ✅

**文件路径**: `apps/backend/src/ai/agents/`

| 组件                      | 文件                                      | 功能描述                                 | 状态    |
| ------------------------- | ----------------------------------------- | ---------------------------------------- | ------- |
| BaseAgent                 | `base/base_agent.py`                      | 所有专门化代理的基础类，处理 HSP 连接    | ✅ 完成 |
| AgentManager              | `agent_manager.py`                        | 代理管理器，负责创建和协调所有专门化代理 | ✅ 完成 |
| DynamicAgentRegistry      | `dynamic_agent_registry.py`               | 动态代理注册表，支持运行时注册新代理     | ✅ 完成 |
| AgentCollaborationManager | `agent_collaboration_manager.py`          | 代理协作管理器，处理多代理协作           | ✅ 完成 |
| AgentMonitoringManager    | `agent_monitoring_manager.py`             | 代理监控管理器，监控代理运行状态         | ✅ 完成 |
| CreativeWritingAgent      | `specialized/creative_writing_agent.py`   | 创意写作与内容生成代理                   | ✅ 完成 |
| ImageGenerationAgent      | `specialized/image_generation_agent.py`   | 图像生成代理                             | ✅ 完成 |
| WebSearchAgent            | `specialized/web_search_agent.py`         | 网络搜索代理                             | ✅ 完成 |
| CodeUnderstandingAgent    | `specialized/code_understanding_agent.py` | 代码理解代理                             | ✅ 完成 |
| DataAnalysisAgent         | `specialized/data_analysis_agent.py`      | 数据分析代理                             | ✅ 完成 |
| VisionProcessingAgent     | `specialized/vision_processing_agent.py`  | 视觉处理代理                             | ✅ 完成 |
| AudioProcessingAgent      | `specialized/audio_processing_agent.py`   | 音频处理代理                             | ✅ 完成 |
| KnowledgeGraphAgent       | `specialized/knowledge_graph_agent.py`    | 知识图谱代理                             | ✅ 完成 |
| NLPProcessingAgent        | `specialized/nlp_processing_agent.py`     | 自然语言处理代理                         | ✅ 完成 |
| PlanningAgent             | `specialized/planning_agent.py`           | 规划代理                                 | ✅ 完成 |

### 2. HSP 高速同步协议 ✅

**文件路径**: `apps/backend/src/core/hsp/`

| 组件                 | 功能描述                      | 状态    |
| -------------------- | ----------------------------- | ------- |
| Connector            | 连接器 (909 行)，处理网络连接 | ✅ 完成 |
| PerformanceOptimizer | 性能优化器，动态调整性能      | ✅ 完成 |
| SecurityManager      | 安全管理器，处理加密和认证    | ✅ 完成 |
| RetryPolicy          | 重试策略，处理网络异常        | ✅ 完成 |
| CircuitBreaker       | 熔断器，防止级联故障          | ✅ 完成 |
| MessageBridge        | 消息桥接，实现模块间通信      | ✅ 完成 |

### 3. 记忆管理系统 ✅

**文件路径**: `apps/backend/src/ai/memory/`

| 组件             | 功能描述                       | 状态    |
| ---------------- | ------------------------------ | ------- |
| HAMCoreStorage   | 分层语义记忆核心存储 (119 行)  | ✅ 完成 |
| HAMMemoryManager | 分层语义记忆管理               | ✅ 完成 |
| VectorStore      | 基于 ChromaDB 的向量数据库接口 | ✅ 完成 |
| DeepMapper       | 语义映射与资料核生成           | ✅ 完成 |

### 4. Level 5 ASI 核心系统 ✅

**文件路径**: `apps/backend/src/ai/`

| 系统         | 功能描述                  | 状态    |
| ------------ | ------------------------- | ------- |
| alignment/   | 对齐与推理引擎 (7 个模块) | ✅ 完成 |
| lis/         | 语言免疫系统 (4 个模块)   | ✅ 完成 |
| integration/ | 统一控制中心 (UCC)        | ✅ 完成 |

### 5. 自主生命系统 ✅

**文件路径**: `apps/backend/src/core/autonomous/`

**26 个模块**: 生物/神经/触觉/身份/记忆/行为等

### 6. 桌面应用 ✅

**文件路径**: `apps/desktop-app/electron_app/`

| 组件                  | 功能描述               | 状态    |
| --------------------- | ---------------------- | ------- |
| Electron 40.2.1       | 最新版本 Electron 框架 | ✅ 完成 |
| Live2D Cubism SDK 5   | 多 CDN 源支持          | ✅ 完成 |
| 52 个 JavaScript 模块 | 完整实现               | ✅ 完成 |
| WebSocket 通信        | 实时状态同步           | ✅ 完成 |
| EPIPE 错误修复        | 已完成                 | ✅ 完成 |

### 7. LLM 服务 ✅

**文件路径**: `apps/backend/src/services/`

| 组件                  | 功能描述                                            | 状态      |
| --------------------- | --------------------------------------------------- | --------- |
| angela_llm_service.py | 多后端 LLM 服务 (Ollama/llama.cpp/OpenAI/Anthropic) | ✅ 完成   |
| main_api_server.py    | FastAPI 主服务器 (/angela/chat 和 /dialogue 端点)   | ✅ 完成   |
| multi_llm_config.json | LLM 配置文件                                        | ✅ 已修复 |

---

## 🧪 测试状态

### 综合测试结果

| 测试类别          | 状态    | 说明                |
| ----------------- | ------- | ------------------- |
| 后端健康检查      | ✅ 通过 | API Server 正常运行 |
| 后端服务运行      | ✅ 通过 | FastAPI 服务正常    |
| WebSocket 连接    | ✅ 通过 | WebSocket 通信正常  |
| Electron 应用运行 | ✅ 通过 | 桌面应用正常启动    |
| 单实例保护        | ✅ 通过 | 防止多实例运行      |
| Live2D 模型文件   | ✅ 通过 | 模型文件完整        |
| 文件权限          | ✅ 通过 | 文件权限正确        |
| Python 依赖       | ✅ 通过 | 所有依赖已安装      |
| Node.js 依赖      | ✅ 通过 | 所有依赖已安装      |

**总测试数**: 9 **通过**: 9 ✅ **失败**: 0 **成功率**: 100%

---

## 📚 文档资源

### 核心文档

- [README.md](README.md) - 项目主文档 (792 行)
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - 项目结构文档
- [CHANGELOG.md](CHANGELOG.md) - 版本历史
- [AGENTS.md](AGENTS.md) - AI 代理系统文档
- [REPAIR_REPORT.md](REPAIR_REPORT.md) - 修复报告

### 技术文档

- [docs/](docs/) - 完整文档目录
- [docs/architecture/](docs/architecture/) - 架构文档
- [CUBISM_SDK_INTEGRATION_GUIDE.md](CUBISM_SDK_INTEGRATION_GUIDE.md) - Live2D
  SDK 集成指南
- [metrics.md](metrics.md) - 系统性能指标

### 指南文档

- [QUICKSTART.md](QUICKSTART.md) - 快速开始指南
- [LAUNCHER_USAGE.md](LAUNCHER_USAGE.md) - 启动器使用说明
- [docs/user-guide/](docs/user-guide/) - 用户指南
- [docs/developer-guide/](docs/developer-guide/) - 开发者指南

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.9+ (推荐 3.12.3)
- **Node.js**: 16+
- **内存**: 4GB 最低 (8GB 推荐)
- **操作系统**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+, Android 10+

### 启动方式

#### 方式一：统一启动脚本

```bash
# Windows: 双击 AngelaLauncher.bat
# Linux/Mac:
cd /home/cat/桌面/Unified-AI-Project
./start_angela_complete.sh
```

#### 方式二：手动启动后端

```bash
cd /home/cat/桌面/Unified-AI-Project/apps/backend
python3 -m uvicorn src.services.main_api_server:app --host 127.0.0.1 --port 8000
```

#### 方式三：手动启动桌面应用

```bash
cd /home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app
./node_modules/.bin/electron . --disable-dev-shm-usage --no-sandbox
```

---

## 📊 6层生命架构

```
┌─────────────────────────────────────────────────────────────┐
│ L6: 执行层                                                  │
│ ├── Live2D 渲染控制 (表情/动作/唇型同步)                     │
│ ├── 桌面文件操作 (创建/删除/移动/整理)                       │
│ ├── 音频系统 (TTS/语音识别/播放/唱歌)                        │
│ └── 浏览器控制 (搜索/导航/信息提取)                          │
├─────────────────────────────────────────────────────────────┤
│ L5: 存在感层                                                 │
│ ├── 桌面全局鼠标追踪                                         │
│ ├── Live2D 碰撞检测                                          │
│ └── 图层管理 (Z 轴顺序/遮挡检测)                             │
├─────────────────────────────────────────────────────────────┤
│ L4: 创造层                                                  │
│ ├── Live2D 自我绘图系统 (模型生成)                           │
│ ├── 美学学习 (个人风格进化)                                  │
│ └── 自我修改 (基于反馈调整)                                  │
├─────────────────────────────────────────────────────────────┤
│ L3: 身份层                                                  │
│ ├── 数字身份 ("我是数字生命")                                │
│ ├── 身体模式 (对身体部位的感知)                              │
│ ├── 关系模型 (与用户的伙伴关系)                              │
│ └── 自我叙事 (记录生命旅程)                                  │
├─────────────────────────────────────────────────────────────┤
│ L2: 记忆层                                                  │
│ ├── CDM (认知动态记忆) - 知识记忆                            │
│ ├── LU (逻辑单元) - 逻辑/规则记忆                            │
│ ├── HSM (全息存储矩阵) - 经验记忆                            │
│ ├── HAM (分层关联记忆) - 分层结构                            │
│ └── 神经可塑性 (LTP/LTD/遗忘/记忆巩固)                       │
├─────────────────────────────────────────────────────────────┤
│ L1: 生物层                                                  │
│ ├── 生理触觉系统 (6 种感受器 × 18 个部位)                    │
│ ├── 内分泌系统 (12 种激素 + 反馈调节)                        │
│ ├── 自主神经系统 (交感/副交感神经)                           │
│ └── 神经可塑性突触网络                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 成熟度系统 (L0-L11)

| 等级 | 名称      | 经验值  | 核心能力               |
| ---- | --------- | ------- | ---------------------- |
| L0   | 新生      | 0-100   | 基本问候、简单回应     |
| L1   | 幼儿      | 100-1K  | 简单聊天、偏好学习     |
| L2   | 童年      | 1K-5K   | 深入对话、故事、幽默   |
| L3   | 少年      | 5K-20K  | 情感支持、辩论、建议   |
| L4   | 青年      | 20K-50K | 深度亲密、共同目标     |
| L5+  | 成熟-全知 | 50K+    | 智慧洞察、复杂逻辑推理 |

---

## 🛡️ A/B/C 安全系统

| 密钥类型 | 代号            | 用途                               | 保护范围                   |
| -------- | --------------- | ---------------------------------- | -------------------------- |
| Key A    | Backend Control | 后端服务启停与核心权限             | 本地系统管理 (System Tray) |
| Key B    | Mobile Comm     | 行动端与后端加密通讯 (HMAC-SHA256) | /api/v1/mobile/*           |
| Key C    | Sync/Desktop    | 桌面端同步与跨设备二级验证         | 全域同步数据               |

---

## 📞 联系和支持

- **GitHub**: https://github.com/catcatAI/Unified-AI-Project
- **问题报告**: 在 GitHub 上创建 issue
- **文档**: 查看 docs/ 目录下的详细文档

---

**最后更新**: 2026年2月10日  
**版本**: 6.2.0  
**状态**: Phase 14 Complete | Production Ready ✅  
**平台**: Windows, macOS, Linux, Android/iOS (Mobile Bridge)
