# 職權歸屬表：主 AI / 代理 / AI / AL / 記憶 / 系統

> **這份文件是什麼**：執行期的**職權**地圖——每個域是啥、有啥（擁有哪份狀態、哪個決定權）、負責啥、不負責啥、跟鄰居只交換什麼。
>
> **這份文件不是什麼**：不重新定義「能力由什麼承載」（那是
> [`LAYER_SEPARATION.md`](../06-project-management/LAYER_SEPARATION.md) 的五層與
> [`LAYER_REGISTRY.json`](../06-project-management/LAYER_REGISTRY.json)
> 登記簿的地盤）、不重新定義 AL 契約（[`al-engine-contract.md`](al-engine-contract.md)
> §1）、不畫接線（[`ARCHITECTURE_BACKBONE.md`](../architecture/backbone/ARCHITECTURE_BACKBONE.md)）。
>
> - 版本：7.5.0-dev
> - 日期：2026-10-30
> - ANGELA-MATRIX：`[L3] [βγ] [B] [L2]`

---

## 0. 為什麼還要第四張圖

專案同時有四套分類，**各自回答不同的問題**；過去互相串門子，才產生「職責不清」。

| 圖               | 回答的問題                                               | 唯一來源                                                          | 門禁                                                                               |
| ---------------- | -------------------------------------------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| 五層             | 這個**能力**由什麼承載？（刪掉來源還答得出來嗎）         | `LAYER_SEPARATION.md` + `LAYER_REGISTRY.json`                     | `scripts/check_layer_separation.py`（已併入 `check_fact_gates.py` 的 `layers` 域） |
| 三核心           | 這件事活在**哪個時間尺度**？（當下／跨時間／留下的記錄） | `plans/AL_ENGINE_THREE_CORE_PLAN.md` + `al-engine-contract.md` §1 | 契約 §13（目標，尚未建成）                                                         |
| 主幹線           | 模組怎麼**接線**、單例在哪拿                             | `ARCHITECTURE_BACKBONE.md` + `core/backbone/backbone.py`          | —                                                                                  |
| **本表（職權）** | 誰**有權改**哪份狀態、裁哪個決定                         | 本文件                                                            | 見 §5                                                                              |

**橫切第五塊是量測層**（門禁、基準、口徑）：它不是運行時核心，不歸 AI 也不歸 AL（`AL_ENGINE_THREE_CORE_PLAN.md`
§3.1 已裁定），本表 §2.7 單列，避免重演「十一套智能評分」那個病（`ai/meta/intelligence.py`
是唯一定義）。

## 1. 一句話分工

**主 AI 決定「這次說什麼」；代理決定「誰去把它做掉」；AI 層承載能力；AL 層承載時間；記憶層承載記錄；系統層承載運行。**

前三者對後三者只有**讀**的權利（快照／查詢）。要改，就發事件或走唯一寫入口——這是 §4 違規清單的判準，也是「職權是否清晰」的唯一問題。

---

## 2. 六域職權表

### 2.1 主 AI —— 對話裁決主體

| 項         | 內容                                                                                                                                                                                                                                                    |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **是啥**   | 一次使用者請求的裁決主體：分類、路由、要不要執行、怎麼措辭。                                                                                                                                                                                            |
| **有啥**   | ① **分類與路由權** `ai/core/query_classifier.py`、`ai/core/model_bus.py`、`services/llm/router.py`；② **安全裁決權** `ai/core/execution_gate.py`（可逆性×影響×清晰度）；③ **上下文組裝權** `services/llm/prompt_builder.py`、`core/prompt_manager.py`。 |
| **負責**   | 把輸入變成「一次回應 ＋ 至多一個被核准的動作」；把各層快照**讀**進上下文。                                                                                                                                                                              |
| **非職責** | **不擁有長期身份**（AL 錨只讀）；**不存知識**（答案來自記憶／知識／推理層）；**不寫狀態矩陣**；**不發明 AL 狀態**（`al-engine-contract.md` §1.2 第 3 條）。                                                                                             |
| **介面**   | 讀：AL 快照、記憶查詢結果、量測口徑。寫：回應文本、被核准的動作。                                                                                                                                                                                       |
| **實作**   | `api/routes/chat_routes.py` → `services/chat_service.py` → 上列模組。                                                                                                                                                                                   |

### 2.2 代理 —— 執行單元與編排

