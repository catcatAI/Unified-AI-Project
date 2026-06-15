# QueryClassifier 精確度審查 + 執行路由計畫 v3

**日期**: 2026-06-15
**目標**: 讓 Angela 知行合一 — 意圖分類精確、執行結果回饋 LLM、不確定時不亂做
**對齊**: AGENTS.md (Surgical Precision, No Placeholders), ANGELA_FULL_ARCHITECTURE.md (管線流程)

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

## 2. 執行分數系統（取代簡單閾值）

### 2.1 為什麼不用「安全度分級」

| 方案 | 問題 |
|------|------|
| 高/中/低安全度 | 誰來判斷「安全」？LLM 可能判錯 |
| 高/中/低安全度 | 「安全」太模糊，不夠客觀 |
| 高/中/低安全度 | 同一操作在不同情境下風險不同 |

### 2.2 三因子分數制

```
執行分數 = 可逆性 × 影響度 × 明確度
```

| 因子 | 範圍 | 說明 | 誰決定 |
|------|------|------|--------|
| **可逆性** | 0.0-1.0 | 操作能否撤銷 | 規則（客觀） |
| **影響度** | 0.0-1.0 | 操作影響範圍多大 | 規則（可量化） |
| **明確度** | 0.0-1.0 | 用戶意圖有多清晰 | 分類器（動態） |

### 2.3 可逆性分數表

```python
REVERSIBILITY = {
    # 讀取類：完全可逆（沒改變任何東西）
    "read":     1.0,   # 讀檔案、搜尋、查詢、分析
    # 建立類：可逆（可刪除）
    "create":   0.9,   # 建立檔案、新增任務、新增聯絡人
    # 修改類：可逆但有成本
    "modify":   0.6,   # 修改檔案、編輯設定、重新命名
    # 刪除類：不可逆
    "delete":   0.2,   # 刪除檔案、清空資料、移除帳號
    # 傳送類：不可逆
    "send":     0.1,   # 發訊息、提交表單、發送郵件
    # 系統類：不可逆且影響大
    "system":   0.0,   # 執行指令、安裝軟體、修改系統設定
    # 無操作
    "none":     1.0,   # 純聊天、問問題
}
```

### 2.4 影響度分數表

```python
def estimate_impact(query_type, user_message):
    """根據操作類型和範圍估計影響度"""
    base = {
        "read":     1.0,   # 無影響
        "create":   0.9,   # 新增，影響小
        "modify":   0.7,   # 修改，影響中
        "delete":   0.4,   # 刪除，影響大
        "send":     0.3,   # 傳送，影響大
        "system":   0.2,   # 系統，影響極大
        "none":     1.0,   # 無影響
    }.get(query_type, 0.5)

    # 範圍調整
    if any(w in user_message for w in ["全部", "所有", "整個", "all"]):
        base = max(0.1, base - 0.3)  # 全部操作 → 影響更大
    if any(w in user_message for w in ["一個", "單一", "this", "this one"]):
        base = min(1.0, base + 0.1)  # 單一操作 → 影響較小

    return base
```

### 2.5 明確度分數

```python
def estimate_clarity(text, query_type, confidence):
    """用戶意圖有多清晰"""
    clarity = confidence  # 基礎分來自分類器置信度

    # 調整因子
    # 1. 包含明確動作動詞 → 更清晰
    clear_verbs = ["搜尋", "刪除", "開啟", "關閉", "執行", "下載",
                   "search", "delete", "open", "run", "download"]
    if any(v in text for v in clear_verbs):
        clarity = min(1.0, clarity + 0.1)

    # 2. 包含明確對象 → 更清晰
    if re.search(r'[\w/\\]+\.\w+', text):  # 包含檔案路徑
        clarity = min(1.0, clarity + 0.1)

    # 3. 模糊詞 → 不清晰
    vague_words = ["一下", "看看", "處理", "弄", "搞", "整"]
    if any(w in text for w in vague_words):
        clarity = max(0.1, clarity - 0.2)

    # 4. 太短 → 不清晰
    if len(text) < 5:
        clarity = max(0.2, clarity - 0.1)

    return clarity
```

