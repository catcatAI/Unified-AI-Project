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
  "message_id": "UUID",
  "message_type": "HSP::Fact_v0.1",
  "sender_ai_id": "发送者 DID/URI",
  "recipient_ai_id": "接收者 DID/URI 或主题 URI",
  "payload": { "...": "消息内容" },
  "timestamp_sent": "ISO 8601 UTC",
  "communication_pattern": "publish"
}
```

> 完整欄位定義見 `apps/backend/src/core/hsp/types.py` 的 `HSPMessageEnvelope`。

## 🛠️ 快速使用

### 基本使用

```python
from core.hsp.connector import HSPConnector

# 創建連接（mock_mode=True 可離線測試；fallback 備用協議預設啟用）
connector = HSPConnector(ai_id="my_ai_agent", broker_address="localhost", broker_port=1883)

await connector.connect()
try:
    # 發布意見（publish_opinion 會自動建立 HSPMessageEnvelope 並走 fallback 鏈）
    opinion_payload = {
        "belief_holder_ai_id": "my_ai_agent",
        "justification_type": "text",
        "justification": "根據多次觀測，玩家偏好挖掘直線通道",
    }
    success = await connector.publish_opinion(opinion_payload)
    # 預設 topic：hsp/knowledge/opinions/{ai_id}
finally:
    await connector.disconnect()
```

### 接收消息

```python
# 顯式註冊回調（簽名：payload, sender_ai_id, envelope）
async def handle_task_request(task_payload, sender_ai_id, envelope):
    print(f"收到來自 {sender_ai_id} 的任務：{task_payload.get('request_id')}")

connector.register_on_task_request_callback(handle_task_request)
# 事實訊息同理：connector.register_on_fact_callback(handle_fact)
```

> 其他回調：`register_on_capability_advertisement_callback`、
> `register_on_task_result_callback`、`register_on_acknowledgement_callback`、
> `register_on_connect_callback` 等（見 `core/hsp/connector.py`）。

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

## 歷史 Known Issues（已解決 2026-09-24）

以下三項文檔-代碼不一致已修復，範例已對齊真實 API：

- ✅ Import 路徑：統一為
  `from core.hsp.connector import HSPConnector`（`apps.backend.src.*`
  前綴不匹配運行時包佈局；`EnhancedRovoDevConnector` 已從 `integrations/`
  移除，canonical 連接器為 `core/hsp/connector.py`）。
- ✅ 訊息接收：改為顯式回調註冊（`register_on_*_callback`，簽名
  `(payload, sender_ai_id, envelope)`）；屬性式 `@connector.on_message`
  裝飾器不存在。
- ✅ 訊息結構：示例已改用 `HSPMessageEnvelope`
  真實欄位（`message_id`/`sender_ai_id`/`recipient_ai_id`/`message_type`/`timestamp_sent`/`payload`）。