| 項         | 內容                                                                                                                                                                                                                                                                                                                                               |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **是啥**   | 可被派發、可被編排的執行單元＋編排層。**不是第二個大腦**：它執行已被核准的動作，不裁決內容。                                                                                                                                                                                                                                                       |
| **有啥**   | ① 實例 `ai/agents/base/base_agent.py`、`ai/agents/specialized/`；② 編排與註冊 `ai/agents/agent_manager.py`（`class AgentManager` L272）、`agent_orchestrator.py`、`dynamic_agent_registry.py`、`agent_collaboration_manager.py`；③ 監控 `core/managers/execution_monitor.py`、`system_manager.py`、`dependency_manager.py`；④ 跨進程 `core/hsp/`。 |
| **負責**   | 接收已核准的動作、執行、回報結果與失敗。                                                                                                                                                                                                                                                                                                           |
| **非職責** | 不決定說什麼（主 AI）；不改變 AL 狀態（發事件）；**繞不過 ExecutionGate**。                                                                                                                                                                                                                                                                        |
| **特權**   | **唯一允許的越界寫**：可寫狀態矩陣（見 §4.2——這正是尚未收斂的多寫入者問題）。                                                                                                                                                                                                                                                                      |
| **閘門**   | 單一 owner：`services/execution/gate_execution.py`（「every chat entry point」——chat_routes 之外，REPL／`ChatService.generate_response` 曾完全無閘，該檔 docstring 記錄了這段）。                                                                                                                                                                  |

### 2.3 AI 層 —— 承載能力

| 項         | 內容                                                                                                                                                                                                                                                       |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **是啥**   | 承載「能力」的四層：知識、推理、學習、表層（第五層記憶另列 §2.5）。                                                                                                                                                                                        |
| **有啥**   | 知識 `ai/knowledge_base.py`、`ai/knowledge/wiki_facts.py`；推理 `ai/reasoning/`、`ai/symbolic_reasoner.py`、`services/math_verifier.py`；學習 `ai/garden/`、`ai/ed3n/`、`ai/training/`、`ai/core/training_coordinator.py`；表層 `services/llm/router.py`。 |
| **負責**   | 能回答、能推導、能被教會；每條能力宣稱自帶證據（探針）。                                                                                                                                                                                                   |
| **非職責** | 不寫記憶出處（記憶層）；不算時間漂移（AL）；不裁決執行（主 AI 的 gate）。                                                                                                                                                                                  |
| **判位**   | 用五層那 5 題測驗（刪掉來源還答得出來嗎……），**不要用「它看起來多聰明」判**。                                                                                                                                                                              |

### 2.4 AL 層 —— 承載時間

| 項         | 內容                                                                                                                                                                                                                                         |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **是啥**   | 跨時間演化：時鐘、狀態、轉移、錨（`al-engine-contract.md` §0 的四件事）。                                                                                                                                                                    |
| **有啥**   | `core/life/`（`al_state.py`、`al_memory_policy.py`、`life_essence.py`、`identity_drift.py`、`digital_life_integrator.py`、`autonomous_life_cycle.py`、`heartbeat.py`、`intent_model.py`）、`core/bio/`、快照 `core/engine/state_matrix.py`。 |
| **負責**   | 給定狀態＋事件＋`dt` 算下一個狀態；半衰期／固化／不可逆；身份錨與漂移度量；輸出記憶 retention 策略（**不輸出內容**）；本能驅動（不經 AI）。                                                                                                  |
| **非職責** | 契約 §1.2 六條：不做當下推理、不存知識、不寫 prompt、不直連記憶紀錄、不做表現層、不決定說什麼。                                                                                                                                              |
| **介面**   | AI→AL：模式與目標；AL→AI：身體狀態事件＋**只讀快照**。                                                                                                                                                                                       |
| **現狀**   | 契約狀態 **draft**；§1.2 自承三條邊界「**在今日代碼中全部被違反**」——所以那是**門禁目標**，不是已成立的現狀。                                                                                                                                |

### 2.5 記憶層 —— 承載記錄

