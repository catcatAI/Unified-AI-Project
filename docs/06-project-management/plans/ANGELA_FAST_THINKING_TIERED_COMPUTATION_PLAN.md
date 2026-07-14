# Angela「快思考」分級計算框架 — 設計紀錄（Spec / Record）

> 狀態：**已部分實作並接線（2026-07-14）**。本文件把「哪些運算每次都要參與、哪些不需要每次重算」
> 想清楚、分出等級，並設計出「歷史快照 + 區塊 + 依分級/狀態重組計算」的快思考路徑。
> 對應任務：快思考（System-1）分級計算、快照/區塊、運行期重組。
> 實作現況：domain_ripple 框架接線進生產數學雙軌；B1–B5 修正完成；量化基準見 §11.7；鏈路分析見 §12；最優設計結論見 §14。

- 作者：Angela AI Development Team
- 版本：7.5.0-dev（設計稿）
- 相關提交：§X #261（MathVerifier 單一計算源 + 無狀態數學無情緒）、§X #262（domain_ripple 領域引擎框架）
- ANGELA-MATRIX：`[L4] [βγδ] [A] [L9+]`（架構級設計）

---

## 0. 一句話總結

把「每次輸入都無條件跑一遍的重計算」拆成 **分級（Tier）+ 區塊（Block）+ 快照（Snapshot）**
三層機制：大多數輸入走 **快思考快路徑**（只做 T2 分類 + 直接回答），只有「需要做行為生成 /
深層認知」的輸入才喚醒 T3 重計算。這和 §X #262 的「無狀態運算無情緒」是同一個開關：
**無狀態輸入連狀態漣漪都不該觸發，自然也不該觸發重計算**。

---

## 1. 現狀：現在到底「每次都重算了什麼」

從程式碼實際讀到的（非猜測）：

| 觸發點 | 位置 | 每次成本 | 是否每次都該跑 |
|--------|------|----------|----------------|
| 軸更新後處理 | `core/engine/state_matrix.py:906` `_post_update` | 對**每個軸更新**都跑 `apply_intent_gravity` + `apply_inter_dimensional_drag` + `state_store.update_state`（全域同步）+ callbacks + `_check_thresholds` + `_record_history` | 多數可延後/合併 |
| 影響矩陣傳播 | `state_matrix.py:1012` `compute_influences` | O(dims²) 跨軸影響，全部重算 | 只在有軸實質變動時才需要 |
| 歷史趨勢/異常 | `core/state/temporal.py:207/224/274` `trend/anomalies/correlation` | 每次呼叫都對 window 重算 mean/std → O(window) | 可用遞增統計避免 |
| 吸引子導航 | `ai/memory/attractor_field.py:215,263` `compute_gradient`/`navigate` | 預設 7 個吸引子 × 5 維歐氏距離，navigate 最多呼叫 5 次 → ~35 次距離計算 / 每次輸入 | 無狀態輸入不需要 |
| 神經推論 | `ai/ed3n/core_network.py`、`ai/ed3n/snn/snn_core.py`、`ai/garden/snn_core.py` | 最重一層（網路前向） | 只在需要生成時 |

**關鍵觀察**：
1. 現有 `StateMatrix.history` 與 `TemporalState` 都已經是「快照」機制，但它們存**完整快照**，
   且查詢時（trend/anomalies/correlation）**每次都從頭重算統計**——這正是用戶擔心的事。
2. 沒有任何「快路徑」：現在 `CognitivePipeline.process` 一旦掛了 `attractor_field`，
   就對**每個輸入**跑完整導航 + 漣漪 + 影響，包括純算式 `917 * 814`。
3. §X #262 的 `route_domain()` 已經能判斷「無狀態 vs 有意義」——它本身就是天然的 T2 分類器，
   只是目前只拿來決定「要不要產生情緒」，還沒拿來決定「要不要跑重計算」。

---

## 2. 核心心智模型：三個分離

```
輸入 ──► [分類器 T2] ──► 無狀態? ──是──► 直接回答（快路徑，不碰 T3）
                     │
                     否（有意義 / 需生成）
                     ▼
              [依區塊髒標記] 只重算被觸碰的區塊 T1 快取
                     ▼
              [必要時喚醒 T3] 吸引子導航 / 影響傳播 / 神經推論
```

三個要分清楚的概念：

