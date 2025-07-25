# HSP 快速入门指南

## 🚀 什么是 HSP？

**HSP (Heterogeneous Service Protocol)** 是 Unified-AI-Project 的核心通信协议，用于不同服务和代理之间的消息传递。

### 简单理解
- 🔗 **统一通信**: 让所有 AI 代理能够互相"对话"
- 📦 **标准格式**: 定义了消息的标准格式和结构
- 🌐 **跨平台**: 支持不同技术栈的服务互联

## 📋 核心概念

### 1. 消息类型
```
📨 REQUEST  - 请求消息（我需要帮助）
📬 RESPONSE - 响应消息（这是答案）
📢 EVENT    - 事件消息（发生了什么）
⚠️  ERROR    - 错误消息（出现问题）
```

### 2. 基本消息结构
```json
{
  "id": "唯一标识符",
  "type": "消息类型",
  "sender": "发送者ID",
  "receiver": "接收者ID",
  "payload": "消息内容",
  "timestamp": "时间戳"
}
```

## 🛠️ 快速使用

### 发送请求
```python
from src.hsp import HSPConnector

# 创建连接
connector = HSPConnector()
await connector.connect()

# 发送请求
response = await connector.send_request(
    receiver="math_agent",
    payload={"operation": "add", "numbers": [1, 2, 3]}
)
```

### 接收消息
```python
# 设置消息处理器
@connector.on_message
async def handle_message(message):
    if message.type == "REQUEST":
        # 处理请求
        result = process_request(message.payload)
        # 发送响应
        await connector.send_response(message.id, result)
```

## 🔧 常见用例

### 1. 代理间协作
```
用户 → DialogueManager → ProjectCoordinator → 专门代理
```

### 2. 工具调用
```
代理 → ToolDispatcher → 具体工具 → 返回结果
```

### 3. 状态同步
```
任何服务 → 广播事件 → 所有订阅者收到更新
```

## 📚 进一步学习

- **[完整 HSP 规范](./HSP_SPECIFICATION.md)** - 详细的技术规范
- **[代理协作框架](./architecture/AGENT_COLLABORATION_FRAMEWORK.md)** - 代理如何协作
- **[消息传输机制](../technical_specs/MESSAGE_TRANSPORT.md)** - 底层传输实现

## ❓ 常见问题

**Q: HSP 和 HTTP API 有什么区别？**
A: HSP 是异步消息传递，支持事件驱动；HTTP 是同步请求-响应模式。

**Q: 如何调试 HSP 消息？**
A: 使用内置的消息日志功能，所有消息都会被记录。

**Q: HSP 支持哪些传输方式？**
A: 目前主要支持 MQTT，未来会支持更多传输协议。

---

*这是 HSP 的简化入门指南。完整技术细节请参考 [HSP_SPECIFICATION.md](./HSP_SPECIFICATION.md)。*