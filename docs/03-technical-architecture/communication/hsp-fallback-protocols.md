# HSP Fallback協議系統

## 概述

HSP Fallback協議系統為HSP（Heterogeneous Semantic Protocol）提供了強大的備用通訊機制。當主HSP協議（基於MQTT）不可用時，系統會自動切換到備用協議，確保AI代理之間的通訊不會中斷。

## 架構設計

### 核心組件

1. **FallbackProtocolManager**: 管理多個備用協議的核心組件
2. **BaseFallbackProtocol**: 所有備用協議的基類
3. **具體協議實現**:
   - InMemoryProtocol: 內存協議（本地通訊）
   - FileBasedProtocol: 文件協議（跨進程通訊）
   - HTTPProtocol: HTTP協議（網絡通訊）

### 協議優先級

系統按優先級自動選擇最佳可用協議：

1. **HTTP協議** (優先級 3) - 最高優先級
   - 適用於網絡環境
   - 支持跨機器通訊
   - 具有良好的可靠性

2. **文件協議** (優先級 2) - 中等優先級
   - 適用於本地環境
   - 支持跨進程通訊
   - 持久化存儲

3. **內存協議** (優先級 1) - 最低優先級
   - 適用於同進程通訊
   - 最快的通訊方式
   - 無持久化

## 使用方法

### 基本使用

```python
from src.hsp.connector import HSPConnector

# 創建啟用fallback的HSP連接器
connector = HSPConnector(
    ai_id="my_ai_agent",
    broker_address="127.0.0.1",
    broker_port=1883,
    enable_fallback=True  # 啟用fallback協議
)

# 連接（如果HSP失敗，會自動使用fallback）
await connector.connect()

# 發送消息（自動選擇最佳協議）
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

### 狀態監控

```python
# 檢查通訊狀態
status = connector.get_communication_status()
print(f"HSP可用: {status['hsp_available']}")
print(f"Fallback啟用: {status['fallback_enabled']}")
print(f"活動協議: {status['fallback_status']['active_protocol']}")

# 健康檢查
health = await connector.health_check()
print(f"整體健康: {health['overall_healthy']}")
```

### 配置管理

系統支持通過配置文件進行自定義：

```yaml
# configs/hsp_fallback_config.yaml
hsp_fallback:
  enabled: true
  protocols:
    http:
      priority: 3
      host: "127.0.0.1"
      port: 8765
    file:
      priority: 2
      base_path: "data/fallback_comm"
    memory:
      priority: 1
      queue_size: 1000
```

## 消息格式

### FallbackMessage結構

```python
@dataclass
class FallbackMessage:
    id: str                    # 消息唯一標識
    sender_id: str            # 發送者ID
    recipient_id: str         # 接收者ID
    message_type: str         # 消息類型
    payload: Dict[str, Any]   # 消息載荷
    timestamp: float          # 時間戳
    priority: MessagePriority # 優先級
    correlation_id: str       # 關聯ID（可選）
    retry_count: int          # 重試次數
    max_retries: int          # 最大重試次數
    ttl: float               # 生存時間（可選）
```

### HSP消息包裝

當HSP消息通過fallback協議發送時，會被包裝在FallbackMessage中：

```python
fallback_msg = FallbackMessage(
    id=hsp_envelope["message_id"],
    sender_id=hsp_envelope["sender_ai_id"],
    recipient_id=hsp_envelope["recipient_ai_id"],
    message_type="hsp_message",
    payload={
        "topic": mqtt_topic,
        "envelope": hsp_envelope,
        "qos": qos_level
    },
    # ... 其他字段
)
```

## 協議切換機制

### 自動切換

系統會在以下情況自動切換協議：

1. **HSP連接失敗**: 初始連接失敗時切換到fallback
2. **HSP發送失敗**: 消息發送失敗時嘗試fallback
3. **健康檢查失敗**: 定期健康檢查發現問題時切換
4. **協議降級**: 當前協議出現問題時降級到低優先級協議

### 重試機制

```python
# 消息發送重試邏輯
if not success and message.retry_count < message.max_retries:
    message.retry_count += 1
    await asyncio.sleep(1)  # 等待後重試
    await self._select_active_protocol()  # 重新選擇協議
    success = await self.active_protocol.send_message(message)
```

## 性能特性

### 協議性能比較

| 協議 | 延遲 | 吞吐量 | 可靠性 | 適用場景 |
|------|------|--------|--------|----------|
| HSP (MQTT) | 低 | 高 | 高 | 生產環境 |
| HTTP | 中 | 中 | 高 | 網絡環境 |
| File | 高 | 低 | 中 | 本地環境 |
| Memory | 極低 | 極高 | 低 | 同進程 |

### 優化建議

1. **協議選擇**: 根據部署環境選擇合適的fallback協議
2. **消息優先級**: 為重要消息設置高優先級
3. **TTL設置**: 為消息設置合理的生存時間
4. **健康檢查**: 調整健康檢查頻率平衡性能和可靠性

## 故障處理

### 常見問題

1. **所有協議都失敗**
   - 檢查網絡連接
   - 驗證配置文件
   - 查看日誌錯誤信息

2. **消息丟失**
   - 檢查TTL設置
   - 驗證重試配置
   - 確認接收端正常運行

3. **性能問題**
   - 調整協議優先級
   - 優化消息大小
   - 增加並發處理能力

### 調試工具

```python
# 獲取詳細狀態
status = connector.get_communication_status()
for protocol in status['fallback_status']['protocols']:
    print(f"{protocol['name']}: {protocol['stats']}")

# 啟用詳細日誌
import logging
logging.getLogger('src.hsp.fallback').setLevel(logging.DEBUG)
```

## 擴展開發

### 自定義協議

```python
class CustomProtocol(BaseFallbackProtocol):
    def __init__(self):
        super().__init__("custom")
    
    async def initialize(self) -> bool:
        # 初始化邏輯
        pass
    
    async def send_message(self, message: FallbackMessage) -> bool:
        # 發送邏輯
        pass
    
    async def start_listening(self):
        # 監聽邏輯
        pass
    
    async def health_check(self) -> bool:
        # 健康檢查邏輯
        pass

# 註冊自定義協議
manager = get_fallback_manager()
manager.add_protocol(CustomProtocol(), priority=4)
```

### 消息處理器

```python
def custom_message_handler(message: FallbackMessage):
    if message.message_type == "custom_type":
        # 處理自定義消息類型
        process_custom_message(message.payload)

# 註冊處理器
manager.register_handler("custom_type", custom_message_handler)
```

## 最佳實踐

1. **配置管理**: 使用配置文件管理協議參數
2. **監控告警**: 實施協議切換和失敗的監控告警
3. **測試覆蓋**: 測試各種故障場景下的協議切換
4. **文檔維護**: 保持協議使用文檔的更新
5. **性能調優**: 根據實際使用情況調整協議參數

## 總結

HSP Fallback協議系統提供了強大的通訊容錯能力，確保AI代理間的通訊在各種環境下都能保持可靠。通過合理的配置和使用，可以大大提高系統的可用性和穩定性。