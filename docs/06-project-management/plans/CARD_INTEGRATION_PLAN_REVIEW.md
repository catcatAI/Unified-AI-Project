# Card Integration Plan Review (2026-05-30)

**Date**: 2026-05-30  
**Method**: Proactive audit of `ANGELA_CARD_INTEGRATION_PLAN.md` before implementation  
**Total Issues Found**: 25 (6 HIGH, 12 MEDIUM, 7 LOW)

---

## HIGH — Must Fix Before Implementation

| # | Phase | Issue | Severity |
|---|-------|-------|----------|
| 0.1 | 0 | IntentRegistry never registered as service; learning loop writes to black hole | HIGH |
| 1.1 | 1 | Sync `pipeline.process()` called inside async method blocks event loop | HIGH |
| 1.2 | 1 | Fresh `IntentRegistry()` created per message — patterns never persist | HIGH |
| 2.1 | 2 | `asyncio.get_running_loop()` in sync method crashes in CLI mode | HIGH |
| 2.2 | 2 | Phase 2 makes Stage 3 async but never provides `async process()` | HIGH |
| 3.1 | 3 | `text[:50]` raw fragment as keyword — learning writes garbage | HIGH |
| 4.1 | 4 | `pipeline.process()` blocks event loop inside async TaskManager | HIGH |
| 4.2 | 4 | `datetime.utcnow()` deprecated in Python 3.12+ | HIGH |

## MEDIUM

| # | Phase | Issue | Severity |
|---|-------|-------|----------|
| 0.2 | 0 | CardRegistry registration fragmented across lifecycle stages | MEDIUM |
| 0.3 | 0 | CLI cards never registered with ServiceRegistry | MEDIUM |
| 1.3 | 1 | Race: local CardRegistry lost if pipeline fails | MEDIUM |
| 1.4 | 1 | `HAMMemoryManager()` created without config context | MEDIUM |
| 1.5 | 1 | Keyword-dependent detection misses variant phrasing | MEDIUM |
| 2.3 | 2 | LLMBridge redundantly calls `get_llm_service()` per conflict | MEDIUM |
| 2.4 | 2 | `generate_text("")` indistinguishable from LLM failure | MEDIUM |
| 3.2 | 3 | Learned patterns never feed back into IntentRegistry | MEDIUM |
| 3.3 | 3 | Hardcoded `latency_ms: 0` corrupts route learning stats | MEDIUM |
| 4.3 | 4 | Contradiction: lifespan.py vs wiring.py init location | MEDIUM |
| 4.4 | 4 | `/cards/import` has no auth, rate limiting, or size validation | MEDIUM |
| 4.5 | 4 | TaskProgress stuck "running" on early exceptions | MEDIUM |
| X.1 | All | Bare `except Exception: pass` silences errors; false success | MEDIUM |

## LOW

7 LOW issues — naming, timeout, redundant instances, orphan stats, Pydantic model, etc.

---

## ROOT CAUSE

8/8 HIGH issues trace to one architectural gap: **no central wiring infrastructure for module lifecycle**. Every phase manually creates instances, guesses at singletons, and hand-wires connections — exactly the same pattern that created the original coupling/router.py problems.
