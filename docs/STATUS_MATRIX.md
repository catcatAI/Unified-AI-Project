<!--
  本檔由 scripts/gen_status_matrix.py 自 docs/status_matrix.yaml 生成。
  手改會被覆蓋；改狀態請改 YAML 真相源，再重跑生成器。
  真相源：docs/status_matrix.yaml（meta.version=2.0.0）
-->

# STATUS_MATRIX — 功能成熟度唯一總表

> 本檔是**生成視圖**；單一真相源是 [`status_matrix.yaml`](status_matrix.yaml)。五級狀態：`claimed`（宣稱存在）→ `implemented`（程式存在）→ `wired`（生產路徑呼叫）→
> `verified`（端到端測試證明）→ `production`（benchmark 達標）。每列必須附驗證指令與日期；無法附者降回 `claimed`。
> 「架構完成度」≠「模型能力完成度」：確定性能力與神經泛化分開計分（見 INTELLIGENCE_ASSESSMENT）。
> 狀態快照：2026-09-23（由 YAML 同步）。核對：`python scripts/gen_status_matrix.py check`（0 通過 / 1 違規）。

| 領域 | Claim（宣稱） | Implementation（實作） | 狀態 | 驗證指令／證據 | 最後驗證 |
| --- | --- | --- | --- | --- | --- |
| 主流程 e2e | 對話→分類→閘門→執行→回應全通 | `scripts/verify_main_flow_e2e.py` | **verified** | `python scripts/verify_main_flow_e2e.py`；15/15 exit 0 | 2026-09-17 |
| ExecutionGate | 危險操作前需確認／拒絕 | `apps/backend/src/ai/core/execution_gate.py` | **verified** | `pytest tests/ai/core/test_execution_gate.py`；35 passed | 2026-09-17 |
| Tool handlers | 檔案／任務／搜尋 handler 可用 | `apps/backend/src/services/handlers` | **verified** | `pytest tests/services/test_handlers.py`；55 passed | 2026-09-17 |
| 安全回歸（audit/content/permission） | 0 open alerts 維持 | `tests/security` | **verified** | `pytest tests/security/`；52 passed | 2026-09-17 |
| First-run 偵測 | 無 LLM 後端時啟動即警告（非沉默） | `apps/backend/src/core/system/bootstrap/first_run_detection.py`<br>`apps/backend/main.py` | **verified** | `pytest tests/core/system/bootstrap/test_first_run_detection.py`；13 passed；實測分類 unified=可用、ollama=不可達、雲端=被 local mode 擋 | 2026-09-17 |
| 確定性引擎（Math/KB/symbolic） | 數學、知識、符號推理可靠 | `apps/backend/src/services/math_verifier.py` | **verified** | `python scripts/benchmark_ed3n_garden.py`；ED3N/GARDEN benchmark 20/20；symbolic 探針 100（確定性路徑）；僅確定性層 | 2026-09-03 |
| LLM providers | OpenAI/Anthropic/Gemini/Ollama/llama.cpp 可接入 | `apps/backend/src/services/llm/providers`<br>`apps/backend/src/services/llm/router.py` | **wired** | 配置與路由存在；品質 benchmark 未建立 | 2026-09-17 |
| 多模型路由 | 依任務/硬體/模式自動選後端 | `apps/backend/src/ai/core/model_bus.py`<br>`apps/backend/src/ai/core/query_classifier.py`<br>`apps/backend/src/services/llm/router.py` | **wired** | 架構審計指出重複分類債（Pipeline vs Router vs ModelBus）；收斂列入待辦 | 2026-09-17 |
| 持續學習（ED3N/GARDEN） | 對話中成長詞彙與權重 | `apps/backend/src/ai/ed3n/dictionary_layer.py`<br>`apps/backend/src/ai/ed3n/continuous_learning.py` | **implemented** | 訓練→存檔→門消費已閉環（100K 邊），可分性負結果已記錄（rank≈隨機） | 2026-09-03 |
| 神經開放域泛化 | 誠實標示：低 | `apps/backend/src/ai/unified_engine/core_model.py` | **implemented** | 硬指標探針 symbolic 100 / neural 0；0–60% 視指標 | 2026-09-03 |
| HAM 記憶查詢 | 跨 session 記憶可查 | `apps/backend/src/ai/memory/ham_memory/ham_manager.py`<br>`apps/backend/src/api/routes/context_routes.py` | **verified** | `curl -s localhost:8000/api/v1/context/memory/recent`；GET /api/v1/context/memory/recent 真實查詢；Dashboard MemoryViewer 改接真實資料 | 2026-09-17 |
| Web Dashboard 即時指標 | 系統監控顯示真實狀態 | `apps/web-dashboard/src/pages/api/system/metrics.ts` | **verified** | `curl -s http://localhost:8000/api/v1/ops/status`；mock（Math.random）已移除，proxy → /api/v1/ops/status（psutil） | 2026-09-17 |
| Dashboard 新面板 | Config/Model/Context/Health 可用 | `apps/web-dashboard/src/components/ConfigPanel.tsx`<br>`apps/web-dashboard/src/components/ModelSelector.tsx`<br>`apps/web-dashboard/src/components/ContextViewer.tsx`<br>`apps/web-dashboard/src/components/HealthIndicator.tsx` | **wired** | 面板接 real backend；E2E 手動驗證待補 | 2026-09-17 |
| 明確不支援項文檔 | 正式版聲明範圍 | `docs/user_guide/unsupported.md`<br>`docs/architecture/limitations.md`<br>`docs/user_guide/hardware.md` | **verified** | `ls docs/user_guide/unsupported.md docs/architecture/limitations.md docs/user_guide/hardware.md`；三文檔存在且與 RELEASE_CRITERIA 同步 | 2026-09-17 |
| HSP 加密金鑰 | 加密可用且啟動不炸 | `apps/backend/src/core/hsp/security.py` | **verified** | `pytest tests/core/hsp/`；佔位符自動回退生成＋警告；.env 佔位符致 5 errors 已修 | 2026-09-17 |
| 測試品質門 | 全倉綠 | —（見證據欄） | **verified** | `pytest tests/`；5586 passed, 122 skipped, 0 failed（R74 全倉前景） | 2026-09-21 |
| mypy 型別債 | 收斂中（棘輪門鎖定） | `pyproject.toml`<br>`scripts/mypy_budget_gate.py`<br>`scripts/mypy_budget.txt` | **verified** | `python scripts/mypy_budget_gate.py`；門機制可驗證；基線 476（R82 鎖定；歷史 559→540→518→497→R82 三域＋fixture 過寬 mock 根治→476）；新增債 CI 直接紅燈 | 2026-09-22 |
| flake8 | 0 errors | `.flake8` | **verified** | `python -m flake8`；全倉 0（37 類忽略為已知門檻寬鬆，非隱瞞） | 2026-09-03 |
| 離線能力 | 無 key 可運作（部分） | `apps/backend/src/services/llm/providers/unified.py` | **wired** | unified-1g 永遠可用；反射/數學/字典離線；開放域生成需 LLM；unsupported.md 已聲明邊界 | 2026-09-17 |
| 多模態 | 圖片/音訊/生成 | `apps/backend/src/ai/multimodal` | **implemented** | 真實對比訓練 82% top1（CIFAR 試點）；生成品質未達標 | 2026-09-03 |
| Live2D 具身化 | 桌面互動 | `apps/desktop-app` | **wired** | 可啟動；狀態鏈完整因果驗證未做 | 2026-09-17 |
| Desktop LLM 設定持久化 | Settings 面板改 backend 設定重啟保留 | `apps/backend/src/api/routes/llm_routes.py` | **verified** | `pytest tests/api/test_llm_config.py`；12 passed；preferred mock 驗證（honor＋fallback 警告） | 2026-09-17 |
| Luanti 遊戲代理（識別/記憶/自主性/學習） | 能識別環境、記住去過哪、自主探索、行為可訓練 | `apps/backend/src/ai/autonomous/angela_agent.py`<br>`apps/backend/src/ai/multimodal/game_agent.py`<br>`apps/backend/src/ai/multimodal/game_policy.py`<br>`apps/backend/src/ai/multimodal/skill_selector.py`<br>`apps/backend/src/integrations/luanti_connector.py`<br>`scripts/run_luanti_agent.py` | **wired** | R71 識別/記憶/好奇心＋R74 行為克隆訓練閉環（hold-out 學習門、權重持久化、啟動載入、推論信心可觀測）；驗證指令見 INVOCATION_MATRIX（wired 故不列）；live 樣本待玩家在線累積；20 FPS 仍 ❌（10Hz＋2s poller） | 2026-09-21 |
| 基準與驗收 | 可驗證的多後端基準，任何 OpenAI 相容端點可與原生堆疊同資料同比分器互相比較 | `scripts/run_benchmarks.py`<br>`benchmarks/data/native_bench_v1.json` | **verified** | `pytest tests/test_run_benchmarks.py`；22 tests；115 題官方結果 results/bench_20260922-091107.json（native math 80%/knowledge 26.7%/knowledge_mc 97.5%/code 0%/routing 100%；native-max mc 100%）＋--gate-native 回歸門納入 CI，逐題明細可複審 | 2026-09-22 |
| MSBA 語意區塊架構 | 全輸入經 7 層語意區塊處理，融合表示以 NeuroBlender 9D 注入 LLM context | `apps/backend/src/ai/msba/pipeline.py`<br>`apps/backend/src/ai/msba/intra_block_hit.py`<br>`apps/backend/src/ai/msba/multimodal_blocks.py`<br>`apps/backend/src/ai/msba/relevance_convergence.py`<br>`apps/backend/src/ai/msba/block_selector.py` | **wired** | chat_routes Step 2.75 排程、Step 10 消費（50ms 預算）注入 LLM context；Layer 0 接真實 MathVerifier/ED3N 字典（R77 修復死 import）；193 tests；A/B 對照未啟用 | 2026-09-22 |

