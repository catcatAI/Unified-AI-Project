# Neuro LLM Auto Mode（[auto] 模式規劃）

## 1. 概述

### 目標

為 Angela 新增 `[auto]` LLM 模式作為預設值，讓系統自動分析硬體能力 + 當前系統負載 + 任務複雜度 + 8D 狀態矩陣，即時計算可用時間預算，動態決定：
- 本地還是雲端 LLM
- 哪個模型（參數大小、量化等級）
- 要不要開思考（thinking/reasoning）
- 最大 tokens / temperature 等參數
- 降級路徑與備援策略

### 設計原則

1. **預設為 [auto]** — 所有 LLM 相關配置若未指定，預設走 auto
2. **不破壞現有模式** — manual（指定模型）依然是允許的，auto 只是新增的預設選項
3. **多層預算計算** — 硬體上限 → 系統即時負載 → 任務需求 → 8D 狀態修正
4. **持續學習** — 每次 auto 決策後記錄結果，優化日後的選擇
5. **無 LLM 降級** — 若所有選項不可用，優雅降級到 NeuroBlender

---

## 2. 現有基礎設施盤點

### 2.1 硬體檢測 ✅（已有）

| 檔案 | 內容 |
|------|------|
| `shared/utils/hardware_detector.py` | `SystemHardwareProbe` — CPU/RAM/GPU/VRAM 檢測，`HardwareProfile` dataclass，`_calculate_tier()` 評分，`get_ollama_recommendations()` 建議模型 |
| `apps/backend/src/configs/hardware_profile.json` | 靜態硬體配置檔案 |
| 前端 `hardware-detection.js` | WebGL GPU 檢測、RAM 估算、`getRecommendedMode()` |

### 2.2 LLM 後端 ✅（已有）

| 後端 | 檔案 | 類型 |
|------|------|------|
| LlamaCppBackend | `angela_llm_service.py` ~line 160 | 本地 llama.cpp |
| OllamaBackend | `angela_llm_service.py` ~line 240 | 本地 Ollama API |
| OpenAIAPIBackend | `angela_llm_service.py` ~line 320 | 雲端 OpenAI |
| AnthropicAPIBackend | `angela_llm_service.py` ~line 400 | 雲端 Anthropic |

### 2.3 路由策略 ✅（已有）

| 檔案 | 內容 |
|------|------|
| `config/llm_providers.yaml` | Provider 定義、路由策略（意圖→模型）、降級鏈、效能追蹤 |
| `ai/language_models/router.py` | `PolicyRouter` 按能力評分排序 |
| `config_loader.py` | `get_best_route()` 傳回最低延遲成功路由 |

### 2.4 資源感知 ⚠️（骨架）

| 檔案 | 狀態 |
|------|------|
| `services/resource_awareness_service.py` | 骨架（156 行），有 `get_realtime_metrics()`、`is_system_stressed()`、`get_throttling_factor()`，但**未與 LLM 選擇整合** |

### 2.5 狀態矩陣 ✅（已有）

| 維度 | 對 auto 的影響 |
|------|---------------|
| α (alpha.energy) | 能量低 → 降低 timeout、選輕量模型、不開思考 |
| β (beta.coherence) | 低 coherence → 需要更高品質 model 來維持連貫 |
| γ (gamma) | 不用於 LLM 選擇 |
| δ (delta.happiness) | 高快樂 → 可考慮較長的詩意回應 |
| ε (epsilon.precision) | 高 precision → 強制用高精度模型（如 deepseek-r1） |
| ζ (zeta) | 暫未涉及 |
| θ (theta) | 高 novelty/negativity → 需要更多思考深度 |
| η (eta) | 活躍模組數量、成功率 → 影響並發限制 |

---

## 3. 架構設計

### 3.1 新增元件

