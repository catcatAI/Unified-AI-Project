# Angela 能力補全計畫：ED3N 獨立作戰 + GARDEN 加持 + 持續學習

**日期**: 2026-06-15
**目標**: 讓 Angela 只用 ED3N 也能跟其他 AI 打平，用 GARDEN 時有明顯優勢
**對齊**: AGENTS.md (Surgical Precision, No Placeholders), ANGELA_FULL_ARCHITECTURE.md
**現狀**: Phase 1-2 完成（QueryClassifier v2 + ExecutionGate），102 測試通過

---

## 現狀分析

### 已有能力
| 能力 | 狀態 |
|---|---|
| 16類意圖分類 | ✅ 完成 |
| 執行閘門（三因子分數） | ✅ 完成 |
| 確認機制（confirm/cancel） | ✅ 完成 |
| 執行結果注入 prompt | ✅ 完成 |
| 續行保護（3次停止） | ✅ 完成 |
| ED3N 反射層（問候/數學/邏輯） | ✅ 已有 |
| file_ops handler | ✅ 已有（38行，功能有限） |
| web_search handler | ✅ 已有（63行，未串 API） |
| ChromaDB 向量存儲 | ✅ 已有（HAM 整合） |
| ED3N 持續學習管線 | ✅ 已有（未啟用） |
| HAM 記憶系統 | ✅ 已有（部分接線） |
| 神經可塑性系統 | ✅ 已有（未整合 HAM） |

### 關鍵缺口
| 缺口 | 影響 |
|---|---|
| ED3N 字典只有 ~50 個 preset | 超出範圍就說「不理解」 |
| ED3N 分類輔助路徑休眠 | `_ed3n` 屬性未設定 |
| HANDLER_MAP 只有 file/search | CODE/EXECUTE/TASK/VISION/AUDIO 無 handler |
| 無語意檢索 | ED3N 只做字重疊 |
| 跨 session 記憶未接通 | 換對話就忘了 |
| 持續學習管線未啟用 | 學了但沒用 |
| 無多步驟編排 | 只能單步操作 |

---

## Phase 3: ED3N 能力補強（不依賴 GARDEN）

**目標**: 讓 ED3N 獨立時也能處理 80% 的日常對話

### 3.1 擴充 ED3N 字典 preset（+200 條）

**檔案**: `ai/ed3n/config/presets.json`

新增預設條目：
| 類別 | 數量 | 範例 |
|---|---|---|
| 檔案操作 | 30 | 建立/刪除/複製/移動/讀取/寫入 + 常見副檔名 |
| 網路搜尋 | 20 | 搜尋/查找/Google/查詢 + 常見搜尋意圖 |
| 程式碼 | 25 | 程式/函數/變數/迴圈/除錯/重構 |
| 系統操作 | 20 | 執行/運行/開啟/關閉/重啟 |
| 任務管理 | 25 | 任務/待辦/提醒/排程/行程 |
| 情緒表達 | 30 | 開心/難過/生氣/驚訝/擔心/感謝 |
| 日常對話 | 30 | 天氣/時間/日期/吃飯/睡覺/工作 |
| 知識查詢 | 20 | 什麼是/為什麼/怎麼/多少 |

**驗收**: `ED3NEngine.process("建立新文件")` 回傳非 fallback 回應

### 3.2 啟用 ED3N 分類輔助

**檔案**: `ai/core/query_classifier.py`

```python
# 在 QueryClassifier.__init__ 中：
def __init__(self, ed3n_engine=None):
    self._ed3n = ed3n_engine  # 外部注入，不自己建
```

**檔案**: `api/routes/chat_routes.py`

```python
# 在 _handle_chat_request 中：
classifier = QueryClassifier(ed3n_engine=getattr(self, '_ed3n_engine', None))
```

**驗收**: 分類測試中 ED3N 輔助路徑被觸發

### 3.3 ED3N 語意增強（不需向量）

**檔案**: `ai/ed3n/dictionary_layer.py`

在 `encode()` 中新增**同義詞展開**：
```python
# encode 前先展開同義詞
expanded = self._expand_synonyms(text)
keys = self._exact_encode(expanded)
```

