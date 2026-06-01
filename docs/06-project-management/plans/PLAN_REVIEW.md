# Plan Review: `ANGELA_CARD_INTEGRATION_PLAN.md`

> **Review Date**: 2026-05-30
> **Methodology**: Every file:line claim verified against actual source code. Every factual assertion checked via grep, glob, and file reads.
> **Total Claims Checked**: 30+

---

## 1. Verified Correct

| # | Claim | Evidence |
|---|-------|----------|
| 1 | `MemoryAdapter` has 81 lines | `memory_adapter.py:81` — file ends at line 81 with `__all__` |
| 2 | `PersonalityAdapter` has 59 lines | `personality_adapter.py:59` — file ends at line 59 with `__all__` |
| 3 | `CardRegistry` has 203 lines | `card_store.py:203` — file ends at line 203 |
| 4 | `IntentRegistry` has 168 lines | `intent_registry.py:168` — file ends at line 168 |
| 5 | `ChatService._analyze_intent()` uses hardcoded keywords, not IntentRegistry | `chat_service.py:155-167` — all `any(kw in text_lower for kw in [...])` pattern, no IntentRegistry call |
| 6 | `ChatService` has only `llm_manage` and `file_op` intent branches at lines 122-127 | `chat_service.py:123-126` — only two branches (plus `learning` in _analyze_intent but no branch handler) |
| 7 | `CardRegistry` never registered in `ServiceRegistry` | Grep for `card_registry` in `core/interfaces/service_registry.py` — zero matches |
| 8 | `LLMFallback` uses hardcoded string concatenation, not real LLM | `llm_fallback.py:48-63` — all 4 `_resolve_*` methods return hardcoded `f"...{conflict.description}"` strings |
| 9 | `run_card_import.py` is standalone CLI at line 280 | `run_card_import.py:280-281`: `if __name__ == "__main__": main()` |
| 10 | No async task queue for card import | Grep `asyncio.create_task`, `asyncio.Queue`, `BackgroundTasks`, `Celery` in `core/card/` — zero matches |
| 11 | `LLMBridge` doesn't exist yet | `glob` for `core/card/resolver/llm_bridge.py` — no file found |
| 12 | `CardImportTask` doesn't exist yet | `glob` for `core/card/integration/card_import_task.py` — no file found |
| 13 | `card_import.py` API endpoint doesn't exist | `glob` for `api/v1/endpoints/card_import.py` — no file found |
| 14 | `MemoryAdapter.store_card()` calls `ham.store_experience()` | `memory_adapter.py:43`: `memory_id = await self.ham.store_experience(...)` |
| 15 | Pipeline thresholds: `RESOLUTION_THRESHOLD = 0.85`, `ANGELA_THRESHOLD = 0.70` | `pipeline_orchestrator.py:23-24` |
| 16 | Pipeline constructor only takes `registry` (no adapters) | `pipeline_orchestrator.py:46`: `def __init__(self, registry: Optional[CardRegistry] = None)` |
| 17 | `character_card` YAML intent has 6 keywords at lines 264-273 | `angela_core.yaml:264-273` — 6 keywords at lines 266-271 |
| 18 | `ConfigLoader.learn()` never called with card pipeline data | Grep `.learn(` across backend — only found in `neuro_auto_selector.py:428`, `router.py:1287,1291` (LLM routing), none from card pipeline |
| 19 | `IntentRegistry` not used by `ChatService` | Grep `IntentRegistry` in `services/` — zero matches |
| 20 | D9: `run_card_import.py` isolated from API | No `register`, no `include_router`, no lifespan hook; confirmed isolated |

---

## 2. Partially Correct

### 2.1 AngelaLLMService line count

**Plan says**: `AngelaLLMService (1731行)` in the ASCII diagram and elsewhere.

**Reality**: `angela_llm_service.py` is **40 lines** (a backward-compat re-export shim). The actual implementation lives in `services/llm/router.py` which has **1522 lines** (not 1731 either).

**Impact**: Low — the plan's structural analysis is correct even if the file attribution is wrong. The plan correctly references `router.py:710` and `router.py:1597` for `generate_response` and `generate_text`, which are correct line numbers in `services/llm/router.py`.

### 2.2 `ConfigLoader.learn()` line range

**Plan says** (D8): `config_loader.py:285-311` defines `learn()`.

**Reality**: `learn()` is at lines **285-311** (correct), but the handler methods extend from **313-378**. The plan's reference to `config_loader.py:313` for `intent_pattern` and `config_loader.py:348/365` for `route_success/route_fail` are correct for the private handlers but the D8 range claim (285-311) only covers the public method, not the handlers.

**Impact**: Low — the plan's understanding of `learn()` is correct.

### 2.3 `character_card` handler claim

**Plan says** (D4): `character_card` intent exists but no handler.

