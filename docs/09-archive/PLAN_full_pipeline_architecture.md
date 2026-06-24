# 聊天管線完整架構重構計劃 v10

**日期:** 2026-06-14
**基於:** 12 個代理完整代碼審計（含深度差異分析）
**目標:** 安全清理 + 擴展 QueryClassifier + ED3N 適當整合 + 完整管線
**狀態:** Phase 1-6 全部完成
**架構文件:** [完整架構圖](docs/architecture/ANGELA_FULL_ARCHITECTURE.md)

---

## 一、深度差異分析結論

### 1.1 「不能合併」的項目（之前誤判為重複）

#### `_extract_keywords` x5 — **保持分離**

| 差異 | 影響 |
|------|------|
| template_matcher/composer 用**逐字元拆分** → `["你","好","世","界"]` | regex 版本 → `["你好","世界"]` |
| document_builder 用**繁體中文** stopwords（`這, 與, 之, 於`） | 其他用**簡體**（`这, 与, 之, 于`） |
| composer **完全丟棄英文** | ham_manager 保留英文 |
| ham_manager **接受 dict 輸入** | 其他只接受 str |
| 大小寫敏感性不同 | ham_manager 用 `.lower()`，其他不用 |

**結論:** 每個版本的行為不同，調用者依賴特定行為。強行合併會破壞所有調用者。

#### Config 系統 x4 — **不是重複，是不同系統**

| 系統 | 載入什麼 | API | 數據結構 |
|------|----------|-----|----------|
| AngelaConfig | `src/config/*.yaml`（已棄用） | `get_authority()` + `learn()` | flat dict |
| tiered_loader | `apps/backend/configs/`（3 層合併） | `get_config(path)` | merged dict |
| app_config_loader | **無檔案，硬編碼** | `get_config(key)` | static dict |
| FallbackConfigLoader | `hsp_fallback_config.yaml` | 專用 API | HSP-specific |

**結論:** 不同目錄、不同 API、不同數據結構。不是重複。

#### 情緒系統 x4 — **保持分離**

| 系統 | 情緒標籤 | 算法 | 輸出格式 |
|------|----------|------|----------|
| EmotionAnalyzer | happy/sad/angry/fear/surprise/curious/calm | 關鍵字+權重+否定詞 | dict |
| UserMonitor | happy/sad/neutral/frustrated/excited/anxious/confused/relaxed | 簡單計數 | tuple |
| EmotionSystem | joy/trust/fear/surprise/sadness/disgust/anger/anticipation | 價值評估 | EmotionalState |
| EmotionalBlending | JOY/SADNESS/ANGER/FEAR/DISGUST/SURPRISE/TRUST/ANTICIPATION/LOVE/CALM | PAD 模型 | PADEmotion |

**結論:** 不同情緒標籤、不同算法、不同輸出格式、不同調用者。合併會破壞所有調用者。

#### Cosine Similarity x3 — **保持分離**

| 版本 | 輸入類型 | 用途 |
|------|----------|------|
| composer.py | `List[float]` | 向量相似度 |
| ham_utils.py | `np.ndarray` | NumPy 陣列 |
| err_introspector.py | `Dict[str, float]` | 字典稀疏向量 |

**結論:** 不同數據類型，強行合併會增加複雜度。

---

### 1.2 「可以安全清理」的項目

#### 棄用/空殼代碼 — **刪除**

| 文件 | 原因 |
|------|------|
| `ai/garden/hybrid_router.py` | 自註「已被 ModelBus 取代」 |
| `services/ai_editor.py` | P8-2 棄用，Mock stub |
| `core/state_manager.py` | 3 行空殼 |
| `core/degraded_mode.py` | 5 行空殼 |
| `mcp/connector.py::ProjectError` | 本地 mock 重定義 |

#### ED3N 建立 Bug — **修復**

| 位置 | 問題 | 修復 |
|------|------|------|
| `router.py:1227` | `_ed3n_fallback_text` 每次新建 ED3NEngine | 重用 ModelBus 中的實例 |
| `composer.py:345,903,1126,1156` | 每次 fallback 新建 ED3NEngine | 模組級快取 |

