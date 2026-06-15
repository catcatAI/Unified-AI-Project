# QueryClassifier 精確度審查 + 執行路由計畫 v4 (完整版)

**日期**: 2026-06-15
**目標**: 讓 Angela 知行合一 — 意圖分類精確、執行結果回饋 LLM、不確定時不亂做
**對齊**: AGENTS.md (Surgical Precision, No Placeholders), ANGELA_FULL_ARCHITECTURE.md
**前置**: 已審查 query_classifier.py (277行), router.py (1457行), prompt_builder.py (377行), chat_routes.py (540行), chat_service.py (128行), file_operation_handler.py (38行), web_search_handler.py (63行), model_bus.py (511行)

---

## 1. 核心設計原則

```
知行合一 ≠ 什麼都做
知行合一 = 做了就知道做了、沒做就知道沒做、不確定就問
```

**四條鐵律：**
1. **不確定 → 不執行，問用戶**（寧可多問一句，不能做錯一件事）
2. **執行結果必須回饋 LLM**（做了什麼、成功失敗，都要讓 LLM 看到）
3. **LLM 基於事實回應**（不能自己編結果）
4. **多步驟需要多輪確認**（不能一次做完所有事）

---

## 2. 執行分數系統

### 2.1 三因子分數制

```
執行分數 = 可逆性 × 影響度 × 明確度
```

### 2.2 可逆性分數表（寫死在程式碼中）

```python
REVERSIBILITY = {
    "read":     1.0,   # 讀取類：完全可逆（沒改變任何東西）
    "create":   0.9,   # 建立類：可逆（可刪除）
    "modify":   0.6,   # 修改類：可逆但有成本
    "delete":   0.2,   # 刪除類：不可逆
    "send":     0.1,   # 傳送類：不可逆
    "system":   0.0,   # 系統類：不可逆且影響大
    "none":     1.0,   # 無操作
}
```

### 2.3 影響度計算

```python
def _estimate_impact(self, action_type: str, user_message: str) -> float:
    """根據操作類型和範圍估計影響度。範圍 0.0(影響大) ~ 1.0(無影響)"""
    base = {
        "read": 1.0, "create": 0.9, "modify": 0.7,
        "delete": 0.4, "send": 0.3, "system": 0.2, "none": 1.0,
    }.get(action_type, 0.5)

    # 全部/所有 → 影響更大
    if any(w in user_message for w in ["全部", "所有", "整個", "all", "全部的"]):
        base = max(0.1, base - 0.3)
    # 單一/一個 → 影響較小
    if any(w in user_message for w in ["一個", "單一", "this", "this one", "就好"]):
        base = min(1.0, base + 0.1)

    return base
```

### 2.4 明確度計算

```python
def _estimate_clarity(self, text: str, query_type: str, confidence: float) -> float:
    """用戶意圖有多清晰。範圍 0.0(模糊) ~ 1.0(明確)"""
    clarity = confidence

    # 包含明確動作動詞 → 更清晰
    clear_verbs = [
        "搜尋", "搜索", "刪除", "開啟", "關閉", "執行", "下載", "上傳",
        "讀取", "寫入", "儲存", "建立", "修改", "編輯", "重新命名",
        "search", "delete", "open", "run", "download", "upload",
        "read", "write", "save", "create", "edit", "rename",
    ]
    if any(v in text for v in clear_verbs):
        clarity = min(1.0, clarity + 0.1)

    # 包含明確對象（檔案路徑、URL）→ 更清晰
    if re.search(r'[\w/\\]+\.\w+', text):
        clarity = min(1.0, clarity + 0.1)
    if re.search(r'https?://', text):
        clarity = min(1.0, clarity + 0.1)

    # 模糊詞 → 不清晰
    vague_words = ["一下", "看看", "處理", "弄", "搞", "整", "試試"]
    if any(w in text for w in vague_words):
        clarity = max(0.1, clarity - 0.2)

    # 太短 → 不清晰
    if len(text) < 5:
        clarity = max(0.2, clarity - 0.1)

    return clarity
```

### 2.5 執行分數計算

```python
def _calculate_exec_score(self, action_type: str, user_message: str,
                          query_type: str, confidence: float) -> float:
    """執行分數 = 可逆性 × 影響度 × 明確度"""
    reversibility = REVERSIBILITY.get(action_type, 0.5)
    impact = self._estimate_impact(action_type, user_message)
    clarity = self._estimate_clarity(user_message, query_type, confidence)
    return round(reversibility * impact * clarity, 3)
```

### 2.6 分數範例（完整計算過程）

