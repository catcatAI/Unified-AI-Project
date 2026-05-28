# Angela AI 模組化分析

## 評分總覽

```
模組邊界定義     ██████████ 85  — Protocols、ABCs、Factory 函數都到位
Circular 防護    ████████░░ 70  — 有 cycle 但用 lazy import 撐住
__init__.py 紀律  ████░░░░░░ 40  — models/ 跨套件 import services/
耦合集中度       ██░░░░░░░░ 20  — 2 個 central hub 檔案引 5-7 個 package
共享可變狀態     ██░░░░░░░░ 15  — 20+ singleton，80+ module-level 全域變數
God module 問題   █░░░░░░░░░ 10  — 11 個檔案 >1000 行，前 4 個合計 7,177 行
DI 框架          ░░░░░░░░░░  0  — 無 FastAPI Depends、無 inject、無 auto-register
```

**綜合分數：34/100**

---

## 1. 好的部分

### 1.1 Protocol 介面合約

`core/interfaces/protocols.py` 定義了 6 層生命架構的 protocol：

```python
class L1Biological(Protocol):    # advance_time, get_metabolic_cost
class L2Cognitive(Protocol):     # process_event
class L3Identity(Protocol):      # verify_alignment
class L4Creative(Protocol):      # evaluate_novelty
```

搭配 `@runtime_checkable` 支援 isinstance 檢查。

### 1.2 17 個 ABC

散佈在整個 codebase：

| 位置 | ABC |
|------|-----|
| `angela_llm_service.py` | `BaseLLMBackend(ABC)` |
| `core/cache/` | `CacheBackend(ABC)` |
| `core/hsp/` | `HSPMessageHandler(ABC)`, `HSPTransport(ABC)` |
| `core/ripple/` | `CascadeStrategy(Protocol)` |
| `ai/alignment/` | `AdversarialGenerator(ABC)`, `ProbabilityModel(ABC)` |
| `ai/context/` | `Storage(ABC)` |

### 1.3 Factory 函數（Service Locator 模式）

```python
get_llm_service()              → 懶載入 singleton
get_angela_chat_service()      → function-attribute singleton
get_angela_config()            → 17+ callers 的中心節點
get_metabolic_heartbeat()      → 生物心跳
get_digital_life()             → 生物整合器
```

配合 `core/__init__.py` 的 `create_*()` 工廠：
`create_precision_system()`, `create_maturity_system()`, `create_soul_core()`, `create_i18n_manager()`...

### 1.4 Lazy Import 防 Circular

所有跨套件 import 都在函數內部而非模組層級，這是整個架構沒有在 import 時直接炸掉的唯一原因：

```python
# chat_service.py
async def initialize(self):
    from core.autonomous.physiological_tactile import ...
    from services.vision_service import ...
    
def _handle_intent(self, ...):
    from ai.alignment.free_will_simulator import ...
```

---

## 2. 壞的部分

### 2.1 God Module 問題（11 個檔案 >1000 行）

```
services/angela_llm_service.py          2,287 行  ← LLM 服務 + 全部 provider 轉接器
core/autonomous/state_matrix_adapter.py 1,438 行  ← 雙軌（舊+新）狀態矩陣
core/autonomous/state_matrix.py         1,419 行  ← 原始 8D StateMatrix
services/chat_service.py                1,416 行  ← 聊天 + 意圖路由 + 融合
core/ethics/ethics_manager.py           1,462 行
core/autonomous/neuroplasticity.py      1,348 行
core/autonomous/physiological_tactile.py 1,291 行
core/autonomous/endocrine_system.py     1,053 行
core/fusion/multimodal_fusion_engine.py 1,068 行
core/autonomous/live2d_avatar_generator.py 1,036 行
services/main_api_server.py            1,452 行
```

**這些檔案的共同問題**：一個 PR 可能同時改動聊天邏輯、意圖路由、LLM 呼叫、config 讀取、Google Drive 操作、數學驗證 — 都在同一份檔案裡。

### 2.2 Central Hub Coupling

**`main_api_server.py`** 直接依賴 7 個頂層 package：

