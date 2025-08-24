# 🚀 Unified-AI-Project - 简化后的项目指南

## 📋 现在根目录只有这些核心文件

```text
Unified-AI-Project/
├── 🔧 health-check.bat    # 环境检查工具
├── 🚀 start-dev.bat       # 启动开发环境
├── 🧪 run-tests.bat       # 运行测试套件
├── 📖 README.md           # 项目主要说明
├── 📋 SIMPLE_GUIDE.md     # 本指南
│
├── 📁 docs/               # 所有文档都在这里
├── 📁 backup/             # 备份的脚本
├── 📁 apps/               # 应用代码
├── 📁 packages/           # 共享包
└── 📁 scripts/            # 原始脚本目录
```

## 🎯 快速开始

### 第一次使用
```powershell
# 1. 检查环境是否正常
.\health-check.bat

# 2. 启动开发环境
.\start-dev.bat

# 3. 运行测试验证
.\run-tests.bat
```

### 日常开发
```powershell
# 启动开发环境（包含前端+后端）
.\start-dev.bat

# 服务地址
# - 后端API: http://localhost:8000
# - 前端仪表板: http://localhost:3000
# - ChromaDB: http://localhost:8001
```

## 🔄 如需更多工具

如果需要使用之前的Git修复工具或其他脚本：

```powershell
# 查看备份的脚本
Get-ChildItem backup\scripts\

# 复制需要的脚本回根目录
Copy-Item backup\scripts\fix-git-10k.bat .
Copy-Item backup\scripts\emergency-git-fix.bat .

# 使用完后可以删除
Remove-Item fix-git-10k.bat
```

## 📚 查看文档

所有文档现在整理在 `docs/` 目录中：

```powershell
# 查看所有文档
Get-ChildItem docs\

# 打开特定文档
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

1. **核心功能**: 只保留了3个最重要的脚本
2. **文档整理**: 所有25个MD文档都在 `docs/` 目录
3. **脚本备份**: 所有其他脚本都在 `backup/scripts/` 目录
4. **安全保障**: 没有删除任何重要文件，只是移动和整理
5. **随时恢复**: 可以从备份目录恢复任何需要的文件

## 🎉 清理效果

- **之前**: 根目录有25个MD文件 + 16个BAT脚本
- **现在**: 根目录只有3个核心脚本 + 2个说明文档
- **备份**: 所有文件都安全保存在对应目录中

---

**简化完成！现在项目结构清爽多了** 🌟