```
┌──────────────────────────────────────────────────────┐
│                  NeuroAutoSelector                    │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ HardwareAnalyzer │  │ BudgetScheduler │  │ ModelDecider │ │
│  └─────────────┘  └──────────────┘  └────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ StateInterpreter│  │ LearnRecorder │  │ FallbackGuard│  │
│  └─────────────┘  └──────────────┘  └────────────┘  │
└──────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────┐
│              AngelaLLMService                         │
│  → initialize() uses NeuroAutoSelector instead of     │
│    hardcoded priority list                            │
│  → generate_with_llm() adjusts params on-the-fly      │
└──────────────────────────────────────────────────────┘
```

### 3.2 `NeuroAutoSelector` 類別

位置：`apps/backend/src/ai/response/neuro_auto_selector.py`

```python
class AutoModeConfig(TypedDict):
    enabled: bool              # 是否啟用 auto
    default_if_unknown: str    # 無法判斷時的 fallback（如 "ollama:phi:latest"）
    min_time_budget_ms: int    # 最小時間預算（低於此直接用 NeuroBlender）
    max_time_budget_ms: int    # 最大時間預算
    thinking_budget_ratio: float  # 思考模式額外預算比率

class NeuroAutoSelector:
    """
    [auto] 模式的決策核心。
    按階段執行：
    Phase 1 — 硬體能力分數 (0-100)
    Phase 2 — 系統即時負載 → 可用預算
    Phase 3 — 任務複雜度 → 需求預算
    Phase 4 — 8D 狀態修正
    Phase 5 — 模型選擇
    Phase 6 — 決策記錄與學習
    """
```

---

## 4. 階段流程

### Phase 1 — 硬體能力分數

**輸入**：`SystemHardwareProbe.detect()` → `HardwareProfile`

**計算**：

```python
def _calc_hardware_score(self, profile: HardwareProfile) -> float:
    """
    0-100 分，越高代表越強。
    """
    # 本地模型分數
    local = (
        profile.ram_total_gb * 0.4 +          # RAM: 32GB → 12.8
        (profile.vram_mb / 1024) * 0.6 +       # VRAM: 8GB → 4.8
        profile.cpu_cores_logical * 0.3 +      # 核心: 16 → 4.8
        (50 if profile.accelerator_type in
            (AcceleratorType.NVIDIA, AcceleratorType.AMD) else 0)  # GPU bonus
    )
    return min(local, 100.0)
```

**結果產出**：
- `hardware_tier`: `extreme` (≥80) / `high` (≥60) / `medium` (≥40) / `low` (<40)
- `local_model_capable`: bool（有 GPU 且 VRAM ≥4GB）
- `recommended_local_model`: 從 `get_ollama_recommendations()` 或硬編碼表
- `cloud_latency_base`: 雲端 API 預估基礎延遲

### Phase 2 — 系統即時負載 → 可用預算

**輸入**：`ResourceAwarenessService.get_realtime_metrics()`

**計算**：

```python
def _calc_time_budget(self, hw_score: float) -> int:
    """
    傳回可用時間預算（毫秒）。
    """
    raw_ms = HW_TIME_BUDGET_TABLE.get(self.hardware_tier, 30000)  # 預設 30s
    
    # 系統負載縮放
    load_factor = self.resource_service.get_throttling_factor()  # 0.5-1.0
    budget = raw_ms * load_factor
    
    # 8D 能量修正
    energy = self._get_alpha_energy()
    if energy < 0.3:
        budget *= 0.6        # 低能量，縮短等待
    elif energy > 0.7:
        budget *= 1.1        # 高能量，多給點時間
    
    return int(budget)
```

**時間預算表**（可配置於 `angela_core.yaml`）：

| 硬體等級 | 基礎預算 | 說明 |
|----------|---------|------|
| extreme  | 60000ms | 高階 GPU，本地推理 |
| high     | 30000ms | 中階 GPU / 純 CPU AVX512 |
| medium   | 20000ms | 一般 CPU / 無 GPU |
| low      | 10000ms | 低配備 / 樹莓派等 |
| critical | 3000ms  | 系統壓力大，直接 NeuroBlender |

### Phase 3 — 任務複雜度 → 需求預算

**輸入**：`context` 中的 `complexity`、`intent`、`user_message`

**計算**：

