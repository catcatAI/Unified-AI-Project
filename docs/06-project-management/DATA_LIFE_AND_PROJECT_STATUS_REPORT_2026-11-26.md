# Unified-AI-Project 研究與工程決策報告

> **Repository**: https://github.com/catcatAI/Unified-AI-Project  
> **分析基準 commit**: `65d228db9cc8569c6d19e3aa63df11e96b6b2769` (`HEAD`, 2026-11-26)  
> **報告日期**: 2026-11-26  
> **性質**: 基於當前倉庫文件、狀態矩陣、程式碼與本地驗證命令的校正報告；不是對外宣傳稿。

> **數字更新註記（2026-11-26）**：本文是基準 commit `65d228db9` 的快照，表內測試數
> 10,861 / 11,520 是**建立時的舊值**，與其後續量測不符。目前權威值為
> **`tests/` 10,868 collected，全 testpaths 11,526 passed / 112 skipped / 0 failed**
> （2026-11-26 同步，見 `AGENTS.md`、`docs/STATUS_MATRIX.md`，由
> `scripts/check_test_count.py --update` 寫入）；核心分 0.00/10、系統分 6.41/10 不變。
> 引用本文數字時請用這段更新值，不要引用快照表內的舊值。

---

## 0. 校正摘要：這份報告修正了什麼

本報告修正了先前草稿中的幾個關鍵問題：

| 草稿問題 | 校正後結論 | 證據 |
|---|---|---|
| 分析基準寫成 `a880d1893` | 當前 `HEAD` 為 `65d228db9`；`a880d1893` 是其前 4 個 commit 之一 | `git rev-parse HEAD`, `git log --oneline -5` |
| 把「數據生命」混成單一概念 | 必須拆成 **資料生命週期 / 模型研究證據 / 系統生命狀態** 三層 | 見本文 §3 |
| 把設計願景、模擬機制、已驗證能力混寫 | 每項都標註「設計/實作/模擬/驗證」層級 | `docs/STATUS_MATRIX.md`, `docs/06-project-management/INTELLIGENCE_ASSESSMENT.md` |
| 把 LLM provider / 多模態 / 桌面等能力一律視為成熟 | 依 `STATUS_MATRIX`，多數能力是 `wired/implemented/verified` 混合，不可一概而論 | `docs/STATUS_MATRIX.md`（`gen_status_matrix.py check` 通過） |
| 把生物模擬描述得接近真實生命 | 程式內是模擬參數與啟發式控制，不是生理量測或主觀感受證據 | `core/life/digital_life_integrator.py`, `core/bio/*` |
| 測試數字可能漂移 | 建立時快照：`tests/` **10,861** 項；`STATUS_MATRIX` **11,520 passed, 112 skipped, 0 failed**（2026-11-25）→ **請用上方更新註記的 10,868 / 11,526** | `pytest --collect-only -q`, `docs/STATUS_MATRIX.md` |

---

## 1. 專案定位：它在做什麼，不在做什麼

### 1.1 一句話定位

Unified-AI-Project / Angela AI 不是單純的聊天機器人封裝，也不是已完成的通用 AGI。它比較接近：

> **一個以「數位生命系統」為研究方向的跨平台 AI+AL 框架：把對話、記憶、狀態、模擬生物約束、工具路由、本地/外部模型與具身化介面放進同一個可持續運行的系統骨架。**

這個定位有文件支持，但也必須與實際成熟度分開看：

- `README.md` 將專案描述為跨平台數位生命系統，含多模型路由、記憶、情緒、安全閘門、Agent、Live2D、Luanti。
- `docs/PROJECT_OVERVIEW.md` 與 `docs/COMPREHENSIVE_DESIGN_STANDARD.md` 使用 “data life / 數據生命” 的設計語言。
- `docs/FRAMEWORK_OVERVIEW.md` 明確自我定位為 framework，並警告 ML 權重訓練完成度低、神經能力不能冒充整體能力。
- `docs/STATUS_MATRIX.md` 是對外/對內成熟度真相源，不以願景宣稱為準。

