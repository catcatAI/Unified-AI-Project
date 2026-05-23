# 測試重構與建立計畫
## Plan B: Test Restructuring & Creation

### 架構原則

測試目錄必須**嚴格鏡像**源碼目錄結構，並遵守相同的層級依賴規則：

```
Source                    Tests
──────                    ─────
core/         →          tests/core/          (不可依賴 services/、api/、ai/)
ai/           →          tests/ai/            (不可依賴 services/)
services/     →          tests/services/      (可依賴 core/、shared/、ai/)
api/          →          tests/api/           (可依賴 services/、core/)
shared/       →          tests/shared/        (不可依賴 core/、services/、ai/)
models/       →          tests/models/        (不可依賴 services/)
integration/  →          tests/integration/   (可跨層，但須註明)
```

### 測試分層策略

每個層級的測試分為三種：

| 層級 | 範圍 | 執行時間 | 覆蓋要求 |
|------|------|---------|---------|
| **Unit** | 單一 class/function | <100ms | 80%+ |
| **Integration** | 跨 2-3 層協作 | <5s | 20%+ |
| **E2E** | 完整 flow | <30s | 5%+ |

### 測試優先級

基於風險評估，補測試的優先順序：

```
Priority 1: core/interfaces/   ← Protocol、ServiceRegistry
Priority 2: core/              ← StateMatrix、HSP、managers
Priority 3: shared/            ← SecurityMiddleware、types
Priority 4: services/          ← wiring、LLM service
Priority 5: ai/                ← agents、memory
Priority 6: api/               ← routes、endpoints
Priority 7: models/            ← Pydantic models
Priority 8: integration/       ← Cross-layer flows
```

---

### ✅ 已完成

| Phase | 內容 | 狀態 |
|-------|------|------|
| **Phase 1: Core** | ServiceRegistry (9 tests)、StatePersistence protocol (7 tests)、StateMatrixAdapter (25 tests)、ExecutionMonitor (9 tests)、EtaAxis (18 tests) | ✅ **68 tests** |
| **Phase 2: Shared** | SecurityMiddleware (4 tests)、StandardImports 驗證、wiring | ✅ **4 tests** |
| **Phase 3: Services** | wiring (4 tests)、main_api_server DI (7 tests)、ChatService (16 tests)、VisionService (17 tests)、AudioService (15 tests)、TactileService (11 tests)、AIEditor (21 tests) | ✅ **95 tests** |
| **Phase 4: AI** | Agents (65 tests)、Memory (84 tests)、Dialogue+Alignment (153 tests)、Learning (71 tests)、Lifecycle (162 tests) | ✅ **535 tests** |
| **Phase 5: API** | Router (14 tests)、Endpoints (24 tests)、HealthCheck (4 tests) | ✅ **42 tests** |
| **Phase 6: Migration** | 38 個 unittest.TestCase 全部遷移至 pytest 或移除 | ✅ |
| **Phase 7: Integration** | Server import (2 tests)、Wiring (4 tests)、Middleware (7 tests) | ✅ **13 tests** |
| **Phase 8: AI Migration** | 從 `tests/core_ai/` 搬遷 8 個獨特模組 (`code_understanding`, `compression`, `formula_engine`, `language_models`, `lis`, `meta_formulas`, `personality`, `service_discovery`) 至 `tests/ai/` | ✅ **~20 tests** |
| **Phase 9: Refactor Migration** | 從 `tests/refactor/` 搬遷 24 個檔案至 `tests/core/` (2 個例外: `code_inspector_integration` → `tests/ai/`, `state_matrix_api` → `tests/api/`) | ✅ **24 files** |
| **Cleanup: Dead files** | 移除 14 個 stub/testless 檔案: 5 個 `core_ai/` assert-True, 9 個根目錄非測試 script | ✅ |
| **Cleanup: Stale duplicates** | 移除 `tests/core_ai/` 中與 `tests/ai/` 重疊的5個子目錄 (`context`, `dialogue`, `learning`, `memory`, `rag`) | ✅ |
| **Architecture audit** | 0 層級違規 (架構隔離正確執行) | ✅ |
| **Bug fix audit** | EmotionalState 隱藏 bug 已修復 (缺少 2 個必要欄位) | ✅ |
| **CI Integration** | `.github/workflows/ci.yml` 已更新 (py3.11/3.14, 含新測項) | ✅ |
| **Totals** | **~1030 tests** across 22 directories | ✅ **All passing** |

