# 8D State Matrix 完整修復計畫

## 1. 維度總覽

Angela 的狀態矩陣實際上有 **8 個維度**，但只有 **7 個在 `StateMatrix4D` 中**，η 是獨立系統：

| # | 維度 | 中文名 | 負責 | 初始座標 (X,Y,Z) | Weight | Values 欄位 |
|---|------|--------|------|-------------------|--------|-------------|
| 1 | **α Alpha** | 能量 | 生理能量、舒適、覺醒 | `(0, -5, 0)` | 1.0 | energy, comfort, arousal, rest_need, vitality, tension |
| 2 | **β Beta** | 認知 | 好奇心、專注、學習 | `(0, 10, 0)` | 1.0 | curiosity, focus, confusion, learning, clarity, creativity |
| 3 | **γ Gamma** | 情感 | 快樂、悲傷、憤怒、恐懼等 | `(0, 2, 2)` | 1.0 | happiness, sadness, anger, fear, disgust, surprise, trust, anticipation, love, calm |
| 4 | **δ Delta** | 關係 | 注意力、親密、信任 | `(0, 0, 10)` | 1.0 | attention, bond, trust, presence, intimacy, engagement |
| 5 | **ε Epsilon** | 精確 | 邏輯、精確度、抽象 | `(0, 0, 0)` | 0.3 | logic, precision, abstraction, certainty, complexity, fatigue |
| 6 | **θ Theta** | 元認知 | 新穎度、複雜度、自省 | `(0, 0, 0)` | 0.2 | novelty, complexity, ambiguity, abstraction_level, dimension_fit, creation_urge, theta_negativity, correction_urge, audit_intensity |
| 7 | **ζ Zeta** | 意識流 | 時間連貫、記憶深度、敘事流 | `(0, 0, 0)` | 0.2 | temporal_coherence, memory_depth, narrative_flow, identity_continuity |
| 8 | **η Eta** | 執行層 | 模組觸發、執行追蹤、成功率 | (非座標系統) | N/A | active_modules, module_count, execution_count, success_rate, structural_drift |

### η 特殊性

η **不是** `StateMatrix4D` 的維度。它在 `state_matrix_adapter.py` 中以 `EtaAxisState`（定義於 `eta_axis.py`）獨立存在：
- 擁有自己的 `AtomicModuleType`、`LogicGateType`、`RouterType`
- 不受 XYZ 座標系統影響
- 由 θ 信號驅動觸發
- 正確地在 `export_for_llm()` 中包含

---

## 2. 計算流程圖

```
Dimension Values (energy=0.5, focus=0.7, ...)
        │
        │
        ├──→ compute_coordinate()    ←── 【BUG: 死代碼，從未呼叫】
        │     根據 values 計算 XYZ
        │
        ├──→ perform_spatial_reasoning()  ←── 【BUG: 只改 X】
        │     修改 coordinate (X only)
        │
        ├──→ compute_influences()
        │     使用 influence_matrix 跨維度傳播
        │     → INFLUENCE_RULES 場級映射
        │       【BUG: ε/θ 規則空、ζ 不存在】
        │
        ├──→ get_state() / export_for_llm()
        │     【BUG: get_state() 只回傳 αβγδ】
        │
        └──→ StateMatrixFacade.update()
              → _group_kwargs_by_axis()
                【BUG: 缺少大量 field→axis 映射】
```

---

## 3. 發現的 Bug 完整列表

### Bug A: `compute_coordinate()` 是死代碼

- **位置**: `state_matrix.py:126-201`
- **問題**: 此方法可以從維度 values 正確計算 XYZ 座標，但**整個專案沒有任何地方呼叫它**
- **影響**: 當 values 改變時（如 `energy` 從 0.5 變成 0.8），XYZ 座標**不會自動更新**。座標只能透過 `perform_spatial_reasoning()` 修改（而這個方法只改 X）
- **公式範例**（本應運作但從未執行）：
  ```
  alpha.X = comfort - tension
  alpha.Y = (energy - rest_need) * 10.0
  alpha.Z = arousal - 0.5
  ```