### 1.2 系統主線

當前倉庫能支持的主線可概括為：

```text
使用者/環境輸入
  → 分類、情緒、危機、安全/執行閘門
  → 記憶檢索與狀態讀取
  → 確定性引擎 / 模板 / LLM / Agent 路由
  → 回應或行動
  → 記憶寫入、狀態更新、事件記錄、持久化
  → 下一輪再利用
```

這條主線中，**可靠性較高的部分**主要是確定性能力、路由/閘門、記憶與狀態基礎設施；**仍在研究中的部分**主要是神經模型的可泛化學習、持續學習的真實能力增益、以及生命狀態對行為的可證偽閉環。

### 1.3 不應宣稱的事

以下不能從現有證據直接宣稱：

- Angela 已具備通用智能或自主主體性。
- 生物模擬等於真實生理感受或情緒體驗。
- 有訓練管線、記憶、權重更新，就等於模型已學會開放域泛化。
- 架構完整度等於智能完成度。
- 有本地 checkpoint / benchmark 腳本，就等於任何 clone 都可重現同樣結果。

---

## 2. 現況快照：工程與研究的真實狀態

### 2.1 本次核對

| 項目 | 結果 | 命令/來源 |
|---|---:|---|
| Git HEAD | `65d228db9cc8569c6d19e3aa63df11e96b6b2769` | `git rev-parse HEAD` |
| STATUS_MATRIX 核對 | 通過，30 條目 + pipeline 10 階段 + tree 11 節點 + lifecycle 33 項全綠 | `./.venv/bin/python scripts/gen_status_matrix.py check` |
| `tests/` 收集數 | 10,861 tests collected（建立時快照；**現值 10,868**） | `./.venv/bin/python -m pytest tests/ --collect-only -q` |
| STATUS_MATRIX 記錄的全量測試 | 11,520 passed, 112 skipped, 0 failed（2026-11-25 快照；**現值 11,526**，2026-11-26） | `docs/STATUS_MATRIX.md` |
| 智能評估口徑 | 能力/來源/誠實度三軸；核心分仍 0.00/10 | `docs/06-project-management/INTELLIGENCE_ASSESSMENT.md` |

### 2.2 成熟度不是單一分數

`STATUS_MATRIX.md` 的狀態語言是 `claimed -> implemented -> wired -> verified -> production`。這比「完成/未完成」更適合本專案。

代表性現況（節選）：

| 領域 | 狀態 | 含義 |
|---|---|---|
| 主流程 e2e | verified | 主路徑有端到端驗證腳本 |
| ExecutionGate | verified | 危險操作閘門有測試 |
| HAM 記憶查詢 | verified | 有真實查詢路徑，非純 mock |
| 確定性引擎 | verified（僅確定性層） | 數學/知識/符號推理可靠，但不是神經泛化 |
| LLM providers | wired | 接線存在，品質 benchmark 未建立 |
| 持續學習 ED3N/GARDEN | verified | 訓練→存檔→門消費閉環存在；不等於能力已普遍增長 |
| 神經開放域泛化 | implemented | 有實作與誠實標示，仍低 |
| 多模態 | implemented | 管線存在，品質未達標 |
| Luanti 遊戲代理 | wired | 有識別/記憶/訓練閉環，live 樣本與 20FPS 未達標 |
| Dashboard 新面板 | verified | 有真實資料與瀏覽器 E2E |

**工程判斷**：專案的系統骨架成熟度明顯高於「單一神經核心能力」。決策時應避免用骨架成熟度替代模型能力成熟度。

### 2.3 研究現況：核心分與系統分必須分開

`INTELLIGENCE_ASSESSMENT.md` 給出目前最重要的誠實邊界：