| 輸入 | action_type | 可逆性 | 影響度 | 明確度 | 執行分數 | 決策 |
|------|------------|--------|--------|--------|---------|------|
| `搜尋台北天氣` | read | 1.0 | 1.0 | 0.9 | **0.900** | 直接執行 |
| `讀取 temp.txt` | read | 1.0 | 1.0 | 0.95 | **0.950** | 直接執行 |
| `建立 notes.md` | create | 0.9 | 0.9 | 0.85 | **0.689** | 問用戶 |
| `修改 config.json` | modify | 0.6 | 0.7 | 0.8 | **0.336** | 問用戶 |
| `刪除 temp.txt` | delete | 0.2 | 0.4 | 0.9 | **0.072** | 問用戶+影響 |
| `刪除全部檔案` | delete | 0.2 | 0.1 | 0.9 | **0.018** | 不執行 |
| `幫我查字典` | read | 1.0 | 1.0 | 0.3 | **0.300** | 問用戶 |
| `開玩笑` | system | 0.0 | 0.5 | 0.2 | **0.000** | 不執行 |
| `今天?` | none | 1.0 | 1.0 | 0.2 | **0.200** | 問用戶 |
| `幫我處理檔案` | modify | 0.6 | 0.7 | 0.4 | **0.168** | 問用戶 |
| `不要搜尋` | read | 1.0 | 1.0 | 0.4 | **0.400** | 否定→不執行 |

---

## 3. QueryClassifier v2 完整實作

### 3.1 新增的 QueryResult dataclass

在 `query_classifier.py` 頂部新增：

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class QueryResult:
    """意圖分類結果"""
    primary_type: QueryType
    confidence: float                              # 0.0-1.0
    actionability: float = 0.0                     # 0.0-1.0
    action_type: str = "none"                      # read/create/modify/delete/send/system/none
    secondary_type: Optional[QueryType] = None
    secondary_confidence: float = 0.0
    reason: str = ""
```

### 3.2 新增的常數

```python
# 操作類型推斷用的關鍵字
_CREATE_VERBS = {"建立", "新增", "创建", "新增", "create", "new", "add"}
_MODIFY_VERBS = {"修改", "編輯", "重新命名", "edit", "rename", "modify", "update"}
_DELETE_VERBS = {"刪除", "移除", "清空", "删除", "delete", "remove", "clear"}
_WRITE_VERBS = {"寫入", "儲存", "write", "save"}
_READ_PREFIXES = {"搜尋", "搜索", "查詢", "查看", "讀取", "找", "search", "find", "lookup"}
_SEND_VERBS = {"發送", "傳送", "提交", "send", "submit", "post"}

# REFLEX 不覆蓋的動詞（這些是有意義的單字動詞）
VERBS_NOT_REFLEX = {
    "看", "查", "開", "關", "跑", "跳", "讀", "寫", "聽", "說",
    "吃", "喝", "搜", "刪", "改", "傳", "載", "買", "賣", "打",
}

# 明確知識查詢模式（用於 `?` override 修正）
KNOWLEDGE_QUESTION_PATTERNS = [
    r"^什麼是", r"^什么是", r"^怎麼", r"^为什么", r"^為什麼",
    r"^how\b", r"^what\b", r"^why\b", r"^when\b", r"^where\b", r"^who\b",
    r"^多少", r"^幾個", r"^誰",
]

# 否定詞
_NEGATION_WORDS = {"不要", "別", "取消", "停止", "stop", "cancel", "don't", "no"}
```

### 3.3 完整的 classify() 方法（替換原有）

```python
def classify(self, text: str) -> QueryResult:
    """
    分類使用者輸入。
    返回 QueryResult 包含 primary_type, confidence, actionability, action_type,
    secondary_type, secondary_confidence, reason
    """
    text = text.strip()
    if not text:
        return QueryResult(QueryType.UNKNOWN, 0.0, 0.0, "none", reason="empty_input")

    # Step 0: 否定詞檢測
    has_negation = any(neg in text for neg in _NEGATION_WORDS)

    # Step 1: 長文字启发式
    if len(text) > 200:
        conf = 0.85
        conf = self._adjust_confidence(QueryType.KNOWLEDGE, text, conf, False, has_negation)
        action_type = self._infer_action_type(QueryType.KNOWLEDGE, text)
        return QueryResult(
            primary_type=QueryType.KNOWLEDGE,
            confidence=conf,
            actionability=self._calc_actionability(QueryType.KNOWLEDGE, text, conf),
            action_type=action_type,
            reason="long_text_heuristic"
        )

    # Step 2: 多模式匹配（收集所有匹配）
    matches = []
    for qt, pattern, base_conf in self._patterns:
        m = pattern.search(text)
        if m:
            # 動態置信度
            anchored = m.start() == 0 or m.end() == len(text)
            keyword_count = len(m.group().split())
            conf = self._adjust_confidence(qt, text, base_conf, anchored, has_negation)

            # 可執行性
            act = self._calc_actionability(qt, text, conf)

            # 操作類型
            atype = self._infer_action_type(qt, text)

            matches.append((qt, conf, act, atype))

    # Step 3: ED3N 輔助分類
    try:
        ed3n_type, ed3n_conf = self._ed3n_classify(text)
        if ed3n_conf > 0.5:
            atype = self._infer_action_type(ed3n_type, text)
            act = self._calc_actionability(ed3n_type, text, ed3n_conf)
            matches.append((ed3n_type, ed3n_conf, act, atype))
    except Exception:
        pass  # ED3N 不可用時忽略

    # Step 4: 排序（先比 confidence，再比 actionability）
    matches.sort(key=lambda x: (x[1], x[2]), reverse=True)

    # Step 5: 選擇最佳匹配
    if matches:
        primary = matches[0]
        secondary = None
        if len(matches) > 1 and matches[1][1] >= primary[1] - 0.1:
            secondary = matches[1]

        return QueryResult(
            primary_type=primary[0],
            confidence=primary[1],
            actionability=primary[2],
            action_type=primary[3],
            secondary_type=secondary[0] if secondary else None,
            secondary_confidence=secondary[1] if secondary else 0.0,
            reason="pattern_match"
        )

    # Step 6: REFLEX override（單字 + 低置信度）
    if len(text) < 2:
        if text not in VERBS_NOT_REFLEX:
            return QueryResult(
                QueryType.REFLEX, 0.95, 0.0, "none",
                reason="reflex_single_char_override"
            )
        # 是有意義的動詞，不 override，降低置信度
        return QueryResult(
            QueryType.UNKNOWN, 0.4, 0.3, "read",
            reason="meaningful_single_char"
        )

    # Step 7: `?` override（只有明確知識查詢模式）
    if text.endswith("?") or text.endswith("？"):
        if any(re.search(p, text, re.I) for p in KNOWLEDGE_QUESTION_PATTERNS):
            conf = 0.65
            conf = self._adjust_confidence(QueryType.KNOWLEDGE, text, conf, False, has_negation)
            return QueryResult(
                QueryType.KNOWLEDGE, conf, 0.1, "none",
                reason="knowledge_question_mark_override"
            )

    # Step 8: 回傳 UNKNOWN
    return QueryResult(
        QueryType.UNKNOWN, 0.3, 0.0, "none",
        reason="no_match_fallback"
    )