同義詞表（硬編碼，~100 組）：
```python
_SYNONYM_MAP = {
    "搜尋": ["查找", "找", "查詢", "搜", "search", "find"],
    "刪除": ["移除", "清除", "砍", "delete", "remove"],
    "建立": ["新增", "創建", "新建", "create", "new", "add"],
    "讀取": ["開啟", "打開", "看", "read", "open"],
    "傳送": ["發送", "寄", "送", "send", "submit"],
    # ... 更多
}
```

**驗收**: `"幫我查找天氣"` 和 `"搜尋天氣"` 產生相同 keys

### 3.4 ED3N 反射層擴充

**檔案**: `ai/ed3n/ed3n_engine.py`

在 `_reflex_table` 新增 ~50 條反射規則：
```python
# 檔案操作反射
"建立新文件": "好的，我來幫你建立新文件。請問要建立什麼檔案？",
"刪除檔案": "刪除檔案是不可逆的操作，你確定要刪除嗎？",
"讀取檔案": "請問要讀取哪個檔案？",

# 搜尋反射
"搜尋": "請問要搜尋什麼？",
"幫我找": "請告訴我要找什麼？",

# 狀態反射
"你是誰": "我是 Angela，你的 AI 數字生命助手。",
"你能做什麼": "我可以幫你搜尋資訊、管理檔案、執行程式、處理任務等。",

# ... 更多
```

**驗收**: `"你是誰"` 產生有意義的反射回應（不是 fallback）

### 3.5 ED3N 數學擴充

**檔案**: `ai/ed3n/config/math_presets.json`

支援多位數運算：
```python
# encode 時解析多位數
"123 + 456" → keys: ["123", "plus", "456"]
# network 做加法
```

**驗收**: `"123 + 456"` 回傳 `"579"`

### 3.6 基礎 Handler 實作

**3.6.1 完善 file_ops handler**

**檔案**: `services/handlers/file_operation_handler.py`

```python
async def process(self, query: str, context=None) -> str:
    """完整檔案操作"""
    action = self._detect_action(query)  # read/create/delete/modify/list
    path = self._extract_path(query)
    
    if action == "read":
        return await self._read_file(path)
    elif action == "create":
        return await self._create_file(path, context)
    elif action == "delete":
        return await self._delete_file(path)
    elif action == "list":
        return await self._list_directory(path)
    # ...
```

支援：讀取、建立、刪除、列表、複製、移動、重新命名

**3.6.2 完善 web_search handler**

**檔案**: `services/handlers/web_search_handler.py`

```python
async def process(self, query: str, context=None) -> str:
    """串接搜尋 API"""
    # 方案 A: 串 SerpAPI / Google Custom Search
    # 方案 B: 串 DuckDuckGo (免費)
    # 方案 C: 串 Wikipedia API (免費)
    results = await self._search(query)
    return self._format_results(results)
```

**3.6.3 新增 code_execution handler**

**檔案**: `services/handlers/code_execution_handler.py`（新建）

```python
class CodeExecutionHandler:
    """安全的程式碼執行 handler"""
    
    ALLOWED_LANGUAGES = {"python", "javascript", "shell"}
    SANDBOX_MODE = True  # 沙箱模式，限制檔案系統存取
    
    async def process(self, query: str, context=None) -> str:
        code = self._extract_code(query)
        lang = self._detect_language(query)
        
        if lang not in self.ALLOWED_LANGUAGES:
            return f"不支援 {lang} 語言"
        
        result = await self._execute_in_sandbox(code, lang)
        return result
```

**3.6.4 新增 task_manager handler**

**檔案**: `services/handlers/task_manager_handler.py`（新建）

```python
class TaskManagerHandler:
    """任務管理 handler"""
    
    async def process(self, query: str, context=None) -> str:
        action = self._detect_action(query)  # create/delete/list/update
        
        if action == "create":
            task = self._parse_task(query)
            await self._store_task(task, context)
            return f"已建立任務：{task['title']}"
        elif action == "list":
            tasks = await self._get_tasks(context)
            return self._format_tasks(tasks)
        # ...
```

**3.6.5 新增 vision handler**

**檔案**: `services/handlers/vision_handler.py`（新建）

