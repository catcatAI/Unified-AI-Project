# Angela AI — 完整架構審計

## 一、信息流全圖

```
用戶輸入
  │
  ▼
┌─ chat_routes.py: _handle_chat_request() ──────────────────┐
│  Session 管理 + history 持久化                               │
└──────────────────────────────────────────────────────────┘
  │
  ▼
┌─ _run_chat_pipeline() ───────────────────────────────────┐
│                                                            │
│  Step 1:   驗證 + 截斷                                      │
│  Step 1.5: MainlineDispatcher → intent (GENERATE/LEARN/TRAIN)│
│  Step 2:   初始化 context                                   │
│  Step 3:   IntentRegistry.detect() + MathVerifier           │
│            → 數學？ → IntentRegistry 確認 → ★ 短路返回        │
│            → 否 → 注入 context["_math_result"]               │
│  Step 4:   情緒分析 + 危機等級                                │
│  Step 5b:  情緒行為注入 (routing_mode + response_style)      │
│  Step 5c:  自主生命週期注入                                   │
│  Step 5d:  意圖路由注入                                      │
│  Step 5e:  模態網關注入                                      │
│  Step 5f:  DLI 自我覺察注入                                  │
│  Step 5g:  IntentRegistry 路由 → context (不短路)            │
│  Step 5h:  DesktopInteraction 注入                          │
│  Step 6:   _build_chat_context() (bio/state/ED3N/記憶)       │
│  Step 7:   Execution gate → ★ 可短路 (auto/confirm/reject)   │
│  Step 8:   Agent routing → ★ 可短路 (creative/knowledge/...) │
│  Step 9:   因果預測注入                                      │
│  Step 10:  chat_svc.generate_response()                     │
│                                                            │
└──────────────────────────────────────────────────────────┘
  │
  ▼
┌─ chat_service.py: generate_response() ───────────────────┐
│                                                            │
│  + cultural context enrichment                              │
│  + memory context (vector search)                           │
│  + multimodal context                                       │
│  + grounded context                                         │
│  + knowledge pipeline (local data → ★ 可短路)                │
│                                                            │
│  → AngelaLLMService.generate_response_full()                │
│                                                            │
└──────────────────────────────────────────────────────────┘
  │
  ▼
┌─ router.py: generate_response_full() ────────────────────┐
│                                                            │
│  ★ 又做一次: template match → 可返回                        │
│  ★ 又做一次: 我加的 math regex → 可返回                     │
│  ★ 又做一次: ensemble → 可返回                               │
│  ★ 又做一次: memory retrieval → 可返回                       │
│  ★ 又做一次: knowledge lookup → 可返回                       │
│  ★ 又做一次: neural bridge → 可返回                          │
│  ★ 又做一次: QueryClassifier (又一次!) → question-like?     │
│       → fusion (unified + LLM)                              │
│       → active backend? → LLM generate                      │
│       → no backend? → fallback_response                     │
│                                                            │
│  _fallback_response:                                        │
│       → model bus → 我加的 math → 我加的 reflex map         │
│       → emotional support → honest fallback → NeuroBlender  │
│       → pure template                                       │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

## 二、重複職責分析

### 同一件事被做了 2-3 次的：

| 事情 | 在哪裡做 | 在哪裡又做了一遍 |
|------|---------|----------------|
| **意圖分類** | Step 1.5: MainlineDispatcher → QueryClassifier | Router: QueryClassifier (line ~1035) |
| **數學處理** | Step 3: IntentRegistry + MathVerifier | Router: 我加的 MathVerifier (line ~980) |
| **情感分析** | Step 4: _analyze_emotion_and_crisis | Router: emotional check in _fallback_response |
| **模板匹配** | Router: _try_template_match | Router: _fallback_response 的 reflex map |
| **知識查詢** | Step 3: KnowledgeBase + Step 6: ED3N | Router: _try_knowledge (又有一次) |

### 真正的問題：

**Router 重複了 Pipeline 的所有決策，但沒有接收 Pipeline 的上下文。**

Pipeline 已經知道了：
- `_dispatch_intent` = GENERATE
- `_math_result` = (已驗證的數學結果)
- `emotion` = (已分析的情緒)
- `intent_result` = (已路由的意圖)

但 Router 完全不知道這些，它從零開始又做了一遍分類。

## 三、我的 patch 造成的隱藏死代碼

| 我加的 patch | 位置 | 造成什麼死代碼 |
|-------------|------|-------------|
| **MathVerifier early-return** | router.py L980 | Pipeline Step 3 的 MathVerifier 結果（`_math_result`）被忽略——Pipeline 已經做完了但 Router 又做一遍 |
| **REFLEX_MAP** | router.py L1640 | ReflexSystem、TemplateLibrary、compose_response() 的 reflex 能力全部被繞過 |
| **honest fallback before NeuroBlender** | router.py L1607 | EmotionalSupport template 的 fallback 被移到更前面，intercepting 了原本該到 support template 的輸入 |

## 四、每個模組「能做什麼」vs「實際被叫來做什麼」

| 模組 | 能做什麼 | 實際被叫來做什麼 | 差距 |
|------|---------|----------------|------|
| **QueryClassifier** | 分類 10+ 種意圖 | Pipeline Step 1.5 用它 + Router 又用它 | 重複 |
| **IntentRegistry** | 意圖檢測 + 數學/文檔/學習路由 | Pipeline Step 3 用它 | ✅ 正確 |
| **MathVerifier** | 驗證數學表達式 | Pipeline Step 3 用它 + Router 又用它 | 重複 |
| **TemplateLibrary** | 根據情緒/場景選模板 | Router _try_template_match 用它 | ✅ 正確但被我的 reflex map 繞過 |
| **ReflexSystem** | 處理社交反射（謝謝、再見） | **幾乎沒被任何地方調用** | ⚠️ 被遺忘 |
| **EmotionSystem** | 情緒分析 + 行為調整 | Pipeline Step 4 用它 | ✅ 正確 |
| **KnowledgeBase** | 事實查詢 | Pipeline Step 3 + Router _try_knowledge | 重複 |
| **SemanticQA** | 語義問答 | Router _try_knowledge 用它 | ✅ 正確 |
| **NeuroBlender** | 情感碎片合成 | Router _fallback_response 用它 | ⚠️ 輸出是垃圾 |
| **MemoryIntegration** | 記憶檢索 + 存儲 | Router _try_memory_retrieval + ChatService | 重複 |
| **_build_chat_context** | 組裝完整上下文 | Pipeline Step 6 | ✅ 正確 |
| **prompt_builder** | 構造 LLM prompt | ChatService generate_response | ✅ 正確 |
| **PriorityNegotiator** | 8 投票者加權融合 | Router 內部用它 | ✅ 正確但上游決策被忽略 |

## 五、核心問題

### 問題 1：Pipeline 和 Router 之間沒有信息傳遞

Pipeline 做了 Step 1-9 的決策，但到 Step 10 調用 `chat_svc.generate_response()` 時，這些決策結果（intent、math_result、emotion、agent routing）只有部分在 context 裡。

Router 的 `generate_response_full()` 完全不知道 Pipeline 已經做了什麼，所以它從頭開始分類。

### 問題 2：Router 的 fallback chain 是補丁堆疊

`_fallback_response` 有 6 層：
```
Model Bus → Math → Reflex → Emotional Support → Honest Fallback → NeuroBlender → Pure Template
```

每一層都是因為前一層沒有處理某種輸入而加的。沒有統一的「誰該負責什麼」的設計。

### 問題 3：ReflexSystem 是孤兒

`core/life/tickle_reflex_system.py` 和 `core/life/reflex_manager.py` 存在但幾乎沒被 pipeline 調用。它們的能力（處理「謝謝」、「再見」等社交輸入）被 Router 的硬編 reflex map 取代了。

### 問題 4：Pipeline Step 3 的數學處理被 Router 完全忽略

Pipeline Step 3 已經：
1. 用 IntentRegistry 檢測數學
2. 用 MathVerifier 驗證
3. 確認後短路返回

但因為 IntentRegistry 有時不確認（conf < 0.1），結果注入到 `context["_math_result"]`。Router 的 `generate_response_full()` 根本不看 `context["_math_result"]`，而是自己再做一遍 MathVerifier。

## 六、正確的修復方向

### 不該做的：
- ❌ 在 Router 裡加更多硬編的 fallback 層
- ❌ 在 Router 裡重複 Pipeline 已經做過的分類
- ❌ 用 REFLEX_MAP 取代 ReflexSystem

### 該做的：
1. **Router 應該讀懂 Pipeline 的 context** — `context["_math_result"]`、`context["_dispatch_intent"]`、`context["emotion"]` 等都已經有了，Router 應該基於這些做決策，而不是自己重新分類
2. **Router 應該有一個明確的「pass-through」機制** — 如果 Pipeline 已經決定了這件事（比如數學已確認），Router 應該直接執行而不是重新判斷
3. **移除我的硬編 reflex map** — 讓 ReflexSystem 或 TemplateLibrary 來處理
4. **移除我的 Router math early-return** — Pipeline Step 3 已經做了
5. **讓 `_fallback_response` 變薄** — 它不應該有 6 層 fallback，只應該處理「Pipeline 和 Router 都無法處理」的最後手段
