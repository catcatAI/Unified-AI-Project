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
| **Phase 10: Quality Audit** | 審計核心/AI 15 files (浮點數/時區/mock 斷言), Services/API 24 files (70 WEAK→STRONG), SMOKE→REAL 升級 8 subdirs (7→50 tests) | ✅ **All upgraded** |
| **Phase 11: Legacy Migration** | 40 個 root-level 測試搬遷至正確層級 (services 6, core 22, ai 5, ai/memory 3, ai/agents 2, shared 2) + import path 修復 | ✅ **40 files** |
| **Phase 12: Subdirectory Cleanup** | 刪除 6 個 legacy stub 目錄、合併 agents/ → ai/agents/、刪除 integrations/、清除 8 hsp stubs、搬遷 62 utility scripts → scripts/ | ✅ **Complete** |
| **Architecture audit** | 0 層級違規 (架構隔離正確執行) | ✅ |
| **Bug fix audit** | EmotionalState 隱藏 bug 已修復 (缺少 2 個必要欄位) | ✅ |
| **CI Integration** | `.github/workflows/ci.yml` 已更新 (py3.11/3.14, 含新測項) | ✅ |
| **Totals** | **~1200+ tests** across 30+ directories | ✅ |

### 當前測試目錄結構 (Phase 12 清理後)

```
tests/
├── core/              ← ~114 tests ✅
├── ai/
│   ├── agents/       ← 71 tests ✅ (含 6 merged from tests/agents/)
│   ├── memory/       ← 87 tests ✅ (含 3 legacy moved)
│   ├── alignment/    ← 63 tests ✅
│   ├── dialogue/     ← 90 tests ✅
│   ├── learning/     ← 71 tests ✅
│   ├── lifecycle/    ← 162 tests ✅
│   ├── context/      ← 104 tests ✅
│   ├── execution/    ← 24 tests ✅
│   ├── ops/          ← 14 tests ✅
│   ├── rag/          ← 8 tests ✅
│   ├── crisis/       ← 19 tests ✅
│   ├── code_understanding/  ← 5 tests ✅
│   ├── compression/         ← 4 tests ✅
│   ├── formula_engine/      ← 8 tests ✅
│   ├── language_models/     ← 8 tests ✅
│   ├── lis/                 ← 16 tests ✅
│   ├── meta_formulas/       ← 4 tests ✅
│   ├── personality/         ← 6 tests ✅
│   └── service_discovery/   ← 9 tests ✅
├── services/          ← ~101 tests ✅
├── api/               ← ~43 tests ✅
├── shared/            ← ~6 tests ✅
├── integration/       ← 13 tests ✅
├── models/            ← 35 tests ✅
├── scripts/           ← 62 utility scripts (非 pytest)
├── hsp/               ← 10 files (3 real + mocks)
├── fragmenta/         ← 1 test (keep)
├── game/              ← 3 tests (keep)
├── modules_fragmenta/ ← 4 tests (keep)
├── pet/               ← 17 tests (keep)
├── search/            ← 1 test (keep)
├── training/          ← 1 test (keep)
├── unit/              ← 35 tests (keep)
├── tools/             ← 6 tests (keep)
├── .benchmarks/       ← data dir
├── logs/              ← test artifact dir
├── test_output_data/  ← test artifact dir
├── conftest.py        ← session fixture
└── __init__.py
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

### Phase 12 清理一覽

| 操作 | 數量 | 說明 |
|------|------|------|
| 🗑 刪除 legacy stub 目錄 | 6 dirs | `creation/`, `economy/`, `evaluation/`, `interfaces/`, `meta/`, `security/` |
| 🚚 合併 agents/ → ai/agents/ | 6 files | `test_audio_processing_agent.py`, `test_creative_writing_agent.py`, `test_data_analysis_agent.py`, `test_imports.py`, `test_knowledge_graph_agent.py`, `test_simple.py` |
| 🗑 刪除 agents/ duplicates | 2 files | `test_agent_manager.py`, `test_base_agent.py` (已在 ai/agents/ 有更新版) |
| 🗑 刪除 integrations/ | 6 files | 全部為 stub, 無獨特內容 |
| 🗑 清除 hsp stubs | 8 files | `test_basic.py`, `test_debug.py`, `test_hsp_connector.py`, 等 |
| 🚚 utility scripts → scripts/ | 62 files | runner/verify/check/generate/report scripts |
| 🧹 根目錄剩餘 | 2 files | 僅 `conftest.py` + `__init__.py` |
