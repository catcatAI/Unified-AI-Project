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
| `route_reasoning` | `ai/symbolic_reasoner.py` | 符號推理 pattern：傳遞關係、三段論、日曆、數量（單變量給/拿）、質量騙局、**雞兔同籠類二元線性組**（`_solve_word_problem`）。僅在恰兩類實體存在時求解，3+ 實體退回。 |
| `route_knowledge` | `ai/knowledge_base.py` | 事實查詢：顏色、聲音、單位換算、化學式、動物腿腳/頭數、**車輛輪數、硬幣價值**（`chicken legs=2`、`rabbit legs=4`、`bicycle wheels=2`、`quarter value=25`）。主體屬性查詢支援英文及**中文別名**（`腳踏車`/`一角硬幣` 等）。 |
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
| `cf14ec49` | `route_reasoning` 新增雞兔同籠二元線性求解 + KB 新增 chicken/rabbit + 本分類文件 | 確定性（模型層） |
| `a179f7a9` | 解題器泛化到 **legs / wheels / value** 三屬性（雞兔/車輛/硬幣）、KB 新增腳踏車/硬幣；`_output_matches` 新增 **reasoning 數值多重集合** 比較（訓練邊界把確定性樣本正確跳過） | 確定性（模型層）＋半定性（訓練層邊界） |
| `6ed19173` | reasoning 模板重建接通 runtime（`process()` 以 `"reasoning"` 鍵派遣、`{R0}/{R1}` 取代）；`_solve_word_problem` 3+ 實體退回；KB wheels/value 屬性查詢＋中文別名 | 確定性（模型層）＋半定性（對話層模板） |

---

## 增強路線圖 (Enhancement Roadmap)

> 依「確定性 → 半定性 → 非定性」的分工研究如何持續增強。標記 **已實作** 的即為
> 本次與先前提交已落地者；其餘為**研究提案**（依價值/風險排序），待確認後再實作。

### 半定性（學得/近似層）增強

| 提案 | 內容 | 狀態 |
|---|---|---|
| 訓練邊界 reasoning 化 | `_output_matches` 對結構化 reasoning 輸出用數值多重集合比較，讓確定性樣本（雞兔/硬幣等）在訓練時被正確跳過、並學習 NL 重建模板 | ✅ 已實作（本次） |
| 閘路 cell 擴張 | 學習器已支援 AND/OR/XOR/NAND/NOR/XNOR/NOT；可再加多 bit 位元形式與組合閘，補足 `evaluate_logic` 數值位元缺口 | 提案 |
| 關係 cell 模糊後援 | 以學得 cell 作為解題器**解析失敗**時的近似後援（NL 換言之泛化）；嚴守「只補解析缺口、不重做確定性數學」 | 提案（風險中） |
| reasoning 模板重建 | 把 `_reconstruct_with_template` 的 reasoning 分支改為消費輸入中的數字（35/94）而非整句，讓變體措辭能自動包回 NL | ✅ 已實作（`6ed19173`） |
| ε-增強訓練 | 在封閉真值表旁注入少量語序/同義換言之樣本（以 seed 控制），提升半定性層對措辭變異的韌性 | 提案 |
| 真實日常/常識語料 | 以 `scripts/download_daily_data.py` 下載真實 Stanford Alpaca（52,002 條開放指令對話，CC BY-NC 4.0），`train_pipeline` 訓練起始自動確保；抽樣測試證明與確定性引擎 **0 重疊**（互補）、字典吸收 + Hebbian 學習發生 | ✅ 已實作（本次）；⚠ 測量發現開放長文 recall ~15%，見 §非定性 |

> **測量發現（誠實記錄）**：隨機抽樣 40 條 Alpaca，`learn_batch` 全部吸收（dict 增長、hebbian_delta>0），但 `process()` 開放長文 token-overlap recall 僅 **6/40 ≈ 15%**。
> 即：小關聯 SNN 對開放散文記憶力有限，anchored decode 偏輸入。因此半定性層的可行範圍是
> 短結構化輸出的學習與重建；完整開放對話仍需 LLM fallback（非定性層）承接——此為既有架構分工，非本次回歸。

### 非定性（隨機/生成層）增強

| 提案 | 內容 | 狀態 |
|---|---|---|
| LLM fallback 接線 | 對「結構可解析但無整數解 / 3+ 變量 / 非線性」的文字題，把解析出的結構（實體、總數、屬性）當提示注入 LLM fallback，讓非確定性層從結構出發而非猜 | 提案 |
| 自信度驅動 temperature | 當確定性 + 半定性層皆未命中且證據弱時，提高 LLM temperature 探索；證據強時壓低 | 提案（`MetaController` 已具雛形） |
| 主動互動取樣 | 讓背景任務依互動品質挑選「確定性無法處理」的樣本回報訓練，形成閉環 | 提案 |
| 多候選解取樣 | 對開放式推理題由 network 解碼產生多個候選並用確定性引擎驗證後回傳，把非確定性輸出「收斂」到可驗證答案 | 提案（風險中） |

### 落地原則

- 每一項半定性增強都必須通過「不亂接」檢查：**不得重做確定性引擎已涵蓋的能力**，
  只補「引擎表達不出來」的部分（如 XNOR、措辭變異、無解析時的近似）。
- 每一項非定性增強都必須有可驗證出口（LLM 需 mock，network 需 benchmark），否則只列為提案。
- 新增能力一律先在 `route_reasoning` / `route_math` 等既有委派點掛上，避免改引擎接線。
