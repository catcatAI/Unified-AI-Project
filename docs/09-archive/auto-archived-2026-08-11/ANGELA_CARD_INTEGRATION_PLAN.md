# Angela 卡片導入管道與聊天系統整合計畫

> **目標**: 將現有 `core/card/` 卡片導入管道（CardImportPipeline）接入 Angela 的聊天系統（ChatService → AngelaLLMService），實現三級分發（Program → Angela HAM → LLM）與學習閉環。
> **基於**: 實際代碼審計（2026-05-30）+ README.md 已知問題比對
> **狀態**: 計畫階段 — 全部代碼已存在但彼此孤立

---

## 1. 當前狀態分析（基於實際代碼審計）

### 1.1 現有組件及其連接狀態

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CURRENT STATE                                │
│                                                                     │
│  run_card_import.py  (standalone CLI, 不連任何服務)                  │
│       │                                                             │
│       ▼                                                             │
│  CardImportPipeline.process()                                       │
│       │                                                             │
│       ├──► DeterministicParser     (Stage 1: Auto)                  │
│       ├──► ConflictDetector         (Stage 1)                       │
│       ├──► MergeEngine              (Stage 1)                       │
│       ├──► TimelineResolver         (Stage 1)                       │
│       ├──► TextGravityField         (Stage 2: Angela)               │
│       ├──► TokenExtractor           (Stage 2)                       │
│       └──► LLMFallback              (Stage 3: 硬編碼，非真正LLM)     │
│                                                                     │
│  ⚠ MemoryAdapter (81行)       → 存在但無人呼叫                       │
│  ⚠ PersonalityAdapter (59行)  → RoleplayEngine 已用，但 Pipeline 未接│
│  ⚠ CardRegistry (203行)      → pipeline + run_card_import 使用      │
│  ⚠ IntentRegistry (168行)    → character_card intent 存在但無 handler│
│  ⚠ ConfigLoader.learn()      → 從未接收卡片導入質量數據               │
│                                                                     │
│  ChatService (313行)                                                │
│       ├──► _analyze_intent()   → 僅 keyword match, 無 card pipeline │
│       ├──► generate_response() → 走 LLM, 從不調用 CardImportPipeline│
│       └──► IntentRegistry 從未被 ChatService 使用                    │
│                                                                     │
│  AngelaLLMService / LLM Router (1522行)                             │
│       ├──► HAMMemoryManager    → 用於 memory retrieval              │
│       ├──► MemoryAdapter       → 從未傳入 HAMManager                 │
│       ├──► TemplateMatcher     → P0-2 模板匹配                      │
│       └──► LLMFallback(66行)   → 硬編碼規則，非真正LLM路由            │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 精確的斷開點（file:line）

| # | 斷開點 | 位置 | 說明 |
|---|--------|------|------|
| D1 | `MemoryAdapter` 從未實例化 | `memory_adapter.py:21-22` | `__init__` 接收 `ham_manager=None`，但永遠沒人傳入 |
| D2 | `PersonalityAdapter` RoleplayEngine 已用但 Pipeline 未接 | `roleplay_engine.py:22-23` | `RoleplayEngine.__init__` 自動建立 `PersonalityAdapter()` 實例，但 `CardImportPipeline` 完全不使用它 |
| D3 | `CardImportPipeline` 不接收 adapters | `pipeline_orchestrator.py:46-54` | 建構子只接收 `registry`，沒有 memory/personality adapter 掛鉤 |
| D4 | `ChatService._analyze_intent()` 不使用 IntentRegistry | `chat_service.py:155-167` | 硬編碼 keyword match，忽略了 `IntentRegistry` 和 YAML 定義的 `character_card` intent |
| D5 | ChatService 沒有 `character_card` 意圖處理分支 | `chat_service.py:122-127` | 只有 `llm_manage` 和 `file_op` 兩個分支 |
| D6 | `CardRegistry` 未註冊到 ServiceRegistry（但 CLI 有使用） | 全域 | 無任何地方 `get_registry().register("card_registry", ...)`。注意：`run_card_import.py:149-242` 已直接使用 `CardRegistry()` — 證明 pattern 已驗證 |
| D7 | `LLMFallback` 硬編碼而非使用真實 LLM | `llm_fallback.py:39-63` | 所有 `_resolve_*` 方法都是字串拼接，從未調用 `AngelaLLMService` |
| D8 | `ConfigLoader.learn()` 從未接收卡片數據 | `config_loader.py:285-311` | `learn()` 支援四種事件類型，但無任何代碼從 pipeline 調用它 |
| D9 | `run_card_import.py` 是獨立 CLI | `run_card_import.py:280-281` | `if __name__ == "__main__"`，無法被 API 或服務觸發 |
| D10 | 無異步任務隊列（CardImport專屬） | 缺失 | 大規模導入會阻塞事件循環。注意：專案已有 `asyncio.Queue` 模式在 `unified_control_center.py:50` 和 `feedback_processor.py:174`，可復用 |

