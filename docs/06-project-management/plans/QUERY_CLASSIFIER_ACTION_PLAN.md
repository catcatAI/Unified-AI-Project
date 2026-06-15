# QueryClassifier 精確度審查 + 執行路由計畫 v2

**日期**: 2026-06-15
**目標**: 讓 Angela 知行合一 — 意圖分類精確、執行結果回饋 LLM、不確定時不亂做

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

## 2. 完整生命週期

### 2.1 流程圖

```
使用者輸入
    │
    ▼
┌──────────────────────────────────────────────────────┐
│ Phase 1: 意圖分類                                      │
│                                                        │
│  QueryClassifier v2                                    │
│  ├─ primary_type: 意圖類型                              │
│  ├─ confidence: 置信度 (0.0-1.0)                       │
│  ├─ actionability: 可執行性 (0.0-1.0)                  │
│  └─ secondary_type: 次要意圖 (可選)                     │
└──────────────┬───────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────┐
│ Phase 2: 決策閘門                                      │
│                                                        │
│  ┌─────────────────────────────────────────────────┐  │
│  │ 條件 A: confidence ≥ 0.85                        │  │
│  │         AND actionability ≥ 0.7                  │  │
│  │         → 直接執行（自動）                         │  │
│  ├─────────────────────────────────────────────────┤  │
│  │ 條件 B: confidence 0.65-0.85                     │  │
│  │         OR actionability 0.5-0.7                 │  │
│  │         → 確認後執行（問用戶）                     │  │
│  ├─────────────────────────────────────────────────┤  │
│  │ 條件 C: confidence < 0.65                        │  │
│  │         AND actionability < 0.5                  │  │
│  │         → 純聊天（跳過執行）                       │  │
│  └─────────────────────────────────────────────────┘  │
└──────────────┬───────────────────────────────────────┘
               │
        ┌──────┼──────────┐
        ▼      ▼          ▼
    直接執行  確認後執行   純聊天
        │      │          │
        ▼      ▼          ▼
┌──────────────────────────────────────────────────────┐
│ Phase 3: 執行                                          │
│                                                        │
│  Handler/Agent 執行                                    │
│  輸出: ActionResult(success, result, error,             │
│                     side_effects, rollback_info)        │
│                                                        │
│  side_effects: 執行產生的副作用（刪除了檔案、發送了訊息等）│
│  rollback_info: 如果可以撤銷，提供撤銷方法               │
└──────────────┬───────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────┐
│ Phase 4: 結果回饋 + LLM 續行                           │
│                                                        │
│  執行結果注入 prompt → LLM 看到事實                     │
│  LLM 有兩個選擇：                                       │
│  ├─ 結束：描述結果，對話結束                             │
│  └─ 續行：需要更多資訊 / 需要進一步操作                  │
│                                                        │
│  如果 LLM 判斷需要續行：                                │
│  → 重新進 Phase 1（但帶上下文）                         │
│  → 最多重構 3 次（防止無限迴圈）                         │
└──────────────┬───────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────┐
│ Phase 5: 回應                                          │
│                                                        │
│  最終回應 = LLM 基於執行結果生成的文字                   │
│  包含：做了什麼、結果是什麼、下一步建議（如有）           │
└──────────────────────────────────────────────────────┘
```

### 2.2 完整狀態機