- **修復**: 在每個 `update_*()` 方法末尾呼叫 `compute_coordinate()`

### Bug B: `perform_spatial_reasoning()` 只修改 X 座標

- **位置**: `cognitive_operations.py:56-83`
- **問題**: 所有 `ACCUMULATE`、`DECREMENT`、`AMPLIFY`、`DIMINISH` 操作都只修改 `x`：
  ```python
  new_coord = (x + magnitude, y, z)  # Y 和 Z 永遠不變
  ```
- **影響**: Y 和 Z 座標永遠停留在初始值（α=0,-5,0、β=0,10,0、γ=0,2,2、δ=0,0,10），從未被真實計算偏移
- **修復**: 為不同 CognitiveOp 加上 Y/Z 的運算策略（見第 7 節）

### Bug C: `get_state()` 只回傳 4/7 維度

- **位置**: `state_matrix.py:1329-1334`
- **問題**: 不帶參數呼叫時，只回傳 `alpha`、`beta`、`gamma`、`delta`，**遺漏 epsilon、theta、zeta**
- **影響**:
  - `neuro_auto_selector.py:295` 讀取 state 時取不到 ε/θ/ζ 的值
  - 任何依賴 `get_state()` 的外部位（如 WebSocket 同步通道）都看不到完整的 8D
- **修復**: 將 ε/θ/ζ 加入回傳值

### Bug D: `INFLUENCE_RULES` 不完整

- **位置**: `influence_applicator.py:18-79`
- **問題**:
  - `epsilon` 影響規則為空 dict `{}`（第 77 行）
  - `theta` 影響規則為空 dict `{}`（第 78 行）
  - `zeta` 完全不存在於 `INFLUENCE_RULES` 中
- **影響**: ε、θ、ζ 的維度值變化不會透過 InfluenceApplicator 傳播到其他維度
- **修復**: 補上 ε→αβγδ、θ→αβγδε、ζ→αβγδεθ 的欄位級映射

### Bug E: `StateMatrixFacade._group_kwargs_by_axis()` 映射不全

- **位置**: `state_matrix_adapter.py:1390-1405`
- **問題**: `key_map` 缺少大量欄位，未知鍵預設路由到 `alpha`（第 1401 行 `key_map.get(key, 'alpha')`）
- **遺漏的 field→axis 映射**：
  - α 欄位: `rest_need`、`vitality`
  - β 欄位: `clarity`、`creativity`
  - γ 欄位: `disgust`、`surprise`、`anticipation`、`love`、`calm`
  - δ 欄位: `intimacy`、`engagement`
  - ε 欄位: `abstraction`、`certainty`、`complexity`、`fatigue`（目前只有 logic/precision）
  - θ 欄位: `complexity`、`ambiguity`、`abstraction_level`、`dimension_fit`、`correction_urge`、`audit_intensity`（目前只有 novelty/creation_urge/theta_negativity）
  - ζ 欄位: `temporal_coherence`、`memory_depth`、`narrative_flow`、`identity_continuity`（**完全沒有**）
- **影響**: ζ 的所有更新都被導向 α，η 的所有更新也被導向 α
- **修復**: 補齊所有 field→axis 映射

### Bug F: `get_analysis()` 方法不存在

- **位置**: `state_matrix.py` 中無此方法，但 `state_matrix_adapter.py:318`、`digital_life_integrator.py:405` 等呼叫它
- **影響**: 執行時會拋出 `AttributeError`
- **修復**: 在 `StateMatrix4D` 上實作 `get_analysis()` 方法

### Bug G: 維度數量命名不一致

- 內部註解自稱「4D 矩陣」、「5D 狀態矩陣」、「6D State Matrix System」
- 類別名為 `StateMatrix4D` 但實際有 7 維
- **影響**: 可維護性、新人理解門檻

---

## 4. 現有正確運作的部分 ✅