### 1.3 README.md 對照 — 已知功能斷鏈

根目錄 `README.md`（v7.5.0-dev）已明確列出與本計畫相關的已知問題：

| 本計畫斷開點 | README 對應條目 | 一致？ |
|-------------|----------------|--------|
| D1: MemoryAdapter 無呼叫 | 「記憶鏈（HAM/LU/CDM）— 類別完整但查詢/存儲 flow 從未接上」 | ✅ 一致 — 都是 adapter 存在但未接 |
| D4-D5: ChatService 硬編碼 | 未明確列出（ChatService 拆分後 S1 標示 BROKEN） | 🟡 README 更關注拆分問題而非意圖分發 |
| D6: CardRegistry 未註冊 | 無提及（`core/card/` 子系統在 README 中完全未記錄） | 🟡 新子系統，README 需補充 |
| D8: ConfigLoader 未接入學習 | 「5 大理論公式未整合到 LLM Prompt」 | 🟡 相近問題但不同系統 |
| D10: 無 async 任務隊列 | 「記憶鏈未接」間接相關 | 🟡 間接 |

**關鍵洞察**: `core/card/` 是完全未被主 README 記錄的子系統。README 的「功能斷鏈」清單確認了記憶系統未接線 — 與 D1 完全一致。

### 1.4 現有置信度/類型系統

```
PipelineResult.stage: "auto" | "angela" | "llm"
PipelineResult.confidence: 0.0 - 1.0
  RESOLUTION_THRESHOLD = 0.85  → Stage 1 足夠，跳過 Stage 2/3
  ANGELA_THRESHOLD    = 0.70  → Stage 2 足夠，跳過 Stage 3

CardType: CHARACTER | STORY_LINE | EVENT | RULE | PLAYER_TEMPLATE
          | WORLD_CORE | SCENE | NATION | ORGANIZATION | SKILL
          | ITEM | UNIVERSAL_MECHANISM | WORK_TOOL | PROJECT_MANAGEMENT
          | META_FORMULA | SAFETY_LEXICON | META_SETTING

ConflictType: HARD_ERROR | INTENTIONAL | MULTIVERSE | NARRATIVE_DEVICE
IntentFlag: PENDING | CONFIRMED_KEEP | SUPPRESS_FUTURE
```

---

## 2. 整合架構（目標狀態）

```
User Message
     │
     ▼
ChatService.generate_response()                     [chat_service.py:102]
     │
     ├── IntentRegistry.detect()                    [新增調用]
     │      │
     │      ├── "character_card" detected
     │      │      │
     │      │      ▼
     │      │  CardDispatchHandler (新增)
     │      │      │
     │      │      ├──► CardImportPipeline.process(raw_text)
     │      │      │      │
     │      │      │      ├── Stage 1 (Auto): parse → merge → detect
     │      │      │      ├── Stage 2 (Angela): TextGravityField + HAM retrieve
     │      │      │      └── Stage 3 (LLM): AngelaLLMService.generate_text()
     │      │      │             │                         [router.py:1597]
     │      │      │             └── 替代硬編碼 LLMFallback
     │      │      │
     │      │      ├──► MemoryAdapter.store_card(card, ham=ham)
     │      │      │      │                         [memory_adapter.py:34]
     │      │      │      └── HAMMemoryManager.store_experience()
     │      │      │                               [ham_manager.py:128]
     │      │      │
     │      │      ├──► PersonalityAdapter.load_card(card)
     │      │      │                         [personality_adapter.py:33]
     │      │      │
     │      │      ├──► CardRegistry.add(card)
     │      │      │
     │      │      ├──► ConfigLoader.learn("intent_pattern")
     │      │      │                         [config_loader.py:313]
     │      │      │
     │      │      └──► 返回 "已完成導入：{card.name}" 給用戶
     │      │
     │      ├── "general" / 其他
     │      │      │
     │      │      ▼
     │      │  AngelaLLMService.generate_response()  [router.py:710]
     │      │
     │      └── Learning Loop
     │             │
     │             ├── ConfigLoader.learn("route_success"/"route_fail")
     │             │                         [config_loader.py:348/365]
     │             └── ConfigLoader.learn("threshold_adjust")
     │                                        [config_loader.py:335]
```

---

## 3. 實作階段

### Phase 1: ChatService 意圖分發（最小可行整合）