### 當前測試目錄結構 (Phase 9 清理後)

```
tests/
├── core/              ← ~92 tests ✅ (含 refactor 搬遷 + 原有)
│   ├── autonomous/   ← 原有 + refactor tests
│   ├── interfaces/   ← ServiceRegistry
│   ├── managers/     ← state managers
│   └── state/        ← state adapters
├── ai/
│   ├── agents/       ← 65 tests ✅
│   ├── memory/       ← 84 tests ✅
│   ├── alignment/    ← 63 tests ✅
│   ├── dialogue/     ← 90 tests ✅
│   ├── learning/     ← 71 tests ✅
│   ├── lifecycle/    ← 162 tests ✅
│   ├── context/      ← 104 tests ✅
│   ├── execution/    ← 24 tests ✅
│   ├── ops/          ← 14 tests ✅
│   ├── rag/          ← 8 tests ✅
│   ├── crisis/       ← 19 tests ✅
│   ├── code_understanding/  ← 5 tests ✅ (從 core_ai 搬遷)
│   ├── compression/         ← 4 tests ✅
│   ├── formula_engine/      ← 1 test  ✅
│   ├── language_models/     ← 1 test  ✅
│   ├── lis/                 ← 2 tests ✅
│   ├── meta_formulas/       ← 1 test  ✅
│   ├── personality/         ← 2 tests ✅
│   └── service_discovery/   ← 1 test  ✅
├── services/          ← 95 tests ✅
├── api/               ← ~43 tests ✅ (含 state_matrix_api 搬遷)
├── shared/            ← 4 tests ✅
├── integration/       ← 13 tests ✅
├── models/            ← 35 tests ✅
├── conftest.py        ← session fixture
```

### 剩餘待補層級

| 待補層級 | 檔案數 | 優先度 | 狀態 |
|---------|--------|--------|------|
| `tests/ai/meta/` | 3 | Low | ❌ 零測試 |
| `tests/core/` (剩餘) | ~50 | Medium | ⏳ 部分完成 |
| `tests/ai/` (新搬遷) | 8 subdirs | Low | ⏳ 僅 import smoke — 需升級為 REAL_TEST |

### 品質審計摘要

Phase 9 完成三項審計：

| 審計 | 結果 | 行動 |
|------|------|------|
| **Architecture**: 層級隔離檢查所有測試 | 0 違規 ✅ | 全部通過 |
| **Quality**: 測試能否發現 bug | 5 個源碼 bug 被發現並修復 ✅ | EmotionalState 隱藏 bug 已修復 |
| **Bug Fix Correctness**: 修復方法是否正確 | 4/5 正確, 第 5 個 (EmotionalState) 發現隱藏 bug | 已補上缺少的 2 個必要欄位 |

發現的隱藏 bug: `alignment_manager.py:428` 的 `EmotionalState()` 呼叫只傳入 3/5 必填欄位。真實 `EmotionalState` dataclass 有 5 個必填欄位 (`primary_emotion`, `emotion_intensity`, `secondary_emotions`, `valence`, `arousal`)，但原始碼只傳了 3 個。若 import 成功 (不走 fallback mock)，執行時會 `TypeError: __init__() missing 2 required positional arguments`。

---

### 測試品質門檻

在 Phase 8 驗收前，測試必須滿足：

| 指標 | 最低門檻 | 目標 |
|------|---------|------|
| 語法正確 | 100% | 100% |
| import 不報錯 | 100% | 100% |
| arch violation | 0 | 0 |
| coverage | >15% | >30% |
| stub files | 0 | 0 |
| unittest.TestCase | <38 | <10 |
| CI pass rate | 95%+ | 99%+ |