- **等級（Tier）= 重算頻率 / 成本等級**（靜態 → 慢變 → 每輸入 → 重推論）。
- **區塊（Block）= 狀態/計算圖的分割單位**（按軸分塊；輸入只弄髒相關區塊）。
- **快照（Snapshot）= 歷史 + 遞增統計**（不每次重算，而是滾動維護 mean/std/trend）。

---

## 3. 計算分級（Tier）定義

| Tier | 內容 | 重算觸發 | 快取策略 | 現有對應 |
|------|------|----------|----------|----------|
| **T0 靜態** | 軸 schema、語義錨點、吸引子座標、影響矩陣、formula config | 啟動/配置變更時一次 | 永久快取 | `_init_semantic_anchors`、`_build_default_attractors`、`influence_matrix` |
| **T1 慢變（髒標記）** | 狀態均值、跨軸影響結果、拖拽累積、歷史滾動統計（mean/std/trend） | 某區塊髒了才重算 | 髒標記 + 快取值；快照遞增維護 | `compute_influences` 結果、`TemporalState` 統計 |
| **T2 每輸入（輕）** | 目前狀態向量、領域路由/分類（無狀態 vs 有意義）、有意義時的輕量漣漪 | 每次輸入都跑（但極便宜） | 不快取（天然無狀態） | `get_current_state`、`route_domain`、輕量漣漪 |
| **T3 重推論（按需）** | 吸引子導航、完整影響傳播、CoreNetwork/SNN 前向、因果推理 | **只有** T2 判定「需行為生成 / 深層認知」且狀態夠「有趣」 | 結果短暫快取（同回合復用） | `GradientField.navigate`、`compute_influences`、`CoreNetwork.forward` |

**原則**：T2 永遠跑（便宜、且它正是分類器）；T1 只在髒時跑；**T3 預設不跑**，由 T2 的「有意義 + 需生成」信號喚醒。

---

## 4. 區塊（Block）：把狀態與計算圖分塊

把 6+1 軸切成邏輯區塊，每塊自帶 `dirty` 旗標與快取派生值：

| Block | 軸 | 典型觸碰來源 |
|-------|----|--------------|
| B-physio | α | 生理/節律/張力 |
| B-cog | β | 專注/混淆/學習 |
| B-emo | γ | 情緒（高興/恐懼/驚訝） |
| B-social | δ | 社交/連結 |
| B-math | ε | 數理/邏輯 |
| B-meta | θ | 元認知 |

**運作方式**：
- 一個輸入（例如純算式 `917 * 814`）經 T2 判定無狀態 → **不髒任何區塊** → 不跑 T1 重算、不跑 T3。
- 一個有意義的數學題 → 只髒 `B-math`（與 `B-emo` 若產生高興）→ 只對這兩塊做 T1 重算；
  α/δ/θ 區塊保持快取，不做跨塊全量重算。
- 這就是「部分失效 / 增量重算」：輸入只重算它真正影響的區塊，其餘區塊的快取原樣複用。

**和現有程式碼的對接**：`StateMatrix4D.dimensions` 已經是 per-axis 結構；
區塊只是在其上加一層「dirty flag + cached derived」的包裹，不需要推翻現有設計。

---

## 5. 快照（Snapshot）：歷史改成「遞增維護」而非「每次重算」

現狀問題：`TemporalState.trend/anomalies/correlation` 每次呼叫都對 window 重算 mean/std（O(window)）。
若一回合內呼叫多次（不同軸/欄位），就是重複 O(n) 掃描。

改法（設計，未實作）：
- 在 `record()` 時用 **Welford 遞增演算法** 同步維護每個 (axis, field) 的 `count/mean/M2`，
  異常檢測的 z-score 直接由快取值算出，O(1)。
- trend 的斜率維護「上一筆」與「視窗首尾」即可，不重掃。
- 快照本身仍按區塊切：每個 Block 一份 rolling snapshot（cap 長度），查詢跨區塊時各自取自己的快取。
- 提供 `SnapshotQuery` 已存在（`temporal.py:49`），可直接擴充 `block` 維度。

好處：歷史快照繼續保留（用戶要的「建立出歷史快照」），但**讀取成本從 O(n) 降到 O(1) 遞增**，
符合「不需要每次都計算的就不要每次算」。

---

## 6. 運行期重組（Runtime Reorganization）

由一個輕量 **TierScheduler** 在每個輸入入口決定本回合要跑哪些 Tier/Block：