```
                    ┌─────────────┐
                    │   IDLE      │
                    └──────┬──────┘
                           │ 使用者輸入
                           ▼
                    ┌─────────────┐
                    │ CLASSIFY    │ ← Phase 1
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ AUTO     │ │ CONFIRM  │ │ CHAT     │
        │ EXECUTE  │ │ ASK      │ │ ONLY     │
        │ conf≥0.85│ │ 0.65-0.85│ │ conf<0.65│
        │ act≥0.7  │ │ OR act   │ │ AND act  │
        │          │ │ 0.5-0.7  │ │ <0.5     │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │
             │            │ 用戶確認?   │
             │      ┌─────┴─────┐      │
             │      ▼           ▼      │
             │  ┌────────┐ ┌────────┐  │
             │  │ 確認   │ │ 取消   │  │
             │  │ 執行   │ │ → IDLE │  │
             │  └───┬────┘ └────────┘  │
             │      │                  │
             ▼      ▼                  ▼
        ┌──────────────────────────────────┐
        │         EXECUTE                  │
        │  Handler/Agent 執行              │
        └──────────────┬───────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │         RESULT                   │
        │  ActionResult 回傳              │
        └──────────────┬───────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │         LLM_RESPOND              │
        │  LLM 看到執行結果                │
        │  決定：結束 or 續行？             │
        └──────────────┬───────────────────┘
                       │
              ┌────────┴────────┐
              ▼                 ▼
        ┌──────────┐      ┌──────────┐
        │ DONE     │      │ CONTINUE │
        │ 回應結束 │      │ 回到     │
        │ → IDLE   │      │ CLASSIFY │
        └──────────┘      └──────────┘
```

---

## 3. 各情境完整流程

### 3.1 情境 A：意圖清晰 → 直接執行

```
使用者: "搜尋台北今天天氣"
    │
    ▼
Phase 1: SEARCH, confidence=0.88, actionability=0.9
    │
    ▼
Phase 2: 條件 A 成立 (conf≥0.85, act≥0.7) → 直接執行
    │
    ▼
Phase 3: WebSearchHandler.execute("搜尋台北今天天氣")
    │      → ActionResult(success=True, result="台北 28°C 晴天 濕度65%")
    │
    ▼
Phase 4: 結果注入 prompt
    │      [執行結果] 類型:SEARCH 成功:是 結果:台北 28°C 晴天
    │
    │      LLM 看到結果，決定：
    │      → 用戶只問天氣，不需要更多操作 → 結束
    │
    ▼
Phase 5: "台北今天天氣是 28°C，晴天，濕度 65%。"
```

### 3.2 情境 B：意圖模糊 → 問用戶確認

```
使用者: "幫我處理一下這個檔案"
    │
    ▼
Phase 1: FILE, confidence=0.72, actionability=0.6
    │
    ▼
Phase 2: 條件 B 成立 (conf 0.65-0.85, act 0.5-0.7) → 需要確認
    │
    ▼
Phase 3: 不執行，回問用戶
    │      "你想要對這個檔案做什麼？"
    │      "1. 刪除  2. 移動  3. 重新命名  4. 讀取內容"
    │
    ▼
使用者: "讀取內容"
    │
    ▼
Phase 1 (第2輪): FILE, confidence=0.90, actionability=0.85
    │              (因為「讀取」是明確動作)
    │
    ▼
Phase 2: 條件 A 成立 → 直接執行
    │
    ▼
Phase 3: FileOperationHandler.execute("讀取這個檔案")
    │      → ActionResult(success=True, result="檔案內容: ...")
    │
    ▼
Phase 5: "檔案內容是：..."
```

### 3.3 情境 C：意圖不清晰 → 不執行，純聊天

```
使用者: "今天?"
    │
    ▼
Phase 1: UNKNOWN, confidence=0.3, actionability=0.0
    │
    ▼
Phase 2: 條件 C 成立 (conf<0.65, act<0.5) → 純聊天
    │
    ▼
Phase 3: 跳過，不執行
    │
    ▼
Phase 4: LLM 直接回應（無執行結果）
    │
    ▼
Phase 5: "你是想問今天幾點？還是今天的天氣？還是今天的行程？"
```

### 3.4 情境 D：執行失敗 → 告知原因 + 建議替代

```
使用者: "刪除 system32"
    │
    ▼
Phase 1: FILE, confidence=0.92, actionability=0.95
    │
    ▼
Phase 2: 條件 A 成立 → 直接執行
    │
    ▼
Phase 3: FileOperationHandler.execute("刪除 system32")
    │      → ActionResult(success=False, error="權限不足或路徑不安全")
    │
    ▼
Phase 4: 結果注入 prompt
    │      [執行結果] 類型:FILE 成功:否 錯誤:權限不足或路徑不安全
    │
    │      LLM 看到失敗，決定：
    │      → 告知用戶失敗原因，建議替代方案
    │
    ▼
Phase 5: "無法刪除 system32：系統資料夾受保護，不建議刪除。"
         "如果你是想清理空間，我可以幫你："
         "1. 清理暫存檔  2. 檢查大檔案  3. 卸載不用的程式"
```