| 元件 | 狀態 | 備註 |
|------|------|------|
| `export_for_llm()` | ✅ | 包含 αβγδεθζ + η，是所有匯出中最完整的 |
| `export_to_dict()` | ✅ | 包含所有 7 維 |
| `get_coordinates()` | ✅ | 遍歷 `self.dimensions.items()`，完整回傳 |
| `compute_influences()` | ✅ | 影響矩陣本身完整（雖然規則不完整） |
| `self.dimensions` dict | ✅ | 包含 αβγδεθζ（7 個） |
| 維度初始值設定 | ✅ | 每個維度的 field 初始值合理 |
| η EtaAxisState | ✅ | 獨立系統運作正確 |
| `semantic_anchors` | ✅ | 包含 αβγδεθζ（7 個） |

---

## 5. 修復優先級

```
P0 ─── 崩潰/資料丟失
  Bug C: get_state() 遺漏 3 維  →  NGR/auto 讀不到 εθζ
  Bug E: Facade.update() 映射不全  →  ζ 更新進 α，資料錯誤
  Bug F: get_analysis() 不存在  →  runtime AttributeError

P1 ─── 功能不完整
  Bug D: INFLUENCE_RULES 空/缺 ζ  →  εθζ 不參與跨維度傳播
  Bug A: compute_coordinate() 死代碼  →  values 改變不刷新座標

P2 ─── 正確性
  Bug B: spatial_reasoning 只改 X  →  YZ 永遠初始值
  類別名 StateMatrix4D → 8D  →  命名誤導

P3 ─── 清理
  Bug G: 註解不一致  →  維護成本
```

---

## 6. 實作步驟

### Step 1 — 修復 `get_state()`（Bug C，P0）

**檔案**: `state_matrix.py:1329-1334`

將：
```python
return {
    "alpha": {...},
    "beta": {...},
    "gamma": {...},
    "delta": {...},
}
```

改為：
```python
return {
    "alpha": {...},
    "beta": {...},
    "gamma": {...},
    "delta": {...},
    "epsilon": {**self.epsilon.values.copy(), "coordinate": self.epsilon.coordinate},
    "theta": {**self.theta.values.copy(), "coordinate": self.theta.coordinate},
    "zeta": {**self.zeta.values.copy(), "coordinate": self.zeta.coordinate},
}
```

同時檢查所有 `get_state()` 的呼叫者是否需要更新維度名稱常量（如 `neuro_auto_selector.py:295-306` 中查詢 `state.get("eta")` 但 `get_state()` 從不回傳 eta，因為 η 不在 `StateMatrix4D` 中）。

### Step 2 — 修復 `_group_kwargs_by_axis()`（Bug E，P0）

**檔案**: `state_matrix_adapter.py:1390-1405`

補齊所有遺漏的 field→axis 映射，特別是：
```python
key_map = {
    # ... existing ...
    # Alpha additions
    'rest_need': 'alpha', 'vitality': 'alpha',
    # Beta additions
    'clarity': 'beta', 'creativity': 'beta',
    # Gamma additions
    'disgust': 'gamma', 'surprise': 'gamma', 'anticipation': 'gamma',
    'love': 'gamma', 'calm': 'gamma',
    # Delta additions
    'intimacy': 'delta', 'engagement': 'delta',
    # Epsilon additions
    'abstraction': 'epsilon', 'certainty': 'epsilon',
    'complexity': 'epsilon', 'fatigue': 'epsilon',
    # Theta additions
    'complexity_theta': 'theta',  # avoid key collision with epsilon.complexity
    'ambiguity': 'theta', 'abstraction_level': 'theta',
    'dimension_fit': 'theta', 'correction_urge': 'theta',
    'audit_intensity': 'theta',
    # Zeta (全新增)
    'temporal_coherence': 'zeta', 'memory_depth': 'zeta',
    'narrative_flow': 'zeta', 'identity_continuity': 'zeta',
}
```

同時 `StateMatrixFacade.update()` 加入 `zeta` 路由分支。

### Step 3 — 修復 `get_analysis()`（Bug F，P0）

**檔案**: `state_matrix.py`

