# Unified AI Project 端口管理策略

## 概述

Unified AI Project采用统一的端口管理策略，以避免开发过程中的端口冲突问题。该策略通过自动化检测和解决端口冲突，确保开发环境的稳定性和可靠性。

## 端口分配表

| 服务名称 | 端口号 | 用途说明 |
|---------|-------|---------|
| FRONTEND_DASHBOARD | 3000 | 前端仪表板 Web 服务 |
| DESKTOP_APP | 3001 | 桌面应用 Electron 服务 |
| BACKEND_API | 8000 | 后端 API 服务 |

## 端口管理实现

### 1. 端口管理器 (PortManager)

项目实现了统一的端口管理器，位于 `packages/cli/cli/port_manager.py`。该管理器提供了以下功能：

#### 核心功能
- **端口查询**: 获取指定服务的端口号
- **端口占用检测**: 检查端口是否被占用
- **进程查找**: 查找占用指定端口的进程
- **进程终止**: 终止占用端口的进程
- **PID管理**: 保存和加载服务的进程ID

#### 使用方法
```bash
# 查看端口信息
python packages/cli/cli/port_manager.py info

# 检查端口是否被占用
python packages/cli/cli/port_manager.py check 8000

# 终止占用端口的进程
python packages/cli/cli/port_manager.py kill 8000

# 终止指定服务的进程
python packages/cli/cli/port_manager.py kill-service BACKEND_API

# 获取服务端口号
python packages/cli/cli/port_manager.py get-port BACKEND_API
```

### 2. 前端仪表板端口管理

前端仪表板在 `apps/frontend-dashboard/server.ts` 中实现了端口冲突检测和解决机制：

#### 功能特性
- **PID文件管理**: 保存当前进程的PID，便于后续终止
- **端口占用检测**: 启动前检查端口是否被占用
- **进程终止**: 自动终止已存在的冲突进程
- **IP地址优化**: 使用 `127.0.0.1` 而非 `localhost` 提高兼容性

#### 实现细节
```typescript
// 端口配置
const PORT_CONFIG = {
  FRONTEND_DASHBOARD: 3000,
  DESKTOP_APP: 3001,
  BACKEND_API: 8000
};

// 检查并处理已存在的进程
async function handleExistingProcesses(): Promise<void> {
  // 检查PID文件并终止已存在的进程
  // 检查端口占用并终止占用进程
}
```

### 3. 后端服务端口管理

后端服务在 `apps/backend/scripts/smart_dev_runner.py` 中实现了智能端口管理：

#### 功能特性
- **错误检测**: 检测端口占用错误
- **重试机制**: 启动失败时自动重试
- **分层启动**: 按优先级顺序启动服务

#### 实现细节
```python
def detect_dev_errors(stderr_output, stdout_output):
    """检测开发服务器启动错误"""
    errors = []
    # 检测端口占用错误
    if "Address already in use" in full_output:
        errors.append("port_in_use")
    return errors

def start_uvicorn_server(max_retries=3):
    """启动Uvicorn服务器"""
    for attempt in range(max_retries):
        # 启动服务器并处理端口冲突
```

## 端口冲突解决流程

1. **启动前检查**: 服务启动前检查目标端口是否被占用
2. **PID文件检查**: 检查是否存在PID文件，尝试终止已存在的进程
3. **端口扫描**: 使用系统命令扫描占用端口的进程
4. **进程终止**: 终止占用端口的进程，释放端口资源
5. **服务启动**: 在端口释放后启动新服务

## 最佳实践

### 开发环境
- 使用标准端口分配，避免自定义端口
- 启动服务前运行端口检查
- 定期清理PID文件和僵尸进程

### 生产环境
- 使用环境变量配置端口
- 实施端口监控和告警机制
- 建立端口使用文档和规范

## 故障排除

### 常见问题
1. **端口被占用**: 使用端口管理器终止占用进程
2. **PID文件残留**: 手动删除PID文件后重启服务
3. **权限不足**: 以管理员权限运行端口管理命令

### 诊断命令
```bash
# Windows系统查看端口占用
netstat -ano | findstr :8000

# Linux/Mac系统查看端口占用
lsof -i :8000

# 终止进程
taskkill /PID <pid> /F  # Windows
kill -9 <pid>          # Linux/Mac
```

## 未来改进

1. **Web界面管理**: 提供Web界面管理端口和服务
2. **自动分配**: 实现动态端口分配机制
3. **集群支持**: 支持多机器环境的端口管理
4. **监控告警**: 实施端口使用监控和异常告警

---
*最后更新: 2025年9月21日*
*维护者: Unified AI Project Team*