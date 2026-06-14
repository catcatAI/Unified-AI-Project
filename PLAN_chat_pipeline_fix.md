# Chat Pipeline 完整修復計劃 v2

**日期:** 2026-06-14
**基於:** 完整代碼審計（template_matcher.py, composer.py, ham_manager.py, memory_integration.py, router.py, emotion_analyzer.py, biological_integrator.py, prompt_builder.py, websocket_manager.py, chat_routes.py, chat_service.py）
**目標:** 修復聊天管線中所有中間層斷線，恢復設計意圖
**狀態:** ✅ 全部 11 個根因已修復，9 個文件語法檢查通過

---

## 問題全景

### 完整管線流程（設計意圖 vs 實際）

```
用戶訊息
    │
    ▼
[1] TemplateMatcher.match() ──→ 設計: 3 級匹配（exact → semantic → fuzzy）
    │                            實際: 模板從未載入（router.py 競態條件）→ 永遠 NO_MATCH
    │
    ▼ (score = 0)
[2] MemoryIntegration.try_memory_retrieval()
    │  設計: 從HAM記憶庫檢索匹配模板
    │  實際: ham_manager 只回傳最後 N 筆（不做匹配）→ 硬編碼 score=0.8
    │
    ▼ (如果 ham_manager 有模板)
[3] 返回模板內容 ──→ 不管查詢是啥，都返回最近存的模板
    │
    ▼ (如果 ham_manager 為空)
[4] LLM_FULL ──→ 唯一真正運作的路徑
    │
    ▼
[5] prompt_builder ──→ 設計: 注入 bio_state + 8軸 + history
    │                   實際: context 只有 user_name → prompt 缺少所有關鍵資訊
    │
    ▼
[6] 回應返回 ──→ 設計: 含情緒分析結果
                  實際: 硬編碼 "happy" / 0.5
```

---

## 根因分析（按嚴重性排序）

### 🔴 ROOT-1：模板從未載入 TemplateMatcher

**文件:** `router.py:211-278`
**問題:** `_load_templates_to_matcher()` 在 line 211 被呼叫，但 `self.template_library` 在 line 278 才賦值。`_load_templates_to_matcher` 檢查 `hasattr(self, "template_library")` → False → 0 個模板載入。

**影響:** TemplateMatcher 永遠為空，`match()` 永遠回傳 `NO_MATCH`。

**修法:** 將 `_load_templates_to_matcher()` 的呼叫移到 `template_library` 賦值之後。

```python
# router.py _init_response_system() 中：
# 1. 先建立 TemplateMatcher 和 ResponseComposer（不變）
# 2. 記憶初始化完成後再載入模板
self.template_library = get_template_library()
self._load_templates_to_matcher()  # 移到這裡
```

---

### 🔴 ROOT-2：ham_manager.retrieve_response_templates 不做匹配

**文件:** `ham_manager.py:54-64`
**問題:** 只執行 `return self._data["templates"][-count:]`，完全忽略 `query`、`min_score`、`angela_state`、`user_impression`。

**修法:** 實作基於關鍵字的匹配演算法：

```python
async def retrieve_response_templates(self, query, top_k=5, angela_state=None,
                                       user_impression=None, limit=5, min_score=0.0):
    candidates = self._data.get("templates", [])
    if not candidates:
        return []

    scored = []
    query_chars = set(query)
    for tpl in candidates:
        keywords = tpl.get("keywords", [])
        if not keywords:
            continue
        # 計算關鍵字匹配分數
        best_score = 0.0
        for kw in keywords:
            kw_chars = set(kw)
            intersection = query_chars & kw_chars
            union = query_chars | kw_chars
            if union:
                jaccard = len(intersection) / len(union)
                # 關鍵字完全包含在查詢中加分
                if kw in query:
                    best_score = max(best_score, min(0.95, jaccard * 1.5))
                else:
                    best_score = max(best_score, jaccard)
        if best_score >= min_score:
            scored.append((tpl, best_score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit or top_k]
```

**注意:** 保留 `min_score` 閾值。`min_score=0.0` 表示不過濾（向後兼容）。

---

### 🔴 ROOT-3：ChatService context 嚴重不足

**文件:** `chat_service.py:56-69`
**問題:** `generate_response()` 只傳 `{"user_name": user_name}` 給 LLM。`construct_angela_prompt()` 期望的 `state_for_llm`、`history`、`user_profile` 全部缺失。

**修法:** 重寫 `ChatService.generate_response` 接收並傳遞完整 context：

```python
async def generate_response(self, user_message, user_name="", context=None):
    if not self._initialized:
        await self.initialize()
    
    # 合併 caller context
    merged_context = context or {}
    merged_context.setdefault("user_name", user_name)
    
    response = await self._llm_service.generate_response(user_message, merged_context)
    
    if self._continuous_learning:
        await self._continuous_learning.process_interaction_async(
            user_message, response.text, merged_context
        )
    
    return response
```

---

### 🔴 ROOT-4：chat_routes.py 不注入情緒分析