### 2.6 執行分數計算

```python
def calculate_exec_score(query_type, action_type, user_message, confidence):
    """
    執行分數 = 可逆性 × 影響度 × 明確度
    範圍: 0.0 (絕對不執行) ~ 1.0 (直接執行)
    """
    reversibility = REVERSIBILITY.get(action_type, 0.5)
    impact = estimate_impact(query_type, user_message)
    clarity = estimate_clarity(user_message, query_type, confidence)

    score = reversibility * impact * clarity
    return round(score, 3)
```

### 2.7 分數範例

| 輸入 | 可逆性 | 影響度 | 明確度 | 執行分數 | 決策 |
|------|--------|--------|--------|---------|------|
| `搜尋台北天氣` | 1.0 (read) | 1.0 | 0.9 | **0.900** | 直接執行 |
| `讀取 temp.txt` | 1.0 (read) | 1.0 | 0.95 | **0.950** | 直接執行 |
| `建立 notes.md` | 0.9 (create) | 0.9 | 0.85 | **0.689** | 問用戶 |
| `修改 config.json` | 0.6 (modify) | 0.7 | 0.8 | **0.336** | 問用戶 |
| `刪除 temp.txt` | 0.2 (delete) | 0.4 | 0.9 | **0.072** | 問用戶+顯示影響 |
| `刪除全部檔案` | 0.2 (delete) | 0.1 | 0.9 | **0.018** | 預設不執行 |
| `幫我查字典` | 1.0 (read) | 1.0 | 0.3 | **0.300** | 問用戶（比喻） |
| `開玩笑` | 0.0 (system) | 0.5 | 0.2 | **0.000** | 不執行 |
| `今天?` | 1.0 (none) | 1.0 | 0.2 | **0.200** | 純聊天 |
| `幫我處理檔案` | 0.6 (modify) | 0.7 | 0.4 | **0.168** | 問用戶做什麼 |

---

## 3. 決策閘門（三層）

```
執行分數 ≥ 0.6  → 直接執行（自動）
0.2 ≤ 執行分數 < 0.6  → 問用戶確認
執行分數 < 0.2  → 預設不執行
```

### 3.1 閘門邏輯

```python
class ExecutionGate:
    """執行閘門：基於可逆性×影響度×明確度"""

    AUTO_EXECUTE = 0.6       # 直接執行
    CONFIRM_THRESHOLD = 0.2  # 需要確認
    # < 0.2 → 不執行

    def decide(self, query_type, action_type, user_message, confidence, context):
        score = calculate_exec_score(query_type, action_type, user_message, confidence)

        if score >= self.AUTO_EXECUTE:
            return GateDecision(
                action="auto_execute",
                score=score,
                handler=self._get_handler(query_type),
                reason=f"exec_score={score} >= {self.AUTO_EXECUTE}"
            )

        if score >= self.CONFIRM_THRESHOLD:
            return GateDecision(
                action="confirm_then_execute",
                score=score,
                handler=self._get_handler(query_type),
                reason=f"exec_score={score} in [{self.CONFIRM_THRESHOLD}, {self.AUTO_EXECUTE})",
                confirm_message=self._build_confirm(query_type, action_type, user_message),
                # 附加影響說明
                impact_info=self._describe_impact(action_type, user_message),
            )

        return GateDecision(
            action="reject",
            score=score,
            reason=f"exec_score={score} < {self.CONFIRM_THRESHOLD}",
        )
```

### 3.2 確認訊息（含影響說明）

```python
def _build_confirm(self, query_type, action_type, user_message):
    """建立確認訊息，包含會發生什麼事"""
    action_desc = {
        "read":   "讀取",
        "create": "建立",
        "modify": "修改",
        "delete": "刪除",
        "send":   "傳送",
        "system": "執行系統操作",
    }
    desc = action_desc.get(action_type, "執行操作")

    msg = f"你想要{desc}嗎？"

    # 附加影響說明
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
```

---

## 4. 完整生命週期

### 4.1 流程圖