**目標**: 當用戶說「導入角色卡」時，ChatService 調用 IntentRegistry 並分發到 CardImportPipeline。

#### 3.1.1 修改 `chat_service.py`

**D4 修復 — ChatService 改用 IntentRegistry:**

`chat_service.py:155-167` — 替換 `_analyze_intent()`:
```python
async def _analyze_intent(self, text: str) -> Dict[str, Any]:
    from core.intent_registry import IntentRegistry
    registry = IntentRegistry()
    intent_name, confidence = registry.detect(text)
    category = None
    if intent_name:
        category = intent_name
    return {"primary_intent": category or "general", "confidence": confidence}
```

**D5 修復 — 新增 character_card 處理分支:**

`chat_service.py:122-127` — 在 `generate_response()` 中新增分支:
```python
# 在第 127 行之後（現有 llm_manage/file_op 分支之後）新增：
elif primary_intent == "character_card":
    return await self._handle_card_import_intent(sanitized_message, user_name, primary_intent)
```

**新增方法** — 在 ChatService 類中新增（約 `chat_service.py:276` 之後）:
```python
async def _handle_card_import_intent(self, text: str, user_name: str, intent: str) -> str:
    """處理卡片導入意圖 — 調用 CardImportPipeline。"""
    from core.card.resolver.pipeline_orchestrator import CardImportPipeline
    from core.card.card_store import CardRegistry
    from core.card.integration.memory_adapter import MemoryAdapter
    from core.card.integration.personality_adapter import PersonalityAdapter
    from core.interfaces.service_registry import get_registry
    
    # 1. 初始化管道
    registry = get_registry().get("card_registry") or CardRegistry()
    pipeline = CardImportPipeline(registry=registry)
    
    # 2. 執行三階段導入
    result = pipeline.process(text, source_label=f"chat://{user_name}")
    
    if not result.card or not result.card.card_id:
        return "我沒能從這段描述中解析出卡片資訊，可以給我更完整的格式嗎？"
    
    # 3. 存入 HAM Memory
    ham_mgr = getattr(self, "_ham_manager", None)
    if ham_mgr is None:
        from ai.memory.ham_memory.ham_manager import HAMMemoryManager
        ham_mgr = HAMMemoryManager()
        self._ham_manager = ham_mgr
    
    memory_adapter = MemoryAdapter(ham_manager=ham_mgr)
    memory_id = await memory_adapter.store_card(result.card)
    
    # 4. 裝載到 PersonalityManager
    # 注意: RoleplayEngine (capabilities/roleplay_engine.py:22-23) 已有 PersonalityAdapter 實例。
    # 此處建立新的實例用於卡片導入專用，兩者互不衝突。
    try:
        from ai.personality.personality_manager import PersonalityManager
        pm = PersonalityManager()
        personality_adapter = PersonalityAdapter(personality_manager=pm)
        personality_adapter.load_card(result.card)
    except Exception as e:
        logger.warning(f"Personality loading skipped: {e}", exc_info=True)
    
    # 5. 註冊到 ServiceRegistry
    get_registry().register("card_registry", registry)
    
    # 6. 學習閉環：記錄意圖模式
    try:
        from core.config_loader import get_angela_config
        cfg = get_angela_config()
        cfg.learn("intent_pattern", {
            "intent": "character_card",
            "keywords": [text[:50]],
        })
    except Exception:
        pass
    
    return (
        f"已完成卡片導入：{result.card.name} ({result.card.qualified_id})\n"
        f"  - 處理階段：{result.stage}\n"
        f"  - 置信度：{result.confidence:.2f}\n"
        f"  - 衝突處理：{result.conflicts_resolved}/{result.conflicts_total}\n"
        f"  卡片已存入記憶系統！"
    )
```

#### 3.1.2 修改 `core/intent_registry.py`

**確保 character_card intent 可被 detect() 捕獲:**

YAML 已定義 `character_card` keywords（`angela_core.yaml:264-273`），`IntentRegistry._register_defaults()` 已從 YAML 載入（`intent_registry.py:54-69`）。Hardcoded fallback（`intent_registry.py:79`）也已包含 `character_card` 條目 — **無需修改**。

需確認 ChatService 的 `_analyze_intent()` 調用 `IntentRegistry.detect()` 後，返回的 `character_card` intent 能被 Phase 1 的 handler 捕獲。這屬於 Phase 1.1 的修改範疇。

#### 3.1.3 驗證 Phase 1