### 3.5 情境 E：多步驟任務 → 分步執行

```
使用者: "幫我搜尋 Python 教學，然後整理成筆記"
    │
    ▼
Phase 1: primary=SEARCH (0.85), secondary=FILE (0.70), actionability=0.8
    │
    ▼
Phase 2: 條件 A 成立 (primary conf≥0.85, act≥0.7)
    │      但有 secondary → 暫不執行 secondary
    │
    ▼
Phase 3: 先執行 SEARCH
    │      → ActionResult(success=True, result="找到 5 篇 Python 教學...")
    │
    ▼
Phase 4: 結果注入 prompt
    │      [執行結果] 類型:SEARCH 成功:是 結果:找到 5 篇...
    │
    │      LLM 判斷：用戶還要求「整理成筆記」→ 需要續行
    │      LLM 回應：「找到 5 篇教學，要我整理成筆記嗎？」
    │
    ▼
使用者: "好"
    │
    ▼
Phase 1 (第2輪): FILE, confidence=0.88, actionability=0.9
    │              (「整理」是 FILE 類型的明確動作)
    │
    ▼
Phase 3: FileOperationHandler.execute("整理成筆記")
    │      → ActionResult(success=True, result="已建立筆記 py_notes.md")
    │
    ▼
Phase 5: "已將 5 篇教學整理成筆記，存在 py_notes.md。"
```

### 3.6 情境 F：否定意圖 → 不執行

```
使用者: "不要搜尋"
    │
    ▼
Phase 1: SEARCH, confidence=0.75, actionability=0.3
    │      (含否定詞「不要」→ actionability 降低)
    │
    ▼
Phase 2: 條件 C 成立 (act<0.5) → 純聊天
    │
    ▼
Phase 5: "好的，不搜尋。還有什麼需要幫忙的嗎？"
```

### 3.7 情境 G：誤判 → 自我修正

```
使用者: "開玩笑"
    │
    ▼
Phase 1 (v1): EXECUTE, confidence=0.8 ❌ 誤判
    │
    ▼ (v2 修正後)
Phase 1 (v2): UNKNOWN, confidence=0.3, actionability=0.0
    │          (word boundary 修正，"開" 不再匹配 EXECUTE)
    │
    ▼
Phase 2: 條件 C 成立 → 純聊天
    │
    ▼
Phase 5: "哈哈，你真幽默！有什麼我能幫忙的嗎？"
```

### 3.8 情境 H：LLM 續行 → 但不該做更多事

```
使用者: "搜尋今天的新聞"
    │
    ▼
Phase 1: SEARCH, confidence=0.90, actionability=0.9
    │
    ▼
Phase 3: WebSearchHandler.execute()
    │      → ActionResult(success=True, result="今天的新聞有：...")
    │
    ▼
Phase 4: LLM 看到結果
    │      LLM 想續行：「要不要我幫你整理？要不要儲存？」
    │      但用戶沒要求 → 不自動執行
    │
    ▼
Phase 5: "今天的新聞有：[結果]。需要我幫你整理或儲存嗎？"
         (問用戶，不自動做)
```

**關鍵規則：LLM 只能「問」用戶要不要做更多，不能自動做更多。**
除非用戶在同一次對話中已經明確要求了多步驟（情境 E）。

---

## 4. QueryClassifier v2 設計

### 4.1 分類器輸出

```python
@dataclass
class QueryResult:
    primary_type: QueryType           # 主要意圖
    confidence: float                 # 置信度 (0.0-1.0)
    actionability: float              # 可執行性 (0.0-1.0)
    secondary_type: Optional[QueryType]  # 次要意圖
    secondary_confidence: float       # 次要置信度
    reason: str                       # 分類原因（除錯用）
```

