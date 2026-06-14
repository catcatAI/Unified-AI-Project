# 聊天管線完整架構重構計劃 v8

**日期:** 2026-06-14
**基於:** 9 個代理完整代碼審計（服務、前端、自主認知、API、ED3N、重複分析、調用者映射、路由架構、功能重複深度分析）
**目標:** 全面消除重複（保留 backward-compatible shims）+ 擴展 QueryClassifier + ED3N 適當整合 + 完整管線
**狀態:** 規劃階段

---

## 一、功能重複全面分析

### 1.1 文字處理重複

#### DUP-1: `_extract_keywords()` — 5 個獨立實作

| # | 位置 |发法 | stopwords | 最大數 | 語言 |
|---|------|------|-----------|--------|------|
| A | `template_matcher.py:258` | 逐字元拆分 | 15 個 | 無限 | 中文 |
| B | `ham_manager.py:128` | dict/str 混合 | 16 個（含英文） | 8 | 中英 |
| C | `router.py:1202` | regex 2+ 字元 | 13 個 | 5 | 中英 |
| D | `composer.py:307` | regex 2+ 字元 | 12 個 | 無限 | 中文 |
| E | `document_builder.py:199` | regex `\w` 變體 | 26 個（最多） | 無限 | 中英 |
| F | `ai_editor.py:100` | `text.split()[:5]` | 無 | 5 | **壞掉** |

**判斷:** 應合併。E 的 stopwords 最完整，C 的 regex 最好。合併為一個共用函數。
**調用者:** A(1), B(1), C(1), D(1), E(2) = 6 個調用者需要更新
**向後兼容:** 保留原方法，改為轉接到共用函數

```python
# 合併後
# utils/text_utils.py
def extract_keywords(text, max_keywords=8, stopwords=None):
    """統一關鍵字提取（中英文）"""
    if stopwords is None:
        stopwords = DEFAULT_STOPWORDS  # 合併所有版本
    words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}', text)
    return [w for w in words if w not in stopwords][:max_keywords]

# 各文件保留原方法作為轉接
# template_matcher.py
def _extract_keywords(self, text):
    from utils.text_utils import extract_keywords
    return extract_keywords(text, max_keywords=999, stopwords=TM_STOPWORDS)

# ham_manager.py
def _extract_keywords(self, raw_data):
    from utils.text_utils import extract_keywords
    if isinstance(raw_data, dict):
        text = " ".join(str(v) for v in raw_data.values())
    elif not isinstance(raw_data, str):
        text = str(raw_data)
    else:
        text = raw_data
    return extract_keywords(text, max_keywords=8)
```

#### DUP-2: `_char_bigrams()` — 2 個完全相同的實作

| # | 位置 | 實作 |
|---|------|------|
| A | `template_matcher.py:364` | `{text[i:i+2] for i in range(len(text) - 1)}` |
| B | `ham_manager.py:95` | 同上 + `len < 2` guard |

**判斷:** 應合併。B 有 edge-case guard，更完整。
**調用者:** A(5 內部), B(2 內部) = 7 個調用者
**向後兼容:** 保留原方法，轉接到共用函數

#### DUP-3: Bigram Jaccard 公式 — 2 個相同公式

| # | 位置 | 公式 |
|---|------|------|
| A | `ham_manager.py:86` | `min(0.95, jaccard * 1.2)` |
| B | `template_matcher.py:360` | 同上 |

**判斷:** 應合併到共用函數 `bigram_jaccard(text_a, text_b)`。
**調用者:** A(1), B(1) = 2 個

#### DUP-4: `_normalize_text()` — 1 個實作，應提取共用

| # | 位置 | 功能 |
|---|------|------|
| A | `template_matcher.py:245` | lowercase + 去空格標點 |

**判斷:** 應提取到共用函數，讓其他 `_extract_keywords` 也能用。

---

### 1.2 Config 系統重複

#### DUP-5: 4 個 Config 系統