新增方法：
```python
def get_analysis(self, dimension: Optional[str] = None) -> Dict[str, Any]:
    """回傳完整的分析資料，包含所有維度的數值、座標、權重、wellbeing"""
    state = self.get_state(dimension)
    return {
        "state": state,
        "coordinates": self.get_coordinates(),
        "averages": self.get_dimension_averages(),
        "wellbeing": self.compute_wellbeing(),
        "dimension_count": len(self.dimensions),
    }
```

### Step 4 — 修復 `INFLUENCE_RULES`（Bug D，P1）

**檔案**: `influence_applicator.py:18-79`

為 ε、θ、ζ 補上場級影響規則（需要分析各維度 field 之間的合理映射）：

```
epsilon→alpha:  logic→energy, precision→tension
epsilon→beta:   logic→clarity, precision→focus
epsilon→gamma:  fatigue→sadness, precision→calm
epsilon→delta:  logic→attention, precision→bond
epsilon→theta:  certainty→ambiguity(negative)

theta→alpha:    novelty→arousal, theta_negativity→tension
theta→delta:    novelty→attention, ambiguity→bond(negative)

zeta→alpha:     temporal_coherence→vitality
zeta→beta:      narrative_flow→creativity, memory_depth→clarity
zeta→gamma:     identity_continuity→trust, temporal_coherence→calm
zeta→delta:     memory_depth→bond, narrative_flow→presence
zeta→epsilon:   temporal_coherence→certainty
zeta→theta:     memory_depth→novelty, identity_continuity→dimension_fit
```

### Step 5 — 復活 `compute_coordinate()`（Bug A，P1）

**檔案**: `state_matrix.py`

在每個 `update_*()` 方法末尾加上 `self.{dim}.compute_coordinate()`：

```python
def update_alpha(self, **kwargs):
    for key, value in kwargs.items():
        if key in self.alpha.values:
            self.alpha.values[key] = value
    self.alpha.compute_coordinate()  # ← 新增
```

對 `update_beta`、`update_gamma`、`update_delta`、`update_epsilon`、`update_theta`、`update_zeta` 同樣處理。

同時確認 `compute_coordinate()` 的公式正確：
- 檢查 zeta 的公式（192-200行）中 `memory` 和 `narrative` 應該是 `memory_depth` 和 `narrative_flow`
- 目前程式碼：
  ```python
  y = (state.values.get("memory", 0.5) + state.values.get("narrative", 0.5)) / 2 * 10.0
  ```
  應改為：
  ```python
  y = (state.values.get("memory_depth", 0.6) + state.values.get("narrative_flow", 0.7)) / 2 * 10.0
  ```

### Step 6 — 修復 `perform_spatial_reasoning()`（Bug B，P2）

**檔案**: `cognitive_operations.py:56-83`

為不同操作加上 Y/Z 的處理策略。例如：

```python
if op == CognitiveOp.ACCUMULATE:
    new_coord = (x + magnitude, y + magnitude * 0.3, z + magnitude * 0.1)
elif op == CognitiveOp.DECREMENT:
    new_coord = (x - magnitude, y - magnitude * 0.3, z - magnitude * 0.1)
elif op == CognitiveOp.AMPLIFY:
    new_coord = (x * magnitude, y * magnitude * 0.5, z * magnitude * 0.5)
elif op == CognitiveOp.DIMINISH:
    divisor = magnitude if magnitude != 0 else 1
    new_coord = (x / divisor, y / (divisor * 0.5 + 0.5), z / (divisor * 0.5 + 0.5))
else:  # RESONATE
    new_coord = (x + magnitude * 0.1, y + magnitude * 0.1, z + magnitude * 0.1)
```

或者引入 `spatial_ratio` 配置，讓不同維度的 XYZ 敏感度可調。

### Step 7 — 清理命名（Bug G，P3）

- `StateMatrix4D` → 保留別名，新增 `StateMatrix` 類別名
- 更新檔案頂部註解：`6D State Matrix System` → `8D State Matrix System`
- 考慮是否將 η 正式納入 `self.dimensions`