```

### 3.4 完整的 _adjust_confidence() 方法

```python
def _adjust_confidence(self, query_type: QueryType, text: str,
                       base_conf: float, anchored: bool, has_negation: bool) -> float:
    """動態調整置信度"""
    conf = base_conf

    # 錨定匹配更可靠
    if anchored:
        conf += 0.05

    # 關鍵字密度
    words = text.split()
    if len(words) > 0:
        # 簡單估算：匹配的關鍵字佔比
        matching_keywords = sum(1 for w in words if len(w) >= 2)
        density = matching_keywords / len(words)
        if density > 0.5:
            conf += 0.05
        elif density < 0.2:
            conf -= 0.10

    # 輸入長度
    if len(text) < 5:
        conf -= 0.05
    elif len(text) > 50:
        conf += 0.03

    # 否定詞
    if has_negation:
        conf -= 0.15

    return max(0.1, min(0.95, conf))
```

### 3.5 完整的 _calc_actionability() 方法

```python
def _calc_actionability(self, query_type: QueryType, text: str, confidence: float) -> float:
    """計算可執行性分數"""
    # 類型基礎分
    type_base = {
        QueryType.EXECUTE: 0.9, QueryType.FILE: 0.85, QueryType.SEARCH: 0.8,
        QueryType.CODE: 0.75, QueryType.TASK: 0.7, QueryType.VISION: 0.6,
        QueryType.AUDIO: 0.6, QueryType.COMMAND: 0.5,
        QueryType.KNOWLEDGE: 0.1, QueryType.OPINION: 0.1, QueryType.CREATIVE: 0.1,
        QueryType.GREETING: 0.0, QueryType.REFLEX: 0.0, QueryType.UNKNOWN: 0.0,
        QueryType.MATH: 0.1, QueryType.LOGIC: 0.1,
    }.get(query_type, 0.3)

    # 明確動作動詞 → 提高
    all_action_verbs = (
        list(_CREATE_VERBS) + list(_MODIFY_VERBS) + list(_DELETE_VERBS) +
        list(_SEND_VERBS) + list(_READ_PREFIXES) + list(_WRITE_VERBS)
    )
    if any(v in text for v in all_action_verbs):
        type_base = min(1.0, type_base + 0.1)

    # 模糊詞 → 降低
    vague_words = ["一下", "看看", "處理", "弄", "搞", "整", "試試"]
    if any(w in text for w in vague_words):
        type_base = max(0.0, type_base - 0.2)

    # 否定詞 → 大幅降低
    if any(neg in text for neg in _NEGATION_WORDS):
        type_base = max(0.0, type_base - 0.5)

    return type_base
