# 正式版完成標準 v1（R11）

> 正式版不是版本號，而是交付狀態：所有功能成熟、互無衝突、無異常，
> 實際可用、易用、免維護。PATCH 號誰都能改；此表定義「敢叫正式版」的條件。

## 六維度（皆為必要條件）

| # | 維度 | 正式版門檻 | 驗證方式 | 現況（2026-09-17 R70 重驗） |
|---|------|-----------|---------|-------------------|
| 1 | 功能完整可用 | 每個能力在主流程（對話）真跑通：分類→路由→閘門→執行→回應 | `verify_main_flow_e2e.py` 15/15 exit 0（EXEC/CONFIRM/CONFIRM-EXEC/REJECT 四態，含 task 增查改刪＋search 真搜） | ✅ 15/15（2026-09-17 重跑） |
| 2 | 互無衝突 | 路由/閘門/handler 鍵契約一致；全回歸綠 | 雙向契約測試＋全倉 5442 passed/122 skipped/0 failed＋地圖門 | ✅ 全倉綠（2026-09-17 重驗：**5454 passed**/122 skipped/0 failed，+12 first-run 測試） |
| 3 | 無異常 | 錯誤皆有明確訊息＋正確退出碼；無靜默失敗、無異常逃逸 | 否定/誤判/超時/解析失敗皆有指名回應與測試；`lint:js` 硬失敗已修 | ✅ R3–R12；R70 修 `.env` 佔位符金鑰炸 HSP（5 errors→0）＋first-run 偵測上線 |
| 4 | 實際使用（非模擬） | 訓練/探針數字皆真實更新或真實測量；模擬必須標明或退役 | 學習門（exit 1 若無學習）＋作廢標註＋轉發器 | ✅ R9–R10 |
| 5 | 易用性 | 一命令可跑、可重現；錯誤指引下一步；文檔只寫事實 | e2e/試點皆單命令；confirm/指引訊息；MD 行級事實 | ✅ R70：first-run 偵測＋Dashboard 真實資料＋unsupported/limitations 文檔＋STATUS_MATRIX |
| 6 | 免維護性 | 單一真相源（無鏡像接線）；契約測試鎖邊界；CI 門禁 | handler 註冊複用＋契約測試＋budget/CI jobs；flake8 全倉 0 | ✅ 進行中 |

## 已知缺口（誠實清單，非正式版阻擋即註明）

- COMMAND／設備控制（打開設置／音量）：無 handler，走 agent→LLM（R18 已驗鏈不斷）——**設計內**，正式版需明確為「不支援項」而非沉默。
- 音頻轉錄：agent 已接離線 whisper（R26；無配置即用緩存模型），非語音輸入 whisper 會幻覺（模型已知行為）——轉錄品質另案，鏈路已通。
- 檢索排序品質：DDG 正則失配已修（R29；台北天氣→氣象署／排序教學→官方文檔）；英文 wiki 備援保留（DDG 失敗時）。
- 開放域智能仍依外部／本地 LLM；原生引擎僅確定性＋試點泛化——分數見 INTELLIGENCE_ASSESSMENT（誠實拆分）。
- 地圖 25 檔折疊懸崖：TREND 只認三連升（已註記）。
- 非單調 autosize（如預力窗外）：終驗報錯（已落實）。
- mypy 類型覆蓋債：581 errors（2026-09-17 實測，`mypy apps/backend/src/ --python-version 3.12`） (R87 ensemble -7; R86 audio_encoder_spectral -3; R85 visual_encoder -3; R84 gdrive+selfgen -18; R83 coremodel+diffusion -18; R82 adapter+live2d -20; R81 threshold+agentmgr -22; R80 symbolic+browser -15; R79 heartbeat -11; R78 websocket -11; R77 training_pipeline -15; R76 multimodal_retriever -2; R75 semantic_visual -12; R74 desktop-LLM-persist; R73 neuro_auto_selector -5; R72 action_execution_bridge -5; R71 three_layer_visual -5; R69 primitive_renderer -15; R68 key_manager_gui -13; R67 formula_solver -13; R66 action_executor -16; R65 binary_store -14; R64 body_adapter -6; R63 llm_decision_loop -16; R62 encryption -16; R61 audio_encoder_spectral -12; R60 visual_encoder -7; R59 soul_core -8; R58 desktop_routes -1; R57 repl -8; R56 drive -6; R55 chat_routes -9; R54 dictionary -16; R53 atlassian_api -16; R52 snn_core -16; R50 feedback_loop_engine -17; R48 arithmetic_learner -22; R47 vision_service -22; R46 real_playwright_browser -23; R45 theta_router -31; R44 state_matrix* -13; R43 hsp_connector -27; R42 playground -28; R41 theta_router -31; R40 level5_asi_system -38; R39 state_matrix -36; R38 eta_axis -20; R37 deviation_tracker -28; R36 ethics -35; R35 router -82; R34 1383/R33 1407/R32 1420/R31 1428/R30 持平/R29 持平/R28 1434/R25 1454/R24 1465/R23 1487/R22 1519/R21 1525/R20 1626/R19 1628/R17 1692/R16 1693/R15 1748/R14 1761/曾 2627，內 1028 為包基誤判假簇)——結構性，需多輪分域收斂；`python_version` 保持 3.10（倉庫支援下限），不為降數字而改。
- TS/TSX 無 parser（typescript-eslint 未安裝）：`lint:js` 僅覆蓋 JS；JS 側 0 errors（1348 warnings 既有，不追）。
- JS warnings 1348（多為 no-console）：既有噪聲，不列入門檻；新增代碼不增 warning 為紀律。
- **Web Dashboard 無 React error boundary**：組件崩潰時白屏，無 retry 機制。低優先度，不阻擋正式版。
- **Chat markdown 用 regex 而非 parser**：`ChatPanel.tsx` 用 regex 渲染 bold/code/linebreak，無 `react-markdown` 依賴。Edge case（嵌套 markup、未閉合 code）可能渲染異常。正式版可考慮加 dependency。
- ✅ **Desktop LLM Settings persistence 已落地（R74）**：`GET/POST /api/v1/llm/config` 白名單寫 `llm.user.yaml`（mode/selection/temperature/max_tokens/llm_mode/web_search/memory/max_history/preferred_backend；非法值 400 明確報錯）；router 啟動 honor `settings.preferred_backend`；Settings Save 一併 POST，load 時 GET 預填。重啟生效（`restart_required: true` 誠實返回）。12 tests（`tests/api/test_llm_config.py`）。
- **Dashboard 新面板缺自動化 E2E**：ConfigPanel/ModelSelector/ContextViewer/HealthIndicator 已接 real backend（wired），但缺瀏覽器自動化測試（R70 已解 mock data，E2E 另案）。