```bash
# 1. 測試 IntentRegistry 檢測
cd apps/backend && python -c "
from core.intent_registry import IntentRegistry
r = IntentRegistry()
print(r.detect('幫我生成一個角色卡'))
"

# 2. 測試 ChatService 意圖分發（mock）
cd apps/backend && python -c "
from services.chat_service import ChatService
import asyncio
svc = ChatService()
result = asyncio.run(svc._analyze_intent('角色卡 CC-42 測試'))
print(result)
"

# 3. 啟動服務並測試 API
cd apps/backend && python -c "
from core.interfaces.service_registry import get_registry
from core.card.card_store import CardRegistry
r = CardRegistry()
get_registry().register('card_registry', r)
print('CardRegistry registered')
"
```

---

### Phase 2: 三級分發強化（HAM 記憶檢索 + 真實 LLM 裁決）

**目標**: Stage 2 (Angela) 從 HAM 記憶檢索相關卡片資訊；Stage 3 (LLM) 使用真實 `AngelaLLMService.generate_text()` 替代硬編碼規則。

#### 3.2.1 Stage 2: HAM 記憶增強

**修改 `pipeline_orchestrator.py`** — 新增 HAM 查詢注入：

`pipeline_orchestrator.py:46-54` — 建構子新增 `ham_manager` 參數：
```python
def __init__(self, registry: Optional[CardRegistry] = None,
             ham_manager: Optional[Any] = None):
    self.registry = registry or CardRegistry()
    self.ham_manager = ham_manager
    # ... existing inits ...
```

`pipeline_orchestrator.py:91-106` — `_run_angela_stage()` 強化，新增 HAM 檢索：
```python
def _run_angela_stage(self, card: Card) -> Card:
    unresolved_texts = [c.description for c in card.conflicts if not c.suppressed]
    
    # HAM 記憶檢索增強（新增）
    if self.ham_manager and unresolved_texts:
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            future = asyncio.run_coroutine_threadsafe(
                self.ham_manager.query_core_memory(
                    keywords=[card.core_trait] if card.core_trait else [],
                    data_type_filter="character_card",
                    limit=3,
                ),
                loop,
            )
            memories = future.result(timeout=5.0)
            # HAM 結果注入到衝突解決
        except Exception:
            pass
    
    # ... existing text_gravity logic ...
    if card.core_trait and unresolved_texts:
        scored = self.text_gravity.compute_gravity(card.core_trait, unresolved_texts)
        # ... existing code ...
```

#### 3.2.2 Stage 3: 真實 LLM 裁決

**D7 修復 — 替換硬編碼 LLMFallback 為真實 LLM:**

**新建文件** `core/card/resolver/llm_bridge.py`:
```python
"""
ANGELA-MATRIX: [L4] [β] [B] [L0]
LLM Bridge — connects CardImportPipeline Stage 3 to AngelaLLMService.
Replaces hardcoded LLMFallback with real LLM calls.
"""
import logging
from typing import List, Optional
from core.card.card_types import Card, Conflict, ConflictType, IntentFlag

logger = logging.getLogger(__name__)

class LLMBridge:
    """Bridge that routes Stage 3 conflicts to real LLM via AngelaLLMService."""

    def __init__(self, llm_service=None):
        self._llm = llm_service

    async def resolve_async(self, card: Card, conflicts: List[Conflict]) -> List[Conflict]:
        """Async resolve conflicts using real LLM."""
        resolved = []
        for conflict in conflicts:
            if conflict.suppressed or conflict.user_intent == IntentFlag.CONFIRMED_KEEP:
                resolved.append(conflict)
                continue
            resolution = await self._llm_resolve(card, conflict)
            conflict.resolution = resolution
            conflict.user_intent = IntentFlag.PENDING
            resolved.append(conflict)
        return resolved

    async def _llm_resolve(self, card: Card, conflict: Conflict) -> str:
        if self._llm is None:
            from services.angela_llm_service import get_llm_service
            self._llm = await get_llm_service()
        if not self._llm.is_available:
            return f"LLM unavailable: {conflict.description}"
        prompt = (
            f"Card: {card.name} ({card.card_type.name})\n"
            f"Core trait: {card.core_trait}\n"
            f"Conflict type: {conflict.type.name}\n"
            f"Dimension: {conflict.dimension}\n"
            f"Description: {conflict.description}\n\n"
            f"Resolve this conflict in one short sentence:"
        )
        try:
            result = await self._llm.generate_text(prompt, max_tokens=100, temperature=0.3)
            return result if result else f"Default: {conflict.description}"
        except Exception as e:
            logger.warning(f"LLM resolve failed: {e}", exc_info=True)
            return f"Default: {conflict.description}"
```

**修改 `pipeline_orchestrator.py:53-54`** — 用 LLMBridge 替代 LLMFallback:
```python
# 替換
# self.llm_fallback = LLMFallback()
# 為
from core.card.resolver.llm_bridge import LLMBridge
self.llm_bridge = LLMBridge(llm_service=None)
```