### 4.2 動態置信度

```python
def _calculate_confidence(self, query_type, text, match):
    base = self._base_conf[query_type]

    # 因子 1：匹配品質
    if match.anchored:
        base += 0.05  # 錨定匹配更可靠

    # 因子 2：關鍵字密度
    density = match.keyword_count / max(1, len(text.split()))
    if density > 0.5:
        base += 0.05
    elif density < 0.2:
        base -= 0.10

    # 因子 3：輸入長度
    if len(text) < 5:
        base -= 0.05
    elif len(text) > 50:
        base += 0.03

    # 因子 4：否定詞
    if any(neg in text for neg in ["不要", "別", "取消", "stop"]):
        base -= 0.15

    # 因子 5：上下文一致性（如果有 session history）
    # 如果上一輪是 SEARCH，這一輪也傾向 SEARCH
    if self._context_consistency_boost:
        base += self._context_consistency_boost

    return max(0.1, min(0.95, base))
```

### 4.3 Actionability Score

```python
# 高可執行性動詞（明確要操作）
ACTION_VERBS = {
    "搜尋": 0.9, "搜索": 0.9, "查詢": 0.85,
    "刪除": 0.95, "移動": 0.9, "複製": 0.9,
    "開啟": 0.85, "關閉": 0.85, "執行": 0.9,
    "下載": 0.9, "上傳": 0.9, "安裝": 0.9,
    "讀取": 0.8, "寫入": 0.85, "儲存": 0.8,
    "search": 0.9, "delete": 0.95, "run": 0.9,
    "execute": 0.9, "download": 0.9,
}

# 低可執行性模式（比喻/閒聊）
NON_ACTION_PATTERNS = [
    (r"幫我查一下字典", 0.1),
    (r"幫我看看時間", 0.1),
    (r"聽聽看", 0.1),
    (r"想想看", 0.1),
    (r"看看", 0.2),
    (r"試試看", 0.2),
]

def _calculate_actionability(self, text, query_type):
    # 類型基礎分
    type_base = {
        "execute": 0.9, "file": 0.85, "search": 0.8,
        "code": 0.75, "task": 0.7, "vision": 0.6,
        "audio": 0.6, "command": 0.5,
        "knowledge": 0.1, "opinion": 0.1, "creative": 0.1,
        "greeting": 0.0, "reflex": 0.0, "unknown": 0.0,
    }.get(query_type, 0.3)

    # 檢查是否有明確動作動詞
    for verb, score in ACTION_VERBS.items():
        if verb in text:
            type_base = max(type_base, score)

    # 檢查是否有比喻模式
    for pattern, penalty in NON_ACTION_PATTERNS:
        if re.search(pattern, text):
            type_base = min(type_base, penalty)

    # 否定詞
    if any(neg in text for neg in ["不要", "別", "取消"]):
        type_base = max(0.0, type_base - 0.5)

    return type_base
```

### 4.4 Regex 精確度修正

**問題：substring match 導致誤觸**

修正：所有 regex 使用 word boundary

```python
# Before (有問題)
r"(執行|運行|開啟|關閉|啟動|停止|..."

# After (修正)
r"(?:^|[\s，。！？,.\s])(執行|運行|開啟|關閉|啟動|停止)(?:$|[\s，。！？,.\s])"
```

**EXECUTE 特別修正：**
- `開啟` → 只匹配完整詞，不匹配 `開玩笑`
- `關閉` → 只匹配完整詞，不匹配 `關心`
- 新增：如果含否定詞（不要/別），降低 actionability 但不阻止分類

### 4.5 REFLEX Override 修正

```python
# 單字如果是明確動詞，不 override
VERBS_NOT_REFLEX = {"看", "查", "開", "關", "跑", "跳",
                     "讀", "寫", "聽", "說", "吃", "喝",
                     "搜", "刪", "改", "傳", "載"}

if text in self.reflex_words:
    return QueryResult(REFLEX, 0.95, ...)
elif len(text) < 2 and best_conf < 0.5:
    if text not in VERBS_NOT_REFLEX:
        return QueryResult(REFLEX, 0.95, ...)
    # 否則降低置信度但保持原分類
    best_conf = max(0.4, best_conf)
```

