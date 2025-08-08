# 實施計畫：移除前端模擬數據並整合真實數據

本計畫旨在逐步移除前端應用程式中的模擬數據，並將其替換為從後端 API 獲取的真實數據。計畫將分為多個階段，涵蓋後端 API 開發、前端數據層重構、組件更新以及測試與優化。

## 現有後端 API 端點

根據對 `main_api_server.py` 和 `api_models.py` 的分析，以下是已識別的現有 API 端點及其功能：

*   `/api/v1/health`: 提供系統健康狀態、服務狀態和性能指標。
*   `/api/v1/chat`: 用於 AI 聊天互動。
*   `/api/v1/session/start`: 用於啟動新的用戶會話。
*   `/api/v1/hsp/services`: 用於列出 HSP（Human-System Partnership）能力。
*   `/api/v1/hsp/tasks`: 用於請求 HSP 任務。
*   `/api/v1/hsp/tasks/{correlation_id}`: 用於檢查 HSP 任務狀態。
*   `/api/atlassian/config`: 用於 Atlassian 配置。
*   `/api/atlassian/test-connection`: 用於測試 Atlassian 連接。
*   `/api/atlassian/confluence/spaces`: 用於獲取 Confluence 空間。
*   `/api/atlassian/confluence/pages`: 用於獲取 Confluence 頁面。
*   `/api/atlassian/confluence/pages/create`: 用於創建 Confluence 頁面。
*   `/api/atlassian/jira/projects`: 用於獲取 Jira 專案。
*   `/api/atlassian/jira/issues`: 用於獲取 Jira 問題。
*   `/api/atlassian/jira/issues/create`: 用於創建 Jira 問題。
*   `/api/atlassian/jira/issues/search`: 用於搜索 Jira 問題。
*   `/api/rovo-dev/status`: 用於獲取 Rovo Dev Agent 狀態。
*   `/api/rovo-dev/tasks`: 用於提交 Rovo Dev Agent 任務。
*   `/api/rovo-dev/tasks/list`: 用於列出 Rovo Dev Agent 任務。
*   `/api/rovo-dev/tasks/history`: 用於獲取 Rovo Dev Agent 任務歷史。
*   `/api/v1/code`: 用於程式碼分析（目前有模擬數據回退）。
*   `/api/v1/image`: 用於圖像生成（目前有模擬數據回退）。
*   `/api/v1/search`: 用於搜索（目前返回模擬搜索結果）。

## 需要新增或擴展的 API 端點

為了完全移除前端的模擬數據，需要新增或擴展以下後端 API 端點：

### 1. 系統監控 (System Monitoring)

*   **擴展 `/api/v1/health`**: 增加更詳細的系統指標和服務狀態。
    *   **`/api/v1/system/services` (GET)**: 獲取所有系統服務的詳細狀態（運行中、停止、錯誤等）。
    *   **`/api/v1/system/metrics/detailed` (GET)**: 獲取詳細的 CPU、記憶體、儲存、網路、溫度等指標。

### 2. AI 代理管理 (AI Agent Management)

*   **`/api/v1/agents` (GET)**: 獲取所有 AI 代理的列表，包括其狀態、能力和任務完成情況。
*   **`/api/v1/agents/{id}` (GET)**: 獲取特定 AI 代理的詳細資訊。
*   **`/api/v1/agents/{id}/action` (POST)**: 對特定 AI 代理執行操作（例如，啟動、停止、重啟）。

### 3. 神經網路監控 (Neural Network Monitoring)

*   **`/api/v1/models` (GET)**: 獲取所有神經網路模型的列表，包括其狀態、準確度、損失、訓練進度等。
*   **`/api/v1/models/{id}/metrics` (GET)**: 獲取特定模型的即時性能指標。
*   **`/api/v1/models/{id}/training` (POST)**: 啟動或停止特定模型的訓練過程。

### 4. 圖像生成歷史 (Image Generation History)

*   **`/api/v1/images/history` (GET)**: 獲取所有已生成圖像的歷史記錄，包括提示、URL、時間戳和大小。
*   **`/api/v1/images/{id}` (DELETE)**: 刪除特定生成的圖像記錄。

## 實施階段與優先級

在開始任何新的開發工作之前，務必首先檢查現有代碼庫中是否已存在類似的功能或端點，以避免重複開發並確保代碼的一致性。

### 階段 1：後端 API 開發 (預計 1-2 天)

*   **優先級：高**
    *   擴展 `/api/v1/health` 以提供更詳細的系統指標。
    *   實現 `/api/v1/system/services` 和 `/api/v1/system/metrics/detailed`。
*   **優先級：中**
    *   實現 `/api/v1/agents`、`/api/v1/agents/{id}` 和 `/api/v1/agents/{id}/action`。
    *   實現 `/api/v1/models`、`/api/v1/models/{id}/metrics` 和 `/api/v1/models/{id}/training`。
*   **優先級：低**
    *   實現 `/api/v1/images/history` 和 `/api/v1/images/{id}` (DELETE)。

### 階段 2：前端數據層重構 (預計 1-2 天)

*   **優先級：高**
    *   創建統一的數據獲取 Hook (例如，`useSystemMetrics`, `useAgents`, `useNeuralNetworks`, `useImageHistory`)。
    *   為所有數據獲取操作實現錯誤處理和加載狀態管理。
    *   將現有的 `useChat()` Hook 調整為統一的數據獲取模式。

### 階段 3：組件更新與模擬數據移除 (預計 2-3 天)

*   **優先級：高**
    *   更新 `SystemMonitor.tsx` 以使用新的系統監控 API。
    *   更新 `DashboardOverview.tsx` 以使用真實的系統指標和服務狀態。
*   **優先級：中**
    *   更新 `AIAgents.tsx` 以使用 AI 代理管理 API。
    *   更新 `NeuralNetwork.tsx` 以使用神經網路監控 API。
*   **優先級：低**
    *   更新 `ImageGeneration.tsx` 以使用圖像生成歷史 API，並移除硬編碼的模擬圖像數據。
    *   更新 `CodeAnalysis.tsx` 以確保其完全依賴 `/api/v1/code` 端點，並移除模擬分析結果回退。
    *   更新 `AIChat.tsx` 以確保其完全依賴 `useChat()` Hook，並移除任何殘留的模擬消息。

### 階段 4：優化與測試 (預計 1-2 天)

*   **優先級：高**
    *   對所有更新的組件進行單元測試和整合測試。
    *   進行性能優化，例如數據緩存和請求去重。
    *   確保錯誤狀態的正確顯示和用戶體驗。

## 總體預計時間：5-9 天

本計畫將確保前端應用程式完全使用真實數據，提升用戶體驗和系統的真實性。