# Unified-AI-Project 文档中心

欢迎来到 Unified-AI-Project 的主文档中心。本目录为所有参与者提供清晰、结构化的项目信息入口。

## 📚 文档导航

### 🚀 快速开始
- **[项目概述](../README.md)** - 项目简介和快速开始指南
- **[项目章程](./PROJECT_CHARTER.md)** - 完整的项目架构和组件说明
- **[术语表](./GLOSSARY.md)** - 关键术语和概念定义
- **[路线图](./ROADMAP.md)** - 项目发展规划

### 🎮 游戏设计
- **[游戏概述](./game/README.md)** - Angela's World 游戏设计总览
- **[角色设计](./game/character_design.md)** - 游戏角色设定和背景
- **[Angela 角色设计](./game/character_design_angela.md)** - 核心 AI 角色 Angela 的详细设计
- **[游戏系统](./game/game_systems.md)** - 游戏机制和系统设计
- **[地图设计](./game/map_design.md)** - 游戏世界和场景设计

### 🏗️ 技术架构
- **[架构概览](./technical_design/ARCHITECTURE_OVERVIEW.md)** - 系统整体架构和组件说明
- **[HSP 快速入门](./technical_design/HSP_QUICK_START.md)** - HSP 协议快速入门指南
- **[HSP 规范](./technical_design/HSP_SPECIFICATION.md)** - 异构服务协议详细规范
- **[HAM 设计](./technical_design/architecture/HAM_design_spec.md)** - 分层抽象记忆系统
- **[Fragmenta 设计](./technical_design/architecture/Fragmenta_design_spec.md)** - Fragmenta 架构规范
- **[MCP 集成](./technical_design/CONTEXT7_MCP_INTEGRATION.md)** - Context7 MCP 集成方案
- **[数据标准](./technical_design/INTERNAL_DATA_STANDARDS.md)** - 内部数据格式和标准

### 🔧 技术规范
- **[消息传输](./technical_specs/MESSAGE_TRANSPORT.md)** - 消息传输机制
- **[模型和工具](./technical_specs/MODELS_AND_TOOLS.md)** - AI 模型和工具集
- **[执行监控](./technical_specs/README_EXECUTION_MONITOR.md)** - 执行监控系统
- **[故障排除](./technical_specs/TROUBLESHOOTING.md)** - 常见问题和解决方案

### 🧪 测试文档
- **[测试总结](./testing/test_summary.md)** - 测试修复和改进记录
- **[测试修复摘要](./testing/TEST_FIXES_SUMMARY.md)** - 详细的测试修复历史
- **[测试策略](./technical_design/testing/TEST_TIMEOUT_STRATEGY.md)** - 测试超时策略

### 📊 项目管理
- **[项目状态](./project_status/PROJECT_ORGANIZATION_STATUS.md)** - 当前项目组织状态
- **[成功标准](./project_status/SUCCESS_CRITERIA.md)** - 项目成功评估标准
- **[内容组织](./project_management/PROJECT_CONTENT_ORGANIZATION.md)** - 项目内容组织方式
- **[状态摘要](./project_management/PROJECT_STATUS_SUMMARY.md)** - 项目状态总结

### 🚧 开发文档
- **[重构计划](./development/MERGE_AND_RESTRUCTURE_PLAN.md)** - 项目合并和重构计划
- **[待办事项](./development/TODO_PLACEHOLDERS.md)** - 开发待办和占位符
- **[贡献指南](../CONTRIBUTING.md)** - 如何为项目做出贡献

### 💭 哲学与愿景
- **[项目哲学](./philosophy/PHILOSOPHY_AND_VISION.md)** - 项目核心理念和长期愿景

### 📁 存档
- **[历史文档](./archive/)** - 已过时或历史版本的文档

## 🔍 文档搜索指南

### 按角色查找
- **开发者**: 技术架构 → 技术规范 → 测试文档
- **项目经理**: 项目管理 → 项目状态 → 开发文档
- **设计师**: 游戏设计 → 哲学与愿景
- **新用户**: 快速开始 → 项目概述 → 术语表

### 按主题查找
- **AI 系统**: HAM 设计、Fragmenta 设计、模型和工具
- **通信协议**: HSP 规范、消息传输、MCP 集成
- **游戏开发**: 游戏设计目录下的所有文档
- **系统集成**: 技术架构和技术规范

---

## 🚀 快速行动

### 立即开始使用
1. **安装项目**: `pip install -e .`
2. **验证安装**: `python -c "import src.core_ai; print('✅ 成功!')"`
3. **启动 API**: `uvicorn src.services.main_api_server:app --reload`
4. **测试功能**: `python src/interfaces/cli/main.py query "Hello Angela"`

### 获取帮助
- 📚 **完整指南**: 查看上方的分类导航
- ❓ **常见问题**: 参考 [FAQ](../README.md#常見問題)
- 🤝 **参与贡献**: 阅读 [贡献指南](../CONTRIBUTING.md)
- 🐛 **报告问题**: 提交 GitHub Issue

---

*文档持续更新中，最后更新：2025年1月* 📅
