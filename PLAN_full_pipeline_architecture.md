# 聊天管線完整架構重構計劃 v7

**日期:** 2026-06-14
**基於:** 7 個代理完整代碼審計（服務層、前端、自主認知、API、ED3N 能力、重複分析、路由架構）
**目標:** 消除重複 + 擴展 QueryClassifier + ED3N 適當整合 + 完整管線
**狀態:** 規劃階段

---

## 一、重複實作清理（先做）

### 1.1 共用工具提取

**目標:** 消除 4 個重複實作，提取到 `utils/text_utils.py`

| 重複 | 現有位置 | 行動 |
|------|----------|------|
| `_char_bigrams()` | `ham_manager.py:95`, `template_matcher.py:364` | 提取到 `text_utils.char_bigrams()` |
| Jaccard 公式 | `ham_manager.py:86`, `template_matcher.py:360` | 提取到 `text_utils.bigram_jaccard()` |
| `_extract_keywords()` | `template_matcher.py:258`, `router.py:1202`, `composer.py:307`, `ham_manager.py:128` | 合併為 `text_utils.extract_keywords(text, max_keywords, stopwords)` |

**`utils/text_utils.py` 內容:**
```python
def char_bigrams(text: str) -> set:
    """字元級 bigram，用於中文相似度"""
    if len(text) < 2:
        return {text} if text else set()
    return {text[i:i+2] for i in range(len(text) - 1)}

def bigram_jaccard(text_a: str, text_b: str) -> float:
    """Bigram Jaccard 相似度"""
    a, b = char_bigrams(text_a), char_bigrams(text_b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

def extract_keywords(text: str, max_keywords: int = 8, stopwords: set = None) -> list:
    """統一關鍵字提取（支持中英文）"""
    if stopwords is None:
        stopwords = DEFAULT_STOPWORDS  # 合併所有版本的 stopwords
    # 用 regex 分詞: 中文 2+ 字元, 英文 2+ 字母
    words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}', text)
    return [w for w in words if w not in stopwords][:max_keywords]
```

### 1.2 情緒分析合併

| 現有 | 位置 | 行動 |
|------|------|------|
| EmotionAnalyzer | `emotion_analyzer.py` | **保留** — 關鍵字中文情緒分析 |
| dialogue_context 情緒 | `dialogue_context.py:168` | **移除** — 重複 |
| nlp_agent 情緒 | `nlp_processing_agent.py:33` | **移除** — 重複 |
| EmotionalBlending | `emotional_blending.py` | **保留** — PAD 模型，不同用途 |

### 1.3 Config 系統合併

| 現有 | 位置 | 行動 |
|------|------|------|
| AngelaConfig | `config_loader.py` | **遷移** 到 tiered_loader |
| tiered_loader | `tiered_loader.py` | **保留** — 更完整 |

### 1.4 其他清理

| 清理 | 行動 |
|------|------|
| `StateMatrix4D` 實際是 6D | 重新命名（可選） |
| `get_biological_state` 命名混淆 | 重命名為 `format_bio_state_for_prompt` |
| EmotionAnalyzer 每次請求建立新實例 | 改為 singleton |
| `_ed3n_fallback_text` 每次建立新 ED3N | 重用 ModelBus 中的實例 |

---

## 二、ED3N 適當使用（不硬塞）

### 2.1 ED3N 應該用的地方

| 用途 | ED3N 方法 | 為什麼適合 | 品質影響 |
|------|-----------|-----------|----------|
| **快速反射** | `process_reflex()` | 亚毫秒，LRU 快取，最強組件 | ⭐⭐⭐⭐⭐ |
| **意圖模糊匹配** | `dictionary.encode_soft()` | 比 binary keyword match 好，有 confidence 分數 | ⭐⭐⭐ |
| **歷史相關性** | `dictionary.encode()` | 已在用，key overlap 合理 | ⭐⭐⭐ |
| **Session 歡迎** | `process("welcome", depth="reflex")` | 預設反射模式 | ⭐⭐⭐⭐ |
| **Timeout fallback** | `process("timeout_response", depth="reflex")` | 安全網 | ⭐⭐⭐⭐ |
| **主動互動** | `process("welcome_back"|"idle_check", depth="reflex")` | 預設反射 | ⭐⭐⭐⭐ |
| **多模態輸入** | `process_multimodal()` | 圖片/音訊→dictionary keys | ⭐⭐⭐ |
| **持續學習** | `ContinuousLearningPipeline` | 長期字典成長 | ⭐⭐ |

