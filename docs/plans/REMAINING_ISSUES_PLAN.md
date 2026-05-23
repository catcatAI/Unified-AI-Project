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
- `scripts/health_check_service.py:79,85` — 錯誤 import path

---

### 剩餘項目

#### 1.1 `tests/ai/response/test_neuro_auto_selector.py:139`
- **違規**: `@patch("services.resource_awareness_service.ResourceAwarenessService")` 在 ai 層測試中引用 services
- **解法**: 將 `@patch("services.resource_awareness_service.ResourceAwarenessService")` 改為在全域 mock 前直接匯入目標類別，使用 `@patch.object` 或是用 `from unittest.mock import Mock` 建立 mock instance 後注入
  ```python
  from unittest.mock import Mock, patch
  mock_resource = Mock()
  @patch("ai.response.neuro_auto_selector.ResourceAwarenessService", return_value=mock_resource)
  ```
  這樣 ai 層測試只依賴 ai 層內部 api，不依賴 services 層
- **驗證**: flake8 不報錯 + pytest 通過

#### 1.2 `tests/test_memory_enhancement.py:175,277`
- **違規**: `from services.angela_llm_service import LLMResponse` 在 ai.memory 測試中
- **解法**: 改為 `from core.interfaces.protocols import LLMResponse`
- **驗證**: import 成功 + pytest 通過

#### 1.3 `tests/test_angela_core.py`, `tests/test_websocket.py`, 等
- **違規**: 根目錄測試直接 import `services.main_api_server`
- **解法**: 這些測試實測的是 services 層邏輯，應移至 `tests/services/` 目錄。搬移並更新 import path。
- **注意**: 這些檔案多為 async function 內 import，屬於 lazy import，違規程度較低。搬遷優先度 P2。
- **驗證**: pytest 全部通過

---

### 2. 清除 14 個 Placeholder 測試 (P1)

14 個 `tests/test_*.py` 僅含 `self.assertTrue(True)`，無測試價值。

| 檔案 | 建議處理 |
|------|---------|
| `test_coverage_report.py` | 移除 |
| `test_coverage_analyzer.py` | 移除 |
| `test_core_service_manager.py` | 改為 import smoke test |
| `test_content_analyzer.py` | 改為 import smoke test |
| `test_config_loader.py` | 改為 import smoke test |
| `test_core_services_module.py` | 移除 |
| `test_compat_fix.py` | 移除 |
| `test_concept_models_training.py` | 移除 |
| `test_chromadb_fix.py` | 移除 |
| `test_capital_of_debug.py` | 移除 |
| `test_capital_of.py` | 移除 |
| `test_automated_defect_detector.py` | 移除 |
| `test_audio_service_direct.py` | 移除 |
| `test_atlassian_integration.py` | 移除 |

- **驗證**: `pytest tests/` 通過，移除以不報錯
- **執行**: 批次移除（寫 script 確認後執行）

---

### 3. 修復 Broken Test: `test_tool_call_chain.py` (P1)

- **問題**: 使用 `Mock`, `ContextManager`, `ToolCallChainTracker`, `ToolCallChainContext` 但完全沒有 import
- **解法**: 根據語意補上 import 或改為有效的 import smoke test
  ```python
  from unittest.mock import Mock, MagicMock
  from core.managers.tool_context_manager import ToolContextManager
  ```
- **驗證**: pytest 通過

---

### 4. 未實作的 14 個 stub（已轉換但指向不存在 module）(P2)

- 已轉換為 import test，但 `test_defect_detector`、`test_llm_timeout` 指向不存在的 module
- **解法**: 移除這 2 個檔案

---

### 5. Integration conftest 驗證 (P2)

- conftest mock path 已修正，但 fixture 未被任何 test 調用
- **解法**: 檢查是否有測試使用這些 fixture。如無，標記為待清理

---

### 6. ServiceRegistry Unit Test (P2)

```python
# tests/core/test_service_registry.py
def test_registry_singleton():
    from core.interfaces.service_registry import get_registry
    r1 = get_registry()
    r2 = get_registry()
    assert r1 is r2

def test_register_and_resolve():
    reg = get_registry()
    reg.register("test_svc", 42)
    assert reg.resolve("test_svc") == 42
```
- **驗證**: pytest 通過

---

### 7. 38 個 unittest.TestCase 遷移至 pytest (P2)

這是大工程，建議漸進式遷移：

| 階段 | 內容 | 檔案數 |
|------|------|--------|
| Phase 1 | Placeholder 移除 | 14 |
| Phase 2 | Broken test 修復 | 1 |
| Phase 3 | Import-only tests 遷移 | 8 |
| Phase 4 | Mock-heavy tests 遷移 | 6 |
| Phase 5 | 剩餘真實 tests 遷移 | 9 |

遷移模式：
```python
# Before (unittest)
class TestFoo(unittest.TestCase):
    def test_bar(self):
        self.assertEqual(foo(), 42)

# After (pytest)
def test_bar():
    assert foo() == 42
```

---

### 8. 架構層級測試目錄清理 (P2)

確保所有測試檔案放在正確的層級目錄：

```
tests/
├── core/          ← core/ 的測試
├── ai/            ← ai/ 的測試（不可 import services/）
├── services/      ← services/ 的測試
├── api/           ← api/ 的測試
├── shared/        ← shared/ 的測試
├── models/        ← 需要建立，放 models/ 的測試
└── integration/   ← 跨層整合測試
```

搬遷原則：
- `tests/test_angela_core.py` → `tests/services/` (因為測試的是 services.main_api_server)
- `tests/test_websocket.py` → `tests/services/`
- `tests/test_connection_session.py` → `tests/services/`
- `tests/test_security.py` → `tests/shared/`
- `tests/test_math_tool.py` → `tests/core/`
- `tests/test_logic_tool.py` → `tests/core/`

---

### 執行順序

```
Phase 1: P1 修復 (架構違規 + broken test + placeholder 移除)
Phase 2: P2 ServiceRegistry test + 目錄清理
Phase 3: P2 遷移 unittest.TestCase → pytest
Phase 4: 驗證全測試套件通過
```

### 驗證標準

1. 所有測試架構違規歸零
2. 無 broken test
3. 無 placeholder test
4. ServiceRegistry 有 unit test
5. `pytest tests/` 無 failure（torch-bound tests 可 skip）
6. flake8 on tests/ 無新增錯誤