---

## 7. 影響分析

| Bug | 影響範圍 | 修復難度 | 風險 |
|-----|---------|---------|------|
| C: get_state | NGR composer, NeuroAutoSelector, WebSocket, desktop frontend 8D 顯示 | ★☆☆ 1 行改動 | 低 |
| E: Facade.update | 所有經由 facade 的更新（ζ 更新送錯給 α） | ★☆☆ 1 行改動 + 補 mapping | 低 |
| F: get_analysis | digital_life_integrator, playground, adapter | ★☆☆ 新增方法 | 低 |
| D: Influence rules | εθζ 不參與跨維度傳播 | ★★☆ 需設計合理映射 | 中 |
| A: compute_coordinate | 座標永不隨 values 更新 | ★★☆ 多處改動 | 中 |
| B: spatial YZ | YZ 永遠停於初始值 | ★★★ 需設計數學策略 | 高 |
| G: 命名 | 文件/除錯混亂 | ★☆☆ 純文字改動 | 低 |

---

## 8. 向下相容性與遷移策略

⚠️ **底層更新會影響整個專案**，以下分析所有外部呼叫者，確保修復不造成連鎖崩潰。

### 8.1 影響總表

| 修復步驟 | 受影響檔案數 | 總呼叫點 | 是否向後相容 | 遷移難度 |
|---------|------------|---------|-------------|---------|
| Step 1: `get_state()` 加回 εθζ | 1（neuro_auto_selector） | 3 runtime + 2 scratch | **否** — 回傳 dict key 增加但 shape 不變，僅新增 key 不走 | 低 |
| Step 2: Facade mapping 補全 | 0 | 無外部呼叫 | **是** — 只影響未來更新路由 | 低 |
| Step 3: `get_analysis()` | 7 個檔案 | 9 個呼叫點 | **否** — 新方法不存在 | 低（新增方法即可） |
| Step 4: INFLUENCE_RULES | 0 | 內部資料 | **是** — 只新增規則，不移除 | 低 |
| Step 5: compute_coordinate() | ≈5 檔案改 update_* | 間接影響所有 coordinate 讀取者 | **中度風險** — coordinates 值會改變，影響 spatial_reasoning 結果 | 中 |
| Step 6: spatial YZ | ≈5 檔案 | 間接影響所有座標運算 | **高風險** — YZ 從固定值變動態值 | 高 |
| Step 7: 類別命名 | 多個 import | 語法層改動 | **否** — 類別名改變 | 低（保留別名） |

### 8.2 每個步驟的完整呼叫者分析

#### Step 1 — `get_state()` 改動

**檔案**: `state_matrix.py:1329-1334`

**現有回傳**: `{alpha, beta, gamma, delta}`（4 維）
**改為**: `{alpha, beta, gamma, delta, epsilon, theta, zeta}`（7 維）

**所有外部呼叫者清單**：

| 呼叫者 | 行號 | 讀取哪些 key | 是否會壞 |
|--------|------|-------------|---------|
| `state_matrix_adapter.py:315` | `return self._sm.get_state(dimension)` | 穿透 | ✅ 安全 |
| `neuro_auto_selector.py:268` | `.get_state("alpha")` | 只查 alpha | ✅ 安全 |
| `neuro_auto_selector.py:295-306` | 讀 `state["epsilon"]`, `state["theta"]`, `state["eta"]` | 預期 εθζeta | 🔴 現在會取不到 |
| `scratch/demo_integrated_autonomy.py:43,63` | `matrix.get_state()` | 未知 | ⚠️ 可能依賴 key 順序 |
| `scratch/test_full_intent_autonomy.py:24` | `summary = matrix.get_state()` | 列印用 | ✅ 安全 |