---

### 執行時間估計

| Phase | 檔案數 | 估計人時 | 說明 |
|-------|--------|---------|------|
| 1: Core | ~15 | 8h | StateMatrix + HSP + ServiceRegistry |
| 2: Shared | ~5 | 2h | SecurityMiddleware + types |
| 3: Services | ~10 | 6h | wiring + DI + main_api_server |
| 4: AI | ~8 | 4h | isolation check + agents |
| 5: Models | ~3 | 1h | Pydantic roundtrip |
| 6: Migration | ~38 | 12h | unittest→pytest (批次處理) |
| 7: Integration | ~5 | 4h | cross-layer contracts |
| **Total** | **~84** | **~37h** | ~5 工作天 |

### Conftest 分層架構

每個測試目錄層級建置對應的 `conftest.py`，提供該層級的共用 fixture：

```
tests/
├── conftest.py                    ← session scope: project_root, minimal_app
├── core/conftest.py               ← core 層共用 fixture (mock StateMatrix)
├── ai/conftest.py                 ← ai 層共用 fixture (mock LLM, Memory)
├── services/conftest.py           ← services 層共用 fixture (mock FastAPI app)
├── shared/conftest.py             ← shared 層共用 fixture
└── integration/conftest.py        ← 整合測試共用 fixture (跨層 mock)
```

Fixture scope 選用原則：
- `session` — 昂貴資源（DB、LLM client）— 全域一次
- `module` — 中等資源（FastAPI TestClient）— 每 module 一次
- `function` — 輕量 mock — 每次測試

---

### CI Integration

測試必須在 CI 中自動執行：

```yaml
# .github/workflows/test.yml  (待建立)
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: pytest tests/ --cov=apps/backend/src --cov-report=term --cov-report=html -m "not slow and not online"
      - run: flake8 apps/backend/src tests/
```

---

### 驗收標準

1. `pytest tests/` 全部通過（重 torch 的 test 可 skip）
2. 測試覆蓋率 ≥ 15%（Phase 1 完成即可達到）
3. 0 個架構違規 (flake8 on tests/)
4. 0 個 stub/placeholder 測試檔案
5. 每個核心 interface 都有 conformance test
6. ServiceRegistry 有 unit test

### Phase 9 清理一覽

| 操作 | 檔案/目錄數 | 說明 |
|------|------------|------|
| 🗑 移除 root stubs | 9 files | `test_import.py`, `test_env.py`, `test_path.py`, `test_module.py`, `test_all_fixed_modules.py`, `test_json_fix.py`, `test_modules_with_output.py`, `test_repeat_fix.py`, `test_syntax_fixer.py` |
| 🗑 移除 core_ai stubs | 5 files | `test_agent_manager.py`, `test_crisis_system.py`, `test_deep_mapper.py`, `test_emotion_system.py`, `test_time_system.py` |
| 🗑 移除 core_ai duplicate dirs | 5 dirs | `context/`, `dialogue/`, `learning/`, `memory/`, `rag/` (已由 tests/ai/ 全面覆蓋) |
| 🚚 搬遷 core_ai unique dirs → tests/ai/ | 8 dirs | `code_understanding/`, `compression/`, `formula_engine/`, `language_models/`, `lis/`, `meta_formulas/`, `personality/`, `service_discovery/` |
| 🚚 搬遷 refactor/ → tests/core/ | 24 files | 含 `test_anchor_learning.py` (修復 indent) |
| 🚚 例外搬遷 | 2 files | `code_inspector_integration` → `tests/ai/`, `state_matrix_api` → `tests/api/` |
| 🔧 修復 EmotionalState bug | 1 file | 補上缺少的 2 個必填欄位 (`emotion_intensity`, `secondary_emotions`) |
| 🧹 移除空目錄 | 2 dirs | `tests/core_ai/`, `tests/refactor/` |
