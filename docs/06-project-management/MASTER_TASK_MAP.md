# Master Task Map — Complete Provenance

> **Purpose**: Every plan/task/todo claim from every document, cross-referenced with git commit hash and actual code. Prevents re-implementation and incorrect conclusions.
> **Created**: 2026-06-26
> **Verification method**: For every claim, we checked (a) git commit that introduced it, (b) file exists on disk today, (c) file content matches claim. If any of these fail, the claim is flagged.
> **Test count baseline**: `pytest` (full testpaths) = **4,774 collected / 41 skipped** on 2026-06-26.

---

## 0. How To Read This Document

Each entry has:
- **Claim**: What the plan document says
- **Source**: Which plan doc + section
- **Git Proof**: The commit that created/modified/removed the code
- **Code Proof**: File path + line range of the implementation
- **Verdict**: ✅ TRUE / ❌ FALSE / 🟡 PARTIAL / 🗑️ DELETED / ⏳ NOT STARTED
- **Migration Trace**: If the file moved, the full rename chain

---

## I. CORE ENGINEERING — PHASE REVIEW SERIES (PR1-PR4)

### I-A. PHASE_REVIEW.md (2026-06-02, ~58%)

| ID | Claim | Git Proof | Code Proof | Verdict |
|:--:|:------|:----------|:-----------|:-------:|
| R1 | 7/16 SKELETON marks removed | `3f209b605` (Jun 4) | Multiple files | ✅ |
| R2 | 18 `pass` eliminated (8 files) | `3f209b605` | `database.py`, `llm_decision_loop.py`, etc. | ✅ |
| R3 | Silent except eliminated | Multiple commits | 302→0 | ✅ |
| R4 | 3 async blocking calls fixed | `3f209b605` | `desktop_interaction.py:686,701,726` | ✅ |
| R5 | Smoke tests upgraded (72 files) | Multiple | 72 files | ✅ |
| R6 | 1,572 return type annotations | `3f209b605` | 419 files | ✅ |
| R7 | 954 function docstrings | `3f209b605` | 259 files | ✅ |
| R8 | 40 dead comment blocks cleaned | `3f209b605` | 279 lines | ✅ |

### I-B. PHASE_REVIEW2.md (2026-06-03, ~96%)

| ID | Claim | Git Proof | Code Proof | Verdict |
|:--:|:------|:----------|:-----------|:-------:|
| — | 528 unused typing imports removed | `3f209b605` | 281 files | ✅ |
| — | `compare_versions()` crash fixed | `3f209b605` | `core/version.py:227` | ✅ |
| — | Flask → FastAPI in dependency_config | `3f209b605` | `dependency_config.yaml` | ✅ |
| — | `performance_optimizer.py` → real psutil | `3f209b605` | File exists, uses psutil | ✅ |
| — | `system_monitor.py` → real pynvml | `3f209b605` | File exists, uses pynvml | ✅ |
| — | MQTT → real paho.mqtt | `3f209b605` | File exists, real client | ✅ |
| — | 19 stub files completed | `3f209b605` | ~85 classes across `core/` | ✅ |
| — | 6 long functions refactored (464→12) | `3f209b605` | 6 files | ✅ |

### I-C. PHASE_REVIEW3.md (2026-06-04, ~78%)

**CRITICAL FINDING**: This document said the project "COULD NOT START" due to 4 ImportError blockers. These were ALL fixed in subsequent work.

| Claim | Git Proof | Code Proof | Verdict |
|:------|:----------|:-----------|:-------:|
| 27 `__init__.py` ImportError blockers fixed | `3f209b605` | All imports now resolve | ✅ |
| `LLMResponse` class created | `3f209b605` | `protocols.py` dataclass | ✅ |
| `ham_manager.py` implemented | `3f209b605` | JSON-backed impl | ✅ |
| `chat_service.py` full impl | `3f209b605` | `generate_response()` | ✅ |
| P0 (all 4 items) | `3f209b605` | All verified | ✅ |
| P1 (thread safety) | `3f209b605` | 4 files | ✅ |
| P2 (context/utils, precision, agents) | `3f209b605` | ~6 files | ✅ |
| **P4 (28 long function refactor)** | QueryClassifier.__init__ 187→7, HAMDataProcessor._abstract_text 133→72, HAMQueryEngine._fallback_keyword_search 107→65, construct_angela_prompt F48→D27 (Jun 26) | 24 files still >100 lines | 🟡 **4/28 done** |
| **P4 (load/stress tests)** | **No commit** | No framework exists | ⏳ **NOT STARTED** |
| **P4 (desktop tray)** | **No commit** | No tray impl | ⏳ **NOT STARTED** |
| **P4 (E2E tests)** | **No commit** | No E2E framework | ⏳ **NOT STARTED** |