**neuro_auto_selector.py 特別注意**：
- 第 295 行 `state = self._state_matrix.get_state()` 現在只回傳 4 維
- 第 296-306 行嘗試讀 `state["alpha"]["energy"]`（第 297 行）、`state["epsilon"]`（第 299 行）、`state["theta"]`（第 303-304 行）、`state["eta"]`（第 306 行）
- `state["eta"]` 永遠取不到因為 η 不在 `StateMatrix4D` 中（它在 Adapter 中）
- 修正後 `epsilon` 和 `theta` 變得可讀，但 `eta` 仍然不存在
- **必須另外修改 `StateInterpreter.get_state_dict()`** 使其從 Adapter 或 `export_for_llm()` 讀取 eta，而不是從 `get_state()`
- 安全改法：
  ```python
  state = self._state_matrix.get_state()  # 修復後含 εθζ
  # η 需要從 export_for_llm() 取得
  try:
      full = self._state_matrix.export_for_llm()
      state["eta"] = full.get("eta", {})
  except Exception:
      state["eta"] = {}
  ```

**注意 `get_state(dimension)` 單維度查詢**：
- `get_state("alpha")` 回傳 `{"energy": 0.5, "coordinate": (0,-5,0), ...}` 這種格式
- 這個行為不變，不受影響

#### Step 2 — Facade mapping 補全

**檔案**: `state_matrix_adapter.py:1390-1405`

**現狀**: ζ 的 4 個欄位（temporal_coherence, memory_depth, narrative_flow, identity_continuity）不在 key_map 中，會預設路由到 alpha。
**影響**: 無外部呼叫者直接使用 `facade.update()`（僅有自文件範例）。

#### Step 3 — `get_analysis()` 新增

**檔案**: `state_matrix.py`

**問題**: 此方法不存在，但有 7 個呼叫者會 crash：

| 呼叫者 | 行號 | 崩潰模式 |
|--------|------|---------|
| `state_matrix_adapter.py:318` | `return self._sm.get_analysis()` | AttributeError |
| `state_matrix_adapter.py:613` | `self._sm.get_analysis()` | AttributeError |
| `digital_life_integrator.py:405` | `self.state_matrix.get_analysis()` | AttributeError |
| `digital_life_integrator.py:683` | `self.state_matrix.get_analysis()` | AttributeError |
| `llm_decision_loop.py:233` | `self.state_manager.get_analysis()` | AttributeError |
| `playground.py:70` | `sm._sm.get_analysis()` | AttributeError |
| `state_matrix.py:267` (docstring demo) | `analysis = matrix.get_analysis()` | AttributeError |

預期回傳格式（來自呼叫者的使用模式）：
- `digital_life_integrator.py:406`: `state_analysis.get("meta_state", {}).get("overall_state")`
- `digital_life_integrator.py:684`: `state_analysis.get("allocation", {}).get("overload")`
- `llm_decision_loop.py:234`: `decision = state_analysis.get("decision")`

**實作應回傳**：
```python
{
    "state": self.get_state(),
    "coordinates": self.get_coordinates(),
    "averages": self.get_dimension_averages(),
    "wellbeing": self.compute_wellbeing(),
    "meta_state": {"overall_state": "...", "energy_level": ..., "stable": ...},
    "allocation": {"overload": False, ...},
    "decision": None,
}
```

#### Step 4 — INFLUENCE_RULES 補全

**檔案**: `influence_applicator.py:18-79`

**現狀**:
- `epsilon` 規則 = `{}`（空的）
- `theta` 規則 = `{}`（空的）
- `zeta` 不存在於 `INFLUENCE_RULES` 中

**影響**: `compute_influences()`（`state_matrix.py:1265-1294`）會遍歷影響矩陣並套用規則。當源維度是 ε/θ/ζ 時，`InfluenceApplicator.apply()`（`influence_applicator.py:116-132`）會找不到規則，因此不做任何傳播。

**外部呼叫者**：
| 呼叫者 | 行號 | 使用方式 |
|--------|------|---------|
| `test_audit_comprehensive.py:146` | `influences = sm2.compute_influences()` | 測試用 |
| `test_smoke_real.py:97,246` | `old_influences = sm.compute_influences()` | 測試用 |