**Reality**: `angela_core.yaml:273` assigns handler `DocumentBuilder` to `character_card`. So a handler IS defined in YAML. The plan is correct, however, that ChatService has no handler branch for `character_card` — the YAML handler is irrelevant to ChatService's hardcoded intent dispatch.

**Impact**: Low — the practical problem (no ChatService branch) is correctly identified.

### 2.4 LLMFallback line range

**Plan says** (D7): `llm_fallback.py:39-63` are hardcoded resolve methods.

**Reality**: Lines 39-63 cover `_llm_resolve` (39-46) plus 4 resolve methods (48-63). This is essentially correct, though `_llm_resolve` wraps the dispatcher and resolves methods are 48-63. Total file is 66 lines.

**Impact**: Negligible.

---

## 3. WRONG — Claims That Contradict Actual Code

### 3.1 ⚠️ "PersonalityAdapter exists but never called"

**Plan says**: D2: `PersonalityAdapter` (59行) → 存在但無人呼叫.

**Reality**: **PersonalityAdapter IS called.** `roleplay_engine.py:10` imports it, and `roleplay_engine.py:22-23` instantiates it:
```python
class RoleplayEngine:
    def __init__(self, adapter: Optional[PersonalityAdapter] = None):
        self.adapter = adapter or PersonalityAdapter()  # <-- line 23
```

The `RoleplayEngine` is in `core/card/capabilities/roleplay_engine.py`. It is an existing caller.

**Severity**: **HIGH** — the plan's core premise that "adapters are never called" is false for PersonalityAdapter. The proposed Phase 1 code in the plan (which re-instantiates PersonalityAdapter) would create a second instance, which may be redundant or conflict with the existing RoleplayEngine usage.

### 3.2 ⚠️ "CardRegistry only used internally by pipeline._finalize()"

**Plan says**: D6: "CardRegistry (203行) → 僅 pipeline._finalize() 內部使用".

**Reality**: `CardRegistry` is also used directly by `run_card_import.py`:
- Line 149: `registry = CardRegistry()`
- Line 151: `registry.load(Path(args.load))`
- Line 167: `if is_reference and registry.get(key) is not None`
- Line 169: `registry.add(result.card)`
- Line 189: `registry.save(Path(args.save))`
- Lines 217-219: `registry = CardRegistry()`, `registry.load(Path(args.load))`
- Lines 240-242: `registry.save(Path(args.save))`

**Severity**: **MEDIUM** — the plan understates existing CardRegistry usage. The CLI runner already orchestrates registry lifecycle. This means the registry pattern is already validated; the plan could leverage this.

### 3.3 ⚠️ `api/router.py:167` vs actual `router.py`

**Plan appendix says**: `api/router.py:167 chat_completions()`.

**Reality**: `api/router.py:167` is `POST /chat/completions` — but the function is `chat_completions` defined at `api/router.py:168`, not line 167. The decorator `@router.post("/chat/completions")` is at line 167.

**Severity**: **LOW** — off by one line.

### 3.4 ⚠️ PipelineResult.stage type claim

**Plan section 1.3 says**: `PipelineResult.stage: "auto" | "angela" | "llm"`.

**Reality**: `pipeline_orchestrator.py:30` — the `stage` field is typed as `str`, not a Literal/triple-union. In practice, only "auto", "angela", "llm" are assigned, but the type system doesn't enforce this.

**Severity**: **LOW** — functionally correct, just a typing detail.

---

## 4. Insufficient Evidence

### 4.1 `IntentRegistry` hardcoded fallback is missing `character_card`

**Plan says**: `intent_registry.py:71-84` hardcoded fallback missing `character_card`.

**Reality**: The hardcoded fallback at `intent_registry.py:71-84` **already includes** `character_card` at line 79:
```python
IntentPattern("character_card", ["角色", "角色卡", "生成角色", "人物", "人物卡"], "character_card", priority=6),
```

The plan's Phase 1.2 proposes adding it at line 79, but it's already there. The plan failed to read this line before making the proposal.

**Severity**: **MEDIUM** — the proposed code change is a no-op (adding an already-existing entry). This should be caught in review.

### 4.2 Existing `asyncio.Queue` and background task infrastructure

**Plan says** (D10): "無異步任務隊列" (no async task queue).

**Reality**: While `core/card/` has none, the broader project has:
- `ai/integration/unified_control_center.py:50`: `self.task_queue = asyncio.Queue()`
- `core/feedback_processor.py:174`: `self._pending_feedback: asyncio.Queue = asyncio.Queue()`
- `api/routes/ops_routes.py:99`: Uses FastAPI `BackgroundTasks`
- `ai/memory/ham_memory/ham_background_tasks.py`: `HAMBackgroundTasks` class (used by `ham_manager.py:86`)

**Impact**: The plan correctly notes that the card import system lacks async task infrastructure. However, existing patterns could be reused rather than building from scratch.

### 4.3 `ConfigLoader` learned files existence

