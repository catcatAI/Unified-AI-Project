# Angela 卡片導入管道與聊天系統整合計畫 v2

> **目標**: ModuleManager 驅動的架構接線 — card pipeline + ChatService + IntentRegistry + LLM 在統一模組系統下協作  
> **基於**: 代碼審計（2026-05-30）+ ModuleManager 設計（`docs/03-technical-architecture/design/MODULE_MANAGER_SYSTEM.md`）  
> **審計**: 25 個問題（6 HIGH）已在設計階段標記，非等到執行才發現  
> **狀態**: 設計階段 — 待 M0 實作後啟動

---

## 目錄

1. [當前狀態分析](#1-當前狀態分析)
2. [問題清單（審計發現）](#2-問題清單審計發現)
3. [ModuleManager 方案](#3-modulemanager-方案)
4. [Phase 0: ModuleManager 核心](#4-phase-0-modulemanager-核心)
5. [Phase 1: card_pipeline module](#5-phase-1-card_pipeline-module)
6. [Phase 2: intent_registry + chat_service modules](#6-phase-2-intent_registry--chat_service-modules)
7. [Phase 3: memory + personality adapters](#7-phase-3-memory--personality-adapters)
8. [Phase 4: LLM + async API](#8-phase-4-llm--async-api)
9. [遷移對照表](#9-遷移對照表)
10. [Appendix: 檔案清單](#10-appendix-檔案清單)

---

## 1. 當前狀態分析

### 1.1 現有組件及其連接狀態

```
  run_card_import.py  (standalone CLI, 不連任何服務)
       │
       ▼
  CardImportPipeline.process()
       │
       ├──► DeterministicParser     (Stage 1: Auto)
       ├──► ConflictDetector         (Stage 1)
       ├──► MergeEngine              (Stage 1)
       ├──► TimelineResolver         (Stage 1)
       ├──► TextGravityField         (Stage 2: Angela)
       ├──► TokenExtractor           (Stage 2)
       └──► LLMFallback              (Stage 3: 硬編碼，非真正LLM)

  ⚠ MemoryAdapter (81行)       → 存在但無人呼叫
  ⚠ PersonalityAdapter (59行)  → RoleplayEngine 已用，但 Pipeline 未接
  ⚠ CardRegistry (203行)      → pipeline + run_card_import 使用
  ⚠ IntentRegistry (168行)    → character_card intent 存在但無 handler
  ⚠ ConfigLoader.learn()      → 從未接收卡片導入質量數據

  ChatService (313行)
       ├──► _analyze_intent()   → 僅 keyword match, 無 card pipeline
       ├──► generate_response() → 走 LLM, 從不調用 CardImportPipeline
       └──► IntentRegistry 從未被 ChatService 使用

  AngelaLLMService / LLM Router (1522行)
       ├──► HAMMemoryManager    → 用於 memory retrieval
       ├──► MemoryAdapter       → 從未傳入 HAMManager
       ├──► TemplateMatcher     → P0-2 模板匹配
       └──► LLMFallback(66行)   → 硬編碼規則，非真正LLM路由
```

### 1.2 精確的斷開點（file:line）

| # | 斷開點 | 位置 | 說明 |
|---|--------|------|------|
| D1 | `MemoryAdapter` 從未實例化 | `memory_adapter.py:21-22` | `__init__` 接收 `ham_manager=None`，但永遠沒人傳入 |
| D2 | `PersonalityAdapter` RoleplayEngine 已用但 Pipeline 未接 | `roleplay_engine.py:22-23` | `RoleplayEngine.__init__` 自動建立 `PersonalityAdapter()` 實例，但 `CardImportPipeline` 完全不使用它 |
| D3 | `CardImportPipeline` 不接收 adapters | `pipeline_orchestrator.py:46-54` | 建構子只接收 `registry`，沒有 memory/personality adapter 掛鉤 |
| D4 | `ChatService._analyze_intent()` 不使用 IntentRegistry | `chat_service.py:155-167` | 硬編碼 keyword match，忽略了 `IntentRegistry` 和 YAML 定義的 `character_card` intent |
| D5 | ChatService 沒有 `character_card` 意圖處理分支 | `chat_service.py:122-127` | 只有 `llm_manage` 和 `file_op` 兩個分支 |
| D6 | `CardRegistry` 未註冊到 ServiceRegistry（但 CLI 有使用） | 全域 | 無任何地方 `get_registry().register("card_registry", ...)` |
| D7 | `LLMFallback` 硬編碼而非使用真實 LLM | `llm_fallback.py:39-63` | 所有 `_resolve_*` 方法都是字串拼接，從未調用 `AngelaLLMService` |
| D8 | `ConfigLoader.learn()` 從未接收卡片數據 | `config_loader.py:285-311` | `learn()` 支援四種事件類型，但無任何代碼從 pipeline 調用它 |
| D9 | `CardImportPipeline` 與 API 完全隔離 | `run_card_import.py:280-281` | CLI-only，無 register/router/hook |
| D10 | `IntentRegistry` 未被 ChatService 使用 | `services/` | grep `IntentRegistry` 在 `services/` → 0 結果 |

---

## 2. 問題清單（審計發現）

### 2.1 HIGH — 必須在 Phase 0 解決

| # | 來源 | 問題 | 階段影響 |
|---|------|------|---------|
| H1 | 0.1 | IntentRegistry 永遠不是 singleton → 學習回饋寫進黑洞 | Phase 1, 3 |
| H2 | 1.1 | Sync `pipeline.process()` 在 async 方法內阻塞 event loop | Phase 1 |
| H3 | 1.2 | 每次訊息 new 一個 IntentRegistry → patterns 永遠不持久 | Phase 1, 3 |
| H4 | 2.1 | `asyncio.get_running_loop()` 在 sync method → CLI 模式直接崩 | Phase 3 |
| H5 | 2.2 | Phase 3 讓 Stage 3 變 async 但沒給 `async process()` | Phase 3 |
| H6 | 3.1 | `text[:50]` 作為 keyword → 學習寫 garbage | Phase 3 |

### 2.2 MEDIUM — Phase 0-4 逐步解決

12 個 MEDIUM 問題：registry 碎片化、CLI 隔離、race condition、HAM 無 config、keyword 誤判、LLMBridge 冗餘、latency 統計損壞、lifespan vs wiring 矛盾、無 auth、zombie task、靜默錯誤。

### 2.3 LOW — 語義問題

7 個 LOW：YAML handler 名、timeout、instance 衝突、orphan stats、無 Pydantic model、無 Phase 0。

---

## 3. ModuleManager 方案

### 3.1 核心思路

不手動接線。每個 component 是一個 **Module**，用 `module.yaml` 宣告依賴和提供。**ModuleManager** 自動 discovery、resolve、wire。

```
Manual wiring (舊方案, 25 issues):         ModuleManager (新方案):
  ChatService                              modules/chat_service/module.yaml
    ├── manually import IntentRegistry       depends_on: { intent_registry }
    ├── manually create CardRegistry         provides: { chat_handler }
    ├── manually wire PersonalityAdapter     lifecycle: { init, start, stop }
    └── manually call ConfigLoader.learn()   hooks: { on_card_imported }
```

### 3.2 解決 HIGH 問題的對應

| HIGH | 舊方案會怎麼做 | ModuleManager 方案 |
|------|--------------|-------------------|
| H1 | 手動寫 singleton pattern | descriptor 宣告 `type: singleton` → 自動 |
| H2 | 手動加 `asyncio.to_thread()` | lifecycle 知道 sync/async boundary |
| H3 | 手動 cache instance | ModuleManager 提供 singleton |
| H4 | 手動判斷 CLI vs API context | lifecycle 提供適合的 context |
| H5 | 手動補 `async def process()` | interface schema 強制 sync/async 一致 |
| H6 | 手動 review | config schema 驗證 → 拒絕 garbage |

### 3.3 與舊方案的差異

| 維度 | v1 (舊) | v2 (新) |
|------|---------|---------|
| 接線方式 | 手動改 5 個檔案 | module.yaml 宣告 |
| Singleton 管理 | 每次猜 | descriptor 宣告 |
| Lifecycle | 散落在 lifespan/wiring/router | 統一到 ModuleManager |
| Health check | 無 | 內建 |
| 新模組成本 | 2-3 天分析斷開點 | 寫一個 module.yaml |
| 審計問題 | 執行才發現 | 設計階段標記 25 個 |

---

## 4. Phase 0: ModuleManager 核心

### 4.1 目標
建立 ModuleManager 基礎設施，不影響任何現有程式碼。

### 4.2 新增檔案

| 檔案 | 說明 |
|------|------|
| `core/system/module_manager/models.py` | ModuleDescriptor, DependencySpec, LifecycleHooks dataclasses |
| `core/system/module_manager/scanner.py` | 掃描 `modules/*/module.yaml`，回傳 descriptor list |
| `core/system/module_manager/resolver.py` | topological sort + cycle detection |
| `core/system/module_manager/lifecycle.py` | init/start/stop orchestration |
| `core/system/module_manager/events.py` | Event bus + health monitor |
| `core/system/module_manager/__init__.py` | ModuleManager facade |
| `modules/.gitkeep` | Module 根目錄 |

### 4.3 不修改
現有檔案（wiring.py, lifespan.py, router.py, ChatService）全部不動。

### 4.4 驗收

```
pytest tests/core/module_manager/  — 50+ tests
  ├── scanner: 解析 module.yaml, schema 驗證
  ├── resolver: topological sort, cycle detection
  ├── lifecycle: init → start → stop 順序正確
  ├── events: event bus 發布/訂閱
  └── integration: ModuleManager.start() 完整流程
```

### 4.5 解決的問題
- H1: ModuleManager 提供 singleton 機制
- H2: Lifecycle 知道 sync/async boundary
- H3: ModuleManager 管理 instance 生命週期
- H4: Lifecycle 提供適合的 asyncio context
- H5: Interface schema 強制 sync/async 一致
- H6: Config schema 驗證

---

## 5. Phase 1: card_pipeline module

### 5.1 目標
CardImportPipeline + CardRegistry 成為第一個 ModuleManager 管理的 module。

### 5.2 新增檔案

```
modules/card_pipeline/
  module.yaml        — descriptor
  __init__.py        — init/start/stop functions
  adapter.py         — MemoryAdapter + PersonalityAdapter factory (via ModuleManager)
```

### 5.3 module.yaml

```yaml
name: card_pipeline
version: 1.0.0
kind: service
depends_on:
  required: []            # Phase 1: 不依賴任何 module，先獨立驗證
  optional:
    - ham_memory          # 非必需，沒有時降級
    - personality_module
    - llm_module          # Stage 3 LLM resolution
    - intent_registry     # Phase 2 加入後自動啟用 intent dispatch
provides:
  services:
    - name: card_import_handler
      type: singleton
lifecycle:
  init: modules.card_pipeline.init
  start: modules.card_pipeline.start
  stop: modules.card_pipeline.stop
  health:
    endpoint: /health/card-pipeline
```

### 5.4 init 函數

```python
async def init(deps: dict) -> CardImportHandler:
    """ModuleManager 在依賴都 ready 後呼叫。"""
    registry = CardRegistry()

    memory_adapter = None
    if "ham_memory" in deps:
        memory_adapter = MemoryAdapter(deps["ham_memory"])

    pipeline = CardImportPipeline(
        registry=registry,
        memory_adapter=memory_adapter,
        llm_service=deps.get("llm_module"),
    )

    return CardImportHandler(pipeline=pipeline, registry=registry)
```

### 5.5 解決的 D-points

| D-point | Before | After |
|---------|--------|-------|
| D1 | MemoryAdapter 從未實例化 | ModuleManager 注入 |
| D3 | Pipeline 不接收 adapters | Pipeline 建構子接收 `memory_adapter=` |
| D6 | CardRegistry 未註冊 | ModuleManager 自動註冊到 ServiceRegistry |
| D7 | LLMFallback 硬編碼 | ModuleManager 提供 `llm_module` |
| D9 | CLI 隔離 | CLI 也可以透過 ModuleManager 啟動 |

---

## 6. Phase 2: intent_registry + chat_service modules

### 6.1 目標
IntentRegistry 成為 singleton module，ChatService 透過 ModuleManager 使用它。

### 6.2 新增檔案

```
modules/intent_registry/
  module.yaml        — descriptor
  __init__.py        — init/start functions
modules/chat_service/
  module.yaml        — descriptor
  __init__.py        — init/start functions
```

### 6.3 intent_registry module.yaml

```yaml
name: intent_registry
version: 1.0.0
kind: service
depends_on:
  optional:
    - card_pipeline     # 當 card_pipeline ready 時，動態註冊 character_card intent
provides:
  services:
    - name: intent_registry
      type: singleton
lifecycle:
  init: modules.intent_registry.init
  hooks:
    on_dependency_ready:
      - event: card_pipeline.ready
        handler: modules.intent_registry.on_card_pipeline_ready
```

### 6.4 chat_service module.yaml

```yaml
name: chat_service
version: 1.0.0
kind: service
depends_on:
  required:
    - intent_registry       # singleton, 不再是每次 new
  optional:
    - card_pipeline         # 當使用者說「導入角色卡」時呼叫
    - llm_module
provides:
  services:
    - name: chat_handler
      type: singleton
lifecycle:
  init: modules.chat_service.init
  health:
    endpoint: /health/chat
```

### 6.5 ChatService 改動

```python
# Before (chat_service.py:155-167, 手動 keyword match)
async def _analyze_intent(self, text: str) -> str:
    text_lower = text.lower()
    if "角色卡" in text_lower or "导入" in text_lower:
        return "character_card"
    ...

# After (透過 ModuleManager 取得 IntentRegistry singleton)
# IntentRegistry.detect() 是 sync method，ModuleManager.call() 自動處理 sync/async
async def _analyze_intent(self, text: str) -> str:
    registry = self._module_manager.get_module("intent_registry")
    # ModuleManager.call() 判斷 detect() 是 sync → 用 to_thread() 或在 event loop 執行
    intent = await self._module_manager.call("intent_registry", "detect", text)
    if intent == "character_card" and self._module_manager.has("card_pipeline"):
        return "character_card"
    return intent
```

### 6.6 ModuleManager 注入方式

ChatService 目前的建構子 `__init__()` 不接收 `module_manager`。改動方式：

**選項 A（推薦，最小改動）**：ChatService 透過 ServiceRegistry 取得 ModuleManager：

```python
# chat_service.py: 在需要時 lazy 取得
from core.interfaces.service_registry import get_registry

class ChatService:
    @property
    def _module_manager(self):
        return get_registry().get("module_manager")
```

**選項 B（當 ChatService 成為 module 後）**：ChatService 改用 ModuleManager init 建立，由 lifecycle 傳入 deps。

Phase 2 先用選項 A，Phase 3 遷移到選項 B。

### 6.7 解決的問題

| 問題 | Before | After |
|------|--------|-------|
| H1/H3 (每次 new IntentRegistry) | `IntentRegistry()` per message | `ModuleManager.get("intent_registry")` singleton |
| D4 (ChatService 不使用 IntentRegistry) | 手動 keyword match | `module_manager.call("intent_registry", "detect", text)` |
| D5 (無 character_card 分支) | 只有 2 個分支 | `detect()` 返回後 dispatch |
| D10 (IntentRegistry 0 引用) | services/ 0 match | ModuleManager 注入 |

---

## 7. Phase 3: memory + personality adapters

### 7.1 目標
MemoryAdapter 和 PersonalityAdapter 透過 ModuleManager 注入 pipeline，解決 sync/async 不一致。

### 7.2 關鍵設計決策

Phase 1 的 `CardImportPipeline.process()` 保持 sync（Stage 1-2 是純 CPU 計算），但透過 ModuleManager 在 async context 中自動 `run_in_thread()`：

```python
# ModuleManager Lifecycle 處理 sync/async boundary
class ModuleLifecycle:
    async def call(self, module_name: str, method: str, *args, **kwargs):
        module = self._manager.get_module(module_name)
        impl = getattr(module.instance, method)

        if asyncio.iscoroutinefunction(impl):
            return await impl(*args, **kwargs)
        else:
            return await asyncio.to_thread(impl, *args, **kwargs)
```

### 7.3 解決的問題

| # | 問題 | 方案 |
|---|------|------|
| H4 | `asyncio.get_running_loop()` 在 sync method | Lifecycle.call() 自動判斷 sync/async |
| H5 | Phase 3 要 async 但沒給 async process() | Interface schema 宣告 sync → 強制一致 |
| D1 | MemoryAdapter 從未實例化 | ModuleManager 注入 |
| D2 | PersonalityAdapter 兩個 instance 衝突 | ModuleManager 提供 singleton |

---

## 8. Phase 4: LLM + async API

### 8.1 目標
- LLM service 成為 module（取代 router.py 的 hotspot 角色）
- Async API endpoint 透過 ModuleManager health 系統管理

### 8.2 module.yaml

```yaml
name: llm_module
version: 1.0.0
kind: service
depends_on:
  optional:
    - ham_memory
    # 注意: card_pipeline 依賴 llm_module (optional)，若 llm_module 也依賴 card_pipeline
    # 則形成 cycle。因此 llm_module 不宣告對 card_pipeline 的依賴。
    # card_pipeline 透過 ModuleManager.get("llm_service") 在執行時取得 LLM 服務，
    # 不需要 llm_module 反過來依賴它。
provides:
  services:
    - name: llm_service
      type: singleton
lifecycle:
  init: modules.llm.init
  start: modules.llm.start
  stop: modules.llm.stop
  health:
    endpoint: /health/llm
    interval: 30s
```

### 8.3 API endpoint 改動

```python
# Before (手動管理 task progress)
@router.post("/cards/import")
async def import_card(text: str = Body(...)):
    task_id = str(uuid4())
    asyncio.create_task(_run_import(text, task_id))
    return {"task_id": task_id}

# After (透過 ModuleManager health + events)
@router.post("/cards/import")
async def import_card(text: str = Body(...)):
    module = app.state.module_manager.get_module("card_pipeline")
    task_id = await module.submit_import(text)  # ModuleManager 管理 lifecycle
    return {"task_id": task_id}
```

### 8.4 解決的問題

| # | 問題 | 方案 |
|---|------|------|
| H6 | `text[:50]` garbage keyword | Pipeline result 提供結構化 keyword |
| D8 | ConfigLoader.learn() 從未接收 | Event hook `on_card_imported` → `learn()` |
| lifecycle 管理 | lifespan.py 與 wiring.py 重複 | 統一到 ModuleManager.start() |
| 無 auth/rate limit | 手動補 | ModuleManager middleware hooks |

---

## 9. 遷移對照表

### 9.1 D-points 解決狀態

| D-point | 斷開點 | Phase | 解決方式 |
|---------|--------|-------|---------|
| D1 | MemoryAdapter 從未實例化 | 1+3 | ModuleManager 注入 |
| D2 | PersonalityAdapter instance 衝突 | 1+3 | ModuleManager singleton |
| D3 | Pipeline 不接收 adapters | 1 | `pipeline(memory_adapter=)` 參數 |
| D4 | ChatService 不使用 IntentRegistry | 2 | ModuleManager.get("intent_registry") |
| D5 | 無 character_card 分支 | 2 | IntentRegistry.detect() dispatch |
| D6 | CardRegistry 未註冊 | 1 | ModuleManager 自動註冊 |
| D7 | LLMFallback 硬編碼 | 4 | ModuleManager.get("llm_service") |
| D8 | ConfigLoader.learn() 未接 | 3+4 | Event hook |
| D9 | CLI 隔離 | 1 | ModuleManager 可 CLI/API 共用 |
| D10 | IntentRegistry 0 引用 | 2 | ModuleManager 注入 |

### 9.2 審計問題解決狀態

| 等級 | 總數 | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|------|------|---------|---------|---------|---------|---------|
| HIGH | 6 | 6 (H1-H6) | - | - | - | - |
| MEDIUM | 12 | 2 | 3 | 3 | 2 | 2 |
| LOW | 7 | 1 | 2 | 1 | 1 | 2 |

---

## 10. Appendix: 檔案清單

### 10.1 Phase 0 — ModuleManager 核心（新增 7 檔案）

| 檔案 | 說明 | 行數估計 |
|------|------|---------|
| `core/system/module_manager/models.py` | 資料類別 | ~80 |
| `core/system/module_manager/scanner.py` | 掃描 + 解析 module.yaml | ~100 |
| `core/system/module_manager/resolver.py` | Topological sort + cycle detection | ~120 |
| `core/system/module_manager/lifecycle.py` | Init/start/stop orchestration | ~150 |
| `core/system/module_manager/events.py` | Event bus + health monitor | ~100 |
| `core/system/module_manager/__init__.py` | ModuleManager facade | ~80 |
| `modules/.gitkeep` | Module 根目錄 | 0 |

### 10.2 Phase 1 — card_pipeline（新增 3 檔案，修改 1）

| 檔案 | 操作 | 說明 |
|------|------|------|
| `modules/card_pipeline/module.yaml` | 新增 | Descriptor |
| `modules/card_pipeline/__init__.py` | 新增 | init/start/stop 實作 |
| `modules/card_pipeline/adapter.py` | 新增 | Adapter factory |
| `core/card/resolver/pipeline_orchestrator.py` | 修改 | 建構子加 `memory_adapter=` 參數 |

### 10.3 Phase 2 — intent_registry + chat_service（新增 4 檔案，修改 2）

| 檔案 | 操作 | 說明 |
|------|------|------|
| `modules/intent_registry/module.yaml` | 新增 | Descriptor |
| `modules/intent_registry/__init__.py` | 新增 | init + on_card_pipeline_ready hook |
| `modules/chat_service/module.yaml` | 新增 | Descriptor |
| `modules/chat_service/__init__.py` | 新增 | init |
| `services/chat_service.py` | 修改 | `_analyze_intent()` 改用 IntentRegistry |
| `wiring.py` | 修改 | 加入 ModuleManager.start() |

### 10.4 Phase 3 — memory + personality（新增 0 檔案，修改 2）

| 檔案 | 操作 | 說明 |
|------|------|------|
| `core/card/resolver/pipeline_orchestrator.py` | 修改 | 加 `async_process()` 方法 |
| `core/system/module_manager/lifecycle.py` | 修改 | 加 `call()` 自動判斷 sync/async |

### 10.5 Phase 4 — LLM + API（新增 2 檔案，修改 3）

| 檔案 | 操作 | 說明 |
|------|------|------|
| `modules/llm/module.yaml` | 新增 | Descriptor |
| `modules/llm/__init__.py` | 新增 | init + start |
| `api/v1/endpoints/card_import.py` | 新增 | API endpoint |
| `api/lifespan.py` | 修改 | 簡化為 Manager.start() |
| `services/llm/router.py` | 修改 | 部分 routing 轉給 ModuleManager |
