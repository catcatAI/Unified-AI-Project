# Unified AI Project 启动指南

本指南将帮助您启动Unified AI Project的完整服务。

## 系统要求

- Python 3.8 或更高版本
- Node.js 16 或更高版本
- pnpm 包管理器
- Windows、macOS 或 Linux 操作系统

## 安装依赖

### 1. 安装前端依赖

```bash
pnpm install
```

### 2. 安装后端依赖

```bash
cd apps/backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 启动服务

### 方法一：一键启动（推荐）

在项目根目录下执行：

```bash
pnpm dev
```

这将同时启动后端API服务（端口8000）和前端仪表板（端口3000）。

### 方法二：分别启动服务

#### 启动后端服务

```bash
pnpm dev:backend
```

或者直接使用Python：

```bash
cd apps/backend
python -m uvicorn src.services.main_api_server:app --host 127.0.0.1 --port 8000
```

#### 启动前端服务

```bash
pnpm dev:dashboard
```

## 访问应用

启动成功后，您可以访问以下地址：

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 常见问题

### 1. 端口被占用

如果提示端口被占用，可以使用以下命令杀死占用端口的进程：

```bash
# 杀死占用8000端口的进程（后端）
node scripts/port_manager.js kill-service BACKEND_API

# 杀死占用3000端口的进程（前端）
node scripts/port_manager.js kill-service FRONTEND_DASHBOARD
```

### 2. 依赖安装失败

如果依赖安装失败，请尝试：

```bash
# 清理缓存
pnpm clean

# 重新安装
pnpm install

# 安装后端依赖
cd apps/backend
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. 后端服务无法启动

如果后端服务无法启动，请检查：

1. 确保所有依赖已正确安装
2. 检查是否有Python导入错误
3. 确认端口8000未被其他程序占用

### 4. 前端服务无法启动

如果前端服务无法启动，请检查：

1. 确保Node.js和pnpm已正确安装
2. 检查是否有JavaScript错误
3. 确认端口3000未被其他程序占用

## 手动启动脚本

项目提供了几个批处理脚本来帮助您手动启动服务：

- `start_backend.bat` - 启动后端服务
- `start_all.bat` - 启动前后端完整服务

您可以在Windows资源管理器中双击这些文件来启动服务。

## 健康检查

您可以运行健康检查脚本来验证环境配置是否正确：

```bash
python health_check.py
```

这将检查Python版本、依赖安装状态等关键组件。