| # | 位置 | 系統 | 調用者數 |
|---|------|------|----------|
| A | `config_loader.py:19` | `AngelaConfig` singleton, `get_authority()` | 17+ |
| B | `tiered_loader.py:142` | `get_config()`, 3 層合併 | 13+ |
| C | `app_config_loader.py:24` | `get_config()` 硬編碼 dict | 9+ |
| D | `fallback_config_loader.py:13` | HSP 專用 | 1 |

**判斷:**
- A 和 B 有相同函數名 `get_config` 但不同語義（dotted key vs slash path）
- **合併 A 到 B** — B 更完整（3 層合併、快取）。A 的 `get_authority()` 成為 B 的方法
- **棄用 C** — 硬編碼值，調用者遷移到 B
- **保留 D** — HSP 專用，只有 1 個調用者

**調用者:** A(17+), B(13+), C(9+) = 39+ 個調用者需要遷移
**向後兼容:** 保留 `get_angela_config()` 和 `get_config()` 作為轉接

```python
# config_loader.py — 保留為轉接
def get_angela_config():
    from core.system.config.tiered_loader import get_config
    return get_config("angela")  # 轉接到 tiered_loader

def get_authority(section, default=None):
    from core.system.config.tiered_loader import get_config
    return get_config(f"authority/{section}") or default
```

---

### 1.3 情緒系統重複

#### DUP-6: 4 個情緒系統

| # | 位置 | 類別 | 用途 | 調用者 |
|---|------|------|------|--------|
| A | `emotion_analyzer.py:16` | `EmotionAnalyzer` | 關鍵字中文情緒 | 2 |
| B | `emotion_system.py:74` | `EmotionSystem` | 價值評估+同理心 | 3 |
| C | `emotional_blending.py:197` | `EmotionalBlendingSystem` | PAD 生理模型 | 1 |
| D | `user_monitor.py:289` | `_extract_emotion_keywords()` | 用戶情緒追蹤 | 1 |

**判斷:**
- **保留 A** — 對話層情緒分析（最常用）
- **保留 B** — ASI 對齊層（不同抽象層）
- **保留 C** — 生理模擬層（不同抽象層）
- **合併 D 到 A** — D 是 A 的子集，UserMonitor 應委託給 EmotionAnalyzer

**向後兼容:** D 保留原方法，轉接到 A

---

### 1.4 記憶系統重複

#### DUP-7: 記憶類型定義重複

| # | 位置 | 定義 |
|---|------|------|
| A | `ham_memory/ham_types.py:28` | `HAMRecallResult` |
| B | `memory/types.py:28` | `HAMRecallResult` |
| C | `shared/types/common_types.py:174` | `HAMRecallResult` |

**判斷:** 合併到 B（`memory/types.py`），A 和 C 轉接到 B。

#### DUP-8: 錯誤類型重複

| # | 位置 | 定義 |
|---|------|------|
| A | `ham_memory/ham_types.py:36` | `HAMMemoryError` |
| B | `ham_memory/ham_errors.py:5` | `HAMMemoryError` |

**判斷:** 合併到 A，B 轉接到 A。

#### DUP-9: `HAMMemoryManager` 孤立實作

| # | 位置 | 狀態 |
|---|------|------|
| A | `ham_memory/ham_manager.py:14` | 真實實作 |
| B | `ai_editor.py:17` | Mock/stub，已棄用 |

**判斷:** 刪除 B（已棄用）。

---

### 1.5 狀態管理重複

#### DUP-10: 狀態管理系統重複

| # | 位置 | 類別 | 用途 |
|---|------|------|------|
| A | `state_matrix.py:58` | `StateMatrix4D` | 6D 狀態，1439 行 |
| B | `global_store.py:18` | `GlobalStateStore` | 領域+pub/sub |
| C | `state_persistence.py:79` | `StatePersistence` | Redis/JSON 持久化 |
| D | `state_manager.py:1` | `StateManager` | **空殼**（3 行） |

**判斷:**
- **合併 B 到 A** — A 更完整。B 成為 A 的 facade
- **合併 C 到 B** — 持久化統一
- **刪除 D** — 空殼

---

### 1.6 路由系統重複

#### DUP-11: 路由系統重複

