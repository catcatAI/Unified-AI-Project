# Remaining Issues — Fix Plan

## Issue 1: Math Engine — "2 的 10 次方" → 12 (wrong, should be 1024)

**Root cause** (`math_verifier.py:193-221`):
- `add_ops` contains `"多"` which substring-matches `"多少"` → triggers `2+10`
- `"次方"` not recognized in `_parse_chinese_word_problem` — no power/exponent detection

**Fix** (`math_verifier.py`):
1. Add pow detection before add/subtract checks: `("次方", "次幂", "幂")` → `f"{a}**{b}"`
2. Remove `"多"` from `add_ops` (false positive with `"多少"`)
3. Add `"次方"` to `_contains_likely_math` keywords
4. Verified result: `2**10` → `1024` via engine

## Issue 2: Memory — User info not persisted ("我叫小明" lost next turn)

**Root cause** (4 gaps):
1. `_detect_learning_intent` only matches `["記住","學習","記錄","調整","理解","教我","記住這個"]` — `"我叫小明"` has none → falls to general handler
2. No structured extraction: regex `關於`-prefix only; stores raw blob `"Learning: 記住我叫小明"` 
3. Query uses current message text as keyword → can't match previous user info
4. No `UserProfile` data structure accumulates facts across turns

**Fix**:
1. Add intent triggers: `self-intro` keywords `("我是", "我叫", "我的", "最喜歡")`
2. Add `_handle_user_info_intent()` with regex extraction: `name=小明`, `favorite=獵戶座星雲`
3. Store structured items with `data_type="user_profile"`, indexed by `user_name`
4. On each turn, query for `user_profile` items of current user and inject into context

## Issue 3: Server uses NeuroBlender instead of Gemini (llm_mode: "auto")

**Root cause**: `AngelaLLMService` init defaults `llm_mode="auto"`.
- `conversation_with_angela.py` fixed this by setting `llm_mode: standard`
- HTTP server loads config from `multi_llm_config.json` which doesn't set `llm_mode`

**Fix**: Set `"llm_mode": "standard"` in `multi_llm_config.json` or add auto-detection that prefers available cloud LLM over NeuroBlender when Gemini key is present and API responds.

## Order of Execution

1. **Issue 1** (math engine) — surgical, low risk, high impact fix
2. **Issue 3** (server llm_mode) — single config change  
3. **Issue 2** (memory) — moderate complexity, structured profile system

## Verification

```bash
# Issue 1
curl -X POST http://127.0.0.1:8000/api/v1/angela/chat \
  -d '{"message":"幫我計算 2 的 10 次方是多少？"}' \
  -H "Content-Type: application/json"
# Expected: 1024, not 12

# Issue 3
# Same endpoint, response should come from Gemini (not NeuroBlender fragments)

# Issue 2
curl -X POST ... -d '{"message":"我叫小明，最喜歡獵戶座星雲"}'
curl -X POST ... -d '{"message":"你記得我叫什麼名字嗎？"}'
# Expected: "小明"
```
