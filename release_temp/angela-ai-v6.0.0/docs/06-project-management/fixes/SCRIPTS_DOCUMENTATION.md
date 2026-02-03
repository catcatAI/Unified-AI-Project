# Unified AI Project 脚本文档和使用指南

> **备份说明**: 此文档已备份至 `backup_20250903/script_analysis/SCRIPTS_DOCUMENTATION.md.backup`，作为历史记录保存。
>
> **状态**: 问题已解决，此文档仅供历史参考。

## 1. 概述

本文档提供了Unified AI Project项目中所有脚本的详细说明和使用指南，包括pnpm指令、批处理脚本、PowerShell脚本和Python脚本。

## 2. 统一命令行界面 (CLI)

### 2.1 简介
Unified AI Project CLI (`unified-ai-cli.bat`) 是一个新的统一命令行工具，整合了项目管理的所有功能。

### 2.2 安装和设置
```bash
# CLI工具无需额外安装，直接使用
unified-ai-cli.bat
```

### 2.3 基本用法
```bash
# 显示帮助信息
unified-ai-cli.bat --help

# 显示版本信息
unified-ai-cli.bat --version
```

### 2.4 开发环境管理
```bash
# 启动开发环境
unified-ai-cli.bat dev start

# 启动后端服务
unified-ai-cli.bat dev start --backend

# 启动前端服务
unified-ai-cli.bat dev start --frontend

# 启动所有服务
unified-ai-cli.bat dev start --all

# 停止开发环境
unified-ai-cli.bat dev stop

# 查看开发环境状态
unified-ai-cli.bat dev status

# 重启开发环境
unified-ai-cli.bat dev restart

# 设置开发环境
unified-ai-cli.bat dev setup
```

### 2.5 测试管理
```bash
# 运行所有测试
unified-ai-cli.bat test run

# 运行后端测试
unified-ai-cli.bat test run --backend

# 运行前端测试
unified-ai-cli.bat test run --frontend

# 运行快速测试
unified-ai-cli.bat test run --quick

# 运行慢速测试
unified-ai-cli.bat test run --slow

# 监视模式运行测试
unified-ai-cli.bat test watch

# 生成测试覆盖率报告
unified-ai-cli.bat test coverage

# 生成HTML格式的覆盖率报告
unified-ai-cli.bat test coverage --html

# 在终端显示覆盖率报告
unified-ai-cli.bat test coverage --term

# 列出可用测试
unified-ai-cli.bat test list
```

### 2.6 Git管理
```bash
# 查看Git状态
unified-ai-cli.bat git status

# 清理Git状态
unified-ai-cli.bat git clean

# 强制清理Git状态
unified-ai-cli.bat git clean --force

# 修复常见的Git问题
unified-ai-cli.bat git fix

# 紧急修复Git问题
unified-ai-cli.bat git emergency

# 同步远程仓库
unified-ai-cli.bat git sync

# 创建并切换到新分支
unified-ai-cli.bat git create-branch <branch_name>

# 切换到指定分支
unified-ai-cli.bat git switch-branch <branch_name>
```

## 3. pnpm 指令

### 3.1 根目录指令

#### 安装和设置
```bash
# 安装所有依赖（Node.js和Python）
pnpm install:all

# 设置项目
pnpm setup
```

#### 开发环境
```bash
# 启动前端仪表板
pnpm dev:dashboard

# 启动后端服务
pnpm dev:backend

# 启动桌面应用
pnpm dev:desktop

# 启动后端和前端
pnpm dev

# 启动所有服务
pnpm dev:all
```

#### 测试
```bash
# 运行所有测试
pnpm test

# 运行后端测试
pnpm test:backend

# 运行前端测试
pnpm test:frontend

# 运行桌面应用测试
pnpm test:desktop

# 运行测试覆盖率
pnpm test:coverage

# 监视模式运行测试
pnpm test:watch

# 同时启动开发环境和测试监控
pnpm dev-test
```

#### 构建和清理
```bash
# 构建所有应用
pnpm build

# 清理项目
pnpm clean

# 健康检查
pnpm health-check

# 运行统一管理工具
pnpm unified-ai
```

### 3.2 Backend 目录指令

#### 设置和开发
```bash
# 设置后端环境
pnpm setup

# 启动后端开发服务
pnpm dev

# 启动API服务
pnpm dev:api

# 启动ChromaDB服务
pnpm dev:chroma
```

#### 测试
```bash
# 运行测试
pnpm test

# 生成测试覆盖率报告
pnpm test:coverage

# 监视模式运行测试
pnpm test:watch
```

#### 清理和健康检查
```bash
# 清理虚拟环境
pnpm clean

# 健康检查
pnpm health
```

#### 自动修复
```bash
# 简单自动修复
pnpm fix

# 完整自动修复
pnpm fix:complete

# 高级自动修复
pnpm fix:advanced

# 修复并测试
pnpm fix:test

# 高级修复并测试
pnpm fix:advanced:test

# 验证
pnpm validate

# 验证并修复
pnpm validate:fix

# 修复演示
pnpm demo:fix
```

