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

### Phase 1: Core Layer Tests (Priority: 最高)

#### `tests/core/interfaces/test_service_registry.py`
```python
def test_registry_is_singleton():
    r1 = get_registry()
    r2 = get_registry()
    assert r1 is r2

def test_register_and_resolve():
    reg = get_registry()
    reg.register("test", 42)
    assert reg.resolve("test") == 42
    reg.unregister("test")

def test_register_duplicate_overwrites():
    reg = get_registry()
    reg.register("dup", 1)
    reg.register("dup", 2)
    assert reg.resolve("dup") == 2
```

#### `tests/core/interfaces/test_persistence_protocol.py`
```python
class FakePersistence:
    """Structural subtyping conformance test"""
    async def save_state(self, key, data): ...
    async def load_state(self, key): ...
    async def delete_state(self, key): ...
    async def list_keys(self): ...

def test_persistence_protocol_conformance():
    from core.interfaces.persistence import StatePersistence
    from typing import runtime_checkable
    assert isinstance(FakePersistence(), StatePersistence)
```

#### `tests/core/test_state_matrix_adapter.py`
測試 StateMatrixAdapter 的核心功能（不涉及持久化）：
- `test_update_axis()` — 每個軸更新後值正確
- `test_influence_compute()` — 跨軸影響計算
- `test_temporal_trend()` — 時間序列查詢
- `test_allocation_decide()` — 資源分配決策

#### `tests/core/test_hsp_connector.py`
測試 HSP 連接器：
- `test_connect_disconnect()` — 連線生命週期
- `test_publish_subscribe()` — 發布/訂閱模式

#### `tests/core/managers/test_execution_monitor.py`
- `test_shell_default_false()` — shell 預設為 False
- `test_run_sync_command()` — 同步執行
- `test_run_async_command()` — 非同步執行

---

### Phase 2: Shared Layer Tests

#### `tests/shared/test_security_middleware.py`
```python
def test_middleware_name():
    from shared.security_middleware import SignedCommunicationMiddleware
    assert "Signed" in SignedCommunicationMiddleware.__name__
    assert "Encrypted" not in SignedCommunicationMiddleware.__name__
```

#### `tests/shared/test_standard_imports.py`
```python
def test_module_level_warning_present():
    import shared.standard_imports
    assert "DEAD CODE" in shared.standard_imports.__doc__
```

---

### Phase 3: Services Layer Tests

#### `tests/services/test_wiring.py`
```python
def test_initialize_all_services_exists():
    from services.wiring import initialize_all_services
    assert callable(initialize_all_services)

def test_initialize_with_mock_manager():
    manager = Mock()
    initialize_all_services(manager)
    # 驗證 wiring 正確設定了跨服務依賴
```

#### `tests/services/test_main_api_server_di.py`
- `test_desktop_interaction_depends()` — Depends DI 正確解析
- `test_action_executor_depends()`
- `test_digital_life_depends()`

---

### Phase 4: AI Layer Tests

#### `tests/ai/test_layer_isolation.py`
```python
def test_no_top_level_services_import():
    """驗證 ai/ 層不直接依賴 services/"""
    import ast, os
    ai_dir = "apps/backend/src/ai"
    violations = []
    for root, dirs, files in os.walk(ai_dir):
        for f in files:
            if f.endswith(".py"):
                with open(os.path.join(root, f)) as fh:
                    tree = ast.parse(fh.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom) and node.level == 0:
                            if node.module and node.module.startswith("services"):
                                violations.append((os.path.join(root, f), node.lineno))
    assert len(violations) == 0, f"Ai->services imports found: {violations}"
```

---

### Phase 5: Model Layer Tests

#### `tests/models/test_api_models.py`
```python
def test_chat_message_roundtrip():
    from core.interfaces.protocols import ChatMessage
    msg = ChatMessage(role="user", content="hello")
    d = msg.to_dict()
    msg2 = ChatMessage.from_dict(d)
    assert msg2.role == "user"
    assert msg2.content == "hello"

def test_model_provider_values():
    from core.interfaces.protocols import ModelProvider
    assert ModelProvider.OPENAI.value == "openai"
    assert len(ModelProvider) == 8
```

---

### Phase 6: 移除非 pytest 框架測試

38 個 `unittest.TestCase` 檔案逐步遷移至 pytest。

遷移腳本模板 (`scripts/migrate_unittest_to_pytest.py`)：
```python
# 自動化遷移腳本
# 1. 讀取 unittest.TestCase 檔案
# 2. 將 setUp/tearDown → conftest fixtures
# 3. 將 self.assertEqual → assert
# 4. 將 self.assertRaises → pytest.raises
# 5. 將 @patch → pytest fixture
```

---

### Phase 7: Integration Tests

建立跨層整合測試，驗證架構合約：

```python
# tests/integration/test_core_to_services_contract.py

async def test_state_persistence_across_layers():
    """驗證 core 的 StatePersistence protocol
    可被 services 層的 state_matrix_api 正確實作"""
    from core.interfaces.persistence import StatePersistence
    from services.api.state_matrix_api import state_matrix_persistence
    assert isinstance(state_matrix_persistence, StatePersistence)
```

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