### 2.2 ED3N 不應該用的地方

| 用途 | 為什麼不用 | 用什麼替代 |
|------|-----------|-----------|
| **情緒分析** | ED3N 無情緒模型 | EmotionAnalyzer（關鍵字）+ EmotionalBlending（PAD） |
| **語義理解** | ED3N 無 embedding | LLM 直接處理 |
| **因果推理** | ED3N 無因果模型 | CausalReasoningEngine |
| **知識問答** | ED3N 字典有限 | GARDEN + Cloud LLM |
| **複雜指令** | ED3N reflex 太簡單 | LLM + handlers |

### 2.3 ED3N 在意圖分類中的角色

**不替換 QueryClassifier，而是增強它：**

```python
# query_classifier.py 改進
class QueryClassifier:
    def classify(self, text: str) -> tuple[QueryType, float]:
        # 1. Regex 分類（現有，快速）
        regex_type, regex_conf = self._regex_classify(text)
        
        # 2. ED3N 作為第二信號（可選）
        ed3n_type, ed3n_conf = self._ed3n_classify(text)
        
        # 3. 合併: 取 confidence 較高者
        if ed3n_conf > regex_conf:
            return ed3n_type, ed3n_conf
        return regex_type, regex_conf
    
    def _ed3n_classify(self, text: str) -> tuple[QueryType, float]:
        """ED3N 字典編碼作為分類輔助"""
        try:
            keys = self._ed3n.dictionary.encode_soft(text)
            # 根據匹配的 key 類型推斷意圖
            # 例如: 匹配到 "file" 類 key → FILE
            # 例如: 匹配到 "search" 類 key → SEARCH
            return self._keys_to_intent(keys)
        except Exception:
            return QueryType.UNKNOWN, 0.3
```

**ED3N 字典新增意圖 patterns:**
```python
# dictionary_layer.py 預設新增
{"key": "intent_file", "surface_forms": [{"zh": "檔案", "en": "file"}, {"zh": "整理", "en": "organize"}, ...], "context": {"type": "intent", "intent": "FILE"}}
{"key": "intent_search", "surface_forms": [{"zh": "搜尋", "en": "search"}, {"zh": "查找", "en": "find"}, ...], "context": {"type": "intent", "intent": "SEARCH"}}
```

---

## 三、QueryClassifier 擴展

### 3.1 新增 QueryTypes

```python
class QueryType(Enum):
    REFLEX = "reflex"        # 現有
    GREETING = "greeting"     # 現有
    MATH = "math"             # 現有
    LOGIC = "logic"           # 現有
    KNOWLEDGE = "knowledge"   # 現有
    CREATIVE = "creative"     # 現有
    OPINION = "opinion"       # 現有（需新增 patterns）
    COMMAND = "command"       # 現有
    UNKNOWN = "unknown"       # 現有
    # 新增:
    FILE = "file"             # 檔案操作
    SEARCH = "search"         # 搜尋（網路/Drive/記憶）
    CODE = "code"             # 程式碼
    EXECUTE = "execute"       # 系統執行
    TASK = "task"             # 任務管理
    VISION = "vision"         # 圖片分析
    AUDIO = "audio"           # 音訊處理
```

### 3.2 新增 Patterns

```python
_patterns = [
    # ... 現有 patterns ...
    # FILE
    (QueryType.FILE, r"(整理|清理|刪除|移動|複製|檔案|文件|organize|delete|move|copy|file)", 0.8),
    (QueryType.FILE, r"(桌面|downloads|documents|desktop|downloads)", 0.75),
    # SEARCH
    (QueryType.SEARCH, r"(搜尋|搜索|查找|找|search|find|look\s*for|google)", 0.8),
    (QueryType.SEARCH, r"(網路|web|internet|online|drive|雲端)", 0.7),
    # CODE
    (QueryType.CODE, r"(程式|代碼|code|program|script|debug|bug|函数|function)", 0.8),
    (QueryType.CODE, r"(python|javascript|html|css|sql|api)", 0.85),
    # EXECUTE
    (QueryType.EXECUTE, r"(執行|運行|開啟|關閉|execute|run|open|close|start|stop)", 0.8),
    # TASK
    (QueryType.TASK, r"(任務|工作|待辦|task|todo|planned|schedule|安排)", 0.75),
    # VISION
    (QueryType.VISION, r"(圖片|照片|影像|image|photo|picture|picture|截圖|screenshot)", 0.8),
    # AUDIO
    (QueryType.AUDIO, r"(語音|音訊|錄音|audio|voice|speech|music|音樂)", 0.8),
    # OPINION (補充)
    (QueryType.OPINION, r"(覺得|認為|看法|意見|opinion|think|believe|feel)", 0.75),
]
```