### 3.3 Frontend Dashboard 目录指令

```bash
# 开发模式
pnpm dev

# 构建项目
pnpm build

# 启动生产服务器
pnpm start

# 代码检查
pnpm lint

# 运行测试
pnpm test

# 生成测试覆盖率报告
pnpm test:coverage

# 数据库操作
pnpm db:push
pnpm db:generate
pnpm db:migrate
pnpm db:reset
```

### 3.4 Desktop App 目录指令

```bash
# 启动桌面应用
pnpm start

# 运行测试
pnpm test

# 生成测试覆盖率报告
pnpm test:coverage
```

## 4. 批处理脚本

### 4.1 开发环境脚本

#### unified-ai.bat
主管理工具，提供图形化菜单界面：
```bash
# 直接运行
unified-ai.bat

# 或双击文件运行
```

#### tools\start-dev.bat
启动开发环境：
```bash
# 启动开发环境
tools\start-dev.bat
```

#### scripts\dev.ps1
PowerShell开发环境脚本：
```bash
# 启动开发环境
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 dev

# 安装依赖
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 install

# 运行测试
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 test

# 启动开发环境和测试监控
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 dev-test

# 停止所有服务
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 stop
```

### 4.2 测试脚本

#### tools\run-backend-tests.bat
运行后端测试：
```bash
# 运行快速测试（默认）
tools\run-backend-tests.bat

# 运行所有测试
tools\run-backend-tests.bat all

# 运行慢速测试
tools\run-backend-tests.bat slow

# 并行运行测试
tools\run-backend-tests.bat parallel
```

#### apps\backend\run-component-tests.bat
运行组件测试：
```bash
# 运行组件测试
apps\backend\run-component-tests.bat
```

#### apps\backend\run_test_fixes.bat
运行测试修复：
```bash
# 运行测试修复
apps\backend\run_test_fixes.bat
```

### 4.3 Git管理脚本

#### tools\emergency-git-fix.bat
紧急Git修复：
```bash
# 紧急修复Git问题
tools\emergency-git-fix.bat
```

#### tools\safe-git-cleanup.bat
安全Git清理：
```bash
# 安全清理Git状态
tools\safe-git-cleanup.bat
```

### 4.4 依赖管理脚本

#### tools\fix-dependencies.bat
修复依赖问题：
```bash
# 修复依赖问题
tools\fix-dependencies.bat
```

#### tools\recreate-venv.bat
重新创建虚拟环境：
```bash
# 重新创建Python虚拟环境
tools\recreate-venv.bat
```

### 4.5 数据处理脚本

#### tools\run_data_pipeline.bat
运行数据管道：
```bash
# 运行数据处理管道
tools\run_data_pipeline.bat
```

### 4.6 训练管理脚本

#### tools\train-manager.bat
训练管理器：
```bash
# 运行训练管理器
tools\train-manager.bat
```

#### tools\setup-training.bat
设置训练环境：
```bash
# 设置训练环境
tools\setup-training.bat
```

### 4.7 备份和恢复脚本

#### tools\automated-backup.bat
自动备份：
```bash
# 执行自动备份
tools\automated-backup.bat
```

#### tools\enhanced-file-recovery.bat
增强文件恢复：
```bash
# 执行文件恢复
tools\enhanced-file-recovery.bat
```

### 4.8 系统工具脚本

#### tools\health-check.bat
健康检查：
```bash
# 执行健康检查
tools\health-check.bat
```

#### tools\common-functions.bat
通用函数库（被其他脚本调用）：
```bash
# 不直接运行，由其他脚本引用
```

#### tools\view-error-logs.bat
查看错误日志：
```bash
# 查看错误日志
tools\view-error-logs.bat
```

#### tools\syntax-check.bat
语法检查：
```bash
# 执行语法检查
tools\syntax-check.bat
```

## 5. PowerShell 脚本

### 5.1 scripts\dev.ps1
完整的开发环境管理脚本：
```bash
# 启动开发环境
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 dev

# 安装依赖
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 install

# 运行测试
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 test

# 启动开发环境和测试监控
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 dev-test

# 停止所有服务
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 stop

# 仅启动后端
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 dev -Backend

# 仅启动前端
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 dev -Frontend

# 仅启动桌面应用
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 dev -Desktop

# 运行测试覆盖率
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 test -Coverage

# 监视模式运行测试
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 test -Watch
```

### 5.2 tools\enhanced-backup-restore.ps1
增强备份恢复：
```bash
# 执行增强备份恢复
powershell -ExecutionPolicy Bypass -File tools\enhanced-backup-restore.ps1
```

## 6. Python 脚本

### 6.1 开发工具

#### scripts\health_check.py
健康检查：
```bash
# 运行健康检查
python scripts\health_check.py
```

#### scripts\dev.ps1
开发环境管理（PowerShell）：
```bash
# 通过pnpm运行
pnpm dev
```