**修改 `pipeline_orchestrator.py:85-86`** — 改為 async:
```python
# 替換
# card.conflicts = self.llm_fallback.resolve(card, remaining)
# 為
# 注意：需要將 process() 改為 async
card.conflicts = await self.llm_bridge.resolve_async(card, remaining)
```

> ⚠️ 這需要將 `CardImportPipeline.process()` 改為 `async def process()`，連帶影響 `run_card_import.py` 的調用方式。

#### 3.2.3 驗證 Phase 2

```bash
# 測試 LLMBridge
cd apps/backend && python -c "
import asyncio
from core.card.resolver.llm_bridge import LLMBridge
from core.card.card_types import Card, Conflict, ConflictType
bridge = LLMBridge(None)
card = Card(card_id='TEST-01', name='Test', core_trait='brave')
conflict = Conflict(type=ConflictType.HARD_ERROR, dimension='format', description='Invalid field format')
resolved = asyncio.run(bridge.resolve_async(card, [conflict]))
print(resolved[0].resolution)
"
```

---

### Phase 3: API 端點 + 進度追蹤

**目標**: 新增 REST API 端點觸發導入，非同步執行，支援進度查詢。

#### 3.3.1 新建 `core/card/integration/card_import_task.py`

> **設計選擇**: 專案已有 `asyncio.Queue` 模式在 `unified_control_center.py:50` 和 `feedback_processor.py:174`，以及 `HAMBackgroundTasks`（`ham_background_tasks.py`）。CardImportTaskManager 直接使用 `asyncio.create_task` 更輕量且足夠；若未來需要更複雜的佇列管理，可抽換為共用模式。

```python
"""
ANGELA-MATRIX: [L4] [β] [B] [L0]
CardImportTask — async task wrapper for CardImportPipeline.
Supports progress tracking via TaskProgress.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class TaskProgress:
    task_id: str
    status: str = "pending"  # pending | running | done | failed
    total: int = 0
    completed: int = 0
    errors: list = field(default_factory=list)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

class CardImportTaskManager:
    """Manages async card import tasks with progress tracking."""
    
    def __init__(self):
        self._tasks: Dict[str, TaskProgress] = {}
        self._counter = 0
    
    async def start_import(self, text: str, source_label: str = "api") -> str:
        task_id = f"import_{self._counter:04d}"
        self._counter += 1
        progress = TaskProgress(task_id=task_id, status="running", started_at=datetime.utcnow().isoformat())
        self._tasks[task_id] = progress
        asyncio.create_task(self._run_import(task_id, text, source_label))
        return task_id
    
    async def _run_import(self, task_id: str, text: str, source_label: str):
        try:
            from core.card.resolver.pipeline_orchestrator import CardImportPipeline
            from core.card.card_store import CardRegistry
            from core.interfaces.service_registry import get_registry
            
            registry = get_registry().get("card_registry") or CardRegistry()
            pipeline = CardImportPipeline(registry=registry)
            
            progress = self._tasks[task_id]
            progress.total = 1
            
            result = pipeline.process(text, source_label=source_label)
            progress.completed = 1
            
            if result.card and result.card.card_id:
                progress.status = "done"
                progress.result = {
                    "card_id": result.card.card_id,
                    "qualified_id": result.card.qualified_id,
                    "name": result.card.name,
                    "stage": result.stage,
                    "confidence": result.confidence,
                    "conflicts_resolved": result.conflicts_resolved,
                    "conflicts_total": result.conflicts_total,
                }
                get_registry().register("card_registry", registry)
            else:
                progress.status = "failed"
                progress.errors.append("No card could be parsed from input")
        except Exception as e:
            self._tasks[task_id].status = "failed"
            self._tasks[task_id].errors.append(str(e))
            logger.error(f"Import task {task_id} failed: {e}", exc_info=True)
        finally:
            self._tasks[task_id].finished_at = datetime.utcnow().isoformat()
    
    def get_progress(self, task_id: str) -> Optional[TaskProgress]:
        return self._tasks.get(task_id)

# Global instance
_task_manager = None
def get_card_import_task_manager():
    global _task_manager
    if _task_manager is None:
        _task_manager = CardImportTaskManager()
    return _task_manager
```

#### 3.3.2 新建 API 端點

