# Atlassian API 文档

## 概述

Atlassian API 提供了与 Atlassian 服务（包括 Jira、Confluence 和 Bitbucket）集成的功能。该 API 支持配置管理、状态监控、项目和问题管理、页面创建等功能。

## 基础配置

### 配置 Atlassian 集成

配置 Atlassian 集成需要提供以下信息：

- **domain**: Atlassian 实例的域名（例如：your-domain.atlassian.net）
- **user_email**: 用户邮箱地址
- **api_token**: Atlassian API 令牌
- **cloud_id**: Atlassian Cloud ID

#### 请求示例

```http
POST /api/v1/atlassian/configure
Content-Type: application/json

{
  "domain": "your-domain.atlassian.net",
  "user_email": "user@example.com",
  "api_token": "your-api-token",
  "cloud_id": "your-cloud-id"
}
```

#### 响应示例

```json
{
  "success": true,
  "message": "Atlassian integration configured successfully"
}
```

## 服务状态

### 获取 Atlassian 服务状态

获取当前 Atlassian 服务的连接状态和健康信息。

#### 请求示例

```http
GET /api/v1/atlassian/status
```

#### 响应示例

```json
{
  "connected": true,
  "services": [
    {
      "name": "Confluence",
      "status": "connected",
      "lastSync": "Just now",
      "health": 95
    },
    {
      "name": "Jira",
      "status": "connected",
      "lastSync": "Just now",
      "health": 90
    },
    {
      "name": "Bitbucket",
      "status": "disconnected",
      "lastSync": "Never",
      "health": 0
    }
  ]
}
```

## Confluence 集成

### 获取 Confluence 空间列表

获取所有可用的 Confluence 空间。

#### 请求示例

```http
GET /api/v1/atlassian/confluence/spaces
```

#### 响应示例

```json
{
  "spaces": [
    {
      "id": "12345",
      "key": "SPACEKEY",
      "name": "Space Name",
      "description": "Space description"
    }
  ],
  "count": 1
}
```

### 创建 Confluence 页面

在指定空间中创建新的 Confluence 页面。

#### 请求示例

```http
POST /api/v1/atlassian/confluence/page
Content-Type: application/json

{
  "space_key": "SPACEKEY",
  "title": "Page Title",
  "content": "Page content in storage format"
}
```

#### 响应示例

```json
{
  "success": true,
  "page": {
    "id": "12345",
    "title": "Page Title",
    "space_key": "SPACEKEY"
  }
}
```

### 搜索 Confluence 内容

在 Confluence 中搜索内容。

#### 请求示例

```http
GET /api/v1/atlassian/confluence/search?q=search+query
```

#### 响应示例

```json
{
  "results": [
    {
      "id": "12345",
      "title": "Page Title",
      "excerpt": "Page excerpt...",
      "url": "https://your-domain.atlassian.net/wiki/spaces/SPACEKEY/pages/12345"
    }
  ],
  "count": 1
}
```

## Jira 集成

### 获取 Jira 项目列表

获取所有可用的 Jira 项目。

#### 请求示例

```http
GET /api/v1/atlassian/jira/projects
```

#### 响应示例

```json
{
  "projects": [
    {
      "id": "10000",
      "key": "PROJ",
      "name": "Project Name",
      "description": "Project description"
    }
  ],
  "count": 1
}
```

### 获取 Jira 问题列表

获取 Jira 问题列表，支持 JQL 查询。

#### 请求示例

```http
GET /api/v1/atlassian/jira/issues?jql=project=PROJ&limit=20
```

#### 响应示例

```json
{
  "issues": [
    {
      "id": "10001",
      "key": "PROJ-1",
      "summary": "Issue summary",
      "status": "To Do",
      "assignee": "user@example.com"
    }
  ],
  "count": 1
}
```

### 创建 Jira 问题

创建新的 Jira 问题。

#### 请求示例

```http
POST /api/v1/atlassian/jira/issue
Content-Type: application/json

{
  "project_key": "PROJ",
  "summary": "Issue summary",
  "description": "Issue description",
  "issue_type": "Task"
}
```

#### 响应示例

```json
{
  "success": true,
  "issue": {
    "id": "10001",
    "key": "PROJ-1"
  }
}
```

## Rovo Dev Agents 集成

### 获取 Rovo Dev Agents 列表

获取所有可用的 Rovo Dev Agents。

#### 请求示例

```http
GET /api/v1/atlassian/rovo/agents
```

#### 响应示例

```json
{
  "agents": [
    {
      "id": "agent-1",
      "name": "Code Review Agent",
      "description": "Reviews code for best practices",
      "capabilities": ["code_review", "suggestions"],
      "status": "active"
    }
  ],
  "count": 1
}
```

### 获取 Rovo Dev Tasks 列表

获取所有 Rovo Dev Tasks。

#### 请求示例

```http
GET /api/v1/atlassian/rovo/tasks
```

#### 响应示例

```json
{
  "tasks": [
    {
      "id": "task-1",
      "title": "Review PR #123",
      "description": "Review pull request for new feature",
      "status": "pending",
      "createdAt": "2023-06-15T10:00:00Z",
      "updatedAt": "2023-06-15T10:00:00Z"
    }
  ],
  "count": 1
}
```

### 分配任务给 Agent

将任务分配给指定的 Agent。

#### 请求示例

```http
POST /api/v1/atlassian/rovo/assign
Content-Type: application/json

{
  "task_id": "task-1",
  "agent_id": "agent-1"
}
```

#### 响应示例

```json
{
  "success": true
}
```

## 错误处理

所有 API 端点都遵循标准的 HTTP 状态码：

- **200**: 请求成功
- **400**: 请求参数错误或缺少必要配置
- **401**: 认证失败
- **500**: 服务器内部错误

错误响应格式：

```json
{
  "detail": "Error message"
}
```

## 离线支持

Atlassian API 具有离线支持功能。当网络连接不可用时，API 会将请求排队并在网络恢复时自动同步。