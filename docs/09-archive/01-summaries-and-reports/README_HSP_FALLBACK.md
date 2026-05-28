# HSP Fallback協議系統

## 快速開始

HSP Fallback協議系統為HSP通訊提供了強大的備用機制，確保在主協議不可用時仍能維持通訊。

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

# 連接（自動處理fallback）
await connector.connect()

# 發送消息（自動選擇最佳協議）
fact = {
    "id": "fact_001",
    "statement_type": "natural_language",
    "statement_nl": "測試事實",
    "source_ai_id": "my_ai_agent",
    "timestamp_created": "2024-01-01T00:00:00Z",
    "confidence_score": 0.9
}

success = await connector.publish_fact(fact, "hsp/knowledge/facts/test")
```

### 配置文件

在 `configs/hsp_fallback_config.yaml` 中配置：

```yaml
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

### 狀態監控

```python
# 檢查通訊狀態
status = connector.get_communication_status()
print(f"HSP可用: {status['hsp_available']}")
print(f"活動協議: {status['fallback_status']['active_protocol']}")

# 健康檢查
health = await connector.health_check()
print(f"整體健康: {health['overall_healthy']}")
```

## 協議層級

1. **HTTP協議** (優先級3) - 網絡通訊
2. **文件協議** (優先級2) - 本地跨進程
3. **內存協議** (優先級1) - 同進程高速

## 特性

- ✅ 自動協議切換
- ✅ 透明的消息路由
- ✅ 配置驅動的協議管理
- ✅ 完整的狀態監控
- ✅ 重試和容錯機制
- ✅ 性能統計和調試支持

## 示例

運行完整示例：

```bash
cd Unified-AI-Project
python examples/hsp_fallback_example.py
```

## 文檔

詳細文檔請參考：
- [HSP Fallback協議詳細文檔](../03-technical-architecture/communication/hsp-fallback-protocols.md)
- [實現總結](../03-technical-architecture/communication/hsp-fallback-implementation-summary.md)

## 故障排除

常見問題和解決方案請參考文檔中的故障排除章節。

---

**注意**: 這個實現確保了HSP系統在各種環境下的高可用性，為AI代理間的可靠通訊提供了堅實保障。