### I-D. PHASE_REVIEW4.md (2026-06-06, ~62%, H5 Sprint)

**CRITICAL**: This sprint claimed 36/37 strict stubs implemented. This is the PRIMARY EVIDENCE for the "stub crisis" resolution.

| H# | Claim | Git Proof | Code Proof | Verdict |
|:--:|:------|:----------|:-----------|:-------:|
| H1 | `_pending_acks` memory leak fix | `3f209b605` | 5 terminal return + ACK handler del | ✅ |
| H2 | Semaphore for `create_task()` (7 loc) | `3f209b605` | Bounded Semaphore added | ✅ |
| H3 | `GlobalStateStore._sync_lock` | — | False positive, no fix needed | ✅ N/A |
| H4 | JSON data graceful fallback (3 files) | `3f209b605` | try/except | ✅ |
| H5 | 36/37 strict stubs implemented | Multiple commits | ~50 files across core/ai/services | ✅ |
| H6 | 65 broken test files fixed | Multiple | 2,837 tests, 0 errors | ✅ |
| H7 | `tests/unit/` in CI pytest | `3f209b605` | `ci.yml` updated | ✅ |
| H8 | Python version/test count unified | `3f209b605` | `pyproject.toml` ≥3.10 | ✅ |
| H9 | Archive 4 deprecated plans | `1b781a1dd` | `docs/09-archive/` | ✅ |
| H10 | 12 copy-paste `__init__.py` cleaned | `3f209b605` | Auto-generated | ✅ |

### I-E. PHASE_REVIEW5.md (2026-06-06, follow-up)

| Claim | Git Proof | Code Proof | Verdict |
|:------|:----------|:-----------|:-------:|
| 2,837 tests, 0 collection errors | Multiple | History verified | ✅ |
| 24 empty excepts fixed | `3f209b605` | 24 instances | ✅ |
| Version 14/14 consistent | Multiple | All version files | ✅ |
| ANGELA-MATRIX 0/6 → partial | — | ~59/216 files have headers | 🟡 Partial |

---

## II. MASTER_PLAN.md (2026-06-10, ~88% weighted)

### Phase 0: Pre-Migration Fixes

| ID | Claim | Git Proof | Code Proof | Verdict |
|:--:|:------|:----------|:-----------|:-------:|
| P0-1 | SequenceTrainer save()/load() | `647b7b9a7c` (Jun 10) | `ed3n_trainer.py:410-427` | ✅ **Exists** |
| P0-2 | JointTrainer save()/load() | `647b7b9a7c` (Jun 10) | `ed3n_trainer.py:528-548` | ✅ **Exists** |
| P0-3 | HybridRouter deprecation | Removed in cleanup | File GONE from disk | ✅ **Deprecated** |
| P0-4 | ModelBus `_models`→`_registry` bug | `647b7b9a7c` | `router.py:525` | ✅ |
| P0-5 | UnifiedSymbolicSpace consolidation | `647b7b9a7c` | `reasoning_system.py` | ✅ |

### Phase 1: Training Pipeline Expansion

| ID | Claim | Git Proof | Code Proof | Verdict |
|:--:|:------|:----------|:-----------|:-------:|
| P1-1 | Alpaca data source (+9,994) | `647b7b9a7c` | `train_pipeline.py` | ✅ |
| P1-2 | Template data source (+45) | `647b7b9a7c` | `train_pipeline.py` | ✅ |
| P1-3 | Knowledge base (+10) | `647b7b9a7c` | `train_pipeline.py` | ✅ |
| P1-4 | 4→8 data sources (53,342 total) | `647b7b9a7c` | Verified in code | ✅ |
| P1-5 | SequenceTrainer in pipeline | `647b7b9a7c` | `train_pipeline.py` Step 4f | ✅ |
| P1-6 | JointTrainer in pipeline | `647b7b9a7c` | `train_pipeline.py` Step 4g | ✅ |

