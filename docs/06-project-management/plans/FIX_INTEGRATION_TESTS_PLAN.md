# 修復 Integration Tests 方案

## 問題本質

Integration tests 中的 `patch()` 路徑指向從未存在的架構路徑（如 `core.cognition.cognitive_engine`），但**實際功能存在於不同路徑**（如 `core/active_cognition_formula.py`）。

- **92 個錯誤引用**，分布在 5 個 test files
- **24 個可簡單修復**（類存在，路徑不同 — 直接改 patch path）
- **68 個完全不存在**（類從未實現 — 需建立 aliases/stubs 或標記 skip）

---

## Phase 1: 簡單路徑修正 (24 references)

直接更新 patch path 到實際存在的類。

### 1.1 `core.emotional.emotional_blending_system.EmotionalBlendingSystem`
→ `core.bio.emotional_blending.EmotionalBlendingSystem`

受影響檔案：
- `test_performance_benchmarks.py` (lines 262, 565, 685)
- `test_full_system_integration.py` (lines 457, 526)
- `test_error_recovery.py` (line 293)
- `test_end_to_end_scenarios.py` (lines 216, 387)
- `test_digital_life_compliance.py` (line 701)

### 1.2 `core.execution.action_executor.ActionExecutor`
→ `core.engine.action_executor.ActionExecutor`

受影響檔案：
- `test_full_system_integration.py` (lines 182, 287, 633, 792)

### 1.3 `core.execution.action_execution_bridge.ActionExecutionBridge`
→ `core.action_execution_bridge.ActionExecutionBridge`

受影響檔案：
- `test_full_system_integration.py` (lines 672, 802)

### 1.4 `core.execution.feedback_collector.FeedbackCollector`
→ `core.action_execution_bridge.FeedbackCollector`

受影響檔案：
- `test_full_system_integration.py` (lines 751, 820)

### 1.5 `core.biological.endocrine_system.EndocrineSystem`
→ `core.bio.endocrine_system_core.EndocrineSystem`

受影響檔案：
- `test_full_system_integration.py` (lines 411, 518, 563)
- `test_digital_life_compliance.py` (line 296)

### 1.6 `core.system_health.SystemHealth`
→ `core.life.digital_life_integrator.SystemHealth`

受影響檔案：
- `test_error_recovery.py` (lines 734, 843, 903)

### 1.7 `core.feedback.feedback_loop.FeedbackLoop`
→ `core.bio.feedback_loop.FeedbackLoop`

受影響檔案：
- `test_digital_life_compliance.py` (line 827)

---

## Phase 2: 建立核心 aliases (core/__init__.py)

在 `core/__init__.py` 的 `_LAZY_IMPORTS` 中新增條目，讓 `from core import XXX` 能找到實際類。

### 2.1 情感類
```python
"EmotionalBlendingSystem": "core.bio.emotional_blending",
"PADEmotion": "core.bio.emotional_blending",
"BasicEmotion": "core.bio.emotional_blending",
```

### 2.2 生物類
```python
"BiologicalIntegrator": "core.bio.biological_integrator",
"EndocrineSystem": "core.bio.endocrine_system_core",
"HormoneType": "core.bio.endocrine_types",
"NeuroplasticitySystem": "core.bio.neuroplasticity_core",
```

### 2.3 Live2D 類
```python
"Live2DIntegration": "core.engine.live2d_integration",
"Live2DAvatarGenerator": "core.engine.live2d_avatar_generator",
```

### 2.4 Feedback 類
```python
"FeedbackProcessor": "core.feedback_processor",
"FeedbackLoopEngine": "core.feedback_loop_engine",
```

---

## Phase 3: PerceptionEngine 整合類

建立 `core/perception/perception_engine.py` — 整合現有 perception 元件。

