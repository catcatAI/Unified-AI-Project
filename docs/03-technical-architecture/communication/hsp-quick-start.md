# HSP 快速入门指南

## 🚀 什么是 HSP？

**HSP (Heterogeneous Service Protocol)**
是 Unified-AI-Project 的核心通信协议，用于不同服务和代理之间的消息传递。

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

### 基本使用

```python
from apps.backend.src.integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector

# 創建連接（啟用fallback協議）
connector = EnhancedRovoDevConnector(
    config={'atlassian': {'api_token': 'your_token', 'user_email': 'your_email', 'domain': 'your_domain'}},
    retry_config=None, # 使用默認重試配置
    endpoint_configs=None # 使用默認端點配置
)
async with connector: # 使用異步上下文管理器
    # 發送事實
    fact_payload = {
        "id": "fact_001",
        "statement_type": "natural_language",
        "statement_nl": "這是一個測試事實",
        "source_ai_id": "my_ai_agent",
        "timestamp_created": "2024-01-01T00:00:00Z",
        "confidence_score": 0.9
    }
    success = await connector.publish_fact(fact_payload, "hsp/knowledge/facts/test")
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

- **[完整 HSP 规范](hsp-specification/01-overview-and-concepts.md)** - 详细的技术规范
- **[代理协作框架](../../04-advanced-concepts/agent-collaboration.md)** - 代理如何协作
- **[消息传输机制](message-transport.md)** - 底层传输实现

## 🛡️ 容錯和備用機制

### Fallback協議支持

HSP現在支持多層級的備用協議，確保通訊不中斷：

```python
# 檢查通訊狀態
status = connector.get_communication_status()
print(f"HSP可用: {status['hsp_available']}")
print(f"活動協議: {status['fallback_status']['active_protocol']}")

# 健康檢查
health = await connector.health_check()
print(f"系統健康: {health['overall_healthy']}")
```

### 協議層級

1. **MQTT (主協議)** - 正常網絡環境
2. **HTTP協議** - 網絡受限環境
3. **文件協議** - 本地環境
4. **內存協議** - 同進程通訊

## ❓ 常見問題

**Q: HSP 和 HTTP API 有什麼區別？** A:
HSP 是異步消息傳遞，支持事件驅動；HTTP 是同步請求-響應模式。

**Q: 如何調試 HSP 消息？** A: 使用內置的消息日誌功能，所有消息都會被記錄。

**Q: HSP 支持哪些傳輸方式？**
A: 主要支持 MQTT，並提供 HTTP、文件、內存等備用協議。

**Q: 如果MQTT連接失敗怎麼辦？** A: 系統會自動切換到備用協議，保證通訊不中斷。

---

_这是 HSP 的简化入门指南。完整技术细节请参考
[HSP 规范](hsp-specification/01-overview-and-concepts.md)。_

## Known Issues（與代碼連結的潛在不一致）

- Import 路徑示例可能不正確：
  - 文檔：`from apps.backend.src.integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector`
  - 代碼現狀：`from src.integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector`
  - 建議：統一為以 `src` 為根的匯入路徑，以匹配運行時包佈局。
- 訊息處理裝飾器示例可能不適用：
  - 文檔示例使用 `@connector.on_message`
    裝飾器；目前後端連接器以回調註冊（例如在 `HSPConnector` 透過
    `register_on_*_callback` 或由 `MessageBridge` 轉發）為主。
  - 建議：將示例改為顯式註冊回調的形式，或連結到實際 API 範例（如
    `HSPConnector.register_on_capability_advertisement_callback(...)`）。
- 訊息結構示例與 HSPMessageEnvelope 欄位命名：
  - 文檔示例使用通用字段（id/type/sender/receiver/timestamp）。實作中
    `HSPMessageEnvelope` 使用例如
    `message_id/sender_id/recipient_id/message_type/timestamp_sent/payload`
    等欄位。
  - 建議：在快速入門中加註對應關係，避免新手混淆。
