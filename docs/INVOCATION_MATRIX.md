<!--
  =============================================================================
  FILE_PATH: docs/INVOCATION_MATRIX.md
  FILE_TYPE: documentation (invocation single source of truth)
  PURPOSE: 調用矩陣 — 每個模組「怎麼用、配什麼、怎麼驗證」的可查表
  VERSION: 1.0.0
  STATUS: active
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-09-20
  AUDIENCE: users, developers, support
  SYNC: 與 STATUS_MATRIX.md（成熟度，R75 起真相源 status_matrix.yaml）、RELEASE_CRITERIA.md（門檻）配套
  =============================================================================

  維護規則：
  1. 每列的「調用方式」必須實際可執行（本表建立時全列實測過存在）。
  2. 「驗證」欄附指令與最近一次結果；跑不過的列標 ❌ 不得留在表內當可用項。
  3. 新增功能時先補本表再寫 README，防止宣稱漂移（2026-09-20 啟動器覆寫事件教訓）。
-->

# INVOCATION_MATRIX — 調用方式單一真相源

> 目標：實際使用時**照表調用即可，不必改碼**。每列附驗證指令；宣稱與實際脫節時以本表為準並回報。

## 1. 啟動入口（全列實測存在）

| 調用方式                                              | 作用                                                    | 前置配置                                     | 驗證                                                          | 最近驗證   |
| ----------------------------------------------------- | ------------------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------- | ---------- |
| `python scripts/run_angela.py`                        | 統一啟動器：backend＋desktop（793 行，argparse）        | `.env`（可從 `.env.example` 複製）           | 啟動後 `curl localhost:8000/health` → `{"status":"healthy"}`  | 2026-09-20 |
| `python scripts/run_angela.py --api-only`             | 只啟動 backend                                          | 同上                                         | 同上                                                          | 2026-09-20 |
| `python scripts/run_angela.py --desktop-only`         | 只啟動桌面端                                            | 同上                                         | Electron 視窗出現                                             | 2026-09-20 |
| `python scripts/run_angela.py --health-check`         | 健康檢查（不啟動服務）                                  | 無                                           | exit 0                                                        | 2026-09-20 |
| `python quick_start.py`                               | 互動式環境檢查＋啟動嚮導                                | 無                                           | 依提示走完檢查清單                                            | 2026-09-20 |
| `python apps/backend/main.py`                         | 直接啟動 backend（可帶 `--host/--port/--reload`）       | `.env`                                       | `curl localhost:8000/health`                                  | 2026-09-20 |
| `python apps/backend/start_server.py`                 | 最簡 backend（uvicorn 直啟）                            | `.env`                                       | 同上                                                          | 2026-09-20 |
| `python scripts/run_luanti_agent.py`                  | **Luanti 遊戲自主代理**（獨立進程；勿與統一啟動器混淆） | Luanti＋`apps/luanti-mods/agent_poller` 已裝 | agent log `Angela shutdown complete`／遊戲內 `AngelaBot` 動作 | 2026-09-20 |
| `python -m apps.backend.src.cli.repl`（或 `repl.py`） | 終端 REPL 對話                                          | 無（LLM 可選）                               | 互動回應                                                      | 2026-09-20 |

> ⚠️ 歷史教訓（2026-09-20 修復）：`scripts/run_angela.py`
> 曾於工作區被 Luanti 啟動器內容覆寫（16 行），導致 README 宣稱的 `--api-only`
> 失效。已還原 793 行統一啟動器，遊戲代理分離至 `scripts/run_luanti_agent.py`。

## 2. 核心 API（backend 起動後；prefix `/api/v1`）

| 調用                                                           | 作用                                          | 驗證                                             | 最近驗證   |
| -------------------------------------------------------------- | --------------------------------------------- | ------------------------------------------------ | ---------- |
| `GET /health`                                                  | 健康檢查（無需 prefix）                       | `curl :8000/health`                              | 2026-09-20 |
| `GET /api/v1/llm/status`                                       | LLM 後端狀態                                  | `curl :8000/api/v1/llm/status`                   | 2026-09-17 |
| `GET/POST /api/v1/llm/config`                                  | 讀寫偏好模型（`llm.user.yaml` 持久化）        | `pytest tests/api/test_llm_config.py` 12 passed  | 2026-09-17 |
| `POST /api/v1/chat/unified`                                    | 主對話入口（情緒→危機→閘門→Agent→LLM 全管線） | `python scripts/verify_main_flow_e2e.py` → 15/15 | 2026-09-20 |
| `POST /api/v1/session/start`、`POST /api/v1/session/{id}/send` | 對話 session                                  | 同上 e2e 覆蓋                                    | 2026-09-20 |
| `GET /api/v1/context/memory/recent`                            | HAM 真實記憶查詢                              | Dashboard MemoryViewer 走此 API                  | 2026-09-17 |
| `GET /api/v1/ops/status`、`/ops/metrics`                       | 系統指標（psutil 真值）                       | Dashboard SystemMonitor                          | 2026-09-17 |
| `GET /api/v1/system/status/detailed`                           | 系統狀態詳情                                  | `curl :8000/api/v1/system/status/detailed`       | 2026-09-20 |
| `WS /ws`                                                       | WebSocket 對話串流                            | e2e：EXEC/CONFIRM/CONFIRM-EXEC/REJECT 四態       | 2026-09-17 |
| 全表                                                           | `/docs`（FastAPI Swagger）                    | 啟動後瀏覽 `:8000/docs`                          | 2026-09-20 |

