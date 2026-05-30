# Angela Module Manager System

> **Design Date**: 2026-05-30  
> **Status**: Design Phase  
> **解决的问题**: 耦合集中度 35/100、共享可變狀態 35/100、God module 35/100 — 見 `MODULARITY_ANALYSIS.md`  
> **與 8D Matrix 的關係**: 8D 管理 Angela 的執行時狀態；ModuleManager 管理程式碼的架構接線。兩者互補。

---

## 目錄

1. [問題分析](#1-問題分析)
2. [核心概念](#2-核心概念)
3. [Module Descriptor 格式](#3-module-descriptor-格式)
4. [ModuleManager 架構](#4-modulemanager-架構)
5. [API 設計](#5-api-設計)
6. [與現有基礎設施的整合](#6-與現有基礎設施的整合)
7. [遷移策略](#7-遷移策略)
8. [解決的具體問題](#8-解決的具體問題)
9. [路線圖](#9-路線圖)

---

## 1. 問題分析

### 1.1 三個核心指標

| 指標 | 分數 | 瓶頸 | 根因 |
|------|------|------|------|
| 耦合集中度 | 35/100 | `services/llm/router.py` (1522 行) | 所有模組的手動 import 都集中在 router 和 lifespan |
| 共享可變狀態 | 35/100 | ~14 個 module-level globals | 沒有統一的 lifecycle 管理，被迫用 `_xxx = None` 做 lazy init |
| God module | 35/100 | 9 個檔案 >1000 行 | 模組職責不明確，wiring 邏輯混在業務邏輯中 |

### 1.2 25 個 Plan 問題的根因

ANGELA_CARD_INTEGRATION_PLAN.md 的 audit 發現 25 個問題（6 HIGH）——全部追溯到同一個 root cause：

```
每次接新模組：
  1. 手動猜哪個是 singleton → 可能寫錯
  2. 手動改 router.py / lifespan.py / wiring.py → 3 處不一致
  3. 手動管 lifecycle（init/start/stop） → 同步非同步混雜
  4. 沒有 health check → 壞了不知道
```

---

## 2. 核心概念

### 2.1 什麼是 Module

**Module** 是 Angela 系統中一個自包含的功能單元，具備：

- **自描述**：一個 `module.yaml` 宣告它要做什麼、需要誰、提供什麼
- **自管理**：有自己的 init/start/stop lifecycle
- **可發現**：放在 `modules/` 目錄下，ModuleManager 自動掃描
- **可監控**：提供 health check endpoint

### 2.2 設計原則

| 原則 | 說明 |
|------|------|
| **Declarative over imperative** | 用 YAML 宣告依賴，不要用程式碼手動 import |
| **Incremental migration** | 不一次全改，逐個 hotspot 遷移 |
| **Fail fast** | 啟動時檢查所有依賴，缺了就報錯，不 runtime 崩 |
| **Sync/async aware** | 知道每個 module 是 sync 還是 async，自動提供正確 context |
| **Existing infra first** | 建立在 ServiceRegistry + wiring.py + lifespan.py 之上，不重造輪子 |

---

## 3. Module Descriptor 格式

### 3.1 完整範例

```yaml
# modules/card_pipeline/module.yaml
name: card_pipeline
version: 1.0.0
description: Card import pipeline — deterministic parsing, conflict resolution, LLM bridge
kind: service                     # service | adapter | provider | cli

depends_on:
  required:
    - service_registry
    - intent_registry
    - llm_module
  optional:
    - ham_memory
    - personality_module

provides:
  services:
    - name: card_import_handler
      interface: core.card.protocols.CardImportHandler
      type: singleton              # singleton | factory | transient
  adapters:
    - name: memory_adapter
      interface: core.card.protocols.MemoryAdapter
    - name: personality_adapter
      interface: core.card.protocols.PersonalityAdapter

lifecycle:
  init: modules.card_pipeline.init
  start: modules.card_pipeline.start
  stop: modules.card_pipeline.stop

  health:
    endpoint: /health/card-pipeline
    interval: 30s
    timeout: 5s

  hooks:
    on_dependency_ready:
      - event: ham_memory.ready
        handler: modules.card_pipeline.on_ham_ready
      - event: intent_registry.ready
        handler: modules.card_pipeline.on_intent_ready

config:
  pipeline:
    resolution_threshold: 0.85
    angela_threshold: 0.70
  storage:
    path: data/cards/
```

### 3.2 欄位說明

| 欄位 | 必填 | 說明 |
|------|------|------|
| `name` | ✅ | 模組名稱，同時作為 ServiceRegistry key |
| `version` | ✅ | 語意化版本 |
| `kind` | ✅ | `service`（常駐服務）、`adapter`（純轉接層）、`provider`（後端實作）、`cli`（命令列工具） |
| `depends_on.required` | ❌ | 啟動時必須存在的依賴，缺少則 fail fast |
| `depends_on.optional` | ❌ | 可選依賴，不存在時 module 降級運作 |
| `provides.services` | ❌ | 註冊到 ServiceRegistry 的服務 |
| `provides.adapters` | ❌ | 註冊到 AdapterRegistry 的轉接器 |
| `lifecycle.init` | ✅ | 初始化函數（可 sync 或 async），返回 module 實例 |
| `lifecycle.start` | ❌ | 啟動函數（可 sync 或 async），在 init 完成後呼叫 |
| `lifecycle.stop` | ❌ | 關閉函數（可 sync 或 async），用於清理資源 |
| `lifecycle.health` | ❌ | Health check 設定 (若無指定 endpoint，ModuleManager 用 `get_status()` 回應) |
| `lifecycle.hooks` | ❌ | 事件驅動的 lifecycle hook |
| `config` | ❌ | 預設配置。ModuleManager 啟動時會從 `angela_core.yaml` 讀取 `modules.{name}` 覆蓋此處的值 |

### 3.2a 目錄慣例

所有 module 放在 `apps/backend/src/modules/`（與 `core/`, `services/`, `api/` 同層級）：

```
apps/backend/src/
  modules/
    card_pipeline/
      module.yaml
      __init__.py
    intent_registry/
      module.yaml
      __init__.py
```

這確保 `from modules.card_pipeline import init` 的 import path 可以在現有 `sys.path` 中正確解析。
ModuleManager 的預設掃描路徑是 `[Path("apps/backend/src/modules/")]`。

### 3.2b 配置覆蓋機制

ModuleManager 啟動時讀取 `angela_core.yaml` 的 `modules` 區段：

```yaml
# angela_core.yaml
modules:
  card_pipeline:
    pipeline:
      resolution_threshold: 0.90  # 覆蓋 descriptor 的 0.85
```

合併規則：`angela_core.yaml` > `module.yaml config` > 程式碼內建的預設值。

### 3.3 依賴解析順序

ModuleManager 在啟動時對所有 module 做 topological sort：

```
service_registry (built-in)
  └── intent_registry
       └── card_pipeline
            ├── ham_memory (optional)
            ├── personality_module (optional)
            └── llm_module
                 └── vision_module
                 └── audio_module
```

循環依賴偵測：如果有環 `A → B → C → A`，啟動時報錯，無法啟動。

---

## 4. ModuleManager 架構

### 4.1 系統架構圖

```
┌──────────────────────────────────────────────────────────┐
│                   ModuleManager                           │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Scanner     │  │  Resolver    │  │  Lifecycle    │  │
│  │  discover()  │→│  sort()      │→│  init/start   │  │
│  │  watch()     │  │  detect_cycle│  │  stop/health  │  │
│  └──────────────┘  └──────────────┘  └───────┬───────┘  │
│                                              │          │
│  ┌──────────────┐  ┌──────────────┐          │          │
│  │  Registry    │  │  Events      │◄─────────┘          │
│  │  get/put     │  │  on_ready    │                     │
│  │  status      │  │  on_fail     │                     │
│  └──────┬───────┘  └──────────────┘                     │
└─────────┼────────────────────────────────────────────────┘
          │ uses
          ▼
┌──────────────────────────────────────────────────────────┐
│               ServiceRegistry (existing)                  │
│  register("card_pipeline", instance)                      │
│  get("card_pipeline") → instance                         │
└──────────────────────────────────────────────────────────┘
```

### 4.2 啟動流程

```
ModuleManager.start()
  │
  ├── 1. Scanner.discover()
  │     ├── scan modules/*/module.yaml
  │     ├── validate schema
  │     └── return [ModuleDescriptor, ...]
  │
  ├── 2. Resolver.resolve(descriptors)
  │     ├── topological sort by depends_on
  │     ├── detect cycles → fail fast if found
  │     ├── mark missing optional deps
  │     └── return ordered list
  │
  ├── 3. Lifecycle.init_all(resolved)
  │     ├── for each module in order:
  │     │   ├── call module.init() with resolved deps
  │     │   ├── register result in ServiceRegistry
  │     │   └── if fail → flag as ERROR, continue others
  │     └── return init results
  │
  ├── 4. Lifecycle.start_all(resolved)
  │     ├── for each module in same order (deps first):
  │     │   ├── call module.start() (async aware)
  │     │   ├── fire on_ready event
  │     │   └── if fail → flag as ERROR, skip dependents
  │     └── return start results
  │
  └── 5. Lifecycle.monitor()
        ├── health check every interval
        ├── restart threshold exceeded → flag DEAD
        └── emit status changes as events
```

### 4.3 關閉流程

```
ModuleManager.stop()
  └── for each module in reverse init order:
       ├── call module.stop()
       ├── unregister from ServiceRegistry
       └── fire on_stop event
```

### 4.4 熱插拔流程

```
ModuleManager.hotplug(module_path)
  │
  ├── 1. Scanner.validate(module.yaml)
  ├── 2. Resolver.check_deps(descriptor, existing_modules)
  ├── 3. Lifecycle.init(descriptor)
  ├── 4. Lifecycle.start(descriptor)
  ├── 5a. Re-resolve dependents' hooks (新 module 的事件要註冊到已存在的 listener)
  └── 5b. Update routing table
        ├── if descriptor provides API routes → register in router
        └── if descriptor provides hooks → register in event bus
```

### 4.5 Sync/async boundary 與 thread safety

當 ModuleManager 在 async context 中呼叫 sync method 時，預設使用 `asyncio.to_thread()`，
但需注意 `concurrent.futures` 的要求：**傳入 `to_thread` 的函數和參數必須可 pickle**。

若 module 有不可 pickle 的屬性（如 file handles, socket connections），應：

1. **在 `init()` 中建立這些資源**（ModuleManager 在 async 環境中呼叫 init，不需 pickle）
2. **`start()` 後才使用它們**
3. **在 `module.yaml` 中標記**：
   ```yaml
   lifecycle:
     thread_safe: false  # 若 false，ModuleManager 不在 thread pool 中執行此 module 的 sync method
   ```

若 `thread_safe: false`，ModuleManager 改為在 event loop 中直接呼叫 sync method
（會短暫阻塞 event loop，適合少量快速操作）。長時間 CPU-bound 操作仍應提取到獨立的 thread/process。**不建議用在 pipeline.process() 這類長時間操作** — 這類 method 應宣告為 async。

---

## 5. API 設計

### 5.1 ModuleManager 類

```python
class ModuleManager:
    """Central orchestrator for module lifecycle and wiring."""

    async def discover(self, paths: list[Path] = None) -> list[ModuleDescriptor]: ...
    def resolve(self, descriptors: list[ModuleDescriptor]) -> list[ModuleDescriptor]: ...
    async def init_all(self, resolved: list[ModuleDescriptor]) -> dict[str, InitResult]: ...
    async def start_all(self, resolved: list[ModuleDescriptor]) -> dict[str, StartResult]: ...
    async def stop_all(self) -> None: ...
    async def hotplug(self, path: Path) -> HotplugResult: ...

    # Registry
    def get_module(self, name: str) -> Optional[ModuleInstance]: ...
    def has(self, name: str) -> bool: ...
    def list_modules(self) -> dict[str, ModuleStatus]: ...
    def get_status(self, name: str) -> ModuleStatus: ...

    # Events
    def on(self, event: str, handler: Callable): ...
    def emit(self, event: str, data: Any): ...
```

### 5.2 ModuleDescriptor 資料類

```python
@dataclass
class ModuleDescriptor:
    name: str
    version: str
    kind: ModuleKind  # service | adapter | provider | cli
    description: str = ""

    depends_on: DependencySpec = field(default_factory=DependencySpec)
    provides: ProvidedServices = field(default_factory=ProvidedServices)
    lifecycle: LifecycleHooks = field(default_factory=LifecycleHooks)
    config: dict = field(default_factory=dict)

@dataclass
class DependencySpec:
    required: list[str] = field(default_factory=list)
    optional: list[str] = field(default_factory=list)

@dataclass
class ProvidedServices:
    services: list[ServiceDecl] = field(default_factory=list)
    adapters: list[AdapterDecl] = field(default_factory=list)

@dataclass
class LifecycleHooks:
    init: str = ""       # dotted path to sync factory function
    start: str = ""      # dotted path to async/sync start
    stop: str = ""       # dotted path to async/sync stop
    health: HealthConfig = field(default_factory=HealthConfig)
    hooks: list[HookDecl] = field(default_factory=list)
```

### 5.3 Events

| Event | 觸發時機 | Data |
|-------|----------|------|
| `{module}.init` | 模組 init 完成 | `{name, instance, elapsed_ms}` |
| `{module}.ready` | 模組 start 完成 | `{name, provided_services}` |
| `{module}.failed` | 模組 init 或 start 失敗 | `{name, phase, error}` |
| `{module}.stopped` | 模組 stop 完成 | `{name, elapsed_ms}` |
| `{module}.health_ok` | 健康檢查通過 | `{name, latency_ms}` |
| `{module}.health_fail` | 健康檢查失敗 | `{name, error, consecutive_fails}` |
| `dependency.missing` | 必需依賴不存在 | `{module, missing_dep}` |

---

## 6. 與現有基礎設施的整合

### 6.1 ServiceRegistry（已存在）

ModuleManager 不取代 ServiceRegistry，而是建立在它之上：

```python
# Before (手動註冊)
get_registry().register("card_registry", CardRegistry())

# After (ModuleManager 自動註冊)
manager = ModuleManager()
manager.discover()  # 掃描 modules/*/module.yaml
manager.resolve()   # 排序依賴
manager.init_all()  # 自動呼叫 init → register to ServiceRegistry
manager.start_all() # 自動呼叫 start
```

所有 `get_registry().get("xxx")` 的現有程式碼不受影響。

### 6.2 wiring.py（已存在）

`wiring.py` 的 `initialize_all_services()` 改為：

```python
async def initialize_all_services():
    manager = ModuleManager(
        registry=get_registry(),
        scan_paths=[Path("modules/")]
    )
    await manager.start()
    # 向後相容：舊的 wiring 邏輯在完全遷移前保留
    await _legacy_wiring(manager)
```

### 6.3 lifespan.py（已存在）

`lifespan.py` 的 `startup`/`shutdown` 改為：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    manager = await initialize_all_services()
    app.state.module_manager = manager

    yield

    # shutdown
    await manager.stop_all()
    app.state.module_manager = None
```

### 6.4 router.py（現有 hotspot）

router.py 不再手動 import 每個 service，而是透過 ModuleManager：

```python
# Before
from services.chat_service import ChatService
from services.vision_service import VisionService

# After (只在需要時才 lazy resolve)
module_manager = app.state.module_manager
chat = module_manager.get_module("chat_service")
vision = module_manager.get_module("vision_service")
```

---

## 7. 遷移策略

### 7.1 階段規劃

| Phase | 內容 | 目標 | 影響 |
|-------|------|------|------|
| **M0** | ModuleManager 核心 + descriptor schema | Scanner, Resolver, Lifecycle, Events | 新建，不影響現有 |
| **M1** | card_pipeline 成為第一個 module | `modules/card_pipeline/module.yaml` | 驗證整個流程 |
| **M2** | intent_registry module | 解決 intent 學習回饋問題 | 修復 HIGH 8/8 |
| **M3** | chat_service module | ChatService 不再直接 import | 降耦合 |
| **M4** | llm_module (取代 router.py hotspot) | `modules/llm/module.yaml` | 1522→拆分 |
| **M5** | 其餘 service → module | vision, audio, tactile, drive | 全面覆蓋 |

### 7.2 M0: ModuleManager 核心

**新增檔案**:
- `core/system/module_manager/__init__.py` — ModuleManager 類
- `core/system/module_manager/scanner.py` — Scanner
- `core/system/module_manager/resolver.py` — Resolver
- `core/system/module_manager/lifecycle.py` — Lifecycle 管理
- `core/system/module_manager/events.py` — Event bus
- `core/system/module_manager/models.py` — ModuleDescriptor dataclass
- `modules/` — 根目錄，放置所有 module descriptor

**不修改任何現有檔案**。ModuleManager 在這一階段是純新增，與現有系統並行運作。

**測試目錄**: `tests/core/module_manager/`（與現有 `tests/core/` 結構一致）：
```
tests/core/module_manager/
  test_models.py       — ModuleDescriptor dataclass 序列化/反序列化
  test_scanner.py      — module.yaml 解析、schema 驗證、缺失欄位報錯
  test_resolver.py     — topological sort、cycle detection、optional deps
  test_lifecycle.py    — init→start→stop 順序、sync/async 感知
  test_events.py       — event bus 發布/訂閱、health monitor
  test_manager.py      — ModuleManager.start() 完整流程、hotplug
```

### 7.3 M1: card_pipeline 示範

新增 `modules/card_pipeline/module.yaml` + 實作 init/start 函數。
ModuleManager 可以獨立啟動 card_pipeline，不需要改任何現有 wiring。

### 7.4 M2-M5: 逐步遷移

每個 module 遷移步驟：
1. 寫 `module.yaml`
2. 實作 `init()` 函數（取代原有的 `get_xxx()` factory）
3. 更新 `module.yaml` 的 `depends_on` 指向已遷移的 module
4. 從 `wiring.py` / `lifespan.py` 移除手動 wiring
5. 確認 test 通過

---

## 8. 解決的具體問題

### 8.1 與 25 個 Plan Issues 的對應

| Issue | Phase | Severity | ModuleManager 如何解決 |
|-------|-------|----------|----------------------|
| 0.1 IntentRegistry 非 singleton | 0 | HIGH | Descriptor 宣告 `intent_registry` → ModuleManager 提供 singleton |
| 1.1 Sync pipeline in async | 1 | HIGH | Descriptor 宣告 sync/async → ModuleManager 提供 `run_in_thread()` |
| 1.2 Fresh IntentRegistry per msg | 1 | HIGH | ModuleRegistry 提供 singleton，不再每次 new |
| 2.1 asyncio in sync method | 2 | HIGH | Lifecycle 知道 sync/async 邊界 → 提供 async context |
| 2.2 No async process() | 2 | HIGH | Descriptor 宣告 `interface: CardImportHandler` → 編譯時檢查 |
| 3.1 text[:50] garbage keyword | 3 | HIGH | Config schema 驗證 → 拒絕無意義資料 |
| 4.1 pipeline 阻塞 event loop | 4 | HIGH | ModuleManager 自動在 thread pool 跑 CPU-bound modules |
| 4.2 deprecated utcnow() | 4 | HIGH | Code review + 統一 lint |
| 0.3 CLI 卡片不可見 | 0 | MEDIUM | CLI module 用 ModuleManager，註冊到 ServiceRegistry |
| 1.3 Pipeline 失敗丟失 | 1 | MEDIUM | ModuleManager 管理 registry state → 不會丟 |
| 4.3 lifespan vs wiring 矛盾 | 4 | MEDIUM | 只有一個入口：ModuleManager.start() |
| 4.4 無 auth/rate limit | 4 | MEDIUM | Module descriptor 可宣告 middleware 需求 |
| X.1 靜默錯誤 | All | MEDIUM | ModuleManager events 追蹤每個失敗 |

### 8.2 與三個架構指標的對應

| 指標 | Before | After ModuleManager | 原因 |
|------|--------|-------------------|------|
| 耦合集中度 | 35 | **65-70** | router.py 的 import 職責由 ModuleManager 接管 |
| 共享可變狀態 | 35 | **60** | module-level `_xxx = None` → ModuleManager lifecycle |
| God module | 35 | **60** | 模組只 export interface，wiring 在 descriptor |

### 8.3 與 8D Matrix 的互動

| 維度 | 8D Matrix | ModuleManager |
|------|-----------|---------------|
| 範圍 | Angela 執行時狀態 | 程式碼架構接線 |
| 資料 | cognitive/emotional/bio metrics | Module 依賴/健康/狀態 |
| 輸出 | Response generation, behavior | Service wiring, routing |
| 時機 | 每個 user message | 啟動時 + 熱插拔時 |
| 整合 | ModuleManager 可以 query 8D 狀態 | 8D 可以透過 ModuleManager 取得 module 健康度 |

---

## 9. 路線圖

```
Week 1: M0 ModuleManager 核心
  ├── models.py (ModuleDescriptor dataclasses)
  ├── scanner.py (module.yaml 解析 + 驗證)
  ├── resolver.py (topological sort + cycle detection)
  ├── lifecycle.py (init/start/stop/hooks)
  ├── events.py (event bus + health monitor)
  └── __init__.py (ModuleManager facade)
  → test: 50+ tests, 0 external dependencies

Week 2: M1 card_pipeline + M2 intent_registry
  ├── modules/card_pipeline/module.yaml
  ├── modules/card_pipeline/init.py
  ├── modules/intent_registry/module.yaml
  ├── modules/intent_registry/init.py
  └── 更新 wiring.py 加入 ModuleManager
  → 卡片導入 + IntentRegistry singleton 可運作

Week 3: M3 chat_service module
  ├── modules/chat_service/module.yaml
  ├── modules/chat_service/init.py
  ├── 從 lifespan.py 移除 ChatService 手動 import
  └── 更新 router.py 用 module_manager.get()
  → ChatService 改由 ModuleManager 管理

Week 4: M4 llm_module（router.py 拆分）
  ├── modules/llm/module.yaml
  ├── modules/llm/providers/
  ├── modules/llm/prompt_builder/
  └── router.py → modules/llm/router.py (縮小到 200 行)
  → 1522 行 router.py 變成 200 行 gateway + 模組內 routing

Week 5: M5 其餘 service
  ├── vision, audio, tactile, drive
  ├── 每個 service 建立 module.yaml
  └── wiring.py 只剩 ModuleManager.start()
  → 所有 service 統一管理
```

### 9.1 驗收標準

| 標準 | 門檻 | 驗證方式 |
|------|------|---------|
| ModuleManager 啟動 | 0 error | `pytest tests/core/module_manager/` |
| 舊系統不受影響 | 所有既有 test pass | `pytest tests/` |
| card_pipeline 可獨立部署 | module.yaml + init OK | `manager.discover("modules/card_pipeline")` |
| 熱插拔不影響其他 module | 新增/移除 module，其餘正常 | `manager.hotplug("modules/new_module")` |
| Cycle detection 正確 | 故意引入 cycle → fail fast | `resolver.detect_cycles()` |
| Health check 報告正確 | module 掛了 → status=DEAD | `manager.get_status("xxx")` |