- 有統一定義：能力 capability、來源 source、誠實度 integrity 三軸。
- 系統分可以包含模板、查表、確定性規則、路由後的正確答案。
- **核心分只算 SNN/LLM 產生且正確的答案**；表層正確不進核心分。
- 文件明確記錄：**「50 個正確答案中，由模型產生的：0。」**（`INTELLIGENCE_ASSESSMENT.md`）
- 因此核心階梯仍在 L0，不能因系統能回答就宣稱核心已學會。

這不是否定專案，而是說明：

> **目前系統擅長的是「組裝可靠能力」，還不是「由核心模型自主產生可靠能力」。**

---

## 3. 「數據生命」真正含義：三層拆解

這是本報告的核心。使用者要求的拆法應作為正式口徑：

1. **資料生命週期 Data Lifecycle**：資料如何被產生、清洗、表示、使用、鞏固、衰退、持久化、重載。
2. **模型研究證據 Model Research Evidence**：哪些能力是真的被測到，哪些只是架構、框架、模擬或訓練集現象。
3. **系統生命狀態 System Life State**：Angela 在運行時維護的內部狀態機、資源/情緒/成熟度/節律等模擬控制訊號。

三者相關，但**不能互相冒名**。

### 3.1 第一層：資料生命週期（Data Lifecycle）

#### 定義

資料生命週期關心的是「資料/記憶/權重/事件」的可追蹤旅程：它從哪來、如何變形、何時被使用、何時過期、何時可重現。

這一層回答的是工程問題：**資料是否乾淨、可追蹤、可持久化、可回放、可刪除？**

#### 倉庫中的實作證據

| 階段 | 現有實作/證據 | 觀察 |
|---|---|---|
| 來源與攝取 | 字典/語料/對話/事件/多模態資料；`PRODUCTION_ARCHITECTURE.md` 有 ingest-process-store-analyze-backup 高層圖 | 高層方向存在，但不是所有資料源都有統一 provenance schema |
| 轉換與表示 | HAM entry 有 `content/data_type/metadata/keywords/namespace/timestamp`；`_extract_keywords`、模板/對話分桶 | 資料進入後已成為可檢索記憶物件，不只是原始文字 |
| 儲存與上限 | HAM 每桶 `_max_entries_per_bucket=5000`，超限裁剪；JSON 持久化 | 有基本容量治理，但不是完整資料湖/版本化資料平台 |
| 保留與衰退 | HAM `prune()`：低重要性 30 天、中 90 天、高重要性 >=0.7 保留；最近 50 筆保護；`protected` 不刪；`al_retain_days` 可覆蓋分層 | **已實作**的資料生命週期規則，屬工程事實 |
| 策略化記憶 | `al_memory_policy.retention_policy()` 由 AL 快照輸出 `retention_seconds/weight/consolidate`；HAM `_apply_retention_policy()` 執行並 stamp `al_retain_days/al_weight/protected` | 這是「系統生命狀態」影響「資料生命週期」的真實介面 |
| 記憶鞏固觸發 | `DigitalLifeIntegrator` 有 `memory_bridge`；GROWING/RESTING/DORMANT 會呼叫 `trigger_consolidation()` | 有觸發線路；鞏固效果仍需看 neuroplasticity 實作與測試 |
| 產物持久化 | checkpoint、JSON state、vector store、benchmark JSON、訓練輸出散見 `data/`, `checkpoints/`, docs/reports | 產物存在，但跨機器可重現性仍是風險 |

#### 重要程式事實（HAM）

`apps/backend/src/ai/memory/ham_memory/ham_manager.py` 顯示：

- 預設存放 `data/memory/ham_memory.json`，支援 `ANGELA_DATA_DIR`。
- bucket 分 `templates` / `conversations`，並限制 conversation 類不污染 template 回答。
- `store_experience()` 會補 timestamp、套用 AL retention policy、執行 `prune()`、再落盤。
- `prune()` 以 age + effective importance 決策；`al_weight` 只影響保留決策，不覆寫原 `importance`。
- 有 unservable template 過濾，避免拒答/身份洩漏/破壞性動作回放污染。