```python
def _estimate_task_cost(self, context: Dict) -> TaskBudget:
    """
    分析任務所需的計算資源。
    """
    intent = context.get("intent", "general")
    complexity = context.get("complexity", 0.5)
    
    # 意圖基礎成本
    intent_cost = INTENT_COST_MAP.get(intent, COST_GENERAL)
    # 0.0-1.0: math > code > reasoning > general > smalltalk
    
    # 文字長度成本
    msg_len_cost = min(len(context.get("user_message", "")) / 2000, 1.0) * 0.2
    
    # 總需求分數 (0.0-1.0)
    demand = min(intent_cost + msg_len_cost, 1.0)
    
    return TaskBudget(
        demand_score=demand,
        needs_reasoning=demand > 0.6,        # 高需求 → 需要 thinking
        min_quality=intent_cost > 0.4,        # 高品質要求
        preferred_context_window=8192 if demand > 0.7 else 4096,
    )
```

**INTENT_COST_MAP**（可配置於 `angela_core.yaml` 新增 `auto_mode.intent_cost`）：

| 意圖 | 成本 | 原因 |
|------|------|------|
| math | 0.9 | 需要推理與計算 |
| code | 0.8 | 需要上下文理解 |
| task | 0.7 | 需規劃與記憶 |
| reasoning | 0.6 | 需邏輯推理 |
| general | 0.4 | 一般對話 |
| smalltalk | 0.2 | 簡單回應 |
| emotion | 0.3 | 情感回應 |

### Phase 4 — 8D 狀態修正

**輸入**：`state_matrix.py` 的 `export_for_llm()` + 當前軸值

**應用**：

```python
def _apply_state_correction(
    self, budget: int, task: TaskBudget, state: Dict[str, float]
) -> AutoDecision:
    """
    8D 狀態矩陣修正決策。
    """
    decision = AutoDecision(
        time_budget=budget,
        use_thinking=task.needs_reasoning,
        model_size="auto",
        backend="auto",
        temperature=0.7,
        max_tokens=512,
    )
    
    # ε.precision 高 → 強制用精確模型
    if state.get("epsilon_precision", 0.5) > 0.7:
        decision.use_thinking = True
        decision.temperature = 0.3
        
    # δ.happiness 低 → 縮短、安撫導向
    if state.get("delta_happiness", 0.5) < 0.35:
        decision.max_tokens = 256
        decision.temperature = 0.8  # 多樣化安慰
        decision.tone = "gentle"
    
    # α.energy 低 → 降低資源消耗
    if state.get("alpha_energy", 0.5) < 0.3:
        decision.time_budget = min(budget, 10000)
        decision.model_size = "small"
        decision.use_thinking = False
    
    # θ.novelty 高 → 考慮雲端強模型
    if state.get("theta_novelty", 0.3) > 0.7:
        if self.cloud_available:
            decision.backend = "cloud"
            decision.model_size = "large"
            decision.max_tokens = 1024
    
    return decision
```

### Phase 5 — 模型選擇

綜合以上所有因素，執行最終的模型選擇：

```python
async def decide(self, context: Dict) -> AutoResult:
    # Phase 1-2: 硬體 + 系統負載 → 時間預算
    hw_profile = self.hardware_probe.detect()
    hw_score = self._calc_hardware_score(hw_profile)
    budget = self._calc_time_budget(hw_score)
    
    # Phase 3: 任務需求
    task = self._estimate_task_cost(context)
    
    # Phase 4: 狀態修正
    state = self._get_current_state()
    decision = self._apply_state_correction(budget, task, state)
    
    # 低預算短路 → NeuroBlender
    if decision.time_budget < 5000:
        return AutoResult(
            backend="neuroblender",
            model="",
            params={},
            reason=f"Time budget too low ({decision.time_budget}ms)",
        )
    
    # 選擇後端
    backend, model = await self._select_backend(
        time_budget=decision.time_budget,
        task_need=task,
        state=decision,
    )
    
    # 選擇思考模型
    if decision.use_thinking and "deepseek" in model.lower():
        pass  # 保持 reasoning 模型
    elif decision.use_thinking:
        model = self._find_thinking_model(backend)
    
    # 調整參數
    params = self._build_params(decision, model)
    
    return AutoResult(
        backend=backend,
        model=model,
        params=params,
        reason=self._summarize_decision(hw_score, task, state),
    )
```