```python
class VisionHandler:
    """視覺處理 handler"""
    
    async def process(self, query: str, context=None) -> str:
        # 從 context 取得圖片 URL/路徑
        image_path = context.get("image_path")
        if not image_path:
            return "請提供圖片"
        
        description = await self._analyze_image(image_path)
        return description
```

**3.6.6 新增 audio handler**

**檔案**: `services/handlers/audio_handler.py`（新建）

```python
class AudioHandler:
    """音訊處理 handler"""
    
    async def process(self, query: str, context=None) -> str:
        audio_path = context.get("audio_path")
        if not audio_path:
            return "請提供音訊"
        
        text = await self._transcribe(audio_path)
        return text
```

**3.6.7 註冊所有 handler**

**檔案**: `services/llm/router.py`

```python
# 在 initialize() 中：
from services.handlers.code_execution_handler import CodeExecutionHandler
from services.handlers.task_manager_handler import TaskManagerHandler
from services.handlers.vision_handler import VisionHandler
from services.handlers.audio_handler import AudioHandler

self.model_bus.register_handler("code_execution", CodeExecutionHandler(), ["code"])
self.model_bus.register_handler("system_command", SystemCommandHandler(), ["execute"])
self.model_bus.register_handler("task_manager", TaskManagerHandler(), ["task"])
self.model_bus.register_handler("vision", VisionHandler(), ["vision"])
self.model_bus.register_handler("audio", AudioHandler(), ["audio"])
```

**檔案**: `ai/core/execution_gate.py`

```python
HANDLER_MAP = {
    "file": "file_ops",
    "search": "web_search",
    "code": "code_execution",
    "execute": "system_command",
    "task": "task_manager",
    "vision": "vision",
    "audio": "audio",
}
```

**驗收**: 每個 handler 有 5+ 單元測試，ExecutionGate 正確路由

### 3.7 Phase 3 測試

**檔案**: `tests/ai/ed3n/test_ed3n_enhanced.py`（新建）

| # | 測試案例 |
|---|---|
| 3.7.1 | `"建立新文件"` → ED3N 反射回應（非 fallback） |
| 3.7.2 | `"刪除檔案"` → ED3N 反射含警告 |
| 3.7.3 | `"你是誰"` → 有意義回應 |
| 3.7.4 | `"123 + 456"` → 回傳 `"579"` |
| 3.7.5 | `"搜尋天氣"` 和 `"查找天氣"` → 相同 keys |
| 3.7.6 | `"建立任務：買牛奶"` → task_manager 處理 |
| 3.7.7 | `"執行 python print('hi')"` → code_execution 處理 |
| 3.7.8 | `"讀取 config.json"` → file_ops 讀取 |
| 3.7.9 | `"列出所有文件"` → file_ops 列表 |
| 3.7.10 | 102 舊測試仍通過 |

---

## Phase 4: GARDEN 整合優勢

**目標**: 用 GARDEN 時有明顯優於 ED3N 的能力

### 4.1 GARDEN 向量語意檢索

**現狀**: GARDEN 的 VectorDictionary 有三層 fallback（SentenceTransformer → TF-IDF → CharBag）
**問題**: Python 3.14 + Windows 上 SentenceTransformer 掛掉

**方案**: 串 ChromaDB 替代 SentenceTransformer

**檔案**: `ai/garden/dictionary.py`

```python
class _ChromaEncoder:
    """使用 ChromaDB 做語意編碼（替代 SentenceTransformer）"""
    
    def __init__(self):
        import chromadb
        self._client = chromadb.Client()
        self._collection = self._client.create_collection("garden_concepts")
    
    def encode(self, text: str) -> List[float]:
        # 用 ChromaDB 內建 embedding
        result = self._collection.query(query_texts=[text], n_results=1)
        return result["embeddings"][0]
```

**驗收**: `"今天天氣如何"` 和 `"氣溫多少"` 語意相似度 > 0.7

### 4.2 GARDEN 知識圖譜導入

**檔案**: `ai/garden/kg_import.py`

已寫好 ConceptNet/Wikidata parser，需要：

1. 下載 ConceptNet 數據（~500MB）
2. 執行 `python -m ai.garden.kg_import --source conceptnet --limit 100000`
3. 匯出到 `ai/garden/config/knowledge_graph.json`

