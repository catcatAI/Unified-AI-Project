<!--
  =============================================================================
  FILE_HASH: Initial
  FILE_PATH: docs/06-project-management/CAUSAL_CHAIN_COMPLETENESS.md
  FILE_TYPE: analysis
  PURPOSE: 因果鏈完整性分析 — 真實自主性的衡量標準與當前差距
  VERSION: 1.0.0
  STATUS: active
  LANGUAGE: zh-tw/en
  LAST_MODIFIED: 2026-06-28
  AUDIENCE: developers, agents
  =============================================================================
-->

# 因果鏈完整性分析 v1.0

> **核心問題**: 專案宣稱「自主性」但真正的因果鏈傳遞有多深？
> 組件間的因果是否真實可驗證？還是只是資料被寫入但從未被消費？
>
> **一句話結論**: 基礎建設扎實（~85%），但因果鏈深度極淺 — 多數組件計算結果從未實際驅動其他組件的行為改變。
> 自主性停留在「記錄與註解」層級，尚未到達「傳遞與驅動」層級。

---

## 目錄

1. [什麼是真實的「完成」？](#1-什麼是真實的完成)
2. [因果鏈完整性三層級](#2-因果鏈完整性三層級)
3. [核心組件因果鏈深度分析](#3-核心組件因果鏈深度分析)
4. [關鍵發現：斷裂的因果鏈](#4-關鍵發現斷裂的因果鏈)
5. [分數修正：誠實的自主性評分](#5-分數修正誠實的自主性評分)
6. [改善路線：從「記錄」到「驅動」](#6-改善路線從記錄到驅動)
7. [驗證標準](#7-驗證標準)

---

## 1. 什麼是真實的「完成」？

### 1.1 虛假的完成（❌ 目前專案常見的模式）

| 模式 | 表現 | 出現頻率 |
|:-----|:------|:---------:|
| **記錄當作完成** | 組件 A 計算結果並寫入 list/dict，但無人消費 | 🔴 高（AutonomousLifeCycle, CausalReasoning） |
| **文字注入當作影響** | 組件 A 的輸出轉為文字塞進 LLM Prompt，LLM 可能忽略 | 🔴 中（EmotionSystem, FormulaMetrics） |
| **規則當作狀態機** | 用 if/else 寫決策，但沒有持續狀態演化 | 🟡 中（ExecutionGate, Heartbeat） |
| **測試通過當作驗證** | 單元測試測「方法回傳正確值」，但沒測因果鏈是否閉合 | 🟡 高（幾乎所有測試） |
| **Callback 註冊當作接線** | 註冊了 callback 但 callback 內什麼都不做 | 🟡 中（LifeCycle callbacks） |

### 1.2 真實完成的定義

一個組件要算「真實完成」必須滿足以下所有條件：

```
Causal Chain Completeness (C³) = 
  State_evolution × Cross_component_propagation × Sustained_operation × Verifiable_effect
```

| 維度 | 定義 | 門檻 |
|:-----|:------|:----:|
| **S (State evolution)** | 組件有明確的內部狀態，狀態會隨時間自然演化（不需外部觸發） | 狀態資料結構 + 時間驅動的演化邏輯 |
| **P (Cross-component propagation)** | 組件 A 的狀態變化 → 組件 B 偵測到變化 → 組件 B 改變自身行為 | 單元測試可追蹤完整的 A→B→C 鏈 |
| **F (Feedback loop)** | 組件的輸出會透過因果鏈影響自己的未來輸入（閉環） | 可驗證的自我修正行為 |
| **V (Verifiable effect)** | 因果鏈的每一環都可透過測試或監控告警驗證 | 斷言式的鏈完整性測試 |

### 1.3 評分標準

```
Score = 基礎架構 × 鏈深度 × 閉環率

鏈深度:
  0 = 組件孤立運算，無人消費（❌ AutonomousLifeCycle, CausalReasoning, EmotionSystem）
  1 = 組件可影響緊鄰的下游（🟡 MetaController → NeuroAutoSelector）
  2 = 組件可影響 2 層下游（🟢 ExecutionGate → LLM → Response）
  3+ = 組件影響形成閉環（🟢 Heartbeat → Bio → Spatial → Heartbeat）

閉環率:
  0% = 無閉環（單向資料流）
  50% = 有部分閉環但斷裂
  100% = 完整閉環，可自我維持
```

---

## 2. 因果鏈完整性三層級

### 層級 1: 記錄級 (Log Level) — 當前主流

```
[Data In] → 計算 → [Output] → 寫入記憶體/DB → [無人消費]
```

| 組件 | 輸入 | 計算 | 輸出 | 誰消費？ |
|:-----|:-----|:------|:-----|:--------:|
| AutonomousLifeCycle | 5 個公式 | 計算 metrics + 做決定 | LifeDecision | ❌ **無人**（只記錄到 decision_history） |
| CausalReasoningEngine | observations | Pearson/Granger | relationships | ❌ **無人**（只存在記憶體中） |
| EmotionSystem | context text | TextBlob 情感分析 | EmotionalState | 🟡 僅文字注入到 LLM Prompt |

### 層級 2: 傳遞級 (Propagation Level)

```
[Data In] → 計算 → [Output] → 下游組件讀取 → 行為改變
```

| 組件 | 鏈 | 深度 |
|:-----|:---|:----:|
| Heartbeat | CPU% → BioIntegrator stress → Cerebellum posture | 2-3 層 ✅ |
| DigitalLifeIntegrator | Phase transition → _apply_state_behaviors → StateMatrix/Bio | 2 層 ✅ |
| MetaController | Confidence input → EWMA → threshold suggestion | 1 層 🟡 |

### 層級 3: 閉環級 (Feedback Level) — 理想目標

```
[State A] → [Component X] → [State B] → [Component Y] → [State A']
                                                          ↑
                                                          └── 回饋影響自身
```

**目前沒有任何組件達到此等級。**

---

## 3. 核心組件因果鏈深度分析

### 3.1 AutonomousLifeCycle (410L) — 🟡 C³ = 2.0/10 (was 0.1/10, ✅ fixed 2026-06-28)

**修復摘要**: `_execute_decision()` 已加入，將 4 種決策類型分派至 `BehaviorExecutor`。決策不再只記錄不執行。

```python
# 修復後: 決策被執行
async def _lifecycle_loop(self):
    decision = self._evaluate_and_decide(metrics)
    if decision:
        self._record_decision(decision)
        success = await self._execute_decision(decision)  # ✅ 新加入
        # decision → BehaviorExecutor.execute() → execution callbacks
```

**剩餘問題**: 
- BehaviorExecutor 目前只記錄執行歷史，尚未連接至更深的管線
- 無閉環（執行結果不影響下一次決策）
- 需要 `execution_callbacks` 的下游消費者接線

### 3.2 CausalReasoningEngine (218L) — 🟡 C³ = 2.0/10 (was 0.5/10, ✅ fixed 2026-06-28)

```python
# 虛假完成範例 #2: 因果引擎不參與因果
def predict(self, cause, context=None) -> List[Dict]:
    # 可以預測 cause 的 effect
    return sorted([r for r in self._relationships if r.get("cause") == cause], ...)

# → predict() 從未被系統任何部分呼叫來改變行為
# → learn() 只在 chat pipeline 中以 fire-and-forget 方式呼叫
# → Granger 因果、confounding、do-calculus 都是真實演算法，但處於「真空」中
```

**修復摘要**: `predict()` 現已接入 LLM 管線。在 `chat_routes.py` 中新增 `_inject_causal_predictions()`，在 LLM 呼叫前將因果預測注入 context，再由 `prompt_builder.py` 的 `_append_causal_insights()` 將預測加入 LLM prompt。因果鏈: learn → predict → context injection → prompt builder → LLM sees insights。

**剩餘問題**:
- 預測在 Round 1 不會出現（需先學到關係）
- 尚未形成閉環（LLM 回應後的行為改變不回饋至因果模型）
- `ingest_temporal_state()` 橋樑已存在但未定期觸發

### 3.3 EmotionSystem (280L) — ❌ C³ = 1.0/10

```python
# 虛假完成範例 #3: 情感不影響行為
class EmotionalState:
    primary_emotion: EmotionType  # ✅ 真實情緒狀態
    emotion_intensity: float      # ✅ 強度
    valence: float                # ✅ 效價
    arousal: float                # ✅ 喚醒度

def analyze_emotional_context(self, context) -> EmotionalState:
    # ✅ TextBlob 真正分析文字情感
    state = EmotionalState(...)
    self.emotion_history.append(state)
    return state

# → 然後呢？誰改變了行為？
# → get_emotion_summary() → injected into LLM prompt → LLM "sees" it
# → 這是文字注入，不是行為驅動
# → apply_influence() 是空方法（just logging）
```

**問題**:
- `EmotionalState` 是完整的 → ✅
- `emotion_history` 記錄所有變化 → ✅
- 但「影響」只透過 prompt 文字間接傳遞 → 🟡
- `apply_influence()` 是空殼 → ❌
- 沒有 emotion → endocrine → behavior 的連結 → ❌
- `ValueAssessment` 的 `_calculate_dimension_score` 回傳 `str` 型別（type bug！）→ ❌

### 3.4 MetaController (130L) — 🟡 C³ = 3.5/10 (was 3.0/10, ✅ fixed 2026-06-29)

**修復摘要**: `_threshold_adjustments` 現在被 `get_calibration()` 真正填入，新增 `auto_apply_thresholds()` 返回所有來源的調整值供下游消費。在 `NeuroAutoSelector._analyze_task()` 中，調整值現在影響 `reasoning_threshold`、`quality_threshold`、`high_demand_threshold` 三個決策門檻。`record_result()` 每次記錄後自動觸發 `auto_apply_thresholds()`。

**因果鏈**: record_confidence → get_calibration → _threshold_adjustments 填入 → _analyze_task 讀取 → 調整 reasoning/quality/high_demand 門檻 → 決策參數改變

**剩餘問題**:
- 調整是所有 backend 的平均值，可能互相抵消
- 無閉環（調整結果不影響後續校準）
- 需隨著更多資料累積讓校準更準確

### 3.5 Heartbeat (MetabolicHeartbeat) — 🟢 C³ = 5.0/10

```python
# 目前最完整的因果鏈
async def _run_loop(self):
    cpu = psutil.cpu_percent()           # ✅ 真實硬體感測
    battery = psutil.sensors_battery()   # ✅ 真實硬體感測
    stress = fatigue_impact              # ✅ 計算壓力
    
    await self.bio_integrator.process_stress_event(...)  # ✅ 注入生理系統
    # → 生理系統的 stress 會影響 arousal
    # → arousal 會影響心跳間隔（dynamic_interval）
    # → arousal 會影響 spatial movement（_update_spatial_state）

async def _update_spatial_state(self, arousal, stress):
    if arousal > threshold:
        self.target_x = random.randint(...)  # ✅ 喚醒度高 → 改變目標位置
    
    dx = engine.calculate_attractive_displacement(...)
    self.x += dx  # ✅ 實際移動
    
    if self._check_collision(next_x):
        await reflex_mgr.trigger_physical_trauma(...)  # ✅ 碰撞 → 創傷反應
```

**優點**:
- 真實硬體感測（CPU, Battery）→ stress → ✅
- stress → arousal → 行為改變（移動速度、目標位置）✅
- 碰撞偵測 → 創傷反應 ✅
- 環境偵測 → 激素調整 ✅

**不足**:
- 鏈雖長但不夠寬（只影響移動和心跳，不影響其他系統）
- 創傷反應是 fire-and-forget（無人消費其結果）
- 沒有全域行為調整（如「太累了所以降低探索慾望」）

### 3.6 DigitalLifeIntegrator (380L) — 🟡 C³ = 3.5/10

```python
# 有真實狀態機但只有部分狀態有實際行為
LifeCycleState:
    INITIALIZING → AWAKENING → GROWING → MATURE → RESTING → DORMANT

async def _apply_state_behaviors(self, state):
    if state == GROWING:
        self.state_matrix.update_beta(learning=0.8, curiosity=0.7)  # ✅ 真實狀態改變
        self.memory_bridge.trigger_consolidation()                   # ✅ 真實行為
    elif state == MATURE:
        self.state_matrix.update_beta(clarity=metrics.life_intensity) # ✅ 公式連結
    elif state == RESTING:
        await self.bio_integrator.process_relaxation_event(...)      # ✅ 真實放鬆
        self.memory_bridge.trigger_consolidation()                   # ✅ 記憶鞏固
    # INITIALIZING, AWAKENING, DORMANT → 無行為 ❌
```

**優點**:
- 生命週期狀態機是真實的 ✅
- 3/6 狀態有實際行為（GROWING, MATURE, RESTING）✅
- 狀態轉換觸發生理和狀態矩陣變化 ✅

**不足**:
- 3/6 狀態是空殼（INITIALIZING, AWAKENING, DORMANT）❌
- 行為深但不寬（只影響 state_matrix 和 bio，不影響 routing 或 response）
- `_compute_maturity_score` 依賴 state_matrix，但又用 state_matrix 的 `evaluate_math_spatially` 計算 — 潛在遞迴問題

### 3.7 IntentModel (80L) — ❌ C³ = 0.1/10

```python
class SelfIntent:
    # 完整的意圖資料結構 ✅
    category: IntentCategory
    target_coordinate: Tuple[float, float, float]
    urgency: float
    strength: float
    decay_rate: float

class IntentManager:
    def add_intent(self, intent): ...      # ✅
    def update_intents(self, delta): ...    # ✅ 強度隨時間衰減
    def get_intent_influence(self, dim): ... # ✅
    
    def scan_memory_proximity(self, ...):  # ❌ pass
    def generate_homeostatic_intents(self): # ❌ pass
```

**問題**:
- 資料結構完整但 2/5 方法是空殼 ❌
- 意圖只存在記憶體中，沒有 component 消費 `get_intent_influence()` ❌
- 沒有 homeostatic 意圖生成（意圖不會自動產生）❌

---

## 4. 關鍵發現：斷裂的因果鏈

### 4.1 整體因果鏈地圖

```
                   ┌──────────────────────┐
                   │   User Message        │
                   └──────┬───────────────┘
                          │
                   ┌──────▼───────────────┐
                   │   ExecutionGate      │  ← 真實閘門 (C³=4/10)
                   │   action=reject/exec │
                   └──────┬───────────────┘
                          │ decision
                   ┌──────▼───────────────┐
                   │   Router/LLM         │  ← 真實路由 (C³=5/10)
                   │   generate_response  │
                   └──────┬───────────────┘
                          │ response
              ┌───────────┼───────────┐
              │           │           │
       ┌──────▼───┐ ┌─────▼────┐ ┌───▼──────┐
       │ Causal   │ │ Emotion  │ │ Meta     │
       │Reasoning │ │ System   │ │Controller│
       │ learn()  │ │ summary  │ │ record() │
       │ F-F      │ │→prompt   │ │→EWMA     │
       │ ❌孤立   │ │ 🟡被動  │ │ 🟡建議   │
       └──────────┘ └──────────┘ └──────────┘
              │           │           │
              ▼           ▼           ▼
        全都斷在這裡！── 沒有下游消費 ──┐
                                       │
       ┌───────────────────────────────┘
       │
┌──────▼───────────────┐
│  AutonomousLifeCycle  │
│  make_life_decision() │
│  → decision_history   │ ← 斷在這裡！決策只記錄不執行
└──────────────────────┘
       │
       ▼
  (無人去讀)

       ┌──────────────────────┐
       │  Heartbeat           │ ← 目前最長的鏈
       │  CPU→stress→position │
       │  env→hormone→state   │
       └──────────────────────┘
```

### 4.2 最重要的斷裂點

| # | 斷裂點 | 影響 | 狀態 |
|:-:|:-------|:-----|:----:|
| 1 | **AutonomousLifeCycle decisions → 無人消費** | 自主性核心完全斷裂 | ✅ **FIXED** (commit `40dce741a`) — `_execute_decision()` dispatching to BehaviorExecutor |
| 2 | **CausalReasoningEngine predictions → 無人消費** | 因果引擎像學院派論文 | ✅ **FIXED** (commit `78dac066e`) — predict() sends to LLM prompt via _inject_causal_predictions + _append_causal_insights |
| 3 | **EmotionSystem → 只進 LLM Prompt** | 情感不影響真實行為 | ✅ **FIXED** (commit `f9cf68ac5`) — apply_influence() real, get_behavioral_adjustment() → prompt builder → LLM sees guidance |
| 4 | **MetaController threshold adjustments → 不自動套用** | 適應性學習中斷 | ✅ **FIXED** (this commit) — auto_apply_thresholds() + _analyze_task() uses calibration adjustments |
| 5 | **IntentModel.generate_homeostatic_intents → pass** | 意圖系統不完整 | ✅ **FIXED** (commit `e713db0e0`) — both stubs now real |
| 6 | **LifeCycle 3/6 states 無行為** | 生命週期不完整 | 🟡 P2 |

### 4.3 虛假完成案例（具體代碼）

**案例 A**: AutonomousLifeCycle 的決策
```python
# 被稱為「完整」，因為有 async loop、有公式計算、有決策邏輯
# 實際上決策從不執行

def _lifecycle_loop(self):
    while self._running:
        metrics = self._update_metrics()           # ✅ 計算指標
        decision = self._evaluate_and_decide(metrics)  # ✅ 做決策
        if decision:
            self._record_decision(decision)         # ✅ 記錄決策
            # ❌ 缺少: self._execute_decision(decision)
        ...

# 修復方案:
# 1. 在 AutonoumousLifeCycle 中加入 _execute_decision()
# 2. 決策類型映射到實際行為:
#    - "exploration" → 觸發 HSM 探索 → 改變 QueryClassifier 行為
#    - "coexistence" → 觸發非偏執共存 → 改變 response 模板
#    - "construction" → 觸發主動認知 → 改變學習優先級
#    - "reallocation" → 觸發資源重新分配 → 改變 routing 策略
```

**案例 B**: CausalReasoningEngine 的預測
```python
# 被稱為「完整」，因為有 Granger、confounding、do-calculus
# 實際上預測從不影響系統行為

# 在 chat_routes.py 中:
async def _handle_chat_request(...):
    ...
    # causal_engine.learn() 被 fire-and-forget 呼叫
    asyncio.create_task(causal_engine.learn(observation))
    # → 學完就沒了！
    
    # 缺少:
    # predictions = causal_engine.predict(current_topic)
    # if predictions:
    #     context["causal_insights"] = predictions
    #     # LLM 就會看到因果洞察
```

**案例 C**: EmotionSystem 的情緒
```python
# 被稱為「完整」，因為有 EmotionalState、Valence、Arousal
# 實際上情緒只變成文字

# 在 prompt_builder.py 中:
prompt += f"Current emotional state: {emotion_summary}"
# → LLM 讀到文字，但 LLM 可以選擇忽略

# 缺少:
# if emotional_state.primary_emotion == EmotionType.FEAR:
#     context["routing_mode"] = "conservative"  # 害怕時保守路由
#     context["response_style"] = "soothing"    # 安撫式回應
```

---

## 5. 分數修正：誠實的自主性評分

### 5.1 修正後的因果鏈評分

| 組件 | 之前宣稱 | 實際 C³ | 基礎架構 | 鏈深度 | 閉環率 | 真實度 |
|:-----|:--------:|:-------:|:--------:|:------:|:-----:|:-----:|
| **Heartbeat → Bio → Spatial** | ✅完整 | **5.0/10** | 8/10 | 3 | 30% | 🟢 唯一接近真實的 |
| **ExecutionGate → Pipeline** | ✅完整 | **4.0/10** | 8/10 | 3 | 0% | 🟢 單向確定性閘門 |
| **DigitalLifeIntegrator** | ✅完整 | **3.5/10** | 7/10 | 2 | 40% | 🟡 部分狀態有行為 |
| **MetaController** | ✅完整 | **3.0/10** | 6/10 | 1 | 50% | 🟡 建議但不執行 |
| **EmotionSystem** | ✅完整 | **2.0/10** | 7/10 | 2 | 0% | 🟡 行為驅動 (commit `f9cf68ac5`) |
| **MetaController** | ✅完整 | **3.5/10** | 7/10 | 2 | 0% | 🟡 調整已自動套用 (this commit) |
| **AutonomousLifeCycle** | ✅完整 | **2.0/10** | 7/10 | 2 | 0% | 🟡 決策已執行 (commit `40dce741a`) |
| **CausalReasoningEngine** | ✅完整 | **2.0/10** | 7/10 | 1 | 0% | 🟡 predict() 已接入 LLM prompt (commit `78dac066e`) |
| **IntentModel** | ✅完整 | **1.0/10** | 5/10 | 1 | 0% | 🟡 stubs 已實作，但意圖尚未被消費 |

### 5.2 整體自主性分數

```
之前的自主性分數: 3/10（框架存在，不穩定）

修正後的真實自主性分數: 0.5/10（因果鏈幾乎全部斷裂）

差異原因:
- 之前只看「有沒有這個組件」、「有沒有 async loop」、「程式碼長不長」
- 現在看「組件的輸出是否真正驅動了下游行為改變」
```

### 5.3 基礎架構 vs 因果鏈深度 — 兩個維度

| 維度 | 之前評分方式 | 真實評分 | 差距 |
|:-----|:-----------|:--------:|:----:|
| **基礎架構完整性** | 代碼存在、可導入、有測試 | **~85%** | 🟢 接近真實 |
| **因果鏈深度** | 有接線、有資料流 | **~10%** | 🔴 嚴重高估 |
| **自主行為真實度** | 有 LifeDecision、有公式 | **~5%** | 🔴 嚴重高估 |

**關鍵認知**: 基礎架構 85% 是對的 — 只是這些漂亮的架構都在做同一件事：**計算並記錄，然後停止**。

---

## 6. 改善路線：從「記錄」到「驅動」

### 6.1 P0（必須修復）— 決策驅動 ✅（已修復 2026-06-28）

**目標**: 讓 AutonomousLifeCycle 的決策真正改變系統行為

```
Before: decision → record → end
After:  decision → dispatch → BehaviorExecutor records → execution callbacks notified → verifiable
```

**已實作** (commit `40dce741a`):
- `_execute_decision()` 將 4 種決策類型分派至 BehaviorExecutor
- 4 個 dispatch 方法：`_dispatch_exploration`, `_dispatch_coexistence`, `_dispatch_construction`, `_dispatch_reallocation`
- 執行回呼、執行狀態追蹤
- `make_life_decision()` 改為 async，包含執行
- 呼叫的 `get_lifecycle_summary()` 包含 execution_history_count

**Causal depth 更新**: 0.1→2.0/10（決策現在確實被執行，但尚未形成閉環）

### 6.2 P0（必須修復）— 因果引擎接入 ✅（已修復 2026-06-28）

**目標**: 讓 CausalReasoningEngine 的預測影響系統行為

```
Before: learn → store → end
After:  learn → predict → context injection → LLM sees insights → behavioral change
```

**已實作** (commit `78dac066e`):
- `_inject_causal_predictions()` 在 LLM 前呼叫 `causal.predict()`
- `_append_causal_insights()` 將預測 formatted 加入 prompt
- 鏈: predict() → context injection → prompt builder → LLM sees insights

**Causal depth 更新**: 0.5→2.0/10（預測現在確實進入 LLM prompt，但尚未形成閉環）

**驗證方式**: `test_causal_prediction_affects_routing()` — 驗證因果預測改變路由選擇

### 6.3 P1（短期）— 情感驅動行為

**目標**: 讓 EmotionSystem 的狀態直接影響 routing 和 response

```
Before: emotion → text in prompt → LLM may ignore
After:  emotion → routing_mode = conservative/exploratory → actual behavior changes
```

**驗證方式**: `test_emotion_affects_routing_mode()` — 驗證情緒狀態改變路由策略

### 6.4 P2（中期）— MetaController 自動套用

**目標**: 讓 MetaController 的 threshold 調整自動生效

```
Before: record → calculate → store recommendation → end
After:  record → calculate → auto-apply threshold adjustment → behavior changes
```

### 6.5 P2（中期）— LifeCycle 狀態補全

**目標**: 為 INITIALIZING, AWAKENING, DORMANT 加入實際行為

| 狀態 | 應有行為 |
|:-----|:---------|
| INITIALIZING | 逐漸增加認知負載、初始化所有公式系統、建立初始記憶 |
| AWAKENING | 緩慢探索環境、建立基礎知識域、學習使用者模式 |
| DORMANT | 深度記憶鞏固、背景清理、資源回收、低功耗模式 |

---

## 7. 驗證標準

### 7.1 鏈完整性測試（新類型測試）

每個因果鏈必須有專屬的完整性測試，格式：

```python
def test_causal_chain_<component>_<path>() -> None:
    """Verify that component A's state change → component B's behavior change."""
    # 1. Setup: 初始化組件 A 和 B
    # 2. Trigger: 改變 A 的狀態
    # 3. Assert: 驗證 B 的行為改變（不只是 B 的資料改變）
    # 4. Trace: 完整鏈條每一環都可追蹤
```

### 7.2 禁止模式

| 模式 | 禁止原因 | 替代方案 |
|:-----|:---------|:---------|
| `callback(x)` but callback is empty | 虛假接線 | 移除 callback 或填入實際行為 |
| `engine.predict()` never called | 真空演算法 | 刪除或接入生產管線 |
| `decision_history` append-only | 只記錄不執行 | 加入 `_execute_decision()` |
| `get_summary()` → prompt injection only | 文字代替行為 | 加入實際行為改變 |
| `apply_influence()` → just log | 空殼方法 | 實作或移除 |

### 7.3 可接受的最低標準

要宣稱一個組件「完整」，必須同時滿足：

1. **基礎架構**: 代碼存在、可導入、有 ✅
2. **因果鏈深度 ≥ 2**: 輸出被至少一個下游組件消費並改變行為 ✅
3. **鏈完整性測試**: 有測試驗證 A→B 的因果傳遞 ✅
4. **無禁止模式**: 沒有空 callback、空方法、孤立計算 ❌（目前多數組件此項失敗）

---

## 附錄: 當前各組件生命週期狀態實際調查

| 組件 | 檔案 | 行數 | async loop | 有狀態 | 影響下游 | 鏈深度 | 評級 |
|:-----|:-----|:----:|:----------:|:------:|:--------:|:------:|:----:|
| MetabolicHeartbeat | `core/life/heartbeat.py` | 206 | ✅ | ✅ | ✅ Bio+Spatial | 3 | 🟢 |
| ExecutionGate | `ai/core/execution_gate.py` | 170 | ❌ | ❌純計算 | ✅ Router | 2 | 🟢 |
| DigitalLifeIntegrator | `core/life/digital_life_integrator.py` | 380 | ✅ | ✅ | 🟡部分 | 2 | 🟡 |
| MetaController | `ai/meta/meta_controller.py` | 130 | ❌ | ✅ EWMA | 🟡記錄但不套用 | 1 | 🟡 |
| AutonomousLifeCycle | `core/life/autonomous_life_cycle.py` | 410 | ✅ | ✅ | ❌無 | 0 | 🔴 |
| EmotionSystem | `ai/alignment/emotion_system.py` | 280 | ❌ | ✅ | 🟡只有文字 | 0.5 | 🔴 |
| CausalReasoningEngine | `ai/reasoning/causal_reasoning_engine.py` | 218 | ❌ | ✅ | ❌無 | 0 | 🔴 |
| IntentModel | `core/life/intent_model.py` | 80 | ❌ | 🟡部分 | ❌無 | 0 | 🔴 |
| ModalityGateway | `core/life/digital_life_integrator.py` | 70 | ❌ | ✅ | 🟡狀態更新但無人讀 | 0.5 | 🔴 |

**總計**: 9 個核心自主性組件，只有 2 個有實質因果鏈傳遞，7 個處於「計算但不驅動」狀態。

---

## 0. 基石原則：禁止未完成組件參與因果鏈

> **核心命令**: 在開始搞因果鏈前，禁止有未完成或完成度不支持因果鏈的任何組件、系統存在。
> 因果鏈網路必須從完成細節自然連接且編織出來，而非從上而下強制接線。

### 0.1 為什麼？

因果鏈的定義是：
```
Component_A.state_change → Component_B.detect() → Component_B.behavior_change → Component_C...
```

如果 Component_A 是不完整的（例如決策只記錄不執行），那麼：
- Component_B 永遠收不到 A 的輸出 → 鏈在 A 就斷了
- 即使強制把 A 和 B 接起來，B 收到的也是空資料 → 虛假因果
- 測試可以通過（因為測試只測「A 能輸出」不測「B 收到並改變行為」）→ 虛假驗證

**結論**: 一個不完整的組件，足以讓整條因果鏈無效。

### 0.2 什麼叫「完成度支持因果鏈」？

一個組件要算「可以參與因果鏈」，必須滿足：

| 條件 | 說明 | 驗證方式 |
|:-----|:------|:---------|
| **① 無 stub/pass** | 所有方法都有真實實現 | grep 確認無 `pass`、`raise NotImplementedError` |
| **② 輸出被消費** | 組件輸出至少被一個下游組件讀取並改變行為 | 鏈完整性測試 |
| **③ 無斷裂 callback** | 所有 callback 註冊點都有至少一個真實消費者 | 檢查 callback 註冊鏈 |
| **④ 無模擬延遲** | `asyncio.sleep()` 用於真實等待，非模擬處理時間 | 檢查 sleep 語義 |
| **⑤ 循環合理** | 更新頻率在該硬體場景的合理範圍內 | 定時分析測試 |
| **⑥ 異常處理完整** | 所有 create_task 有 exception handler | 檢查 task 註冊 |

### 0.3 前後端統一標準

| 層級 | 適用範圍 | 禁止事項 |
|:-----|:---------|:---------|
| **後端 Python** | 所有 `apps/backend/src/` | stub、pass、空 callback、模擬 sleep |
| **前端 JS/TS** | `apps/desktop-app/`, `apps/web-live2d-viewer/` | 未接線的 UI 元件、假資料、TODO handler |
| **共享 JS** | `packages/shared-js/` | 未使用的匯出、未實作的平台適配 |
| **像素引擎** | `apps/pixel-angela/` | 崩潰的渲染路徑、未處理的 WebSocket 訊息 |
| **OS橋接** | `apps/gemini-os-bridge/` | timeout 不夠、無錯誤恢復的視窗操作 |

### 0.4 因果鏈的織法：從下而上，非從上而下

**錯誤方式（從上而下）**:
```
1. 先設計完整的因果鏈圖（A→B→C→D）
2. 然後開始補 A 的輸出、B 的輸入、C 的轉換…
3. → 結果：A 的輸出格式改了→B 壞了→整條鏈重來
```

**正確方式（從下而上）**:
```
1. 先確保 Component_A 是 100% 完整的（內部狀態+輸出）
2. 再確保 Component_B 是 100% 完整的（能接收輸入+改變行為）
3. 然後寫一行程式碼把 A 的輸出接到 B 的輸入
4. → 結果：自然產生了 A→B 因果鏈
5. 重複第 2-4 步，鏈自然延伸
```

### 0.5 當前禁止參與因果鏈的組件

以下組件在完成度不足之前，**不得被納入任何因果鏈**：

| 組件 | 阻塞原因 | 需完成的工作 |
|:-----|:---------|:-------------|
| ✅ **AutonomousLifeCycle** | 修復完成 (commit `40dce741a`) | `_execute_decision()` 已加入，分派至 BehaviorExecutor |
| ✅ **CausalReasoningEngine** | 修復完成 (commit `78dac066e`) | predict() 已接入 LLM prompt 管線 (chat_routes._inject_causal_predictions → prompt_builder._append_causal_insights) |
| ❌ **EmotionSystem** | apply_influence() 是空殼 | 實作情緒→行為的真實映射 |
| ❌ **IntentModel** | 2/5 方法是 pass | 實作 scan_memory_proximity 和 generate_homeostatic_intents |
| ❌ **DigitalLifeIntegrator** | 3/6 狀態無行為 | 補齊 INITIALIZING, AWAKENING, DORMANT 行為 |
| ✅ **MetaController** | 修復完成 (commit `f9cf68ac5`) | auto_apply_thresholds() 已加入，NeuroAutoSelector._analyze_task() 現在讀取調整值影響 reasoning/quality/high_demand 門檻 |
| ❌ **Heartbeat Integration** | 60x 頻率差導致不同步 | 統一 Heartbeat Primary 和 Integration 循環 |
| ❌ **Level5ASI Process** | 使用模擬 sleep(1.0) | 移除模擬延遲 |
| ❌ **前端 Live2D** | 隨機彩色矩形 | 補齊 Live2D 模型渲染路徑 |
| ❌ **前端 Dashboard** | 假資料或 TODO handler | 接上真實後端 API |

### 0.6 例外條款

以下情況的組件可以「不完整但存在」：

| 情況 | 範例 | 條件 |
|:-----|:------|:-----|
| **純工具函數** | `primitive_renderer.py` | 不參與任何因果鏈 |
| **純資料結構** | `types.py`, `dataclasses` | 無行為邏輯 |
| **未來擴展預留** | `plans/` 中的設計文件 | 明確標記 `DRAFT` |
| **僅供 LLM 包裝器** | `router.py` 中的 provider | 不宣稱自主性，只代理 API 呼叫 |

### 0.7 驗證閘門

在任何因果鏈相關的 PR 或 commit 之前，必須通過：

```bash
# 1. 確認無 pass 殘留
cd /d/Projects/Unified-AI-Project
python -c "
import os
count = 0
for root, dirs, files in os.walk('apps/backend/src'):
    for f in files:
        if f.endswith('.py'):
            with open(os.path.join(root, f)) as fh:
                for i, line in enumerate(fh, 1):
                    stripped = line.strip()
                    if stripped == 'pass' and not stripped.startswith('#'):
                        print(f'  pass@{root}/{f}:{i}')
                        count += 1
print(f'Total pass statements: {count}')
"

# 2. 確認所有 asyncio.sleep 有正當理由
# 3. 確認所有 create_task 有 exception handler
# 4. 確認測試覆蓋因果鏈（而非孤立組件）
```

---

---

## 8. 時鐘/脈衝/心跳/同步分析

### 8.1 核心問題：沒有統一的時間基準

專案中 **沒有一個全域的系統時鐘**。每個組件各自為政，用 `asyncio.sleep()` 決定自己的更新頻率。
這導致：
- 組件間的時間基準不一致
- 無法對齊因果鏈的時間軸
- 無法區分「真實時間」和「模擬時間」
- 無硬體感知的動態頻率調整

### 8.2 完整時鐘/循環盤點

按更新頻率排序，從最快到最慢：

| # | 組件 | 檔案 | 間隔 | 每次工作 | 合理性 |
|:-:|:-----|:-----|:----:|:---------|:------:|
| 1 | ActionExecutor FPS | `action_executor.py` | **0.05s** (50ms, 20Hz) | 執行行動隊列 | 🟡 對行動執行來說合理，但沒有硬體適應 |
| 2 | Bridge Fast | `action_execution_bridge.py` | **0.05s** (50ms) | 橋接輪詢 | 🟡 與上面重複 |
| 3 | ANS Update | `autonomic_nervous_system.py` | **0.5s** (2Hz) | 更新自主神經狀態 | ✅ 生理模擬需要這頻率 |
| 4 | Bridge Poll | `action_execution_bridge.py` | **0.1s** (10Hz) | 執行橋接輪詢 | 🟡 與 Bridge Fast 重複 |
| 5 | Audio Poll | `audio_system.py` | **0.1s** (10Hz) | 音訊輪詢 | ✅ 音訊需要低延遲 |
| 6 | Tactile Update | `physiological_tactile_system.py` | **0.1s** (10Hz) | 觸覺更新 | ✅ 觸覺感測需要高頻率 |
| 7 | Transport Poll | `hsp/transport.py` | **0.1s** (10Hz) | HSP傳輸輪詢 | ✅ 通訊需要低延遲 |
| 8 | Sleep Short | 多處使用 | **0.1s** | 通用短暫等待 | 🟡 多處濫用，應依場景命名 |
| 9 | Emotion Tick | `emotional_blending.py` | **1.0s** (1Hz) | 情感混合更新 | ✅ 情感演變不需要太快 |
| 10 | Bio Integrate Tick | `biological_integrator.py` | **1.0s** (1Hz) | 生理整合 | 🟡 與其他生理循環不同步 |
| 11 | ANS Tick | `autonomic_nervous_system.py` | **1.0s** (1Hz) | ANS輔助更新 | 🟡 與 ANS Update(0.5s) 不一致 |
| 12 | Execution Check | `execution_monitor.py` | **1.0s** (1Hz) | 執行監控 | ✅ 合理 |
| 13 | Level5 Process | `level5_asi_system.py` | **1.0s** | 模擬處理時間 | ❌ 這是模擬延遲，不是真實處理 |
| 14 | Agent Poll | `agent_manager.py` | **0.5s** | Agent輪詢 | 🟡 可接受 |
| 15 | Neural Update | `neuroplasticity_core.py` | **60.0s** (1/min) | 神經可塑性 | ✅ 神經可塑性不需要高頻率 |
| 16 | Life Integrator Params | `digital_life_integrator.py` | **60.0s** (1/min) | 動態參數更新 | ✅ 合理 |
| 17 | Agent Cleanup | `dynamic_agent_registry.py` | **30.0s** | 清理失聯agent | ✅ 合理 |
| 18 | Scan Desktop | `desktop_interaction.py` | **30.0s** | 掃描桌面 | ✅ 合理 |
| 19 | Endocrine Update | `endocrine_system_core.py` | **5.0s** | 內分泌系統 | ✅ 符合生理模擬需求 |
| 20 | Level5 Config Update | `level5_config.py` | **5.0s** | L5配置更新 | 🟡 過於頻繁？ |
| 21 | Metabolic Interval | `angela_model_core.py` | **2.0s** | 代謝更新 | 🟡 與 Heartbeat(30s) 不一致 |
| 22 | Heartbeat Primary | `heartbeat.py` | **5.0~60.0s** (動態) | 生物/代謝循環 | ✅ 動態調整，最佳實踐 |
| 23 | Heartbeat Integration | `heartbeat.py` | **0.1s** | 小腦/神經整合 | 🟡 與 Primary 循環不一致 |
| 24 | Life Cycle Check | `digital_life_integrator.py` | **10.0s** | 生命週期檢查 | ✅ 合理 |
| 25 | Proactive Check | `proactive_interaction_system.py` | **15.0s** | 主動互動檢查 | ✅ 合理 |
| 26 | HAM Hourly | `ham_background_tasks.py` | **3600.0s** (1/hr) | HAM背景任務 | ✅ 長時間任務 |
| 27 | Narrative Update | `cyber_identity.py` | **86400.0s** (1/day) | 敘事更新 | ✅ 每日更新合理 |
| 28 | Decision Interval | `autonomous_life_cycle.py` | **300.0s** (5min) | 生命決策 | 🟡 太慢？自主決策應更快 |
| 29 | Session Heartbeat | `connection_session.py` | **30.0s** | WebSocket心跳 | ✅ 網路標準 |
| 30 | HAM Sync | `chat_service.py` | **3600.0s** (1/hr) | HAM同步 | 🟡 1小時太長，使用中可能遺失 |
| 31 | Bio Monitor | `system_monitor.py` | **5.0s** | 系統監控 | ✅ 合理 |
| 32 | CML Auto-train | `multimodal_service.py` | **60.0s** | 多模態微訓練 | ✅ 背景訓練合理 |

### 8.3 循環合理性分析

#### 🟢 合理 (12/32)
- 生理模擬 (ANS 0.5s, 內分泌 5s, 神經可塑性 60s)
- 長時間任務 (HAM 1hr, 敘事 1day)
- 網路心跳 (Session 30s)
- 背景訓練 (CML 60s)

#### 🟡 有問題 (12/32)
- **重複循環**: Bridge Poll(0.1s) 和 Bridge Fast(0.05s) 做類似事情
- **不一致的同類循環**: ANS Update(0.5s) vs ANS Tick(1.0s) 在同一系統內
- **自主決策太慢**: 300s(5min) 對「自主性」來說太長
- **HAM同步太慢**: 3600s(1hr) 可能導致記憶遺失
- **Sleep Short 濫用**: 8+ 個組件使用同樣的 0.1s sleep key，但代表不同語義

#### 🔴 不合理 (8/32)
- **Level5 Process 1s**: 這是 `asyncio.sleep(1.0)` 模擬處理時間，不是真實計算
- **代謝 2s vs 心跳 5-60s**: 兩個代謝相關循環頻率不一致
- **Heartbeat 兩個循環**: Primary(5-60s) 和 Integration(0.1s) 頻率差 50-600倍
- **Behavoir Loop Tight 1.0s**: 5+ 個 lifecycle 循環使用相同 sleep 值做「防止緊密循環」，應統一管理

### 8.4 硬體感知分析

#### 目前有硬體感知的組件

| 組件 | 感測的硬體 | 如何影響行為 |
|:-----|:-----------|:-------------|
| MetabolicHeartbeat | CPU使用率, 電池電量 | CPU高→fatigue增加→stress升高→心跳加速→移動變慢 |
| MetabolicHeartbeat | 電量 < 20% | 觸發 starvation stress event |
| ActionExecutor | 無 | 固定 50ms 循環，不考慮硬體負載 |
| ANS | 無 | 固定 0.5s 循環 |
| 其餘 28+ 循環 | **無** | 全部固定頻率 |

#### 缺少的硬體適應

| 硬體指標 | 目前誰在用？ | 應該影響誰？ |
|:---------|:------------|:-------------|
| **CPU溫度** | 無人使用 | 全部高頻循環（應在過熱時降頻） |
| **記憶體使用率** | 無人使用 | 資料庫查詢頻率、batch size |
| **GPU使用率** | 無人使用 | 視覺處理頻率、訓練頻率 |
| **磁碟IO** | 無人使用 | 持久化頻率、HAM同步頻率 |
| **網路延遲** | 無人使用 | 外部API呼叫頻率、同步策略 |
| **電池模式** | 部分（只檢查<20%） | 全部循環（電池模式時減半頻率） |

#### 不同硬體的合理值

| 硬體場景 | ANS | 心跳 | 決策 | 神經可塑性 | 敘事 |
|:---------|:---:|:----:|:----:|:---------:|:----:|
| **桌機(高效能)** | 0.5s | 5-30s 動態 | 60s | 60s | 1day |
| **筆電(一般)** | 1.0s | 10-60s 動態 | 120s | 120s | 1day |
| **筆電(電池)** | 2.0s | 30-120s 動態 | 300s | 300s | 1day |
| **低功耗裝置(RPi)** | 5.0s | 60-300s 動態 | 600s | 600s | 7days |
| **雲端伺服器** | 0.2s | 1-10s 動態 | 30s | 30s | 1day |

**目前情況**: 所有場景使用同一組固定值。只有 Heartbeat 有動態調整（但只根據 stress/arousal，不根據硬體）。

### 8.5 同步與非同步問題

#### 同步模式使用盤點

| 模式 | 數量 | 用途 | 評價 |
|:-----|:----:|:-----|:----:|
| `asyncio.sleep(fixed)` | **80+** 處 | 循環等待 | 🟡 大部分應改為事件驅動 |
| `asyncio.sleep(dynamic)` | **2** 處 | Heartbeat動態間隔, retry backoff | ✅ 最佳實踐 |
| `asyncio.create_task()` | **15+** 處 | 背景循環啟動 | ✅ 正確用法 |
| `asyncio.wait_for()` | **10+** 處 | 操作超時 | ✅ 必要保護 |
| `asyncio.Event()` | **3** 處 | 事件驅動同步 | 🟡 太少！應廣泛使用取代 sleep 輪詢 |
| `asyncio.Lock()` | **5+** 處 | 資源互斥 | ✅ 必要 |
| `time.sleep()` (同步) | **5** 處 | 指令碼中的等待 | ❌ 阻塞事件循環 |

#### 關鍵同步問題

1. **輪詢代替事件**: 80+ 處使用 `asyncio.sleep()` 輪詢，但只有 3 處使用 `asyncio.Event()`。
   - 例如: `_lifecycle_loop()` 每 300s 醒來檢查 metrics，但 metrics 更新是同步計算的
   - 改善: 使用 Event 在 metrics 更新時通知 lifecycle，減少無謂輪詢

2. **沒有同步點對齊**: 30+ 個獨立循環各自為政，沒有全局時鐘 tick
   - 改善: 引入 `GlobalSystemClock`，每 tick 廣播一次，組件選擇監聽哪些 tick

3. **Fire-and-forget 非同步**: CausalReasoningEngine.learn()、CML 訓練等被 create_task 但無人 await
   - 這些任務如果拋出異常，會被靜默吞沒（沒有 exception handler）

4. `time.sleep()` 在 async 上下文: 至少 5 處使用同步 `time.sleep()`，阻塞整個事件循環

### 8.6 改善建議

| # | 建議 | 影響 | 難度 |
|:-:|:-----|:----:|:----:|
| 1 | **引入 GlobalSystemClock**: 統一時間基準，支援 tick 訂閱 | 🔴 高 | 中 |
| 2 | **循環頻率標準化**: 合併重複循環、統一語義命名 | 🟡 中 | 低 |
| 3 | **事件驅動取代輪詢**: `asyncio.Event()` 取代 80% 的 sleep 輪詢 | 🟡 中 | 中 |
| 4 | **硬體感知動態頻率**: 根據 CPU/GPU/電池動態調整所有循環 | 🟡 中 | 高 |
| 5 | **HardwareProfile**: 定義 5 種硬體場景的預設頻率表 | 🟡 中 | 低 |
| 6 | **消除 time.sleep()**: 所有同步 sleep 改為 asyncio.sleep | 🔴 高 | 低 |
| 7 | **Fire-and-forget 異常處理**: 為所有 create_task 註冊 exception handler | 🔴 高 | 低 |
| 8 | **自主決策頻率提升**: 300s→60s，讓自主性更即時 | 🟡 中 | 低 |

### 8.7 硬體設定檔範例

```yaml
# configs/system/hardware_profiles.yaml
profiles:
  high_performance_desktop:
    base_frequency: 1.0
    ans_update: 0.5
    heartbeat_min: 5.0
    heartbeat_max: 30.0
    decision_interval: 60.0
    neuroplasticity_update: 60.0
    
  laptop_power_saver:
    base_frequency: 0.5
    ans_update: 2.0
    heartbeat_min: 30.0
    heartbeat_max: 120.0
    decision_interval: 300.0
    neuroplasticity_update: 300.0
    
  server_cloud:
    base_frequency: 2.0
    ans_update: 0.2
    heartbeat_min: 1.0
    heartbeat_max: 10.0
    decision_interval: 30.0
    neuroplasticity_update: 30.0
```