**文件:** `chat_routes.py:84-171`
**問題:** `EmotionAnalyzer` 存在但從未呼叫。情緒永遠硬編碼。

**修法:**

```python
# chat_routes.py _handle_chat_request() 中：
emotion_result = None
try:
    from services.llm.emotion_analyzer import EmotionAnalyzer
    analyzer = EmotionAnalyzer()
    emotion_result = analyzer.analyze_emotion(user_message)
except Exception:
    pass

context["emotion"] = emotion_result  # 傳入 LLM context

# ... LLM 回應後 ...
response_dict = {
    "response_text": response_text,
    "source": source,
    "emotion": emotion_result.get("emotion", "neutral") if emotion_result else "neutral",
    "emotion_confidence": emotion_result.get("confidence", 0.5) if emotion_result else 0.5,
    "emotion_intensity": emotion_result.get("intensity", 0.5) if emotion_result else 0.5,
    "session_id": session_id,
}
```

---

### 🔴 ROOT-5：prompt_builder 生物狀態用檔案讀取

**文件:** `prompt_builder.py:29-34`
**問題:** `get_biological_state()` 讀取 `data/brain_status.json`，但此檔案可能不存在或過期。`BiologicalIntegrator.get_biological_state()` 的即時狀態未被使用。

**修法:** 修改 `get_biological_state()` 支援 context 注入：

```python
def get_biological_state(context=None):
    # 優先使用 context 中的即時狀態
    if context and "bio_state" in context:
        bio = context["bio_state"]
        return _format_bio_state(bio)
    
    # Fallback 到檔案讀取
    try:
        with open("data/brain_status.json") as f:
            bio = json.load(f)
        return _format_bio_state(bio)
    except (FileNotFoundError, json.JSONDecodeError):
        return "生物狀態：尚未初始化"
```

---

### 🟡 ROOT-6：對話歷史為空且全局共享

**文件:** `websocket_manager.py:228`, `router.py:562-566`
**問題:** 
- WebSocket 路徑 `history=[]` 永遠空
- `AngelaLLMService.conversation_history` 是全局 singleton，所有 session 共享

**修法:** 在 SessionManager 中維護 per-session 歷史：

```python
# websocket_manager.py
# SessionManager 需要新增對話歷史欄位
# _handle_chat_message 中：
history = session_manager.get_history(session_id)[-10:]  # 最近 10 條
response = await _handle_chat_request(
    user_message, user_name, history=history, session_id=session_id
)
session_manager.append_history(session_id, {"role": "user", "content": user_message})
session_manager.append_history(session_id, {"role": "assistant", "content": response["response_text"]})
```

---

### 🟡 ROOT-7：broadcast_state_updates 結構對應錯誤

**文件:** `websocket_manager.py:134-137`
**問題:** 讀取 `bio_state.get("fatigue")` 和 `bio_state.get("hormones")`，但 `get_biological_state()` 回傳的是 `stress_level` 和 `hormonal_effects`。

**修法:** 修正 key 對應：

```python
state_data = {
    "alpha": {"energy": bio_state.get("arousal", 50) / 100, ...},
    "gamma": {"happiness": bio_state.get("mood", 0.5), ...},
    "delta": {"intensity": bio_state.get("stress_level", 0.3)},
    # fatigue → arousal/100 的反向
    # hormones → hormonal_effects
}
```

---

### 🟡 ROOT-8：BiologicalIntegrator 假 Singleton

**文件:** `biological_integrator.py:140-141`
**問題:** `__init__` 用 `if getattr(self, "_initialized", False): return` 但不回傳 `self`。第二次實例化會得到空殼物件。

**修法:** 改用真正的 singleton pattern：

```python
_instance = None

class BiologicalIntegrator:
    def __new__(cls, config=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config=None):
        if self._initialized:
            return
        self._initialized = True
        # ... 初始化 ...
```

---

### 🟡 ROOT-9：TemplateMatcher 演算法缺陷

**文件:** `template_matcher.py`
**問題:**
- Semantic hash 實際只是 normalized exact match（不是語義匹配）
- 中文分詞是字元級別（每個字 = 1 個 keyword），Jaccard 噪音大

**修法:** 改用基於關鍵字重疊的匹配（不改架構，只改演算法）：

```python
def _calculate_similarity(self, query, template):
    """基於關鍵字重疊的相似度"""
    query_keywords = set(self._extract_keywords(query))
    template_keywords = set(template.keywords)
    if not query_keywords or not template_keywords:
        return 0.0
    intersection = query_keywords & template_keywords
    union = query_keywords | template_keywords
    jaccard = len(intersection) / len(union) if union else 0.0
    # 關鍵字命中率加權
    coverage = len(intersection) / len(template_keywords) if template_keywords else 0.0
    return min(0.95, jaccard * 0.6 + coverage * 0.4)
```

---

### 🟢 ROOT-10：memory_integration.py dict/tuple 判斷

**文件:** `memory_integration.py:100-112`
**問題:** 為了兼容 ham_manager 的 dict 回傳和假設的 tuple 回傳，寫了複雜的判斷邏輯。

