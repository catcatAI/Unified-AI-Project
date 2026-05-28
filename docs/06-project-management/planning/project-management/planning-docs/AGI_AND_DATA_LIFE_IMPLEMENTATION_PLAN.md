# AGI 與「數據生命」落地實施計劃（Phase Next）

版本：v0.1
日期：2025-08-06
負責：Backend/Architecture 團隊

## 1. 背景與目標

本計劃針對當前專案中與 AGI 能力及「數據生命（Data-as-life）」架構相關的關鍵能力作聚焦落地：
- 建立不中斷運行（熱重載/熱遷移/排水）的演化式系統運維模式。
- 加強觀測性（Observability）與可治理性，讓學習、記憶與通訊可被量化與審計。
- 以語言免疫系統（LIS）為核心，將「異常→對策→成效→升級/淘汰」形成端到端閉環。
- 打造自我改進（Self-improvement）最小演示，將學習回饋與指標提升連動。

## 2. 範圍（Scope）
- 後端 FastAPI（apps/backend）與核心服務（src/core_services）
- 熱端點群（/api/v1/hot/...）與對應服務（HotReloadService、ToolDispatcher、PersonalityManager、HSP/MCP connectors）
- 記憶（HAM）、LIS（incident/antibody）、學習與評估（Evaluator）
- 文檔與測試（docs、tests）

## 3. 交付（Deliverables）
1) 可觀測性擴展：
   - /api/v1/hot/status 回傳更豐富的通訊指標（HSP/MCP）與系統指標（學習/記憶/任務）。
   - 儀表盤/報表結構草案（可先以 JSON 輸出與 log 聚合）。

2) LIS 端到端流程：
   - 異常偵測→incident 入庫→抗體生成/選擇→效果評估→抗體升級/淘汰 的 API/測試樣例。
   - 以 HAM metadata（LIS_* 常量）串接查詢條件（類型/嚴重度/時間窗/標籤）。

3) 自我改進最小演示：
   - 以特定場景（例如指令跟隨/代碼建議）定義 KPI（準確率/成功率/錯誤率）。
   - 實作一個能影響 Trust/策略選擇的簡易學習回饋回路，並於儀表盤展示差異。

4) 文檔與一致性修正：
   - 修正 quick-start 類文檔 import 路徑與回調 API 示例，使與現行代碼一致。
   - 在關鍵文檔中加入「Known Issues」與鏈接治理機制（持續更新）。