### Phase 6 — 決策記錄與學習

每次 auto 決策後記錄到 `learned_routes.yaml`：

```yaml
# auto/ learned from NeuroAutoSelector
auto_decisions:
  - timestamp: 2026-05-19T12:00:00
    hw_score: 62.5
    system_load: 0.35
    intent: "general"
    decision:
      backend: "ollama"
      model: "phi:latest"
      thinking: false
      budget_ms: 30000
      actual_ms: 12000
      success: true
```

`LearnRecorder` 會：
- 每 100 筆記錄自動統計各配置的成功率/延遲
- 失敗率高的組合自動降低優先權
- 成功率高且延遲低的組合獲得加分

---

## 5. 與現有系統整合

### 5.1 `AngelaLLMService.initialize()` 修改

```python
async def initialize(self) -> bool:
    if self.llm_mode == "auto":
        # [auto] 模式：使用 NeuroAutoSelector 選擇初始後端
        self.auto_selector = NeuroAutoSelector(...)
        result = await self.auto_selector.decide(context={})
        if result.backend == "neuroblender":
            self.is_available = False
            return False
        self.active_backend = self.backends[result.backend]
        self.active_model = result.model
        self.is_available = True
    else:
        # 現有邏輯：優先順序清單
        ...
```

### 5.2 `_generate_with_llm()` 動態調整

每次 LLM 調用前，重新評估當前的時間預算：

```python
async def _generate_with_llm(self, user_message, context):
    if self.llm_mode == "auto":
        # 重新評估當前狀態
        result = await self.auto_selector.decide(context)
        
        # 如果預算不足，降級
        if result.backend == "neuroblender":
            return await self._fallback_response(user_message, context)
        
        # 如果需要切換後端
        if result.backend != self.active_backend_type:
            self.active_backend = self.backends[result.backend]
            self.active_backend_type = result.backend
        
        # 使用動態 timeout
        timeout = result.params["timeout_ms"] / 1000.0
    else:
        timeout = 30.0  # 現有固定超時
    
    # 繼續現有邏輯...
```

### 5.3 `ResourceAwarenessService` 強化

現有骨架需補實：

```python
class ResourceAwarenessService:
    def get_throttling_factor(self) -> float:
        # 現有：固定 0.5/1.0
        # 改為：連續縮放
        if not self.psutil:
            return 1.0
        cpu = self.psutil.cpu_percent(interval=0.1) / 100.0
        mem = self.psutil.virtual_memory().percent / 100.0
        # 綜合負載因子：0.2 (輕載) ~ 1.0 (滿載)
        return min(cpu * 0.6 + mem * 0.4, 1.0)
    
    def get_available_ram_mb(self) -> float:
        """傳回可用 RAM（MB）"""
        if not self.psutil:
            return 512.0
        return self.psutil.virtual_memory().available / (1024 * 1024)
```

### 5.4 Config 新增

在 `angela_core.yaml` 新增 `auto_mode` 區段：

```yaml
auto_mode:
  enabled: true
  default_if_unknown: "ollama:phi:latest"
  min_time_budget_ms: 5000
  max_time_budget_ms: 60000
  
  intent_cost:
    math: 0.9
    code: 0.8
    task: 0.7
    reasoning: 0.6
    general: 0.4
    smalltalk: 0.2
    emotion: 0.3
  
  time_budget_table:
    extreme: 60000
    high: 30000
    medium: 20000
    low: 10000
    critical: 3000
  
  local_model_ram_thresholds:
    - min_ram_gb: 16
      min_vram_gb: 8
      recommend: "deepseek-r1:latest"
    - min_ram_gb: 8
      min_vram_gb: 4
      recommend: "qwen2.5-coder:latest"
    - min_ram_gb: 4
      min_vram_gb: 0
      recommend: "phi:latest"
  
  cloud_providers_priority:
    - "openai"
    - "anthropic"
    - "google"
```