| # | 位置 | 類別 | 狀態 |
|---|------|------|------|
| A | `hybrid_router.py:69` | `HybridRouter` | **已棄用**（自註） |
| B | `model_bus.py:45` | `ModelBus` | 活躍 |
| C | `language_models/router.py:124` | `PolicyRouter` | 活躍（不同域） |
| D | `theta_router.py:99` | `ThetaRouter` | 活躍（不同域） |

**判斷:** 刪除 A（已棄用）。保留 B, C, D（不同路由層）。

---

### 1.7 錯誤處理重複

#### DUP-12: 2 個錯誤階層

| # | 位置 | 系統 |
|---|------|------|
| A | `angela_error.py:47` | `AngelaError`（15+ 子類） |
| B | `shared/error.py:1` | `ProjectError`（4 子類） |
| C | `mcp/connector.py:20` | `ProjectError` 本地 mock |

**判斷:** 合併 B 到 A。刪除 C（mock）。

---

### 1.8 棄用/空殼代碼

#### DUP-13: 棄用代碼

| # | 位置 | 說明 |
|---|------|------|
| A | `ai/garden/hybrid_router.py` | 自註棄用，被 ModelBus 取代 |
| B | `services/ai_editor.py` | P8-2 棄用 |
| C | `core/state_manager.py` | 3 行空殼 |
| D | `core/degraded_mode.py` | 5 行空殼 |
| E | `mcp/connector.py::ProjectError` | 本地 mock |

**判斷:** 全部刪除。

---

### 1.9 Singleton 模式不一致

#### DUP-14: 8+ 種 singleton 實現

| # | 位置 | 模式 |
|---|------|------|
| A | `biological_integrator.py:139` | `__new__` override |
| B | `config_loader.py:63` | Module-level getter |
| C | `waiting_scheduler.py:49` | Module-level getter |
| D | `lifespan.py:27` | Module-level globals |
| E | `state_matrix_api.py:41` | Module-level getter |
| F | `hot_reload_service.py:26` | Module-level getter |
| G | `art_learning_workflow.py:195` | Module-level getter |
| H | `google_drive_service.py:297` | Module-level getter |

**判斷:** 標準化為 module-level getter 模式（最常見）。可選：建立 `@singleton` 裝飾器。

---

### 1.10 Cosine Similarity 重複

#### DUP-15: 3 個 cosine 實現

| # | 位置 | 輸入類型 |
|---|------|----------|
| A | `composer.py:1086` | `List[float]` |
| B | `ham_utils.py:63` | `np.ndarray` |
| C | `err_introspector.py:120` | `Dict[str, float]` |

**判斷:** 保留分離 — 不同數據類型，強行合併會增加複雜度。

---

### 1.11 `get_biological_state` 命名混淆

#### DUP-16: 2 個同名不同函數

| # | 位置 | 返回 | 用途 |
|---|------|------|------|
| A | `prompt_builder.py:26` | `str` | prompt 格式化 |
| B | `biological_integrator.py:559` | `Dict` | 原始數據 |

**判斷:** 重命名 A 為 `format_bio_state_for_prompt()`。保留 B 不變。

---

## 二、共用工具提取計劃

### 2.1 建立 `utils/text_utils.py`

