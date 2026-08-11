# Angela AI 模組化分析

> **⚠️ 過時警告（2026-05-30 審計）**: 此文件撰寫於 2026-05-21。其後 codebase 經歷大幅重構：
> - `main_api_server.py` 從 1,452 → 314 行，`angela_llm_service.py` 從 2,287 → 36 行（shim），`chat_service.py` 從 1,416 → 313 行
> - FastAPI `Depends` 現在用於 11 個路由檔案（42 次出現）
> - `models/` 跨套件 import 已清理
> - `__new__` singleton 模式已全部消除
>
> 以下為重構後的更新評分：

## 評分總覽（2026-05-30 更新）

```
模組邊界定義     ██████████ 85  — Protocols、ABCs、Factory 函數都到位（不變）
Circular 防護    ████████░░ 70  — 有 cycle 但用 lazy import 撐住（不變）
__init__.py 紀律  ████████░░ 75  — ↑ 從 40 提升（models/ 跨套件 import 已修復）
耦合集中度       ████░░░░░░ 35  — ↑ 從 20 提升（main_api_server/chat_service 大量瘦身，但 router.py 成為新 hotspot）
共享可變狀態     ████░░░░░░ 35  — ↑ 從 15 提升（__new__ 模式已消除，~14 個 module-level globals）
God module 問題   ████░░░░░░ 35  — ↑ 從 10 提升（11→9 個 >1000 行檔案，top4 從 7,177→5,714 行）
DI 框架          █████░░░░░ 50  — ↑ 從 0 提升（FastAPI Depends 42 次、ServiceRegistry、wiring.py）
```

**重構後綜合分數：~55/100**（↑ 從 34/100）

注意：原始 34/100 評分基於重構前的 codebase。實際模組化改善已發生，但 `services/llm/router.py`（1,522 行）成為新的耦合 hotspot。

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
core/engine/live2d_avatar_generator.py  1,032 行  (原 core/autonomous/)
services/main_api_server.py               314 行  (↓ 重構後瘦身 78%)
```

**這些檔案的共同問題**：一個 PR 可能同時改動聊天邏輯、意圖路由、LLM 呼叫、config 讀取、Google Drive 操作、數學驗證 — 都在同一份檔案裡。

**2026-05-30 更新**: 重構後 `main_api_server.py`（314 行）、`chat_service.py`（313 行）、`angela_llm_service.py`（36 行 shim）已大幅瘦身。但 `services/llm/router.py`（1,522 行）成為新的耦合 hotspot。

### 2.2 Central Hub Coupling（重構後）

**2026-05-30 更新**: `main_api_server.py` 和 `chat_service.py` 的耦合已大幅降低（瘦身 78%/78%）。耦合轉移到：

**`services/llm/router.py`**（1,522 行）— 新 hotspot：
```
services/ (angela_llm_service, chat_service, math_verifier, vision_service, audio_service)
core/     (config_loader, engine/state_matrix, engine/state_matrix_adapter, tools/*)
ai/       (memory/ham_memory, response/composer, alignment/ego_guard, context/*)
```

**`api/lifespan.py`**（237 行）— 12 個 module-level lazy-loaded singleton：
```
services/ (vision, audio, tactile, chat, llm, wiring, digital_life, economy)
core/     (config_loader, life/heartbeat, bio/biological_integrator)
```

**任何子系統的改動都需要檢查 `router.py`** — 這是新的耦合中心。

### 2.3 Pervasive Singleton 共享可變狀態（重構後）

| 型態 | 數量 | 範例 |
|------|------|------|
| `__new__` singleton | **0**（↑ 已全部消除） | 原 AngelaLLMService, StateMatrix4D 等已改為 function-attribute 或 ServiceRegistry |
| Function-attribute singleton | 5+ | get_angela_chat_service._instance, get_llm_service 等 |
| Module-level `_xxx = None` 全域 | **~14**（↓ 從 20+ 減少） | lifespan.py 的 12 個 lazy-load + chat_service/config_loader/router |
| Module-level 快取 | 5 | router.py 的 _llm_service, _MEMORY_ENHANCED 等 |

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
