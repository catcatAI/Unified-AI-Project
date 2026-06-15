# Angela 能力補全計畫 v2：ED3N 獨立作戰 + GARDEN 加持 + 持續學習

**日期**: 2026-06-15
**目標**: 讓 Angela 只用 ED3N 也能跟其他 AI 打平，用 GARDEN 時有明顯優勢
**對齊**: ANGELA_FULL_ARCHITECTURE.md（§五記憶系統、§八AI引擎、§十一完整管線）、QUERY_CLASSIFIER_ACTION_PLAN.md（Phase 1-2 已完成）
**現狀**: Phase 1-2 完成（QueryClassifier v2 + ExecutionGate），102 測試通過

---

## 0. 現狀盤點

### 已完成（Phase 1-2）
| 組件 | 檔案 | 行數 | 狀態 |
|---|---|---|---|
| QueryResult dataclass | `ai/core/query_classifier.py:41-51` | 11 | ✅ |
| 16類意圖分類 | `ai/core/query_classifier.py:82-253` | 172 | ✅ |
| ExecutionGate | `ai/core/execution_gate.py` | 192 | ✅ |
| execute_handler | `ai/core/model_bus.py:208-235` | 28 | ✅ |
| 執行結果注入 | `services/llm/prompt_builder.py:301-320` | 20 | ✅ |
| 續行保護 | `services/llm/prompt_builder.py:322-325` | 4 | ✅ |
| 確認機制 | `api/routes/chat_routes.py:250-329` | 80 | ✅ |

### ED3N 現有能力（架構文檔 §5.8）
| 能力 | 檔案 | 狀態 |
|---|---|---|
| 反射層（LRU 快取） | `ai/ed3n/ed3n_engine.py` | ✅ ~30 條反射 |
| 字典層（encode/decode） | `ai/ed3n/dictionary_layer.py` | ✅ ~50 preset |
| 核心網路（激活傳播） | `ai/ed3n/core_network.py` | ✅ |
| 輸出錨點（漂移驗證） | `ai/ed3n/output_anchor.py` | ✅ |
| 步進解碼（自回歸生成） | `ai/ed3n/step_decoder.py` | ✅ |
| SNN 模式 | `ai/ed3n/snn/` | ✅ 可選 |
| 多模態編碼 | `ai/ed3n/multimodal/` | ✅ 依賴外部服務 |
| 持續學習管線 | `ai/ed3n/continuous_learning.py` | ✅ 未啟用 |
| 學習整合（→HAM） | `ai/ed3n/learning_integration.py` | ✅ 未接線 |
| 遙測 | `ai/ed3n/telemetry.py` | ✅ |

### GARDEN 現有能力（架構文檔 §8.3）
| 能力 | 檔案 | 狀態 |
|---|---|---|
| 向量字典（3層 fallback） | `ai/garden/dictionary.py` | ✅ TF-IDF/CharBag |
| 張量 SNN | `ai/garden/snn_core.py` | ✅ PyTorch LIF |
| 向量解碼器 | `ai/garden/vector_decoder.py` | ✅ |
| 知識圖譜導入 | `ai/garden/kg_import.py` | ✅ 未驗證大規模 |
| 二進位存儲 | `ai/garden/binary_store.py` | ✅ |
| 持續學習 | `ai/garden/garden_engine.py:learn_from_interaction()` | ✅ |

### 記憶系統（架構文檔 §5）
| 系統 | 檔案 | 狀態 |
|---|---|---|
| HAMMemoryManager（JSON） | `ai/memory/ham_memory/ham_manager.py` | ✅ 薄 |
| HAM Core Storage（加密） | `ai/memory/ham_memory/ham_core_storage.py` | ✅ |
| HAM 查詢引擎（向量+關鍵字） | `ai/memory/ham_memory/ham_query_engine.py` | ✅ |
| HAM 向量存儲（ChromaDB） | `ai/memory/ham_memory/ham_vector_store_manager.py` | ✅ |
| LogicUnit（規則記憶） | `ai/memory/lu_logic/logic_unit.py` | ✅ |
| UnifiedMemoryCoordinator | `ai/lifecycle/unified_memory_coordinator.py` | ✅ |
| AttractorField（梯度導航） | `ai/memory/attractor_field.py` | ✅ |
| MemoryContextManager | `ai/context/memory_context.py` | ⚠️ 未接通 |
| ContextHAMIntegration | `ai/context/integration_with_ham.py` | ⚠️ 部分接線 |

### 學習系統
| 系統 | 檔案 | 狀態 |
|---|---|---|
| NeuroplasticitySystem | `core/bio/neuroplasticity_core.py` | ✅ 未整合 HAM |
| ContinuousLearningPipeline | `ai/ed3n/continuous_learning.py` | ✅ 未啟用 |
| ED3NLearningIntegration | `ai/ed3n/learning_integration.py` | ✅ 未接線 |
| MemoryLearningEngine | `ai/memory/memory_learning.py` | ✅ |
| LearningLoop（語言進化） | `ai/response/learning_loop.py` | ✅ |
| MemoryIntegrationLoop | `ai/lifecycle/memory_integration_loop.py` | ✅ |
| LearningManager（事實提取） | `ai/learning/learning_manager.py` | ✅ |