#### FallbackConfigLoader Bug — **修復**

| 位置 | 問題 | 修復 |
|------|------|------|
| `memory_template.py:262` | 呼叫 `FallbackConfigLoader.get_authority()` — 該方法不存在 | 改用 `get_angela_config()` |

#### 情緒關鍵字重複 — **提取共用常數**

| 位置 | 問題 | 修復 |
|------|------|------|
| `emotion_analyzer.py` + `user_monitor.py` | ~30 個共同中文關鍵字各寫一遍 | 提取到 `core/emotion_constants.py` |
| `user_monitor.py` | 有關鍵字重複（`難過×2`, `糟糕×2`, `害怕×2`, `amazing×2`） | 去重 |

#### Singleton 模式不一致 — **標準化（低優先級）**

| 模式 | 文件 | 行動 |
|------|------|------|
| `__new__` override | biological_integrator.py | 保留（已有 singleton 邏輯） |
| Module-level getter | config_loader, waiting_scheduler, state_matrix_api 等 | 保留（最常見模式） |
| Module-level globals | lifespan.py | 保留（5 個 singleton 統一管理） |

**結論:** 不強行統一，保持各文件現有模式。

---

### 1.3 「可以安全提取共用」的項目

#### `_char_bigrams` — **提取共用，保留轉接**

| 位置 | 差異 |
|------|------|
| `template_matcher.py:364` | `{text[i:i+2] for i in range(len(text) - 1)}` |
| `ham_manager.py:95` | 同上 + `len < 2` guard |

**差異:** B 有 edge-case guard，更完整。A 無 guard。
**安全合併:** 是 — B 是 A 的超集。合併後 A 的調用者不會受到影響（guard 是額外保護）。
**向後兼容:** 保留原方法，轉接到共用函數。

#### Bigram Jaccard 公式 — **提取共用，保留轉接**

| 位置 | 公式 |
|------|------|
| `ham_manager.py:86` | `min(0.95, jaccard * 1.2)` |
| `template_matcher.py:360` | 同上 |

**差異:** 完全相同。
**安全合併:** 是。
**向後兼容:** 保留原方法，轉接到共用函數。

#### `_normalize_text` — **提取共用**

| 位置 | 功能 |
|------|------|
| `template_matcher.py:245` | lowercase + 去標點空格 |

**只有一個實作。** 提取到共用函數供其他文件使用（如果需要）。

---

## 二、實際可執行的清理計劃

### 2.1 Phase 1: 安全清理 (1-2 天)

#### 步驟 1: 建立 `utils/text_utils.py`

```python
"""共用文字處理工具 — 只提取已驗證安全的共用函數"""

import re
from typing import List, Set, Optional

def char_bigrams(text: str) -> set:
    """字元級 bigram（含 edge-case guard）"""
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

def normalize_text(text: str) -> str:
    """文字標準化：lowercase + 去標點空格"""
    text = text.lower()
    for ch in [" ", "?", "!", "。", "？", "！", "，", ","]:
        text = text.replace(ch, "")
    return text
```

#### 步驟 2: 各文件向後兼容轉接

```python
# template_matcher.py — 保留原方法
from utils.text_utils import char_bigrams as _char_bigrams_util
from utils.text_utils import bigram_jaccard as _bigram_jaccard_util
from utils.text_utils import normalize_text as _normalize_text_util

class TemplateMatcher:
    @staticmethod
    def _char_bigrams(text):
        return _char_bigrams_util(text)
    
    def _normalize_text(self, text):
        return _normalize_text_util(text)
    
    def _calculate_similarity(self, user_input, template):
        user_lower = self._normalize_text(user_input)
        # ... 其餘邏輯不變，改用 _bigram_jaccard_util
```

```python
# ham_manager.py — 保留原方法
from utils.text_utils import char_bigrams as _char_bigrams_util
from utils.text_utils import bigram_jaccard as _bigram_jaccard_util

class HAMMemoryManager:
    @staticmethod
    def _char_bigrams(text):
        return _char_bigrams_util(text)
    
    # _extract_keywords 保持不動（有 dict 處理邏輯）
    # _calculate_similarity 改用 _bigram_jaccard_util
```

