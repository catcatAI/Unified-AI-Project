# 確定性分類指南 (Determinism Classification)

> 本文件把專案的引擎、組件與流程，在 **模型 / 訓練 / 對話** 三個層面區分為
> **確定性 (Deterministic) / 半定性 (Semi-deterministic) / 非定性 (Non-deterministic)**。
> 這是**分類與備註層級**的文件，不涉及任何代碼邏輯變更。若代碼註解與分類不一致，
> 允許同步修正註解（備註能碰）。

## 定義

| 類別 | 判定標準 | 相同輸入 → 相同輸出？ |
|---|---|---|
| **確定性 (Deterministic)** | 無權重、無機率、無學習；由規則 / 公式 / 查表 / 窮舉驅動 | 永遠相同（100% 可重現） |
| **半定性 (Semi-deterministic)** | 有學習或統計分量；主幹可由確定性規則描述，但輸出取決於學得的權重或累積狀態 | 權重凍結、狀態固定時相同；否則可能不同 |
| **非定性 (Non-deterministic)** | 含隨機取樣、生成或時序競爭；輸出不可由輸入單獨決定 | 不保證相同 |

**優先序原則**：引擎與對話管線一律 **確定性 → 半定性 → 非定性** 依序嘗試，
前一層命中即短路返回，非確定性層是「最後手段」。

---

## 模型層 (Models) — 推理引擎與組件

### 確定性

| 組件 | 位置 | 提供的功能 |
|---|---|---|
| `evaluate_math` | `services/math_verifier.py` | 算式求值：`+ − × ÷ % **`、三角、sqrt/log、常數、factorial、中文數字。全專案唯一的運算來源（單一 compute source）。 |
| `evaluate_logic` | `services/math_verifier.py` | 布林自我語言：true/false、and/or/not、等值。**注意：無法表達 XNOR**（引擎缺口）。 |
| `gate_router.try_logic_gate` | `ai/arithmetic/gate_router.py` | 閘路路由橋：引擎優先（先問 `evaluate_logic`）；僅當引擎表達不出來時（今日為 **XNOR** 與數值位元形式 `N OP M`）才落到學習器。路由本身確定。 |
| `route_reasoning` | `ai/symbolic_reasoner.py` | 符號推理 pattern：傳遞關係、三段論、日曆、數量（單變量給/拿）、質量騙局、**雞兔同籠類二元線性組**（`_solve_word_problem`）。 |
| `route_knowledge` | `ai/knowledge_base.py` | 事實查詢：顏色、聲音、單位換算、化學式、動物腿腳/頭數（含 `chicken legs=2`、`rabbit legs=4`）。 |
| `relational_chain` | `ai/reasoning/relational_chain.py` | 比較關係鏈解析（A 比 B 高…，誰最高）。 |
| Reflex 表 | ED3N `_stage_reflex` / GARDEN `_ReflexTable` | 精確 / 子字串的 canned 回應匹配（問候、既定回答）。 |
| 安全性規則 | 危機評級、負面詞過濾、硬編門檻 | 依規則表判定，不涉及學習。 |

### 半定性

| 組件 | 位置 | 提供的功能 |
|---|---|---|
| `ArithmeticLearner` + `_CellMLP` | `ai/arithmetic/arithmetic_learner.py` | 數字 cell 學習器：加 / 減 / 乘 / 邏輯四組 cell，softmax heads，在封閉真值表上以 L-BFGS-B 訓練。**權重凍結後前向確定，但屬學得的近似能力**。 |
| SNN cores | ED3N SNN core / GARDEN `TensorSNNCore` | Hebbian 學習的權重；給定權重前向確定，但能力來自訓練。 |
| 向量檢索 / 解碼 | GARDEN `VectorDictionary`、ED3N encode / latent / enrichment / network decode | cosine 相似度檢索與權重驅動重建；給定 embedding/權重確定，但 embedding 與權重是學得的。 |
| `CausalReasoningEngine` | `ai/reasoning/causal_reasoning_engine.py` | 種子因果規則 + 緩衝區預測；規則確定、緩衝依歷史累積。 |

### 非定性

| 組件 | 位置 | 提供的功能 |
|---|---|---|
| LLM providers | `services/llm/*`（9 個後端） | temperature 取樣生成；相同提示可產生不同輸出，不可重現。 |

---

## 訓練層 (Training)

### 確定性

