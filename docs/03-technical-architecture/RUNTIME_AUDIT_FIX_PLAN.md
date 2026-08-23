# 執行期行為審計與修復計畫（RUNTIME_AUDIT_FIX_PLAN）

> 狀態：**已審計 · 修復中**
> 日期：2026-08-24
> 方法：**依代碼與實際運行驗證**，不採信 MD 宣稱。
> 離線模擬：無雲端金鑰、無 ollama、`deployment.mode=local`。

---

## 1. 訊息流實測地圖（一則訊息被誰處理、順序）

```
POST /chat/* 或 WS chat_message
 → chat_routes._handle_chat_request
   1. 驗證/截斷
   2. mainline_dispatcher 分類入隊
   3. 數學雙軌 (MathVerifier) — StateMatrix 更新
   4. 情緒分析 + 危機評估 + 注入 (emotional/lifecycle/intent/state)
   5. document_router 意圖（注入不攔截）
   6. _build_chat_context（ED3N 詞典檢索歷史 + DialogueContext）
   7. ExecutionGate: QueryClassifier → 自動執行/確認/拒絕
   8. AgentOrchestrator 自動路由（可能直接回答）
   9. causal 預測注入
  10. ChatService.generate_response:
      KnowledgePipeline 先行（math→weather→KB→dict→symbolic→HAM）命中即短路
      → AngelaLLMService:
         ModelBus 預匹配 → TemplateMatcher(>0.8 罐頭) → ensemble
         → HAM 模板 → knowledge_base → neural bridge(死) → active_backend(unified)
 11. 事後: 因果學習/意圖回饋/情緒迴饋 → 回應格式化+存 session
```

**重複處理**：同一訊息被分類 2-3 次（ExecutionGate / ModelBus / Agent）；兩套並行歷史儲存（session.messages vs WS `_session_history`）。

---

## 2. 離線智能實測評級（不用 LLM）

| 子系統 | 實測 | 評級 |
|---|---|---|
| 確定性數學/邏輯 | `123*456=56088` 正確 | ✅ works |
| curated KB / 語義 QA | Paris/Tokyo 正確 | ✅ works（規模小）|
| 詞典翻譯 | 「你好呀」→「你好 = hello」 | ⚠️ works 但**過度觸發** |
| TemplateMatcher 小說閒聊 | cat-singing → 音樂罐頭 conf 0.95 | ❌ broken-ish |
| HAM 記憶模板 | "Is Paris bigger than London?" → 法國首都快取 | ❌ self-poisoning |
| 統計核 boolean 層 | 開放問題 → "…please=true" 捏造 | ❌ fabrication |
| NeuroBlender | 情緒驅動片段合成（唯一離線情緒感知生成器）| ⚠️ 很少被到達 |

**關鍵斷線**：PriorityNegotiator 產出的 GenerationParams 被 UnifiedBackend **完全丟棄**；prompt_builder 的情緒/危機/因果上下文被 `_strip_wrapper` 剝光——8 個 voter 的調變在主離線路徑上**零效果**。

## 3. 自主性實測

| 系統 | 離線狀態 |
|---|---|
| MetabolicHeartbeat | ✅ 全活（代謝/CNS/健康投票）|
| DigitalLifeIntegrator | ✅ 三循環全活 |
| AutonomousLifeCycle | ⚠️ 活但**分裂腦**（Bug A）|
| ProactiveInteraction | ✅ 活（ED3N 反射+天氣源）|
| LLMDecisionLoop | ⚠️ 活但退化為規則 fallback（JSON 解析失敗）|

## 4. Bug 清單與修復分級

| # | Bug | 證據 | 級別 | 修法 |
|---|---|---|---|---|
| A | lifecycle 分裂腦：lifespan 與 DLI 各建一份，chat 讀到休眠份 | lifespan.py:353 vs dli.py:448 | HIGH | 統一走 shared factory |
| B | lifecycle save_state 無呼叫者→持久化死 | alc.py:1113 | HIGH | shutdown hook 接上 |
| C | DynamicThresholdManager 永不可達（INITIALIZING 直跳 AWAKENING）| dli.py:747 vs :457 | MED | initialize 中補呼叫 |
| D | 空訊息 → HTTP 500 | chat_routes.py:412 | HIGH | 改 400 + 友善訊息 |
| E | ≤10 字元一律當翻譯 → 問候被劫持 | knowledge_pipeline.py:292 | HIGH | 加意圖判別（非單詞/含問句特徵不譯）|
| F | warm-up race：KP 需 entry≥100 但 ED3N 背景載入 | chat_service.py:215 | MED | KP 未就緒時跳過 dict 路由 |
| G | boolean 層對任意問句捏造 "=true/false" | unified_engine.py:189 | HIGH | 只在偵測到命題結構時走 boolean |
| H | HAM 自毒：conf≥0.5 即存模板（含捏造答案）| router.py:1741 | HIGH | 拒絕存 route=statistical-core 且 conf<0.7；提供清除 |
| I | fallback 死層（ed3n/garden tier、neural bridge）| router.py:1266,1741 | MED | 移除死分支 |
| L/M | sessions get/set 競態、WS 雙歷史 | chat_routes.py:666 | LOW | 本次不動（併發重構另案）|

## 5. 修復後目標

- 已知事實→semantic-qa 自然句；未知→誠實拒答（不再捏造 =true）
- 不再被詞典劫持問候
- HAM 不再自毒
- lifecycle 單例 + 持久化活
- 離線智能誠實分級寫回 RESULTS.md