#### 步驟 3: 刪除棄用代碼

| 文件 | 行動 |
|------|------|
| `ai/garden/hybrid_router.py` | 刪除整個文件 |
| `services/ai_editor.py` | 刪除整個文件 |
| `core/state_manager.py` | 刪除整個文件 |
| `core/degraded_mode.py` | 刪除整個文件 |
| `mcp/connector.py` | 移除本地 `ProjectError` mock，改用 `shared/error.py` import |

#### 步驟 4: 修復 ED3N 建立 Bug

```python
# router.py — _ed3n_fallback_text 修復
def _ed3n_fallback_text(self, text):
    try:
        # 重用 ModelBus 中的實例
        engine = self.model_bus._registry.get("ed3n", (None,))[0]
        if engine is None:
            from ai.ed3n.ed3n_engine import ED3NEngine
            engine = ED3NEngine()
            engine.load_presets()
        return engine.process(text, depth="shallow")
    except Exception:
        return "抱歉，我暫時無法回應。"
```

```python
# composer.py — 模組級 ED3N 快取
_ed3n_engine = None

def _get_ed3n():
    global _ed3n_engine
    if _ed3n_engine is None:
        from ai.ed3n.ed3n_engine import ED3NEngine
        _ed3n_engine = ED3NEngine()
        _ed3n_engine.load_presets()
    return _ed3n_engine
```

#### 步驟 5: 修復 FallbackConfigLoader Bug

```python
# memory_template.py:262 — 修復
# 現狀（壞掉）:
_cfg = get_config_loader()  # Returns FallbackConfigLoader
score_weights = _cfg.get_authority("angela_core", {}).get("template_matching", {}).get("score_weights", {})
# get_authority() 不存在於 FallbackConfigLoader

# 修復:
from core.config_loader import get_angela_config
_cfg = get_angela_config()
score_weights = _cfg.get_authority("angela_core", {}).get("template_matching", {}).get("score_weights", {})
```

#### 步驟 6: 提取共用情緒關鍵字常數

```python
# core/emotion_constants.py
SHARED_EMOTION_KEYWORDS = {
    "happy": ["开心", "高兴", "快乐", "棒", "好", "哈哈", "喜欢", "爱"],
    "sad": ["难过", "悲伤", "失望", "哭", "痛苦"],
    "angry": ["烦", "生气", "讨厌", "糟糕"],
    "fear": ["担心", "害怕", "紧张", "焦慮"],
    "surprise": ["哇"],
    "calm": ["平静", "休息"],
}
```

```python
# user_monitor.py — 使用共用常數 + 去重
from core.emotion_constants import SHARED_EMOTION_KEYWORDS
# 移除重複的關鍵字（難過×2, 糟糕×2, 害怕×2, amazing×2）
```

---

## 三、ED3N 適當使用

### 3.1 ED3N 能力與適合用途

| 能力 | 品質 | 適合 | 不適合 |
|------|------|------|--------|
| ReflexLayer | ⭐⭐⭐⭐⭐ | 問候、timeout、固定回覆 | 複雜理解 |
| encode_soft() | ⭐⭐⭐ | 意圖輔助、歷史相關性 | 語義分析 |
| encode() | ⭐⭐ | 歷史 key overlap | 新穎匹配 |
| process_shallow() | ⭐⭐⭐ | 無 LLM 時回覆 | 高品質生成 |
| process_multimodal() | ⭐⭐⭐ | 圖片/音訊→keys | 圖片理解 |
| continuous_learning | ⭐⭐ | 字典成長 | 即時學習 |
| train() | ⭐⭐ | 批次學習 | 線上學習 |

### 3.2 ED3N 在各處的使用

| 位置 | 用途 | 方法 |
|------|------|------|
| chat_routes.py | 歡迎、timeout、cancelled | process_reflex() |
| router.py | ModelBus reflex 層 + fallback | process() |
| composer.py | compose_fallback | process_shallow() |
| proactive_interaction | 主動互動訊息 | process_reflex() |
| chat_routes.py | 歷史相關性 | dictionary.encode() |
| chat_service.py | 持續學習 | process_interaction() |
| learning_integration | HAM 同步 | dictionary 操作 |
| training_coordinator | reflex 同步 | reflex 操作 |