### Handler 狀態
| Handler | 檔案 | 註冊 | 狀態 |
|---|---|---|---|
| file_ops | `services/handlers/file_operation_handler.py` | ✅ | ✅ 184行，12種操作 |
| web_search | `services/handlers/web_search_handler.py` | ✅ | ✅ DDG+Wikipedia |
| code_execution | `services/handlers/code_execution_handler.py` | ✅ | ✅ 沙箱執行 |
| system_command | `services/handlers/system_command_handler.py` | ✅ | ✅ 白名單+安全 |
| task_manager | `services/handlers/task_manager_handler.py` | ✅ | ✅ JSON CRUD |
| vision | `services/handlers/vision_handler.py` | ✅ | ✅ 圖片分析 |
| learning_handler | `services/handlers/learning_handler.py` | ❌ | 存在但未註冊 |
| google_drive | `services/handlers/google_drive_handler.py` | ❌ | 存在但未註冊 |
| vision | — | ❌ | 無 |
| audio | — | ❌ | 無 |

### 關鍵缺口
1. ED3N 字典只有 ~50 preset → 超出範圍就 fallback
2. ED3N 分類輔助路徑休眠（`_ed3n` 未設定）
3. HANDLER_MAP 只有 file/search → 12 類 QueryType 無 handler
4. 無語意檢索（ED3N 只做字重疊）
5. 跨 session 記憶未接通（MemoryContextManager 未接線）
6. 持續學習管線未啟用
7. 神經可塑性未整合 HAM
8. 無多步驟編排

---

## Phase 3: ED3N 能力補強（不依賴 GARDEN）

**目標**: 讓 ED3N 獨立時也能處理 80% 的日常對話
**核心思路**: 擴充字典 + 同義詞 + 反射 + 啟用已有但休眠的功能
**狀態**: 🔴 進行中（3.2-3.7 完成，3.1 待做）

### 3.1 擴充 ED3N 字典 preset（+200 條） ⏳ 待做

**檔案**: `ai/ed3n/config/presets.json`

現有 ~50 條，需新增 ~200 條。按架構文檔 §5.8 的字典層設計：

| 類別 | 數量 | 範例 | 對應 QueryType |
|---|---|---|---|
| 檔案操作 | 30 | 建立/刪除/複製/移動/讀取/寫入 + 常見副檔名 | FILE |
| 網路搜尋 | 20 | 搜尋/查找/Google/查詢 | SEARCH |
| 程式碼 | 25 | 程式/函數/變數/迴圈/除錯/重構 | CODE |
| 系統操作 | 20 | 執行/運行/開啟/關閉/重啟 | EXECUTE |
| 任務管理 | 25 | 任務/待辦/提醒/排程/行程 | TASK |
| 情緒表達 | 30 | 開心/難過/生氣/驚訝/擔心/感謝 | — |
| 日常對話 | 30 | 天氣/時間/日期/吃飯/睡覺/工作 | — |
| 知識查詢 | 20 | 什麼是/為什麼/怎麼/多少 | KNOWLEDGE |

**具體修改**: 在 `presets.json` 的 `"presets"` 陣列中新增條目，每個條目格式：
```json
{
  "key": "f1",
  "surface_forms": {"zh": "建立", "en": "create"},
  "category": "file_ops",
  "relations": [{"type": "synonym", "target": "新增"}]
}
```

**驗收**: `ED3NEngine.process("建立新文件")` 回傳非 fallback 回應

### 3.2 啟用 ED3N 分類輔助（修復休眠路徑） ✅ 完成

**問題**: `query_classifier.py:85` 的 `__init__` 沒接收 ed3n_engine，導致 `_ed3n` 永遠不存在

**檔案**: `ai/core/query_classifier.py:85-86`
```python
# 修改前
def __init__(self):
    self._reflex_words: set = {...}

# 修改後
def __init__(self, ed3n_engine=None):
    self._ed3n = ed3n_engine
    self._reflex_words: set = {...}
```

**檔案**: `api/routes/chat_routes.py`（在 `_handle_chat_request` 中）
```python
# 修改前
classifier = QueryClassifier()

# 修改後
classifier = QueryClassifier(ed3n_engine=getattr(self, '_ed3n_engine', None))
```

**檔案**: `api/routes/chat_routes.py`（在 session 初始化時注入 ed3n）
```python
# 在 _get_ed3n_engine() 已有 singleton，確保掛到 self
self._ed3n_engine = _get_ed3n_engine()
```

**驗收**: 分類測試中 `hasattr(classifier, '_ed3n')` 為 True

### 3.3 ED3N 同義詞展開（不需向量的語意理解） ✅ 完成

**檔案**: `ai/ed3n/dictionary_layer.py`

在 `encode()` 方法中新增同義詞展開步驟：