```
使用者輸入
    │
    ▼
┌──────────────────────────────────────────────────────┐
│ Phase 1: 意圖分類                                      │
│  QueryClassifier v2                                   │
│  輸出: (primary_type, confidence, actionability,      │
│         secondary_type)                               │
└──────────────┬───────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────┐
│ Phase 2: 執行分數 + 決策                               │
│                                                       │
│  exec_score = 可逆性 × 影響度 × 明確度                 │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │ score ≥ 0.6  → 直接執行                          │ │
│  │ 0.2 ≤ score < 0.6 → 問用戶確認                   │ │
│  │ score < 0.2 → 預設不執行                         │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────┬───────────────────────────────────────┘
               │
        ┌──────┼──────────┐
        ▼      ▼          ▼
    直接執行  確認後執行   不執行
        │      │          │
        ▼      ▼          ▼
┌──────────────────────────────────────────────────────┐
│ Phase 3: 執行                                          │
│  Handler/Agent 執行                                    │
│  輸出: ActionResult(success, result, error,            │
│                     rollback_info)                     │
└──────────────┬───────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────┐
│ Phase 4: 結果回饋 + LLM 續行                           │
│                                                       │
│  執行結果注入 prompt → LLM 看到事實                    │
│  LLM 決定：                                           │
│  ├─ 結束：描述結果                                     │
│  └─ 續行：問用戶要不要繼續（不能自動做）               │
│                                                       │
│  續行時：重新進 Phase 1（帶上下文）                     │
│  最多 3 次（防止無限迴圈）                              │
└──────────────┬───────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────┐
│ Phase 5: 回應                                          │
│  最終回應 = LLM 基於執行結果生成的文字                  │
└──────────────────────────────────────────────────────┘
```

### 4.2 狀態機

```
                    ┌─────────────┐
                    │   IDLE      │
                    └──────┬──────┘
                           │ 使用者輸入
                           ▼
                    ┌─────────────┐
                    │ CLASSIFY    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ AUTO     │ │ CONFIRM  │ │ REJECT   │
        │ EXECUTE  │ │ ASK      │ │          │
        │ score≥0.6│ │ 0.2-0.6  │ │ score<0.2│
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │
             │      ┌─────┴─────┐      │
             │      ▼           ▼      │
             │  ┌────────┐ ┌────────┐  │
             │  │ 確認   │ │ 取消   │  │
             │  └───┬────┘ └───┬────┘  │
             │      │          │       │
             ▼      ▼          ▼       ▼
        ┌──────────────────────────────────┐
        │         EXECUTE                  │
        └──────────────┬───────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │         RESULT                   │
        └──────────────┬───────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │         LLM_RESPOND              │
        └──────────────┬───────────────────┘
                       │
              ┌────────┴────────┐
              ▼                 ▼
        ┌──────────┐      ┌──────────┐
        │ DONE     │      │ CONTINUE │
        │ → IDLE   │      │ → CLASSIFY│
        └──────────┘      └──────────┘
```

---

## 5. 各情境完整流程

### 5.1 情境 A：讀取類（高可逆） → 直接執行

```
使用者: "搜尋台北今天天氣"
    │
    ▼
Phase 1: SEARCH, confidence=0.88
    │
    ▼
Phase 2: action_type=read, exec_score = 1.0 × 1.0 × 0.9 = 0.900
         0.900 ≥ 0.6 → 直接執行
    │
    ▼
Phase 3: WebSearchHandler.execute("搜尋台北今天天氣")
    │      → ActionResult(success=True, result="台北 28°C 晴天 濕度65%")
    │
    ▼
Phase 4: 結果注入 prompt
    │      [執行結果] 類型:SEARCH 成功:是 結果:台北 28°C 晴天
    │      LLM 看到結果 → 不需要更多操作 → 結束
    │
    ▼
Phase 5: "台北今天天氣是 28°C，晴天，濕度 65%。"
```

### 5.2 情境 B：刪除類（低可逆） → 問用戶