```

### 3.6 完整的 _infer_action_type() 方法

```python
def _infer_action_type(self, query_type: QueryType, text: str) -> str:
    """根據意圖和文字推斷操作類型"""
    # 無操作類
    if query_type in (QueryType.GREETING, QueryType.REFLEX, QueryType.OPINION,
                      QueryType.CREATIVE, QueryType.KNOWLEDGE, QueryType.MATH,
                      QueryType.LOGIC):
        return "none"

    # 讀取類
    if query_type in (QueryType.SEARCH, QueryType.VISION, QueryType.AUDIO):
        if any(w in text for w in _WRITE_VERBS):
            return "modify"
        return "read"

    # FILE 類：根據動詞判斷
    if query_type == QueryType.FILE:
        if any(w in text for w in _DELETE_VERBS):
            return "delete"
        if any(w in text for w in _CREATE_VERBS):
            return "create"
        if any(w in text for w in _MODIFY_VERBS):
            return "modify"
        return "read"

    # CODE/EXECUTE → system
    if query_type in (QueryType.CODE, QueryType.EXECUTE):
        return "system"

    # TASK → create or delete
    if query_type == QueryType.TASK:
        if any(w in text for w in _DELETE_VERBS):
            return "delete"
        return "create"

    # COMMAND → 根據內容判斷
    if query_type == QueryType.COMMAND:
        if any(w in text for w in _DELETE_VERBS):
            return "delete"
        if any(w in text for w in _CREATE_VERBS):
            return "create"
        if any(w in text for w in _MODIFY_VERBS):
            return "modify"
        return "read"

    return "none"
```

### 3.7 Regex word boundary 修正

**問題：** 現有 pattern 使用 `re.search()` 做 substring match，`"開玩笑"` 會匹配到 `"開"` 進入 EXECUTE。

**修正方式：** 所有 pattern 加上前后邊界，確保匹配完整詞。

```python
# 修正前 (query_classifier.py 現有)
r"(執行|運行|開啟|關閉|啟動|停止|..."  # substring match

# 修正後：中文用前後空白/標點做邊界
# 因為 Python \b 不支援中文，所以手動加邊界
WORD_BOUNDARY = r"(?:^|[\s，。！？,.\s])"
WORD_BOUNDARY_END = r"(?:[\s，。！？,.\s]|$)"

# EXECUTE pattern 修正
r"(?:^|[\s，。！？,.\s])(執行|運行|開啟|關閉|啟動|停止|)(?:[\s，。！？,.\s]|$)"
# 測試: "開玩笑" → 不匹配（"開" 不在完整詞列表中）
# 測試: "開啟檔案" → 匹配 "開啟"
# 測試: "請執行這個" → 匹配 "執行"

# FILE pattern 修正
r"(?:^|[\s，。！？,.\s])(整理|刪除|文件|文件夾|目錄|file|folder|directory)(?:[\s，。！？,.\s]|$)"

# SEARCH pattern 修正
r"(?:^|[\s，。！？,.\s])(搜尋|搜索|找|查|search|find|lookup)(?:[\s，。！？,.\s]|$)"

# CODE pattern 修正
r"(?:^|[\s，。！？,.\s])(程序|代碼|函數|debug|refactor|code|function)(?:[\s，。！？,.\s]|$)"

# COMMAND pattern (已錨定到開頭，不需改)
r"^(幫我|請|打開|關閉|開始|停止|can you|please)"
```

**需要修正的 pattern 清單（query_classifier.py:48-198）：**

| Pattern | 修正前 | 修正後 |
|---------|--------|--------|
| EXECUTE | `r"(執行\|運行\|..."` | 加 WORD_BOUNDARY |
| FILE | `r"(整理\|刪除\|..."` | 加 WORD_BOUNDARY |
| SEARCH | `r"(搜尋\|搜索\|..."` | 加 WORD_BOUNDARY |
| CODE | `r"(程序\|代碼\|..."` | 加 WORD_BOUNDARY |
| TASK | `r"(任務\|工作\|..."` | 加 WORD_BOUNDARY |
| VISION | `r"(圖片\|照片\|..."` | 加 WORD_BOUNDARY |
| AUDIO | `r"(語音\|音訊\|..."` | 加 WORD_BOUNDARY |
| COMMAND | `r"^(幫我\|..."` | 已錨定，不改 |
| MATH | `r"(\d+\s*[+\-*/]\s*\d+)"` | 不改（已有數字邊界） |
| LOGIC | `r"(true\|false\|..."` | 加 WORD_BOUNDARY |
| KNOWLEDGE | `r"(什麼是\|how\|..."` | 加 WORD_BOUNDARY |
| CREATIVE | `r"(寫\|作\|..."` | 加 WORD_BOUNDARY |
| OPINION | `r"(覺得\|認為\|..."` | 加 WORD_BOUNDARY |
| GREETING | `r"(你好\|hello\|..."` | 加 WORD_BOUNDARY |

**驗證方法：**
```python
# 測試用例
test_cases = [
    ("開玩笑", None),           # 不應匹配 EXECUTE
    ("關心你", None),           # 不應匹配 EXECUTE
    ("幫我搜尋天氣", "SEARCH"),  # 應匹配 SEARCH
    ("刪除 temp.txt", "FILE"),  # 應匹配 FILE
    ("執行這個命令", "EXECUTE"), # 應匹配 EXECUTE
    ("幫我看看", "VISION"),     # 應匹配 VISION（不是 EXECUTE）
]
```

### 3.8 REFLEX Override 修正

在 classify() 的 Step 6 中已有完整處理（見 3.3）。

---

## 4. ExecutionGate 完整實作

### 4.1 GateDecision dataclass

在 `router.py` 頂部或新建 `execution_gate.py` 中：

```python
from dataclasses import dataclass, field
from typing import Optional, Callable, Awaitable, Any