**新建文件** `apps/backend/src/api/v1/endpoints/card_import.py`:
```python
"""Card Import API endpoints — import cards via ChatService or direct text."""
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any

router = APIRouter(prefix="/cards", tags=["Card Import"])

@router.post("/import")
async def import_card(
    request: Dict[str, Any] = Body(...),
):
    """Import a card from text description. Returns task_id for progress polling."""
    text = request.get("text", "")
    source = request.get("source", "api")
    if not text or len(text) < 10:
        raise HTTPException(status_code=400, detail="Text too short")
    from core.card.integration.card_import_task import get_card_import_task_manager
    mgr = get_card_import_task_manager()
    task_id = await mgr.start_import(text, source_label=source)
    return {"task_id": task_id, "status": "running"}

@router.get("/import/{task_id}")
async def get_import_progress(task_id: str):
    """Get import task progress."""
    from core.card.integration.card_import_task import get_card_import_task_manager
    mgr = get_card_import_task_manager()
    progress = mgr.get_progress(task_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": progress.task_id,
        "status": progress.status,
        "total": progress.total,
        "completed": progress.completed,
        "errors": progress.errors,
        "result": progress.result,
        "started_at": progress.started_at,
        "finished_at": progress.finished_at,
    }

@router.get("/registry")
async def get_card_registry():
    """Get all cards in registry."""
    from core.interfaces.service_registry import get_registry
    registry = get_registry().get("card_registry")
    if not registry:
        return {"cards": [], "count": 0}
    cards = registry.list_all()
    return {
        "count": len(cards),
        "cards": [
            {
                "qualified_id": c.qualified_id,
                "name": c.name,
                "card_type": c.card_type.name if c.card_type else None,
                "world_line": c.world_line,
                "stage": getattr(c, "_stage", None),
            }
            for c in cards
        ],
    }
```

**修改 `api/v1/endpoints/__init__.py`** — 註冊新路由：
```python
# 在 include_endpoint_routers() 中新增
from .card_import import router as card_import_router
router.include_router(card_import_router)
```

#### 3.3.3 驗證 Phase 3

```bash
# 測試任務管理器
cd apps/backend && python -c "
import asyncio
from core.card.integration.card_import_task import get_card_import_task_manager
mgr = get_card_import_task_manager()
task_id = asyncio.run(mgr.start_import('角色卡 CC-99 測試角色\n世界線: W01\n姓名: 測試者\n核心特質: 勇敢'))
print(f'Task: {task_id}')
import time; time.sleep(0.5)
progress = mgr.get_progress(task_id)
print(progress)
"
```

---

### Phase 4: 學習閉環

**目標**: 將卡片導入質量反饋回 `ConfigLoader.learn()`，讓系統自動調整意圖檢測和路由策略。

#### 3.4.1 在 ImportPipeline 成功後調用 config_loader.learn()

**修改 Phase 1 的 `_handle_card_import_intent()`** — 在成功導入後新增：
```python
# 在 return 之前新增學習閉環
try:
    from core.config_loader import get_angela_config
    cfg = get_angela_config()
    # 1. 記錄意圖模式
    cfg.learn("intent_pattern", {
        "intent": "character_card",
        "keywords": [text[:50]],
    })
    # 2. 如果走了 Stage 3，記錄路由結果
    if result.stage == "llm":
        cfg.learn("route_success" if result.conflicts_resolved > 0 else "route_fail", {
            "provider": "card_import_pipeline",
            "intent": "character_card",
            "latency_ms": 0,
        })
    # 3. 根據置信度調整閾值
    if result.confidence < 0.5:
        cfg.learn("threshold_adjust", {
            "metric": "card_import_confidence",
            "value": result.confidence,
        })
except Exception:
    pass
```

#### 3.4.2 在 wiring 中預先註冊服務

**修改 `services/wiring.py`** — 在 `initialize_all_services()` 結尾（第 107 行之前）新增。注意：`README.md` 已確認 `services/wiring.py` 是正確的 startup DI 注入點。
```python
# CardRegistry — 在 startup 中註冊，確保 Pipeline 和 API 端點可用
try:
    from core.card.card_store import CardRegistry
    from core.interfaces.service_registry import get_registry
    if get_registry().get("card_registry") is None:
        get_registry().register("card_registry", CardRegistry())
        logger.info("[Lifecycle] CardRegistry initialized in wiring")
except Exception as e:
    logger.warning(f"[Lifecycle] CardRegistry init failed: {e}", exc_info=True)
```

> **注意**: 選擇 `wiring.py` 而非 `lifespan.py`，因為 `wiring.py` 是預設的 DI 注入點。`lifespan.py` 的 service preinit loop（`lifespan.py:168-228`）結構不同，不適合插入 CardRegistry 初始化。

#### 3.4.3 驗證 Phase 4