```
def route_turn(text, state):
    engine, value, cls = route_domain(text)        # T2 分類（已有）
    if value is None or not cls["meaningful"]:
        return FAST_PATH   # 只回答，跳過 T1 重算與 T3
    touched = engine.touched_blocks(cls)            # 例如 {B-math, B-emo}
    invalidate(touched)                             # 只髒相關區塊
    if needs_generation(state, cls):                # 狀態夠「有趣」/ 需行為
        run_t3(state, touched)                      # 吸引子導航 + 影響 + 推論
    return NORMAL_PATH
```

`needs_generation` 的判斷可依：狀態偏離基線（anomaly）、有未決意圖、輸入是開放式提問等。
這讓「重組計算」根據**分級 + 當下狀態**動態決定，而非固定全跑。

**和既有快路徑的關係**：這把 §X #262 的「無狀態數學無情緒」自然升級成
「無狀態輸入 → 不髒區塊 → 不跑 T3 → 直接回答」，一脈相承。

---

## 7. 現有模組如何對接到此框架（不是重寫，是統一）

| 現有模組 | 在框架中的角色 | 需要補的 |
|----------|----------------|----------|
| `StateMatrix4D` + `dimensions` | T1 狀態本體 + 區塊基礎 | 加 per-block dirty flag + cached derived |
| `TemporalState` | 快照/歷史 | 改為 Welford 遞增統計（O(1) 查詢） |
| `GradientField` / `AttractorField` | T3 吸引子導航 | 預設不跑；僅 T2 喚醒時跑 |
| `compute_influences` | T3 跨軸影響 | 改為髒標記觸發，非顯式全量 |
| `CoreNetwork` / `SNN` | T3 神經推論 | 僅需生成時呼叫 |
| `domain_ripple.route_domain` | **T2 分類器（已存在）** | 額外回傳 `touched_blocks` |
| `CognitivePipeline` | 組裝範例 | 用 TierScheduler 取代「有 attractor_field 就全跑」 |

結論：**大部分零件已存在**，本框架是把它們「按 Tier/Block 重新編排 + 加髒標記/遞增統計」，
不是從零蓋一套。風險與複雜度可控。

---

## 8. 風險 / 注意 / 待決問題

1. **快取陳舊（staleness）**：T1 快取必須在「正確的髒標記」下失效，否則狀態會飄。
   → 髒標記的最小單位要 = 區塊，不能太粗。
2. **部分重算的正確性**：跨區塊影響（影響矩陣）意味著只重算 B-math 可能漏掉它對 B-cog 的拖拽。
   → 區塊失效要沿「影響矩陣」傳播（B-math 髒 → 依 influence_matrix 把相依區塊也標髒）。
3. **不要過度工程**：T3 快路徑的效益取決於實際流量。
   → 見 Phase 1：先**量化**現有每回合成本，再決定是否值得。
4. **快照與隱空間**：用戶提到「(隱)空間」——StateMatrix 的座標空間 + 吸引子梯度場就是「隱空間」。
   快照不僅存數值，也可存「座標點 + 最近吸引子」做空間鄰近查詢（已是 `GradientField` 的能力）。

---

## 9. 建議執行階段（Phase）

- **Phase 0（本文件）**：想清楚、寫紀錄。✅
- **Phase 1 — 量化**：**DONE（見 §11.7 實測表）**。已量出純算術 ~85µs、navigate ~1ms（生產 stub→0）、
  `update_alpha` ~227µs、`anomalies` O(history) 全掃。瓶頸與收益已確認。
- **Phase 2 — T1 髒標記 + 遞增快照**：`TemporalState` 改 Welford；`StateMatrix` 加 per-block dirty +
  cached derived。無行為改變，純優化讀取。
- **Phase 3 — 區塊分割**：定義 Block 映射 + 沿影響矩陣的失效傳播。
- **Phase 4 — TierScheduler + 快路徑**：在聊天/查詢入口接 `route_domain` 信號，
  無狀態輸入直接跳過 T3。
- **Phase 5 — T3 按需喚醒**：吸引子導航 / 影響傳播 / 神經推論改為「僅需生成時」呼叫，
  結果同回合短暫快取。

---

## 10. 開放問題（留待實作時定）

- `needs_generation` 的閾值如何依 `anomaly` / 意圖 / 輸入類型校準？
- 快取鍵要不要含「對話上下文雜湊」以避免跨使用者污染？
- 區塊粒度要不要比「按軸」更細（單一 field 級）？過細會增加髒標記管理成本。
- 神經推論結果的「短暫快取」有效期多長（同回合？同話題？）

