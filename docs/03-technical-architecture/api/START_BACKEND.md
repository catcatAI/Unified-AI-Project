# 后端服务启动指南

本文档提供了多种启动 Unified AI Project 后端服务的方法，以应对不同环境下的问题。

## 方法一：使用 pnpm 命令（推荐）

```bash
pnpm dev:backend
```

如果此方法无法正常工作，请尝试以下方法。

## 方法二：直接运行 Python 脚本

### 在 PowerShell 中：

```powershell
cd apps\backend
python scripts/smart_dev_runner.py
```

### 在 CMD 中：

```cmd
cd apps\backend
python scripts/smart_dev_runner.py
```

## 方法三：使用 uvicorn 直接启动

### 在 PowerShell 中：

```powershell
cd apps\backend
python -m uvicorn src.services.main_api_server:app --reload --host 127.0.0.1 --port 8000
```

### 在 CMD 中：

```cmd
cd apps\backend
python -m uvicorn src.services.main_api_server:app --reload --host 127.0.0.1 --port 8000
```

## 常见问题排查

### 1. 端口被占用

如果提示端口 8000 被占用，可以：

1. 使用任务管理器结束占用端口的进程
2. 或者修改启动命令中的端口号：
   ```bash
   python -m uvicorn src.services.main_api_server:app --reload --host 127.0.0.1 --port 8001
   ```

### 2. 缺少依赖包

如果提示缺少依赖包，请运行：

```bash
cd apps\backend
pip install -r requirements.txt
```

### 3. PowerShell 执行策略限制

如果在 PowerShell 中遇到执行策略限制，可以：

1. 以管理员身份打开 PowerShell
2. 执行以下命令：
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

## 验证服务是否启动成功

服务启动成功后，可以通过以下方式验证：

1. 访问 http://127.0.0.1:8000/status
2. 访问 http://127.0.0.1:8000/docs 查看 API 文档

如果看到 JSON 格式的响应，说明服务已成功启动。