<!--
  =============================================================================
  FILE_HASH: Initial
  FILE_PATH: docs/06-project-management/CAUSAL_CHAIN_COMPLETENESS.md
  FILE_TYPE: analysis
  PURPOSE: 因果鏈完整性分析 — 真實自主性的衡量標準與當前差距
  VERSION: 1.0.0
  STATUS: active
  LANGUAGE: zh-tw/en
  LAST_MODIFIED: 2026-07-02 (updated for §X #117: CausalReasoningEngine closed-loop — routing adjustments)
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
| AutonomousLifeCycle | 5 個公式 | 計算 metrics + 做決定 | LifeDecision | ✅ **BehaviorExecutor** (`_execute_decision()` dispatch → execution callbacks) |
| CausalReasoningEngine | observations | Pearson/Granger/confounding/do-calculus | relationships | ✅ **LLM prompt** (`_inject_causal_predictions` → `_append_causal_insights`) |
| EmotionSystem | context text | TextBlob 情感分析 + PAD 映射 | EmotionalState + behavioral_adjustment | ✅ **prompt builder** (文字注入 + routing_mode 影響 via apply_influence)

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

### 3.1 AutonomousLifeCycle (410L) — 🟡 C³ = 3.0/10 (was 2.0/10, ✅ fixed 2026-07-01 §X #74)

**修復摘要**: `_execute_decision()` 已加入 (2026-06-28)，將 4 種決策類型分派至 `BehaviorExecutor`。§X #74 (2026-07-01): 加入執行回饋閉環 — `execution_success_rate` 現在影響後續決策的動態閾值。

```python
# 修復後 (v2): 決策執行 + 回饋閉環
async def _lifecycle_loop(self):
    decision = self._evaluate_and_decide(metrics)
    if decision:
        self._record_decision(decision)
        success = await self._execute_decision(decision)
        # success 記錄在 executions_succeeded/failed

# _evaluate_and_decide 新加入:
# context["execution_success_rate"] = ...
# if success_rate < 0.5: 保守 (threshold+0.15, risk-0.2)
# if success_rate > 0.9: 大膽 (threshold-0.1, risk+0.15)
```

**因果鏈**: metrics → evaluate → decision → execute → success/fail → 回饋 → 下一次 evaluate

**C³ 更新**: 2.0→**3.0/10**（現在有閉環：執行結果影響後續決策閾值）

**§X #85 (2026-07-01) — Config-driven feedback thresholds**: 6 個硬編碼閾值 (success_rate_low, success_rate_high, confidence_penalty, confidence_boost, risk_penalty, risk_boost) 已遷移至 `lifecycle_value()` config 驅動。新測試文件 `tests/core/test_autonomous_life_cycle.py` 驗證 config 驅動行為。C³: 3.0→**3.5/10**（可維護性 + 可驗證性提升）。

**§X #113 (2026-07-02) — Lifecycle behavioral adjustment → routing/response pipeline**: Added `get_behavioral_adjustment()` to AutonomousLifeCycle that maps life phase (EMERGENCE→conservative, EXPLORATION→exploratory, etc.) and recent decision type (exploration→adventurous, coexistence→empathetic, etc.) to a routing_mode/response_style dict. Wired into chat_routes.py pipeline step 5c via `_get_lifecycle()` singleton and injected as `context["lifecycle_behavior"]`. Read in router.py `_prepare_generation_context()` as Priority 1 before emotional_behavior (Priority 2) and angela_emotion (Priority 3). 10 new tests verify all 5 phases, all 4 decision type overrides, confidence computation, and the full cascade.

**Causal chain**: lifecycle metrics → evaluate → decision → get_behavioral_adjustment() → context inject → router._prepare_generation_context() reads lifecycle_behavior.routing_mode → temperature/max_tokens modulation.

**C³ 更新**: 3.5→**4.5/10**（生命週期決策現在直接影響 LLM 參數：phase→routing_mode→temperature/max_tokens）+ `get_lifecycle_summary()` 文字注入（已有）

### 3.2 CausalReasoningEngine (218L) — 🟢 C³ = 6.0/10 (was 4.5→6.0, ✅ §X #117)

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

**§X #69 (2026-06-30): Temporal buffer + dynamic strength — DONE**
- `_fire_causal_learning()` 現在維護 per-session 時間緩衝 (`_CAUSAL_BUFFERS`)，累積 `msg_lengths`/`resp_lengths`/`engagement_ratios`。
- ≥ 5 次交互後傳遞累積列表給 `causal.learn()`，使 Granger 因果檢定可以觸發時間優先性檢測。
- 動態強度 `dynamic_strength = min(0.9, max(0.1, engagement / 5.0))` 取代硬編碼 0.5，回應/查詢比例高 → 高強度。
- 緩衝上限 100 條（溢位時修剪至最後 50 條）。
- 8 個新單元測試驗證緩衝建立/重用/會話隔離/累積/上限/動態強度/空回應保護。

**C³ 更新**: 3.0→**4.0/10** (§X #82) — `ingest_temporal_state()` 現已在聊天管線中定期觸發（`_fire_causal_learning` 內部）。TemporalState 儲存每次互動的快照（msg_length/resp_length/engagement_ratio），每 5 次互動自動呼叫 `ingest_temporal_state(ts, window=20)`。解決了「橋樑存在但未觸發」的問題。

**§X #112 (2026-07-02) — Retrospective warm-start**: Added `retrospective_warm_start()` method that creates 6 baseline causal relationships from synthetic retrospective data. This means `predict("user_input")` returns results from Round 1 of every conversation, not just Round 5+. Called automatically in lifespan.py `_try_init_causal_reasoning()` at server startup. 7 new tests verify baseline creation, idempotency, graph integrity, and pre-live-data prediction.

```python
# Before: Round 1-4 predict returned empty → no causal insights in LLM prompt
# After: Warm-start populates baseline relationships → predict works immediately
causal.predict("user_input")
# Returns:
#   [{"cause": "user_input", "effect": "angela_response", "strength": 0.65, ...},
#    {"cause": "user_input", "effect": "angela_response", "strength": 0.55, ...},
#    {"cause": "user_input", "effect": "angela_response", "strength": 0.50, ...}]
```

**C³ 更新**: 4.0→**4.5/10** (CausalReasoningEngine.retrospective_warm_start() — Granger still requires 5 rounds, but predict() works from Round 1 via synthetic baseline relationships).

**§X #117 (2026-07-02) — Causal routing adjustment closes the closed-loop**: Added `_get_causal_routing_adjustment()` to chat_routes.py that reads causal predictions (`user_input`, `query_complexity`, `conversation_momentum`, `interaction_value` average strength) and computes concrete `temperature_bias` and `max_tokens_bias` values. These are injected into context as `causal_routing` when confidence ≥ 0.25. In router.py `_prepare_generation_context()`, causal routing is applied as a modifier (Priority 3.5, after routing_mode): temperature adjusted by bias (clamped 0.1-1.5) and max_tokens by bias (clamped 128-1024). 11 new tests verify routing adjustment computation, injection thresholding, and all key prediction scenarios. **The loop is now closed**: causal predictions → parameter adjustments → LLM behavior change → new observations → updated predictions.

```python
# 目前真實鏈: 文字注入 + routing_mode 計算 → prompt 指南 + bio stress/relaxation
class EmotionSystem:
    def apply_influence(self, source, type, value, intensity):
        # ✅ 真實 PAD 模型: 14 種影響類型映射 (dopamine/adrenaline/cortisol/...)
        # ✅ 更新 valence/arousal/dominance → 新 emotion 狀態
        self.emotion_history.append(influenced_state)

    def get_behavioral_adjustment(self):
        # ✅ 回傳 routing_mode/response_style (conservative vs exploratory)
        # ✅ 回傳 emotional_state/intensity/valence/arousal
        return {"routing_mode": ..., "response_style": ..., ...}

# 消費位置:
# chat_routes.py:176-203 → context["angela_emotion"] = adj
# chat_routes.py:192   → context["emotional_behavior"] (硬編碼映射)
# prompt_builder.py:467-499 → 兩者注入 LLM prompt
# chat_routes.py:203-217 → 跨組件: _apply_emotion_to_biology() → BiologicalIntegrator stress/relaxation
```

**現狀**:
- `EmotionalState` 完整、PAD 模型、14 種影響類型映射 → ✅
- `apply_influence()` 真實實現（非空殼）→ ✅
- `emotion_history` 記錄所有變化 + 上限 1000 筆 → ✅
- `get_behavioral_adjustment()` 回傳 routing_mode/response_style → ✅
- 兩路注入 prompt: `emotional_behavior`（用戶情緒→路由）+ `angela_emotion`（Angela 自身情緒）→ ✅
- routing_mode 現在影響 LLM 參數：conservative → temperature-0.3, max_tokens→384; exploratory → temperature+0.3, max_tokens→768 (§X #73) → ✅
- 跨組件 Emotion→Bio: 高壓力情緒(anger/fear/sadness)觸發 BiologicalIntegrator.process_stress_event(); 正面情緒(joy/trust)觸發 process_relaxation_event() (§X #80) → ✅

**C³ 更新**: 3.0→**4.0/10** — 新增跨組件 Emotion→BiologicalIntegrator 鏈。Angela 的情緒狀態現在直接影響生物壓力/放鬆系統，建立 emotion → endocrine → behavior 的第一個跨組件連結。額外 23 個測試驗證映射強度、方法呼叫正確性、整合情境。

### 3.4 MetaController (165L) — 🟡 C³ = 4.5/10 (was 3.5→4.0, ✅ fixed 2026-07-02 §X #115)

**修復摘要**: `_threshold_adjustments` 現在被 `get_calibration()` 真正填入，新增 `auto_apply_thresholds()` 返回所有來源的調整值供下游消費。在 `NeuroAutoSelector._analyze_task()` 中，調整值現在影響 `reasoning_threshold`、`quality_threshold`、`high_demand_threshold` 三個決策門檻。`record_result()` 每次記錄後自動觸發 `auto_apply_thresholds()`。

**§X #83 (2026-07-01) — Closed-loop feedback via calibration history**: `get_calibration()` 現在追蹤每次校準結果（over/under/stable）到 `_calibration_history`（per-source deque, maxlen=5），並維護 `_adjustment_multipliers`。連續 3 次過度自信或不足自信 → 調整幅度 x1.5（加速修正）；連續 2 次穩定 → 調整幅度 x0.8（最小 1.0，防止過度修正）。15 個測試（10 核心 + 5 閉環新增）全數通過。

**§X #115 (2026-07-02) — Calibration cache + weighted aggregate**: 新增 `_calibration_cache`（dirty flag 機制）避免校準重複計算；新增 `_raw_adjustments` 分離乘數前後的調整值；新增 `get_weighted_adjustment()` 基於可靠性和樣本數的加權聚合（代替簡單平均，防止對立調整互相抵消）。`_update_closed_loop()` 被提取為獨立方法，在快取命中時也會調用（閉環乘數正確更新）。`NeuroAutoSelector._analyze_task()` 改為使用 `get_weighted_adjustment()`。9 個新測試驗證快取、加權聚合、閉環相容性。

**因果鏈**: record_confidence → get_calibration (cache-aware) → _threshold_adjustments 填入 → _analyze_task 用 weighted adjustment → 調整 reasoning/quality/high_demand 門檻 → 決策參數改變 → 校準歷史回饋（快取命中時仍更新）→ 下一次調整幅度放大/縮小（閉環持續）

**已解決**: 調整是所有 backend 的平均值可能互相抵消 → 改用加權聚合（weighted adjustment）解決

**剩餘**: 需隨著更多資料累積讓校準更準確

### 3.5 ExecutionGate (248L) — 🟢 C³ = 6.0/10 (was 5.0/10, ✅ §X #95)

**C³ 6.0 — Execution result feedback loop (fully closed)**: `ExecutionGate` tracks auto-execution outcomes (success/fail) per handler via `record_result()`. Success rate ≥ 90% with ≥ 5 results → +0.05 threshold bonus (lower effective threshold, more trust). Success rate ≤ 30% with ≥ 3 results → -0.05 penalty (raise threshold, more caution). Wired into chat pipeline: both auto-execute AND confirm-path results now feed back via `gate.record_result()`. 59 tests (48 existing + 11 new) all pass. **§X #95**: confirm-path handler execution now calls `record_result()` on both success and failure — the confirm path was the last unclosed segment of the loop.

**Causal chain**: input → _calculate_exec_score → feedback-adjusted effective threshold → decide auto/confirm/reject → handler execution → record_result(success/fail) → next decide uses adjusted threshold (closed-loop achieved).

**Closed-loop rate**: 100% (both auto-execute and confirm-path now wired).

### 3.6 Heartbeat (MetabolicHeartbeat) — 🟢 C³ = 5.0/10

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

### 3.6 DigitalLifeIntegrator (380L) — 🟡 C³ = 5.0/10 (was 4.5/10, ✅ fixed 2026-06-30)

**修復摘要 (commit 2026-06-29)**: 為 INITIALIZING, AWAKENING, DORMANT 三個遺漏狀態加入實際行為。現在所有 6 個狀態都有 distinct 的行為邏輯。
**§X #71 (2026-06-30)**: DORMANT auto-transition 已加入。兩個自動進入路徑：
1. **時間基礎**: RESTING + 無活動 > `dormant_threshold_minutes`（預設 120min）→ DORMANT
2. **成熟度基礎**: RESTING + maturity < 0.2 → DORMANT（深度休眠節能）
7 個測試驗證轉換邏輯。C³ 更新: 4.5→5.0/10（完整的狀態機循環: MATURE→RESTING→DORMANT 現在是閉合的）。

```python
LifeCycleState:
    INITIALIZING → AWAKENING → GROWING → MATURE → RESTING → DORMANT

async def _apply_state_behaviors(self, state):
    if state == INITIALIZING:
        self.state_matrix.update_beta(learning=0.3, curiosity=0.2)  # ✅ 保守基線
        self.dynamic_params = DynamicThresholdManager(...)           # ✅ 初始化動態參數
        self.record_life_event(...)                                  # ✅ 記錄初始生命事件
    elif state == AWAKENING:
        self.state_matrix.update_beta(learning=0.5, curiosity=0.4)  # ✅ 逐步提升認知
        await self.user_monitor.start()                              # ✅ 啟動使用者監控
        await self.bio_integrator.process_relaxation_event(...)      # ✅ 生物系統覺醒
    elif state == GROWING:
        ...  # Learning boost + memory consolidation                 # (原已存在)
    elif state == MATURE:
        ...  # Formula evaluation to beta clarity                     # (原已存在)
    elif state == RESTING:
        ...  # Bio relaxation + memory consolidation                   # (原已存在)
    elif state == DORMANT:
        self.state_matrix.update_beta(learning=0.05, curiosity=0.05) # ✅ 抑制活動
        self.memory_bridge.trigger_consolidation()                    # ✅ 深層記憶鞏固
        await self.bio_integrator.process_relaxation_event(0.9)       # ✅ 深度放鬆
        # 動態參數漂移檢查                                           # ✅ 資源審計
```

**優點**:
- 生命週期狀態機是真實的 ✅
- **6/6 狀態皆有實際行為** ✅
- 狀態轉換觸發生理和狀態矩陣變化 ✅
- 每個狀態有獨立 emoji 標記：🔧 INITIALIZING, 🔆 AWAKENING, 🌱 GROWING, ✨ MATURE, 💤 RESTING, 💤 DORMANT

**剩餘問題**:
- 行為深但不寬（只影響 state_matrix 和 bio，不影響 routing 或 response）
- `_compute_maturity_score` 依賴 state_matrix，但又用 state_matrix 的 `evaluate_math_spatially` 計算 — 潛在遞迴問題

### 3.7 IntentModel (152L) — 🟡 C³ = 3.0/10 (was 0.1→2.0, ✅ §X #81)

**修復摘要**: `scan_memory_proximity()` 現在被 DLI lifecycle 實際呼叫（之前是死碼）。None bridge 安全處理。

- **Stub 修復** (commit `e713db0e0` 2026-06-28): `scan_memory_proximity()` 和 `generate_homeostatic_intents()` 從 pass 改為真實實作。
- **下游消費接線** (commit `this commit` 2026-06-29): DigitalLifeIntegrator._life_cycle_loop() 每 30s 呼叫 `_update_intent_state()`
- **scan_memory_proximity 接線** (§X #81): `_update_intent_state()` 現已呼叫 `self.intent_manager.scan_memory_proximity(self.memory_bridge, state_snapshot)`。當 memory_bridge 為 None 時安全跳過。
- **None bridge 處理**: `scan_memory_proximity()` 現已在方法入口處檢查 bridge is None，返回而不拋出異常。

**因果鏈**: HAM memory proximity → scan_memory_proximity → create exploration intents → update_intents → get_intent_influence → state matrix update (3 層：外部記憶體 → 內部狀態)**§X #97 (2026-07-01) — 3D multi-parameter influence mapping**: `_update_intent_state()` now maps each 3D intent vector component (ix, iy, iz) to a **distinct parameter** per dimension instead of collapsing to a single scalar magnitude. Alpha: ix→energy, iy→comfort, iz→arousal. Beta: ix→focus, iy→curiosity, iz→learning. Gamma: ix→happiness, iy→trust, iz→anticipation. Delta: ix→bond, iy→trust, iz→attention. Directional intent information now preserved across all 4 controlled dimensions (12 parameters total vs previously 4). C³: 3.0→**4.0/10**.

**Bug fix — zeta dimension missing from DEFAULT_DIMENSIONS**: `state_matrix.py` referenced `self.zeta` in `get_state()` and `get_analysis()` but zeta was not included in DEFAULT_DIMENSIONS (only alpha/beta/gamma/delta/epsilon/theta). This caused `AttributeError` on every bare-minimal DLI initialization that called `get_state()`. Added zeta with consciousness-flow parameters (narrative_flow, temporal_coherence, identity, memory_access).

**剩餘問題**: 
- `retrieve_by_spatial_proximity()` 不在目前 HAM API 中 — bridge 為 None 時不觸發（安全退化）

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
| 4 | **MetaController threshold adjustments → 不自動套用** | 適應性學習中斷 | ✅ **FIXED** (commit `2be528751`) — auto_apply_thresholds() + _analyze_task() uses calibration adjustments |
| 5 | **IntentModel.generate_homeostatic_intents → pass** | 意圖系統不完整 | ✅ **FIXED** (commit `e713db0e0`) — both stubs now real |
| 6 | **LifeCycle 3/6 states 無行為** | 生命週期不完整 | ✅ **FIXED** (commit `this commit`) — all 6 states now have distinct behaviors |

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
| **ExecutionGate → Pipeline** | ✅完整 | **6.0/10** (was 5.0, §X #95) | 8/10 | 3 | 100% | 🟢 執行結果回饋閉環 (auto-execute + confirm-path): record_result() 成功/失敗 → 動態調整有效閾值 (§X #84+§X #95) |
| **DigitalLifeIntegrator** | ✅完整 | **5.0/10** (was 4.5, §X #71) | 8/10 | 2 | 60% | 🟡 6/6 狀態有行為 + DORMANT auto-transition (commit `7b86cf28b`) |
| **MetaController** | ✅完整 | **4.5/10** (was 4.0, §X #115) | 7/10 | 2 | 30% | 🟡 校準快取 + 加權聚合 (dirty-flag cache + reliability-weighted adjustment, §X #115) |
| **EmotionSystem** | ✅完整 | **4.5/10** (was 4.0, §X #94) | 9/10 | 4 | 50% | 🟢 Emotion→BiologicalIntegrator stress/relaxation + interaction_feedback loop (§X #94) |
| **AutonomousLifeCycle** | ✅完整 | **4.5/10** (was 3.5, §X #113) | 8/10 | 3 | 50% | 🟡 決策執行 + 回饋閉環 + config 驅動閾值 + get_behavioral_adjustment() → routing/response pipeline (§X #113) |
| **CausalReasoningEngine** | ✅完整 | **6.0/10** (was 4.5, §X #117) | 9/10 | 4 | 50% | 🟢 Causal routing adjustment closes the loop — predictions now modulate LLM temperature/max_tokens via _get_causal_routing_adjustment() (§X #112+§X #117) |
| **IntentModel** | ✅完整 | **4.0/10** (was 3.0, §X #97) | 7/10 | 3 | 30% | 🟢 3D vector multi-parameter mapping preserves directional info across 12 parameters (§X #97) |

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

### 6.5 P2（中期）— LifeCycle 狀態補全 ✅（已修復 2026-06-29）

**目標**: 為 INITIALIZING, AWAKENING, DORMANT 加入實際行為

| 狀態 | 實作行為 |
|:-----|:---------|
| INITIALIZING | ✅ 設定保守基線 state matrix (learning=0.3, curiosity=0.2)、初始化 dynamic params、記錄初始生命事件 |
| AWAKENING | ✅ 逐步提升認知維度 (learning=0.5, curiosity=0.4)、啟動 user_monitor.start()、生物系統覺醒 |
| DORMANT | ✅ 抑制狀態矩陣 (learning=0.05)、深層記憶鞏固、生物深度放鬆 (0.9)、動態參數漂移檢查 |

**Causal depth 更新**: 3.5→4.5/10（6/6 狀態皆有行為，但 DORMANT 無自動轉入路徑）

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
| ExecutionGate | `ai/core/execution_gate.py` | 248 | ❌ | ✅ 執行結果回饋 (full) | ✅ Router (+ closed-loop via record_result, auto+confirm) | 4 | 🟢 |
| DigitalLifeIntegrator | `core/life/digital_life_integrator.py` | 380 | ✅ | ✅ | ✅ 6/6 狀態行為 | 2 | 🟡 |
| MetaController | `ai/meta/meta_controller.py` | 130 | ❌ | ✅ EWMA | ✅ auto_apply_thresholds | 2 | 🟡 |
| AutonomousLifeCycle | `core/life/autonomous_life_cycle.py` | 420+ | ✅ | ✅ | ✅ BehaviorExecutor + routing/response pipeline via get_behavioral_adjustment() | 4 | 🟡→🟢 |
| EmotionSystem | `ai/alignment/emotion_system.py` | 280 | ❌ | ✅ | ✅ apply_influence + prompt + interaction feedback | 4 | 🟢 |
| CausalReasoningEngine | `ai/reasoning/causal_reasoning_engine.py` | 218 | ❌ | ✅ | ✅ Causal routing adjustment closes the loop — predictions affect LLM temperature/max_tokens via _get_causal_routing_adjustment | 4 | 🟢 |
| IntentModel | `core/life/intent_model.py` | 80 | ❌ | ✅ | ✅ DigitalLifeIntegrator (3D multi-parameter) | 3 | 🟡 |
| ModalityGateway | `core/life/digital_life_integrator.py` | 70 | ❌ | ✅ | ✅ Prompt injection via _append_modality_state (DLI-preferred singleton) | 3 | 🟡 |

**總計**: 9 個核心自主性組件，7 個有鏈深度 ≥ 1（已接線至下游消費者），2 個傳遞良好，1 個孤立。

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
| ✅ **AutonomousLifeCycle** | 修復完成 (commits `40dce741a` + §X #74) | `_execute_decision()` 已加入，分派至 BehaviorExecutor + `execution_success_rate` 回饋閉環 |
| ✅ **CausalReasoningEngine** | 修復完成 (commit `78dac066e`) | predict() 已接入 LLM prompt 管線 (chat_routes._inject_causal_predictions → prompt_builder._append_causal_insights) |
| ✅ **EmotionSystem** | 修復完成 (commit `f9cf68ac5`) | apply_influence() 真實 PAD 映射 + get_behavioral_adjustment() 情緒→行為接線 |
| ✅ **IntentModel** | 修復完成 (commits `e713db0e0` + `this commit` 2026-06-29) | stubs 已實作 + 已接入 DigitalLifeIntegrator 管線，get_intent_influence() 實際驅動 state matrix 更新 |
| ✅ **MetaController** | 修復完成 (commit `f9cf68ac5` + `2be528751`) | auto_apply_thresholds() 已加入，NeuroAutoSelector._analyze_task() 現在讀取調整值影響 reasoning/quality/high_demand 門檻 |
| ✅ **DigitalLifeIntegrator** | 修復完成 (commit `this commit` 2026-06-29) | 6/6 生命週期狀態皆有實際行為 — INITIALIZING (保守基線+dynamic params)、AWAKENING (user monitor+bio 覺醒)、DORMANT (深度鞏固+放鬆+資源審計) |
| ✅ **Heartbeat Integration** | 修復完成 (commit `this commit` 2026-06-29) | Integration 循環間隔從固定 0.1s → 2.0-10.0s 動態 (基於 arousal)，頻率差從 50-600x 降至 ~2x |
| ✅ **Level5ASI Process** | 修復完成 (commit `this commit` 2026-06-29) | 移除 `await asyncio.sleep(1.0)` 模擬延遲，改為 `await asyncio.sleep(0)` 事件循環讓出 |
| ❌ **前端 Live2D** | 隨機彩色矩形 | 補齊 Live2D 模型渲染路徑 |
| ❌ **前端 Dashboard** | 假資料或 TODO handler | 接上真實後端 API |
| ✅ **encode_with_retry empty data** | 修復完成 (commit `f05e020d7`, §X #60) | Fast-fail on empty data: 不浪費 3 次 retry 在無效資料上，直接寫入 crisis_log 並返回 |
| ✅ **Heartbeat stop() bug** | 修復完成 (commit `this commit` 2026-06-29) | stop() 未取消 _integration_task，現已補齊並處理 CancelledError |
| ✅ **CyberIdentity reflection** | 修復完成 (commit `this commit` 2026-06-29) | _reflection_task 加入 exception handler |
| ✅ **Broadcast task** | 修復完成 (commit `this commit` 2026-06-29) | 廣播 task 加入 exception handler |

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
| 21 | Metabolic Interval | `angela_model_core.py` | **2.0s** → clock.wait_for_ticks(20) @10Hz (§X #76) | 代謝更新 | 🟢 現已使用 GlobalSystemClock 事件驅動時間基 (2026-07-01) — `asyncio.sleep(2.0)` 改為 `clock.wait_for_ticks(20)` |
| 22 | Heartbeat Primary | `heartbeat.py` | **5.0~60.0s** (動態) | 生物/代謝循環 | ✅ 動態調整，最佳實踐 |
| 23 | Heartbeat Integration | `heartbeat.py` | **2.0~10.0s** (動態, 依 arousal) | 小腦/神經整合 | ✅ 已修復 2026-06-29 — 頻率從 0.1s→動態 2-10s，消除 50-600x 差。stop() 現同時取消 Integration task (commit `this commit`) |
| 24 | Life Cycle Check | `digital_life_integrator.py` | **10.0s** | 生命週期檢查 | ✅ 合理 |
| 25 | Proactive Check | `proactive_interaction_system.py` | **15.0s** | 主動互動檢查 | ✅ 合理 |
| 26 | HAM Hourly | `ham_background_tasks.py` | **3600.0s** (1/hr) | HAM背景任務 | ✅ 長時間任務 |
| 27 | Narrative Update | `cyber_identity.py` | **86400.0s** (1/day) | 敘事更新 | ✅ 每日更新合理 |
| 28 | Decision Interval | `autonomous_life_cycle.py` | **60.0s** (1min, was 300s/5min) | 生命決策 | ✅ 已修復 2026-06-29 — §8.6 #8: 預設從 300s→60s |
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

#### 🟡 有問題 (11/32)
- **重複循環**: Bridge Poll(0.1s) 和 Bridge Fast(0.05s) 做類似事情
- **不一致的同類循環**: ANS Update(0.5s) vs ANS Tick(1.0s) 在同一系統內
- **HAM同步太慢**: 3600s(1hr) 可能導致記憶遺失
- **Sleep Short 濫用**: 8+ 個組件使用同樣的 0.1s sleep key，但代表不同語義

#### 🔴 不合理 (6/32) — 全部已修復 ✅
- ~~**Level5 Process 1s**: 已修復 2026-06-29 ✅~~
- ~~**代謝 2s vs 心跳 5-60s**: 兩個代謝相關循環頻率不一致~~
- ~~**Heartbeat 兩個循環**: Primary(5-60s) 和 Integration(2-10s) 頻率差 ~2倍 ✅ 已修復 2026-06-29~~
- ~~**Behavoir Loop Tight 1.0s**: 5+ 個 lifecycle 循環使用相同 sleep 值做「防止緊密循環」，應統一管理~~
- ~~**ModalityGateway**: 狀態更新但無人讀 — §X #116 (2026-07-02) 已閉合因果鏈 ✅~~

### 8.4 硬體感知分析

#### 目前有硬體感知的組件

| 組件 | 感測的硬體 | 如何影響行為 |
|:-----|:-----------|:-------------|
| MetabolicHeartbeat | CPU使用率, 電池電量 | CPU高→fatigue增加→stress升高→心跳加速→移動變慢 |
| MetabolicHeartbeat | 電量 < 20% | 觸發 starvation stress event |
| **所有 loop_sleep() 使用者** | **HardwareProfile 場景偵測** | 2026-06-29: `loop_sleep()` 現自動套用 `HardwareProfile.apply_multiplier()`。桌機/伺服器頻率提高，電池/低功耗裝置頻率降低。 |
| ActionExecutor | 無 | 固定 50ms 循環（透過 loop_sleep 取得硬體感知值） |
| ANS | 無 | 固定 0.5s 循環（透過 loop_sleep 取得硬體感知值） |
| 其餘 28+ 循環 | **全部** 透過 loop_sleep() | 全部固定頻率 → 現在有硬體感知基本調整 |

#### 缺少的硬體適應

| 硬體指標 | 目前誰在用？ | 應該影響誰？ |
|:---------|:------------|:-------------|
| **CPU溫度** | 無人使用 | 全部高頻循環（應在過熱時降頻） |
| **記憶體使用率** | 無人使用 | 資料庫查詢頻率、batch size |
| **GPU使用率** | 無人使用 | 視覺處理頻率、訓練頻率 |
| **磁碟IO** | 無人使用 | 持久化頻率、HAM同步頻率 |
| **網路延遲** | 無人使用 | 外部API呼叫頻率、同步策略 |
| **電池模式** | HardwareProfile (自動場景偵測) | ✅ 全部循環透過 `loop_sleep()` — 筆電(一般) 0.7x、省電模式 0.5x |

#### 不同硬體的合理值 — 現在透過 HardwareProfile + loop_sleep() 自動套用

| 硬體場景 | ANS | 心跳 | 決策 | 神經可塑性 | 敘事 |
|:---------|:---:|:----:|:----:|:---------:|:----:|
| **桌機(高效能)** | 0.5s | 5-30s 動態 | 60s | 60s | 1day |
| **筆電(一般)** | 1.0s | 10-60s 動態 | 120s | 120s | 1day |
| **筆電(電池)** | 2.0s | 30-120s 動態 | 300s | 300s | 1day |
| **低功耗裝置(RPi)** | 5.0s | 60-300s 動態 | 600s | 600s | 7days |
| **雲端伺服器** | 0.2s | 1-10s 動態 | 30s | 30s | 1day |

**目前情況**: HardwareProfile 基本整合完成：`loop_sleep()` 自動套用 multiplier。即時硬體指標 (CPU溫度、GPU負載) 的動態調整為未來工作。

#### 歷史脈絡

```
2026-06-28: 所有循環使用固定值。只有 Heartbeat 有動態調整（stress/arousal-based）
2026-06-29: HardwareProfile 建立（§8.6 #5），定義 5 種場景的頻率表
2026-06-29: loop_sleep() 接線（§8.6 #4 BASIC），所有 32 個循環自動獲得硬體感知
```

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
| 1 | **引入 GlobalSystemClock**: 統一時間基準，支援 tick 訂閱 | 🔴 **DONE** (2026-07-01, §X #76) — `core/clock/global_system_clock.py`: 可設定頻率 (0.1-1000Hz)、start/stop、tick 訂閱 (任意間隔)、disable/enable 訂閱、異常隔離。13 tests pass。 | 高 | 中 |
| 2 | **循環頻率標準化**: 合併重複循環、統一語義命名 | ✅ **DONE** (2026-06-29) — Bridge `_wait_for_completion` 改用 `asyncio.Event` 取代 0.05s 輪詢，消除 bridge_fast 與 bridge_poll 其中一個重複循環。`emotion_tick`(1.0s) 整併至 `emotion_update`(1.0s) — 同一檔案同名同值。`bridge_fast` 重新命名為 `bridge_error_backoff` — 語義明確化。**3/4 重複循環已處理** |
| 3 | **事件驅動取代輪詢**: `asyncio.Event()` 取代 80% 的 sleep 輪詢 | 🟢 **PARTIAL** (2026-07-01) — Bridge `_wait_for_completion` 已從 0.05s 輪詢改為 `asyncio.Event` 事件驅動。AngelaModelCore._metabolic_loop 已從 `asyncio.sleep(2.0)` 改為 `clock.wait_for_ticks(20)` 事件驅動 (§X #77)。79+ 處 sleep 輪詢尚待改進 |
| 4 | **硬體感知動態頻率**: 根據 CPU/GPU/電池動態調整所有循環 | 🟢 **BASIC** (2026-06-29) — `loop_sleep()` 現已自動套用 HardwareProfile multiplier。所有 32 個循環現在有硬體感知頻率調整。待改進：個別硬體指標 (CPU溫度、GPU負載) 的即時動態調整。 |
| 5 | **HardwareProfile**: 定義 5 種硬體場景的預設頻率表 | ✅ **DONE** (2026-06-29) — `hardware_profile.py`: HardwareScenario enum (5 scenarios), FrequencyProfile dataclass (22 interval fields), PROFILES with distinct values for each scenario, HardwareProfile class with auto-detection (env var, CI, headless Linux, ARM, battery, default), runtime overrides, multiplier API. 20 tests pass |
| 6 | **消除 time.sleep()**: 所有同步 sleep 改為 asyncio.sleep | ✅ **DONE** (2026-06-29) — 確認所有剩餘 `time.sleep()` 呼叫皆在同步/執行緒上下文中 (agent_manager._wait_router_health, agent_manager_extensions subprocess 範例, repl.py 執行緒, execution_monitor 監控執行緒)。非 async 函式中的 `time.sleep()` 為正確用法。§8.6 #6 實質完成 |
| 7 | **Fire-and-forget 異常處理**: 為所有 create_task 註冊 exception handler | 🟢 **EXTENDED** (2026-06-29) — 又 6 個檔案加入 try/except 保護背景循環: action_execution_bridge._execution_loop + 5 個 bio 循環 (ANS, EmotionalBlending, MultidimensionalTrigger, Neuroplasticity, Tactile)。總計: **16 task handlers in 13 files**（原 10 handlers / 7 files + 6 new protected loops）。§8.6 #7 實質完成 — 所有背景 loop 皆已保護 | 🔴 高 | 低 |
| 8 | **自主決策頻率提升**: 300s→60s，讓自主性更即時 | ✅ **DONE** (2026-06-29) — `autonomous_life_cycle.py`: 預設 `decision_interval` 300.0→60.0 |

### 8.7 硬體設定檔 — 實作

File: `apps/backend/src/core/system/config/hardware_profile.py`

已實作 5 種硬體場景的頻率設定檔，包含 22 個循環欄位 + base_multiplier。

| 場景 | base_multiplier | ANS | 心跳 | 決策 | 神經可塑性 |
|:-----|:---------------:|:---:|:----:|:----:|:---------:|
| HIGH_PERFORMANCE_DESKTOP | 1.0 | 0.5s | 5-30s | 60s | 60s |
| LAPTOP_NORMAL | 0.7 | 1.0s | 10-60s | 120s | 120s |
| LAPTOP_POWER_SAVER | 0.5 | 2.0s | 30-120s | 300s | 300s |
| LOW_POWER_DEVICE | 0.3 | 5.0s | 60-300s | 600s | 600s |
| SERVER_CLOUD | 2.0 | 0.2s | 1-10s | 30s | 30s |

自動偵測優先級: env var → CI → headless Linux → ARM → battery → default

API: `HardwareProfile()` → `.scenario`, `.profile`, `.get(key, default)`, `.set_override(key, value)`, `.apply_multiplier(base_value)`, `.get_summary()`

詳見: `apps/backend/src/core/system/config/hardware_profile.py` (實作) + `tests/core/test_hardware_profile.py` (20 測試)

---

## 9. 維護會話追蹤

### 9.1 §X #87-#93 (2026-07-01): 維護與測試整理 — 無 C³ 影響

以下會話均為文件同步、測試去重、審計工作，**未變更任何因果鏈深度或分數**：

| §X | 工作 | 類型 | C³ 影響 |
|:--:|:-----|:----:|:-------:|
| #87 | MD test count sync (4,643→4,717, 5 files) | 文件同步 | 無 |
| #88 | Orphan print-based tests → pytest skip (3 files, +9 tests) | 測試整理 | 無 |
| #89 | Import-only test consolidation (3→1 file, 4,726→4,723) | 測試去重 | 無 |
| #90 | IMPROVEMENT_ROADMAP.md sync | 文件同步 | 無 |
| #91 | README.md sync (4,726→4,723) | 文件同步 | 無 |
| #92 | AGENTS.md NOTE sync (§X #87-91) | 文件同步 | 無 |
| #93 | ACTIVE_SCRIPTS.md stale ref removal | 文件清理 | 無 |
| #94 | EmotionSystem interaction_feedback loop (+11 tests, 4,723→4,734) | 功能新增 | C³ +0.5 (4.0→4.5) (CAUSAL_CHAIN §3.3) |
| #95 | ExecutionGate _results class-level → cross-instance feedback persistence (+1 test, 4,734→4,735) | 修復 | C³ +1.0 (5.0→6.0, 真正生效 — 之前實例級別導致跨回合反饋遺失) |
| #96 | AutonomousLifeCycle per-type execution feedback — _evaluate_and_decide() reads per-type stats for threshold modulation (+6 tests, 4,735→4,741) | 功能新增 | C³ +0.5 (3.5→4.0, 決策類型層級回饋) |
| #97 | IntentModel 3D multi-parameter mapping — each 3D vector component maps to distinct parameter per dimension; state_matrix zeta dimension fix (+6 tests, 4,741→4,748) | 功能增強+修復 | C³ +1.0 (3.0→4.0, 全12參數方向性 preserved + zeta bug fix enables intent update) |
| #98 | DLI circular import fix — brain_bridge_service.py TYPE_CHECKING guard breaks chain (DLI→services→brain_bridge_service→DLI). Unblocks +2 tests (was 6 pass+1 skip→7 pass; test_get_digital_life now runs). | 修復 | 無 C³ 影響（結構性改善，解鎖測試覆蓋） |
| #99 | Bare except:pass → proper logging across 15 instances in 10 files | 品質改善 | 無 C³ 影響 |
| #100 | DynamicThresholdManager.update_from_state_matrix() real implementation (+7 tests) | 功能新增 | 無 C³ 影響（非因果鏈參與者） |
| #101 | CAUSAL_CHAIN_COMPLETENESS.md duplicate lines fix | 文件整理 | 無 C³ 影響 |
| #102 | 3 orphan fixes: code_understanding_tool stub→real AST; evolution_engine docstring→real impl; PersonalityAdapter graceful degradation (PersonalityManager removed Phase 12) | 孤兒修復 | 無 C³ 影響 |
| #103 | Test consolidation & quality: rovo dedup (-3 tests, import already covered); training target validation (+9, baseline for VisualDecoder/AudioWaveformDecoder); 2 weak test files fixed (try/except/pytest.fail removed, silent-pass import tests split into 6 parametrized tests + bug fix get_timestamp→now_timestamp) | 測試整理 | 無 C³ 影響 |
| #104 | _SMOKE_MODULES audit: removed 9 dead entries (Phase 9-12 deleted modules), fixed 8 path prefixes (apps.backend.src.→relative) — 0 imports silently skipped for the first time | 測試整理 | 無 C³ 影響 |
| #105 | 4 mock-fallback fixes: test_trained_models.py: 11 mock tests against nonexistent ai.models → 3 proper import skips; test_type_fixes.py: removed unnecessary MockVectorMemoryStore fallback (real module exists); test_benchmark.py: except Exception: return [] → proper pytest.skip() for deleted ai.ops; deadlock_detector.py: except ImportError: pass → logger.debug() | 測試品質 | 無 C³ 影響 |
| #106 | test_quick_e2e.py: 4 false-pass async tests → proper @pytest.mark.skip; test_learning_orchestrator.py: removed unnecessary sys.modules mock injection (real LearningOrchestrator doesn't import from ai.evaluation); MD sync across 5 files | 測試品質+文件同步 | 無 C³ 影響 |
| #109 | Removed 13 stale `# (removed incomplete import: from …)` comments across 6 files (system_manager.py, tool_context.py, model_context.py, integration_with_ham.py, config.py, dialogue_context.py) | 代碼清理 | 無 C³ 影響 |
| #110 | Training quality benchmarks — TestQualityMetrics (8: ssim/psnr/snr) + TestTextureBenchmark (2: CIFAR-10 texture training) — +11 tests (4,742→4,753) | 測試品質 | 無 C³ 影響 |
| #111 | TrainingCoordinator production wiring — asyncio.Lock + eviction caps (max 100 examples / 10000 hashes per domain) + all methods async + lifespan.py factory + ChatService dedup/tracking wiring + scripts/train_pipeline.py async bridge fix (+3 eviction tests, 4,753) | 生產接線 | 無 C³ 影響 |
| #111d | SyntaxError fix — chat_service.py orphaned except block from §X #111 caused 8 cascading collection errors. Moved orphaned `except` back before TrainingCoordinator block. Defense-in-depth: `except (ImportError, SyntaxError)` in protocols.py + test_state_matrix_api.py. +138 tests unblocked (4,618→4,756). | 修復 | 無 C³ 影響（結構性修復，解鎖測試收集） |

**總結**: §X #94 EmotionSystem C³ +0.5; §X #95 ExecutionGate C³ +1.0; §X #96 AutonomousLifeCycle C³ +0.5; §X #97 IntentModel C³ +1.0 + zeta fix; §X #98 DLI circular import fix unblocks +2 tests; §X #99 15 except:pass→logging; §X #100 DynamicThresholdManager real impl +7 tests; §X #101 CAUSAL_CHAIN duplicate fix; §X #102 3 orphan fixes; §X #103 test consolidation & quality (+11 net, 4,755→4,766); §X #104 _SMOKE_MODULES audit (-18, 4,766→4,748); §X #105 4 mock-fallback fixes (-6, 4,748→4,742); §X #106 test_quick_e2e proper skip + learning_orchestrator mock cleanup + MD sync; §X #109 13 stale import comments cleaned; §X #110 +11 training quality benchmarks (4,742→4,753); §X #111 TrainingCoordinator production wiring — async + eviction + ChatService dedup; §X #111d SyntaxError fix — orphaned except in chat_service.py, unblocks 8 collection errors (+138, 4,618→4,756); §X #112 CausalReasoningEngine retrospective_warm_start() — predict() works from Round 1 (+7 tests, 4,756→4,763); §X #113 AutonomousLifeCycle behavioral_adjustment → routing/response pipeline (+10 tests, 4,763→4,774); §X #114 Lifecycle singleton unification (+0 tests, 4,774); §X #115 MetaController calibration cache + weighted adjustment — C³ 4.0→4.5 (+9 tests, 4,774→4,783); §X #116 ModalityGateway state → prompt injection — C³ 0.5→3.0 (+3 tests, 4,783→4,786); §X #117 CausalReasoningEngine closed-loop — _get_causal_routing_adjustment() → temperature/max_tokens modulation (+8 tests, 4,786→**4,794 tests — 0 errors**, C³ 4.5→6.0); §X #118 Test consolidation — _patch_routing_causal helper extract in test_causal_session_buffer.py (0 net, 4,794); §X #119 Import test consolidation — merged test_imports.py into test_smoke_imports.py (+6 net, 4,794→**4,800 tests — 0 errors**)。