| 組件 | 位置 | 提供的功能 |
|---|---|---|
| 合成資料產生 | `ArithmeticLearner.generate_*_truth_table` 等 | 封閉真值表（加/減/乘/邏輯）窮舉生成，無隨機性。 |
| `is_deterministic_match` / `record_template_match` | `ai/garden/garden_engine.py` | **訓練時的能力邊界守衛**：若確定性引擎已能正確回答樣本（math/logic/knowledge/reasoning/chain），訓練就跳過該樣本——不把計算事實當關聯學習（不亂接）。 |
| L-BFGS-B 優化器 | `_CellMLP.fit` | 給定資料與種子即確定的數值優化器。 |
| Hebbian 更新 | SNN cores | 給定激發順序即確定的權重更新規則。 |
| 評估 / 驗證 | benchmark、accuracy 檢查 | 重現性測量。 |

### 半定性

| 組件 | 位置 | 提供的功能 |
|---|---|---|
| 連續學習管線 | `TrainingCoordinator` / `ContinuousLearningPipeline` | dedup、追蹤、選樣；決定「學什麼」取決於對話歷史與狀態。 |
| Anchor learning / ripple | anchor 引擎、domain ripple | 規則驅動但路徑依賴累積狀態。 |
| `EvolutionEngine` | 性格演化 | 情緒/反饋驅動；依反饋歷史演化。 |

### 非定性

| 組件 | 位置 | 提供的功能 |
|---|---|---|
| MLP 隨機初始化 | `DigitRepresentation` / `_CellMLP` | 隨機初始化但**以 seed 控制**；固定 seed 即可重現。 |
| LLM 蒸餾 / 生成標籤 | 訓練資料生成（若用 LLM） | 生成結果不可重現。 |

---

## 對話層 (Dialogue / Chat)

### 確定性

| 組件 | 位置 | 提供的功能 |
|---|---|---|
| 雙軌數學門 | `api/routes/chat_routes.py::_try_math_verification` → `MathVerifier.verify` | 主管線前直接辨識並回答算式；stateless 算式對 state matrix 不做認知改動。 |
| 階段順序 | ED3N / GARDEN `process` | reflex → math/logic → reasoning → knowledge → chain → network/LLM；短路命中。 |
| `gate_router` 掛接 | `route_math` 兩顆引擎 hook | 邏輯閘語句在對話路由層確定處理。 |
| 安全性 / 情感規則 | 危機評級、情緒分析、負面過濾 | 規則表判定。 |

### 半定性

| 組件 | 位置 | 提供的功能 |
|---|---|---|
| `PriorityNegotiator` | `ai/meta/priority_negotiator.py` | 8 個 voter（lifecycle / emotional / intent / angela_emotion / causal / meta_calibration / heartbeat / dli_state）weighted 融合成 routing_mode。給定狀態確定，但狀態聚合了反饋/學習歷史。 |
| `MetaController` | 校準快取 + reliability-weighted 調整 | 依歷史自信度調 temperature/tokens。 |
| `EmotionSystem` 反饋迴路 | 時間趨勢、持續負面計數器 | 規則確定、依反饋歷史累積。 |
| `AutonomousLifeCycle` | 滾動互動品質視窗 → 行為調整 | 依最近 20 次互動品質覆寫保守/探索。 |
| `DynamicThresholdManager` | 由 state matrix 動態調門檻 | 依當下情感維度值調整。 |
| ED3N / GARDEN network 解碼 | 確定性階段未命中時 | 學得權重驅動的近似回應。 |

### 非定性

| 組件 | 位置 | 提供的功能 |
|---|---|---|
| LLM fallback 生成 | LLM fallback 鏈 | temperature 取樣，不可重現。 |
| 背景任務 / 主動互動 | 時序觸發 | 依系統狀態與時機觸發，非輸入決定。 |

---

## 關鍵邊界規則

1. **確定性優先**：對話、ED3N、GARDEN 一律先跑確定性階段，命中即返回。
2. **不亂接（學習只補引擎缺口）**：學習器只學引擎表達不出來的能力（今日為 **XNOR**）。
   確定性引擎已能回答的樣本，訓練跳過（`is_deterministic_match`）。
3. **能力邊界不燒進權重（§B）**：不得把計算事實 / 解題能力硬編進 SNN 權重或作關聯記憶；
   確定性能力留在確定性模組（`evaluate_math` / `route_reasoning` / `route_knowledge`）。
4. **可重現**：MLP / SNN 初始化與資料生成均以 `seed` 控制，固定 seed 可重現訓練。
5. **分類屬文檔層級**：本文件是分類基準；代碼註解可同步備註，但不改任何代碼邏輯。

---

## 相關變更記錄

| 提交 / 狀態 | 內容 | 影響的分類 |
|---|---|---|
| `ce32a98e` | 數字學習器擴充減 / 乘 / 邏輯 cell | 半定性（模型層） |
| `ccd3c35a` | 學習閘路接進 dict/SNN（1+2） | 半定性（模型層）＋確定性路由（對話層） |
| 未提交（本次） | `route_reasoning` 新增雞兔同籠二元線性求解 + KB 新增 chicken/rabbit | 確定性（模型層） |