@dataclass
class GateDecision:
    """執行閘門決策"""
    action: str                    # "auto_execute" | "confirm_then_execute" | "reject"
    score: float                   # 執行分數
    handler: Optional[str] = None  # handler ID（auto_execute/confirm 時）
    reason: str = ""
    confirm_message: str = ""      # 確認訊息（confirm 時）
    impact_info: str = ""          # 影響說明（confirm 時）
    action_type: str = "none"      # 操作類型
    original_query: str = ""       # 原始查詢（等確認後執行用）
```

### 4.2 ExecutionGate 完整類

```python
class ExecutionGate:
    """執行閘門：基於可逆性×影響度×明確度決定是否執行"""

    AUTO_EXECUTE = 0.6
    CONFIRM_THRESHOLD = 0.2

    # Handler 映射
    HANDLER_MAP = {
        "file": "file_ops",
        "search": "web_search",
        # "code": "code_execution",     # 未來實作
        # "execute": "system_command",  # 未來實作
        # "task": "task_manager",       # 未來實作
    }

    def __init__(self, model_bus=None):
        self._model_bus = model_bus

    def decide(self, query_type: str, action_type: str, user_message: str,
               confidence: float, context: dict) -> GateDecision:
        """決定是否執行"""
        score = self._calculate_exec_score(action_type, user_message, query_type, confidence)

        # 否定詞強制 reject
        if any(neg in user_message for neg in _NEGATION_WORDS):
            return GateDecision(
                action="reject", score=score,
                reason="negation_detected",
                original_query=user_message,
            )

        # 檢查是否有 handler
        handler_id = self.HANDLER_MAP.get(query_type)

        if score >= self.AUTO_EXECUTE and handler_id:
            return GateDecision(
                action="auto_execute", score=score,
                handler=handler_id,
                action_type=action_type,
                reason=f"exec_score={score} >= {self.AUTO_EXECUTE}",
                original_query=user_message,
            )

        if score >= self.CONFIRM_THRESHOLD:
            if handler_id:
                return GateDecision(
                    action="confirm_then_execute", score=score,
                    handler=handler_id,
                    action_type=action_type,
                    reason=f"exec_score={score} in [{self.CONFIRM_THRESHOLD}, {self.AUTO_EXECUTE})",
                    confirm_message=self._build_confirm(action_type, user_message),
                    impact_info=self._describe_impact(action_type, user_message),
                    original_query=user_message,
                )
            # 有分數但沒 handler → 問用戶要做什麼
            return GateDecision(
                action="confirm_then_execute", score=score,
                action_type=action_type,
                reason="has_score_but_no_handler",
                confirm_message="你想要我做什麼？可以更具體說明嗎？",
                original_query=user_message,
            )

        return GateDecision(
            action="reject", score=score,
            reason=f"exec_score={score} < {self.CONFIRM_THRESHOLD}",
            original_query=user_message,
        )

    def _calculate_exec_score(self, action_type: str, user_message: str,
                              query_type: str, confidence: float) -> float:
        reversibility = REVERSIBILITY.get(action_type, 0.5)
        impact = self._estimate_impact(action_type, user_message)
        clarity = self._estimate_clarity(user_message, query_type, confidence)
        return round(reversibility * impact * clarity, 3)

    def _estimate_impact(self, action_type: str, user_message: str) -> float:
        base = {
            "read": 1.0, "create": 0.9, "modify": 0.7,
            "delete": 0.4, "send": 0.3, "system": 0.2, "none": 1.0,
        }.get(action_type, 0.5)
        if any(w in user_message for w in ["全部", "所有", "整個", "all", "全部的"]):
            base = max(0.1, base - 0.3)
        if any(w in user_message for w in ["一個", "單一", "this", "this one", "就好"]):
            base = min(1.0, base + 0.1)
        return base

    def _estimate_clarity(self, text: str, query_type: str, confidence: float) -> float:
        clarity = confidence
        clear_verbs = [
            "搜尋", "搜索", "刪除", "開啟", "關閉", "執行", "下載", "上傳",
            "讀取", "寫入", "儲存", "建立", "修改", "編輯", "重新命名",
            "search", "delete", "open", "run", "download", "upload",
            "read", "write", "save", "create", "edit", "rename",
        ]
        if any(v in text for v in clear_verbs):
            clarity = min(1.0, clarity + 0.1)
        if re.search(r'[\w/\\]+\.\w+', text):
            clarity = min(1.0, clarity + 0.1)
        if re.search(r'https?://', text):
            clarity = min(1.0, clarity + 0.1)
        vague_words = ["一下", "看看", "處理", "弄", "搞", "整", "試試"]
        if any(w in text for w in vague_words):
            clarity = max(0.1, clarity - 0.2)
        if len(text) < 5:
            clarity = max(0.2, clarity - 0.1)
        return clarity

    def _build_confirm(self, action_type: str, user_message: str) -> str:
        desc = {
            "read": "讀取", "create": "建立", "modify": "修改",
            "delete": "刪除", "send": "傳送", "system": "執行系統操作",
        }.get(action_type, "執行操作")
        msg = f"你想要{desc}嗎？"
        if action_type == "delete":
            msg += "\n⚠️ 刪除後無法復原。"
        elif action_type == "send":
            msg += "\n⚠️ 傳送後無法撤回。"
        elif action_type == "system":
            msg += "\n⚠️ 系統操作可能影響其他程式。"
        elif action_type == "modify":
            msg += "\n 修改會覆蓋原始內容。"
        msg += "\n確認後我會執行。"
        return msg

    def _describe_impact(self, action_type: str, user_message: str) -> str:
        parts = []
        if "全部" in user_message or "所有" in user_message:
            parts.append("⚠️ 這會影響所有項目")
        if action_type == "delete":
            parts.append("此操作無法撤銷")
        return "；".join(parts)