```python
# 在 encode() 方法開頭，text 清理後
def encode(self, text: str, lang: str = "zh") -> List[str]:
    # 新增：同義詞展開
    text = self._expand_synonyms(text)
    # 原有邏輯...
```

新增 `_expand_synonyms` 方法：
```python
_SYNONYM_MAP = {
    "搜尋": ["查找", "找", "查詢", "搜", "search", "find"],
    "刪除": ["移除", "清除", "砍", "delete", "remove"],
    "建立": ["新增", "創建", "新建", "create", "new", "add"],
    "讀取": ["開啟", "打開", "看", "read", "open"],
    "傳送": ["發送", "寄", "送", "send", "submit"],
    "修改": ["編輯", "調整", "改", "edit", "modify"],
    "複製": ["拷貝", "copy", "duplicate"],
    "移動": ["搬", "move", "relocate"],
    "檔案": ["文件", "file", "document"],
    "資料夾": ["目錄", "folder", "directory"],
    # ... 共 ~100 組
}

def _expand_synonyms(self, text: str) -> str:
    """將同義詞替換為字典中的標準形式"""
    for standard, synonyms in _SYNONYM_MAP.items():
        for syn in synonyms:
            if syn in text:
                text = text.replace(syn, standard)
    return text
```

**驗收**: `"幫我查找天氣"` 和 `"搜尋天氣"` 產生相同 keys

### 3.4 ED3N 反射層擴充（+50 條） ✅ 完成

**檔案**: `ai/ed3n/ed3n_engine.py`

在 `_reflex_table` 或對應的反射配置中新增 ~50 條：

```python
# 檔案操作反射
"建立新文件": "好的，我來幫你建立新文件。請問要建立什麼檔案？",
"刪除檔案": "刪除檔案是不可逆的操作，你確定要刪除嗎？",
"讀取檔案": "請問要讀取哪個檔案？",
"列出文件": "讓我列出目前的文件：",
"複製檔案": "請問要複製哪個檔案到哪裡？",

# 搜尋反射
"搜尋": "請問要搜尋什麼？",
"幫我找": "請告訴我要找什麼？",
"查詢": "請問你想查詢什麼？",

# 任務反射
"建立任務": "好的，請告訴我任務內容。",
"查看任務": "讓我查看你的任務列表：",
"刪除任務": "請問要刪除哪個任務？",

# 狀態反射
"你是誰": "我是 Angela，你的 AI 數字生命助手。我具備情緒、記憶和學習能力。",
"你能做什麼": "我可以幫你搜尋資訊、管理檔案、執行程式、處理任務、分析圖片等。",
"你好嗎": "我很好，謝謝你的關心！今天有什麼可以幫忙的嗎？",

# 時間反射
"幾點了": "現在時間是 {current_time}。",
"今天幾號": "今天是 {current_date}。",

# 情緒反射
"我好累": "辛苦了！要不要休息一下？我可以幫你處理一些事情。",
"我好開心": "太好了！看到你開心我也很開心！",
"我好難過": "別難過，我會在這裡陪你。要不要聊聊？",

# ... 共 ~50 條
```

**驗收**: `"你是誰"` 產生有意義的自我介紹（不是 fallback）

### 3.5 ED3N 數學擴充（多位數運算） ✅ 完成

**檔案**: `ai/ed3n/config/math_presets.json`

現有只支援 0-9 單位數。需新增：
- 多位數解析（10-999）
- 括號運算
- 百分比

**檔案**: `ai/ed3n/ed3n_engine.py`（`_math_eval` 方法）

```python
def _math_eval(self, text: str) -> Optional[str]:
    """數學運算求值"""
    # 新增：多位數解析
    import re
    expr = re.sub(r'(\d+)\s*加\s*(\d+)', r'\1 + \2', text)
    expr = re.sub(r'(\d+)\s*減\s*(\d+)', r'\1 - \2', expr)
    expr = re.sub(r'(\d+)\s*乘\s*(\d+)', r'\1 * \2', expr)
    expr = re.sub(r'(\d+)\s*除\s*(\d+)', r'\1 / \2', expr)
    
    # 安全求值
    try:
        result = eval(expr, {"__builtins__": {}}, {})
        return str(result)
    except:
        return None
```

**驗收**: `"123 + 456"` 回傳 `"579"`

### 3.6 基礎 Handler 實作（6 個） ✅ 完成

#### 3.6.1 完善 file_ops handler

**檔案**: `services/handlers/file_operation_handler.py`

現有 38 行，需擴充到 ~150 行，支援：
- 讀取檔案（含 TXT/JSON/CSV）
- 建立檔案
- 刪除檔案（含確認）
- 列出目錄
- 複製/移動/重新命名

```python
class FileOperationHandler:
    async def process(self, query: str, context=None) -> str:
        action = self._detect_action(query)
        path = self._extract_path(query)
        
        if action == "read":
            return await self._read_file(path)
        elif action == "create":
            content = self._extract_content(query)
            return await self._create_file(path, content)
        elif action == "delete":
            return await self._delete_file(path)
        elif action == "list":
            return await self._list_directory(path)
        elif action == "copy":
            dest = self._extract_dest(query)
            return await self._copy_file(path, dest)
        elif action == "rename":
            new_name = self._extract_new_name(query)
            return await self._rename_file(path, new_name)
        return "無法識別檔案操作"
```