---

> 本文件為設計紀錄，不含實作。實作前先走 Phase 1 量化，確認收益再動手，
> 避免過度工程。與 §X #261 / #262 同一脈絡：把「不必要的重計算」和「不必要的情緒/狀態」
> 一起消掉，系統就從「每次都全跑」變成「大多數走快思考」。

---

# 11. 全專案運算現狀盤點（數 / 理 / 化引擎、漣漪 / 情緒 / 狀態、矩陣）

> 本章把前面設計落回「當下程式碼真實長什麼樣」，回答三件事：
> **(a) 快能多快 / 慢能多慢（實測）**；**(b) 每個引擎是否正確**；
> **(c) 是否夠細膩、有沒有被忽略的缺口**。所有結論基於實際讀碼 + 實測，
> 非猜測。對應用戶「整個專案都要想清楚」。

## 11.1 模組接線圖（事實）

- `ai/memory/domain_ripple.py`（數/理/化引擎 + 有界認知）與 `ai/memory/cognitive_pipeline.py`
  目前**只有彼此引用**；全專案 grep `route_domain / DomainRippleEngine / apply_ripple_to_state`
  只命中這兩個檔。→ **尚未接進生產 chat 路徑**。
- 生產用的 `StateMatrixAdapter.gradient_field` 是 **stub**
 （`_GradientFieldProperty.compute_gradient / navigate` 回傳空導航，`navigation_steps:1`、
  `nearest_attractors:[]`）。→ 生產路徑中「吸引子導航」目前是 **no-op**。
- 生產用的 `CognitivePipeline` 也未被任何路由/服務 instantiate（只有單元測試建它）。

**結論（關鍵）**：當下生產中 **數學不產生情緒、也不跑吸引子導航**。
§X #261/#262 的「有界認知」是**已設計、已測、但未接線**的框架。
因此「快/慢」問題在生產中**目前不成立**；本文是預先設計 + 待接線盤點。
這同時意味著：任何「快思考」改造都必須先決定**要不要、在哪接線**，否則優化對象不存在。

## 11.2 數學引擎

- `services/math_verifier.py:compute_arithmetic` = **單一計算源**（中文轉換、`%`、`//`、
  一元正負 `operator.pos/neg` 修正均已修）。**正確性：✅**。
- `MathRippleEngine.compute()`（`math_ripple_engine.py:627`）：自帶 tokenize + 運算，
  **再被 `compute_arithmetic` 覆寫結果**。第一遍手算實質浪費（僅用來產漣漪）。
  → 冗餘但不影響正確；可改成「只做結構分析、數值交給 MathVerifier」。
- 深度自動偵測 `_estimate_result_magnitude`（`math_ripple_engine.py:170`）是 **regex 粗略估**
  （取最大數字、算乘法次數）。對非數值表達式可能誤判 ripple depth。→ **可接受但不總是精確**。
- **細膩度缺口**：MathRippleEngine 產生的漣漪幅度**源頭未 clamp**
  （`alpha_arousal` 可達 0.8、`gamma_excitement` 0.7，見 `_compute_single` 乘法/冪分支），
  而 `domain_ripple` 自家的 Physics/Chemistry `make_ripples` 都把幅度 clamp 到 ≤0.5/0.4。
  → 同為「有意義」時，**數學題的情緒強度远強於物理/化學題**，幅度基準不一致。

## 11.3 物理引擎（`PhysicsDomainEngine`）

- `compute()` 只是把內嵌算術轉交 `MathVerifier`；**不是真正解速度/力/能量的物理公式**
  （沒有 `v=at`、`F=ma`、`E=mc²`、`p=mv` 的求解）。
- **細膩度（好）**：依主導物理量給不同漣漪形狀——
  `speed/accel→arousal+excitement`、`force→tension+fear`、`energy/momentum→excitement`、
  `mass/dist/pressure→clarity`。設計是**有語意區分**的。
- **正確性**：算式結果正確；但本質是「帶物理關鍵字的算術」，不是物理求解器。
  → 「是否夠細膩」：**初階**，可擴充真公式（見 §11.9 P2）。

## 11.4 化學引擎（`ChemistryDomainEngine`）

- `_molar_mass()`（`domain_ripple.py:424`）**真實正確**：內建 ~40 元素週期表，
  能解析 `H2O`、`C6H12O6`、`NaCl` 等。→ **正確性：✅**。