```
使用者: "刪除 temp.txt"
    │
    ▼
Phase 1: FILE, confidence=0.92
    │
    ▼
Phase 2: action_type=delete, exec_score = 0.2 × 0.4 × 0.9 = 0.072
         0.072 < 0.2 → 預設不執行
    │
    ▼
Phase 3: 不執行，回問用戶
    │      "你想要刪除嗎？"
    │      "⚠️ 刪除後無法復原。"
    │      "確認後我會執行。"
    │
    ▼
使用者: "好，確認"
    │
    ▼
Phase 3 (第2輪): FileOperationHandler.execute("刪除 temp.txt")
    │      → ActionResult(success=True, result="已刪除 temp.txt")
    │
    ▼
Phase 5: "已刪除 temp.txt。"
```

### 5.3 情境 C：比喻（明確度低） → 問用戶做什麼

```
使用者: "幫我查一下字典"
    │
    ▼
Phase 1: SEARCH, confidence=0.75
    │
    ▼
Phase 2: action_type=read, exec_score = 1.0 × 1.0 × 0.3 = 0.300
         0.300 在 [0.2, 0.6) → 問用戶確認
    │
    ▼
Phase 3: "你想要搜尋什麼？可以更具體說明嗎？"
    │
    ▼
使用者: "查 Python 的 list comprehension"
    │
    ▼
Phase 1 (第2輪): SEARCH, confidence=0.90
    │
    ▼
Phase 2: exec_score = 1.0 × 1.0 × 0.95 = 0.950 → 直接執行
    │
    ▼
Phase 3: WebSearchHandler.execute()
    │      → ActionResult(success=True, result="Python list comprehension: ...")
    │
    ▼
Phase 5: "Python list comprehension 的用法：..."
```

### 5.4 情境 D：不執行（分數太低）

```
使用者: "今天?"
    │
    ▼
Phase 1: UNKNOWN, confidence=0.3
    │
    ▼
Phase 2: action_type=none, exec_score = 1.0 × 1.0 × 0.2 = 0.200
         0.200 ≥ 0.2 → 問用戶（但因為是 none 類，直接問）
    │
    ▼
Phase 5: "你是想問今天幾點？還是今天的天氣？還是今天的行程？"
```

### 5.5 情境 E：誤觸修正

```
使用者: "開玩笑"
    │
    ▼
Phase 1 (v2): UNKNOWN, confidence=0.3, action_type=none
    │          (word boundary 修正，"開" 不再匹配 EXECUTE)
    │
    ▼
Phase 2: exec_score = 0.0 → 不執行
    │
    ▼
Phase 5: "哈哈，你真幽默！有什麼我能幫忙的嗎？"
```

### 5.6 情境 F：否定意圖

```
使用者: "不要搜尋"
    │
    ▼
Phase 1: SEARCH, confidence=0.75
    │      (含否定詞「不要」→ confidence 降低)
    │
    ▼
Phase 2: action_type=read, exec_score = 1.0 × 1.0 × 0.4 = 0.400
         0.400 在 [0.2, 0.6) → 但含否定詞
    │
    │      檢查否定詞 → 強制 reject
    │
    ▼
Phase 5: "好的，不搜尋。還有什麼需要幫忙的嗎？"
```

### 5.7 情境 G：多步驟 → 分步執行

```
使用者: "幫我搜尋 Python 教學，然後整理成筆記"
    │
    ▼
Phase 1: primary=SEARCH (0.85), secondary=FILE (0.70)
    │
    ▼
Phase 2: 先處理 primary
         SEARCH: action_type=read, exec_score = 1.0 × 1.0 × 0.85 = 0.850 → 直接執行
         有 secondary → 暫不處理
    │
    ▼
Phase 3: WebSearchHandler.execute()
    │      → ActionResult(success=True, result="找到 5 篇 Python 教學...")
    │
    ▼
Phase 4: 結果注入 prompt
    │      LLM 判斷：用戶還要求「整理成筆記」→ 問用戶要不要繼續
    │      LLM: "找到 5 篇教學，要我整理成筆記嗎？"
    │
    ▼
使用者: "好"
    │
    ▼
Phase 1 (第2輪): FILE, confidence=0.88
    │
    ▼
Phase 2: action_type=create, exec_score = 0.9 × 0.9 × 0.9 = 0.729 → 直接執行
    │
    ▼
Phase 3: FileOperationHandler.execute("整理成筆記")
    │      → ActionResult(success=True, result="已建立 py_notes.md")
    │
    ▼
Phase 5: "已將 5 篇教學整理成筆記，存在 py_notes.md。"
```