```python
"""共用文字處理工具 — 消除重複實作"""

import re
from typing import List, Set, Optional

# 合併所有版本的 stopwords
DEFAULT_STOPWORDS = {
    # 中文
    "你", "我", "他", "她", "的", "了", "嗎", "呢", "吧", "啊", "是",
    "在", "有", "和", "就", "不", "也", "這", "那", "什麼", "怎麼",
    "可以", "沒有", "一個", "我們", "他們", "如果", "但是", "因為",
    # 英文
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "i", "you", "he", "she",
    "it", "we", "they", "me", "him", "her", "us", "them", "my", "your",
    "his", "its", "our", "their", "this", "that", "these", "those",
}

def char_bigrams(text: str) -> set:
    """字元級 bigram，用於中文相似度"""
    if len(text) < 2:
        return {text} if text else set()
    return {text[i:i+2] for i in range(len(text) - 1)}

def bigram_jaccard(text_a: str, text_b: str) -> float:
    """Bigram Jaccard 相似度（含 1.2x 縮放和 0.95 上限）"""
    a, b = char_bigrams(text_a), char_bigrams(text_b)
    if not a or not b:
        return 0.0
    jaccard = len(a & b) / len(a | b)
    return min(0.95, jaccard * 1.2)

def extract_keywords(
    text: str,
    max_keywords: int = 8,
    stopwords: Optional[Set[str]] = None,
) -> List[str]:
    """統一關鍵字提取（支持中英文）"""
    if stopwords is None:
        stopwords = DEFAULT_STOPWORDS
    words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}', text)
    return [w for w in words if w not in stopwords][:max_keywords]

def normalize_text(text: str) -> str:
    """文字標準化：lowercase + 去標點空格"""
    text = text.lower()
    for ch in [" ", "?", "!", "。", "？", "！", "，", ","]:
        text = text.replace(ch, "")
    return text
```

### 2.2 各文件向後兼容轉接

```python
# template_matcher.py
from utils.text_utils import char_bigrams as _char_bigrams_util
from utils.text_utils import bigram_jaccard as _bigram_jaccard_util
from utils.text_utils import extract_keywords as _extract_keywords_util
from utils.text_utils import normalize_text as _normalize_text_util

class TemplateMatcher:
    @staticmethod
    def _char_bigrams(text):
        return _char_bigrams_util(text)
    
    def _calculate_similarity(self, user_input, template):
        user_lower = _normalize_text_util(user_input)
        # ... 其餘邏輯不變，改用 _bigram_jaccard_util
    
    def _extract_keywords(self, text):
        return _extract_keywords_util(text, max_keywords=999, stopwords=TM_STOPWORDS)

# ham_manager.py
from utils.text_utils import char_bigrams as _char_bigrams_util
from utils.text_utils import bigram_jaccard as _bigram_jaccard_util
from utils.text_utils import extract_keywords as _extract_keywords_util

class HAMMemoryManager:
    @staticmethod
    def _char_bigrams(text):
        return _char_bigrams_util(text)
    
    def _extract_keywords(self, raw_data):
        if isinstance(raw_data, dict):
            text = " ".join(str(v) for v in raw_data.values())
        elif not isinstance(raw_data, str):
            text = str(raw_data)
        else:
            text = raw_data
        return _extract_keywords_util(text, max_keywords=8)

# router.py
from utils.text_utils import extract_keywords as _extract_keywords_util

class AngelaLLMService:
    def _extract_keywords(self, text):
        return _extract_keywords_util(text, max_keywords=5)

# composer.py
from utils.text_utils import extract_keywords as _extract_keywords_util

class ResponseComposer:
    def _extract_keywords(self, text):
        return _extract_keywords_util(text, max_keywords=999)
```

---

## 三、ED3N 適當使用分析

### 3.1 ED3N 各能力品質評估

| 能力 | 方法 | 品質 | 速度 | 適合用途 |
|------|------|------|------|----------|
| 快速反射 | `process_reflex()` | ⭐⭐⭐⭐⭐ | <1ms | 問候、固定回覆、timeout fallback |
| 字典模糊匹配 | `encode_soft()` | ⭐⭐⭐ | <5ms | 意圖輔助分類、歷史相關性 |
| 字典精確匹配 | `encode()` | ⭐⭐ | <1ms | 歷史 key overlap（已用） |
| 淺層處理 | `process_shallow()` | ⭐⭐⭐ | ~10ms | 回應生成（無 LLM 時） |
| 多模態編碼 | `process_multimodal()` | ⭐⭐⭐ | ~50ms | 圖片/音訊→keys |
| 持續學習 | `process_interaction()` | ⭐⭐ | async | 長期字典成長 |
| 深層處理 | `process_deep()` | ⭐⭐⭐ | ~100ms | 複雜回應（不常用） |
| 訓練 | `train()` | ⭐⭐ | 批次 | 批次學習 |

### 3.2 ED3N 應該用的地方