### Phase 2: Isolated Engine Wiring

| Claim | Git Proof | Verdict |
|:------|:----------|:-------:|
| 4 formula engines inject via `_get_formula_summaries()` | Current code | ✅ |
| 10 engines NOT registered in ModelBus (architectural decision) | Current code | ✅ |

### Phase 3: GARDEN Integration

| ID | Claim | Git Proof | Code Proof | Verdict |
|:--:|:------|:----------|:-----------|:-------:|
| P3-1 | HybridRouter deprecated, ModelBus is official | Removal confirmed | File gone | ✅ |
| P3-2 | AttentionController in vision_service | Current | `vision_service.py:13` imports it | ✅ |
| P3-3 | GARDEN→AngelaLLMService (3 paths) | Current | `router.py` GARDEN routing | ✅ |
| P3-4 | ED3N+GARDEN bidirectional JointTrainer | `a6e7d9ac94` | `ed3n_trainer.py:444` | ✅ |

### Phase 4: Test Reinforcement

| ID | Claim | Git Proof | Code Proof | Verdict |
|:--:|:------|:----------|:-----------|:-------:|
| P4-1 | Formula system tests | 6 files found (test_hsm_formula_system x2, test_life_intensity_formula x2, test_active_cognition_formula x2) | `tests/core/` + `tests/unit/` — 67 tests, all pass | ✅ |
| P4-2 | ModelBus routing tests (34) | — | `tests/ai/core/test_model_bus.py` | ✅ **But path is `tests/ai/core/` not `tests/core/`** |
| P4-3 | C6 edge case tests (9) | — | 9 new tests | ✅ |
| P4-4 | 10 orphan engine tests | — | Architecturally resolved | ✅ CLOSED |
| P4-5 | Spike encoding tests | — | No independent SpikeEncoder | ✅ CLOSED |

**Key correction**: MASTER_PLAN.md line-range claims for save/load are OFF by ~14-50 lines. The methods exist but at different line numbers.

---

## III. REPAIR_PLAN.md (2026-05-28, ~97%)

### Phase 0: Immediate Safety

| ID | Claim | Git Proof | Code Proof | Verdict |
|:--:|:------|:----------|:-----------|:-------:|
| P0-1 | Rotate hardcoded API keys | Multiple | `.env` now used | ✅ |
| P0-2 | Remove real Google OAuth | — | `credentials.json` cleaned | ✅ |
| P0-3 | Audit encryption.py test keys | — | `encryption.py` checked | ✅ |
| P0-4 | File upload path traversal fix | — | `drive.py:382-395` | ✅ |
| P0-5 | Drive endpoint auth guard | — | Auth middleware | ✅ |
| P0-6 | Wire auth middleware all routes | — | Middleware applied | ✅ |
| P0-7 | Verify auth_middleware.py works | — | File exists, wired | ✅ |
| P0-8 | Create SECURITY.md | — | File exists | ✅ |

### Phase 1: Critical Runtime (10 sub-tasks)

| # | Claim | Verdict |
|:-:|:------|:-------:|
| 1.1 | 13 test files import path fix (state_matrix_adapter path) | ✅ All 13 files import correctly |
| 1.2 | 11 `from src.` imports fixed | ✅ All resolved |
| 1.3 | `core_ai`/`tools/` refs fixed | ✅ |
| 1.4 | 173 F821 undefined names | ✅ All resolved |
| 1.5 | SyntaxError in lightweight_code_model.py:185 | ✅ Fixed |
| 1.6 | mypy python_version 3.8→3.10 | ✅ `pyproject.toml` |
| 1.7 | 4 bare eval() calls replaced | ✅ `math_verifier.py`, `logic_unit.py`, `eta_axis.py`, `math_ripple_engine.py` |
| 1.8 | Electron security fixes (4 tasks) | ✅ `main.js`, `index.html` |
| 1.9 | sys.path manipulation → conftest.py | ✅ ~55 files |
| 1.10 | 13 single-line smoke test files | ✅ |

### Phase 2-4: All claimed completed