## 已解缺口（2026-09-17 R70 對齊輪）

- ✅ **Web Dashboard mock data 已清除**：`pages/api/system/metrics.ts` 改為 proxy → `/api/v1/ops/status`（psutil 真值）；新增 `pages/api/memories.ts` proxy → 新後端 `GET /api/v1/context/memory/recent`（HAM 真實查詢）；`SystemMonitor` 加 disk 列與錯誤提示，`MemoryViewer` 顯示真實記憶＋未初始化/錯誤狀態。
- ✅ **Backend first-run detection 已補**：`core/system/bootstrap/first_run_detection.py`（分類 usable/unreachable_local/blocked_cloud）+ `main.py` lifespan 接線；13 單元測試鎖行為。無可用後端時啟動即 WARN 並附修復指引。
- ✅ **明確不支援項文檔已落地**：`docs/user_guide/unsupported.md`、`docs/architecture/limitations.md`、`docs/user_guide/hardware.md`（此表引用的三處文檔此前不存在）。
- ✅ **`.env` 佔位符金鑰導致 HSP 5 errors + auth 測試環境洩漏**：`HSP_ENCRYPTION_KEY=generate_key` 佔位符使 Fernet 建構炸（stash 驗證為 HEAD 既有，非新引入）；`security.py` 現驗證 key 合法性，佔位符自動回退生成＋明確警告；`.env` 兩個佔位符已換真金鑰（gitignored）。`test_instantiation_with_config` 補 `monkeypatch.delenv("SECRET_KEY")` 修正 env 洩漏造成的隔離缺陷（`main_api_server` 匯入時 `load_dotenv` 會把 `.env` 的 `SECRET_KEY` 帶進 process env，優先序 env>config 為設計，測試未隔離）。
- ✅ **STATUS_MATRIX 建立**：`docs/STATUS_MATRIX.md` 為功能成熟度唯一總表（五級狀態：claimed/implemented/wired/verified/production），淘汰互相矛盾的舊狀態描述。

## 正式版明確不支援項（正式版釋出時必須在文檔中明確列出）

| 項目 | 狀態 | 替代方案 | 文檔位置 |
|------|------|----------|----------|
| COMMAND/設備控制（打開設置、調音量、開關 WiFi 等）| **不支援** | 無 handler，走 agent→LLM 降級 | docs/user_guide/unsupported.md |
| 實時音訊串流輸入/輸出 | **不支援** | 僅支援離線檔案轉錄（whisper） | docs/user_guide/unsupported.md |
| 視頻通話/螢幕共享 | **不支援** | 無相關 handler | docs/user_guide/unsupported.md |
| 多使用者並發會話隔離 | **不支援** | 單用戶架構 | docs/architecture/limitations.md |
| 分散式部署/多節點協同 | **不支援** | 單機部署 | docs/architecture/limitations.md |
| 硬體加速推理（CUDA/ROCm/Metal） | **不支援** | 僅 CPU 推理 | docs/user_guide/hardware.md |
| 自動程式碼生成/修改專案代碼 | **不支援** | 僅支援代碼解析/分析 | docs/user_guide/unsupported.md |
| 資料庫直接操作（SQL 執行） | **不支援** | 僅支援向量/記憶體查詢 | docs/user_guide/unsupported.md |
| 系統級權限操作（sudo、驅動安裝） | **不支援** | 僅用戶空間操作 | docs/user_guide/unsupported.md |

## 迭代規則

每輪至少一個完整階段（研究→修復→驗證→MD→提交）；新缺口先進此表再排期；
任何「看起來完成」必須附真跑證據，否則視為未完成。