### 設計：
```python
class PerceptionEngine:
    """整合視覺、聽覺、觸覺感知的統一引擎。"""
    
    def __init__(self):
        self.visual_sampler = VisualSampler()
        self.auditory_sampler = AuditorySampler()
        self.tactile_sampler = TactileSampler()
        self.attention = AttentionController()
    
    async def process(self, input_data: dict) -> dict:
        """統一的感知處理入口。"""
        # 決定注意力焦點
        focus = self.attention.decide_focus(input_data)
        # 根據焦點選擇感知通道
        if focus.mode == "visual":
            result = await self.visual_sampler.sample(focus.target)
        elif focus.mode == "auditory":
            result = await self.auditory_sampler.sample(focus.target)
        # ...etc
        return {"perceived_data": ..., "confidence": ..., ...}
```

### 需要同時修正：
- `core/perception/__init__.py` 加入 `PerceptionEngine` 導出
- `core/__init__.py` 的 `_LAZY_IMPORTS` 加入 `"PerceptionEngine"`

---

## Phase 4: 處理剩餘 68 個 gap references

這些類在 codebase 中完全不存在。策略：

### 4.1 真的缺失的類 → 建立最小 stub
- `CognitiveEngine` — 包裝 `ActiveCognitionFormula` 的適配器類
- `TactileSystem` — 包裝 `PhysiologicalTactileSystem` 的別名
- `PhysiologicalSystem` — 包裝 `BiologicalIntegrator` 的別名
- `Live2DRenderer` — 包裝 `Live2DAvatarGenerator` 的別名
- `ExpressionController` — 包裝現有 expression 邏輯的適配器

### 4.2 完全不存在也無對應物的類 → skip test
以下類完全不存在且無對應功能：
- `CognitiveEngine` (14 uses) → Create adapter
- `ReflectionEngine` (3 uses) → Create adapter wrapping CyberIdentity._reflection_loop
- `InputMonitor` (2 uses) → Skip tests
- `EventProcessor` (4 uses) → Skip tests  
- `ResponseGenerator` (2 uses) → Skip tests
- `NLG` (3 uses) → Skip tests
- `FeatureManager` (2 uses) → Skip tests
- `FaultIsolation` (1 use) → Skip tests
- `StateManager` (2 uses) → Skip tests
- `StrategyAdjuster` (2 uses) → Skip tests
- `BiorhythmSystem` (1 use) → Skip tests
- `SimpleCognition` (1 use) → Skip tests
- `FallbackPerception` (1 use) → Skip tests
- `StaticFallback` (1 use) → Skip tests
- `LipSyncController` (2 uses) → Skip tests
- `DegradedModeProcessor` (1 use) → Skip tests
- `DegradedModeResponder` (1 use) → Skip tests
- `UserNotifier` (1 use) → Skip tests

### 4.3 更新 test markers
所有 gap tests 加上 `@pytest.mark.skip(reason="module not yet implemented — see FIX_INTEGRATION_TESTS_PLAN.md")`

---

## Phase 5: MD 文檔更新

### 5.1 OVERVIEW.md
- 章節 "Deep Analysis" 中 clarifying: integration tests vs actual code paths
- 新增說明 section 解釋 planned architecture vs actual paths

### 5.2 MASTER_PLAN.md
- 更新 Live2D 完成度 Claim（從 "90% complete" → 明確指出實際路徑）
- 更新 execution/biological/emotional 等 sections 指向正確路徑

### 5.3 SERVICE_CATALOG.md
- 無需變更（它已使用正確路徑）

---

## 執行順序

```
Phase 1 (24 路徑修正) → Phase 2 (aliases) → Phase 3 (PerceptionEngine)
  → Phase 4 (stubs + skip) → Phase 5 (MD update)
```

每個 Phase 完成後執行：
```
python -m pytest tests/integration/ --tb=short -q -x
```

---

## 驗證方式

```bash
# 每次 Phase 後確認 integration tests 狀態
cd D:\Projects\Unified-AI-Project\apps\backend
python -m pytest tests/integration/ --tb=line -q  # 看失敗數是否下降

# 確認不影響 unit/core tests
python -m pytest tests/ tests/core/ --tb=line -q

# 確認不影響 import
python -c "from core.perception.perception_engine import PerceptionEngine"
```