**驗收**: `GARDENEngine.process("巴黎是法國的首都")` 回傳正確知識

### 4.3 GARDEN 多步驟推理

**檔案**: `ai/garden/garden_engine.py`

在 `process()` 中加入**推理鏈**：
```python
def process(self, text: str, depth: str = "auto", context=None) -> str:
    # Step 1: 意圖分解
    sub_intents = self._decompose_intent(text)
    
    # Step 2: 逐步推理
    results = []
    for intent in sub_intents:
        result = self._single_step_process(intent, context)
        results.append(result)
    
    # Step 3: 綜合回應
    return self._synthesize(results)
```

**驗收**: `"搜尋台北天氣然後整理成報告"` → 先搜尋，再整理

### 4.4 GARDEN 情緒理解增強

**檔案**: `ai/garden/garden_engine.py`

利用 hormonal modulation：
```python
# 偵測用戶情緒
emotion = self._detect_emotion(text)

# 調整激素水平
if emotion == "angry":
    self._hormonal.cortisol = 0.8
    self._hormonal.serotonin = 0.3
elif emotion == "happy":
    self._hormonal.serotonin = 0.8
    self._hormonal.dopamine = 0.7

# SNN 閾值自動調整 → 回應風格跟著變
```

**驗收**: 用戶生氣時回應更溫和，用戶開心時回應更活潑

### 4.5 GARDEN 持續學習

**檔案**: `ai/garden/garden_engine.py`

```python
def learn_from_interaction(self, user_text: str, response: str, feedback: float):
    """從互動中學習"""
    # 1. 字典成長
    new_concepts = self._extract_new_concepts(user_text, response)
    for concept in new_concepts:
        self._dictionary.add_entry(concept)
    
    # 2. 權重更新（Hebbian）
    input_keys = self._dictionary.encode(user_text)
    output_keys = self._dictionary.encode(response)
    self._snn.hebbian_update(input_keys, output_keys, feedback)
    
    # 3. 定期保存
    if self._interaction_count % 100 == 0:
        self.save()
```

**驗收**: 多次互動後，GARDEN 對重複主題的回應更準確

### 4.6 Phase 4 測試

| # | 測試案例 |
|---|---|
| 4.6.1 | 語意相似查詢 → 相同 keys（TF-IDF 模式） |
| 4.6.2 | `"巴黎是哪國首都"` → 知識圖譜回應 |
| 4.6.3 | 多步驟任務 → 分步執行 |
| 4.6.4 | 情緒化輸入 → 情緒調整回應 |
| 4.6.5 | 10 次互動後 → 字典成長 |
| 4.6.6 | GARDEN 回應品質 > ED3N（同查詢） |

---

## Phase 5: 持續學習整合

**目標**: 讓 ED3N 和 GARDEN 都能從互動中學習，且學習成果跨 session 持久化

### 5.1 啟用 ED3N 持續學習

**檔案**: `services/chat_service.py`

```python
class ChatService:
    def __init__(self):
        # 啟用持續學習管線
        self._learning_pipeline = ContinuousLearningPipeline(
            growth_interval=10,   # 每 10 次互動成長一次
            train_interval=50,    # 每 50 次互動訓練一次
        )
        self._learning_pipeline.load()  # 載入之前的狀態
    
    async def generate_response(self, user_message, ...):
        response = await self._llm_service.generate(...)
        
        # 記錄互動
        self._learning_pipeline.record_interaction(
            user_message, response, 
            context={"session_id": session_id}
        )
        
        # 檢查是否該成長/訓練
        await self._learning_pipeline.step()
        
        return response
```

**驗收**: `angela_learning_state.json` 持續更新

### 5.2 ED3N → HAM 記憶同步

**檔案**: `ai/ed3n/learning_integration.py`

```python
class ED3NLearningIntegration:
    def sync_to_ham(self, ed3n_dictionary):
        """將 ED3N 字典同步到 HAM 持久記憶"""
        for entry in ed3n_dictionary.entries:
            self._ham.store({
                "type": "ed3n_concept",
                "key": entry.key,
                "surface_forms": entry.surface_forms,
                "relations": entry.relations,
                "importance": entry.confidence,
            })
```