| 項         | 內容                                                                                                                                                                          |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **是啥**   | 被時間留下的東西：可歸屬、可更正、有出處的一筆紀錄。                                                                                                                          |
| **有啥**   | `ai/memory/`（`ham_memory/`、`taught_facts.py`、`importance_scorer.py`、`memory_learning.py`）、詞典 `ai/ed3n/dictionary_layer.py`（460K+ 條目）、落盤 `apps/backend/data/`。 |
| **負責**   | 記錄與出處；按 AL 給的 policy 做 retention／decay（**AL 出策略、記憶層執行**）；可撤銷、可過期。                                                                              |
| **非職責** | 不當知識（有公開來源的命題歸 knowledge）；不推理（reasoning）；**不決定我是誰**（錨歸 AL，契約 §6）。                                                                         |
| **判位**   | 來源刪掉就答不出來 → 這是記憶／檢索，**不是學習**（五層第 1 題）。                                                                                                            |

### 2.6 系統層 —— 承載運行

| 項         | 內容                                                                                                                                                                                                                                                                                                                                          |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **是啥**   | 運行底座：進程生命週期、單例、配置、事件匯流排、模組熱插拔、外部閘道。                                                                                                                                                                                                                                                                        |
| **有啥**   | `api/lifespan.py`（生命週期與 `_get_*` 工廠）、`core/backbone/backbone.py`（`get_backbone()`，自述取代 lifespan 約 130 個工廠）、`core/system/`（`state_store/global_store.py` 事件匯流排與全局狀態、`module_manager/`、`config/`、`cluster_manager.py`、`security_monitor.py`）、`core/config` + `configs/`、`services/main_api_server.py`。 |
| **負責**   | 起停與接線；配置優先序（profile → feature → default）；事件投遞；跨模組單例生命週期。                                                                                                                                                                                                                                                         |
| **非職責** | 不承載能力、不裁決內容、不動 AL 語義。                                                                                                                                                                                                                                                                                                        |
| **已判定** | `core/event_loop_system.py` 自稱 DEPRECATED 且**零引用** → 事件走 `GlobalStateStore`（backbone §3.6）；檔案待清。                                                                                                                                                                                                                             |

### 2.7 橫切：量測層（不是第七個運行時核心）

| 項         | 內容                                                                                                                                                                                                             |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **是啥**   | 口徑與證據：定義、門禁、基準、分數。                                                                                                                                                                             |
| **有啥**   | `scripts/check_fact_gates.py`（唯一檢查入口：definitions／layers／intelligence／benchmarks…各域）、`scripts/check_layer_separation.py`、`benchmarks/`、`ai/meta/intelligence.py`、`data/intelligence_reports/`。 |
| **負責**   | 一條宣稱 ＝ 一個定義 ＝ 一個數字 ＝ 一個地方；及格線外接公開基準（`INTELLIGENCE_PASS_CRITERIA.md`）。                                                                                                            |
| **非職責** | 不是運行時核心、不歸 AI 也不歸 AL；**任何一域都不得為了過門禁去調口徑**。                                                                                                                                        |

---

## 3. 對照表：本表 × 三核心 × 五層 × 主幹線

這張表就是 `AL_ENGINE_THREE_CORE_PLAN.md` §3.2 要求的「對齊聲明」——
**knowledge 層不屬於三分法的「記憶」，surface 層不屬於「AI 的推理」，代理不屬三分法。**

| 本表域 | 三核心                   | 五層                                       | 主幹線角色                      | 代表模組                                                     |
| ------ | ------------------------ | ------------------------------------------ | ------------------------------- | ------------------------------------------------------------ |
| 主 AI  | AI（當下）               | 表層 + 讀其他層                            | 上層（讀快照）＋下層入口        | `chat_routes` / `chat_service` / `router` / `execution_gate` |
| 代理   | **不屬三分法**（執行體） | —                                          | 下層（外部閘道 `external.py`）  | `ai/agents/*`、`core/managers/*`、`core/hsp/`                |
| AI 層  | AI                       | knowledge / reasoning / learning / surface | 字典與模組註冊                  | `ai/{knowledge,reasoning,garden,ed3n}`                       |
| AL 層  | AL                       | —（**不承載能力**）                        | 矩陣與座標軸                    | `core/life`、`core/bio`、`state_matrix`                      |
| 記憶層 | 記憶                     | memory                                     | 記憶登錄器 `backbone/memory.py` | `ai/memory/*`                                                |
| 系統層 | **不屬三分法**（底座）   | —                                          | 上／中／下層本體                | `core/system`、`core/backbone`、`api/lifespan`               |
| 量測層 | **橫切**（§3.1 裁定）    | 全部的裁判                                 | —                               | `check_fact_gates`、`benchmarks`                             |

---

## 4. 已知違規與含混（帶狀態）