```bash
# 測試學習閉環
cd apps/backend && python -c "
from core.config_loader import get_angela_config
cfg = get_angela_config()
result = cfg.learn('intent_pattern', {
    'intent': 'character_card',
    'keywords': ['導入測試角色卡'],
})
print(f'Learn result: {result}')
stats = cfg.get_learned_stats()
print(f'Stats: {stats}')
"
```

---

## 4. 架構圖（ASCII）

```
                                  ┌──────────────────────┐
                                  │    User / API Call    │
                                  └──────────┬───────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  IntentRegistry  │
                                    │  .detect(text)   │
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │ "character_card"       │ "general" / other      │
                    ▼                        ▼                        │
           ┌──────────────────┐   ┌──────────────────┐               │
           │CardImportPipeline│   │AngelaLLMService  │               │
           │                  │   │.generate_response│               │
           │ Stage 1: Auto    │   └────────┬─────────┘               │
           │  Parse / Merge   │            │                          │
           │  / Detect        │            ▼                          │
           │        │         │   ┌──────────────────┐               │
           │ Stage 2: Angela  │   │ P0-2 Template    │               │
           │  TextGravity     │   │ Matcher          │               │
           │  HAM Retrieve    │   └────────┬─────────┘               │
           │        │         │            │                          │
           │ Stage 3: LLM     │            ▼                          │
           │  LLMBridge       │   ┌──────────────────┐               │
           │  (真實 LLM)      │   │ Memory Retrieval │               │
           └────────┬─────────┘   │ (HAM)            │               │
                    │             └────────┬─────────┘               │
                    ▼                      ▼                         │
           ┌─────────────────────────────────────────┐               │
           │         Post-Processing Pipeline         │               │
           │                                          │               │
           │  ┌──────────────┐  ┌──────────────────┐  │               │
           │  │MemoryAdapter │  │PersonalityAdapter │  │               │
           │  │.store_card() │  │.load_card()      │  │               │
           │  └──────┬───────┘  └────────┬─────────┘  │               │
           │         │                    │             │               │
           │         ▼                    ▼             │               │
           │  ┌──────────────┐  ┌──────────────────┐  │               │
           │  │HAMMemoryMgr  │  │PersonalityManager │  │               │
           │  │store_exp()   │  │apply_adjustment() │  │               │
           │  └──────────────┘  └──────────────────┘  │               │
           │                                          │               │
           │  ┌────────────────────────────────────┐  │               │
           │  │ ConfigLoader.learn()               │  │               │
           │  │  intent_pattern / route_success    │  │               │
           │  │  threshold_adjust                  │  │               │
           │  └────────────────────────────────────┘  │               │
           └─────────────────────────────────────────┘               │
                                             │                        │
                                    ┌────────▼────────┐               │
                                    │  Response to     │               │
                                    │  User            │               │
                                    └─────────────────┘               │
                                             ▲                        │
                                             └────────────────────────┘
```

---

## 5. 依賴關係

| Phase | 依賴 | 需要先完成 |
|-------|------|-----------|
| Phase 1 | 無 | — |
| Phase 2 | Phase 1 (IntentRegistry + ChatService 分支) | 確保分發路徑正確 |
| Phase 3 | Phase 1, Phase 2 | API 端點需要 pipeline 可用 |
| Phase 4 | Phase 1, Phase 2 | 學習閉環需要 pipeline 結果數據 |

---

## 6. 風險評估

| # | 風險 | 影響 | 概率 | 緩解措施 |
|---|------|------|------|---------|
| R1 | `CardImportPipeline.process()` 是同步方法，調用真實 LLM 後需改為 async | 需要修改 pipeline 和所有調用方 | 高 | 新增 `async_process()` 方法保持向後兼容，同時逐步棄用同步 `process()` |
| R2 | `HAMMemoryManager` 初始化需要加密金鑰和 ChromaDB | 如果環境缺少依賴，記憶功能降級 | 中 | `MemoryAdapter` 應捕獲 ImportError 優雅降級 |
| R3 | 大文本導入（>10K tokens）阻塞事件循環 | 使用者體驗下降 | 中 | Phase 3 的 TaskManager 使用 `asyncio.create_task` 避免阻塞 |
| R4 | `PersonalityManager.apply_personality_adjustment()` 不存在或介面不同 | 裝載失敗 | 低 | 程式碼審計確認 `personality_adapter.py:51` 呼叫此方法。如果運行時缺失，PersonalityAdapter 有 try/except |
| R5 | `LLMFallback` 被其他地方直接 import 使用 | 替換後遺漏 import | 低 | `__all__` 和 import 分析確認僅 `pipeline_orchestrator.py.py` 使用 |
| R6 | YAML 和 hardcoded fallback 的 `character_card` keywords 不全 | 部分中文意圖無法捕獲 | 低 | Existing fallback + `learn()` 自動補充，Phase 1.1 後 ChatService 會使用 IntentRegistry |