這代表資料生命週期在 HAM 層**不是只有概念圖**，已有具體規則。

#### 這一層常見誤判

- **誤判 A**：有 prune/consolidation 就代表記憶像人一樣可靠。  
  **校正**：這只是規則化記憶治理，品質仍受資料污染、檢索錯誤、namespace、重載一致性影響。
- **誤判 B**：checkpoint 存在就代表可重現。  
  **校正**：還要看格式、loader、權重/hash、資料來源、本機路徑、版本相容性。
- **誤判 C**：資料被存下來就有價值。  
  **校正**：未驗證或污染資料會反向傷害訓練與評估，專案自己已有 leak/hardcode/污染修正歷史。

### 3.2 第二層：模型研究證據（Model Research Evidence）

#### 定義

模型研究證據關心的是「能力主張能否被證明」：分數從哪來、由哪層產生、是否洩漏、是否可重跑、是否跨未見樣本成立。

這一層回答的是研究問題：**我們真的學到了什麼？**

#### 倉庫中的證據分級

應使用 `INTELLIGENCE_ASSESSMENT.md` 的六型分數口徑：

| 分數類型 | 意義 | 不能拿來宣稱什麼 |
|---|---|---|
| 架構分數 | 結構能支持什麼 | 不等於能跑出能力 |
| 框架分數 | 模組/框架存在 | 不等於訓練有效 |
| 預期分數 | 設計上應可做到 | 不等於實測結果 |
| 訓練分數 | 訓練集表現 | 不等於泛化 |
| 驗證分數 | hold-out / 未見樣本表現 | 仍需看協議與污染 |
| 實際分數 | 真實使用/端到端表現 | 不可用單一 benchmark 取代 |

#### 當前關鍵研究事實

- **確定性能力強、可審計**：Math/KB/symbolic/retrieval 是系統目前可靠輸出的重要來源。
- **神經核心仍弱**：`INTELLIGENCE_ASSESSMENT` 明確把核心分與系統分分開；核心分 0.00/10，核心階梯 L0。
- **來源歸因是硬要求**：正確答案若由 lookup/template/rule 產生，不可記入神經核心能力。
- **訓練閉環存在，但證據等級有限**：`STATUS_MATRIX` 將持續學習列為 verified（訓練→存檔→門消費閉環），同時註明可分性負結果已記錄、長期能力增長證據仍待累積。
- **資料污染是歷史主因**：專案文件反覆處理 bpc 洩漏、hardcoded accuracy、fallback 日誌污染、hold-out 設計等問題。這說明研究流程正在成熟，但也說明舊分數不可輕信。

#### 這一層的決策規則

任何「Angela 變聰明了」的說法，至少要能回答：

1. 用哪個資料集/協議？是否 hold-out / leave-roster-out / unseen paraphrase？
2. 答案由哪層產生？SNN/LLM/模板/查表/規則？
3. 有無污染？訓練集洩漏、prompt echo、fallback 文本、硬編碼答案？
4. 能否重跑？checkpoint、seed、config、資料 hash、環境是否齊全？
5. 改善是局部擬合，還是跨情境轉移？

答不出來，就不能升級為研究結論。

### 3.3 第三層：系統生命狀態（System Life State）

#### 定義

系統生命狀態關心的是 Angela 運行時的內部控制狀態：生命週期階段、喚醒、意圖、模擬生物訊號、記憶橋接、模態閘門等。

這一層回答的是控制問題：**系統此刻如何調節自己？**

#### 倉庫中的實作證據

`core/life/digital_life_integrator.py` 是核心協調器之一，可觀察到：