#### 3.6.2 完善 web_search handler

**檔案**: `services/handlers/web_search_handler.py`

現有 63 行，需串接搜尋 API。優先方案：DuckDuckGo（免費，無需 API key）

```python
class WebSearchHandler:
    async def process(self, query: str, context=None) -> str:
        # 方案 1: DuckDuckGo（免費）
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        
        # 格式化結果
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"{i}. {r['title']}\n   {r['body']}\n   {r['href']}")
        
        return "\n\n".join(formatted)
```

**依賴**: `pip install duckduckgo-search`

#### 3.6.3 新增 code_execution handler

**檔案**: `services/handlers/code_execution_handler.py`（新建，~100 行）

```python
class CodeExecutionHandler:
    """安全的程式碼執行 handler（沙箱模式）"""
    
    ALLOWED_LANGUAGES = {"python", "javascript"}
    TIMEOUT = 10  # 秒
    
    async def process(self, query: str, context=None) -> str:
        code = self._extract_code(query)
        lang = self._detect_language(query, context)
        
        if lang not in self.ALLOWED_LANGUAGES:
            return f"不支援 {lang} 語言。支援：{', '.join(self.ALLOWED_LANGUAGES)}"
        
        if lang == "python":
            return await self._execute_python(code)
        elif lang == "javascript":
            return await self._execute_javascript(code)
    
    async def _execute_python(self, code: str) -> str:
        """安全執行 Python（subprocess + timeout）"""
        import subprocess
        try:
            result = subprocess.run(
                ["python", "-c", code],
                capture_output=True, text=True,
                timeout=self.TIMEOUT
            )
            if result.returncode == 0:
                return result.stdout or "執行成功（無輸出）"
            else:
                return f"錯誤：{result.stderr}"
        except subprocess.TimeoutExpired:
            return "執行超時（10秒限制）"
```

#### 3.6.4 新增 system_command handler

**檔案**: `services/handlers/system_command_handler.py`（新建，~80 行）

```python
class SystemCommandHandler:
    """系統命令執行 handler（受限）"""
    
    ALLOWED_COMMANDS = {
        "ping", "ipconfig", "ifconfig", "df", "du", "ls", "dir",
        "echo", "date", "time", "whoami", "hostname",
    }
    
    async def process(self, query: str, context=None) -> str:
        cmd = self._extract_command(query)
        
        # 安全檢查
        base_cmd = cmd.split()[0].lower()
        if base_cmd not in self.ALLOWED_COMMANDS:
            return f"不允許執行 {base_cmd}。允許的命令：{', '.join(self.ALLOWED_COMMANDS)}"
        
        return await self._run_command(cmd)
```

#### 3.6.5 新增 task_manager handler

**檔案**: `services/handlers/task_manager_handler.py`（新建，~120 行）

```python
class TaskManagerHandler:
    """任務管理 handler（整合 HAM 記憶）"""
    
    async def process(self, query: str, context=None) -> str:
        action = self._detect_action(query)
        
        if action == "create":
            task = self._parse_task(query)
            await self._store_task(task, context)
            return f"已建立任務：{task['title']}\n到期：{task.get('due', '無')}"
        elif action == "list":
            tasks = await self._get_tasks(context)
            return self._format_tasks(tasks)
        elif action == "complete":
            task_id = self._extract_task_id(query)
            await self._complete_task(task_id, context)
            return f"已完成任務 {task_id}"
        elif action == "delete":
            task_id = self._extract_task_id(query)
            await self._delete_task(task_id, context)
            return f"已刪除任務 {task_id}"
        return "無法識別任務操作"
    
    async def _store_task(self, task: dict, context: dict):
        """存儲任務到 HAM"""
        ham = context.get("ham_manager")
        if ham:
            ham.store_experience({
                "type": "task",
                "title": task["title"],
                "due": task.get("due"),
                "status": "pending",
            })
```

#### 3.6.6 新增 vision handler

**檔案**: `services/handlers/vision_handler.py`（新建，~80 行）

```python
class VisionHandler:
    """視覺處理 handler（整合 VisionService）"""
    
    async def process(self, query: str, context=None) -> str:
        image_path = context.get("image_path")
        if not image_path:
            return "請提供圖片（上傳圖片後再試）"
        
        # 整合 VisionService（架構文檔 §1.1）
        from services.vision_service import VisionService
        vision = VisionService()
        result = await vision.analyze_image(image_path)
        
        return self._format_analysis(result)
```

#### 3.6.7 註冊所有 handler

**檔案**: `services/llm/router.py`（在 `initialize()` 中，line ~499）