## 3. 配置體系（分層，非重複）

| 層         | 檔案                                               | 說明                                                         | 誰在用                             |
| ---------- | -------------------------------------------------- | ------------------------------------------------------------ | ---------------------------------- |
| 底層載入   | `core/system/config/tiered_loader.py`              | YAML 分層合併＋`write_user_config`                           | 上層                               |
| 型別化存取 | `core/config_loader.py`（`AngelaConfig`）          | Authority+Learned 雙層語意、意圖關鍵字、路由政策             | router、chat_service、repl、routes |
| LLM 配置   | `configs/system/llm.default.yaml`＋`llm.user.yaml` | provider/模型/模式（local/cloud）                            | llm_routes、first-run 偵測         |
| 環境變數   | `.env`                                             | 金鑰類（`SECRET_KEY`、`HSP_ENCRYPTION_KEY` 需真 Fernet key） | AuthMiddleware、HSP security       |
| 生命狀態   | `data/autonomous_lifecycle_state.json`             | **跨進程共享**（server↔遊戲 agent；R71c）                    | AutonomousLifeCycle 兩端           |

> 原則：**改配置不踫碼**。使用者配置一律進 `*.user.yaml`／`.env`；
> `*.default.yaml` 是出廠值不可編輯。

## 4. 模組重複度結論（審查紀錄，防再犯）

| 領域        | 結論                                                                                                                      | 證據                                                         |
| ----------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| 配置        | **分層非重複**：tiered_loader（合併）→ config_loader（型別存取）                                                          | 前者被後者 import；消費者清晰                                |
| 記憶        | **分層非重複**：HAM 核心 → 向量適配（chroma/numpy fallback）→ 領域外觀（multimodal/game bridge 橋接 `_ham`）              | `game_memory_bridge` 直呼 `ham.store_experience`，非平行存儲 |
| 情緒        | **三件套分工**：emotion_analyzer（文字辨識）／emotion_system（狀態+行為調整）／emotional_blending（生理混合）             | 各自 docstring＋消費點不同                                   |
| LLM 呼叫    | **兩條路徑，正當分工**：主系統 ModelBus/router（對話、多 provider）；`llm_game_interface`（遊戲 20Hz 直連本地 llama.cpp） | STATUS_MATRIX 缺口 #7 已標記；非疏漏                         |
| 自主性/生命 | **單一實作**（core/life），遊戲 agent import 並跨進程共享狀態                                                             | R71c 修復 save_state 死碼；39 tests                          |
| 沙箱執行    | **單一 gate**：handler 僅可經 ExecutionGate.execute_handler；ModelBus route() 不派發 handler（C3 修復）                   | test_model_bus.py:341 回歸釘死                               |

## 5. 驗證指令速查（發佈前照單全跑）

```bash
# 1. 主流程 e2e（管線+閘門四態）
python scripts/verify_main_flow_e2e.py            # → 15/15

# 2. 確定性 benchmark
python scripts/benchmark_ed3n_garden.py           # → 20/20

# 3. 安全關鍵
python -m pytest tests/services/test_handlers.py \
                 tests/ai/core/test_execution_gate.py \
                 tests/ai/core/test_model_bus.py \
                 tests/security/ -q               # → 全 passed

# 4. 全倉回歸
python -m pytest tests/ -q --timeout=120          # → 5454+ passed, 0 failed

# 5. Lint
python -m flake8 apps/backend/src scripts/run_luanti_agent.py  # 既有基準為準
```

> 維護：任何「照表調用失敗」的情形，先修表或修碼，二選一必須當場收斂——不允許「文件說有、實際要改碼」的狀態過夜。
