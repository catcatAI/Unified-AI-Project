# 📚 完整文档索引

## 🎯 按文档类型分类

### 📖 核心文档

| 文档名称 | 位置                      | 描述               | 更新状态 |
| -------- | ------------------------- | ------------------ | -------- |
| 项目概述 | `README.md`               | 项目简介和快速开始 | ✅ 最新  |
| 项目章程 | `docs/PROJECT_CHARTER.md` | 完整架构说明       | ✅ 最新  |
| 术语表   | `docs/GLOSSARY.md`        | 关键概念定义       | ✅ 最新  |
| 贡献指南 | `CONTRIBUTING.md`         | 参与项目指南       | ✅ 最新  |

### 🎮 游戏设计文档

| 文档名称    | 位置                                   | 描述                | 完成度  |
| ----------- | -------------------------------------- | ------------------- | ------- |
| 游戏概述    | `docs/game/README.md`                  | Angela's World 总览 | ✅ 完整 |
| 主设计文档  | `docs/game/main_design.md`             | 核心游戏设计        | ✅ 完整 |
| 角色设计    | `docs/game/character_design.md`        | 游戏角色设定        | ✅ 完整 |
| Angela 设计 | `docs/game/character_design_angela.md` | AI 角色详细设计     | ✅ 新建 |
| 游戏系统    | `docs/game/game_systems.md`            | 游戏机制设计        | ✅ 完整 |
| 地图设计    | `docs/game/map_design.md`              | 游戏世界设计        | ✅ 完整 |
| 成功标准    | `docs/game/SUCCESS_CRITERIA.md`        | 游戏成功指标        | ✅ 完整 |

### 🏗️ 技术架构文档

| 文档名称       | 位置                                                                  | 描述                 | 复杂度 |
| -------------- | --------------------------------------------------------------------- | -------------------- | ------ |
| HSP 规范       | `docs/technical_design/HSP_SPECIFICATION.md`                          | 异构服务协议         | 🔴 高  |
| HAM 设计       | `docs/technical_design/architecture/HAM_design_spec.md`               | 分层抽象记忆         | 🔴 高  |
| Fragmenta 设计 | `docs/technical_design/architecture/Fragmenta_design_spec.md`         | Fragmenta 架构       | 🔴 高  |
| MCP 集成       | `docs/technical_design/CONTEXT7_MCP_INTEGRATION.md`                   | Context7 集成        | 🟡 中  |
| 数据标准       | `docs/technical_design/INTERNAL_DATA_STANDARDS.md`                    | 内部数据格式         | 🟡 中  |
| 代理协作       | `docs/technical_design/architecture/AGENT_COLLABORATION_FRAMEWORK.md` | 代理协作框架         | 🔴 高  |
| AVIS 规范      | `docs/technical_design/architecture/AI_Virtual_Input_System_spec.md`  | AI 虚拟输入系统      | 🔴 高  |
| LIS 規範       | `docs/technical_design/architecture/Linguistic_Immune_System_spec.md` | 語言免疫系統         | 🔴 高  |
| 核心服務概述   | `docs/technical_design/CORE_SERVICES_OVERVIEW.md`                     | 核心服務初始化與管理 | 🟢 高  |

### 🔧 技术规范文档

| 文档名称   | 位置                                               | 描述          | 实用性 |
| ---------- | -------------------------------------------------- | ------------- | ------ |
| 消息传输   | `docs/technical_specs/MESSAGE_TRANSPORT.md`        | 消息传输机制  | 🟢 高  |
| 模型和工具 | `docs/technical_specs/MODELS_AND_TOOLS.md`         | AI 模型工具集 | 🟢 高  |
| 执行监控   | `docs/technical_specs/README_EXECUTION_MONITOR.md` | 执行监控系统  | 🟡 中  |
| 故障排除   | `docs/technical_specs/TROUBLESHOOTING.md`          | 问题解决指南  | 🟢 高  |

### 🧪 测试文档

| 文档名称     | 位置                                                     | 描述         | 状态    |
| ------------ | -------------------------------------------------------- | ------------ | ------- |
| 测试总结     | `docs/testing/test_summary.md`                           | 测试修复记录 | ✅ 最新 |
| 测试修复摘要 | `docs/testing/TEST_FIXES_SUMMARY.md`                     | 详细修复历史 | ✅ 最新 |
| 测试策略     | `docs/technical_design/testing/TEST_TIMEOUT_STRATEGY.md` | 测试超时策略 | ✅ 最新 |

### 📊 项目管理文档

| 文档名称 | 位置                                                      | 描述         | 重要性 |
| -------- | --------------------------------------------------------- | ------------ | ------ |
| 项目状态 | `docs/project_status/PROJECT_ORGANIZATION_STATUS.md`      | 当前组织状态 | 🟢 高  |
| 成功标准 | `docs/project_status/SUCCESS_CRITERIA.md`                 | 项目成功指标 | 🟢 高  |
| 内容组织 | `docs/project_management/PROJECT_CONTENT_ORGANIZATION.md` | 内容组织方式 | 🟡 中  |
| 状态摘要 | `docs/project_management/PROJECT_STATUS_SUMMARY.md`       | 项目状态总结 | 🟡 中  |

### 🚧 开发文档

| 文档名称 | 位置                                             | 描述         | 时效性  |
| -------- | ------------------------------------------------ | ------------ | ------- |
| 重构计划 | `docs/development/MERGE_AND_RESTRUCTURE_PLAN.md` | 项目重构计划 | 🟡 历史 |
| 待办事项 | `docs/development/TODO_PLACEHOLDERS.md`          | 开发待办列表 | 🟢 活跃 |

## 🎯 按使用场景分类

### 🚀 新用户入门路径

1. `README.md` - 项目概述
2. `docs/README.md` - 文档导航
3. `docs/GLOSSARY.md` - 术语表
4. `docs/00-overview/PROJECT_CHARTER.md` - 详细架构

### 👨‍💻 开发者技术路径

1. `docs/technical_design/HSP_SPECIFICATION.md` - 通信协议
2. `docs/technical_design/architecture/HAM_design_spec.md` - 记忆系统
3. `docs/technical_specs/` - 技术规范目录
4. `docs/testing/` - 测试文档目录

### 🎮 游戏开发路径

1. `docs/game/README.md` - 游戏概述
2. `docs/game/main_design.md` - 主设计
3. `docs/game/character_design_angela.md` - Angela 设计
4. `docs/game/game_systems.md` - 游戏系统

### 📊 项目管理路径

1. `docs/project_status/PROJECT_ORGANIZATION_STATUS.md` - 项目状态
2. `docs/project_management/` - 管理文档目录
3. `docs/development/TODO_PLACEHOLDERS.md` - 待办事项

## 🔍 文档质量评估

### ✅ 高质量文档

- `README.md` - 清晰的项目介绍
- `docs/game/` 目录 - 完整的游戏设计
- `docs/technical_specs/TROUBLESHOOTING.md` - 实用的故障排除

### 🟡 需要优化的文档

- `docs/technical_design/HSP_SPECIFICATION.md` - 过于复杂，需要简化
- `docs/technical_design/architecture/` - 部分文档过于技术化
- `docs/development/MERGE_AND_RESTRUCTURE_PLAN.md` - 历史文档，需要更新

### 🔴 需要重点关注的文档

- 复杂的技术架构文档需要添加更多示例
- 部分文档缺少目录和导航
- 一些文档需要更新到最新状态

---

_本索引每月更新一次，最后更新：2025年1月_