---

## 6. 邊界情況處理

| 情況 | 處理方式 |
|------|---------|
| 無網路 | `cloud backends` 自動排除，只用本地 |
| 無 GPU | `vram_mb=0` → 只推薦 phi/lite，禁用思考模式 |
| CPU 100% | `get_throttling_factor()` < 0.3 → 直接 NeuroBlender |
| RAM < 1GB | 無法載入 8B+ 模型 → 只推 1B-3B |
| 用戶指定 model | `llm_mode != auto` → 跳過 auto，使用用戶設定 |
| 首次啟動（無學習數據） | 使用 `default_if_unknown` + 硬體推薦 |
| 學習數據足夠 | 根據歷史成功率 + 延遲做加權 |
| energy=0 | 直接 NeuroBlender，不嘗試 LLM |
| multi-turn 對話 | 複雜度疊加累積，隨回合數遞增 |
| 流式 streaming | auto 模式支持 streaming，但需在預算內決定 chunk 大小 |

---

## 7. 實現階段

### Phase A — 基礎結構
- [x] 創建 `NeuroAutoSelector` 類別骨架
- [x] 實現 `HardwareAnalyzer`（包裝 `SystemHardwareProbe`）
- [x] 實現 `BudgetScheduler`（硬體分數 → 時間預算）
- [x] 單元測試：硬體分數計算、各 tier 預算

### Phase B — 任務分析 + 8D 整合
- [x] 實現 `_estimate_task_cost()`
- [x] 實現 `_apply_state_correction()`（讀取 state_matrix）
- [x] 單元測試：意圖分級、各種 state 組合的修正結果

### Phase C — 模型選擇核心
- [x] 實現 `_select_backend()`（本地 vs 雲端權衡）
- [x] 實現 `_build_params()`（temperature / max_tokens / context_window）
- [x] 學習紀錄 `LearnRecorder`
- [x] 單元測試：各種硬體+意圖組合的選擇

### Phase D — 整合到 `AngelaLLMService`
- [x] `initialize()` 新增 auto 模式分支
- [x] `_generate_with_llm()` 動態超時與後端切換
- [x] `ResourceAwarenessService` 強化補實（連續縮放、available_ram_mb、cpu_count）
- [ ] 整合測試：auto 模式完整流程 (pending — 需 mocking LLM backends)

### Phase E — 配置 + 文檔
- [x] `angela_core.yaml` 新增 `auto_mode` 區段
- [x] 此份計劃文檔最終化
- [ ] 更新 `API_ENDPOINTS.md`（如有新 API）
- [ ] 更新 `README.md` v6.4.0 特性

---

## 8. 成功指標

| 指標 | 目標 |
|------|------|
| auto 模式決策延遲 | < 50ms（不含 LLM 推理） |
| 正確選擇率 | ≥ 90%（與 manual 指定相比不差） |
| 降級時機準確率 | ≥ 95%（不應降級時不降級） |
| 學習收斂時間 | ≤ 200 次請求 |
| NeuroBlender 降級率 | ≤ 5%（真正無資源可用時） |
| 用戶感知延遲 | 不高於 manual 模式平均值 ± 20% |

---

## 9. 相關檔案

| 檔案 | 用途 |
|------|------|
| `ai/response/neuro_auto_selector.py` | **（新建）** Auto 模式決策核心 |
| `services/angela_llm_service.py` | 整合 auto 模式初始化與動態切換 |
| `services/resource_awareness_service.py` | 強化即時系統負載偵測 |
| `shared/utils/hardware_detector.py` | 硬體能力偵測（已有） |
| `config/angela_core.yaml` | 新增 `auto_mode` 配置區段 |
| `config/llm_providers.yaml` | Provider/模型定義（已有） |
| `core/config_loader.py` | `get_best_route()` / 學習系統（已有） |
| `ai/language_models/router.py` | `PolicyRouter` 評分（可選整合） |
| `tests/ai/response/test_neuro_auto_selector.py` | **（新建）** 測試 |