**修法:** ROOT-2 修復後，ham_manager 統一回傳 `(template, score)` tuple，此處簡化為：

```python
if results and len(results) > 0:
    best_template, score = results[0]
    if score < 0.3:
        return None  # 分數太低，不命中
    template_content = best_template.get("content", "")
    template_id = best_template.get("id", "unknown")
    return LLMResponse(
        text=template_content,
        backend="memory-template",
        model="template-based",
        confidence=score,
        metadata={"template_id": template_id, "template_score": score, "memory_hit": True},
    )
```

---

### 🟢 ROOT-11：生物系統不接受聊天輸入

**文件:** `chat_routes.py`, `websocket_manager.py`
**問題:** 聊天不觸發 `BiologicalIntegrator` 的任何處理方法。

**修法:** 在 `_handle_chat_request` 中：

```python
# 情緒分析後，觸發生物狀態更新
try:
    from core.bio.biological_integrator import BiologicalIntegrator
    bio = BiologicalIntegrator()
    # 聊天作為聽覺刺激
    bio.process_auditory_stimulus(volume=0.6, content=user_message)
    # 如果情緒強烈，觸發壓力/放鬆事件
    if emotion_result:
        if emotion_result["emotion"] in ("sad", "angry", "fear"):
            bio.process_stress_event(intensity=emotion_result["intensity"] * 0.3)
        elif emotion_result["emotion"] in ("happy", "calm"):
            bio.process_relaxation_event(intensity=emotion_result["intensity"] * 0.2)
except Exception:
    pass  # 生物系統是 best-effort
```

---

## 實作順序（依賴關係）

| 階段 | 任務 | 依賴 | 預估 |
|------|------|------|------|
| **1** | ROOT-1：修復模板載入時機 | 無 | 10 min |
| **2** | ROOT-2：修復 ham_manager 匹配邏輯 | 無 | 20 min |
| **3** | ROOT-10：簡化 memory_integration | ROOT-2 | 10 min |
| **4** | ROOT-3：ChatService context 完整化 | 無 | 15 min |
| **5** | ROOT-5：prompt_builder 生物狀態注入 | 無 | 10 min |
| **6** | ROOT-4：情緒分析接入 | 無 | 15 min |
| **7** | ROOT-6：per-session 對話歷史 | ROOT-3 | 20 min |
| **8** | ROOT-7：broadcast key 修正 | 無 | 10 min |
| **9** | ROOT-8：BiologicalIntegrator singleton | 無 | 10 min |
| **10** | ROOT-9：TemplateMatcher 演算法改良 | ROOT-1 | 15 min |
| **11** | ROOT-11：生物系統接受聊天輸入 | ROOT-4 | 10 min |

**總計:** ~2.5 小時

---

## 驗證矩陣

| 測試案例 | 預期結果 | 驗證方式 |
|----------|---------|---------|
| 發送 "喵?" | 匹配到帶 "喵?" keyword 的模板 | 觀察 log: `COMPOSED` 或 `HYBRID` route |
| 發送完全不同的訊息 | 不匹配任何模板，走 LLM_FULL | 觀察 log: `LLM_FULL` route |
| 發送 "我好難過" | 情緒分析返回 sad，生物狀態更新 | 觀察 log: `emotion: sad`，state_update 中 delta 變化 |
| 連續發送 3 條訊息 | LLM 能參考前 2 條歷史 | 觀察 log: prompt 中包含 history |
| 重啟後發送 "喵?" | 不再卡在同個回覆 | 回覆內容隨機/多樣 |
| 觸摸像素角色 | 生物反饋正常 | 觸摸後 state_update 中 arousal 變化 |

---

## 風險評估

| 風險 | 影響 | 緩解 |
|------|------|------|
| ROOT-2 加入 min_score 閾值可能讓之前「能用」的匹配失效 | 中 | `min_score=0.0` 預設不過濾，逐步調高 |
| ROOT-7 broadcast key 修正可能影響桌面端/web 端 | 低 | key 名稱不變，只修正值來源 |
| ROOT-8 singleton 修正可能影響多處實例化 | 中 | 確保所有使用處都改為 `BiologicalIntegrator()` |
| ROOT-9 演算法改良可能改變匹配行為 | 中 | 保留舊的 hash-based 匹配作為 fallback |

---

## 不修改的組件（確認正常運作）

| 組件 | 狀態 |
|------|------|
| TemplateMatcher 架構（hash index + keyword index） | ✅ 架構正確，只是模板未載入 |
| ResponseComposer.compose_response() | ✅ 正確 |
| DeviationTracker | ✅ 正確 |
| EmotionAnalyzer.analyze_emotion() | ✅ 正確，只是未接入 |
| BiologicalIntegrator 核心邏輯 | ✅ 正確，只是 singleton 和 key mapping 有問題 |
| prompt_builder.construct_angela_prompt() | ✅ 正確，只是 context 不足 |
| ChatService 架構 | ✅ 正確，只是 context 傳遞不完整 |