- **文檔/實作不符（minor）**：docstring 寫「molar mass + ideal gas」，
  但 `compute()` 只算莫耳質量，未實作 ideal gas。
- **細膩度缺口（⚠️）**：`make_ripples()` 回傳 `beta_learning` 與 `gamma_anticipation`，
  但 `apply_ripple_to_state()`（`domain_ripple.py:110`）**只處理固定 key 集合**，
  並不包含 `beta_learning` / `gamma_anticipation` → 化學的「學習 / 期待」認知被**靜默丟棄**。
  （`cognition_deltas` 路徑會補 `gamma_anticipation`，但 chemistry 漣漪本身的 `beta_learning` 仍丟失。）
- 週期表僅 ~40 元素，常見足夠；稀有元素會被判 `can_handle=False`。

## 11.5 漣漪 / 情緒 / 狀態

- 分類規則（無狀態 vs 有意義）清晰且正確：無狀態（`917*814`、`1+1`）**不產生任何情緒/狀態**。✅
- **重大細膩度/正確性缺口（⚠️）**：`apply_ripple_to_state` 與
  `CognitivePipeline._apply_cognition_deltas` 都**直接寫 `axis.values[key]=...`**，
  **繞過 `StateMatrix4D.update()`** → 因此**不觸發 `_post_update`**
  （`state_matrix.py:906`：意圖重力、跨維拖拽、全域 `state_store` 同步、history、callbacks、thresholds 全跳過）。
  → 數學產生的情緒**不會被重力/拖拽動力學整合**，也**不會寫入全域 state_store**
  （其他消費者如 `digital_life_integrator`、router 看不到）。這是直接違背「狀態應被整合」的隱含預期。
- `cognition_deltas` 的 `_DELTA_MAP`（`cognitive_pipeline.py:176`）完整涵蓋
  `gamma_happiness/excitement/sadness/fear/surprise/anticipation/trust`、`beta_*`、
  `alpha_*`、`delta_*`、`epsilon_*` → **無幽靈維度**。✅（但 chemistry 的 `beta_learning` 仍丟失，見 §11.4）
- clamp 到 `[0,1]`：✅ 情緒不會爆走；但疊加在 0.5 基線上，強漣漪會很快飽和。可接受。

## 11.6 矩陣 / 影響 / 隱空間

- `_post_update`（`state_matrix.py:906`）每次軸更新都做：
  **複製 6 軸全量快照進 history**（`_record_history` 拷貝 alpha/beta/gamma/delta/epsilon/theta）
  + 意圖重力 + 跨維拖拽 + `state_store.update_state`（全域同步）+ callbacks + thresholds。
  → 單次 `update_alpha` **~227µs**，且每次存「全量 6 軸快照」而非差量。⚠️ 偏重。
- `compute_influences()`（`state_matrix.py:1012`）O(dims²) + 空間因子 + influence applicator，
  **~363µs**；**顯式呼叫才跑**，非每次更新。OK。
- `TemporalState`：
  - `trend` ~44µs（掃 `window=50`）。✅
  - **`anomalies` 掃「整個 history（上限 500）」找前 10 個異常**
    （`temporal.py:233` `for snap in reversed(self.history)` 無 window 限制）→ **O(history) 非 O(window)**。⚠️
    這**正是用戶擔心的「每次都重算」**：隨 history 增長只會變慢，且每回合若多次呼叫更明顯。
  - `correlation` ~166µs（掃兩條 series）。OK 但同樣全量掃。
- 隱空間（座標 + 吸引子梯度場）：設計細膩（高斯衰減 `_gaussian_decay`、7 個語義預結構化吸引子、
  `navigate` 沿梯度走最多 5 步）。**但生產 adapter 是 stub**，且 `CognitivePipeline.process`
  對「無狀態輸入」**照樣呼叫 `navigate`**（`cognitive_pipeline.py:232`，不判 meaningful）→
  即使用戶要的「無狀態不該重算」也沒在 lab 路徑落實。

## 11.7 快慢邊界（實測，Windows / venv 3.14，單位 µs，n=2000 除非註明）