### 3.3 ModelBus 擴展

```python
# model_bus.py — 新增 handler 註冊
def register_handler(self, handler_id: str, handler, intent_types: list):
    """註冊非 LLM handler（檔案、搜尋等）"""
    self._handlers[handler_id] = handler
    for intent_type in intent_types:
        self._handler_map[intent_type] = handler_id

# 路由邏輯擴展
def route(self, text, query_type="auto", context=None):
    # ... 現有分類 ...
    
    # 新增: 如果是 handler 類型，直接派發
    if query_type in self._handler_map:
        handler_id = self._handler_map[query_type]
        handler = self._handlers[handler_id]
        return RouteDecision(
            action=RouteAction.EXECUTE,
            engine=handler,
            confidence=0.9,
            reasoning=f"Handler dispatch: {handler_id}"
        )
    
    # ... 現有 LLM 路由 ...
```

---

## 四、管線全貌（完成後的樣子）

### 4.1 完整流程圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端層                                    │
│  Desktop Electron │ Web Live2D │ Mobile │ Pixel                 │
│  ─────────────────────────────────────────────────────────────  │
│  輸入: 文字 │ 圖片(新) │ 音訊(新) │ 檔案(新) │ 觸覺             │
│  輸出: 文字 │ Live2D │ 狀態 │ 生物回饋                          │
└──────────────────────┬──────────────────────────────────────────┘
                       │ WebSocket + HTTP
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     接入層                                      │
│  WebSocket Manager │ HTTP Router │ Session Manager              │
│  協議: connect 握手 → chat/image/audio/file_message             │
│  Session: 30 條歷史 │ 單設備 │ 心跳                              │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   輸入標準化層                                    │
│  InputClassifier                                                │
│  ─────────────────────────────────────────────────────────────  │
│  偵測: TEXT │ IMAGE │ AUDIO │ FILE │ MULTIMODAL                 │
│  標準化: {type, data, metadata}                                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   意圖分類層（擴展 QueryClassifier）              │
│  QueryClassifier + ED3N dictionary.encode_soft() (輔助)         │
│  ─────────────────────────────────────────────────────────────  │
│  16 種意圖: REFLEX │ GREETING │ MATH │ LOGIC │ KNOWLEDGE │      │
│    CREATIVE │ OPINION │ COMMAND │ FILE │ SEARCH │ CODE │        │
│    EXECUTE │ TASK │ VISION │ AUDIO │ UNKNOWN                    │
│  輸出: (QueryType, confidence)                                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┬──────────────┐
          ▼            ▼            ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│  Handler 管線 │ │ LLM 管線  │ │ 感知管線  │ │  高級管線     │
│  ─────────── │ │ ──────── │ │ ──────── │ │  ──────────  │
│  FILE→FileOp  │ │ REFLEX→  │ │ VISION→  │ │  自主認知     │
│  SEARCH→Web   │ │  ED3N    │ │  Vision  │ │  因果推理     │
│  CODE→CodeIns │ │ GREETING→│ │ AUDIO→   │ │  知識圖譜     │
│  EXECUTE→     │ │  ED3N    │ │  Audio   │ │  學習系統     │
│  DesktopInter │ │ MATH→    │ │          │ │  經驗回放     │
│  TASK→        │ │  ED3N/   │ │          │ │              │
│  ProjectCoord │ │  GARDEN  │ │          │ │              │
│               │ │ KNOWLEDGE│ │          │ │              │
│               │ │ →GARDEN/ │ │          │ │              │
│               │ │  Cloud   │ │          │ │              │
│               │ │ CREATIVE │ │          │ │              │
│               │ │ →Cloud   │ │          │ │              │
│               │ │ OTHER→   │ │          │ │              │
│               │ │  fan-out │ │          │ │              │
└──────┬───────┘ └─────┬────┘ └────┬─────┘ └──────┬───────┘
       │               │           │               │
       └───────────────┴───────────┴───────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   回應合成層                                      │
