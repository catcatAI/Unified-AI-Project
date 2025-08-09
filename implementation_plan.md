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

## 實施狀態更新 (2024年1月)

### ✅ 已完成的階段

#### 階段 1：後端 API 開發 (已完成)
*   ✅ **擴展系統監控 API**
    *   實現 `/api/v1/system/metrics/detailed` - 提供詳細的 CPU、記憶體、磁盤、網路、進程和溫度指標
    *   擴展 `/api/v1/health` 端點以支援更詳細的系統狀態
*   ✅ **AI 代理管理 API**
    *   實現 `/api/v1/agents` - 獲取所有 AI 代理列表
    *   實現 `/api/v1/agents/{id}` - 獲取特定代理詳細資訊
    *   實現 `/api/v1/agents/{id}/action` - 代理操作控制
*   ✅ **神經網路監控 API**
    *   實現 `/api/v1/models` - 獲取神經網路模型列表
    *   實現 `/api/v1/models/{id}/metrics` - 模型性能指標
    *   實現 `/api/v1/models/{id}/training` - 訓練狀態監控
*   ✅ **圖像生成歷史 API**
    *   實現 `/api/v1/images/history` - 圖像歷史記錄
    *   實現 `/api/v1/images/{id}` (DELETE) - 圖像刪除
    *   實現 `/api/v1/images/batch-delete` - 批量刪除
    *   實現 `/api/v1/images/statistics` - 圖像統計

#### 階段 2：前端數據層重構 (已完成)
*   ✅ **API 函數庫更新** (`api.ts`)
    *   新增 TypeScript 接口定義 (`DetailedSystemMetrics`, `AIAgent`, `NeuralNetworkModel`, `GeneratedImage` 等)
    *   實現所有新 API 端點的函數
*   ✅ **React Hooks 創建** (`use-api-data.ts`)
    *   `useDetailedSystemMetrics` - 詳細系統指標
    *   `useAIAgents`, `useAgentDetails`, `useAgentAction` - AI 代理管理
    *   `useNeuralNetworkModels`, `useModelMetrics`, `useTrainingStatus` - 神經網路監控
    *   `useImageHistory`, `useDeleteImage`, `useBatchDeleteImages`, `useImageStatistics` - 圖像管理

#### 階段 3：組件更新與模擬數據移除 (已完成)
*   ✅ **系統監控組件** (`system-monitor.tsx`)
    *   集成 `useDetailedSystemMetrics` 和 `useServiceHealth` hooks
    *   添加詳細的 CPU、記憶體、磁盤、網路、進程、溫度監控
    *   實現實時數據刷新和錯誤處理
*   ✅ **AI 代理管理組件** (`ai-agents.tsx`)
    *   使用 `useAIAgents` 和 `useAgentAction` hooks
    *   實現代理操作功能（啟動/停止、配置）
    *   添加加載狀態和錯誤處理
*   ✅ **圖像生成組件** (`image-generation.tsx`)
    *   集成圖像歷史管理 API hooks
    *   添加標籤式界面：生成、歷史、統計
    *   實現圖像選擇、單個和批量刪除功能
*   ✅ **神經網路組件** (`neural-network.tsx`)
    *   使用神經網路監控 API hooks
    *   添加多標籤界面：概覽、模型、指標、訓練
    *   實現模型選擇和詳細指標查看

### 🔧 當前階段：除錯與優化任務

#### 除錯任務清單

##### 1. API 連接測試
*   **任務**: 驗證所有新 API 端點的連接性和回應格式
*   **檢查項目**:
    *   `/api/v1/system/metrics/detailed` 回應格式和數據完整性
    *   `/api/v1/agents` 系列端點的功能性
    *   `/api/v1/models` 系列端點的數據準確性
    *   `/api/v1/images/history` 和相關端點的操作正確性
*   **預期結果**: 所有 API 端點正常回應，數據格式符合前端期望

##### 2. 前端組件功能驗證
*   **任務**: 確保所有更新的組件正確顯示真實數據
*   **檢查項目**:
    *   系統監控頁面顯示實時系統指標
    *   AI 代理頁面正確列出代理狀態和操作
    *   神經網路頁面顯示模型信息和訓練狀態
    *   圖像生成頁面的歷史記錄和統計功能
*   **預期結果**: 所有組件正確渲染，無模擬數據殘留

##### 3. 錯誤處理測試
*   **任務**: 驗證網路錯誤和 API 失敗的處理機制
*   **檢查項目**:
    *   API 請求失敗時的錯誤顯示
    *   加載狀態的正確顯示
    *   重試機制的功能性
    *   降級到模擬數據的回退機制
*   **預期結果**: 優雅的錯誤處理，良好的用戶體驗

##### 4. 性能優化驗證
*   **任務**: 確保數據獲取的效率和用戶體驗
*   **檢查項目**:
    *   API 請求的響應時間
    *   數據緩存機制的有效性
    *   組件重新渲染的優化
    *   記憶體使用情況
*   **預期結果**: 快速響應，流暢的用戶界面

##### 5. 跨瀏覽器兼容性測試
*   **任務**: 確保在不同瀏覽器中的一致性
*   **檢查項目**:
    *   Chrome、Firefox、Safari、Edge 的兼容性
    *   響應式設計在不同屏幕尺寸的表現
    *   JavaScript 功能的跨瀏覽器支援
*   **預期結果**: 所有主流瀏覽器正常運行

### 🚀 執行除錯任務

#### 當前服務器狀態
*   **後端 API 服務器**: 運行在 http://localhost:8000
*   **前端開發服務器**: 運行在 http://localhost:3000

#### 除錯執行計畫
1. **API 端點測試** - 使用 curl 或 Postman 測試所有新端點
2. **前端功能測試** - 在瀏覽器中逐一驗證每個組件
3. **整合測試** - 測試前後端數據流的完整性
4. **性能測試** - 監控響應時間和資源使用
5. **用戶體驗測試** - 模擬真實使用場景

## 總體預計時間：5-9 天 (原計畫) + 1-2 天 (除錯優化)

本計畫將確保前端應用程式完全使用真實數據，提升用戶體驗和系統的真實性。當前階段專注於系統穩定性和性能優化。