- **生命週期狀態機**：`INITIALIZING / AWAKENING / GROWING / MATURE / RESTING / DORMANT`。
- **子系統協調**：BiologicalIntegrator、ActionExecutor、MemoryNeuroplasticityBridge、StateMatrix、IntentManager、DynamicThresholdManager、AutonomousLifeCycle。
- **健康與活動追蹤**：health check loop、activity status、rest/dormant 轉換。
- **模態閘控 ModalityGateway**：依 arousal、dissonance、任務型態開關 TEXT/AUDIO/VISUAL_3D/CODE。
- **CNS 事件訂閱**：接收 `routing.response_generated`、`emotion.updated`、`lifecycle.decision_executed`。
- **互動回饋**：`process_interaction_feedback(engagement_ratio, success)` 會更新內部 engagement window，低 engagement 時關閉 visual_3d，高時重新開啟。
- **記憶鞏固觸發**：GROWING/RESTING/DORMANT 行為會呼叫 `memory_bridge.trigger_consolidation()`。

`core/life/al_memory_policy.py` 顯示系統生命狀態如何影響資料策略：

- `retention_seconds <- drift`：變動越快，保留越短。
- `weight <- intensity × emotion.arousal × rhythm`：高強度/高喚醒/特定節律下提高記憶權重。
- `consolidate <- life_phase == CONSOLIDATION 且 identity drift 未觸發閘門`：不是任何時候都固化。
- 未觀測來源退回 default（D11），避免缺資料時亂改記憶規則。

#### 模擬/啟發式邊界

這一層有很多「像生命」的命名，但必須讀成**控制語義**：

- `arousal`, `stress`, `heart_rate`, `happiness`, `trust`, `mood` 等是**模擬狀態槽位**或控制變數。
- `engagement_ratio` 在程式註解中明說是 proxy（回應長度/訊息長度），不是真實使用者投入度量測。
- `success` 在回饋鏈中是最小 proxy（例如非空回應），不是答案正確性判定。
- ModalityGateway 的關閉/開啟是資源保守 heuristic，不是對使用者情緒的證明。

#### 這一層的正確價值

它的價值不在「證明 Angela 有感覺」，而在：

- 提供可觀測的內部狀態座標；
- 讓記憶、路由、模態、資源策略有統一控制面；
- 為未來做可證偽實驗提供介面：狀態改變是否真的帶來更好任務表現、記憶穩定性或互動品質。

---

## 4. 三層如何互動：真正的「數據生命」應這樣理解

### 4.1 互動關係

```text
             ┌──────────────────────────────┐
             │  模型研究證據                │
             │  (能否證明學到/泛化/可重現)  │
             └──────────────▲───────────────┘
                            │ 驗證/否證
                            │
┌───────────────────────────┼───────────────────────────┐
│                           │                           │
│   資料生命週期             │         系統生命狀態       │
│   (資料/記憶/權重/產物)    │         (相位/喚醒/意圖)   │
│   - ingest/clean/store     │         - lifecycle        │
│   - retrieve/prune         │         - bio/state        │
│   - consolidate/persist    │         - modality gate    │
│   - reload/replay          │         - feedback proxy   │
└──────────────▲────────────┴────────────▲──────────────┘
               │                          │
               └────────── 控制策略 ──────┘
                 (retention/weight/consolidate)
```

### 4.2 一個具體例子：記憶不是單層

一段對話進入系統後，可能同時穿過三層：

1. **資料生命週期**：被寫入 HAM conversation，帶 timestamp/keywords/importance/namespace；之後可能被 prune、保留、protected。
2. **系統生命狀態**：當下 life phase、arousal、intensity、rhythm、identity drift 影響 AL memory policy，決定保留期、權重、是否固化。
3. **模型研究證據**：若這段資料後續用於訓練或評估，必須證明它沒有污染 hold-out、沒有把 fallback/錯誤輸出當真值、沒有造成分數虛高。

這就是為什麼「數據生命」不能只講生命比喻，也不能只講資料庫。

### 4.3 專案真正獨特的地方

這個專案的研究價值，不在於某個單一模組領先，而在於它試圖把三層接起來：

