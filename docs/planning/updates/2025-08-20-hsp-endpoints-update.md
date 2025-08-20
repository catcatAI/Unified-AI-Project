# HSP 端點與整合狀態更新（2025-08-20）

本次更新聚焦在後端 HSP 任務請求/狀態查詢端點與現有 HSP 實作的對齊，並梳理整體整合測試尚未通過的區塊與後續落地計畫。

## 已完成的調整

- 統一由 HSPConnector 發送任務請求
  - 端點改為使用 HSPConnector.send_task_request 產生 correlation_id 並透過 MQTT 主題（或 fallback）發送。
  - 正確構造 HSPTaskRequestPayload 與 HSPMessageEnvelope。
- 透過 ServiceDiscovery 解析目標 AI
  - 支援使用 capability_id 解析到實際 target_ai_id（找不到能力時回應 404/對應錯誤）。
- 任務狀態查詢策略
  - 優先從 HAMMemoryManager 查找既有的任務結果（完成/失敗）。
  - 若 HAM 無結果，回退至 DialogueManager 內部追蹤的 pending 狀態。
  - 兩者皆無則回傳未知或過期狀態。
- 相容性修正
  - 將服務可用性判斷從「if not service」改為「if service is None」，避免 MagicMock 在測試中被誤判為 falsy。
  - 修正 HAMMemoryManager 的匯入路徑並補上 uuid 匯入。

## 測試現況

- 服務端點測試：tests/services/test_main_api_server_hsp.py 全數通過。
- HSP 套件與整合測試：tests/hsp 尚有多項失敗（11 失敗 / 14 通過，具體數量以當前分支為準）。主要集中在：
  - 事實（Fact）發佈/訂閱的收斂與回調觸發順序。
  - ServiceDiscovery 能力清單與廣播（Capability Advertisement）在測試環境的資料注入/隔離策略。
  - DialogueManager 內部任務委派與 TaskResult 回流同步路徑尚未完全打通。

## 已作出的設計決策

- Topic 命名與 QoS：
  - 任務請求預設主題 hsp/requests/{recipient_ai_id}，需要 ACK；任務結果 hsp/results/{requester_ai_id}，不強制 ACK。
  - Fact 多為廣播語義，recipient_ai_id 使用 all，qos_parameters.requires_ack=False。
- 服務檢查採用 is None 判斷，以兼容測試替身（MagicMock/AsyncMock）。

## 風險與技術債

- 測試環境內的 HSP 事件流（MQTT 或 fallback/in-memory）行為與真實部署之差異，容易造成 race condition 與時序相關 flakiness。
- ServiceDiscovery 的能力資料來源需要在測試中可注入，否則容易導致「能力不存在」的非功能性失敗。
- DialogueManager 與 HAMMemoryManager 的界面在整合測試中應提供輕量 stub 或 fixture，避免跨模組耦合導致測試難以收斂。

## 下一步優先級（建議）

1) 為 HSPConnector 提供測試用 in-memory pub/sub 模式
- 目標：在無 MQTT 依賴下，可在單測中可靠收發 Fact、TaskRequest、TaskResult、ACK。
- 作法：
  - 啟用 mock_mode 時，InternalBus 或簡化版事件匯流排即時派發訊息至已註冊回調。
  - 對應 publish_message 與 subscribe 的最小行為，確保 on_*_received 能被觸發。

2) ServiceDiscovery 測試資料注入/替身
- 目標：在測試前置步驟主動註冊能力清單或以 fixture 注入靜態能力資料。
- 作法：
  - 提供 add_capability / set_capabilities_for_test 之類 API 或 fixture。
  - 覆寫 find_capabilities/get_all_capabilities 的來源（記憶體而非外部系統）。

3) DialogueManager 與 HSP 任務回路對齊
- 目標：單測內能從任務請求到結果回流，完整經過 DM 的 pending/完成/失敗狀態轉移。
- 作法：
  - 在 DM 增加對 TaskResult 的 in-memory 處理回路與對 HAM 的寫入模擬。
  - 在 tests/hsp 增加對結果回寫/讀取的驗證。

4) HAMMemoryManager 輕量 stub
- 目標：不依賴真實 HAM，即可在測試中查得完成/失敗結果。
- 作法：
  - 提供 set_task_result/get_task_result 的 in-memory 實作（僅於測試使用）。

5) ContentAnalyzerModule 支援 HSP Fact 結構化資料
- 目標：讓 Fact 能在分析模組中被識別並驅動後續決策（如觸發任務或更新狀態）。
- 作法：
  - 增加 Fact schema 映射與欄位解讀邏輯；
  - 在單測中藉由發佈 Fact 驗證模組行為。

## 里程碑與驗收

- M1：HSPConnector 單元測試全部通過（含 in-memory 模式）。
- M2：tests/hsp 中的整合案例大幅收斂（≥ 90% 通過）。
- M3：端到端流程（任務請求 -> 結果回流 -> 狀態查詢）穩定通過，無 flakiness。

## 手動驗證指引（節選）

- 建立 HSP 任務
  - POST /api/v1/hsp/tasks
  - 輸入：capability_id 或 target_ai_id，以及任務參數（parameters）。
  - 成功回應：201 + correlation_id。
- 查詢任務狀態
  - GET /api/v1/hsp/tasks/{request_id}
  - 優先從 HAM 查詢，無結果則返回 pending 或 unknown。

## 附註

- 此更新不涉及前端 UI 變更。
- 若之後需要外部 Broker 或 Fallback 參數化，請整理 .env / config.* 並補充測試專用設定。