### 4.6 `?` Override 修正

```python
# 只有明確知識查詢模式才 override
KNOWLEDGE_Q = [
    r"^什麼是", r"^什麼是", r"^怎麼", r"^為什麼",
    r"^how\b", r"^what\b", r"^why\b", r"^when\b",
    r"^多少", r"^幾個", r"^誰",
]

if best_conf < 0.5 and text.endswith("?"):
    if any(re.search(p, text, re.I) for p in KNOWLEDGE_Q):
        return QueryResult(KNOWLEDGE, 0.65, "knowledge_question")
    # 否則保持 UNKNOWN
```

### 4.7 Tie-Breaking 改進

```python
# 收集所有匹配
matches = []
for qt, pattern, base_conf in self._patterns:
    if pattern.search(text):
        conf = self._calculate_confidence(qt, text, match)
        act = self._calculate_actionability(text, qt.value)
        matches.append((qt, conf, act))

# 排序：先比 confidence，再比 actionability
matches.sort(key=lambda x: (x[1], x[2]), reverse=True)

if matches:
    primary = matches[0]
    secondary = matches[1] if len(matches) > 1 and matches[1][1] >= primary[1] - 0.1 else None
    return QueryResult(
        primary_type=primary[0],
        confidence=primary[1],
        actionability=primary[2],
        secondary_type=secondary[0] if secondary else None,
        secondary_confidence=secondary[1] if secondary else 0.0,
    )
```

---

## 5. 決策閘門（Confidence Gate）

### 5.1 閘門邏輯

```python
class ConfidenceGate:
    """置信度閘門：決定要不要執行"""

    # 閾值
    AUTO_EXECUTE_CONF = 0.85     # 自動執行最低置信度
    AUTO_EXECUTE_ACT = 0.7       # 自動執行最低可執行性
    CONFIRM_CONF = 0.65          # 需要確認的最低置信度
    CONFIRM_ACT = 0.5            # 需要確認的最低可執行性

    def decide(self, result: QueryResult, context: dict) -> GateDecision:
        # 條件 A：直接執行
        if (result.confidence >= self.AUTO_EXECUTE_CONF and
            result.actionability >= self.AUTO_EXECUTE_ACT and
            result.primary_type.value in HANDLER_MAP):
            return GateDecision(action="auto_execute",
                              handler=result.primary_type.value,
                              reason="high_confidence_high_actionability")

        # 條件 B：需要確認
        if (result.confidence >= self.CONFIRM_CONF or
            result.actionability >= self.CONFIRM_ACT):
            # 檢查是否有 handler
            if result.primary_type.value in HANDLER_MAP:
                return GateDecision(action="confirm_then_execute",
                                  handler=result.primary_type.value,
                                  reason="medium_confidence_or_actionability",
                                  confirm_message=self._build_confirm_msg(result))
            # 沒有 handler，但有意圖 → 問用戶要幹嘛
            return GateDecision(action="ask_user",
                              reason="has_intent_but_no_handler",
                              confirm_message=self._build_ask_msg(result))

        # 條件 C：純聊天
        return GateDecision(action="chat_only",
                          reason="low_confidence_low_actionability")

    def _build_confirm_msg(self, result):
        """建立確認訊息"""
        type_desc = {
            "file": "操作檔案",
            "search": "搜尋",
            "code": "執行程式碼",
            "execute": "執行命令",
            "task": "管理任務",
            "vision": "分析圖片",
            "audio": "播放音訊",
        }
        desc = type_desc.get(result.primary_type.value, "執行操作")
        return f"你想要{desc}嗎？確認後我會執行。"

    def _build_ask_msg(self, result):
        """建立詢問訊息"""
        return "你想要我做什麼？可以更具體說明嗎？"
```

### 5.2 Router 整合