### 3.3 ED3N 不使用的地方

| 位置 | 為什麼 | 替代 |
|------|--------|------|
| emotion_analyzer.py | 無情緒模型 | 關鍵字+權重 |
| prompt_builder.py | 無 embedding | LLM 直接處理 |
| causal_reasoning | 無因果模型 | CausalReasoningEngine |
| vision_service | 多模態是 bolt-on | VisionService |
| knowledge_qa | 字典有限 | GARDEN + Cloud |

---

## 四、QueryClassifier 擴展

### 4.1 新增 QueryTypes

```python
class QueryType(Enum):
    # 現有 (9)
    REFLEX, GREETING, MATH, LOGIC, KNOWLEDGE, CREATIVE, OPINION, COMMAND, UNKNOWN
    # 新增 (7)
    FILE, SEARCH, CODE, EXECUTE, TASK, VISION, AUDIO
```

### 4.2 新增 Patterns

```python
# OPINION 補充
(QueryType.OPINION, r"(覺得|認為|看法|意見|opinion|think|believe|feel)", 0.75),
# FILE
(QueryType.FILE, r"(整理|清理|刪除|移動|複製|檔案|文件|organize|delete|move|copy|file)", 0.8),
# SEARCH
(QueryType.SEARCH, r"(搜尋|搜索|查找|找|search|find|look\s*for|google)", 0.8),
# CODE
(QueryType.CODE, r"(程式|代碼|code|program|script|debug|bug|函数|function)", 0.8),
# EXECUTE
(QueryType.EXECUTE, r"(執行|運行|開啟|關閉|execute|run|open|close|start|stop)", 0.8),
# TASK
(QueryType.TASK, r"(任務|工作|待辦|task|todo|planned|schedule|安排)", 0.75),
# VISION
(QueryType.VISION, r"(圖片|照片|影像|image|photo|picture|截圖|screenshot)", 0.8),
# AUDIO
(QueryType.AUDIO, r"(語音|音訊|錄音|audio|voice|speech|music|音樂)", 0.8),
```

### 4.3 ED3N 作為輔助分類

```python
def classify(self, text):
    regex_type, regex_conf = self._regex_classify(text)
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

### 5.1 Handler 註冊

```python
class ModelBus:
    def register_handler(self, handler_id, handler, intent_types):
        self._handlers[handler_id] = handler
        for t in intent_types:
            self._handler_map[t] = handler_id
```

### 5.2 路由擴展

```python
def route(self, text, query_type="auto", context=None):
    # ... 分類 ...
    if query_type in self._handler_map:
        return RouteDecision(action=RouteAction.EXECUTE, engine=self._handlers[self._handler_map[query_type]])
    # ... LLM 路由 ...
```

---

## 六、管線全貌（完成後）

```
用戶輸入（文字/圖片/音訊/檔案）
    │
    ▼
[接入層] WebSocket + HTTP + Session
    │
    ▼
[意圖分類] QueryClassifier + ED3N encode_soft()（輔助）
    │  16 種意圖
    │
    ▼
[管線分派] ModelBus（提升為主要路由）
    │
    ├─ REFLEX/GREETING → ED3N reflex
    ├─ MATH → ED3N → GARDEN
    ├─ FILE/SEARCH/CODE/EXECUTE/TASK → Handlers
    ├─ VISION/AUDIO → Services
    ├─ KNOWLEDGE → GARDEN → Cloud
    ├─ CREATIVE → Cloud
    └─ 其他 → fan-out
    │
    ▼
[回應合成] Composer / NeuroBlender
    │
    ▼
[狀態更新] Bio + State + Neuroplasticity
    │
    ▼
[記憶存儲] HAM (fire-and-forget)
    │
    ▼