│  ResponseComposer │ NeuroBlender │ DeviationTracker              │
│  ─────────────────────────────────────────────────────────────  │
│  策略: COMPOSED │ HYBRID │ MEMORY │ LLM │ REFLEX │ HANDLER      │
│  品質: 偏差追蹤 │ 成功率學習                                      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   狀態更新層                                      │
│  BiologicalIntegrator │ StateMatrix4D │ Neuroplasticity          │
│  ─────────────────────────────────────────────────────────────  │
│  輸入→狀態: 情緒、壓力、覚醒、荷爾蒙、突觸權重                       │
│  狀態→輸出: prompt 動態建構、Live2D、生物回饋                       │
│  自主→指令: 自主生命週期決策 → prompt 指令                          │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 各管線詳細流程

#### A. Handler 管線（File/Search/Code/Execute/Task）

```
用戶: "幫我整理桌面" 
  → InputClassifier: TEXT
  → QueryClassifier: (COMMAND/FILE, 0.8)
  → ModelBus: FILE → FileOperationHandler
  → FileOperationHandler.handle("organize_desktop")
  → 返回: {status: "success", operations: [...]}
  → LLM: 整理成自然語言回應
  → 回應: "已整理桌面，移動了 12 個檔案到對應資料夾"
```

#### B. 感知管線（Vision/Audio）

```
用戶上傳圖片 + "這是什麼？"
  → InputClassifier: IMAGE
  → VisionService.analyze_image(image_data)
  → 返回: {description: "一隻貓", objects: ["cat"], emotions: ["cute"]}
  → QueryClassifier: (KNOWLEDGE, 0.7)
  → context["vision_context"] = 分析結果
  → LLM: 看到圖片描述 + 用戶問題
  → 回應: "這是一隻可愛的橘貓！牠看起來很放鬆"
```

#### C. LLM 管線（現有，改進）

```
用戶: "今天天氣如何"
  → InputClassifier: TEXT
  → QueryClassifier: (KNOWLEDGE, 0.7)
  → Template match: 無匹配
  → Memory match: 無匹配
  → ModelBus: KNOWLEDGE → GARDEN → Cloud fallback
  → LLM 生成回應
  → 回應合成
  → 狀態更新
  → 回應
```

#### D. 自主認知管線

```
每 5 分鐘:
  → AutonomousLifeCycle 決策
  → 決策寫入 decision_history

用戶提問時:
  → prompt_builder 讀取最新自主決策
  → 注入: "自主系統決定探索新主題：認知缺口過大"
  → LLM 根據自主決策調整回應
```

### 4.3 ED3N 在各管線中的角色

| 管線 | ED3N 用途 | 方法 | 品質 |
|------|-----------|------|------|
| Handler | 無 | — | — |
| Vision | 多模態編碼 | `encode(image)` → keys | ⭐⭐⭐ |
| Audio | 多模態編碼 | `encode(audio)` → keys | ⭐⭐⭐ |
| LLM (reflex) | 快速反射 | `process_reflex()` | ⭐⭐⭐⭐⭐ |
| LLM (greeting) | 問候 | `process_reflex()` | ⭐⭐⭐⭐⭐ |
| LLM (math) | 數學反射 | `process_reflex()` | ⭐⭐⭐⭐ |
| LLM (timeout) | 安全網 | `process_reflex()` | ⭐⭐⭐⭐ |
| LLM (fallback) | 後備生成 | `process_shallow()` | ⭐⭐⭐ |
| 意圖分類 | 模糊匹配輔助 | `encode_soft()` | ⭐⭐⭐ |
| 歷史相關性 | 關鍵字匹配 | `encode()` | ⭐⭐⭐ |
| 主動互動 | 預設訊息 | `process_reflex()` | ⭐⭐⭐⭐ |
| 持續學習 | 字典成長 | `process_interaction()` | ⭐⭐ |

---

## 五、前端整合（新增能力）

### 5.1 需新增的前端功能

| 功能 | Desktop | Web | Mobile | Pixel |
|------|:-------:|:---:|:------:|:-----:|
| 圖片上傳 | 拖拽/按鈕 | 拖拽/按鈕 | 相機/相簿 | 截圖 |
| 音訊上傳 | 錄音按鈕 | 錄音按鈕 | 原生錄音 | — |
| 檔案上傳 | 檔案選擇器 | 檔案選擇器 | 原生選擇器 | tray 選單 |
| WebSocket 擴展 | image/audio/file_message | 同左 | 同左 | 同左 |

### 5.2 WebSocket 協議擴展