### 5.8 情境 H：LLM 續行 → 只能問，不能做

```
使用者: "搜尋今天的新聞"
    │
    ▼
Phase 3: WebSearchHandler.execute()
    │      → ActionResult(success=True, result="今天的新聞有：...")
    │
    ▼
Phase 4: LLM 看到結果
    │      LLM 想續行 → 但不能自動做
    │
    ▼
Phase 5: "今天的新聞有：[結果]。需要我幫你整理或儲存嗎？"
         (問用戶，不自動做)
```

### 5.9 情境 I：執行失敗 → 告知原因

```
使用者: "刪除 system32"
    │
    ▼
Phase 2: action_type=delete, exec_score = 0.2 × 0.4 × 0.9 = 0.072
         0.072 < 0.2 → 預設不執行
    │
    ▼
Phase 3: "你想要刪除嗎？⚠️ 刪除後無法復原。確認後我會執行。"
    │
    ▼
使用者: "確認"
    │
    ▼
Phase 3 (第2輪): FileOperationHandler.execute("刪除 system32")
    │      → ActionResult(success=False, error="權限不足或路徑不安全")
    │
    ▼
Phase 4: 結果注入 prompt
    │      [執行結果] 類型:FILE 成功:否 錯誤:權限不足或路徑不安全
    │      LLM 看到失敗 → 告知原因
    │
    ▼
Phase 5: "無法刪除 system32：系統資料夾受保護，不建議刪除。"
```

---

## 6. QueryClassifier v2 設計

### 6.1 分類器輸出

```python
@dataclass
class QueryResult:
    primary_type: QueryType
    confidence: float                    # 0.0-1.0
    actionability: float                 # 0.0-1.0
    action_type: str                     # "read"/"create"/"modify"/"delete"/"send"/"system"/"none"
    secondary_type: Optional[QueryType]
    secondary_confidence: float
    reason: str
```

### 6.2 動態置信度

```python
def _calculate_confidence(self, query_type, text, match):
    base = self._base_conf[query_type]

    if match.anchored:
        base += 0.05

    density = match.keyword_count / max(1, len(text.split()))
    if density > 0.5:
        base += 0.05
    elif density < 0.2:
        base -= 0.10

    if len(text) < 5:
        base -= 0.05
    elif len(text) > 50:
        base += 0.03

    if any(neg in text for neg in ["不要", "別", "取消", "stop"]):
        base -= 0.15

    return max(0.1, min(0.95, base))
```

### 6.3 Action Type 推斷

```python
def _infer_action_type(self, query_type, text):
    """根據意圖和文字推斷操作類型"""
    # 直接匹配
    if query_type in ("GREETING", "REFLEX", "OPINION", "CREATIVE", "KNOWLEDGE"):
        return "none"

    # 讀取類
    if query_type in ("SEARCH", "VISION", "AUDIO"):
        # 如果含寫入詞 → modify
        if any(w in text for w in ["寫入", "儲存", "save", "write"]):
            return "modify"
        return "read"

    # FILE 類：根據動詞判斷
    if query_type == "FILE":
        if any(w in text for w in ["刪除", "移除", "清空", "delete", "remove"]):
            return "delete"
        if any(w in text for w in ["建立", "新增", "create", "new"]):
            return "create"
        if any(w in text for w in ["修改", "編輯", "重新命名", "edit", "rename", "modify"]):
            return "modify"
        return "read"  # 預設讀取

    # CODE/EXECUTE → system
    if query_type in ("CODE", "EXECUTE"):
        return "system"

    # TASK → create or modify
    if query_type == "TASK":
        if any(w in text for w in ["刪除", "取消", "delete", "cancel"]):
            return "delete"
        return "create"

    # COMMAND → 根據內容判斷
    if query_type == "COMMAND":
        return "read"  # 預設讀取，由具體 handler 決定

    return "none"
```

### 6.4 Regex 精確度修正

