# Unified-AI-Project 批处理脚本使用指南

## 🎯 概述

本指南整合了项目中所有批处理脚本的使用方法、功能说明和故障排除信息，旨在为开发者提供清晰、一致的操作指导。

## 📋 核心脚本说明

### unified-ai.bat - 统一管理工具 (推荐)
**用途**: 统一管理项目的各种功能
**特点**: 
- ✅ 整合所有常用功能
- ✅ 简化操作流程
- ✅ 提供友好的菜单界面
- ✅ 包含所有原有脚本的功能

**使用方法**:
```cmd
双击运行 unified-ai.bat
```

**选项说明**:
1. **Health Check** - 环境健康检查
2. **Setup Environment** - 安装依赖和设置环境
3. **Start Development** - 启动开发环境
4. **Run Tests** - 运行测试套件
5. **Git Management** - Git 状态管理和清理
6. **Training Setup** - 训练环境设置
7. **Emergency Git Fix** - 紧急 Git 修复

### health-check.bat - 环境健康检查
**用途**: 检查开发环境是否正确配置
**特点**: 
- ✅ 检查 Node.js、Python、pnpm 是否已安装
- ✅ 检查项目依赖是否已安装
- ✅ 检查 Python 虚拟环境和配置文件
- ✅ 提供问题解决建议

**使用方法**:
```cmd
双击运行 health-check.bat
```

### start-dev.bat - 开发环境启动
**用途**: 自动设置并启动开发环境
**特点**:
- ✅ 自动安装依赖
- ✅ 创建 Python 虚拟环境
- ✅ 提供多种启动选项

**使用方法**:
```cmd
双击运行 start-dev.bat
```

**选项说明**:
1. **启动完整开发环境** - 后端 + 前端
2. **只启动后端** - API 服务器 + ChromaDB
3. **只启动前端** - 仪表板界面
4. **运行测试** - 所有组件的单元测试
5. **清理 Git 状态** - 清理 Git 仓库状态

### run-tests.bat - 测试套件
**用途**: 运行项目测试
**特点**:
- ✅ 支持多种测试模式
- ✅ 提供详细的测试结果
- ✅ 包含覆盖率报告生成

**使用方法**:
```cmd
双击运行 run-tests.bat
```

**选项说明**:
1. **All Tests** - 后端 + 前端 + 桌面应用
2. **Backend Only** - Python pytest
3. **Frontend Only** - Jest 测试
4. **Desktop Only** - Electron 测试
5. **Coverage Reports** - 生成覆盖率报告
6. **Quick Tests** - 跳过标记为 'slow' 的测试
7. **Watch Mode** - 文件变化时自动运行测试
8. **Check Git Status** - 检查 Git 状态
9. **Exit** - 退出

### safe-git-cleanup.bat - Git 状态清理
**用途**: 安全地清理 Git 状态
**特点**:
- ✅ 只添加重要的项目文件
- 🛡️ 不会删除任何现有文件
- ✅ 确保 .gitignore 正确忽略临时文件
- ✅ 安全提交和推送

**使用方法**:
```cmd
双击运行 safe-git-cleanup.bat
```

## 🔧 技术改进与修复

### 编码问题修复
所有脚本均已修复中文字符编码问题：
```batch
@echo off
chcp 65001 >nul 2>&1                    # 设置UTF-8编码
setlocal enabledelayedexpansion          # 启用延迟变量扩展
```

### 进度条功能
关键脚本已添加进度条功能，提供清晰的执行状态反馈。

### 错误处理增强
- 自动回退机制：pnpm 失败时尝试 npm
- 详细错误代码和建议
- 智能环境检测和修复提示

### pytest.ini 配置文件修复
在项目中发现并修复了 [apps/backend/pytest.ini](../apps/backend/pytest.ini) 文件中的 Git 合并冲突标记。
这解决了后端测试无法运行的问题。

详细信息请查看：[PYTEST_INI_FIX_REPORT.md](PYTEST_INI_FIX_REPORT.md)

## 🎮 推荐使用流程

### 首次使用流程
```
1. health-check.bat     # 检查环境状态
   ↓
2. start-dev.bat        # 设置并启动开发环境
   ↓  
3. run-tests.bat        # 运行测试验证
```

### 日常开发流程
```
1. start-dev.bat        # 启动开发环境
   ↓
2. 开发过程中自动重载
   ↓
3. run-tests.bat        # 验证更改
```

### 故障排查流程
```
1. health-check.bat     # 诊断问题
   ↓
2. 按建议修复问题
   ↓
3. start-dev.bat        # 重新设置环境
   ↓
4. run-tests.bat        # 验证修复
```

## 🛠️ 故障排除

### 常见问题

1. **"Node.js 未安装"**
   - 下载并安装 Node.js: https://nodejs.org/

2. **"Python 未安装"**
   - 下载并安装 Python: https://python.org/

3. **"pnpm 未安装"**
   - 运行: `npm install -g pnpm`

4. **端口被占用**
   - 检查是否有其他服务占用 8000、3000、8001 端口
   - 关闭其他服务或重启电脑

5. **Python 虚拟环境问题**
   - 删除 `apps\backend\venv` 文件夹
   - 重新运行 `start-dev.bat`

6. **后端测试失败**
   - 检查 [apps/backend/pytest.ini](../apps/backend/pytest.ini) 文件是否包含合并冲突标记
   - 查看 [PYTEST_INI_FIX_REPORT.md](PYTEST_INI_FIX_REPORT.md) 了解解决方案

### 重置项目环境

如果遇到严重问题，可以重置环境：

1. 删除以下文件夹：
   - `node_modules`
   - `apps\backend\venv`
   - `apps\frontend-dashboard\node_modules`
   - `apps\desktop-app\node_modules`

2. 重新运行 `start-dev.bat`

## 📊 脚本功能对比

| 脚本 | 主要功能 | 特点 | 推荐使用场景 |
|------|----------|------|--------------|
| `health-check.bat` | 环境检查 | 详细检查、修复建议 | 首次设置、问题排查 |
| `start-dev.bat` | 开发环境 | 自动设置、服务启动 | 日常开发、环境配置 |
| `run-tests.bat` | 测试执行 | 快速简洁 | 日常测试 |
| `safe-git-cleanup.bat` | Git 清理 | 安全操作 | Git 状态维护 |

## 📈 最佳实践

1. **首次设置后**，运行一次完整测试确保环境正常
2. **日常开发**，建议使用"开发 + 测试监控"模式
3. **提交代码前**，运行完整测试套件和覆盖率检查
4. **遇到问题时**，首先运行健康检查

---
*本指南基于 Unified-AI-Project 项目批处理脚本的实际功能整理*