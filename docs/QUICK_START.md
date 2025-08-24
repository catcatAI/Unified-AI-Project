# Unified AI Project - 快速开始指南

欢迎使用 Unified AI Project！本指南将帮助您快速设置和运行项目。

## 🎯 一键开始

### 第一次使用

1. **双击运行** `health-check.bat` - 检查系统环境
2. **双击运行** `start-dev.bat` - 自动设置并启动开发环境
3. **选择菜单选项** 根据需要启动相应服务

### 日常开发

- **环境检查**: 双击 `health-check.bat`
- **开发环境**: 双击 `start-dev.bat`
- **快速测试**: 双击 `quick-test.bat` (推荐，无交互)
- **完整测试**: 双击 `test-runner.bat` (完整功能)

## 📋 批处理脚本说明

### `health-check.bat` - 健康检查
- 检查 Node.js、Python、pnpm 是否已安装
- 检查项目依赖是否已安装
- 检查 Python 虚拟环境和配置文件
- 提供问题解决建议

### `start-dev.bat` - 开发环境
提供以下选项：
1. **启动完整开发环境** - 后端 + 前端
2. **只启动后端** - API 服务器 + ChromaDB
3. **只启动前端** - 仪表板界面
4. **运行测试** - 所有组件的单元测试
5. **运行测试覆盖率** - 生成详细的测试报告
6. **开发 + 测试监控** - 开发环境 + 文件变化自动测试

## 📋 批处理脚本说明

### `health-check.bat` - 健康检查
- 检查 Node.js、Python、pnpm 是否已安装
- 检查项目依赖是否已安装
- 检查 Python 虚拟环境和配置文件
- 提供问题解决建议

### `start-dev.bat` - 开发环境
提供以下选项：
1. **启动完整开发环境** - 后端 + 前端
2. **只启动后端** - API 服务器 + ChromaDB
3. **只启动前端** - 仪表板界面
4. **运行测试** - 所有组件的单元测试
5. **运行测试覆盖率** - 生成详细的测试报告
6. **开发 + 测试监控** - 开发环境 + 文件变化自动测试

### `run-tests.bat` - 测试套件 (推荐)
提供以下选项：
1. **All Tests** - 后端 + 前端 + 桌面应用
2. **Backend Only** - Python pytest
3. **Frontend Only** - Jest 测试
4. **Desktop Only** - Electron 测试
5. **Coverage Reports** - 生成覆盖率报告
6. **Quick Tests** - 跳过标记为 'slow' 的测试，提高测试速度
7. **Watch Mode** - 文件变化时自动运行测试
8. **Exit**

### `quick-test.bat` - 快速测试 (强烈推荐)
- **非交互式**：一键运行，无需选择菜单，避免无限循环问题
- **快速验证**：自动运行所有组件的基础测试
- **清晰反馈**：显示每个组件的测试状态
- **问题诊断**：失败时提供具体的修复建议
- **适用场景**：日常开发验证、CI/CD集成
- **使用方法**：双击运行即可，无需任何交互

### `test-runner.bat` - 高级测试工具 (功能最全)
包含进度条和详细错误处理的完整测试解决方案：
1. **Run All Tests** - 完整测试套件，带进度条
2. **Backend Tests Only** - 详细的后端测试
3. **Frontend Tests Only** - 详细的前端测试
4. **Desktop App Tests Only** - 详细的桌面应用测试
5. **Generate Test Coverage Reports** - 完整覆盖率报告
6. **Quick Tests** - 快速测试模式
7. **Watch Mode** - 持续测试监控
8. **Health Check** - 环境验证
9. **Exit**

🔧 **最新修复**：
- **解决了中文字符编码问题**：改用英文输出，避免 Windows 批处理脚本的编码错误
- **添加了进度条功能**：测试过程更直观，不会出现"一直跑"的情况
- **增强了错误处理**：提供详细的故障排除建议
- **改进了自动回退机制**：pnpm 失败时自动尝试 npm
- **新增了健康检查功能**：快速验证环境状态
- **优化了用户体验**：清晰的步骤提示和结果反馈

## 🌐 服务地址

启动后可以访问：

- **后端 API**: http://localhost:8000
- **前端仪表板**: http://localhost:3000  
- **ChromaDB**: http://localhost:8001
- **API 文档**: http://localhost:8000/docs

## 🔍 测试覆盖率报告

测试覆盖率报告生成位置：
- **后端**: `apps\backend\htmlcov\index.html`
- **前端**: `apps\frontend-dashboard\coverage\index.html`
- **桌面应用**: `apps\desktop-app\coverage\index.html`

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

### 重置项目环境

如果遇到严重问题，可以重置环境：

1. 删除以下文件夹：
   - `node_modules`
   - `apps\backend\venv`
   - `apps\frontend-dashboard\node_modules`
   - `apps\desktop-app\node_modules`

2. 重新运行 `start-dev.bat`

## 🎮 开发工作流

### 推荐工作流：开发 + 测试监控

1. 运行 `start-dev.bat`
2. 选择 "6. 开发 + 测试监控"
3. 系统会启动：
   - 后端 API 服务器
   - 前端开发服务器
   - ChromaDB 数据库
   - 自动测试监控

4. 当您修改代码时：
   - 服务器会自动重载
   - 相关测试会自动运行
   - 测试结果实时显示

### 传统工作流：分离开发和测试

1. 开发时运行 `start-dev.bat` → 选择开发环境
2. 测试时运行 `run-tests.bat` → 选择测试类型
3. 需要时运行 `health-check.bat` 检查环境

## 📝 开发建议

1. **首次设置后**，运行一次完整测试确保环境正常
2. **日常开发**，建议使用"开发 + 测试监控"模式
3. **提交代码前**，运行完整测试套件和覆盖率检查
4. **遇到问题时**，首先运行健康检查

## 🆘 获取帮助

如果遇到问题：
1. 运行 `health-check.bat` 检查环境
2. 查看错误信息和建议
3. 查阅项目文档
4. 检查日志输出

---

**Happy Coding! 🚀**

> 注意：这些批处理脚本设计为在 Windows 环境下使用。如果您使用 macOS 或 Linux，请参考 `DEVELOPMENT_GUIDE.md` 中的 Node.js 和 Shell 脚本说明。