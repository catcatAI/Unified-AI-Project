<!--
  =============================================================================
  FILE_HASH: GENERATED
  FILE_PATH: docs/DIALOGUE_PIPELINE_AUDIT_2026-08-16.md
  FILE_TYPE: documentation
  PURPOSE: 對話/推理管線深審計（2026-08-16）— ED3N 匹配、router fallback、auto-selector
  VERSION: 7.5.0-dev
  STATUS: active
  LANGUAGE: zh-TW
    LAST_MODIFIED: 2026-08-16
  AUDIENCE: developers, agents
  =============================================================================
-->

# 對話 / 推理管線深審計（2026-08-16）

> 本檔案記錄針對 **對話→LLM 路由→本地引擎推理** 鏈路的深審計發現。
> 多數問題是「跑測試抓不到、需實際呼叫或讀取產物才能暴露」的類型。
> 方法：2 路並行子代理（ED3N 引擎 / router 對話管線）逐檔讀碼 + 主代理 runtime 複核。

## 修復狀態（2026-08-16）

| # | 嚴重度 | 問題 | 狀態 |
|---|--------|------|------|
| A | CRITICAL | `knowledge_base.route_knowledge` substring 匹配 → pigeon→oink / education→meow 等錯誤答案 | ✅ 詞邊界修復 |
| B | CRITICAL | ED3N `ReflexLayer` substring 吞詞（helping→help、goodness→good） | ✅ 詞邊界修復 |
| C | HIGH | ED3N prompt 被 `<user_message>` wrapper 污染，破壞匹配 | ✅ ED3NBackend 剝 wrapper |
| D | HIGH | `_try_fallback_chain` 返回 error/empty response 不繼續 → 用戶收到空答案 | ✅ 檢查 error+empty，繼續 |
| E | HIGH | fallback 扁平化把 key 也加入 → 重試剛失敗的後端 | ✅ 只取 values |
| F | HIGH | Anthropic `check_health` 雙 `/v1` → 永遠 404 | ✅ 修正 URL |
| G | HIGH | `_select_cloud` break 條件錯 → Anthropic/Google 永不可選 | ✅ 改用 NEUROBLENDER 判斷 |
| H | HIGH | auto mode 非重入鎖自死鎖 | ✅ reentrancy 短路 |
| I | MEDIUM | 空 text 無 error 傳到用戶 | ✅ `_post_process_response` 視空為失敗 |
| J | MEDIUM | ED3N 訓練 grow 單字元 token（`len(t)>=1`） | ✅ ASCII `len>=3` |
| K | MEDIUM | ModelBus `_handle_knowledge` 只路由 garden（disabled）→ ED3N 不答知識 | ⏳ 設計意圖，GARDEN 重訓後啟用即可 |
| L | HIGH | ED3N `generate()`/StepDecoder 死碼（訓練權重白費） | ⏳ 需架構接線，風險高暫不改 |
| M | MEDIUM | ED3N 未接線方法（latent/SNN/multimodal surface） | ⏳ 未改（低風險表面） |
| N | HIGH | `PrecomputeService._tasks` 無界增長 + 無消費者（每對話 enqueue 永久累積） | ✅ LRU 上限（max_tasks=200） |
| O | LOW | `route_knowledge` 79 次獨立 regex → token-set 一次分詞 O(1) 查詢（217µs→10µs） | ✅ 拆步優化 |

---

## A. CRITICAL — `route_knowledge` substring 匹配產生錯誤答案

`apps/backend/src/ai/knowledge_base.py:297`：`if subject in t` 是**無詞邊界**的原始子字串匹配。
runtime 實證（修復前）：
```
'pigeon sound'   -> 'oink'   （匹配 "pig"）
'coward sound'   -> 'moo'    （匹配 "cow"）
'search color'   -> 'blue'   （匹配 "sea"）
'dogma sound'    -> 'woof'   （匹配 "dog"）
'birdie sound'   -> 'tweet'  （匹配 "bird"）
'education sound'-> 'meow'   （匹配 "cat"）
'weekend'        -> '7'      （匹配 "week"）
```
`route_knowledge` 被 `router.py _try_knowledge`（:903）在對話路徑使用 → 用戶查「pigeon」得到「oink」。

