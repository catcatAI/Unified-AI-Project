# 統計 API 實現概覽

本文檔概述了統一 AI 專案中統計相關 API 的後端實現和前端使用情況。

## 後端統計 API

後端提供了多個用於獲取系統、模型和圖像統計數據的 API 端點。這些端點主要在 `main_api_server.py` 中實現。

### 系統指標

- **GET /api/v1/system/metrics/detailed**
  - **描述**: 獲取詳細的系統運行指標，例如 CPU 使用率、記憶體使用率、磁碟使用率等。
  - **實現**: 在 `main_api_server.py` 中，此端點會返回模擬數據或從系統監控組件獲取實時數據。

### 模型指標

- **GET /api/v1/models/{model_id}/metrics**
  - **描述**: 獲取特定模型的性能指標，例如訓練進度、準確度、損失等。
  - **實現**: 在 `main_api_server.py` 中，此端點會根據 `model_id` 返回對應模型的模擬指標數據。

### 圖像統計

- **GET /api/v1/images/statistics**
  - **描述**: 獲取圖像相關的統計數據，例如圖像總數、不同類型的圖像數量等。
  - **實現**: 在 `main_api_server.py` 中，此端點會返回模擬數據或從圖像管理服務獲取實際統計數據。

## 前端統計數據使用

前端儀表板 (`frontend-dashboard`) 使用 React Hooks 來消費這些後端統計 API，並在 UI 上展示相關數據。

主要相關文件位於 `d:\Projects\Unified-AI-Project\apps\frontend-dashboard\src` 目錄下。

### Hooks

在 `use-api-data.ts` 中定義了多個用於獲取統計數據的自定義 Hook：

- `useSystemMetrics`: 用於獲取系統指標。
- `useDetailedSystemMetrics`: 用於獲取詳細系統指標。
- `useModelMetrics`: 用於獲取特定模型指標。
- `useImageStatistics`: 用於獲取圖像統計數據。

### UI 組件

這些 Hook 被不同的 UI 組件使用，以在儀表板上展示數據：

- `dashboard-overview.tsx`: 可能會展示系統總體指標。
- `neural-network.tsx`: 可能會展示模型相關的性能指標。
- `image-generation.tsx`: 導入並使用了 `useImageStatistics` Hook，用於展示圖像相關統計。

## CLI 統計功能

CLI 應用程式 (`packages/cli`) 中也包含一些與統計相關的功能，主要用於執行監控和報告。

- `execution_monitor_cli.py`: 包含打印「Execution Statistics」的功能，用於顯示命令執行統計。
- `execution_manager.py`: 包含 `get_execution_statistics` 和 `reset_statistics` 函數，用於管理執行統計數據。

## 總結

統計 API 在後端通過多個 RESTful 端點提供，前端通過 React Hooks 消費這些數據並在儀表板上可視化。CLI 工具也提供了執行統計相關的功能，用於監控和報告。未來可以進一步完善這些 API 的實時數據獲取和更詳細的統計分析功能。