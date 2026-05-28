# Unified-AI.bat 快速开始指南

## 🎯 简介

为了解决项目中批处理脚本过多的问题，我们创建了 `unified-ai.bat` 统一管理工具。这个工具整合了所有常用的批处理脚本功能，提供了一个简单易用的菜单界面。

## 📋 功能概览

统一管理工具包含以下主要功能：

1. **Health Check** - 环境健康检查
2. **Setup Environment** - 安装依赖和设置环境
3. **Start Development** - 启动开发环境
4. **Run Tests** - 运行测试套件
5. **Git Management** - Git 状态管理和清理
6. **Training Setup** - 训练环境设置
7. **Emergency Git Fix** - 紧急 Git 修复

## 🚀 使用方法

### 1. 双击运行
最简单的使用方法是直接双击项目根目录下的 `unified-ai.bat` 文件。

### 2. 命令行运行
你也可以在命令行中运行：
```cmd
unified-ai.bat
```

### 3. 通过 npm 运行
我们还在 `package.json` 中添加了快捷方式：
```bash
pnpm unified-ai
```

## 🎮 详细使用说明

### 首次使用
1. 双击运行 `unified-ai.bat`
2. 选择 "Setup Environment" (选项 2) 来安装所有依赖和设置环境
3. 等待设置完成
4. 选择 "Start Development" (选项 3) 来启动开发环境

### 日常开发
1. 双击运行 `unified-ai.bat`
2. 选择 "Start Development" (选项 3)
3. 选择 "Start Full Development Environment" (选项 1)
4. 开发服务器将在以下地址启动：
   - 后端 API: http://localhost:8000
   - 前端仪表板: http://localhost:3000

### 运行测试
1. 双击运行 `unified-ai.bat`
2. 选择 "Run Tests" (选项 4)
3. 选择你想要运行的测试类型：
   - All Tests (所有测试)
   - Backend Only (仅后端测试)
   - Frontend Only (仅前端测试)
   - 等等...

### Git 管理
1. 双击运行 `unified-ai.bat`
2. 选择 "Git Management" (选项 5)
3. 选择相应的 Git 操作：
   - Check Git Status (检查状态)
   - Safe Git Cleanup (安全清理)
   - Git 10K+ Fix (处理大量文件问题)

### 训练准备
1. 双击运行 `unified-ai.bat`
2. 选择 "Training Setup" (选项 6)
3. 等待训练环境设置完成

## 🛠️ 故障排除

### 脚本无法运行
- 确保你在项目根目录下运行脚本
- 确保你有执行批处理文件的权限
- 如果双击无法运行，尝试右键选择"以管理员身份运行"

### 环境检查失败
- 按照脚本提示安装缺失的组件（Node.js、Python、pnpm等）
- 确保你的系统 PATH 环境变量包含了这些工具

### 开发服务器无法启动
- 检查端口是否被占用（8000、3000、8001）
- 确保防火墙没有阻止这些端口
- 检查是否有其他服务正在使用这些端口

## 📈 优势

### 减少脚本数量
- 整合前：24个独立脚本
- 整合后：1个统一脚本 + 5个核心脚本
- 减少75%的脚本数量

### 简化操作流程
- 统一入口：只需要记住一个脚本名称
- 菜单导航：通过数字选择功能，无需记忆复杂命令
- 功能整合：相关功能分组展示，提高易用性

### 保持功能完整性
- 所有原有脚本的功能都包含在统一工具中
- 保留了核心独立脚本以确保兼容性
- 提供了传统命令行方式作为备选

## 🔄 过渡计划

### 当前状态
- [x] 创建 unified-ai.bat
- [x] 更新相关文档
- [x] 功能测试完成
- [ ] 用户反馈收集中

### 未来计划
- [ ] 根据用户反馈优化功能
- [ ] 逐步标记过时脚本
- [ ] 在文档中推荐使用统一工具
- [ ] 适当时机逐步删除冗余脚本

## 📞 支持

如果你在使用统一管理工具时遇到任何问题，请查看：
1. [批处理脚本使用指南](BATCH_SCRIPTS_USAGE_GUIDE.md)
2. [Git与项目管理指南](GIT_AND_PROJECT_MANAGEMENT.md)
3. [训练准备检查清单](TRAINING_PREPARATION_CHECKLIST.md)

或者在项目中提交 issue 寻求帮助。