| 用途 | 方法 | 為什麼 | 調用者 |
|------|------|--------|--------|
| Session 歡迎 | `process("welcome", depth="reflex")` | 亚毫秒 | chat_routes.py |
| Timeout fallback | `process("timeout_response", depth="reflex")` | 安全網 | chat_routes.py |
| Cancelled fallback | `process("timeout_response", depth="reflex")` | 安全網 | chat_routes.py |
| 主動互動 | `process("welcome_back"\|"idle_check", depth="reflex")` | 預設 | proactive_interaction |
| Composer fallback | `process("compose_fallback", depth="shallow")` | 後備 | composer.py |
| ModelBus reflex 層 | `process()` via ModelBus | 快速路由 | model_bus.py |
| 歷史相關性 | `dictionary.encode()` | key overlap | chat_routes.py |
| 意圖輔助 | `dictionary.encode_soft()` | 模糊匹配 | query_classifier |
| 持續學習 | `process_interaction()` | 字典成長 | chat_service.py |
| HAM 同步 | `ED3NLearningIntegration` | 知識轉移 | learning_integration.py |

### 3.3 ED3N 不應該用的地方

| 用途 | 為什麼 | 替代方案 |
|------|--------|----------|
| 情緒分析 | 無情緒模型 | EmotionAnalyzer |
| 語義理解 | 無 embedding | LLM 直接處理 |
| 因果推理 | 無因果模型 | CausalReasoningEngine |
| 知識問答 | 字典有限 | GARDEN + Cloud |
| 複雜指令 | reflex 太簡單 | LLM + handlers |
| 圖片分析 | 多模態是 bolt-on | VisionService |

### 3.4 ED3N bug 修復

**`_ed3n_fallback_text` 每次建立新實例:**
```python
# router.py:1227 — 現狀
engine = ED3NEngine()  # 每次 fallback 都新建

# 修復: 重用 ModelBus 中的實例
engine = self.model_bus._registry.get("ed3n", (None,))[0]
if engine is None:
    engine = ED3NEngine()
```

**Composer 每次 fallback 建立 4 個新實例:**
```python
# composer.py:345,903,1126,1156 — 現狀
_ED3NEngine().process(...)  # 每次新建

# 修復: 建立模組級快取
_ed3n_engine = None
def _get_ed3n():
    global _ed3n_engine
    if _ed3n_engine is None:
        from ai.ed3n.ed3n_engine import ED3NEngine
        _ed3n_engine = ED3NEngine()
        _ed3n_engine.load_presets()
    return _ed3n_engine
```

---

## 四、QueryClassifier 擴展

### 4.1 新增 QueryTypes

```python
class QueryType(Enum):
    # 現有
    REFLEX = "reflex"
    GREETING = "greeting"
    MATH = "math"
    LOGIC = "logic"
    KNOWLEDGE = "knowledge"
    CREATIVE = "creative"
    OPINION = "opinion"       # 需補 patterns
    COMMAND = "command"
    UNKNOWN = "unknown"
    # 新增
    FILE = "file"             # 檔案操作
    SEARCH = "search"         # 搜尋
    CODE = "code"             # 程式碼
    EXECUTE = "execute"       # 系統執行
    TASK = "task"             # 任務管理
    VISION = "vision"         # 圖片分析
    AUDIO = "audio"           # 音訊處理
```

### 4.2 ED3N 作為輔助分類信號

```python
def classify(self, text):
    # 1. Regex 分類
    regex_type, regex_conf = self._regex_classify(text)
    
    # 2. ED3N 作為第二信號
    try:
        keys = self._ed3n.dictionary.encode_soft(text)
        ed3n_type, ed3n_conf = self._keys_to_intent(keys)
        if ed3n_conf > regex_conf:
            return ed3n_type, ed3n_conf
    except Exception:
        pass
    
    return regex_type, regex_conf
```

---

## 五、ModelBus 擴展

### 5.1 Handler 註冊機制