## Chat Pipeline（主對話管線）

> 入口：`apps/backend/src/api/routes/chat_routes.py`。階段構成為真相源事實；路徑存在性與 wired 由 `check` 核對。

| # | 階段 | 模組 |
| --- | --- | --- |
| 1 | 意圖／複雜度分類 | `apps/backend/src/ai/core/query_classifier.py` |
| 2 | 情緒分析與閾值調整 | `apps/backend/src/services/llm/emotion_analyzer.py` |
| 3 | 危機偵測閘門 | `apps/backend/src/ai/crisis/crisis_system.py` |
| 4 | Level5ASI 對齊檢查 | `apps/backend/src/ai/level5_asi_system.py` |
| 5 | 意圖註冊與路由 | `apps/backend/src/core/intent_registry.py` |
| 6 | 執行權限閘門 | `apps/backend/src/ai/core/execution_gate.py` |
| 7 | 文檔/任務意圖路由 | `apps/backend/src/services/document_router.py` |
| 8 | 模型匯流排（多 provider 呼叫） | `apps/backend/src/ai/core/model_bus.py` |
| 9 | 因果預測注入 | `apps/backend/src/ai/reasoning/causal_reasoning_engine.py` |
| 10 | 記憶查詢與更新 | `apps/backend/src/ai/memory/ham_memory/ham_manager.py`<br>`apps/backend/src/ai/memory/domain_ripple.py` |

