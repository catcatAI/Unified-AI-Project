# Unified AI Project - 开发环境使用指南

本文档详细说明如何设置和使用 Unified AI
Project 的开发环境，解决"执行后能测试，测试后能执行，执行中能测试"的需求。

## 🚀 快速开始

### 1. 环境要求

- **Node.js** >= 18.0.0
- **Python** >= 3.8
- **pnpm** (推荐) 或 npm

### 2. 一键设置

```bash
# 克隆项目后，运行一键设置
pnpm setup
# 或者
node scripts/setup.js
```

这个命令会：

- 检查系统依赖
- 安装所有 Node.js 依赖
- 创建 Python 虚拟环境
- 安装 Python 依赖
- 创建默认配置文件
- 运行健康检查

### 3. Windows 用户

```cmd
# 使用批处理脚本
scripts\\dev.bat install
```

## 📋 可用脚本

### Node.js 脚本 (推荐)

```bash
# 开发环境
pnpm dev              # 启动后端 + 前端
pnpm dev:backend      # 只启动后端
pnpm dev:frontend     # 只启动前端
pnpm dev:desktop      # 只启动桌面应用
pnpm dev:all          # 启动所有组件

# 测试
pnpm test             # 运行所有测试
pnpm test:backend     # 运行后端测试
pnpm test:frontend    # 运行前端测试
pnpm test:desktop     # 运行桌面应用测试
pnpm test:coverage    # 运行测试覆盖率
pnpm test:watch       # 测试监听模式

# 开发 + 测试
pnpm dev-test         # 同时启动开发环境和测试监控

# 端口管理
pnpm port-info        # 显示端口信息
pnpm port-check       # 检查端口是否被占用
pnpm port-kill-service # 终止占用端口的服务

# 工具
pnpm setup            # 项目设置
pnpm health-check     # 健康检查
pnpm clean            # 清理依赖
```

### Windows 批处理脚本

```cmd
# 基本用法
scripts\\dev.bat [action] [option]

# 示例
scripts\\dev.bat install           # 安装依赖
scripts\\dev.bat dev               # 启动开发环境
scripts\\dev.bat dev backend       # 只启动后端
scripts\\dev.bat test              # 运行测试
scripts\\dev.bat test coverage     # 运行测试覆盖率
scripts\\dev.bat dev-test          # 开发 + 测试监控
scripts\\dev.bat stop              # 停止所有服务
```

### PowerShell 脚本 (高级用户)

```powershell
# 使用 PowerShell 脚本获得更多功能
.\\scripts\\dev.ps1 dev -Backend -Watch
.\\scripts\\dev.ps1 test -Coverage
.\\scripts\\dev.ps1 dev-test
```

## 🔄 开发工作流

### 模式 1: 传统开发模式

```bash
# 1. 启动开发环境
pnpm dev

# 2. 在另一个终端运行测试
pnpm test

# 3. 代码修改后重新测试
pnpm test:backend  # 只测试后端
```

### 模式 2: 监听测试模式

```bash
# 启动测试监听模式 - 文件变化自动运行测试
pnpm test:watch
```

### 模式 3: 开发 + 测试一体化 (推荐)

```bash
# 一个命令同时启动开发环境和测试监控
pnpm dev-test
```

这个模式会：

- 启动后端 API 服务器 (localhost:8000)
- 启动前端仪表板 (localhost:3000)
- 启动 ChromaDB 服务器 (localhost:8001)
- 监听文件变化并自动运行相关测试
- 提供实时的测试反馈

### 模式 4: 分离式开发

```bash
# 终端 1: 只启动后端
pnpm dev:backend

# 终端 2: 只启动前端
pnpm dev:frontend

# 终端 3: 测试监控
node scripts/test-watcher.js
```

## 🧪 测试策略

### 测试类型

1. **单元测试**: 测试单个函数/类
2. **集成测试**: 测试组件间交互
3. **端到端测试**: 测试完整用户流程

### 测试配置

#### 后端测试 (pytest)

- 配置文件: `apps/backend/pytest.ini`
- 测试目录: `apps/backend/tests/`
- 覆盖率报告: `apps/backend/htmlcov/`