- 資料不是靜態資料集，而是會進入運行記憶。
- 記憶不是只存不管，而是有保留、權重、固化、衰退策略。
- 系統狀態不是 UI 動畫，而是會影響記憶策略與模態閘控。
- 研究評估不是只看 demo，而是開始要求來源歸因、污染控制、hold-out、可重現性。

但「接起來」不等於「已閉環證明」。目前更準確的說法是：

> **介面已部分存在，閉環證據仍不足。**

---

## 5. 資料生命週期深挖：目前能證明什麼

### 5.1 已有的資料治理能力

| 能力 | 證據 | 成熟度判斷 |
|---|---|---|
| 記憶容量上限 | HAM `_max_entries_per_bucket=5000` | 基礎可用 |
| 時效/重要性保留 | 30/90 天分層 + keep floor + protected | 基礎可用 |
| AL 策略注入 | `al_retain_days/al_weight/protected` stamping | 有設計且有實作 |
| 汙染模板過濾 | `is_unservable_template` + relevance/subject guards | 針對已知污染模式的防護 |
| metadata 自描述 | P1-9 save 時蓋 `schema_version/saved_at/counts` | 有助於資料檢查 |
| 產物/狀態持久化 | lifecycle JSON、checkpoints、memory JSON、vector store | 存在，但分散 |

### 5.2 主要缺口

| 缺口 | 為什麼重要 | 建議 |
|---|---|---|
| 缺乏統一 Data Manifest | 無法一眼知道一筆資料的來源、用途、權限、污染狀態 | 建立 dataset/memory/artifact manifest schema |
| 記憶系統分散 | HAM、VectorStore、StateMatrix、lifecycle、checkpoints 各自持久化 | 定義統一 MemoryItem/Artifact 抽象與來源映射 |
| 重現性不足 | 本機 checkpoint、路徑、環境差異會破壞驗證 | 為關鍵產物加 hash、schema version、loader round-trip 測試 |
| 刪除/保留策略可解釋性不足 | 使用者難理解為何被記住或遺忘 | 暴露 retention decision trace（不含敏感內容） |
| 訓練資料與 runtime 記憶邊界仍需更硬 | runtime fallback/錯誤輸出曾污染訓練 | 對訓練入口加 provenance + quarantine gate |

### 5.3 對「數據生命週期」的正確表述

可以說：

- 專案已實作**部分資料生命週期控制**，尤其在 HAM 記憶保留、權重調制、鞏固觸發與污染過濾。
- 專案正在建立**研究資料治理意識**，包括 hold-out、leak-free、provenance、fact gate。

不應說：

- 專案已擁有完整、統一、可審計的全域資料生命週期平台。
- 所有資料都已具備端到端 lineage、可重現與可回放保證。

---

## 6. 模型研究證據深挖：目前能證明什麼

### 6.1 已證明的能力

| 能力 | 證據 | 邊界 |
|---|---|---|
| 系統骨架可運行 | STATUS_MATRIX 多項 verified；主流程 e2e 15/15 | 不等於智能高 |
| 確定性能力可靠 | math/KB/symbolic 路徑被明確驗證與審計 | 不是神經學習 |
| 記憶查詢路徑真實存在 | HAM recent/context routes verified | 不等於長期記憶推理已解 |
| 持續學習管線有閉環 | 訓練→存檔→門消費已閉環 | 不等於普遍能力增長 |
| 評估誠實性提升 | intelligence assessment 有來源拆分、score type、pass criteria、open gates | 仍需長期維持 |

### 6.2 尚未證明的能力

| 主張 | 現況 | 缺的證據 |
|---|---|---|
| ED3N/GARDEN 能自主產生可靠開放域答案 | 核心分 0.00/10，核心階梯 L0 | unseen 泛化、來源為模型生成且正確 |
| 持續學習帶來淨能力增長 | 閉環存在，但長期增長證據待累積 | 前後測、回歸測、跨任務轉移、災難性遺忘監測 |
| 生命狀態改善智能表現 | 有狀態與 feedback 介面 | 消融實驗：有/無 life state 對任務、記憶、穩定性的因果影響 |
| 記憶鞏固提升長期表現 | 有 consolidation trigger 與 neuroplasticity 模擬 | 長期保留、再測試、干擾/遺忘曲線對照 |
| 多模態理解成熟 | implemented | 真實感知品質、端到端任務成功率、延遲與錯誤分析 |