| 運算 | p50 | p95 | max | 備註 |
|------|-----|-----|-----|------|
| `compute_arithmetic('917 * 814')` | 85 | 255 | 1925 | 純算術，最便宜之一 |
| `compute_arithmetic('1+1')` | 121 | 546 | 11680 | |
| `route_domain` 無狀態 | 298 | 1268 | 29332 | 要試 3 個引擎（化學掃公式/物理掃關鍵字/數學算） |
| `route_domain` 有意義 | 74 | 280 | 6702 | 化學/問句命中快 |
| `attractor navigate`（5步, 7吸引子） | **1001** | 4149 | 38135 | **最貴單項，是純數學 ~12×**；生產中是 stub 故實際 0 |
| `update_alpha`（含 `_post_update`） | 227 | 994 | 8661 | 含 6 軸全量快照拷貝 |
| `compute_influences` | 363 | 1336 | 9140 | O(dims²)+空間因子 |
| `temporal.trend` | 44 | 142 | 3769 | 掃 window=50 |
| `temporal.anomalies` | 125 | 404 | 5300 | **掃整個 history（O(500)）** |
| `temporal.correlation` | 166 | 580 | 6737 | |
| 全 domain ripple 管線（有意義） | 98 | 420 | 3356 | `route+ripple+apply`；因直接寫 values 不進 `_post_update` 故便宜 |

**解讀**：
- 最便宜：純算術 ~85µs、trend ~44µs。
- 最貴單項：**attractor navigate ~1ms**（生產是 stub → 實際 0；lab 路徑則是純數學 12×）。
- 瓶頸在「每次都無條件跑」的組合：若每輸入都 `route_domain`(~300µs) + `navigate`(~1ms) +
  `update`(~227µs) → **~1.5ms / 輸入**，且 `anomalies` 隨 history 增長而變慢。
- **快思考改造後預期上限**：無狀態輸入只跑「輕量預篩 + 直接回答」，
  目標 **<100µs**（砍掉 navigate + update 的全量快照 `_post_update`）。

## 11.8 正確性 / 細膩度總評

| 項目 | 正確性 | 細膩度 / 缺口 |
|------|--------|----------------|
| 數值計算（MathVerifier） | ✅ 正確 | 單一源，良 |
| 化學莫耳質量 | ✅ 正確 | 週期表 ~40 元素；ideal gas 未做（文檔不符） |
| 物理 | ⚠️ 算式正確，非真物理求解 | 漣漪形狀有語意；可接真公式 |
| 情緒/狀態 | ⚠️ 漣漪旁路 `_post_update`，不被重力/拖拽/全域 store 整合 | chemistry `beta_learning/anticipation` 丟失；三引擎幅度基準不一致 |
| 矩陣/影響 | ✅ 影響計算是對的 | `_post_update` 每次存全量快照；`anomalies` 全量掃描 |
| 隱空間/吸引子 | ✅ 設計細膩 | 生產 adapter 是 stub；lab 路徑對無狀態也照跑導航 |

## 11.9 建議修正清單（優先級）

**P0（接線前必做）**
1. 決定 `CognitivePipeline` / `domain_ripple` 是否接進生產 chat 路徑；
   若接，先用 TierScheduler（§6）讓**無狀態輸入跳過 `navigate`** 與 `_post_update` 全量快照。
2. 修 chemistry `beta_learning` / `gamma_anticipation` 被丟失：
   在 `apply_ripple_to_state` 補這兩 key，或改 `make_ripples` 用已支援的 key。

**P1（細膩度 / 一致性）**
3. 明確設計意圖：漣漪寫入**要走 `update()` 或顯式觸發 `_post_update`**（使情緒被重力/拖拽/store 整合），
   或**文檔化「漣漪是旁路、不進全域 store」**並據此調整消費者預期。
4. `TemporalState.anomalies` 改為 **window 限制 / 遞增統計**（Welford），消除 O(history) 重掃。
5. 三引擎漣漪幅度**統一到同一 clamp 上限**（數學題目前過強）。
6. `route_domain` 加**輕量預篩**（無數字且無化学式且無物理/化學關鍵字 → 直接返回 None），
   避免對一般閒聊浪費 ~300µs 跑 3 個引擎。

**P2（擴充）**
7. 物理引擎接真公式（`v=at`、`F=ma`、`E=mc²`、`p=mv`、`P=mgh`）。
8. 化學補 ideal gas / 擴充元素表。
9. `history` 改**差量快照**（只存變動軸），減少 `_post_update` 拷貝成本。

> 小結：數值計算與化學莫耳質量**正確**；物理是「帶語意的算術」；情緒/狀態與矩陣的
> **正確性尚可，但細膩度有數處被忽略的缺口**（旁路不整合、anomalies 全掃、幅度不一致、
> chemistry 認知丟失）。快路徑的「快」在生產中**目前是 0 成本因為根本沒接**，
> 真正的優化對象是「接線後如何不讓無狀態輸入觸發 navigate / 全量 _post_update」——
> 與 §6 的 TierScheduler 完全對齊。