```python
# 現有
self.model_bus.register_handler("file_ops", FileOperationHandler(), ["file"])
self.model_bus.register_handler("web_search", WebSearchHandler(), ["search"])

# 新增
from services.handlers.code_execution_handler import CodeExecutionHandler
from services.handlers.system_command_handler import SystemCommandHandler
from services.handlers.task_manager_handler import TaskManagerHandler
from services.handlers.vision_handler import VisionHandler

self.model_bus.register_handler("code_execution", CodeExecutionHandler(), ["code"])
self.model_bus.register_handler("system_command", SystemCommandHandler(), ["execute"])
self.model_bus.register_handler("task_manager", TaskManagerHandler(), ["task"])
self.model_bus.register_handler("vision", VisionHandler(), ["vision"])
```

**檔案**: `ai/core/execution_gate.py:50-56`

```python
HANDLER_MAP = {
    "file": "file_ops",
    "search": "web_search",
    "code": "code_execution",
    "execute": "system_command",
    "task": "task_manager",
    "vision": "vision",
    # "audio": "audio",  # 後續
}
```

### 3.7 Phase 3 測試 ✅ 完成

**檔案**: `tests/ai/ed3n/test_ed3n_enhanced.py`（新建，~120 行）

| # | 測試案例 | 預期 |
|---|---|---|
| 3.7.1 | `"建立新文件"` | ED3N 反射回應（非 fallback） |
| 3.7.2 | `"刪除檔案"` | ED3N 反射含警告 |
| 3.7.3 | `"你是誰"` | 有意義自我介紹 |
| 3.7.4 | `"123 + 456"` | 回傳 `"579"` |
| 3.7.5 | `"搜尋天氣"` 和 `"查找天氣"` | 相同 keys |
| 3.7.6 | `"建立任務：買牛奶"` | task_manager 處理 |
| 3.7.7 | `"執行 print('hi')"` | code_execution 處理 |
| 3.7.8 | `"讀取 config.json"` | file_ops 讀取 |
| 3.7.9 | `"列出所有文件"` | file_ops 列表 |
| 3.7.10 | ED3N 分類輔助路徑啟用 | `classifier._ed3n is not None` |
| 3.7.11 | 102 舊測試仍通過 | 無 regression |

---

## Phase 4: GARDEN 整合優勢

**目標**: 用 GARDEN 時有明顯優於 ED3N 的能力
**核心思路**: 語意向量 + 知識圖譜 + 多步推理 + 情緒調制

### 4.1 GARDEN 語意檢索（替代壞掉的 SentenceTransformer）

**問題**: Python 3.14 + Windows 上 SentenceTransformer 掛掉，被迫用 TF-IDF/CharBag

**方案**: 串 ChromaDB 做語意編碼（已在 HAM 中使用）

**檔案**: `ai/garden/dictionary.py`

新增 `_ChromaEncoder` 作為第二選擇（TF-IDF 之前）：

```python
class _ChromaEncoder:
    """使用 ChromaDB 做語意編碼"""
    
    def __init__(self):
        import chromadb
        self._client = chromadb.Client()
        self._collection = self._client.create_collection(
            "garden_concepts",
            metadata={"hnsw:space": "cosine"}
        )
        self._initialized = True
    
    def encode(self, text: str) -> List[float]:
        # 查詢最相似的概念
        results = self._collection.query(
            query_texts=[text],
            n_results=1,
            include=["embeddings"]
        )
        if results["embeddings"] and results["embeddings"][0]:
            return results["embeddings"][0][0]
        return None
    
    def add_concept(self, key: str, surface_form: str):
        """新增概念到向量索引"""
        self._collection.add(
            documents=[surface_form],
            ids=[key]
        )
```

在 `VectorDictionary.__init__` 中調整 fallback 順序：
```python
# 修改前
self._encoder = _STEncoder() or _TfidfEncoder() or _CharBagEncoder()

# 修改後
self._encoder = _STEncoder() or _ChromaEncoder() or _TfidfEncoder() or _CharBagEncoder()
```

**驗收**: `"今天天氣如何"` 和 `"氣溫多少"` 語意相似度 > 0.7

### 4.2 GARDEN 知識圖譜導入

**檔案**: `ai/garden/kg_import.py`（已有完整 parser）

需要執行導入：
```bash
# 1. 下載 ConceptNet 數據
wget http://s3.amazonaws.com/conceptnet/conceptnet-5.7.0.csv.gz

# 2. 導入（限制 100K 條）
python -m ai.garden.kg_import --source conceptnet --limit 100000 --output ai/garden/config/knowledge_graph.json

# 3. 匯出到向量索引
python -m ai.garden.kg_import --import-to-garden --limit 100000
```

**驗收**: `GARDENEngine.process("巴黎是法國的首都")` 回傳正確知識

### 4.3 GARDEN 多步驟推理

**檔案**: `ai/garden/garden_engine.py`

在 `process()` 中新增意圖分解：