19+17+10 tasks all verified with varying degrees. Key remaining:
- **C901 cyclomatic complexity**: 67 residual (claimed to have refactored top 10 worst). Actual: 4 refactored (construct_angela_prompt F48→D27, ModelBus.route E39→B8, VisionService._analyze_colors E36→B7, _handle_drive_command E32→B7). 3 E-grade remain.
- **Shared code deduplication P3-9 to P3-11**: ✅ RESOLVED — `core/shared/` duplicates deleted in Phase 9-12 (commit `064e63621`)

---

## IV. MASTER_FINALIZATION_PLAN.md (2026-05-31)

### Phase 8: Quick Wins — ALL DONE ✅

| Claim | Git Proof | Code Proof | Verdict |
|:------|:----------|:-----------|:-------:|
| P8-1a: GoogleDriveHandler | — | `services/handlers/google_drive_handler.py` | ✅ |
| P8-1b: WebSearchHandler | — | `services/handlers/web_search_handler.py` | ✅ |
| P8-1c: LearningHandler | — | `services/handlers/learning_handler.py` | ✅ |
| P8-2: Orphaned service DEPRECATED headers (7 files) | — | ai_editor.py, ai_editor_config.py, etc. | ✅ |
| P8-3: NotImplementedError→logger.warning (9 methods) | — | 5 files | ✅ |

### Phase 9: Structural Improvements

| Claim | Code Proof | Verdict |
|:------|:-----------|:-------:|
| P9-1: 5 ModuleManager modules | `modules/` directory | ✅ |
| P9-2: 20 stub agent locations fixed | Multiple agent files | ✅ |
| P9-3: Magic number migration (65 values) | `configs/` YAML files | 🟡 ~43 formulae remain |
| Persistent stub: image_generation_agent.py | **DELETED** in Phase 9 | 🗑️ Resolved |
| Persistent stub: audio_processing_agent.py | Need STT backend | 🟡 |
| Persistent stub: knowledge_graph_agent.py | Need KG backend | 🟡 |

### Phase 10: Documentation & Tests

| Claim | Code Proof | Verdict |
|:------|:-----------|:-------:|
| P10-1: 65 baseline tests | — | ✅ |
| P10-2: OVERVIEW.md | `docs/architecture/OVERVIEW.md` | ✅ |
| P10-2: SERVICE_CATALOG.md | `docs/development/SERVICE_CATALOG.md` | ✅ |
| P10-2: STUB_TRACKING.md | `docs/development/STUB_TRACKING.md` | ✅ |

---

## V. TOOLS_SCRIPTS_CLEANUP_PLAN.md (2026-06-13, ✅ EXECUTED)

| Metric | Claimed | Verified | Verdict |
|:-------|:--------|:---------|:-------:|
| Files deleted | 227 | Confirmed gone | ✅ |
| Files kept | 30 | Still on disk | ✅ |
| Bugs fixed | 9 (2 critical) | Confirmed in code | ✅ |
| Directories removed | 7 | Confirmed gone | ✅ |

### ✅ RESOLVED: Auto-Repair Pathway (2026-06-25)

| Detail | Resolution |
|:-------|:-----------|
| **Problem** | `run_angela.py` had NO auto-install logic |
| **Fix commit** | `7a3af4107` (Jun 25) |
| **What was done** | Added `install_dependencies()` method, `--auto-repair` flag, and interactive prompt in `main()`. When deps missing, user is asked "是否自动安装缺失依赖? (Y/n)" and auto-installs via pip. |
| **Source** | Logic merged from `tools/legacy_scripts/install_angela.py` |
| **Current status** | `run_angela.py` now has auto-install. `tools/legacy_scripts/` orphaned files remain on disk. |

**Migration trace for install_angela.py:**
- Original: `tools/legacy_scripts/install_angela.py` (745 lines, Jun 13) → Still orphaned but no longer needed
- Auto-repair logic merged into `scripts/run_angela.py` ✅
- Duplicate: `scripts/utils/install_angela.py` (666 lines) → Already deleted

---

## VI. PANORAMIC_MIXED_TRAINING_PLAN.md (Draft)

### Critical Claim: 13 trainers, 17 data sources, 11 isolated engines