```

---

## 5. Session Context 管理

### 5.1 pending_action 存儲

在 `chat_routes.py` 的 `_handle_chat_request` 中，session context 已有 dict 結構。新增：

```python
# session context 新增欄位
context["pending_action"] = None        # 等待確認的 GateDecision
context["continuation_count"] = 0       # 續行次數
context["last_action_result"] = None    # 上次執行結果
```

### 5.2 確認機制流程

```python
async def _handle_chat_request(user_message, user_name, history, session_id, extra_context):
    # ... 現有邏輯（情緒分析、危機偵測等）...

    context = extra_context or {}
    pending = context.get("pending_action")

    # 如果有 pending action，檢查是否是確認/取消
    if pending:
        msg_lower = user_message.strip().lower()
        confirm_words = {"好", "是", "確認", "ok", "yes", "sure", "確定", "對"}
        cancel_words = {"不要", "取消", "算了", "no", "cancel", "skip", "不用"}

        if msg_lower in confirm_words:
            # 執行
            handler_id = pending.handler
            if handler_id and self.model_bus:
                result = await self.model_bus.execute_handler(
                    handler_id, pending.original_query, context
                )
                context["last_action_result"] = result
                context["pending_action"] = None
                # 繼續到 LLM 生成（帶執行結果）

        elif msg_lower in cancel_words:
            context["pending_action"] = None
            return {
                "content": "好的，不執行。還有什麼需要幫忙的嗎？",
                "hit_score": 0.0,
                "hit_source": "gate_cancel",
            }

        else:
            # 不是確認也不是取消 → 當作新輸入，清除 pending
            context["pending_action"] = None

    # Phase 1: 意圖分類
    classifier = QueryClassifier()
    result = classifier.classify(user_message)

    # Phase 2: 執行分數 + 決策
    gate = ExecutionGate(model_bus=self.model_bus)
    decision = gate.decide(
        query_type=result.primary_type.value,
        action_type=result.action_type,
        user_message=user_message,
        confidence=result.confidence,
        context=context,
    )

    if decision.action == "auto_execute":
        # 直接執行
        if decision.handler and self.model_bus:
            action_result = await self.model_bus.execute_handler(
                decision.handler, user_message, context
            )
            context["last_action_result"] = action_result
            context["continuation_count"] = 0
        # 繼續到 LLM 生成

    elif decision.action == "confirm_then_execute":
        # 存 pending，回傳確認訊息
        context["pending_action"] = decision
        return {
            "content": decision.confirm_message,
            "hit_score": result.confidence,
            "hit_source": "gate_confirm",
            "route": result.primary_type.value,
        }

    else:  # reject
        # 不執行，跳過
        context["last_action_result"] = None

    # Phase 4: LLM 生成（帶執行結果）
    # ... 現有 LLM 生成邏輯 ...
    # 在 prompt 中注入 last_action_result
```

---

## 6. Result Injection Prompt

### 6.1 在 prompt_builder.py 中新增

在 `construct_angela_prompt` 的 line ~365（`<user_message>` 之前）插入：

```python
# 執行結果注入（如果有）
action_result = context.get("last_action_result")
if action_result:
    action_block = (
        f"\n[執行結果]\n"
        f"類型: {action_result.get('type', 'unknown')}\n"
        f"成功: {'是' if action_result.get('success', False) else '否'}\n"
        f"結果: {action_result.get('result', '')}\n"
        f"錯誤: {action_result.get('error', '')}\n"
        f"\n請基於以上執行結果回應使用者。"
        f"如果執行失敗，請說明原因並建議替代方案。\n"
    )
    messages.append({"role": "user", "content": action_block})
```

### 6.2 LLM 續行保護 prompt

在 `construct_angela_prompt` 的 system_prompt 中追加：

```python
system_prompt += (
    "\n\n[執行規則]\n"
    "- 如果收到執行結果，你必須基於事實回應\n"
    "- 如果執行成功，描述結果\n"
    "- 如果執行失敗，說明原因並建議替代方案\n"
    "- 如果你判斷使用者還需要更多操作，問他們要不要繼續\n"
    "- 不要自動執行更多操作，除非使用者明確要求\n"
)
```

### 6.3 續行迴圈保護

```python
# 在 _handle_chat_request 中
continuation = context.get("continuation_count", 0)
if continuation >= 3:
    # 強制停止續行
    system_prompt += "\n\n[警告] 已達最大續行次數，請直接回應使用者，不要再建議進一步操作。"