5) 測試鞏固：
   - 針對 /api/v1/hot/*、LIS 流程、Evaluator、ServiceDiscovery、TrustManager 增補 smoke/整合測試。

## 4. 工作分解（Workstreams）

### WS-1 可觀測性（Observability）
- 指標擴展：
  - HSP：訊息吞吐（tx/rx/s）、重連次數、最後錯誤時間、能力廣告數、staleness 概況。
  - MCP：同 HSP 指標集合。
  - Learning：當前迴圈學習事件數、最近一次學習時間、Trust 調整次數與最近值。
  - Memory（HAM）：容量、索引項數、最近查詢/命中率（可先 mock）。
  - LIS：近 24h 事件數、抗體使用/新增/淘汰數量、平均效果。
- 輸出：/api/v1/hot/status 增加 metrics 區塊；docs/05-development/hot-reload-and-drain.md 增補欄位說明與樣例。

### WS-2 LIS 端到端
- API/流程：
  - 新增最小異常偵測示例（可先由 ContentAnalyzer/LearningManager 觸發 mock）。
  - HAMLISCache：確立查詢與入庫欄位（已存在常量，補齊缺口）。
  - 效果評估：以 Evaluator 或簡單統計更新 antibody effectiveness。
- 測試：tests/core_ai/lis/* 與整合測試補齊端到端路徑。

### WS-3 自我改進演示（Self-improvement Loop）
- KPI：定義一組可量化的簡化指標（如「回應正確率/錯誤率」或「工具調度成功率」）。
- 策略：將學習回饋（成功/失敗事件）映射到 Trust/路由選擇與工具/LLM 選擇機制。
- 展示：在儀表端點/日誌中呈現前/後差異，並提供範例操作流程。

### WS-4 文檔一致性
- 對齊 import 路徑與 API 示例（特別是 HSP quick-start、fallback 說明）。
- 針對每份關鍵文檔添加「Known Issues」小節並持續更新，直至全部修正。

### WS-5 測試

### WS-6 五方法架構整合（執行+審核、回溯/時待區）
- 審核器（Audit）：對關鍵任務引入二次評估（規則 + 二次模型），可採樣或在高風險場景啟用
- 緩衝回朔（Buffered backtracking）與時待區（Staging area）：在輸出前允許回溯/修正，記錄為新的 policy 事件
- 非同步/事件驅動：以 HSP/DM Hook 串接審核/回朔；可擴展為工作流
- 工具化委派：將計數/視覺等易錯子任務交由專用工具，返回結構化結果
- 指標：正確率、幻覺率、延遲、成功率；/status 暴露 learning.tools 與審核回溯統計
- 增補 /api/v1/hot/* 端點 smoke 測試。
- LIS 端到端管線測試與資料一致性檢查。
- Evaluator 與自我改進 loop 的 KPI 測試（最小集）。

## 5. 里程碑（Milestones）
- M1（~1 週）：/api/v1/hot/status 擴展 + 文檔更新 + smoke 測試。
- M2（~2 週）：LIS 端到端最小流程（API/測試/文檔）。
- M3（~2 週）：自我改進演示（KPI/回饋閉環/可視化）。
- M4（持續）：文檔一致性治理與測試鞏固。

## 6. 驗收標準（Acceptance Criteria）
- /api/v1/hot/status 包含 HSP/MCP/學習/記憶/LIS 指標，文檔與回傳示例一致。
- 可用的 LIS 端到端示例與測試，能觀測到抗體效果變動。
- 有一個最小自我改進示範，能看到指標對比前後差異。
- 主要文檔中「Known Issues」數量下降並關閉。

## 7. 風險與緩解（Risks & Mitigations）
- 指標計算對效能影響：採取抽樣/聚合，或延遲計算；儀表指標先以近似值/估計替代。
- LIS 效果評估資料稀疏：以 mock/回放資料先行，逐步替換為真實事件。
- 自我改進帶來不穩定：在測試/排水模式下切換策略，提供回滾機制（熱重載）。

## 8. 相關文件與代碼對應
- 端點與服務：apps/backend/src/services/main_api_server.py、apps/backend/src/services/hot_reload_service.py
- 觀測：apps/backend/src/hsp/connector.py、apps/backend/src/mcp/connector.py
- 記憶/LIS：apps/backend/src/core_ai/lis/lis_cache_interface.py、apps/backend/src/core_ai/memory/*
- 學習/評估：apps/backend/src/core_ai/learning/*、apps/backend/src/core_ai/evaluation/task_evaluator.py
- 文檔：docs/05-development/hot-reload-and-drain.md、docs/03-technical-architecture/*

## 9. 後續追蹤（Tracking）

## 10. 參考（References）
- CROSS_MODULE_IMPACT_MATRIX.md
- TECHNICAL_ROADMAP.md §2.4/2.5
- PERCEPTION_ACTION_FEEDBACK_PLAN.md
- ROBUSTNESS_AND_SAFETY_HARDENING_PLAN.md
- docs/05-development/observability-guide.md
- docs/05-development/hot-reload-and-drain.md

- 每次合併後刷新 docs/API_ENDPOINTS.md 與儀表欄位說明。
- 在 docs 中保留「Known Issues」清單直到全部修復。
- 於 planning/docs 中每週更新一次進度與指標截圖/JSON 片段。