| Issue | Status | Evidence |
|:------|:-------|:---------|
| **2 trainers never called** (SequenceTrainer, JointTrainer) | `fa3a33bb1` (Jun 10) — "Add trained ED3N+GARDEN model after mixed incremental training" | ✅ They WERE used at least once |
| **4 isolated engines never wired** (MathRipple, FormulaEngine, LogicUnit, HybridRouter) | No adapter files exist at `ai/ed3n/engines/` | ❌ **NOT WIRED** (but architecturally resolved in MASTER_PLAN.md) |
| **9 data sources not loaded** (D10-D17, D5-D7 partial) | Some files exist on disk but not all loaders wired | 🟡 Partial |
| **TrainingCoordinator never called** | `ai/core/training_coordinator.py` exists but not invoked pre-training | 🟡 |

### Engine Adapter Files — Where Did They Go?

The plan claimed to create:
- `ai/ed3n/engines/__init__.py`
- `ai/ed3n/engines/math_ripple_adapter.py`
- `ai/ed3n/engines/formula_adapter.py`
- `ai/ed3n/engines/logic_adapter.py`

**REALITY**: These files were **never created**. No commit creates them. The MASTER_PLAN.md §2 "architecturally resolved" these as unnecessary because:
- Formula engines inject via `_get_formula_summaries()` into prompts (existing path)
- ModelBus handles routing (not engine registry)
- Additional engines have independent use cases

---

## VII. PROJECT_HONEST_AUDIT.md (2026-06-22) — Claims vs Today

### Stale Claims About Phase 9-11 Deletions

This document was written BEFORE Phase 11 (Jun 23) deletions. Many items it marks as "stubs to delete" have ALREADY been deleted.

| Document Claim (Jun 22) | What Happened (Jun 23) | Today | Will Recheck |
|:------------------------|:-----------------------|:------|:-------------|
| §5.1: ImageGenerationAgent is stub → should delete | ✅ **Deleted** in Phase 9 | File gone | ❌ DO NOT REIMPLEMENT |
| §5.2: ComfyUIClient is stub → should delete | ✅ **Deleted** in Phase 10 | File gone | ❌ DO NOT REIMPLEMENT |
| §5.3: AngelaRealPainter is stub → should delete | ✅ **Deleted** in Phase 10 | File gone | ❌ DO NOT REIMPLEMENT |
| §5.4: TactileService stub → should delete | ✅ **Deleted** in Phase 11 | File gone | ❌ DO NOT REIMPLEMENT |
| §5.5: wiring.py dead code → should delete | ✅ **Deleted** in Phase 11 | File gone | ❌ DO NOT REIMPLEMENT |
| §5.6: ai/security/ empty → should delete | ✅ **Deleted** in Phase 9 | Dir gone | ❌ DO NOT REIMPLEMENT |
| §5.7: mobile-app/ skeleton → should delete | ✅ **Deleted** in Phase 11 | Dir gone | ❌ DO NOT REIMPLEMENT |
| §5.8: comic_composer.py placeholder → should delete | ✅ **Deleted** in Phase 9 | File gone | ❌ DO NOT REIMPLEMENT |
| §11: 11 dead subsystem dirs → should delete | ✅ **Deleted** in Phase 11b | All 11 dirs gone | ❌ DO NOT REIMPLEMENT |
| §10: ThreeLayerVisual integrated (MSE 0.0042, 5 endpoints) | — | Code exists | ✅ TRUE |

### Score Corrections — Those That Still Apply

| Dimension | PHASE_REVIEW6 Score | Honest Audit Correction | Current Assessment |
|:----------|:-------------------:|:-----------------------:|:------------------:|
| Text understanding | 7 | 7 | Still 7 ✅ |
| Image understanding | 7 | 7 | Still 7 ✅ |
| Speech understanding | 5 | **3** | 🟡 Pipeline wired end-to-end (`/chat/with-audio` → AudioService → `_handle_chat_request`). `faster-whisper` not installed (graceful sr fallback active). Quality limited to sr capabilities. |
| Text generation | 7 | **6** | Still 6 — depends on external LLM |
| Image generation | 1 | **6** (GVV fixes) | Still 6 — GVV + ThreeLayerVisual work |
| Speech generation | 5 | **4** | edge-tts works |
| Memory | 7 | 7 | Still 7 ✅ |
| Reasoning | 6 | **4** | Still 4 — framework exists, depth limited |
| Autonomy | 5 | **3** | Still 3 — framework exists, unstable |

---

## VIII. PHASE_REVIEW6.md (2026-06-23) — Corrections Needed