### 6.2 测试工具

#### apps\backend\scripts\smart_test_runner.py
智能测试运行器：
```bash
# 运行智能测试
python apps\backend\scripts\smart_test_runner.py

# 传递pytest参数
python apps\backend\scripts\smart_test_runner.py -v --tb=short
```

#### apps\backend\scripts\test_runner.py
测试运行器：
```bash
# 运行测试
python apps\backend\scripts\test_runner.py
```

#### apps\backend\scripts\error_analyzer.py
错误分析器：
```bash
# 分析测试错误
python apps\backend\scripts\error_analyzer.py
```

#### apps\backend\scripts\fix_executor.py
修复执行器：
```bash
# 执行自动修复
python apps\backend\scripts\fix_executor.py
```

#### apps\backend\scripts\workflow_controller.py
工作流控制器：
```bash
# 运行测试-修复工作流
python apps\backend\scripts\workflow_controller.py

# 在不同终端中运行
python apps\backend\scripts\workflow_controller.py --separate-terminals
```

### 6.3 自动修复工具

#### apps\backend\scripts\simple_auto_fix.py
简单自动修复：
```bash
# 运行简单自动修复
python apps\backend\scripts\simple_auto_fix.py

# 修复并测试
python apps\backend\scripts\simple_auto_fix.py --fix --test
```

#### apps\backend\scripts\auto_fix_complete.py
完整自动修复：
```bash
# 运行完整自动修复
python apps\backend\scripts\auto_fix_complete.py
```

#### apps\backend\scripts\advanced_auto_fix.py
高级自动修复：
```bash
# 运行高级自动修复
python apps\backend\scripts\advanced_auto_fix.py

# 测试修复
python apps\backend\scripts\advanced_auto_fix.py --test
```

## 7. 最佳实践

### 7.1 开发环境设置
1. 使用 `unified-ai-cli.bat dev setup` 或 `pnpm install:all` 安装所有依赖
2. 使用 `unified-ai-cli.bat dev start` 或 `pnpm dev` 启动开发环境
3. 定期使用 `unified-ai-cli.bat git sync` 同步代码

### 7.2 测试流程
1. 编写代码后运行 `unified-ai-cli.bat test run` 执行测试
2. 如需详细报告，运行 `unified-ai-cli.bat test coverage --html`
3. 使用监视模式 `unified-ai-cli.bat test watch` 进行持续测试

### 7.3 Git工作流
1. 开始新功能前创建分支：`unified-ai-cli.bat git create-branch feature-name`
2. 定期提交更改并推送到远程仓库
3. 完成功能后同步主分支：`unified-ai-cli.bat git sync`
4. 如遇Git问题，使用 `unified-ai-cli.bat git fix` 或紧急修复 `unified-ai-cli.bat git emergency`

### 7.4 性能优化
1. 使用并行执行功能提高效率
2. 避免重复的环境检查和依赖安装
3. 利用缓存机制减少重复操作

## 8. 故障排除

### 8.1 环境问题
- **Node.js未找到**：确保已安装Node.js并添加到PATH
- **Python未找到**：确保已安装Python并添加到PATH
- **pnpm未找到**：运行 `npm install -g pnpm` 安装pnpm

### 8.2 依赖问题
- **依赖安装失败**：尝试删除node_modules目录后重新安装
- **Python依赖问题**：使用 `unified-ai-cli.bat dev setup` 重新设置Python环境

### 8.3 服务启动问题
- **端口被占用**：检查并终止占用端口的进程
- **服务启动失败**：查看相关日志文件获取详细错误信息

### 8.4 测试问题
- **测试失败**：使用 `unified-ai-cli.bat test watch` 定位问题
- **测试超时**：增加测试超时设置或优化被测试代码

## 9. 迁移指南

### 9.1 从旧脚本迁移到CLI
| 旧脚本 | 新CLI命令 |
|--------|-----------|
| tools\start-dev.bat | unified-ai-cli.bat dev start |
| tools\health-check.bat | unified-ai-cli.bat dev health |
| tools\run-backend-tests.bat | unified-ai-cli.bat test run --backend |
| tools\emergency-git-fix.bat | unified-ai-cli.bat git emergency |

### 9.2 向后兼容性
所有旧脚本仍然可用，但建议逐步迁移到新的CLI工具以获得更好的体验。

## 10. 贡献指南

### 10.1 添加新功能
1. 在 `cli/commands/` 目录下创建新的命令模块
2. 实现相应的功能逻辑
3. 在 `cli/main.py` 中注册新命令
4. 更新文档

### 10.2 改进现有功能
1. 查找需要改进的功能模块
2. 实现改进逻辑
3. 充分测试确保兼容性
4. 更新文档和帮助信息

### 10.3 报告问题
1. 使用统一的错误报告格式
2. 提供详细的复现步骤
3. 包含环境信息和日志文件
4. 提交到项目的issue跟踪系统