### 修復
- subject 匹配改用詞邊界 `(?<![a-z0-9]){subject}(?![a-z0-9])`；CJK aliases 保持 substring。
- `week`/`year` 天數規則改用 `\bweek\b`/`\byear\b`。
- 驗證：13 項測試全過（真實命中保留、假陽性全消除）。

## B. CRITICAL — ED3N `ReflexLayer` substring 吞詞

`ed3n_engine.py:59-64`：`if pattern in normalized` + `len(pattern)>=3` 就無條件返回，
不檢查詞邊界 → `helping/helpful/unhelpful` 全命中 `help` pattern，且它在 Stage 1（:395）
先於所有其它階段執行 → 覆蓋掉可能正確的回答。

### 修復
一律走 `_is_word_boundary_match`（已存在的正確邏輯），並把該函數從「只查第一個
`.find()` 出現」改為「掃描所有出現」（避免 `selfhelp` 內的 `help` 遮掉句子其它位置的
真實 `help`）。驗證：`help me`→help ✓、`helping/helpful/unhelpful`→None ✓。

## C. HIGH — ED3N prompt 被 `<user_message>` wrapper 污染

`prompt_builder.py:361` 給 LLM 後端包 `<user_message>…</user_message>`，但
`ED3NBackend.generate` 直接把含 wrapper 的 prompt 餵給 `process()` →
`encode('<user_message>hello</user_message>')` 把 tag 本身也編碼（含 m14 除/divide 鍵）→
匹配失效、decode 被 overlap guard 拒絕 → fallback。

### 修復（`ed3n.py`）
`ED3NBackend.generate` 剝離 `<user_message>…</user_message>` wrapper，只對用戶真實文字匹配。

## D+E. HIGH — `_try_fallback_chain` 兩缺陷

`router.py:1697` 原先 `return response` **無條件**，即使 `response.error` 或空 text——
後端「返回」error（不 raise）時鏈不繼續 → 用戶收到空答案。且扁平化把 dict keys 也加入
→ 第一個就是剛失敗的後端。

### 修復
- 扁平化只取 values（不重試剛失敗的後端）。
- 只在 `not response.error and text 非空` 時返回；否則 continue。
- 驗證：error→跳過、空→跳過、成功→選中（模擬 3 後端測試通過）。

## F. HIGH — Anthropic `check_health` 雙 `/v1`

`anthropic.py:44` 用 `{base_url}/v1/models`，而 `base_url` 已是
`https://api.anthropic.com/v1`（network_defaults.py:19 / llm.default.yaml:134）
→ `.../v1/v1/models` → 404 → health 永遠失敗，即使 API key 有效也無法選中。

### 修復
改 `{base_url}/models`（generate 用的 `/messages` 是正確的，只 health 壞）。

## G. HIGH — `_select_cloud` break 條件錯

`neuro_auto_selector.py:781` `if decision.backend != OLLAMA: break` 在 initial
`NEUROBLENDER` 下**第一次迴圈就 break** → 除非 openai 可用，Anthropic/Google 永不可選。

### 修復
改用 `decision.backend != NEUROBLENDER` 判斷「已找到匹配」才 break。

## H. HIGH — auto mode 非重入鎖自死鎖

`get_llm_service`（router.py:2078）`async with _llm_service_lock` 內 `await initialize()`
→ auto 模式 `_get_available_backends`（selector.py:827）再調 `get_llm_service()` → 重入
同一非重入 `asyncio.Lock` → 啟動死鎖。

### 修復
`get_llm_service` 開頭：`_llm_service is not None` 時直接返回（不重入鎖）。

## I. MEDIUM — 空 text 無 error 傳到用戶

`OllamaBackend.generate` 空 stream / `ED3NBackend.generate` 無匹配時返回
`text=""` 且**無 error flag**；`_post_process_response` 只查 `response.error` → 空答案直接給用戶。

### 修復
`_post_process_response` 把「空 text」視為失敗觸發 fallback。

## J. MEDIUM — ED3N 訓練 grow 單字元 token