```
新增 Client → Server:
  image_message: {type, data: {image_base64, caption, message_id}}
  audio_message: {type, data: {audio_base64, format, message_id}}
  file_message: {type, data: {file_name, file_base64, mime_type, message_id}}

新增 Server → Client:
  image_analysis: {type, data: {description, objects, emotions}}
  audio_transcription: {type, data: {text, confidence}}
  pipeline_status: {type, data: {pipeline, status, progress}}
```

### 5.3 HTTP API 端點替換

| Stub 端點 | 替換為 | 功能 |
|-----------|--------|------|
| `GET /api/v1/vision/status` | `POST /api/v1/vision/analyze` | 圖片分析 |
| `GET /api/v1/audio/status` | `POST /api/v1/audio/transcribe` | 音訊轉錄 |

---

## 六、管線交互與糾錯

### 6.1 管線間通訊

| 模式 | 用途 | 範例 |
|------|------|------|
| 直接派發 | IntentRouter → Pipeline | 意圖分類 → handler |
| 異步 fire-and-forget | 生物更新、記憶存儲 | 互動後更新 bio_state |
| HTTP 請求-回應 | 圖片/音訊/檔案 | 上傳 → 分析 → 結果 |
| WebSocket 推播 | 狀態更新、生物回饋 | 每 200ms 廣播 |

### 6.2 錯誤處理

| 錯誤 | 處理 | 恢復 |
|------|------|------|
| LLM 超時 | ED3N reflex fallback | 重試 1 次 |
| Handler 失敗 | 返回錯誤描述 | 記錄錯誤 |
| 圖片分析失敗 | 返回「無法分析」+ 繼續文字 | 重試 1 次 |
| 音訊轉錄失敗 | 返回「無法辨識」+ 請文字 | 重試 1 次 |
| WebSocket 斷線 | 自動重連 + 離線佇列 | 指數退避 |
| 生物系統異常 | 使用預設值 | 降級運行 |
| ED3N 異常 | 跳過 ED3N，用 regex/LLM | 記錄錯誤 |

### 6.3 資源控制

```python
class PipelineManager:
    MAX_CONCURRENT = 3
    priorities = {
        "text_chat": 1, "vision": 2, "audio": 2,
        "file_operation": 3, "web_search": 3, "learning": 4,
    }
```

---

## 七、後端 API 完整地圖

### 7.1 現有端點（保留）

| 方法 | 路徑 | 功能 |
|------|------|------|
| POST | `/api/v1/chat/unified` | 統一聊天 |
| POST | `/api/v1/session/start` | 開始 session |
| POST | `/api/v1/session/{id}/send` | 發送訊息 |
| POST | `/api/v1/angela/chat` | Angela 聊天 |
| POST | `/api/v1/dialogue` | 對話 |
| GET/POST | `/api/v1/desktop/*` | 桌面操作 |
| POST | `/api/v1/actions/execute` | 執行動作 |
| POST | `/api/v1/tactile/touch` | 觸覺 |
| GET/POST | `/api/v1/drive/*` | Google Drive |
| POST | `/api/v1/mobile/*` | 手機 |
| GET/POST | `/api/v1/state/*` | 狀態矩陣 |
| WS | `/ws` | WebSocket |

### 7.2 需替換的 Stub

| 現有 | 替換為 |
|------|--------|
| `GET /api/v1/vision/status` | `POST /api/v1/vision/analyze` |
| `GET /api/v1/audio/status` | `POST /api/v1/audio/transcribe` |

### 7.3 需新增的端點

| 方法 | 路徑 | 功能 |
|------|------|------|
| POST | `/api/v1/pipeline/classify` | 意圖分類（debug 用） |
| GET | `/api/v1/lifecycle/status` | 自主生命週期狀態 |
| GET | `/api/v1/lifecycle/decisions` | 最近決策歷史 |

---

## 八、prompt_builder 動態化

### 8.1 讀取自主認知