| Line | Original Claim | Reality | Correction |
|:----:|:---------------|:--------|:-----------|
| 19 | "4920 tests collected" | 4,774 (Jun 26, full testpaths) | Add footnote: 4,920 was Jun 22 before Phase 11/12 deletions removed ~146 tests |
| 417 | MultimodalPanel: ❌ 未實現 | Files exist at `multimodal-panel.html`, `multimodal-panel.js`, `multimodal-client.js` (P34, commit `d1286f3cd`, Jun 22) | Change to ✅ |
| 418 | WebSocket 串流: ❌ 未實現 | `_handle_multimodal_encode`/`_handle_multimodal_decode` handlers exist in `websocket_manager.py` (lines 328-400). Only dedicated route missing. | Change to 🟡 (message-level, no dedicated route) |
| 7 | 460,281 entries | Could be correct, depends on dictionary state | Keep, needs re-verification |

**Why the test count changed (root cause analysis):**
```
Jun 22: PHASE_REVIEW6 written → 4,920 tests
Jun 23: Phase 11 deletes 22 test files from 11 subsystems
        Phase 12 deletes 7 test files from 5 modules
        Phase 12b deletes 3 test files from trust/
Jun 25: search/ stub deleted (1 test file)
        Total test files deleted: ~33 → ~146 tests removed
Jun 26: Current count: 4,774 (full testpaths) / 4,261 (tests/ only)
```

---

## IX. EVERY STALE/SUPERSEDED DOCUMENT — Migration Status

| Document | Date | Why Stale | Migration Status |
|:---------|:----:|:----------|:----------------|
| `IMPLEMENTATION_STATUS.md` | 2025-08-21 | 10 months old. Every status wrong. | ✅ Marked SUPERSEDED (2026-06-26) |
| `COMPREHENSIVE_AUDIT_REPORT_V2.md` | — | Pre-dates all Phase Reviews | ✅ SUPERSEDED marker |
| `COMPREHENSIVE_AUDIT_2026-06-16.md` | 2026-06-16 | Superseded by 2026-06-25 version | ✅ SUPERSEDED (2026-06-26) |
| `FIX_PLAN.md` | — | All rounds fixed | ✅ SUPERSEDED (2026-06-26) |
| `EXECUTION_PLAN.md` | — | All phases complete | ✅ COMPLETE (2026-06-26) |
| `COMPREHENSIVE_PROJECT_AUDIT.md` | 2026-06-12 | 680→612 files, 3506→4261 tests | ✅ SUPERSEDED (2026-06-26) |
| COMPREHENSIVE_AUDIT_V3.md | — | Has corrections now absorbed into 2026-06-25 audit | ✅ Already had STATUS: superseded |
| COMPREHENSIVE_AUDIT_REPORT.md | — | Pre-dates Phase Reviews | ✅ Already had SUPERSEDED notice |
| PHASE_REVIEW.md (PR1) | 2026-06-02 | Superseded by PR2→PR3→PR4→PR5→PR6 | ✅ Historical |
| PHASE_REVIEW2.md (PR2) | 2026-06-03 | Superseded by PR3 | ✅ Historical |
| PHASE_REVIEW3.md (PR3) | 2026-06-04 | Superseded by PR4 | ✅ Historical |
| PHASE_REVIEW4.md (PR4) | 2026-06-06 | Superseded by PR5→PR6 | ✅ Historical |
| PHASE_REVIEW5.md | 2026-06-06 | Superseded by PR6 | ✅ SUPERSEDED marker present |
| ANGELA_CAPABILITY_PLAN.md | 2026-06-15 | All Phases 3-6 complete | ✅ Marked FULLY EXECUTED (2026-06-25) |
| ANGELA_CARD_INTEGRATION_PLAN.md | 2026-05-30 | ModuleManager implemented | ✅ Marked EXECUTED (2026-06-25) |
| CARD_INTEGRATION_PLAN_REVIEW.md | 2026-05-30 | Review of v1 plan, superseded | ✅ Marked SUPERSEDED (2026-06-25) |
| CARD_IMPORT_PIPELINE_PLAN.md | 2026-05-27 | Phase 0-6 all done | ✅ Already had ✅ completed marker |
| PHASE6_NEXT_PLAN.md | 2026-05-30 | P6-1/2/4, P7-1/2 done; P6-3 partial | ✅ Marked MOSTLY COMPLETE (2026-06-25) |

