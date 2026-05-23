# 遺留問題解決計畫
## Plan A: Remaining Issues Resolution

### 目標
在維持架構一致性的前提下，解決所有已知的非功能性問題。

---

### ✅ 已完成

#### 1.1 `tests/ai/response/test_neuro_auto_selector.py:139`
- **狀態**: **✅ 已完成** — `@patch("services.resource_awareness_service.ResourceAwarenessService")` 已移除，改為全域 sys.modules mock + 注入
- **驗證**: pytest 通過

#### 1.2 `tests/test_memory_enhancement.py:175,277`
- **狀態**: **✅ 已完成** — `from services.angela_llm_service import LLMResponse` 已改為 `from core.interfaces.protocols import LLMResponse`
- **驗證**: pytest 通過

#### 1.3 目錄清理
- **狀態**: **✅ 已完成** — `tests/ai/agents/`, `tests/api/`, `tests/ai/memory/`, `tests/ai/alignment/`, `tests/ai/learning/`, `tests/ai/lifecycle/` 均已建立並含測試

#### 2. 清除 Placeholder 測試 (P1)
- **狀態**: **✅ 已完成** — 17 個 placeholder/break 測試已移除或轉換
  - `test_coverage_report.py` → 移除
  - `test_coverage_analyzer.py` → 移除
  - `test_core_service_manager.py` → 轉換為 import smoke test
  - `test_content_analyzer.py` → 轉換為 import smoke test
  - `test_config_loader.py` → 轉換為 import smoke test
  - `test_core_services_module.py` → 移除
  - `test_compat_fix.py` → 移除
  - `test_concept_models_training.py` → 移除
  - `test_chromadb_fix.py` → 移除
  - `test_capital_of_debug.py` → 移除
  - `test_capital_of.py` → 移除
  - `test_automated_defect_detector.py` → 移除
  - `test_audio_service_direct.py` → 移除
  - `test_atlassian_integration.py` → 移除
  - `test_defect_detector.py` → 移除（指向不存在 module）
  - `test_llm_timeout.py` → 移除（指向不存在 module）
  - `test_tool_call_chain.py` → 已修復 import
- **驗證**: pytest 全部通過

#### 3. Broken Test 修復
- **`test_tool_call_chain.py`**: **✅** 已補上 import
- **`test_type_fixes.py::test_health_check_service`**: **✅** 已修復（移除 scripts/ 依賴）
- **`test_real_causal_reasoning_engine.py::test_causal_strength_calculation`**: **✅** 已修復（實作 Pearson correlation，非 hardcoded 0.75）

#### 4. Stub 測試清理
- **狀態**: **✅ 已完成** — 6 個 pre-existing stub 移除（`test_health_ready_endpoints.py`, `test_hot_endpoints.py`, `test_hsp_endpoints.py`, `test_llm_interface.py`, `test_models_endpoints.py`, `test_sandbox_executor.py`）

#### 5. ServiceRegistry Unit Test
- **狀態**: **✅ 已完成** — `tests/core/interfaces/test_service_registry.py` 含 9 個 tests

#### 6. unittest.TestCase 遷移
- **狀態**: **✅ 已完成** — 所有 38 個 unittest.TestCase 檔案已遷移至 pytest 或移除

#### 7. 源碼 Bug 修復
- `real_causal_reasoning_engine.py:80` — hardcoded 0.75 → Pearson correlation
- `alignment_manager.py:389` — `meets` NameError → `meets_thresholds`
- `alignment_manager.py:430` — `emotional_arousal=` → `arousal=`
- `alignment_manager.py:428` — `EmotionalState()` 只傳入 3/5 必填欄位 → 補上 `emotion_intensity` + `secondary_emotions`
- `scripts/health_check_service.py:79,85` — 錯誤 import path

#### 8. 測試目錄清理 (Phase 9)
- 移除 9 個根目錄非測試 script: `test_import.py`, `test_env.py`, `test_path.py`, `test_module.py`, `test_all_fixed_modules.py`, `test_json_fix.py`, `test_modules_with_output.py`, `test_repeat_fix.py`, `test_syntax_fixer.py`
- 移除 5 個 `tests/core_ai/` assert-True stubs: `test_agent_manager.py`, `test_crisis_system.py`, `test_deep_mapper.py`, `test_emotion_system.py`, `test_time_system.py`
- 移除 5 個 `tests/core_ai/` 重疊子目錄 (`context`, `dialogue`, `learning`, `memory`, `rag`)
- 搬遷 8 個 `tests/core_ai/` 獨特子目錄 → `tests/ai/`
- 搬遷 24 個 `tests/refactor/` 檔案 → `tests/core/`
- 修復 `tests/refactor/test_anchor_learning.py:274` indent error
- 移除空目錄 `tests/core_ai/`, `tests/refactor/`

#### 9. 品質審計
- **架構審計**: 所有層級隔離 ✅ 0 違規
- **測試品質審計**: ~28 個純 smoke test 轉換或移除
- **Bug fix 審計**: 發現 EmotionalState 隱藏 bug (3/5 必填欄位) 並修復

---

### 剩餘項目

#### 1. 根目錄 legacy test 尚未搬遷 (P2)
以下檔案仍在 `tests/` 根目錄，未依架構搬遷至正確層級：

| 檔案 | 測試目標 | 目標目錄 | 優先度 |
|------|---------|---------|--------|
| `test_angela_core.py` | `services.main_api_server` | `tests/services/` | P2 |
| `test_websocket.py` | `services.main_api_server` | `tests/services/` | P2 |
| `test_connection_session.py` | `services.connection_session` | `tests/services/` | P2 |
| `test_security.py` | `shared.security` | `tests/shared/` | P2 |
| `test_math_tool.py` | `core.math_tool` | `tests/core/` | P3 |
| `test_logic_tool.py` | `core.logic_tool` | `tests/core/` | P3 |

**注意**: 這些檔案多為 async function 內 import (lazy import)，架構違規程度較低。

#### 2. 新搬遷的 8 個 tests/ai/ 子目錄待升級 (P3)
從 `tests/core_ai/` 搬遷至 `tests/ai/` 的 8 個子目錄目前多為 import smoke test，缺少真實 assertion：

| 目錄 | 測試數 | 目前性質 | 建議升級 |
|------|--------|---------|---------|
| `code_understanding/` | 5 | REAL (LightweightCodeModel) | 已足夠 |
| `compression/` | 4 | REAL (AlphaDeepModel) | 已足夠 |
| `formula_engine/` | 1 | SMOKE | 升級為 REAL |
| `language_models/` | 1 | SMOKE | 升級為 REAL |
| `lis/` | 2 | SMOKE | 升級為 REAL |
| `meta_formulas/` | 1 | SMOKE | 升級為 REAL |
| `personality/` | 2 | SMOKE | 升級為 REAL |
| `service_discovery/` | 1 | SMOKE | 升級為 REAL |

#### 3. `tests/ai/meta/` 零測試 (P3)
`tests/ai/meta/` 目錄目前不存在 — `ai/meta/` 模組無對應測試。

#### 4. `tests/core/` 剩餘 ~50 個 source modules 無測試
- ~50 個 `core/` 模組仍無測試覆蓋
- 同 `TEST_RESTRUCTURE_PLAN.md` 所述

#### 5. Integration conftest 驗證 (P2)
- conftest mock path 已修正，但 fixture 未被任何 test 調用
- 待確認是否保留或清理

#### 6. flake8 on tests/ 尚未啟用於 CI
- `tests/` 目錄尚未納入 flake8 檢查