```python
def construct_angela_prompt(user_message, context, neuro_vocabulary=None):
    # 讀取自主生命週期（共享實例，有累積狀態）
    try:
        from core.life.autonomous_life_cycle import get_lifecycle_summary
        lifecycle = get_lifecycle_summary()
        phase = lifecycle.get("current_phase", "EXPLORATION")
        decisions = lifecycle.get("recent_decisions", [])
    except Exception:
        phase, decisions = "EXPLORATION", []
    
    # 動態指令
    directives = []
    if decisions:
        latest = decisions[0]
        directives.append(f"自主系統決定{latest.decision_type}：{latest.rationale}")
    
    # θ 創造衝動
    theta = context.get("state_for_llm", {}).get("theta", {})
    if theta.get("creation_urge", 0) > 0.6:
        directives.append("創造衝動高，嘗試新穎表達")
    
    # 動態系統提示
    system_prompt = f"""你是 Angela，一個活潑可愛的 AI 數字生命。
特點：開朗、友善、偶爾俏皮。

【自主狀態】
生命階段: {phase}
{chr(10).join(directives) if directives else "(自主系統運作中)"}

【生物狀態】
{bio_line}
"""
```

### 8.2 公式實例共享

```python
# 從 autonomous_life_cycle 獲取（共享實例，有累積狀態）
# 不再每次新建 5 個 formula 實例
def get_formula_summaries():
    try:
        from core.life.autonomous_life_cycle import get_lifecycle_summary
        metrics = get_lifecycle_summary().get("current_metrics", {})
        return "\n".join([
            f"HSM: {metrics.get('hsm', 0):.4f}",
            f"生命強度: {metrics.get('life_intensity', 0):.4f}",
            f"活躍認知: {metrics.get('active_cognition', 0):.4f}",
        ])
    except Exception:
        return ""
```

---

## 九、實施順序

### Phase 1: 重複清理 (1 天)
1. 建立 `utils/text_utils.py`
2. 提取 `char_bigrams`, `bigram_jaccard`, `extract_keywords`
3. 修改 `ham_manager.py`, `template_matcher.py`, `router.py`, `composer.py` 使用共用函數
4. 移除 `dialogue_context.py`, `nlp_processing_agent.py` 的情緒分析
5. EmotionAnalyzer 改為 singleton
6. 修復 `_ed3n_fallback_text` 重用實例

### Phase 2: QueryClassifier 擴展 (1-2 天)
1. 新增 QueryTypes: FILE, SEARCH, CODE, EXECUTE, TASK, VISION, AUDIO
2. 新增 patterns
3. 補充 OPINION patterns
4. ED3N encode_soft 作為輔助分類信號

### Phase 3: ModelBus 擴展 (1-2 天)
1. 新增 handler 註冊機制
2. 註冊 FileOperationHandler, GoogleDriveHandler, WebSearchHandler, LearningHandler
3. 路由邏輯擴展: handler 類型直接派發
4. 提升 ModelBus 為主要路由（不只 fallback）

### Phase 4: 自主認知整合 (1-2 天)
1. prompt_builder 讀取 autonomous_life_cycle 決策
2. 公式實例共享
3. 動態 prompt 指令建構

### Phase 5: 感知管線接入 (2-3 天)
1. 替換 vision.py, audio.py stub
2. 前端圖片/音訊上傳
3. WebSocket 協議擴展

### Phase 6: 高級管線 (2-3 天)
1. 因果推理接入
2. 知識圖譜接入
3. 學習系統完善

---

## 十、文件清單

### 需要新建
| 文件 | 功能 |
|------|------|
| `utils/text_utils.py` | 共用文字工具 |
| `services/pipeline/input_classifier.py` | 輸入類型偵測 |

### 需要修改
| 文件 | 修改 |
|------|------|
| `ai/response/template_matcher.py` | 使用 text_utils |
| `ai/memory/ham_memory/ham_manager.py` | 使用 text_utils |
| `services/llm/router.py` | 使用 text_utils, 修復 ed3n_fallback |
| `ai/response/composer.py` | 使用 text_utils |
| `ai/core/query_classifier.py` | 新增 types + patterns + ED3N 輔助 |
| `ai/core/model_bus.py` | 新增 handler 註冊 + 路由擴展 |
| `services/llm/prompt_builder.py` | 動態 prompt + 自主認知整合 |
| `api/routes/chat_routes.py` | 接入 InputClassifier, singleton EmotionAnalyzer |
| `api/routes/v1/endpoints/vision.py` | 替換 stub |
| `api/routes/v1/endpoints/audio.py` | 替換 stub |
| `services/websocket_manager.py` | 擴展訊息類型 |

### 需要保持不動
| 文件 | 原因 |
|------|------|
| `core/bio/*` | 已完整 |
| `ai/ed3n/*` | 已完整 |
| `ai/garden/*` | 已完整 |
| `ai/memory/*` | 已完整（除 ham_manager 用 text_utils） |
| `ai/response/*` | 已完整（除 composer 用 text_utils） |