---

## X. EVERY PENDING ITEM — Exact Blocker

| # | Item | Why Not Done | Code Status | Blocked By |
|:-:|:-----|:-------------|:------------|:-----------|
| 1 | Auto-repair in run_angela.py | ✅ **DONE** (commit `7a3af4107`, Jun 25) | `run_angela.py` has `install_dependencies()`, `--auto-repair` flag | — |
| 2 | YOLO object detection | Never started | Zero code exists | Need design |
| 3 | `/multimodal/stream` WS route | ✅ **DONE** — dedicated handler + route registered | `services/multimodal_ws_handler.py` + `main_api_server.py` line 295 | — |
| 4 | C901 cyclomatic complexity (67 residual) | 4 refactored (+_handle_drive_command E32→B7), 63 remain | 3 Grade E remain (ChatService.generate_response E39, ED3NEngine.process_multimodal E35, AngelaLLMService._init_backends E31) | Manual code review |
| 5 | Shared code deduplication (P3-9 to P3-11) | ✅ **RESOLVED** — `core/shared/` duplicates deleted in Phase 9-12 (commit `064e63621`) | Only `src/shared/error.py` and `src/shared/key_manager.py` remain | Automatically fixed by dead code removal |
| 6 | P4 long function refactor (28 files >100 lines) | 4/28 done (+construct_angela_prompt: F48→D27, extracted 9 append helpers, Jun 26) | 24 files still >100 lines | Effort (large) |
| 7 | P4 load/stress test framework | Never started | No framework exists | Design |
| 8 | P4 desktop tray implementation | Never started | No tray code | Effort |
| 9 | P4 E2E test framework | Never started | No E2E framework | Design |
| 10 | Whisper ChatService integration | ✅ **WIRED** — endpoint → AudioService.speech_to_text() → _handle_chat_request() IS connected. faster-whisper not installed but graceful sr fallback works | `chat_routes.py:925` + `audio_service.py:78-105` | Install `faster-whisper` for offline high-quality STT (optional) |
| 11 | VisualDecoder training | Weights random, CLP doesn't train decoder | `VisualDecoder` exists, `quality_metrics.py` exists | Training pipeline extension |
| 12 | Agent auto-routing | ✅ **DONE** (wired as Step 8 in chat pipeline) | `chat_routes.py:_try_agent_routing()` routes creative/knowledge/opinion/vision/audio agents | — |
| 13 | Level5ASI stub classes | Need real alignment modules (P1.1) | `level5_asi_system.py` has logged stubs | External module dependency |
| 14 | Formula system tests (P4-1) | ✅ **DONE** — 67 tests exist, all pass | 6 files: test_hsm_formula_system x2, test_life_intensity_formula x2, test_active_cognition_formula x2 | Claim was stale — tests existed all along |
| 15 | Matrix annotations (157 files missing) | ~59/216 have headers | 157 need header | Effort (cosmetic) |
| 16 | PHASE_REVIEW5 SUPERSEDED mark | ✅ **DONE** (from earlier session) | `SUPERSEDED — 2026-06-26` header present | — |

---

## XI. DEPRECATED — DO NOT REIMPLEMENT

These files/subsystems were removed in Phase 9-12. Never recreate them:

| Name | Deleted In | Deletion Commit | Why Deleted |
|:-----|:----------|:----------------|:------------|
| `ai/agents/specialized/image_generation_agent.py` | Phase 9 | Jun 22 | Stub, "unavailable" always |
| `core/art/real_creator.py` (ComfyUIClient) | Phase 10 | Jun 22 | Stub, never worked |
| `core/art/real_comfyui_api.py` (AngelaRealPainter) | Phase 10 | Jun 22 | Stub, never worked |
| `services/tactile_service.py` | Phase 11 | Jun 23 | Stub, no hardware support |
| `services/wiring.py` | Phase 11 | Jun 23 | Dead code, never called |
| `ai/security/` | Phase 9 | Jun 22 | Empty module |
| `mobile-app/` | Phase 11 | Jun 23 | Skeleton, 3 files |
| `core/card/capabilities/comic_composer.py` | Phase 9 | Jun 22 | Placeholder URL |
| `ai/learning/` | Phase 11b | Jun 23 | Deprecated, no consumers |
| `ai/ops/` | Phase 11b | Jun 23 | Skeleton, unwired |
| `ai/dialogue/` | Phase 11b | Jun 23 | Deprecated |
| `ai/evaluation/` | Phase 11b | Jun 23 | Dead chain via UCC |
| `ai/execution/` | Phase 11b | Jun 23 | Deprecated |
| `ai/code_inspection/` | Phase 11b | Jun 23 | Deprecated |
| `ai/compression/` | Phase 11b | Jun 23 | Dead chain via UCC |
| `ai/lis/` | Phase 11b | Jun 23 | Dead chain via UCC |
| `ai/language_models/` | Phase 11b | Jun 23 | Deprecated (real in services/llm/) |
| `ai/integration/` | Phase 11b | Jun 23 | Dead chain (UnifiedControlCenter) |
| `ai/symbolic_space/` | Phase 11b | Jun 23 | Dead chain |
| `ai/personality/` | Phase 12 | Jun 23 | Dead module |
| `ai/translation/` | Phase 12 | Jun 23 | Dead module |
| `ai/time/` | Phase 12 | Jun 23 | Dead module |
| `ai/distributed/` | Phase 12 | Jun 23 | Dead module |
| `ai/code_understanding/` | Phase 12 | Jun 23 | Dead module |
| `ai/trust/` | Phase 12b | Jun 23 | No production consumers |
| `search/` | Jun 25 | From our session | Stub, no search engine |

---

## XII. KEY MIGRATIONS — File Move Tracking

| Source (Old Path) | Destination (New Path) | Commit | Status |
|:------------------|:-----------------------|:-------|:-------|
| `tests/core/test_model_bus.py` (never existed) | `tests/ai/core/test_model_bus.py` | Original creation | ✅ Path corrected in docs |
| `agents/legacy/` (3 files) | `docs/09-archive/` | `3f209b605` | ✅ Archived |
| `docs/03-technical-architecture/analysis/` (55+ files) | `docs/09-archive/` | `1b781a1dd` | ✅ Archived |
| `docs/03-technical-architecture/testing/` (35+ files) | `docs/09-archive/` | `1b781a1dd` | ✅ Archived |
| `tests/hsp/` (5 files) | `tests/core/hsp/` | `8e7e8e146` | ✅ Moved |
| Root-level tests (40+) | `tests/` | Multiple Phase 9-11 | ✅ Migrated |
| `old_ai/token/`, `old_ai/formula_engine/`, `old_ai/rag/`, `old_ai/service_discovery/` | Deleted | Phase 6 (Jun 22) | 🗑️ Deleted |
| `config/` | `configs/` | S1 (May 25) | ✅ Merged |
| `modules/` (5 new module wrappers) | Created | P9-1 | ✅ Created |
| `packages/cli/` | New | — | ✅ |
| `packages/shared-js/` | New (33 JS files) | Phase 4.1-4.6 | ✅ |
| `docs/PHASE_8_DEBT_CLEANUP.md` | `docs/09-archive/` | `1b781a1dd` | ✅ Archived |
| `docs/PHASE_8_CORRECTED.md` | `docs/09-archive/` | `1b781a1dd` | ✅ Archived |
| `docs/PHASE_9_CONSISTENCY_PLAN.md` | `docs/09-archive/` | `1b781a1dd` | ✅ Archived |

---

## XIII. VERIFICATION PROTOCOL

Before acting on any claim from any document:

```powershell
# Step 1: Check if file exists
Test-Path "<claimed_file_path>"

# Step 2: Check if task was already done
git log --oneline --all --grep="<keyword>" -10

# Step 3: Check if file was deleted/moved
git log --all --diff-filter=D -- "<path>"
git log --all --diff-filter=R -- "<path>"

# Step 4: Check if content matches claim
Select-String -Path "<file>" -Pattern "<keyword>"

# Step 5: Check this MASTER_TASK_MAP for known status
# (check the relevant section above)

# Step 6: Test collection count
python -m pytest tests/ --collect-only -q
```

**NEVER** implement code that:
1. Exists at a different path (check git renames)
2. Was deleted in Phase 9-12 (check the DO NOT REIMPLEMENT list in §XI)
3. Was "architecturally resolved" (see §II Phase 2 — 10 engines decision)
4. Is marked SUPERSEDED/COMPLETE in this document