無生產環境外部呼叫者直接呼叫 `compute_influences()`。影響在 `compute_influences()` 內部使用，然後透過 `_apply_influence()` → `InfluenceApplicator.apply()` 間接影響維度值。

#### Step 5 — `compute_coordinate()` 復活

**檔案**: `state_matrix.py`

**作法**: 在 7 個 `update_*()` 方法末尾各加一行 `self.{dim}.compute_coordinate()`

**風險**: 
- `compute_coordinate()` 目前是死代碼，加入後座標會開始變化
- 所有讀取 `.coordinate` 的程式碼會看到新值
- `cognitive_operations.py` 的 `perform_spatial_reasoning()`、`apply_intent_gravity()`、`apply_inter_dimensional_drag()` 都會受到影響

**關鍵依賴鏈**：
```
update_alpha(energy=0.8)   [每次 refresh 或事件觸發]
  → compute_coordinate()  [NEW: 座標重新計算]
    → alpha.coordinate 變更
      → compute_spatial_influence_factor() 使用新座標計算距離
      → Live2D 座標映射
      → export_for_llm() 匯出新座標
```

**需特別關注的座標消費者**：

| 程式碼 | 行號 | 讀取方式 |
|--------|------|---------|
| `cognitive_operations.py:67` 的 `perform_spatial_reasoning()` | 讀取 `state.coordinate` 作為操作的起點 | 受影響 |
| `cognitive_operations.py:45` 的 `compute_spatial_influence_factor()` | 計算兩維度座標的距離 | 受影響 |
| `state_matrix.py:1252-1253` 的 `compute_spatial_influence_factor()`（同名不同位置） | 讀取 `source.coordinate` 和 `target.coordinate` | 受影響 |
| `playground.py:30,73,88` | `.alpha.coordinate` 直接讀取 | 受影響 |
| 各種測試檔案的 `assert coord[0] == ...` | 斷言座標值 | 可能失敗 |

**遷移策略**：
1. 先在 `test_*` 環境中加入 `compute_coordinate()` 呼叫，觀察哪些測試斷言失敗
2. 更新測試斷言為新預期值
3. 然後在生產程式碼中加入
4. 公式中 `zeta` 的 key 名稱修正（`memory` → `memory_depth`, `narrative` → `narrative_flow`）需同時處理

#### Step 6 — `perform_spatial_reasoning()` 加入 YZ 修改

**檔案**: `cognitive_operations.py:56-83`

**最高風險步驟**。因為 YZ 從永遠不變改為動態值，會影響：
- 所有 `perform_spatial_reasoning()` 的外部呼叫者
- 所有依賴 `.coordinate[1]` 和 `.coordinate[2]` 的程式碼
- `compute_influences()` 的距離計算
- `get_dimension_value()`（回傳 `coordinate[0]`）— 這個不受影響

**外部呼叫者**：

| 呼叫者 | 行號 | 操作 | 風險 |
|--------|------|------|------|
| `state_matrix.py:1353-1356` | `self._psr(self.dimensions, "beta", CognitiveOp.ACCUMULATE, 0.1)` | 實際生產呼叫 | 高 |
| `cognitive_operations.py:116` | `execute_thought_chain()` 內部迴圈 | 間接 | 高 |
| `cognitive_operations.py:180` | `evaluate_math_spatially()` 對 epsilon 操作 | 高 |
| `test_cognitive_operations.py` 多處 | 座標斷言測試 | 中（測試會壞但可修） |

**遷移策略**：
1. 引入 `spatial_ratio` 配置（每維度可配置 XYZ 敏感度）
2. 預設 Y/Z 係數為 0.3/0.1（比 X 小，確保 X 仍是主軸）
3. 先更新測試檔案的期望值
4. 分批上線 — 先 α/β 加入 YZ，觀察影響，再逐步推廣到其他維度

### 8.3 測試檔案更新清單