**Plan implies** `learned_patterns.yaml` exists and works.

**Reality**: `learned_patterns.yaml` exists and has real data. The `learn()` method writes to it. This is correct but the plan doesn't verify the actual YAML structure beyond existence.

---

## 5. Missing — Things the Plan Should Have Considered

### 5.1 `MemoryAdapter` IS exported from `__init__.py`

`core/card/integration/__init__.py:6` exports `MemoryAdapter` and `PersonalityAdapter` in `__all__`. The plan treats them as orphaned, but they're part of a designed subpackage API.

### 5.2 No discussion of `services/wiring.py`

The existing `services/wiring.py` is the cross-service DI injection point at startup. The plan proposes adding CardRegistry init to `lifespan.py` but doesn't mention `wiring.py` which is the **designated** place for service wiring. Adding to `lifespan.py` directly would bypass the wiring module.

### 5.3 `Lifespan.py` structure mismatch

The plan proposes adding CardRegistry init around line 191 of `lifespan.py`. However:
- `lifespan.py:168-228` is the entire `lifespan()` context manager
- Line 191 is inside the `for svc_name in _lc.get("services_to_preinit", [])` loop, after the BiologicalIntegrator try/except
- The "line 191" reference would put CardRegistry init inside the preinit loop's `except` block (line 192), which doesn't make sense

The plan's line references for lifespan modifications are based on an inaccurate mental model of the file.

### 5.4 Pipeline's `process()` is synchronous — async migration impact

The plan notes this as R1 risk but doesn't fully analyze the downstream impact:
- `run_card_import.py` calls `pipeline.process()` synchronously in non-async `_process_file()` 
- Changing to `async_process()` would require rewriting the CLI runner's `_process_file()` to `async def`
- The Phase 2 code proposes using `asyncio.run_coroutine_threadsafe()` with `None` loop — this is a bug pattern

### 5.5 `asyncio.run_coroutine_threadsafe(None, ...)` is invalid

Phase 2 code at line 297-303:
```python
asyncio.run_coroutine_threadsafe(
    self.ham_manager.query_core_memory(...),
    None,  # <-- BUG: None is not an event loop
)
```
Passing `None` as the loop argument is invalid. This would raise `TypeError` at runtime.

### 5.6 No test for the `pytest` commands in the validation section

The plan suggests running `pytest tests/core/test_intent_registry.py -v -k "character_card"` but:
- This test may not exist yet
- The plan doesn't verify test file existence

---

## 6. Action Items

### Required Fixes in the Plan

| # | Severity | Status | Fix |
|---|----------|--------|-----|
| A1 | **HIGH** | 🟡 Doc fix needed | Remove claim that "PersonalityAdapter is never called". Add note that `roleplay_engine.py:22-23` already instantiates it. The plan should discuss whether to reuse existing RoleplayEngine callers or create a new instance in ChatService. |
| A2 | **MEDIUM** | 🟡 Doc fix needed | Remove Phase 1.2 (adding `character_card` to `intent_registry.py:79`) — it already exists in the hardcoded fallback. |
| A3 | **MEDIUM** | ⬜ Code fix needed | Fix `asyncio.run_coroutine_threadsafe(None, ...)` bug in Phase 2 code. Must pass `asyncio.get_event_loop()` or the running loop. |
| A4 | **MEDIUM** | 🟡 Doc fix needed | Update lifespan modification plan to use `services/wiring.py` instead of directly patching `lifespan.py` at a misleading line reference. The actual location logic in lifespan.py is different from what the plan assumes. |
| A5 | **LOW** | 🟡 Doc fix needed | Correct file attribution: AngelaLLMService is 40 lines (shim); actual implementation is `services/llm/router.py:1522` lines. |
| A6 | **LOW** | 🟡 Doc fix needed | Update the line reference for `api/router.py:167` to `api/router.py:168` (function definition is one line after decorator). |
| A7 | **LOW** | 🟡 Doc fix needed | Consider existing `ham_background_tasks.py` as a reuse candidate instead of building CardImportTaskManager from scratch. |
| A8 | **LOW** | 🟡 Doc fix needed | Add note about `wiring.py` as the proper DI wiring point for CardRegistry, not just lifespan. |

### Suggested Improvements

| # | Suggestion |
|---|------------|
| S1 | Add Pulse check: verify that `roleplay_engine.py`'s existing `PersonalityAdapter` usage is compatible with the planned ChatService flow. |
| S2 | Add note about `process()` → `async_process()` migration: the CLI runner's `_process_file` helper is synchronous and wraps `pipeline.process()`. Async migration means both need updating. |
| S3 | Consider whether `CardImportTaskManager` should reuse the existing `asyncio.Queue` pattern from `unified_control_center.py` or `feedback_processor.py`. |
| S4 | The plan's threshold constants (`0.85`, `0.70`) are correctly identified from `pipeline_orchestrator.py:23-24`. No change needed. |