**檔案**: `services/chat_service.py`

```python
# 在背景任務中定期同步
async def _sync_ed3n_to_ham(self):
    while True:
        await asyncio.sleep(3600)  # 每小時
        self._learning_integration.sync_to_ham(self._ed3n.dictionary)
```

**驗收**: ED3N 學到的新概念在重啟後仍在 HAM 中

### 5.3 神經可塑性 → HAM 整合

**檔案**: `ai/lifecycle/memory_integration_loop.py`

```python
class MemoryIntegrationLoop:
    async def _process_memory(self, memory):
        # 現有：分析模式、結構化
        
        # 新增：喂給神經可塑性系統
        trace = self._neuroplasticity.encode(memory.content)
        self._neuroplasticity.consolidate(trace)
        
        # 新增：根據存取頻率調整重要性
        if memory.access_count > 5:
            memory.importance *= 1.2
```

**驗收**: 常用記憶的重要性自動提升

### 5.4 跨 Session 記憶

**檔案**: `ai/context/memory_context.py`

```python
class MemoryContextManager:
    def save_session(self, session_id: str):
        """儲存 session 到磁碟"""
        session_data = {
            "memories": [m.to_dict() for m in self._memories],
            "short_term": [m.to_dict() for m in self._short_term],
            "long_term": [m.to_dict() for m in self._long_term],
        }
        path = f"sessions/{session_id}.json"
        with open(path, "w") as f:
            json.dump(session_data, f)
    
    def load_session(self, session_id: str):
        """從磁碟載入 session"""
        path = f"sessions/{session_id}.json"
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            # 還原記憶...
```

**檔案**: `api/routes/chat_routes.py`

```python
# 在 session 開始時載入
context = await self._memory_context.load_session(session_id)

# 在 session 結束時儲存
await self._memory_context.save_session(session_id)
```

**驗收**: 重啟後對話歷史仍在

### 5.5 學習回饋循環

**檔案**: `ai/response/learning_loop.py`

```python
class LearningLoop:
    def process_response(self, user_message: str, response: str, user_feedback: float):
        """處理回饋"""
        # 1. 提取語言特徵
        fragments = self._extractor.extract(response)
        
        # 2. 調整 ED3N 字典
        for fragment in fragments:
            if fragment.novelty > 0.7:
                self._ed3n.dictionary.grow(fragment.text)
        
        # 3. 調整 GARDEN 權重
        if self._garden:
            self._garden.learn_from_interaction(user_message, response, user_feedback)
        
        # 4. 更新學習率
        self._learning_rate = self._adapt_rate(user_feedback)
```

**驗收**: 用戶糾正後，類似問題的回應改善

### 5.6 Phase 5 測試

| # | 測試案例 |
|---|---|
| 5.6.1 | 10 次互動後 `angela_learning_state.json` 更新 |
| 5.6.2 | ED3N 新概念持久化到 HAM |
| 5.6.3 | 重啟後對話歷史仍在 |
| 5.6.4 | 常用記憶重要性提升 |
| 5.6.5 | 用戶糾正後回應改善 |
| 5.6.6 | 學習率根據回饋調整 |

---

## Phase 6: 端到端整合測試

**目標**: 驗證完整流程

### 6.1 整合測試案例（14 條）