```python
# router.py 中的決策流程
async def _handle_chat_request(user_message, user_name, history, session_id, extra_context):
    # Phase 1: 意圖分類
    result = self.query_classifier.classify(user_message)

    # Phase 2: 決策閘門
    gate = ConfidenceGate()
    decision = gate.decide(result, context)

    if decision.action == "auto_execute":
        # 直接執行
        handler = self._get_handler(decision.handler)
        action_result = await handler.execute(user_message, context)
        context["action_result"] = action_result

    elif decision.action == "confirm_then_execute":
        # 問用戶確認
        return ChatResponse(
            content=decision.confirm_message,
            route=result.primary_type.value,
            hit_score=result.confidence,
            hit_source="gate_confirm",
            pending_action=decision,  # 暫存，等用戶確認
        )

    elif decision.action == "ask_user":
        # 問用戶要做什麼
        return ChatResponse(
            content=decision.confirm_message,
            route=result.primary_type.value,
            hit_score=result.confidence,
            hit_source="gate_ask",
        )

    elif decision.action == "chat_only":
        # 純聊天，跳過 ModelBus
        context["action_result"] = None

    # Phase 4: LLM 生成
    llm_response = await self.llm_service.generate(user_message, context)

    # Phase 5: 回應
    return ChatResponse(
        content=llm_response.text,
        route=result.primary_type.value,
        hit_score=result.confidence,
        hit_source="llm",
    )
```

### 5.3 確認機制

```python
# 當用戶回覆 "好" / "確認" / "是" 時
async def _handle_confirmation(self, user_message, pending_action, context):
    # 檢查是否是確認回覆
    confirm_words = {"好", "是", "確認", "ok", "yes", "sure", "確定"}
    cancel_words = {"不要", "取消", "算了", "no", "cancel", "skip"}

    if user_message.strip().lower() in confirm_words:
        # 執行
        handler = self._get_handler(pending_action.handler)
        action_result = await handler.execute(pending_action.original_query, context)
        context["action_result"] = action_result
        # 繼續 LLM 生成...

    elif user_message.strip().lower() in cancel_words:
        return ChatResponse(content="好的，不執行。還有什麼需要幫忙的嗎？")

    else:
        # 用戶沒有確認也沒有取消，當作新的輸入
        # 重新分類，帶上上下文
        return await self._handle_chat_request(user_message, ...)
```

---

## 6. LLM 續行邏輯

### 6.1 LLM 收到的 Prompt 結構

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

### 6.2 LLM 回應分類

LLM 的回應可以是：

| 類型 | 判斷方式 | 處理 |
|------|---------|------|
| **結束** | 回應中不含提問/建議 | 直接回傳 |
| **建議繼續** | 回應包含「要不要我...」 | 回傳，等用戶回覆 |
| **自動續行** | ❌ 不允許 | LLM 不應該自動做更多事 |

**關鍵規則：LLM 只能建議，不能自動做。**

### 6.3 續行迴圈保護

```python
# 在 session context 中追蹤
context["continuation_count"] = context.get("continuation_count", 0)

if context["continuation_count"] >= 3:
    # 防止無限迴圈
    context["action_result"] = None
    # 加入 prompt：用戶似乎需要更多幫助，但請先確認
```

---

## 7. 修正前 vs 修正後

| 輸入 | 修正前 | 修正後 |
|------|--------|--------|
| `開玩笑` | EXECUTE 0.8 ❌ 執行 | UNKNOWN 0.3, act=0.0 → 純聊天 ✅ |
| `關心` | EXECUTE 0.8 ❌ 執行 | UNKNOWN 0.3, act=0.0 → 純聊天 ✅ |
| `幫我查字典` | SEARCH 0.8 ❌ 執行 | SEARCH 0.6, act=0.3 → 純聊天 ✅ |
| `搜尋台北天氣` | SEARCH 0.8 ⚠️ 不確定 | SEARCH 0.88, act=0.9 → 直接執行 ✅ |
| `刪除 temp.txt` | FILE 0.8 ⚠️ | FILE 0.85, act=0.95 → 直接執行 ✅ |
| `今天幾點?` | KNOWLEDGE 0.65 ⚠️ | UNKNOWN 0.3, act=0.0 → 純聊天 ✅ |
| `好看嗎?` | KNOWLEDGE 0.65 ❌ | OPINION 0.6, act=0.1 → 純聊天 ✅ |
| `看` | REFLEX 0.95 ❌ | VISION 0.5, act=0.4 → 純聊天 ✅ |
| `不要搜尋` | SEARCH 0.8 ❌ 執行 | SEARCH 0.75, act=0.3 → 純聊天 ✅ |
| `幫我處理檔案` | FILE 0.8 ❌ 直接執行 | FILE 0.72, act=0.6 → 問用戶確認 ✅ |