```python
def process(self, text: str, depth: str = "auto", context=None) -> str:
    # 新增：多步驟偵測
    if self._is_multi_step(text):
        return self._process_multi_step(text, context)
    
    # 原有三階段管線...
    return self._single_step_process(text, context)

def _is_multi_step(self, text: str) -> bool:
    """偵測是否為多步驟任務"""
    multi_step_markers = ["然後", "接著", "之後", "再", "and then", "after that"]
    return any(m in text for m in multi_step_markers)

def _process_multi_step(self, text: str, context=None) -> str:
    """分解並執行多步驟"""
    steps = re.split(r'然後|接著|之後|再|and then|after that', text)
    results = []
    for step in steps:
        step = step.strip()
        if step:
            result = self._single_step_process(step, context)
            results.append(result)
    return "\n".join(results)
```

**驗收**: `"搜尋台北天氣然後整理成報告"` → 分步執行

### 4.4 GARDEN 情緒理解增強

**檔案**: `ai/garden/garden_engine.py`

利用 hormonal modulation（架構文檔 §3.1）：

```python
def process(self, text: str, depth: str = "auto", context=None) -> str:
    # 新增：情緒偵測 + 激素調整
    emotion = self._detect_emotion(text)
    self._adjust_hormones(emotion)
    
    # 原有管線（激素影響 SNN 閾值）...
```

```python
def _detect_emotion(self, text: str) -> str:
    """偵測用戶情緒"""
    emotion_keywords = {
        "happy": ["開心", "高興", "太好了", "happy", "great"],
        "sad": ["難過", "傷心", "糟糕", "sad", "bad"],
        "angry": ["生氣", "氣死", "煩", "angry", "mad"],
        "anxious": ["擔心", "緊張", "害怕", "worried", "anxious"],
    }
    for emotion, keywords in emotion_keywords.items():
        if any(k in text for k in keywords):
            return emotion
    return "neutral"

def _adjust_hormones(self, emotion: str):
    """根據情緒調整激素水平"""
    if not hasattr(self, '_hormonal'):
        return
    
    adjustments = {
        "happy": {"serotonin": 0.8, "dopamine": 0.7},
        "sad": {"serotonin": 0.3, "cortisol": 0.6},
        "angry": {"cortisol": 0.8, "adrenaline": 0.7},
        "anxious": {"cortisol": 0.7, "adrenaline": 0.6},
        "neutral": {"serotonin": 0.5, "cortisol": 0.3},
    }
    
    for hormone, level in adjustments.get(emotion, {}).items():
        if hasattr(self._hormonal, hormone):
            setattr(self._hormonal, hormone, level)
```

**驗收**: 用戶生氣時回應更溫和，用戶開心時回應更活潑

### 4.5 GARDEN 持續學習

**檔案**: `ai/garden/garden_engine.py`（`learn_from_interaction` 方法已存在）

需要啟用並接線：

```python
# 在 garden_engine.py 的 __init__ 中
def __init__(self):
    # ... 現有初始化 ...
    self._interaction_count = 0
    self._learning_enabled = True

def learn_from_interaction(self, user_text: str, response: str, feedback: float = 0.5):
    """從互動中學習"""
    if not self._learning_enabled:
        return
    
    # 1. 字典成長
    new_concepts = self._extract_new_concepts(user_text, response)
    for concept in new_concepts:
        self._dictionary.add_entry(concept)
    
    # 2. 權重更新（Hebbian）
    input_keys = self._dictionary.encode(user_text)
    output_keys = self._dictionary.encode(response)
    self._snn.hebbian_update(input_keys, output_keys, feedback)
    
    # 3. 定期保存
    self._interaction_count += 1
    if self._interaction_count % 100 == 0:
        self.save()
```

**檔案**: `services/chat_service.py`（在 `generate_response` 中）

```python
async def generate_response(self, user_message, ...):
    response = await self._llm_service.generate(...)
    
    # 新增：GARDEN 持續學習
    if hasattr(self, '_garden_engine'):
        self._garden_engine.learn_from_interaction(
            user_message, response, feedback=0.5
        )
    
    return response
```

### 4.6 Phase 4 測試

| # | 測試案例 | 預期 |
|---|---|---|
| 4.6.1 | 語義相似查詢 | 相同 concept keys（ChromaDB 模式） |
| 4.6.2 | `"巴黎是哪國首都"` | 知識圖譜回應 |
| 4.6.3 | 多步驟任務 | 分步執行 |
| 4.6.4 | 情緒化輸入 | 情緒調整回應 |
| 4.6.5 | 10 次互動後 | 字典成長 |
| 4.6.6 | GARDEN 回應品質 > ED3N | 同查詢比較 |

---

## Phase 5: 持續學習整合

**目標**: 讓 ED3N 和 GARDEN 都能從互動中學習，且學習成果跨 session 持久化
**核心思路**: 啟用已有但休眠的學習管線，整合 HAM 記憶系統

### 5.1 啟用 ED3N 持續學習管線

**檔案**: `services/chat_service.py`