### 6.3 研究上最該避免的陷阱

1. **把系統正確當模型正確**：路由到計算器或 KB 的正確，不是 SNN/LLM 核心能力。
2. **把訓練集擬合當泛化**：必須保留 unseen roster/entity/paraphrase/order/restart 測試。
3. **把模擬指標當真實測量**：proxy 要明確命名為 proxy。
4. **把架構圖當完成度**：模組存在不等於接線、驗證、品質達標。
5. **把本地可跑當可重現**：沒有 artifact manifest 的實驗結果只能算觀察，不算穩定證據。

---

## 7. 系統生命狀態深挖：目前能證明什麼

### 7.1 已有的生命狀態機制

| 機制 | 證據 | 類型 |
|---|---|---|
| LifeCycleState 狀態機 | `DigitalLifeIntegrator.LifeCycleState` | 實作/控制邏輯 |
| Maturity score 由 state matrix 穩定性估算 | `_compute_maturity_score()` | 啟發式模擬 |
| ModalityGateway | 依 arousal/dissonance 開關模態 | 啟發式資源控制 |
| Intent influence 寫回 state matrix | `_update_intent_state()` / `_apply_intent_influence()` | 控制迴路實作 |
| Memory bridge consolidation trigger | GROWING/RESTING/DORMANT 行為 | 介面實作 |
| AL memory policy | retention/weight/consolidate 由 snapshot 決定 | 策略實作 |
| CNS event feedback | emotion/routing/lifecycle 事件訂閱 | 事件迴路實作 |
| Neuroplasticity core | LTP/LTD/Hebbian/Ebbinghaus/consolidation dataclasses/enums | 模擬模型實作 |

### 7.2 這一層不是什麼

- 不是生理監測系統：沒有真實心率、血壓、荷爾蒙感測器資料。
- 不是情緒科學證明：情緒/喚醒是可計算狀態，不是主觀體驗證據。
- 不是完整認知模型：成熟度、意圖、記憶鞏固目前多為啟發式或局部模擬。
- 不是自動帶來能力提升的魔法層：必須用消融實驗證明效益。

### 7.3 這一層應該怎麼用

把它當成：

> **可觀測、可調參、可消融、可回放的控制平面（control plane）**。

不要把它當成：

> **已被證明的數位意識或生物等價生命。**

---

## 8. 工程決策建議：接下來該做什麼

### P0：把「資料生命週期」產品化為可審計基礎設施

**目標**：任何關鍵資料/記憶/產物都能回答「從哪來、怎麼用、為何保留、能否重現」。

- 定義統一 manifest：`id, type, source, created_at, producer, schema_version, hash, namespace, retention_policy, provenance, verified`.
- 為 HAM / checkpoints / training outputs / benchmark results 補齊最小 lineage。
- 將 runtime 記憶與訓練資料入口硬隔離：訓練必須經過 quarantine/provenance gate。
- 為 prune/consolidation/export 增加可解釋 trace（metadata only）。

**驗收**：抽樣一筆記憶或模型產物，可在 5 分鐘內追溯來源、策略、版本與使用紀錄。

### P1：把「模型研究證據」從管線存在提升到能力證據

**目標**：只接受可歸因、可重跑、可否證的能力提升。

- 所有核心能力實驗強制標註 score type、source attribution、dataset split、artifact hash。
- 維持核心分/系統分分離；禁止 lookup/template 正確答案進入核心分。
- 對持續學習建立 before/after + regression + forgetting 三件套。
- 對 ED3N/GARDEN 優先做 unseen entity / paraphrase / order / restart / leave-roster-out，而不是擴大 demo 題庫。