## Feature Tree（產品能力樹）

```

- 對話
  - 核心對話（多 provider LLM＋原生引擎 fallback）
  - 情緒與危機（辨識/狀態/閘門）
  - 記憶（HAM/向量/跨 session）
  - MSBA 語意區塊（7 層管線＋NeuroBlender）
- 專業 Agent（11 specialized）
- 多模態（視覺/音訊/生成）
- 具身化（桌面/Live2D/生命週期）
- Luanti 遊戲代理
- 外部整合（Drive/OS 橋）
- 離線原生（ED3N/GARDEN/確定性）
```


## 生命週期（Active / Partial / Planned / Deleted）

| 狀態 | 項目 | 備註 |
| --- | --- | --- |
| ✅ active | Live2D 桌面伴侶 |  |
| ✅ active | Crystal Cards 遊戲 |  |
| 🟡 partial | 遊戲代理 L4（技能學習/策略） | L0-L3 wired；L4 訓練管線通但 live 樣本未累積 |
| 🟡 partial | 圖片生成品質 | 管線通、品質未達標 |
| 🟡 partial | 對外公開 benchmark | 115 題管線、官方數據與 CI 回歸門已建（benchmarks/README.md）；跨 AI 對比待外部 LLM 端點實際接入跑分 |
| 🟡 partial | MSBA 端到端品質驗證（融合品質 benchmark） | 管線與橋接 wired＋193 tests；融合輸出品質未 benchmark，A/B 對照未啟用 |
| 🗓️ planned | 遊戲 20FPS 閉環 | 現 10Hz＋2s poller |
| 🗓️ planned | Dashboard E2E 自動化 |  |
| 🗑️ deleted | Mobile app | Phase 11 刪（骨架；路徑歷史 apps/mobile，非目錄型 token 免掃） |
| 🗑️ deleted | TactileService | Phase 11 刪（無硬體） |
| 🗑️ deleted | ImageGenerationAgent | Phase 9 刪（stub） |
| 🗑️ deleted | ComfyUIClient/AngelaRealPainter | Phase 10 刪（stub） |
| 🗑️ deleted | apps/backend/src/services/wiring.py | Phase 11 刪（死碼） |
| 🗑️ deleted | 11 dead subsystems（learning/ops/dialogue/evaluation/execution/code_inspection/compression/lis/language_models/integration/symbolic_space） | Phase 11b 刪 |
| 🗑️ deleted | 5 dead modules（code_understanding/personality/time/translation/distributed） | Phase 12 刪 |
| 🗑️ deleted | apps/backend/src/ai/trust/ | Phase 12b 刪 |
| 🗑️ deleted | apps/backend/src/ai/security/ | Phase 9 刪 |
| 🗑️ deleted | apps/backend/src/core/card/capabilities/comic_composer.py | Phase 9 刪（佔位 URL） |
| 🗑️ deleted | apps/backend/src/integrations/luanti_bridge.py | R76 刪——三傳輸實驗（UDP/WS/HTTP-polling）敗者，零引用零測試；生產走 luanti_connector（websockets）＋luanti_polling_bridge（HTTP） |
| 🗑️ deleted | apps/backend/src/integrations/luanti_ws_bridge.py | R76 刪——同上，零引用零測試 |
| 🗑️ deleted | apps/backend/src/ai/core/trust_manager.py | R76 刪——Phase 12b Trust 模組的換位復活體（980 行），零生產接線（唯一 import 者為自身測試） |
| 🗑️ deleted | apps/backend/src/core/desktop/tray_manager.py | R76 刪——與桌面端 electron_app/js/tray-manager（生產實際使用的實作）平行重複；Python 版零引用 |
| 🗑️ deleted | apps/backend/src/core/desktop/key_manager_gui.py | R76 刪——僅被已刪的 tray_manager.py 以 subprocess 呼叫；714 行零生產引用 |
| 🗑️ deleted | apps/backend/src/core/ethics/ethics_manager.py | R76 刪——1389 行零生產引用零配置；import 測試轉退役鎖 |
| 🗑️ deleted | apps/backend/src/core/evolution/emergence_engine.py | R76 刪——零引用 |
| 🗑️ deleted | apps/backend/src/core/knowledge/unified_knowledge_graph.py | R76 刪——main.py 明文「UnifiedKnowledgeGraph 桩模块已移除」的復活體（428 行）；真功能在 ai.garden.kg_import 與 ai.meta.knowledge_pipeline |
| 🗑️ deleted | apps/backend/src/core/local_processing.py | R76 刪——38 行零引用（document_router 的同名函數為獨立實作非 import） |
| 🗑️ deleted | apps/backend/src/core/feedback_loop_engine.py | R76 刪——1027 行零生產引用（R72 曾修其 TYPE_CHECKING 死引用，本輪確認整檔無接線） |
| 🗑️ deleted | apps/backend/src/ai/agents/agent_manager_extensions.py | R76 刪——244 行零引用（agent_manager/agent_adapter 為實際實作） |
| 🗑️ deleted | apps/backend/src/ai/context/config.py ＋ exceptions.py ＋ storage/database.py | R76 刪——包內包外均零引用；storage 包（base/disk/memory）健康保留 |
| 🗑️ deleted | apps/backend/src/services/api_models.py | R76 刪——純 re-export 壳（22 行）且零引用；canonical 在 models/api_models.py（basename 豁免） |
| 🗑️ deleted | apps/backend/src/game/widgets.py | R76 刪——14 行共用 widget 零引用 |
| 🗑️ deleted | packages/cli/cli_runner.py | R76 刪——包外層殘留副本（setup.py find_packages 安裝不到）；__main__.py 曾錯誤 import 它致 python -m cli 啟動即炸，已改指 unified_cli.main |