```
services/ (vision, audio, tactile, chat, llm, math_verifier, atlassian, state_matrix)
core/     (config_loader, autonomous.*)
api/      (router, endpoints)
system/   (security_monitor)
shared/   (security_middleware, key_manager)
economy/  (economy_manager)
integrations/ (os_bridge_adapter)
```

**`chat_service.py`** 直接依賴 5 個頂層 package：

```
core/     (config_loader, autonomous.*, gsi_governance, system.*, tools.*)
ai/       (alignment.*, memory.*, security.*, personality.*, response.*)
services/ (vision_service, angela_llm_service, math_verifier)
integrations/ (google_drive_service)
shared/   (standard_imports, error)
```

**任何子系統的改動都需要檢查這兩份檔案** — 這是耦合的典型症狀。

### 2.3 Pervasive Singleton 共享可變狀態

| 型態 | 數量 | 範例 |
|------|------|------|
| `__new__` singleton | 10+ | AngelaLLMService, StateMatrix4D, BiologicalIntegrator, AngelaConfigLoader... |
| Function-attribute singleton | 5+ | get_angela_chat_service._instance |
| Module-level `_xxx = None` 全域 | 20+ | main_api_server.py 的 _desktop_interaction, _action_executor 等 |
| Module-level 快取 | 8 | angela_llm_service.py 的 _MEMORY_ENHANCED, HAMMemoryManager... |

**後果**：
- 測試需要手動 reset singleton 狀態
- 單元測試彼此互相影響
- 隱含的 global state mutation 難以追蹤

### 2.4 跨套件 `__init__.py`

```python
# models/__init__.py ← 應該只導入 models/ 內的東西
from services.api_models import UserInput, AIOutput, SessionStartRequest, ...
```

**違反了一般架構原則**：`models/` 是資料層，不該反向依賴 `services/`（服務層）。

### 2.5 `interfaces/` 目錄是空殼

```
apps/backend/src/interfaces/
└── __init__.py  ← 空的，無任何內容
```

規劃了介面層但從未實作。實際的 Protocol 定義在 `core/interfaces/protocols.py`，但 `interfaces/` 這個包沒有任何匯出。

---

## 3. 中性/值得注意

### 3.1 雙軌架構（Refactoring Pattern）

`state_matrix_adapter.py` 明確標示雙軌策略：

```python
# 軌 A（新）：使用 refactored 模組 (Axis, TemporalState, InfluenceSpace, AllocationPolicy)
# 軌 B（舊）：保持現有 StateMatrix4D 所有接口和行為不變
```

好處：可增量重構。壞處：1,438 行的 adapter 是技術債的直接體現。

### 3.2 TYPE_CHECKING 防護

少數檔案（2 處）使用 `TYPE_CHECKING` 來避免運行時 import：

```python
if TYPE_CHECKING:
    from ai.integration.unified_control_center import UnifiedControlCenter
    from services.angela_llm_service import AngelaLLMService
```

正確做法，但應推廣到更多跨套件 import。

### 3.3 42 個頂層目錄

`src/` 底下有 42 個 entries，很多是 single-file package：

```
economy/   → 只有 economy_manager.py + __init__.py
fragmenta/ → 4 個實驗檔
creation/  → 只有 creation_engine.py
search/    → 只有 search_engine.py
pet/       → 只有 pet_manager.py
```

這增加了跨套件 import 的表面積，且缺乏依賴方向規範。

---

## 4. 改善建議

| 優先級 | 動作 | 預估工時 | 影響 |
|--------|------|---------|------|
| 🔴 | 把 `chat_service.py` 拆成：chat_routing + intent_handler + consciousness_synth | 2 天 | 最大耦合源 |
| 🔴 | 把 `main_api_server.py` 的 service initialization 移到獨立 `wiring.py` | 1 天 | 第二大耦合源 |
| 🟡 | 補上 DI 框架（至少用 FastAPI Depends） | 2 天 | 可測試性 |
| 🟡 | 把 20+ singleton 改為 instance 傳遞 | 3 天 | 測試獨立性 |
| 🟢 | 補上 `interfaces/__init__.py` 匯出所有 Protocol | 2 小時 | 文件化 |
| 🟢 | 修 `models/__init__.py` 的錯誤 import | 1 小時 | 架構紀律 |