回應 + Live2D + 生物回饋
```

---

## 七、實施順序

### Phase 1: 安全清理 ✅ 完成
1. ✅ 建立 `utils/text_utils.py`（char_bigrams, bigram_jaccard, normalize_text）
2. ✅ template_matcher + ham_manager 轉接到共用函數
3. ✅ 刪除棄用代碼（5 個文件）
4. ✅ 修復 ED3N 建立 bug（router + composer）
5. ✅ 修復 FallbackConfigLoader bug（memory_template.py）
6. ✅ 提取共用情緒關鍵字常數 + user_monitor 去重

### Phase 2: QueryClassifier 擴展 ✅ 完成
1. ✅ 新增 7 個 QueryTypes（FILE, SEARCH, CODE, EXECUTE, TASK, VISION, AUDIO）
2. ✅ 新增 patterns（含 OPINION 補充）
3. ✅ ED3N encode_soft 作為輔助分類

### Phase 3: ModelBus 擴展 ✅ 完成
1. ✅ Handler 註冊機制（register_handler, _adapt_handler）
2. ✅ 註冊 handlers（file_ops, web_search）
3. ✅ 路由擴展（_resolve_candidates for 7 new types）
4. ✅ 提升為主要路由（handler-first for FILE/SEARCH/CODE/EXECUTE/TASK）

### Phase 4: 自主認知整合 ✅ 完成
1. ✅ prompt_builder 讀取自主決策（get_autonomous_decisions）
2. ✅ 公式實例共享（module-level singletons）
3. ✅ 動態 prompt（θ 路由狀態 + 理論公式指標）

### Phase 5: 感知管線 ✅ 完成（最小可行範圍）
1. ✅ VisionService 整合（/vision/analyze endpoint）
2. ✅ 圖片上下文整合到 prompt_builder（【圖片分析結果】section）
3. ⏳ 前端上傳（Desktop/Web/Mobile/Pixel — 留待後續）
4. ⏳ WebSocket 擴展（binary data — 留待後續）

### Phase 6: Handler 註冊 ✅ 完成
1. ✅ lifespan 中註冊 file_operation_handler + web_search_handler
2. ✅ ModelBus handler_map 正確映射

---

## 八、文件清單

### 需要新建
| 文件 | 功能 | 狀態 |
|------|------|------|
| `utils/text_utils.py` | 共用文字工具（char_bigrams, bigram_jaccard, normalize_text） | ✅ 已建立 |
| `core/emotion_constants.py` | 共用情緒關鍵字常數 | ✅ 已建立 |

### 需要修改（轉接，不改行為）
| 文件 | 修改 | 狀態 |
|------|------|------|
| `template_matcher.py` | _char_bigrams + _normalize_text 轉接到 text_utils | ✅ 已完成 |
| `ham_manager.py` | _char_bigrams 轉接到 text_utils | ✅ 已完成 |
| `router.py` | 修復 _ed3n_fallback_text bug | ✅ 已完成 |
| `composer.py` | ED3N 模組級快取 | ✅ 已完成 |
| `memory_template.py` | 修復 FallbackConfigLoader bug | ✅ 已完成 |
| `user_monitor.py` | 使用共用情緒常數 + 去重 | ✅ 已完成 |
| `query_classifier.py` | 新增 types + patterns + ED3N | ✅ 已完成 |
| `model_bus.py` | 新增 handler 註冊 + 路由 | ✅ 已完成 |
| `prompt_builder.py` | 動態 prompt + image context | ✅ 已完成 |
| `chat_routes.py` | vision/analyze + chat/with-image endpoints | ✅ 已完成 |
| `lifespan.py` | 註冊 handlers | ✅ 已完成 |

### 需要刪除
| 文件 | 原因 |
|------|------|
| `ai/garden/hybrid_router.py` | 自註棄用 |
| `services/ai_editor.py` | P8-2 棄用 |
| `core/state_manager.py` | 空殼 |
| `core/degraded_mode.py` | 空殼 |
| `mcp/connector.py::ProjectError` | 本地 mock |

### 明確不動（深度分析確認不是重複）
| 文件 | 原因 |
|------|------|
| `_extract_keywords` x5 | 行為不同，不能合併 |
| Config 系統 x4 | 不同系統，不是重複 |
| 情緒系統 x4 | 不同抽象層，不能合併 |
| Cosine Similarity x3 | 不同數據類型 |
| `get_biological_state` x2 | 不同返回類型（str vs dict） |
| Singleton 模式 | 保持各文件現有模式 |