```python
class ModelBus:
    def __init__(self):
        self._registry = {}      # LLM backends
        self._handlers = {}      # Non-LLM handlers
        self._handler_map = {}   # intent_type → handler_id
    
    def register_handler(self, handler_id, handler, intent_types):
        """註冊 handler（file, drive, search 等）"""
        self._handlers[handler_id] = handler
        for t in intent_types:
            self._handler_map[t] = handler_id
```

### 5.2 路由擴展

```python
def route(self, text, query_type="auto", context=None):
    # ... 現有分類 ...
    
    # 新增: handler 類型直接派發
    if query_type in self._handler_map:
        handler_id = self._handler_map[query_type]
        return RouteDecision(
            action=RouteAction.EXECUTE,
            engine=self._handlers[handler_id],
            confidence=0.9,
        )
    
    # ... 現有 LLM 路由 ...
```

### 5.3 提升為主要路由

```python
# router.py generate_response() — 改進
async def generate_response(self, user_message, context=None):
    # 1. Template match（現有）
    # 2. Memory retrieval（現有）
    
    # 3. 意圖分類 + 路由（提升為主要路徑）
    query_type, conf = self.query_classifier.classify(user_message)
    
    # Handler 路由
    if query_type in self.model_bus._handler_map:
        handler_id = self.model_bus._handler_map[query_type]
        handler = self.model_bus._handlers[handler_id]
        result = await handler.handle(query_type, {"text": user_message, "context": context})
        return LLMResponse(text=result.get("response_text", ""), ...)
    
    # LLM 路由
    return await self._generate_with_llm(user_message, context)
```

---

## 六、管線全貌（完成後）

### 6.1 完整流程圖

```
用戶輸入（文字/圖片/音訊/檔案）
    │
    ▼
[接入層] WebSocket Manager / HTTP Router / Session Manager
    │
    ▼
[輸入標準化] InputClassifier → {type: text|image|audio|file, data, metadata}
    │
    ▼
[意圖分類] QueryClassifier + ED3N encode_soft()（輔助）
    │  16 種意圖: REFLEX|GREETING|MATH|LOGIC|KNOWLEDGE|CREATIVE|
    │  OPINION|COMMAND|FILE|SEARCH|CODE|EXECUTE|TASK|VISION|AUDIO|UNKNOWN
    │
    ▼
[管線分派] ModelBus（提升為主要路由）
    │
    ├─ REFLEX/GREETING → ED3N process_reflex() → 直接回覆
    ├─ MATH → ED3N → GARDEN fallback
    ├─ FILE → FileOperationHandler → LLM 整理
    ├─ SEARCH → WebSearchHandler → LLM 整理
    ├─ CODE → CodeInspector → LLM 整理
    ├─ VISION → VisionService → LLM 整理
    ├─ AUDIO → AudioService → LLM 整理
    ├─ EXECUTE → DesktopInteraction → LLM 整理
    ├─ TASK → ProjectCoordinator → LLM 整理
    ├─ KNOWLEDGE → GARDEN → Cloud fallback
    ├─ CREATIVE → Cloud LLM
    ├─ 其他 → fan-out to all backends
    │
    ▼
[回應合成] ResponseComposer / NeuroBlender / DeviationTracker
    │
    ▼
[狀態更新] BiologicalIntegrator + StateMatrix4D + Neuroplasticity
    │
    ▼
[記憶存儲] HAMMemoryManager (fire-and-forget)
    │
    ▼
[自主認知] AutonomousLifeCycle 決策 → prompt_builder 讀取
    │
    ▼
回應 + Live2D 參數 + 生物回饋
```

### 6.2 各管線角色

| 管線 | 處理什麼 | 用什麼 | 不用什麼 |
|------|----------|--------|----------|
| Reflex | 問候、固定回覆 | ED3N reflex | LLM |
| Handler | 檔案/搜尋/執行 | 現有 handlers | ED3N |
| Vision | 圖片分析 | VisionService | ED3N |
| Audio | 音訊轉錄 | AudioService | ED3N |
| LLM | 一般對話 | QueryClassifier + ModelBus | ED3N（除 reflex fallback） |
| Autonomy | 自主決策 | AutonomousLifeCycle | ED3N |

---

## 七、實施順序