```python
# 所有 regex 使用 word boundary
r"(?:^|[\s，。！？,.\s])(執行|運行|開啟|關閉|啟動|停止)(?:$|[\s，。！？,.\s])"
```

### 6.5 REFLEX Override 修正

```python
VERBS_NOT_REFLEX = {"看", "查", "開", "關", "跑", "跳",
                     "讀", "寫", "聽", "說", "吃", "喝",
                     "搜", "刪", "改", "傳", "載"}

if text in self.reflex_words:
    return QueryResult(REFLEX, 0.95, ...)
elif len(text) < 2 and best_conf < 0.5:
    if text not in VERBS_NOT_REFLEX:
        return QueryResult(REFLEX, 0.95, ...)
    best_conf = max(0.4, best_conf)
```

### 6.6 `?` Override 修正

```python
KNOWLEDGE_Q = [
    r"^什麼是", r"^什麼是", r"^怎麼", r"^為什麼",
    r"^how\b", r"^what\b", r"^why\b", r"^when\b",
    r"^多少", r"^幾個", r"^誰",
]

if best_conf < 0.5 and text.endswith("?"):
    if any(re.search(p, text, re.I) for p in KNOWLEDGE_Q):
        return QueryResult(KNOWLEDGE, 0.65, "knowledge_question")
```

### 6.7 Tie-Breaking 改進

```python
matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
# 先比 confidence，再比 actionability
```

---

## 7. LLM 續行邏輯

### 7.1 Prompt 結構

```
[系統指令]
你是 Angela。你會收到使用者的訊息和可能的執行結果。
如果收到執行結果，你必須基於事實回應。
如果執行成功，描述結果。
如果執行失敗，說明原因並建議替代方案。
如果你判斷使用者還需要更多操作，問他們要不要繼續。
不要自動執行更多操作，除非使用者明確要求。

[對話歷史]
...

[使用者訊息]
{user_message}

[執行結果] (如果有)
類型: {action_type}
成功: {success}
結果: {result}
錯誤: {error}

[自主認知]
...
```

### 7.2 LLM 回應規則

| 類型 | 判斷方式 | 處理 |
|------|---------|------|
| **結束** | 不含提問/建議 | 直接回傳 |
| **建議繼續** | 含「要不要我...」 | 回傳，等用戶 |
| **自動續行** | ❌ 不允許 | LLM 不自動做更多 |

### 7.3 續行迴圈保護

```python
context["continuation_count"] = context.get("continuation_count", 0)
if context["continuation_count"] >= 3:
    context["action_result"] = None
    # 加入 prompt：請先確認用戶需求
```

---

## 8. 修正前 vs 修正後

| 輸入 | 修正前 | 修正後 |
|------|--------|--------|
| `開玩笑` | EXECUTE 0.8 ❌ | UNKNOWN, score=0.000 → 不執行 ✅ |
| `關心` | EXECUTE 0.8 ❌ | UNKNOWN, score=0.000 → 不執行 ✅ |
| `幫我查字典` | SEARCH 0.8 ❌ | SEARCH, score=0.300 → 問用戶 ✅ |
| `搜尋台北天氣` | SEARCH 0.8 ⚠️ | SEARCH, score=0.900 → 直接執行 ✅ |
| `讀取 temp.txt` | FILE 0.8 ⚠️ | FILE, score=0.950 → 直接執行 ✅ |
| `刪除 temp.txt` | FILE 0.8 ❌ 直接執行 | FILE, score=0.072 → 問用戶+影響說明 ✅ |
| `今天幾點?` | KNOWLEDGE 0.65 ⚠️ | UNKNOWN, score=0.200 → 問用戶 ✅ |
| `好看嗎?` | KNOWLEDGE 0.65 ❌ | OPINION, score=0.100 → 不執行 ✅ |
| `看` | REFLEX 0.95 ❌ | VISION, score=0.400 → 問用戶 ✅ |
| `不要搜尋` | SEARCH 0.8 ❌ | SEARCH, score=0.400 + 否定 → 不執行 ✅ |
| `幫我處理檔案` | FILE 0.8 ❌ | FILE, score=0.168 → 問用戶做什麼 ✅ |