**驗收**：新增能力宣稱時，能附上命令、產物、來源分布、未見測試與回歸結果。

### P1：把「系統生命狀態」做成可證偽控制實驗

**目標**：證明 life state 有用，而不只是有趣。

- 為 ModalityGateway、AL memory policy、consolidation trigger 做 A/B 消融。
- 明確標記 proxy：`engagement_ratio`、`success`、模擬生理值不得偽裝成真實量測。
- 建立 state transition replay：給定同一事件序列，狀態轉移可重放。
- 衡量指標限於可觀測項：任務成功率、記憶命中、遺忘率、恢復時間、延遲、成本。

**驗收**：至少一個 life-state 機制能證明「開啟比關閉」在特定任務上有統計或可重現收益。

### P2：收斂產品敘事

**目標**：避免研究框架、桌面伴侶、遊戲代理、AGI 願景互相稀釋。

- 對外敘事：本地可審計 AI+AL 研究框架 / 數位生命系統實驗平台。
- 對內研發：核心研究問題只保留 2-3 條，例如「持續記憶定址」、「可重現學習證據」、「生命狀態控制增益」。
- 對功能擴張設閘門：新模組必須說明它服務哪一層（資料生命週期/研究證據/生命狀態），否則不進核心路線。

---

## 9. 最終結論

Unified-AI-Project 最值得肯定的，不是它已經做出通用數位生命，而是它已經把幾個通常被分開處理的問題放到同一個系統裡：

- **資料生命週期**：資料/記憶如何保留、衰退、固化、持久化。
- **模型研究證據**：能力是否真的學到、是否可歸因、是否可重現。
- **系統生命狀態**：運行中的內部狀態如何調節記憶、模態與行為。

這三層如果分開看，都不夠構成「數據生命」；只有當它們被誠實地接起來、並且能被測量與否證時，才接近專案真正想追的東西。

**目前最準確的判斷**：

- 系統骨架：**有實質進展**。
- 資料生命週期：**局部實作存在，但尚未統一成可審計平台**。
- 模型研究證據：**誠實度提升明顯，但核心神經能力仍未突破**。
- 系統生命狀態：**控制面已成形，但仍以模擬/啟發式為主，缺乏因果效益證明**。

**一句話決策建議**：

> 下一階段不要再用「更多模組」證明雄心；要用「更強的證據鏈」證明數據生命：每筆資料可追溯、每個能力可歸因、每個生命狀態可消融、每次提升可重現。

---

## 附錄 A：本次查核的主要檔案

- `README.md`
- `docs/STATUS_MATRIX.md`
- `docs/FRAMEWORK_OVERVIEW.md`
- `docs/PROJECT_OVERVIEW.md`
- `docs/COMPREHENSIVE_DESIGN_STANDARD.md`
- `docs/03-technical-architecture/PRODUCTION_ARCHITECTURE.md`
- `docs/06-project-management/INTELLIGENCE_ASSESSMENT.md`
- `apps/backend/src/core/life/digital_life_integrator.py`
- `apps/backend/src/core/life/al_memory_policy.py`
- `apps/backend/src/ai/memory/ham_memory/ham_manager.py`
- `apps/backend/src/core/bio/neuroplasticity_core.py`（透過搜尋確認 LTP/LTD/Hebbian/Ebbinghaus/consolidation）

## 附錄 B：本次執行的驗證命令

```bash
git rev-parse HEAD
git log --oneline -5
./.venv/bin/python scripts/gen_status_matrix.py check
./.venv/bin/python -m pytest tests/ --collect-only -q
``` 

觀察結果：

- `HEAD = 65d228db9cc8569c6d19e3aa63df11e96b6b2769`
- `STATUS_MATRIX 核對通過：30 條目＋pipeline 10 階段＋tree 11 節點＋lifecycle 33 項，全綠`
- `10861 tests collected in 5.20s`（僅 `tests/` 收集）