| #   | 事項                                                                                                                                                           | 證據                                                            | 狀態                                                                                                                                                                                                                                                                             |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 4.1 | 三核心／五層／職權三套分類各說各話                                                                                                                             | `AL_ENGINE_THREE_CORE_PLAN.md` §3.2 自承                        | **已解**——§3 對照表；三者問題不同，不互斥                                                                                                                                                                                                                                        |
| 4.2 | **狀態矩陣多寫入者**：`agent_manager` / DLI / `state_matrix_api` 三處 + 兩處直接 mutation（`math_ripple_engine` L460-475、911-922；`domain_ripple` L149、239） | `ARCHITECTURE_BACKBONE.md` §11.3 #5                             | **未解**——唯一寫入口未收斂；本表判準：只有 AL 能改狀態語義，其餘走事件                                                                                                                                                                                                           |
| 4.3 | 記憶 4+ 實例（HAM）                                                                                                                                            | 同上 §11.3 #2                                                   | **部分解**——backbone `memory` 登記已建，殘餘實例待盤                                                                                                                                                                                                                             |
| 4.4 | 幽靈指標：`update_zeta()` 零生產呼叫、`η.structural_drift` 恆為 0、`find_drift()` 只有測試呼叫、情緒不跨重啟、`data/state/` 為空                               | `AL_ENGINE_THREE_CORE_PLAN.md` §3.4；`ISSUES_2026-10-29.md` §六 | **待裁決**（屬 AL 主線 Phase 3）                                                                                                                                                                                                                                                 |
| 4.5 | 兩套同名成熟度階梯 L0–L11（`core/maturity/` vs 前端 `maturity-tracker.js`）                                                                                    | `AL_ENGINE_THREE_CORE_PLAN.md` §3.3                             | **待裁決**：接線或刪除                                                                                                                                                                                                                                                           |
| 4.6 | `core/event_loop_system.py` DEPRECATED、零引用                                                                                                                 | `ARCHITECTURE_BACKBONE.md` §11.2                                | **已判定**走 `GlobalStateStore`；檔案待清。2026-10-30 補驗：**生產零引用成立，但不是全倉零引用**——3 個測試檔 import 它（`tests/unit/test_smoke_imports.py`、`tests/core/test_smoke_core.py`、`tests/core/test_event_queue_deferred.py`），清檔要連測試一起裁決，不能當孤兒直接刪 |
| 4.7 | ExecutionGate 曾有兩條入口（REPL／ChatService 完全無閘，模型回「Done!」但動作沒發生）                                                                          | `services/execution/gate_execution.py` docstring                | **已解**——單一 owner                                                                                                                                                                                                                                                             |
| 4.8 | AL 契約 §1.2 三條邊界「今日代碼全部被違反」                                                                                                                    | 契約自述                                                        | **門禁目標**，非現狀（別當成已成立）                                                                                                                                                                                                                                             |     | 4.9 | 幽靈指標以外，`chat_routes` 摘除 `structural_drift` 後 ζ 的其他讀點（`websocket_manager` / `system_routes` / `composer`）是否仍找舊鍵 | `ISSUES_2026-10-29.md` §六 | **已驗，無殘留**（2026-10-30）：`websocket_manager` / `composer` 全檔無 `zeta`／`drift` 字樣；`system_routes` L126 迭代的是狀態矩陣的 **zeta 軸值**（`axes` 端點），不是 `structural_drift` 鍵。另外 `cli/repl.py` L523 讀 `measured_eta_metrics()` 且已處理 `None`，`lifespan.py` L870 組快照時也先判 `None` |

---

## 5. 門禁與維護規則

1. **不開新腳本**：任何可機器判定的新項，一律進 `scripts/check_fact_gates.py`
   的一個域（既有 definitions／layers／intelligence／benchmarks…）。
2. **本表目前沒有機器門禁**——職權是設計判斷，AST 判不出來。可判定的部分已由既有門禁覆蓋：能力歸層 →
   `check_layer_separation.py`；定義唯一 → `check_fact_gates.py`
   `definitions`；分數口徑 → `intelligence` 域。
3. **維護順序**：新增域或搬模組時，**先改本表 §2／§3，再改代碼**。
4. **衝突裁定**：本表與其他三張圖衝突時，用一句話裁定——
   **能力歸五層、時間歸 AL、職權歸本表、接線歸主幹線、口徑歸量測層。**