---

## 9. 實作計畫

### Phase 1: QueryClassifier v2（2-3 天）

| # | 項目 | 檔案 | 工作量 |
|---|------|------|--------|
| 1.1 | 動態置信度計算 | `query_classifier.py` | 0.5 天 |
| 1.2 | Action type 推斷 | `query_classifier.py` | 0.5 天 |
| 1.3 | 多標籤分類 | `query_classifier.py` | 0.5 天 |
| 1.4 | Regex word boundary | `query_classifier.py` | 0.5 天 |
| 1.5 | REFLEX override 修正 | `query_classifier.py` | 0.25 天 |
| 1.6 | `?` override 修正 | `query_classifier.py` | 0.25 天 |
| 1.7 | Tie-breaking 改進 | `query_classifier.py` | 0.25 天 |
| 1.8 | 單元測試（30+ 測試） | `test_query_classifier.py` | 0.5 天 |

### Phase 2: 執行分數 + 決策閘門（2-3 天）

| # | 項目 | 檔案 | 工作量 |
|---|------|------|--------|
| 2.1 | ExecutionGate 類 | `router.py` | 0.5 天 |
| 2.2 | 確認機制（含影響說明） | `router.py` | 0.5 天 |
| 2.3 | 否定詞檢測 | `router.py` | 0.25 天 |
| 2.4 | Handler 路由表 | `model_bus.py` | 1 天 |
| 2.5 | Result injection prompt | `prompt_builder.py` | 0.5 天 |
| 2.6 | 純聊天快速路徑 | `router.py` | 0.25 天 |
| 2.7 | 續行迴圈保護 | `router.py` | 0.25 天 |
| 2.8 | 單元測試 | `test_router.py` | 0.5 天 |

### Phase 3: 整合測試（1-2 天）

| # | 測試案例 |
|---|---------|
| 3.1 | 讀取類直接執行（5 個） |
| 3.2 | 刪除類問用戶（5 個） |
| 3.3 | 比喻不執行（5 個） |
| 3.4 | 誤觸不執行（5 個） |
| 3.5 | 否定不執行（5 個） |
| 3.6 | 執行成功回饋 LLM（5 個） |
| 3.7 | 執行失敗回饋 LLM（5 個） |
| 3.8 | 確認機制（5 個） |
| 3.9 | 多步驟任務（5 個） |
| 3.10 | 續行迴圈保護（3 個） |
| 3.11 | 舊 86 個測試仍通過 |

---

## 10. 驗收標準

### 精確度
- [ ] `"開玩笑"` → 不執行 (score=0.0)
- [ ] `"關心"` → 不執行 (score=0.0)
- [ ] `"幫我查字典"` → 問用戶 (score=0.3)
- [ ] `"搜尋台北天氣"` → 直接執行 (score=0.9)
- [ ] `"讀取 temp.txt"` → 直接執行 (score=0.95)
- [ ] `"刪除 temp.txt"` → 問用戶+影響說明 (score=0.07)
- [ ] `"今天幾點?"` → 問用戶 (score=0.2)
- [ ] `"好看嗎?"` → 不執行 (score=0.1)
- [ ] `"看"` → 問用戶 (score=0.4)
- [ ] `"不要搜尋"` → 不執行（否定）

### 知行合一
- [ ] 執行成功 → LLM 回應包含結果
- [ ] 執行失敗 → LLM 回應說明原因
- [ ] LLM 不能自動執行更多操作
- [ ] 續行迴圈 ≤ 3 次

### 回歸
- [ ] 舊 86 個測試仍通過
- [ ] 新增 ≥ 30 個邊界測試

---

## 11. 與架構文檔對齊

本計畫與以下文檔一致：
- **AGENTS.md**: Surgical Precision（精確修改目標檔案）, No Placeholders（所有邏輯完整實作）
- **ANGELA_FULL_ARCHITECTURE.md**: 管線流程（Phase 1-5）符合十一章完整管線流程
- **README.md**: 管線描述（WebSocket → 情緒 → 危機 → 對齊 → LLM → 因果學習 → 回應）