> `deleted` 列表由工具做**防復活門**：同名路徑在磁碟再現即 CI 紅（勿重實作）。

## 誠實缺口（正式版判斷依據）

1. **路由重複決策**（Pipeline/Router/ModelBus 各自分類）— 架構債，最高優先收斂。
2. **學習品質未證明** — 「字典增長」≠「能力增長」；需 hold-out 前後測成為常態門。
3. **Dashboard E2E** — 新面板僅 wired，缺自動化瀏覽器測試。
4. **mypy 540** — 棘輪門鎖定（`scripts/mypy_budget_gate.py`）；新增型別債 CI 直接紅燈。
5. **公開 benchmark** — angela_bench 115 題管線與 CI 回歸門已建（`scripts/run_benchmarks.py --gate-native`）；跨 AI 對比待外部 LLM 端點實際接入跑分。
6. **Luanti policy** — 訓練管線已通（hold-out 學習門鎖測試）；live 樣本待玩家在線累積；20 FPS 仍 ❌（10Hz＋2s poller）。
7. **EmotionSystem 跨進程不共享** — 遊戲 agent 與主 server 生命階段已透過共享 lifecycle JSON 互通（R71c），情緒狀態仍各自 in-memory。

> 調用方式查詢：見 **[`INVOCATION_MATRIX.md`](INVOCATION_MATRIX.md)**。本表答「能不能用、多成熟」；該表答「怎麼用、配什麼、怎麼驗證」。

## 維護規則

- 改狀態**只改 `docs/status_matrix.yaml`**，重跑 `python scripts/gen_status_matrix.py`；手改本檔會被覆蓋。
- 任何「看起來完成」必須附驗證指令＋日期，否則寫 `claimed`。
- YAML 落實體核對：路徑不存在 / verified 無指令 → CI 紅燈；pipeline 階段模組須被生產碼引用（wired）；deleted 項目磁碟復活即紅（防重實作）。
- 修復安全相關項目時，同時把 regression payload 加進 `tests/security/`。
- 舊文件與本表衝突時，以本表為準並修訂舊文件。