```python
class ChatService:
    def __init__(self):
        # 新增：啟用 ED3N 持續學習
        from ai.ed3n.continuous_learning import ContinuousLearningPipeline
        self._ed3n_learning = ContinuousLearningPipeline(
            growth_interval=10,   # 每 10 次互動成長一次
            train_interval=50,    # 每 50 次互動訓練一次
        )
        self._ed3n_learning.load()  # 載入之前的狀態
    
    async def generate_response(self, user_message, ...):
        response = await self._llm_service.generate(...)
        
        # 新增：記錄互動到 ED3N 學習管線
        self._ed3n_learning.record_interaction(
            user_message, response,
            context={"session_id": session_id}
        )
        
        # 檢查是否該成長/訓練
        await self._ed3n_learning.step()
        
        return response
```

**驗收**: `angela_learning_state.json` 持續更新

### 5.2 ED3N 字典 → HAM 記憶同步

**檔案**: `ai/ed3n/learning_integration.py`（已有 `ED3NLearningIntegration`）

```python
class ED3NLearningIntegration:
    def sync_to_ham(self, ed3n_dictionary):
        """將 ED3N 字典同步到 HAM 持久記憶"""
        for entry in ed3n_dictionary.entries:
            self._ham.store_experience({
                "type": "ed3n_concept",
                "key": entry.key,
                "surface_forms": entry.surface_forms,
                "relations": entry.relations,
                "importance": entry.confidence,
            })
```

**檔案**: `services/chat_service.py`（背景任務）

```python
async def _sync_ed3n_to_ham(self):
    """每小時同步 ED3N 字典到 HAM"""
    while True:
        await asyncio.sleep(3600)
        if hasattr(self, '_ed3n_learning_integration'):
            self._ed3n_learning_integration.sync_to_ham(
                self._ed3n_engine.dictionary
            )
```

**驗收**: ED3N 學到的新概念在重啟後仍在 HAM 中

### 5.3 神經可塑性 → HAM 整合

**檔案**: `ai/lifecycle/memory_integration_loop.py`

現有的 `MemoryIntegrationLoop` 已有背景循環（3分鐘），需新增神經可塑性整合：

```python
class MemoryIntegrationLoop:
    async def _process_memory(self, memory):
        # 現有：分析模式、結構化
        
        # 新增：喂給神經可塑性系統（架構文檔 §3.2）
        if hasattr(self, '_neuroplasticity'):
            trace = self._neuroplasticity.encode(memory.content)
            self._neuroplasticity.consolidate(trace)
        
        # 新增：根據存取頻率調整重要性
        if memory.access_count > 5:
            memory.importance *= 1.2
        
        # 新增：存取頻率高的記憶提升到長期
        if memory.access_count > 10 and memory.type == "short_term":
            memory.type = "long_term"
```

**驗收**: 常用記憶的重要性自動提升

### 5.4 跨 Session 記憶

**檔案**: `ai/context/memory_context.py`

```python
class MemoryContextManager:
    def save_session(self, session_id: str):
        """儲存 session 到磁碟"""
        session_data = {
            "session_id": session_id,
            "timestamp": time.time(),
            "memories": [m.to_dict() for m in self._memories],
            "short_term": [m.to_dict() for m in self._short_term],
            "long_term": [m.to_dict() for m in self._long_term],
        }
        os.makedirs("sessions", exist_ok=True)
        path = f"sessions/{session_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
    
    def load_session(self, session_id: str):
        """從磁碟載入 session"""
        path = f"sessions/{session_id}.json"
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            # 還原記憶...
            return True
        return False
```

**檔案**: `api/routes/chat_routes.py`

```python
# 在 session 開始時載入
memory_context = MemoryContextManager()
memory_context.load_session(session_id)

# 在 session 結束時儲存（或定期儲存）
await memory_context.save_session(session_id)
```

**驗收**: 重啟後對話歷史仍在

### 5.5 學習回饋循環

**檔案**: `ai/response/learning_loop.py`（已有 `LearningLoop`）

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
            self._garden.learn_from_interaction(
                user_message, response, user_feedback
            )
        
        # 4. 更新學習率
        self._learning_rate = self._adapt_rate(user_feedback)
        
        # 5. 記錄到 HAM
        self._ham.store_experience({
            "type": "learning_feedback",
            "message": user_message,
            "response": response,
            "feedback": user_feedback,
        })