---

## 8. 實作計畫

### Phase 1: QueryClassifier v2（2-3 天）

| # | 項目 | 檔案 | 工作量 |
|---|------|------|--------|
| 1.1 | 動態置信度計算 | `query_classifier.py` | 0.5 天 |
| 1.2 | Actionability score | `query_classifier.py` | 0.5 天 |
| 1.3 | 多標籤分類（primary/secondary） | `query_classifier.py` | 0.5 天 |
| 1.4 | Regex word boundary 修正 | `query_classifier.py` | 0.5 天 |
| 1.5 | REFLEX override 修正 | `query_classifier.py` | 0.25 天 |
| 1.6 | `?` override 修正 | `query_classifier.py` | 0.25 天 |
| 1.7 | Tie-breaking 改進 | `query_classifier.py` | 0.25 天 |
| 1.8 | 單元測試（新增 30+ 測試） | `test_query_classifier.py` | 0.5 天 |

### Phase 2: Confidence Gate + 執行路由（2-3 天）

| # | 項目 | 檔案 | 工作量 |
|---|------|------|--------|
| 2.1 | ConfidenceGate 類 | `router.py` | 0.5 天 |
| 2.2 | 確認機制（confirm/cancel） | `router.py` | 0.5 天 |
| 2.3 | Handler 路由表（補齊 code/execute/task/vision/audio） | `model_bus.py` | 1 天 |
| 2.4 | Result injection prompt | `prompt_builder.py` | 0.5 天 |
| 2.5 | 純聊天快速路徑（跳過 ModelBus） | `router.py` | 0.25 天 |
| 2.6 | 續行迴圈保護 | `router.py` | 0.25 天 |
| 2.7 | 單元測試 | `test_router.py` | 0.5 天 |

### Phase 3: 整合測試（1-2 天）

| # | 測試案例 |
|---|---------|
| 3.1 | 模糊查詢不誤觸（10 個案例） |
| 3.2 | 明確查詢正確執行（10 個案例） |
| 3.3 | 低置信度不執行（10 個案例） |
| 3.4 | 否定查詢不執行（5 個案例） |
| 3.5 | 執行成功回饋 LLM（5 個案例） |
| 3.6 | 執行失敗回饋 LLM（5 個案例） |
| 3.7 | 確認機制（5 個案例） |
| 3.8 | 多步驟任務（5 個案例） |
| 3.9 | 續行迴圈保護（3 個案例） |
| 3.10 | 舊 86 個測試仍通過 |

---

## 9. 驗收標準

### 精確度
- [ ] `"開玩笑"` → 不執行
- [ ] `"關心"` → 不執行
- [ ] `"幫我查字典"` → 不執行
- [ ] `"搜尋台北天氣"` → 直接執行
- [ ] `"刪除 temp.txt"` → 直接執行
- [ ] `"今天幾點?"` → 純聊天
- [ ] `"好看嗎?"` → 純聊天
- [ ] `"看"` → 不執行
- [ ] `"不要搜尋"` → 不執行

### 知行合一
- [ ] 執行成功 → LLM 回應包含結果
- [ ] 執行失敗 → LLM 回應說明原因
- [ ] LLM 不能自動執行更多操作（只能建議）
- [ ] 續行迴圈 ≤ 3 次

### 回歸
- [ ] 舊 86 個測試仍通過
- [ ] 新增 ≥ 30 個邊界測試