---

## 12. 整條聊天鏈路與耗時（Chain Latency / Bottleneck Analysis）

> 2026-07-14 實際讀 `api/routes/chat_routes.py` + `chat_service.py` + `services/llm/router.py`，
> 把「每次輸入」在生產中真正跑的順序與成本攤開。結論：**微觀 tiering（attractor/state）省的是
> 微秒，相對 LLM 呼叫是 0；真正的槓桿在「鏈路頂端的決策分流」與「每輪恆開的分析器」**。

### 12.1 生產 `_handle_chat_request` 實際順序（`chat_routes.py:1076`）

| # | 步驟 | 內容 | 成本量級 | 可否跳 |
|---|------|------|----------|--------|
| 1 | 驗證/截斷 | 長度、session init | µs | — |
| 2 | **數學雙軌** | `_try_math_verification` → `MathVerifier.verify()` → 命中即 early-return（**現已呼叫 `apply_domain_cognition`**） | µs | ✅ 命中即短路（跳過 3–13） |
| 3 | 建上下文 | session dict 組裝 | µs | — |
| 4 | **情緒分析** | `EmotionAnalyzer.analyze()`（可能 LLM-backed）+ crisis + bio stimulus | ms / 潛在 LLM | ⚠ 可輕量化 |
| 5 | 注入 | lifecycle / intent / modality / awareness | µs | — |
| 6 | IntentRegistry 路由 | `_try_intent_routing` | µs | — |
| 7 | 建 LLM 上下文 | bio state + `StateMatrix4D` 複製 + **ED3N 歷史檢索 O(history)** + dialogue + memory | ms（隨 history 線性成長） | ⚠ 限窗 |
| 8 | 執行閘 | `QueryClassifier`（×1）+ `ExecutionGate` + `IntentRegistry` | µs / 潛在模型載入 | ⚠ 高置信本地路徑可跳 |
| 9 | Agent 自動路由 | `AgentManager` + `Orchestrator` | µs | ⚠ |
| 10 | 因果預測 | `causal.predict` / routing adjustment | µs | — |
| 11 | **LLM 生成** | `generate_response` | **秒級（網路/LLM）← 主導瓶頸** | ❌ 核心 |
| 12 | 後處理 | causal learning / 格式化 | µs | — |

### 12.2 瓶頸結論

- **主導成本 = LLM 呼叫（步驟 11）**，秒級。其餘全部 µs~數十 ms。
- **每輪恆開的分析器**（步驟 4/8/9）：`EmotionAnalyzer`、`QueryClassifier`（×2）、`ExecutionGate`、
  `IntentRegistry`（×2）、`AgentOrchestrator`、`causal.predict`。多數為本地，但部分可能 LLM-backed
  或首次載入模型；它們在**每個 token** 都跑，是僅次於 LLM 的系統性開銷。
- **ED3N 歷史檢索（步驟 7）**：`for entry in history:` 對每個歷史項做編碼，O(history) 隨對話長度線性成長
  —— 與 §11.8 的 `anomalies` 全掃是**同一類「長對話線性成長」問題**，應限窗。
- **attractor field**：生產中 `StateMatrixAdapter.gradient_field` 是 **stub（回傳空導航）**，成本 = 0。
  實驗室 `navigate()` ~1ms，相對 LLM 仍是 0。

### 12.3 與 §11.7 基準的對照

§11.7 微基準：compute_arithmetic ~85µs、route_domain 無狀態 ~298µs（已加 prefilter→更低）、
attractor navigate ~1001µs（prod stub→0）、full domain pipeline ~98µs。這些全部 **< 1.5ms**，
相對 LLM 秒級可忽略。因此「快思考」在生產的真正價值不是微觀 tiering 本身，而是
**用 tiering 的分流判斷去避免 LLM 與恆開分析器**（見 §14）。

---

## 13. 已修復問題清單（2026-07-14，B1–B5）