---

## 7. 驗證策略

### 7.1 自動化測試

```bash
# Phase 1 驗證
pytest tests/core/test_intent_registry.py -v -k "character_card"

# Phase 2 驗證
pytest tests/core/card/test_pipeline_orchestrator.py -v

# Phase 3 驗證
cd apps/backend && python -m pytest tests/api/test_card_import.py -v

# 全量回歸
cd apps/backend && pytest tests/ -v --cov=core/card --cov=services/chat_service
```

### 7.2 手動測試序列

```bash
# 1. 啟動服務並測試 API 導入
cd apps/backend && python -m uvicorn services.main_api_server:app --reload

# 2. 透過 API 導入卡片
curl -X POST http://localhost:8000/api/v1/cards/import \
  -H "Content-Type: application/json" \
  -d '{"text": "角色卡 CC-TEST-01\n世界線: W01\n姓名: 測試用角色\n核心特質: 好奇心旺盛\n性格: 開朗, 直率\n背景: 來自遙遠星系的探險家"}'

# 3. 查詢導入進度
curl http://localhost:8000/api/v1/cards/import/import_0000

# 4. 通過聊天導入
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "幫我導入一個角色卡 CC-42，世界線 W01，勇敢的戰士"}]}'

# 5. 查詢 registry 狀態
curl http://localhost:8000/api/v1/cards/registry
```

---

## 8. 檔案修改摘要

| 操作 | 檔案 | 說明 |
|------|------|------|
| **修改** | `chat_service.py:155-167` | 替換 `_analyze_intent()` 使用 IntentRegistry |
| **修改** | `chat_service.py:122-127` | 新增 `character_card` 意圖分支 |
| **新增** | `chat_service.py` (約第 276 行後) | 新增 `_handle_card_import_intent()` 方法 |
| **修改** | `intent_registry.py:79` | Fallback 模式補上 character_card 條目 |
| **修改** | `pipeline_orchestrator.py:46-54` | 建構子新增 `ham_manager` 參數 |
| **修改** | `pipeline_orchestrator.py:53` | 用 `LLMBridge` 替代 `LLMFallback` |
| **修改** | `pipeline_orchestrator.py:85` | process() 改為 async + 使用 LLMBridge |
| **新增** | `core/card/resolver/llm_bridge.py` | 真實 LLM 裁決橋接器 |
| **新增** | `core/card/integration/card_import_task.py` | 異步任務管理 + 進度追蹤 |
| **新增** | `api/v1/endpoints/card_import.py` | 卡片導入 REST API 端點 |
| **修改** | `api/v1/endpoints/__init__.py` | 註冊 card_import 路由 |
| **修改** | `api/lifespan.py` (約第 191 行) | 預初始化 CardRegistry |
| 不修改 | `memory_adapter.py` | 已正確實作，僅需傳入 ham_manager |
| 不修改 | `personality_adapter.py` | 已正確實作，僅需傳入 personality_manager |
| 不修改 | `config_loader.py` | learn() 已支援所需事件類型 |
| 不修改 | `ham_manager.py` / `ham_query_engine.py` | API 已完備，直接調用即可 |

---

## 附錄: 關鍵代碼路徑對照

```
聊天導入流程:
  POST /api/v1/chat/completions
    → api/router.py:168 chat_completions()
    → services/chat_service.py:102 generate_response()
    → chat_service.py:116 _analyze_intent()
    → core/intent_registry.py:106 detect()
    → [character_card detected]
    → chat_service.py:[new] _handle_card_import_intent()
    → core/card/resolver/pipeline_orchestrator.py:56 process()
    → core/card/integration/memory_adapter.py:34 store_card()
    → ai/memory/ham_memory/ham_manager.py:128 store_experience()
    → core/card/integration/personality_adapter.py:33 load_card()
    → core/config_loader.py:285 learn()

API 導入流程:
  POST /api/v1/cards/import
    → api/v1/endpoints/card_import.py:[new] import_card()
    → core/card/integration/card_import_task.py:[new] start_import()
    → core/card/resolver/pipeline_orchestrator.py:56 process()
    → (同上後續流程)

三級分發路徑:
  CardImportPipeline.process()
    Stage 1: DeterministicParser → MergeEngine → ConflictDetector → TimelineResolver
      → confidence >= 0.85? → _finalize("auto")
    Stage 2: TextGravityField + TokenExtractor + HAM retrieve
      → conflicts remaining? and confidence >= 0.70? → _finalize("angela")
    Stage 3: LLMBridge.resolve_async() → AngelaLLMService.generate_text()
      → _finalize("llm")
```