#### 前端测试 (Jest)

- 配置文件: `apps/frontend-dashboard/jest.config.js`
- 测试目录: `apps/frontend-dashboard/__tests__/`

#### 桌面应用测试 (Jest)

- 配置文件: `apps/desktop-app/jest.config.js`
- 测试目录: `apps/desktop-app/__tests__/`

### 测试最佳实践

```bash
# 运行特定测试
cd apps/backend
source venv/bin/activate  # Linux/Mac
call venv\\Scripts\\activate.bat  # Windows
pytest tests/test_specific.py -v

# 运行标记的测试
pytest -m "not slow"  # 跳过慢测试
pytest -m "integration"  # 只运行集成测试

# 调试模式
pytest --pdb  # 失败时进入调试器
pytest -s     # 显示print输出
```

## 🔧 故障排除

### 常见问题

1. **Python 虚拟环境问题**

   ```bash
   # 重新创建虚拟环境
   cd apps/backend
   rm -rf venv  # Linux/Mac
   rmdir /s venv  # Windows
   python -m venv venv
   # 然后重新运行 pnpm setup
   ```

2. **依赖冲突**

   ```bash
   # 清理并重新安装
   pnpm clean
   pnpm install
   pnpm setup
   ```

3. **端口被占用**

   ```bash
   # 使用端口管理工具
   pnpm port-info                    # 查看所有端口状态
   pnpm port-check 8000             # 检查特定端口
   pnpm port-kill-service BACKEND   # 终止后端服务

   # 或者手动查找占用端口的进程
   netstat -ano | findstr :8000  # Windows
   lsof -i :8000  # Linux/Mac

   # 或者使用不同端口
   uvicorn src.services.main_api_server:app --port 8001
   ```

4. **ChromaDB 连接问题**
   ```bash
   # 手动启动 ChromaDB
   cd apps/backend
   source venv/bin/activate
   python start_chroma_server.py
   ```

### 端口管理策略

项目采用统一的端口管理策略来避免开发过程中的端口冲突问题：

| 服务名称           | 端口号 | 用途说明               |
| ------------------ | ------ | ---------------------- |
| FRONTEND_DASHBOARD | 3000   | 前端仪表板 Web 服务    |
| DESKTOP_APP        | 3001   | 桌面应用 Electron 服务 |
| BACKEND_API        | 8000   | 后端 API 服务          |

项目实现了自动化的端口冲突检测和解决机制，在启动服务之前会自动检测并终止已存在的冲突进程。详细信息请参阅：[端口管理策略](PORT_MANAGEMENT_STRATEGY.md)

### 调试技巧

1. **使用健康检查**

   ```bash
   pnpm health-check
   python scripts/health_check.py
   ```

2. **查看日志**

   ```bash
   # 后端日志 (开发模式会输出到控制台)
   # 前端日志 (浏览器开发者工具)
   ```

3. **测试调试**
   ```bash
   # 后端测试调试
   pytest --pdb -x  # 第一个失败时停止并进入调试器

   # 前端测试调试
   pnpm test --debug
   ```

## 📊 性能监控

开发环境提供了以下监控功能：

1. **API 性能**: 后端自动记录 API 响应时间
2. **测试性能**: 测试运行时间和覆盖率
3. **资源使用**: 内存和 CPU 使用情况
4. **热重载**: 文件变化检测和自动重启

## 🔒 安全注意事项

开发环境配置了基本的安全措施：

1. **CORS**: 允许本地开发端口
2. **环境变量**: 敏感信息使用环境变量
3. **虚拟环境**: Python 依赖隔离
4. **测试隔离**: 测试使用独立的数据库

## 📝 贡献指南

1. **代码规范**: 遵循项目的代码风格
2. **测试覆盖**: 新功能必须有对应测试
3. **文档更新**: 更新相关文档
4. **提交信息**: 使用清晰的提交信息

## 🆘 获取帮助

如果遇到问题：

1. 查看这个文档
2. 运行 `pnpm health-check`
3. 检查项目的 Issues
4. 查看详细的错误日志

---

**Happy Coding! 🎉**