```

---

## 7. 否定詞完整處理

### 7.1 否定詞檢測位置

在兩個地方檢查：
1. **QueryClassifier.classify()** — Step 0（line ~210）→ 降低 confidence
2. **ExecutionGate.decide()** — score 計算後 → 強制 reject

### 7.2 否定詞不影響分類，只影響執行

```python
# classify() 中：否定詞降低 confidence 但不改變 type
has_negation = any(neg in text for neg in _NEGATION_WORDS)
conf = self._adjust_confidence(qt, text, base_conf, anchored, has_negation)
# type 不變，但 conf 降低 → 可能導致 score 太低 → 不執行

# ExecutionGate.decide() 中：否定詞強制 reject
if any(neg in user_message for neg in _NEGATION_WORDS):
    return GateDecision(action="reject", score=score, reason="negation_detected")
```

---

## 8. Handler 接口統一

### 8.1 現有 handler 接口不統一

| Handler | 接口 | 回傳 |
|---------|------|------|
| FileOperationHandler | `handle(intent, params)` | `Dict[str, Any]` |
| WebSearchHandler | `handle(text, intent)` | `str` |

### 8.2 統一為 `execute(query, context)` 接口

在 `model_bus.py` 的 `_adapt_handler` 已經做了包裝（line 150-178），將 handler 包裝為 `process(query, context)` 接口。

**需要修改：** 讓 `execute_handler` 方法回傳結構化結果：

```python
async def execute_handler(self, handler_id: str, query: str, context: dict) -> dict:
    """執行 handler 並回傳結構化結果"""
    handler = self._handlers.get(handler_id)
    if not handler:
        return {"type": "unknown", "success": False, "error": f"handler {handler_id} not found"}

    try:
        adapted = self._adapted_handlers.get(handler_id, handler)
        result = await asyncio.wait_for(
            adapted.process(query, context),
            timeout=30.0
        )
        return {
            "type": handler_id,
            "success": True,
            "result": str(result),
            "error": None,
        }
    except asyncio.TimeoutError:
        return {"type": handler_id, "success": False, "result": None, "error": "timeout"}
    except Exception as e:
        return {"type": handler_id, "success": False, "result": None, "error": str(e)}
```

---

## 9. 完整流程（修正後的 _handle_chat_request）

```python
async def _handle_chat_request(user_message, user_name, history, session_id, extra_context):
    """完整聊天處理流程（含執行閘門）"""
    context = extra_context or {}

    # === 現有邏輯（不變）===
    # 驗證訊息長度 (lines 98-106)
    # 數學驗證 (lines 116-131)
    # 情緒分析 (lines 133-140)
    # 危機偵測 (lines 143-151)
    # 生物刺激 (lines 154-166)

    # === 新增：處理 pending confirmation ===
    pending = context.get("pending_action")
    if pending:
        msg_lower = user_message.strip().lower()
        if msg_lower in {"好", "是", "確認", "ok", "yes", "sure", "確定", "對"}:
            if pending.handler and hasattr(self, 'model_bus') and self.model_bus:
                result = await self.model_bus.execute_handler(
                    pending.handler, pending.original_query, context
                )
                context["last_action_result"] = result
                context["pending_action"] = None
                context["continuation_count"] = 0
        elif msg_lower in {"不要", "取消", "算了", "no", "cancel", "skip", "不用"}:
            context["pending_action"] = None
            return {"content": "好的，不執行。還有什麼需要幫忙的嗎？",
                    "hit_score": 0.0, "hit_source": "gate_cancel"}
        else:
            context["pending_action"] = None

    # === 新增：意圖分類 ===
    classifier = QueryClassifier()
    classify_result = classifier.classify(user_message)

    # === 新增：執行閘門 ===
    gate = ExecutionGate(model_bus=getattr(self, 'model_bus', None))
    decision = gate.decide(
        query_type=classify_result.primary_type.value,
        action_type=classify_result.action_type,
        user_message=user_message,
        confidence=classify_result.confidence,
        context=context,
    )

    if decision.action == "auto_execute":
        if decision.handler and hasattr(self, 'model_bus') and self.model_bus:
            action_result = await self.model_bus.execute_handler(
                decision.handler, user_message, context
            )
            context["last_action_result"] = action_result

    elif decision.action == "confirm_then_execute":
        context["pending_action"] = decision
        return {
            "content": decision.confirm_message,
            "hit_score": classify_result.confidence,
            "hit_source": "gate_confirm",
            "route": classify_result.primary_type.value,
        }

    else:  # reject
        context["last_action_result"] = None

    # === 現有 LLM 生成邏輯（不變）===
    # _chat_svc.generate_response(user_message, user_name, context=context)
    # 但在 prompt_builder 中會注入 last_action_result