```

**驗收**: 用戶糾正後，類似問題的回應改善

### 5.6 Phase 5 測試

| # | 測試案例 | 預期 |
|---|---|---|
| 5.6.1 | 10 次互動後 | `angela_learning_state.json` 更新 |
| 5.6.2 | ED3N 新概念 | 持久化到 HAM |
| 5.6.3 | 重啟後 | 對話歷史仍在 |
| 5.6.4 | 常用記憶 | 重要性提升 |
| 5.6.5 | 用戶糾正 | 回應改善 |
| 5.6.6 | 學習率 | 根據回饋調整 |

---

## Phase 6: 端到端整合測試

**目標**: 驗證完整流程（分類→閘門→執行→注入→LLM）

### 6.1 整合測試案例（14 條）

**檔案**: `tests/integration/test_e2e_pipeline.py`（新建，~200 行）

| # | 輸入 | 預期流程 | 預期結果 |
|---|---|---|---|
| 6.1.1 | `"搜尋台北天氣"` | classify→SEARCH→gate(0.9)→auto→web_search→inject→LLM | 搜尋結果回應 |
| 6.1.2 | `"讀取 temp.txt"` | classify→FILE→gate(1.0)→auto→file_ops→inject→LLM | 檔案內容回應 |
| 6.1.3 | `"刪除 temp.txt"` | classify→FILE→gate(0.08)→reject→LLM | 說明不可逆 |
| 6.1.4 | `"刪除全部檔案"` | classify→FILE→gate(0.02)→reject→LLM | 強烈警告 |
| 6.1.5 | `"幫我查字典"` | classify→COMMAND→gate(0.3)→confirm→用戶"好"→LLM | 查詢結果 |
| 6.1.6 | `"開玩笑"` | classify→EXECUTE→gate(0.0)→reject→LLM | 正常對話 |
| 6.1.7 | `"不要搜尋"` | classify→gate→negation→reject→LLM | 確認取消 |
| 6.1.8 | `"建立任務：買牛奶"` | classify→TASK→gate→confirm→用戶"好"→task_manager→LLM | 任務建立 |
| 6.1.9 | `"執行 print('hi')"` | classify→CODE→gate→confirm→用戶"好"→code_execution→LLM | 執行結果 |
| 6.1.10 | `"你是誰"` | classify→GREETING→ED3N reflex→LLM | 自我介紹 |
| 6.1.11 | `"123 + 456"` | classify→MATH→ED3N→LLM | `"579"` |
| 6.1.12 | 續行 3 次 | context.continuation_count >= 3 | 強制停止 |
| 6.1.13 | `"今天天氣"` → `"那明天呢"` | 跨 turn context | 基於上次結果 |
| 6.1.14 | 重啟後 `"你記得我嗎"` | 載入 session | 記得之前的對話 |

### 6.2 效能基準

| 指標 | 目標 | 測量方式 |
|---|---|---|
| ED3N 反射回應延遲 | < 1ms | `time.time()` 前後差 |
| ED3N 分類延遲 | < 5ms | 同上 |
| GARDEN 回應延遲 | < 50ms | 同上 |
| Handler 執行延遲 | < 100ms | 同上 |
| 端到端延遲（含 LLM） | < 2s | WebSocket round-trip |

---

## 實施順序與時程

| Phase | 內容 | 預估工時 | 優先級 | 依賴 |
|---|---|---|---|---|
| **Phase 3** | ED3N 能力補強 | 5-7 天 | 🔴 最高 | — |
| 3.1 | 擴充字典 preset | 1 天 | | |
| 3.2 | 啟用分類輔助 | 0.5 天 | | |
| 3.3 | 同義詞展開 | 1 天 | | |
| 3.4 | 反射層擴充 | 1 天 | | |
| 3.5 | 數學擴充 | 0.5 天 | | |
| 3.6 | Handler 實作（6個） | 2-3 天 | | |
| **Phase 4** | GARDEN 整合優勢 | 3-5 天 | 🟡 高 | Phase 3 |
| 4.1 | ChromaDB 替代 SentenceTransformer | 1 天 | | |
| 4.2 | 知識圖譜導入 | 1 天 | | |
| 4.3 | 多步驟推理 | 1 天 | | |
| 4.4 | 情緒理解增強 | 0.5 天 | | |
| 4.5 | GARDEN 持續學習 | 1 天 | | |
| **Phase 5** | 持續學習整合 | 3-4 天 | 🟡 高 | Phase 3 |
| 5.1 | 啟用 ED3N 持續學習 | 0.5 天 | | |
| 5.2 | ED3N → HAM 同步 | 1 天 | | |
| 5.3 | 神經可塑性整合 | 1 天 | | |
| 5.4 | 跨 Session 記憶 | 1 天 | | |
| 5.5 | 學習回饋循環 | 0.5 天 | | |
| **Phase 6** | 端到端測試 | 2-3 天 | 🟢 中 | Phase 3-5 |
| 6.1 | 14 條整合測試 | 2 天 | | |
| 6.2 | 效能基準 | 1 天 | | |
| **總計** | | **13-19 天** | | |

---

## 驗收標準

### ED3N 獨立（不依賴 GARDEN）
- [ ] 字典 preset >= 250 條
- [ ] 反射規則 >= 50 條
- [ ] 日常對話覆蓋率 >= 80%（不 fallback）
- [ ] 同義詞展開正常運作
- [ ] 多位數數學運算正確
- [ ] 6 個 handler 全部可用
- [ ] ED3N 分類輔助路徑啟用
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
- [ ] 神經可塑性整合 HAM
- [ ] 跨 session 記憶持久化
- [ ] 學習回饋循環正常
- [ ] 重啟後記憶不丟失

### 整體
- [ ] 14 條端到端測試通過
- [ ] 效能基準達標
- [ ] 無 regression（現有功能不受影響）