### Phase 1: 重複清理 + 向後兼容 (2-3 天)
1. 建立 `utils/text_utils.py`
2. 合併 `_extract_keywords` x5 → 1 個共用 + 5 個轉接
3. 合併 `_char_bigrams` x2 → 1 個共用 + 2 個轉接
4. 合併 bigram Jaccard x2 → 1 個共用 + 2 個轉接
5. 提取 `_normalize_text` 到共用
6. 合併情緒系統 D → A（UserMonitor 轉接到 EmotionAnalyzer）
7. 修復 ED3N 建立 bug（router + composer）
8. 刪除棄用代碼（hybrid_router, ai_editor mock, state_manager stub, degraded_mode stub）
9. 合併錯誤階層（ProjectError → AngelaError）
10. 重命名 `get_biological_state` → `format_bio_state_for_prompt`

### Phase 2: Config 系統合併 (1-2 天)
1. 合併 AngelaConfig 到 tiered_loader
2. 保留 `get_angela_config()` 和 `get_config()` 作為轉接
3. 棄用 app_config_loader，調用者遷移
4. 測試所有 config 調用者

### Phase 3: QueryClassifier 擴展 (1-2 天)
1. 新增 QueryTypes
2. 新增 patterns
3. 補充 OPINION patterns
4. ED3N encode_soft 作為輔助分類

### Phase 4: ModelBus 擴展 (1-2 天)
1. 新增 handler 註冊機制
2. 註冊 handlers
3. 路由擴展
4. 提升為主要路由

### Phase 5: 自主認知整合 (1-2 天)
1. prompt_builder 讀取自主決策
2. 公式實例共享
3. 動態 prompt

### Phase 6: 感知管線 (2-3 天)
1. 替換 vision/audio stub
2. 前端上傳
3. WebSocket 擴展

---

## 八、文件清單

### 需要新建
| 文件 | 功能 |
|------|------|
| `utils/text_utils.py` | 共用文字工具 |

### 需要修改（合併+轉接）
| 文件 | 修改 |
|------|------|
| `template_matcher.py` | 使用 text_utils，保留原方法轉接 |
| `ham_manager.py` | 使用 text_utils，保留原方法轉接 |
| `router.py` | 使用 text_utils，修復 ed3n bug |
| `composer.py` | 使用 text_utils，修復 ed3n 建立 |
| `document_builder.py` | 使用 text_utils |
| `emotion_analyzer.py` | 不變（singleton 化） |
| `user_monitor.py` | 轉接到 EmotionAnalyzer |
| `query_classifier.py` | 新增 types + patterns + ED3N |
| `model_bus.py` | 新增 handler 註冊 + 路由 |
| `prompt_builder.py` | 動態 prompt + 重命名 get_biological_state |
| `config_loader.py` | 轉接到 tiered_loader |
| `chat_routes.py` | singleton EmotionAnalyzer, InputClassifier |
| `vision.py` | 替換 stub |
| `audio.py` | 替換 stub |
| `websocket_manager.py` | 擴展訊息類型 |
| `angela_error.py` | 吸收 ProjectError |

### 需要刪除
| 文件 | 原因 |
|------|------|
| `ai/garden/hybrid_router.py` | 自註棄用 |
| `services/ai_editor.py` | P8-2 棄用 |
| `core/state_manager.py` | 空殼 |
| `core/degraded_mode.py` | 空殼 |
| `mcp/connector.py::ProjectError` | mock |
| `ham_memory/ham_errors.py` | 重複 |
| `ai/memory/types.py::HAMRecallResult` | 重複（保留 ham_types.py 版） |

### 需要保持不動
| 文件 | 原因 |
|------|------|
| `core/bio/*` | 已完整 |
| `ai/ed3n/*` | 已完整 |
| `ai/garden/*` | 已完整 |
| `ai/memory/*` | 已完整（除合併） |
| `ai/response/*` | 已完整（除合併） |
| `emotion_system.py` | 不同抽象層，保留 |
| `emotional_blending.py` | 不同抽象層，保留 |
| `cosine 相似度 x3` | 不同數據類型，保留分離 |
