<!--
  =============================================================================
  FILE_PATH: docs/STATUS_MATRIX.md
  FILE_TYPE: status (single source of truth for feature maturity)
  PURPOSE: 唯一狀態總表 — 對齊「宣稱 / 實作 / 已接線 / 可驗證 / 品質達標」
  VERSION: 1.0.0
  STATUS: active
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-09-17
  AUDIENCE: maintainers, auditors, users
  =============================================================================
-->

# STATUS_MATRIX — 功能成熟度唯一總表

> 本檔是功能成熟度的**單一真相源**，取代散落各處、互相矛盾的舊狀態描述。
> 五級狀態定義（取自 2026-09 對齊審查）：`claimed`（宣稱存在）→ `implemented`（程式存在）→ `wired`（生產路徑呼叫）→ `verified`（端到端測試證明）→ `production`（benchmark 達標）。
> 每列必須附驗證指令與日期；無法附者降回 `claimed`。
> 「架構完成度」≠「模型能力完成度」：確定性能力與神經泛化分開計分（見 INTELLIGENCE_ASSESSMENT）。

## 狀態快照（2026-09-17，@ main 工作區）

| 領域 | Claim（宣稱） | Implementation（實作） | 五級狀態 | 驗證指令／證據 | 最後驗證 |
|------|--------------|----------------------|----------|----------------|----------|
| 主流程 e2e | 對話→分類→閘門→執行→回應全通 | `scripts/verify_main_flow_e2e.py` 真接線 | **verified** | `python scripts/verify_main_flow_e2e.py` → 15/15 exit 0 | 2026-09-17 |
| ExecutionGate | 危險操作前需確認／拒絕 | `ai/core/execution_gate.py`（auto/confirm/reject 三態） | **verified** | `pytest tests/ai/core/test_execution_gate.py` 35 passed | 2026-09-17 |
| Tool handlers | 檔案／任務／搜尋 handler 可用 | handlers + gate 註冊複用 | **verified** | `pytest tests/services/test_handlers.py` 55 passed | 2026-09-17 |
| 安全回歸（audit/content/permission） | 0 open alerts 維持 | `tests/security/` | **verified** | `pytest tests/security/` 52 passed | 2026-09-17 |
| First-run 偵測 | 無 LLM 後端時啟動即警告（非沉默） | `core/system/bootstrap/first_run_detection.py` + `main.py` lifespan 接線 | **verified** | `pytest tests/core/system/bootstrap/test_first_run_detection.py` 13 passed；實測分類 unified=可用、ollama=不可達、雲端=被 local mode 擋 | 2026-09-17 |
| 確定性引擎（Math/KB/symbolic） | 數學、知識、符號推理可靠 | MathVerifier、KnowledgeBase、`_solve_transitive`/`_solve_ranking_facts` | **verified**（僅確定性層） | ED3N/GARDEN benchmark 20/20；symbolic 探針 100（確定性路徑） | 2026-09-03 |
| LLM providers | OpenAI/Anthropic/Gemini/Ollama/llama.cpp 可接入 | `services/llm/providers/` + router | **wired** | 配置與路由存在；品質 benchmark 未建立 | 2026-09-17 |
| 多模型路由 | 依任務/硬體/模式自動選後端 | LLMRouter + QueryClassifier + ModelBus + deployment.mode | **wired** | 有架構審計指出的重複分類債（Pipeline vs Router vs ModelBus）；收斂列入待辦 | 2026-09-17 |
| 持續學習（ED3N/GARDEN） | 對話中成長詞彙與權重 | DictionaryLayer.learn、Hebbian、save/load、checkpoint 接線 | **implemented / quality unproven** | 訓練→存檔→門消費已閉環（100K 邊），但可分性負結果已記錄（rank≈隨機） | 2026-09-03 |
| 神經開放域泛化 | —（誠實：低） | FixedSizeCore 等 | **implemented**（0–60% 視指標） | 硬指標探針 symbolic 100 / neural 0；軟硬指標分流已標註 | 2026-09-03 |
| HAM 記憶查詢 | 跨 session 記憶可查 | `ham_manager.query_core_memory` | **verified** | 新 `GET /api/v1/context/memory/recent` 真實查詢；Dashboard MemoryViewer 改接真實資料 | 2026-09-17 |
| Web Dashboard 即時指標 | 系統監控顯示真實狀態 | `pages/api/system/metrics.ts` proxy → `/api/v1/ops/status`（psutil） | **verified**（mock 已移除） | `Math.random()` mock 路由已改 proxy；SystemMonitor 顯示 CPU/Mem/Disk 真值＋錯誤提示 | 2026-09-17 |
| Dashboard 新面板 | Config/Model/Context/Health 可用 | ConfigPanel/ModelSelector/ContextViewer/HealthIndicator + proxy routes | **wired** | 面板接 real backend；E2E 手動驗證待補 | 2026-09-17 |
| 明確不支援項文檔 | 正式版聲明範圍 | `docs/user_guide/unsupported.md`、`docs/architecture/limitations.md`、`docs/user_guide/hardware.md` | **verified** | 文檔存在且與 RELEASE_CRITERIA 同步 | 2026-09-17 |
| HSP 加密金鑰 | 加密可用且啟動不炸 | `core/hsp/security.py` 驗證 Fernet key，佔位符自動回退生成＋警告 | **verified** | `.env` 佔位符 `generate_key` 已致 5 errors → 修復後全綠；`pytest tests/core/hsp/` 通過 | 2026-09-17 |
| 測試品質門 | 全倉綠 | pytest testpaths 全量 | **verified** | `pytest tests/` → **5454 passed, 122 skipped, 0 failed**（2026-09-17 含本輪新增 13） | 2026-09-17 |
| mypy 型別債 | 收斂中 | R80 後 **710 errors**（2026-09-17 實測） | **implemented**（結構性） | 見 RELEASE_CRITERIA mypy 行 | 2026-09-17 |
| flake8 | 0 errors | .flake8 設定 | **verified** | 全倉 0（37 類忽略為已知門檻寬鬆，非隱瞞） | 2026-09-03 |
| 離線能力 | 無 key 可運作（部分） | unified-1g 永遠可用；反射/數學/字典離線 | **wired / partial** | 開放域生成需 LLM；unsupported.md 已聲明邊界 | 2026-09-17 |
| 多模態 | 圖片/音訊/生成 | Vision/Audio/CLIP/GVV 管線 | **implemented** | 真實對比訓練 82% top1（CIFAR 試點）；生成品質未達標 | 2026-09-03 |
| Live2D 具身化 | 桌面互動 | Electron + Cubism + WebSocket | **wired** | 可啟動；狀態鏈完整因果驗證未做 | 2026-09-17 |
| Desktop LLM 設定持久化 | Settings 面板改 backend 設定重啟保留 | `GET/POST /api/v1/llm/config` → `llm.user.yaml`＋router 啟動 honor preferred | **verified** | `pytest tests/api/test_llm_config.py` 12 passed；preferred mock 驗證（honor＋fallback 警告） | 2026-09-17 |

## 誠實缺口（正式版判斷依據）

1. **路由重複決策**（Pipeline/Router/ModelBus 各自分類）— 架構債，最高優先收斂。
2. **學習品質未證明** — 「字典增長」≠「能力增長」；需 hold-out 前後測成為常態門。
3. **Dashboard E2E** — 新面板僅 wired，缺自動化瀏覽器測試。
4. **mypy 710** — 多輪分域收斂進行中（R80；詳見 RELEASE_CRITERIA）。
5. **公開 benchmark** — 確定性能力有腳本級驗證；對外可重現的品質報告尚未發佈。

## 維護規則

- 任何「看起來完成」必須附驗證指令＋日期，否則寫 `claimed`。
- 修復安全相關項目時，同時把 regression payload 加進 `tests/security/` 或對應測試。
- 舊文件與本表衝突時，以本表為準並修訂舊文件。