| # | 輸入 | 預期流程 | 預期結果 |
|---|---|---|---|
| 6.1.1 | `"搜尋台北天氣"` | classify→SEARCH→gate→auto_execute→web_search→inject→LLM | 搜尋結果回應 |
| 6.1.2 | `"讀取 temp.txt"` | classify→FILE→gate→auto_execute→file_ops→inject→LLM | 檔案內容回應 |
| 6.1.3 | `"刪除 temp.txt"` | classify→FILE→gate→reject→LLM | 說明不可逆 |
| 6.1.4 | `"刪除全部檔案"` | classify→FILE→gate→reject(0.02)→LLM | 強烈警告 |
| 6.1.5 | `"幫我查字典"` | classify→COMMAND→gate→confirm→用戶回"好"→execute→LLM | 查詢結果 |
| 6.1.6 | `"開玩笑"` | classify→EXECUTE→gate→reject→LLM | 正常對話 |
| 6.1.7 | `"不要搜尋"` | classify→gate→negation→reject→LLM | 確認取消 |
| 6.1.8 | `"建立任務：買牛奶"` | classify→TASK→gate→confirm→用戶回"好"→task_manager→LLM | 任務建立 |
| 6.1.9 | `"執行 print('hi')"` | classify→CODE→gate→confirm→用戶回"好"→code_execution→LLM | 執行結果 |
| 6.1.10 | `"你是誰"` | classify→GREETING→ED3N reflex→LLM | 自我介紹 |
| 6.1.11 | `"123 + 456"` | classify→MATH→ED3N→LLM | `"579"` |
| 6.1.12 | 續行 3 次 | context.continuation_count >= 3 | 強制停止 |
| 6.1.13 | `"今天天氣"` → `"那明天呢"` | 跨 turn context | 基於上次結果 |
| 6.1.14 | 重啟後 `"你記得我嗎"` | 載入 session | 記得之前的對話 |

### 6.2 效能基準

| 指標 | 目標 |
|---|---|
| ED3N 反射回應延遲 | < 1ms |
| ED3N 分類延遲 | < 5ms |
| GARDEN 回應延遲 | < 50ms |
| Handler 執行延遲 | < 100ms |
| 端到端延遲（含 LLM） | < 2s |

---

## 實施順序與時程

| Phase | 內容 | 預估工時 | 優先級 |
|---|---|---|---|
| **Phase 3** | ED3N 能力補強 | 5-7 天 | 🔴 最高 |
| 3.1 | 擴充字典 preset | 1 天 | |
| 3.2 | 啟用分類輔助 | 0.5 天 | |
| 3.3 | 同義詞展開 | 1 天 | |
| 3.4 | 反射層擴充 | 1 天 | |
| 3.5 | 數學擴充 | 0.5 天 | |
| 3.6 | Handler 實作（6個） | 2-3 天 | |
| **Phase 4** | GARDEN 整合優勢 | 3-5 天 | 🟡 高 |
| 4.1 | ChromaDB 替代 SentenceTransformer | 1 天 | |
| 4.2 | 知識圖譜導入 | 1 天 | |
| 4.3 | 多步驟推理 | 1 天 | |
| 4.4 | 情緒理解增強 | 0.5 天 | |
| 4.5 | GARDEN 持續學習 | 1 天 | |
| **Phase 5** | 持續學習整合 | 3-4 天 | 🟡 高 |
| 5.1 | 啟用 ED3N 持續學習 | 0.5 天 | |
| 5.2 | ED3N → HAM 同步 | 1 天 | |
| 5.3 | 神經可塑性整合 | 1 天 | |
| 5.4 | 跨 Session 記憶 | 1 天 | |
| 5.5 | 學習回饋循環 | 0.5 天 | |
| **Phase 6** | 端到端測試 | 2-3 天 | 🟢 中 |
| 6.1 | 14 條整合測試 | 2 天 | |
| 6.2 | 效能基準 | 1 天 | |
| **總計** | | **13-19 天** | |

---

## 驗收標準

### ED3N 獨立（不依賴 GARDEN）
- [ ] 字典 preset >= 250 條
- [ ] 反射規則 >= 50 條
- [ ] 日常對話覆蓋率 >= 80%（不 fallback）
- [ ] 同義詞展開正常運作
- [ ] 多位數數學運算正確
- [ ] 6 個 handler 全部可用
- [ ] 102 舊測試 + 30+ 新測試通過

### GARDEN 加持
- [ ] 語意檢索相似度 > 0.7（同義查詢）
- [ ] 知識圖譜導入 >= 100K 條
- [ ] 多步驟推理正確
- [ ] 情緒調整回應正常
- [ ] GARDEN 回應品質 > ED3N

### 持續學習
- [ ] ED3N 學習管線啟用
- [ ] ED3N → HAM 同步正常
- [ ] 跨 session 記憶持久化
- [ ] 學習回饋循環正常
- [ ] 重啟後記憶不丟失

### 整體
- [ ] 14 條端到端測試通過
- [ ] 效能基準達標
- [ ] 無 regression（現有功能不受影響）