```

---

## 10. 實作計畫（含具體修改位置）

### Phase 1: QueryClassifier v2（2-3 天）

| # | 項目 | 檔案:行號 | 具體修改 |
|---|------|-----------|---------|
| 1.1 | 新增 QueryResult dataclass | `query_classifier.py:1-18` | 在 import 後新增 dataclass |
| 1.2 | 新增常數 | `query_classifier.py:19-40` | 在 QueryType 後新增所有常數 |
| 1.3 | 替換 classify() | `query_classifier.py:200-243` | 用 3.3 的完整方法替換 |
| 1.4 | 新增 _adjust_confidence() | `query_classifier.py` | 新方法（3.4） |
| 1.5 | 新增 _calc_actionability() | `query_classifier.py` | 新方法（3.5） |
| 1.6 | 新增 _infer_action_type() | `query_classifier.py` | 新方法（3.6） |
| 1.7 | 修正 regex patterns | `query_classifier.py:48-198` | 所有 pattern 加 word boundary |
| 1.8 | 單元測試 | `tests/ai/core/test_query_classifier_v2.py` | 新建，30+ 測試 |

### Phase 2: ExecutionGate（1-2 天）

| # | 項目 | 檔案:行號 | 具體修改 |
|---|------|-----------|---------|
| 2.1 | 新建 ExecutionGate | `ai/core/execution_gate.py` | 新建檔案（4.2 完整類） |
| 2.2 | 新增 execute_handler | `model_bus.py:128-148` | 新增結構化回傳方法（8.2） |
| 2.3 | 修改 _handle_chat_request | `chat_routes.py:88-327` | 插入確認處理 + 分類 + 閘門（第 9 章） |
| 2.4 | 修改 prompt_builder | `prompt_builder.py:354-365` | 插入執行結果注入（6.1）+ 續行保護（6.3） |
| 2.5 | 單元測試 | `tests/ai/core/test_execution_gate.py` | 新建，15+ 測試 |

### Phase 3: 整合測試（1-2 天）

| # | 測試案例（具體輸入/預期） |
|---|---------|
| 3.1 | `"搜尋台北天氣"` → exec_score ≥ 0.6 → 自動執行 |
| 3.2 | `"讀取 temp.txt"` → exec_score ≥ 0.6 → 自動執行 |
| 3.3 | `"刪除 temp.txt"` → exec_score < 0.2 → 問用戶 |
| 3.4 | `"刪除全部檔案"` → exec_score < 0.2 → 問用戶+影響說明 |
| 3.5 | `"幫我查字典"` → exec_score 0.2-0.6 → 問用戶 |
| 3.6 | `"開玩笑"` → exec_score = 0 → 不執行 |
| 3.7 | `"不要搜尋"` → 否定詞 → reject |
| 3.8 | `"看"` → 單字不 override → exec_score 0.2-0.6 → 問用戶 |
| 3.9 | `"今天?"` → exec_score ~0.2 → 問用戶 |
| 3.10 | 確認後執行：先問 → 用戶回"好" → 執行 → LLM 回應含結果 |
| 3.11 | 執行失敗：刪除 system32 → 失敗 → LLM 說明原因 |
| 3.12 | 多步驟：搜尋+整理 → 先搜尋 → 問要不要整理 → 整理 |
| 3.13 | 續行迴圈保護：3 次後強制停止 |
| 3.14 | 舊 86 個測試仍通過 |

---

## 11. 驗收標準（完整清單）

### 精確度（每個都有具體分數）
- [ ] `"開玩笑"` → action_type=system, exec_score=0.0 → reject
- [ ] `"關心"` → action_type=system, exec_score=0.0 → reject
- [ ] `"幫我查字典"` → action_type=read, exec_score=0.3 → confirm
- [ ] `"搜尋台北天氣"` → action_type=read, exec_score=0.9 → auto_execute
- [ ] `"讀取 temp.txt"` → action_type=read, exec_score=0.95 → auto_execute
- [ ] `"刪除 temp.txt"` → action_type=delete, exec_score=0.07 → confirm+影響
- [ ] `"今天幾點?"` → action_type=none, exec_score=0.2 → confirm
- [ ] `"好看嗎?"` → action_type=none, exec_score=0.1 → reject
- [ ] `"看"` → action_type=read, exec_score=0.4 → confirm
- [ ] `"不要搜尋"` → 否定詞 → reject

### 知行合一
- [ ] auto_execute → LLM prompt 包含 `[執行結果]` 區塊
- [ ] 執行成功 → LLM 回應描述結果
- [ ] 執行失敗 → LLM 回應說明失敗原因
- [ ] confirm_then_execute → 回傳確認訊息，context 存 pending_action
- [ ] 用戶回"好" → 執行 → LLM 回應含結果
- [ ] 用戶回"取消" → 不執行 → 回傳取消訊息
- [ ] LLM 續行 → 只建議，不自動執行
- [ ] 續行迴圈 ≥ 3 → 強制停止

### 回歸
- [ ] 舊 86 個測試仍通過
- [ ] 新增 ≥ 30 個邊界測試