`train_pipeline.py:1235` `len(t) >= 1` → 每個單字元（含 19 個單字母、每個數字、
`__`）grow 進 ED3N 字典（checkpoint 實證 212/258 條目含此類垃圾）。`preprocess`
（:88）把數字拆成單字元放大此問題。

### 修復
ASCII token 需 `len>=3`；CJK 單字保留（合法中文詞）。需重訓才清潔 checkpoint。

## K. MEDIUM — ModelBus `_handle_knowledge` 只路由 garden（disabled）

`model_bus.py:335` 知識查詢只 `_try_model("garden", ...)`，而 garden 未註冊（disabled）
→ 返回 "Model 'garden' not registered" → **ED3N 不參與知識查詢**。判定為**設計意圖**
（garden 是知識路由目標），GARDEN 重訓並啟用後自然修復，**不立即改**。

## L. HIGH — ED3N `generate()`/StepDecoder 死碼

`ed3n_engine.py:1169 generate()` → `StepDecoder.generate_text()`（step_decoder.py:136）
全庫無呼叫者；SequenceTrainer/JointTrainer 訓練的權重沒有實際被推理路徑使用。
真實路徑是 `process()` → `_process_unlocked()`（不走 StepDecoder）。
**屬「功能未接線」而非 bug**，接線是架構變更、風險高，暫不改，記入待辦。

## M. MEDIUM — ED3N 未接線公開方法

`process_snn()` / `process_multimodal()` / `enable_latent_space()` / `set_dual_encoder_router()`
/ `get_snn_stats()` / `load_presets_from_config()` 均無生產呼叫者。僅記錄。

## 結論與後續

- A-J + N + O 共 12 項已修復並通過測試；K/L/M 記錄待辦。
- **與 GARDEN 的對應關係**：A/B（substring 吞詞）與 GARDEN 的 prefix 誤合併是**同一類模式**——
  短 pattern 吞長詞。這是本次深審計反覆出現的根因類別。
- 既有環境事實（非本次引入）：`apps/backend/tests/` 的 14 個 pre-existing failures 與
  `llm_mode: standard`（auto 死鎖 H 在標準模式不觸發，屬潛在啟動風險）。

---

## 附錄：步數拆分 vs 合併的優化結論（2026-08-16）

針對「能否把大步拆成更多小步來加速」的系統性結論：

| 環節 | 現況 | 拆步會更快嗎？ | 結論 |
|------|------|---------------|------|
| 訓練 `_rebuild_index` | 每 batch(500) 全量 TF-IDF fit O(V·D) | ❌ 拆成增量 append 會讓 TF-IDF 全局統計偏差 → 匹配分數不準 | **不拆**（準確度邊界） |
| 訓練 Hebbian update | 已向量化 + batch 內去重 | ❌ 拆成更細子批次 → rebuild 更頻繁 → 更慢 | **不拆** |
| 匹配 Step 2 精確命中 | hash 查表 O(1) | — | 已最優 |
| 匹配 Step 3 prefix 桶 | 前 3 字元分桶 + 桶內掃描 | ⚠️ 污染桶大時可再分桶，但清潔後桶小無需 | 已近最優 |
| 匹配 Step 4/5 TF-IDF | BLAS matmul | ❌ 算法已到極限；唯一收益在消除污染（重訓） | **不拆** |
| 對話 6 步短路 | template→ensemble→memory→knowledge→neural→LLM | — | 每步 guard 已廉價；主成本在 LLM |
| 對話 knowledge 查表 | 79 次獨立 regex（217µs） | ✅ **token-set 一次分詞 + O(1) 查詢（10µs，-97%）** | **已拆步** |
| 對話記憶體 | `PrecomputeService._tasks` 無界 | ✅ LRU 上限（max_tasks=200） | **已修** |

**核心洞察**：這個 codebase 的「大步」多數是**算法已達極限**（向量化、分桶、batched matmul），
真正能拆的「步」是**資料結構層**的——把「N 次獨立小掃描」拆成「1 次預處理 + N 次 O(1) 查詢」
（token-set）或「1 次合併 regex」（union）。而**不能拆的**是會改變語義統計的（增量 TF-IDF）。
「拆更多步更快」的實際例子是 knowledge 查表（-97%）與記憶體上限（堵泄漏）；其餘已到優化極限。