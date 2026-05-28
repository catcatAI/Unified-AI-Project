# HSP高速同步協議 文檔

## 現況

HSP (High-Speed Synchronization Protocol) 高速同步協議是 Unified AI Project 的核心通信框架，目前已完成實現並處於穩定狀態。它支持內部模塊與外部 AI 實體的可信協作，是系統各組件間通信的基礎設施。

### 實現狀態

- **完成度**: 100%
- **版本**: 1.0.0
- **位置**: `apps/backend/src/core/hsp/`
- **主要文件**: 
  - `connector.py`: HSP連接器實現
  - `performance_optimizer.py`: 性能優化器
  - `types.py`: 協議類型定義

### 核心功能

- **消息傳遞**: 基於MQTT的可靠消息傳遞
- **任務請求與響應**: 標準化的任務請求與結果處理
- **服務發現**: 能力註冊與發現機制
- **性能優化**: 消息壓縮、批處理和緩存
- **容錯機制**: 斷線重連、消息重試和備用協議

### 已實現的特性

- **HSPConnector**: 完整的連接器實現，支持消息發布與訂閱
- **性能優化器**: 實現消息壓縮、緩存和批處理
- **備用協議**: 支持HTTP、文件和內存協議作為備用
- **Web界面集成**: 桌面應用中的HSP任務請求界面

## 設計

### 架構設計

HSP協議採用分層設計，將通信、消息處理和性能優化分離，確保系統的可靠性和可擴展性。

#### 關鍵組件

1. **HSPConnector**
   - 連接管理: 建立和維護MQTT連接
   - 消息發布: 發送任務請求和結果
   - 消息訂閱: 接收和處理消息
   - 錯誤處理: 連接錯誤和消息重試

2. **HSPPerformanceOptimizer**
   - 消息壓縮: 減少網絡帶寬使用
   - 消息緩存: 避免重複處理
   - 批量發送: 提高吞吐量
   - 性能監控: 跟踪消息處理指標

3. **備用協議系統**
   - 協議優先級: 基於可用性和性能的協議選擇
   - 無縫切換: 在主協議失敗時自動切換
   - 健康檢查: 定期檢查協議可用性

### 消息格式

HSP協議使用標準化的消息信封格式，包含以下關鍵字段：

```python
envelope: HSPMessageEnvelope = {
    "hsp_envelope_version": "0.1",
    "message_id": str(uuid.uuid4()),
    "correlation_id": correlation_id,
    "sender_ai_id": self.ai_id,
    "recipient_ai_id": payload.get("requester_ai_id", target_ai_id_or_topic),
    "timestamp_sent": datetime.now(timezone.utc).isoformat(),
    "message_type": "HSP::TaskResult_v0.1",
    "protocol_version": "0.1",
    "communication_pattern": "response",
    "security_parameters": None,
    "qos_parameters": {"requires_ack": False, "priority": "high"},
    "routing_info": None,
    "payload_schema_uri": get_schema_uri("HSP_TaskResult_v0.1.schema.json"),
    "payload": payload
}
```

### 配置系統

HSP協議支持豐富的配置選項，通過YAML配置文件進行管理：

```yaml
# HSP主協議配置
hsp_primary:
  # MQTT配置
  mqtt:
    broker_address: "127.0.0.1"
    broker_port: 1883
    keepalive: 60
    qos_default: 1
    
  # 連接配置
  connection:
    # 連接超時（秒）
    timeout: 10
    # 重連間隔（秒）
    reconnect_interval: 5
    # 最大重連次數
    max_reconnect_attempts: 3
```

## 未來計劃

1. **性能增強**
   - 實現更高效的消息路由算法
   - 優化批處理策略
   - 添加自適應壓縮

2. **安全增強**
   - 實現端到端加密
   - 添加消息簽名和驗證
   - 實現更完善的訪問控制

3. **可擴展性改進**
   - 支持更多備用協議
   - 實現集群模式
   - 添加負載均衡機制

4. **監控與診斷**
   - 實現詳細的性能指標收集
   - 添加可視化監控界面
   - 實現自動診斷和修復機制