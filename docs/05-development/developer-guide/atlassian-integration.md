# Atlassian 集成开发者指南

## 概述

本文档介绍了如何在 Unified AI Project 中集成和使用 Atlassian 服务。Atlassian 集成提供了与 Jira、Confluence 和 Bitbucket 的连接，支持项目管理、文档协作和代码仓库管理。

## 架构概览

Atlassian 集成采用分层架构设计：

```
前端应用 (React)
    ↓ HTTP API
后端服务 (FastAPI)
    ↓ Atlassian API
Atlassian CLI 桥接器
    ↓ Atlassian CLI (acli)
Atlassian 云服务
```

## 核心组件

### 1. Atlassian CLI 桥接器

位于 `apps/backend/src/integrations/atlassian_cli_bridge.py`，负责与 Atlassian CLI 工具通信。

主要功能：
- 执行 Atlassian CLI 命令
- 解析命令输出
- 处理错误和异常

### 2. 增强版 Atlassian 桥接器

位于 `apps/backend/src/integrations/enhanced_atlassian_bridge.py`，扩展了基础桥接器的功能。

主要功能：
- 集成演示学习管理器
- 支持离线模式
- 提供高级功能接口

### 3. Atlassian API 服务

位于 `apps/backend/src/services/atlassian_api.py`，提供 RESTful API 接口。

主要功能：
- 配置管理
- 状态监控
- 数据操作接口

### 4. 前端 Atlassian API 客户端

位于 `apps/frontend-dashboard/src/lib/atlassian-api.ts`，提供前端与后端服务的通信接口。

主要功能：
- 封装 HTTP 请求
- 处理离线模式
- 提供 React Hook 接口

## 配置要求

### 1. Atlassian CLI 安装

确保系统中已安装 Atlassian CLI 工具：

1. 下载并安装 Atlassian CLI
2. 将 `acli.exe` 添加到系统 PATH 或放置在项目根目录
3. 配置 Atlassian 认证信息

### 2. 环境变量配置

在 `.env` 文件中配置以下环境变量：

```env
ACLIPATH=acli.exe  # Atlassian CLI 路径
```

### 3. Atlassian 认证配置

需要以下认证信息：

- **Domain**: Atlassian 实例域名
- **User Email**: 用户邮箱
- **API Token**: Atlassian API 令牌
- **Cloud ID**: Atlassian Cloud ID

## API 使用指南

### 1. 配置集成

在前端应用中配置 Atlassian 集成：

```typescript
import { useAtlassianApi } from '@/lib/atlassian-api';

const { client } = useAtlassianApi();

const config = {
  domain: 'your-domain.atlassian.net',
  userEmail: 'user@example.com',
  apiToken: 'your-api-token',
  cloudId: 'your-cloud-id'
};

await client.configure(config);
```

### 2. 获取服务状态

```typescript
const status = await client.getStatus();
console.log('Connected:', status.connected);
console.log('Services:', status.services);
```

### 3. 操作 Jira 项目

```typescript
// 获取项目列表
const projects = await client.getJiraProjects();

// 创建新问题
const issue = await client.createJiraIssue('PROJ', 'Issue Summary', 'Issue Description');
```

### 4. 操作 Confluence 页面

```typescript
// 获取空间列表
const spaces = await client.getConfluenceSpaces();

// 创建新页面
const page = await client.createConfluencePage('SPACEKEY', 'Page Title', 'Page Content');
```

## 离线支持

Atlassian 集成支持离线模式，当网络不可用时：

1. 请求会被缓存到本地队列
2. 网络恢复后自动同步
3. 提供离线状态监控

```typescript
// 检查离线状态
const offlineStatus = client.getOfflineStatus();
console.log('Online:', offlineStatus.isOnline);
console.log('Queue size:', offlineStatus.queueSize);
```

## 错误处理

集成提供了完善的错误处理机制：

1. **网络错误**: 自动重试和离线缓存
2. **认证错误**: 提示重新配置
3. **权限错误**: 明确的错误信息
4. **API 错误**: 详细的错误描述

```typescript
try {
  await client.createJiraIssue('PROJ', 'Summary');
} catch (error) {
  console.error('Failed to create issue:', error.message);
}
```

## 测试

### 1. 单元测试

为各个组件编写单元测试：

```python
# backend/tests/integrations/test_atlassian_api.py
def test_atlassian_config_model(self):
    config = AtlassianConfig(
        domain="test.atlassian.net",
        user_email="test@example.com",
        api_token="test_token",
        cloud_id="test_cloud_id"
    )
    assert config.domain == "test.atlassian.net"
```

### 2. 集成测试

测试各组件间的集成：

```python
# backend/tests/integration/test_atlassian_integration.py
def test_configure_atlassian_success(self):
    config = AtlassianConfig(...)
    response = client.post("/api/v1/atlassian/configure", json=config.dict())
    assert response.status_code == 200
```

### 3. 端到端测试

测试完整的用户工作流程：

```python
# tests/e2e/test_atlassian_workflow.py
def test_atlassian_full_workflow(self):
    # 1. 配置集成
    # 2. 检查状态
    # 3. 操作数据
    # 4. 验证结果
```

## 最佳实践

### 1. 性能优化

- 使用缓存减少重复请求
- 批量处理多个操作
- 合理设置超时时间

### 2. 安全性

- 安全存储 API 令牌
- 验证用户输入
- 实施适当的权限控制

### 3. 错误处理

- 提供用户友好的错误信息
- 记录详细的错误日志
- 实现优雅的降级机制

## 故障排除

### 1. Atlassian CLI 未找到

**问题**: 系统提示找不到 `acli.exe`

**解决方案**:
1. 确认 Atlassian CLI 已正确安装
2. 检查 `ACLIPATH` 环境变量配置
3. 将 `acli.exe` 添加到系统 PATH

### 2. 认证失败

**问题**: 配置后仍无法连接 Atlassian 服务

**解决方案**:
1. 验证认证信息是否正确
2. 检查网络连接
3. 确认 Atlassian API 令牌权限

### 3. 离线模式问题

**问题**: 离线操作后数据未同步

**解决方案**:
1. 检查网络连接状态
2. 手动触发同步操作
3. 查看离线队列状态

## 扩展开发

### 1. 添加新功能

要添加新的 Atlassian 功能：

1. 在 `AtlassianCLIBridge` 中实现新的 CLI 命令方法
2. 在 `atlassian_api.py` 中添加相应的 API 端点
3. 在前端 `atlassian-api.ts` 中添加客户端方法
4. 更新前端 UI 组件

### 2. 支持更多 Atlassian 产品

要支持其他 Atlassian 产品（如 Bitbucket）：

1. 在 `AtlassianCLIBridge` 中添加相应的产品命令
2. 在 API 服务中添加新的端点
3. 在前端客户端中添加新的方法
4. 创建对应的前端 UI 组件

## 贡献指南

欢迎贡献代码和改进：

1. Fork 项目仓库
2. 创建功能分支
3. 提交更改和测试
4. 发起 Pull Request

请确保：
- 遵循代码风格指南
- 添加适当的测试
- 更新相关文档
- 通过所有 CI 检查