| 測試檔案 | 可能受影響的測試 | 原因 |
|---------|---------------|------|
| `tests/refactor/test_smoke_real.py` | `test_dimensional_coordinates` | `get_state()` 回傳更多 key + coordinates 改變 |
| `tests/refactor/test_audit_comprehensive.py` | 多個 `update_*` + `compute_influences` 測試 | coordinates 改變影響距離計算 |
| `tests/refactor/test_phase7.py` | `update_*` 系列測試 | 同上有影響 |
| `tests/refactor/test_state_matrix_integrations.py` | `update_gamma` 測試 | 同上 |
| `tests/refactor/test_state_matrix_api.py` | `update_alpha` 等 | 同上 |
| `tests/ai/response/test_neuro_auto_selector.py` | `StateInterpreter` 測試 | `get_state_dict()` 預期 values 變 |
| `tests/core/test_cognitive_operations.py` | 所有座標斷言 | Step 6 的 YZ 變更 |

### 8.4 分批上線策略

```
第一批（P0，立刻可做）:
  • Step 3: get_analysis() — 純新增，無侵入
  • Step 1: get_state() 加 εθζ — 1 行程式碼
  • Step 2: Facade mapping — 純資料

第二批（P1，需更新測試）:
  • Step 4: INFLUENCE_RULES — 純新增資料
  • Step 7: 類別別名

第三批（P1，有中度風險）:
  • Step 5: compute_coordinate() 復活
    - 先修正 zeta 公式 key 名稱
    - 在測試中啟用 → 更新測試
    - 然後在生產環境啟用

第四批（P2，高風險需謹慎）:
  • Step 6: spatial YZ
    - 引入 spatial_ratio 配置
    - 先在測試中啟用
    - α→β→γ 逐步擴展
```

### 8.5 回滾方案

每個步驟獨立可回滾，不互相依賴。核心原則：

1. `get_state()` 回傳較多 key — 只加不減，相容舊呼叫者
2. `get_analysis()` 新增 — 不影響任何現有邏輯
3. `compute_coordinate()` 可透過移除呼叫來回滾
4. `spatial YZ` 可透過設 `spatial_ratio` 為 `(1,0,0)` 回到純 X 模式

---

## 9. 測試策略

| 測試 | 類型 | 驗證點 |
|------|------|--------|
| `test_get_state_returns_all_8_dims` | 單元 | `get_state()` 回傳包含 αβγδεθζ |
| `test_get_state_delta_has_coordinate` | 單元 | 每個維度回傳含 `coordinate` key |
| `test_facade_zeta_routing` | 單元 | `facade.update(temporal_coherence=0.9)` 真的更新 zeta |
| `test_influence_rules_complete` | 靜態 | `INFLUENCE_RULES` 包含 ε、θ、ζ 的條目 |
| `test_compute_coordinate_called_after_update` | 單元 | `update_alpha(energy=0.8)` 後 `alpha.coordinate[0]` 變了 |
| `test_zeta_formula_keys_correct` | 單元 | `compute_coordinate()` 用 `memory_depth` 而非 `memory` |
| `test_spatial_reasoning_yz_changes` | 單元 | `perform_spatial_reasoning(ACCUMULATE)` 後 Y/Z 也變了 |
| `test_spatial_reasoning_x_dominant` | 單元 | X 的變動幅度 ≥ Y ≥ Z（主軸不變） |
| `test_get_analysis_exists` | 單元 | `state_matrix.get_analysis()` 不回拋 AttributeError |
| `test_get_analysis_keys` | 單元 | `get_analysis()` 回傳包含 `state`、`coordinates`、`wellbeing` |
| `test_export_for_llm_vs_get_state` | 整合 | `export_for_llm()` 和 `get_state()` 的維度集合一致 |
| `test_neuro_auto_selector_state_access` | 整合 | `StateInterpreter.get_state_dict()` 能讀到 εθζ 的值 |
| `test_digital_life_integrator_no_crash` | 整合 | `digital_life_integrator.get_analysis()` 不再 AttributeError |
| `test_compute_influences_with_epsilon` | 整合 | epsilon 的變化透過影響矩陣傳播到其他維度 |
