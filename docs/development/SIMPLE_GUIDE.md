# 🚀 Unified-AI-Project - 简化后的项目指南

## 📋 现在根目录只有这些核心文件

```text
Unified-AI-Project/
├── 🎯 unified-ai.bat      # 统一管理工具 (供人类用户使用)
├── 🤖 ai-runner.bat       # AI代理运行工具 (供AI代理使用)
├── 📖 README.md           # 项目主要说明
├── 📋 SIMPLE_GUIDE.md     # 本指南
│
├── 📁 docs/               # 所有文档都在这里
├── 📁 backup/             # 备份的脚本
├── 📁 apps/               # 应用代码
├── 📁 packages/           # 共享包
├── 📁 scripts/            # 原始脚本目录
└── 📁 tools/              # 其他批处理工具
```

## 🎯 快速开始

### 推荐使用统一管理工具
```powershell
# 1. 双击运行 unified-ai.bat
# 2. 选择相应功能
```

### AI代理使用方式
```powershell
# AI代理可以使用ai-runner.bat执行自动化任务
.\ai-runner.bat setup     # 设置开发环境
.\ai-runner.bat start     # 启动开发服务器
.\ai-runner.bat test      # 运行测试
.\ai-runner.bat train     # 设置训练环境
.\ai-runner.bat health    # 运行健康检查
.\ai-runner.bat clean     # 清理Git状态
```

### 或者使用传统方式
```powershell
# 1. 检查环境是否正常
.\tools\health-check.bat

# 2. 启动开发环境
.\tools\start-dev.bat

# 3. 运行测试验证
.\tools\run-tests.bat
```

### 日常开发

推荐使用统一管理工具：
1. 双击运行 `unified-ai.bat`
2. 选择 "Start Development"
3. 选择 "Start Full Development Environment"

或者使用传统方式：
```powershell
# 启动开发环境（包含前端+后端）
.\tools\start-dev.bat

# 服务地址
# - 后端API: http://localhost:8000
# - 前端仪表板: http://localhost:3000
# - ChromaDB: http://localhost:8001
```

### 训练准备

推荐使用统一管理工具：
1. 双击运行 `unified-ai.bat`
2. 选择 "Training Setup"

或者使用传统方式：
```powershell
# 设置训练环境
.\tools\setup-training.bat
```

## 🔄 如需更多工具

如果需要使用之前的Git修复工具或其他脚本：

```powershell
# 查看tools目录中的脚本
Get-ChildItem tools\

# 使用特定工具
.\tools\fix-git-10k.bat
.\tools\emergency-git-fix.bat
.\tools\safe-git-cleanup.bat
```

## 📚 查看文档

所有文档现在整理在 `docs/` 目录中，特别推荐以下整合文档：

```powershell
# 查看所有文档
Get-ChildItem docs\

# 推荐的整合文档指南
notepad docs\BATCH_SCRIPTS_USAGE_GUIDE.md    # 批处理脚本使用指南
notepad docs\GIT_AND_PROJECT_MANAGEMENT.md   # Git与项目管理指南
notepad docs\TRAINING_PREPARATION_CHECKLIST.md  # 训练准备检查清单

# 其他重要文档
notepad docs\DEVELOPMENT_GUIDE.md
notepad docs\GIT_10K_SOLUTION_REPORT.md
```

## 🛠️ 项目技术栈

- **前端**: Next.js 15 + TypeScript + Tailwind CSS
- **后端**: Python + FastAPI + ChromaDB
- **桌面应用**: Electron
- **包管理**: pnpm
- **测试**: pytest (后端) + jest (前端)

## 💡 重要提示

1. **核心功能**: 只保留了2个最重要的脚本供直接使用，其他脚本移至tools目录
2. **文档整理**: 所有25个MD文档都在 `docs/` 目录
3. **脚本备份**: 所有其他脚本都在 `tools/` 目录
4. **安全保障**: 没有删除任何重要文件，只是移动和整理
5. **随时恢复**: 可以从tools目录使用任何需要的文件

## 🎉 清理效果

- **之前**: 根目录有多个批处理文件
- **现在**: 根目录只有2个核心脚本 + 2个说明文档
- **备份**: 所有文件都安全保存在对应目录中

---

**简化完成！现在项目结构清爽多了** 🌟