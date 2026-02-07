# System Integration (系統整合)

## 總覽 (Overview)

Unified AI 的後端集成架構由兩個核心組件組成，分別負責 **生命週期管理** 與 **認知執行**：

1.  **`UnifiedAISystem` (`enhanced_system_integration.py`)**: 負責系統啟動、自我維護、健康監控與 API 入口路由。
2.  **`UnifiedControlCenter` (`unified_control_center.py`)**: (Phase 14 新增) 負責 AI 任務的編排、並發執行與代理調度。

## 主要職責 (Key Responsibilities)

### 1. 系統生命週期 (`UnifiedAISystem`)
- **組件初始化**: 啟動 `SystemSelfMaintenanceManager` 等基礎設施。
- **健康監控**: 追蹤系統 Uptime 與健康分數。
- **自動修復**: 觸發緊急維護模式。

### 2. 認知任務編排 (`UnifiedControlCenter`)
- **任務隊列**: 使用 `asyncio.Queue` 緩衝複雜認知任務。
- **並發執行**: 維護 Worker Pool 進行多工處理。
- **HSP 調度**: 透過 HSP 協議將任務分派給專門的 AI 代理 (Agents)。

## 核心元件架構

- **Lifecycle Layer (`UnifiedAISystem`)**:
    - `SystemSelfMaintenanceManager`
    - `AuditLogger`
    - `PermissionControlSystem`

- **Execution Layer (`UnifiedControlCenter`)**:
    - `HSPConnector` (通訊骨幹)
    - `AgentManager` (代理管理)
    - `HAMMemoryManager` (記憶存取)
    - `EconomyManager` (經濟系統)

## 工作流程：請求處理 (Workflow: Request Processing)

1.  一個外部請求被傳遞給 `process_request` 方法。
2.  `AuditLogger` 記錄下這次操作的元資料。
3.  系統檢查請求中的 `type` 欄位 (例如: `"dialogue"`, `"tool_execution"`)。
4.  請求被分派到對應的私有處理方法 (例如: `_handle_dialogue_request`)。
5.  該處理方法呼叫對應的管理器或服務 (例如: `self.dialogue_manager.process_message(...)`) 來執行實際的邏輯。
6.  執行結果被包裝成標準格式並返回。

## 使用範例 (Example Usage)

```python
# 配置日誌
logging.basicConfig(level=logging.INFO)

# 建立並啟動統一 AI 系統
unified_ai = UnifiedAISystem()

try:
    unified_ai.start_system()

    # 處理一個範例請求
    example_request = {
        "type": "dialogue",
        "message": "Hello, how can you help me today?",
        "context": {}
    }
    result = unified_ai.process_request("test_user", example_request)
    print(f"Request result: {result}")

finally:
    unified_ai.stop_system()
```
