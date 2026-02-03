# System Integration (系統整合)

## 總覽 (Overview)

`system_integration.py` 模組是 Unified AI 後端系統的核心，包含了 `UnifiedAISystem` 類別。這個類別扮演著整個系統的中樞神經系統，負責初始化、管理所有主要元件，並作為所有外部請求的統一入口點，將請求路由到相應的內部服務。

## 主要職責 (Key Responsibilities)

1.  **元件初始化 (`_initialize_components`)**:
    在系統啟動時，`UnifiedAISystem` 會實例化所有核心 AI 模組、服務、整合工具和安全元件。這確保了所有系統部分都已準備就緒並正確連接。

2.  **生命週期管理 (`start_system` / `stop_system`)**:
    提供統一的方法來安全地啟動和關閉所有被管理的服務。它會按照正確的依賴順序啟動和停止各個元件，以確保系統的穩定性。

3.  **請求路由 (`process_request`)**:
    作為系統的主要進入點，此方法接收所有使用者或外部系統的請求。它會檢查請求的 `type`，並將其分派到對應的內部處理函式。

4.  **安全與審計 (Security & Auditing)**:
    整合了 `AuditLogger` 來記錄所有傳入的操作，並設計了與 `PermissionControlSystem` 的掛鉤點，以在未來實現精細的權限控制。工具執行等敏感操作會透過 `EnhancedSandboxExecutor` 進行隔離。

## 核心元件 (`UnifiedAISystem` Class)

`UnifiedAISystem` 類別在初始化時會載入以下主要系統元件：

- **核心 AI 元件**:
    - `AgentManager`
    - `ExecutionManager`
    - `HAMMemoryManager`
    - `ContinuousLearningManager`
    - `DialogueManager`
- **服務 (Services)**:
    - `MultiLLMService`
    - `AIEditorService`
    - `AIVirtualInputService`
    - `ResourceAwarenessService`
- **整合 (Integrations)**:
    - `EnhancedAtlassianBridge`
    - `RovoDevAgent`
- **安全 (Security)**:
    - `PermissionControlSystem`
    - `AuditLogger`
    - `EnhancedSandboxExecutor`
- **工具 (Tools)**:
    - `ToolDispatcher`

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