| ID | 問題 | 修正 | 位置 |
|----|------|------|------|
| B1 | `apply_ripple_to_state` 漏映射 `beta_learning`（化學知識增長認知丟失） | 補回 `beta_learning` 映射；`gamma_anticipation` 已在 | `ai/memory/domain_ripple.py` |
| B2 | `TemporalState.anomalies` 全歷史掃描 O(history) | 改掃 `self.history[-window:]`（預設 threshold=0.5，最多回傳 10） | `core/state/temporal.py` |
| B3 | 三引擎漣漪幅度不一致（數學高興/重複幅度缺全局上限） | 新增 `RIPPLE_DELTA_CAP = 0.5`，`_add()` clamp 每次增量 | `ai/memory/domain_ripple.py` |
| B4 | `route_domain` 對閒聊也跑 3 引擎（~300µs 浪費） | 新增 `_has_domain_signal` 預篩（物理關鍵字/化學字/數字/Capital 開頭） | `ai/memory/domain_ripple.py` |
| B5 | `CognitivePipeline` 無狀態輸入仍呼叫 `navigate()` | 無狀態跳過 attractor 導航（生產 stub 無意義） | `ai/memory/cognitive_pipeline.py` |

**外加修正 / 接線**
- **共用入口 `apply_domain_cognition()`**：`CognitivePipeline`（實驗室）與 `chat_routes`（生產）皆委託同一函式，雙路徑不可能分歧。
- **生產接線**：`chat_routes._try_math_verification` 在 `MathVerifier` 驗證後呼叫 `apply_domain_cognition(matrix, user_message)`；無狀態 → no-op。
- **修復假重複 bug**：pipeline 原在委派前就把文字塞進 `_recent_math`，導致自己被分類為重複；改為委派**後**才 append。
- **移除重複**：`CognitivePipeline._apply_domain_cognition` 原有的 `_DELTA_MAP` / `_apply_cognition_deltas` 刪除，改用共用 `apply_domain_cognition`。

**測試**：`tests/ai/memory/test_domain_ripple.py`（25 過）、`tests/ai/memory/test_cognitive_pipeline.py`（6 過）、
新增 `tests/core/test_temporal.py`（B2）、domain_ripple 加 B1/B3/B4 回歸測試。共 32 項全過。

---

## 14. 最優設計結論（Optimal Design）

> 需求：「最優不是最單一，也要考慮全面性、適應性」。即最優 = **全面（覆蓋所有領域且一致）+ 適應
> （依輸入分級決定喚醒哪些子系統）**，而非「某條路徑單點最快」。

### 14.1 什麼不是槓桿
- 把 attractor/state 微觀運算再壓到極限（已是 µs~1ms），相對 LLM 秒級效益 ≈ 0。
- 把 `domain_ripple` 框架本身再加速：全領域管線 ~98µs，已可忽略。

### 14.2 真正的槓桿（全面 + 適應）
1. **鏈路頂端決策分流（dual-rail）**：數學（已做）之外，擴展「本地可解即短路、不喚醒 LLM」。
   這是 §0 快路徑的**生產實作**：T2 分類命中 → 直接回答，跳過步驟 3–13。
2. **每輪分析器依必要性分閘**：高置信本地路徑已解時，跳過 `ExecutionGate` / Agent routing；
   無需情緒路由的輸入輕量化 `EmotionAnalyzer`。
3. **長對話線性成長限窗**：`ED3N` 歷史檢索、`TemporalState.anomalies`、`_post_update` 歷史記錄
   統一改視窗/差量（§11.8 已示範 anomalies 限窗）。
4. **一致性（全面）**：所有領域（數/物/化）走同一 `apply_domain_cognition` 入口、同一幅度上限、
   同軸 schema；無狀態 → 零情緒（符合 §X #261/#262）；有意義 → 有界認知。

### 14.3 最終決策
- **保留並接線** domain_ripple 框架（微觀 tiering 的「狀態傳遞」層），作為「本地可解 / 有界認知」
  的單一來源；它不直接省 LLM 時間，但保證「無狀態零情緒、有意義有界認知」在所有路徑一致。
- **快思考的主優化移到 TierScheduler 的「決策分流」層**（§6）：用 T2 分類結果決定是否短路 LLM 與
  恆開分析器 —— 這才是省「秒級」的槓桿。
- **attractor / 狀態快照** 維持為「深度模式才喚醒」的可選重計算（§6 T3），生產 stub 不影響快路徑。
- **驗證方式**：本輪已量化（§11.7 微基準 + §12 鏈路分析）、已修復（B1–B5）、已接線、已補測試。
  後續 TierScheduler 實作時應以「短路率（本地可解比例）」與「LLM 呼叫次數」為首要指標，
  而非微觀 µs。

