# Master Task Map

> **Purpose**: Consolidated inventory of every plan/task/todo across all documents, cross-referenced with git history and actual code.
> **Created**: 2026-06-26
> **Rule**: NEVER re-implement what's already done. If this document says ✅, verify with git/code before acting.

---

## 1. Document Inventory — All Plan/Task/Todo Sources

| Document | Date | Type | Stale? | Notes |
|----------|------|------|--------|-------|
| `PHASE_REVIEW6.md` | 2026-06-23 | Roadmap + Status | 🟡 P30-P44 done | Claims 4,920 tests (actual 4,261). "下一步" items need verification. |
| `PROJECT_HONEST_AUDIT.md` | 2026-06-22 | Honest Assessment | 🟡 Some stale | §8 score corrections outdated (GVV API bugs fixed, ThreeLayerVisual integrated). §5 deletion plan mostly executed. |
| `TOOLS_SCRIPTS_CLEANUP_PLAN.md` | 2026-06-13 | Cleanup Plan | 🟡 Partial exec | 227 files deleted. But auto-repair gap NOT fixed, install_angela.py remains. |
| `MASTER_CONSOLIDATED_PLAN.md` | 2026-06-11 | Master Plan | ✅ Complete | All S/A/B/C tasks done. |
| `COMPREHENSIVE_AUDIT_2026-06-25.md` | 2026-06-25 | Audit | ✅ Current | §5 stub audit corrected last session. |
| `OMISSIONS_CHECKLIST.md` | 2026-06-26 | Gap Tracker | ✅ Current | v1.8.0. 33 skips verified. |
| `REPAIR_ROADMAP.md` | 2026-06-16 | Repair Plan | ✅ Complete | All 6 phases done, 0 remaining tasks. |
| `IMPLEMENTATION_STATUS.md` | **2025-08-21** | Status Report | ❌ Stale | 10 months old. Every status item is wrong. Needs SUPERSEDED mark. |
| `ANGELA_LLM_SNN_ARCHITECTURE_PLAN.md` | 2026-06-06 | Architecture | ✅ Complete | Phases 1-4 all done. |
| `ED3N_MATURITY_PLAN.md` | — | Maturity Plan | ✅ Complete | Tiers 1-3 done. |
| `COMPOSITIONAL_IMAGE_GENERATION_PLAN.md` | — | Image Gen | ✅ Complete | Phases 1-3 done (92 tests). |
| `TEST_RESTRUCTURE_PLAN.md` | — | Test Plan | ✅ Complete | Phases 1-13 done. |
| `QUERY_CLASSIFIER_ACTION_PLAN.md` | — | Classifier | ✅ Complete | v2 + ExecutionGate done. |
| `GARDEN_MODEL_PLAN.md` | — | GARDEN | ✅ Complete | 205 tests. |
| `PHASE_REVIEW.md` → `PHASE_REVIEW5.md` | 2026-06-06 | Historical | ✅ Historical | Superseded by PHASE_REVIEW6. |
| `COMPREHENSIVE_AUDIT_REPORT_V2.md` | — | Historical | ✅ SUPERSEDED | Marked in earlier session. |
| `COMPREHENSIVE_AUDIT_2026-06-16.md` | 2026-06-16 | Historical | ✅ SUPERSEDED | Marked in earlier session. |
| `FIX_PLAN.md` | — | Historical | ✅ SUPERSEDED | Marked in earlier session. |
| `EXECUTION_PLAN.md` | — | Historical | ✅ COMPLETE | Marked in earlier session. |
| `COMPREHENSIVE_PROJECT_AUDIT.md` | 2026-06-12 | Historical | ✅ SUPERSEDED | Marked this session. |
| `RECOMMENDATIONS.md` | — | Historical | ✅ Complete | All 3 items done. |
| `STUB_TRACKING.md` | — | Tracking | ✅ Current | 9 persistent stubs (external deps), all documented. |

---

## 2. Git History Cross-Reference — Every Claimed Completion

### 2.1 P30-P44 Multimodal Pipeline (PHASE_REVIEW6 §2)

| Phase | Claimed | Git Evidence | Code Evidence | Status |
|-------|---------|-------------|---------------|--------|
| P30 MultimodalService + WS | ✅ | `16f225040` (Jun 21) | `multimodal_service.py` 572 lines, `websocket_manager.py` WS handlers | ✅ Real |
| P31 VisualEncoder | ✅ | Part of P30 commit | `visual_encoder.py` 256-dim CNN | ✅ Real |
| P32 AudioSpectralEncoder | ✅ | Part of P30 commit | `audio_encoder_spectral.py` 128-dim | ✅ Real |
| P33 CrossModal attention | ✅ | Part of P30 commit | `shared_latent_space.py` | ✅ Real |
| P34 Desktop Multimodal UI | ✅ | **`d1286f3cd`** (Jun 22) | `multimodal-panel.html`, `multimodal-panel.js`, `multimodal-client.js` | ✅ **Files exist** (PHASE_REVIEW6 was WRONG to mark ❌) |
| P35-P44 | ✅ | Multiple commits | All code files verified | ✅ Real |

### 2.2 MultimodalPanel (PHASE_REVIEW6 §3.2 claimed ❌)

**CORRECTION**: PHASE_REVIEW6 line 417 said "❌ 未實現 — 文件聲稱有但實際未找到 `MultimodalPanel.js`". This is WRONG.

Git commit `d1286f3cd` (Jun 22) created:
- `apps/desktop-app/electron_app/multimodal-panel.html` — 468 lines (5 tabs)
- `apps/desktop-app/electron_app/js/multimodal-panel.js` — 464 lines
- `apps/desktop-app/electron_app/js/multimodal-client.js` — 170 lines (11 API methods)
- `tests/desktop/test_multimodal_panel.py` — 11 tests

All files exist on disk as of 2026-06-26. **PHASE_REVIEW6 §3.2 must be corrected.**

### 2.3 WebSocket Multimodal Streaming (PHASE_REVIEW6 §3.2 claimed ❌)

**CORRECTION**: PHASE_REVIEW6 line 418 said "❌ 未實現 — multimodal_routes.py 中無 WebSocket 端點". PARTIALLY WRONG.

- `websocket_manager.py` has `_handle_multimodal_encode()` and `_handle_multimodal_decode()` handlers (lines 328-400)
- `websocket_handler()` dispatches message types "multimodal_encode" / "multimodal_decode" (lines 440-444)
- BUT: there is NO dedicated `/multimodal/stream` or `/ws/multimodal` HTTP WebSocket endpoint

**Status**: WebSocket multimodal handlers exist at the protocol level but there's no registered endpoint. Needs a route registration.

### 2.4 Phase 9-11 Deletions (PROJECT_HONEST_AUDIT §5, §11)

| Phase | Files | Git Evidence | Code Evidence | Status |
|-------|-------|-------------|---------------|--------|
| Phase 9 | comic_composer.py, ai/security/, image_generation_agent.py | `d08ff55f4` (Jun 22 commit log) | All files confirmed deleted | ✅ Done |
| Phase 10 | real_creator.py, real_comfyui_api.py | d08ff55f4 | All confirmed deleted | ✅ Done |
| Phase 11 | tactile_service.py, wiring.py | d08ff55f4 | All confirmed deleted | ✅ Done |
| Phase 11 | mobile-app/ | d08ff55f4 | Confirmed deleted | ✅ Done |
| Phase 11b | 11 dead subsystems | `d08ff55f4` | All confirmed gone | ✅ Done |

**Total**: 37+ files + 11 subsystems = ~5,920 lines dead code removed.

### 2.5 Tools & Scripts Cleanup (TOOLS_SCRIPTS_CLEANUP_PLAN)

| Action | Claimed | Git Evidence | Code Evidence | Status |
|--------|---------|-------------|---------------|--------|
| Delete 227 files | ✅ | `29b883cbb` (refactor) | Confirmed | ✅ Done |
| 9 bugs fixed | ✅ | Same commit | run_angela.py, ConnectException fixes | ✅ Done |
| **Auto-repair merge** | ⚠️ Planned | **NO matching commit** | `run_angela.py` still has `"请运行: pip install -r requirements.txt"` with no auto-install | ❌ **NOT DONE** |
| **install_angela.py keep** | ✅ Keep | — | `tools/legacy_scripts/install_angela.py` (745 lines) still on disk | 🟡 Orphan |
| **AngelaLauncher.bat keep** | ✅ Keep | — | `tools/legacy_scripts/AngelaLauncher.bat` (60 lines) still on disk | 🟡 Orphan |

**Gap**: The cleanup plan explicitly warned: "Merge auto-repair logic into run_angela.py FIRST before deleting. Risk: HIGH, Impact: HIGH." This was never done. The 2 orphaned files remain in `tools/legacy_scripts/`.

### 2.6 StateMatrixAdapter Fix (latest session)

| Action | Claimed | Git Evidence | Code Evidence | Status |
|--------|---------|-------------|---------------|--------|
| 8 missing methods | ✅ | `ca6a9f362` | All implemented | ✅ Done |
| 9/9 integration tests | ✅ | Same commit | `test_state_matrix_integrations.py` | ✅ Verified |

---

## 3. Pending Items — Verified Against Code

### 🔴 High Priority (Blocking or Gap)

| # | Item | Source Doc | Git? | Code? | Real Status |
|:-:|:-----|:-----------|:----:|:-----:|:------------|
| 1 | **Auto-repair pathway** — merge install_angela.py logic into run_angela.py | TOOLS_SCRIPTS_CLEANUP_PLAN.md line 428 | ❌ No commit | `run_angela.py` has no auto-install | ❌ **Not done. Gap documented since Jun 13.** |
| 2 | **YOLO object detection** | PHASE_REVIEW6.md line 9 | ❌ No commit | Zero code exists | ❌ **Not started** |
| 3 | **WebSocket `/multimodal/stream` endpoint** — dedicated HTTP route | PHASE_REVIEW6.md line 9 | ❌ No commit | WS handlers exist at msg level, but no route | ❌ **Not done** |
| 4 | **tests/ directory test count** — reconcile 4,920 vs 4,261 | PHASE_REVIEW6.md line 19 vs REPAIR_ROADMAP | N/A | Current: 4,261/33 skipped | 🟡 **Discrepancy unexplained** |
| 5 | **22 stale branches** — 19 dependabot + 3 backup | Blocked | — | — | 🟡 Needs developer |
| 6 | **`git rm --cached models/*.npy models/*.pt`** | Blocked | — | — | 🟡 Needs developer |
| 7 | **Python 3.14 test matrix** in CI | Blocked | — | — | 🟡 Needs decision |
| 8 | **JS unit tests** — no real implementation | Blocked | — | `ci.yml` has `echo "No JS tests"` | 🟡 Needs implementation |
| 9 | **`tools/legacy_scripts/` orphaned files** — 2 files after cleanup | TOOLS_SCRIPTS_CLEANUP_PLAN | Partial cleanup done | `install_angela.py` + `AngelaLauncher.bat` remain | 🟡 Blocking auto-repair merge |

### 🟡 Medium Priority

| # | Item | Source | Code Status |
|:-:|:-----|:-------|:------------|
| 10 | **Whisper audio not wired to ChatService** | PROJECT_HONEST_AUDIT §1 | `faster-whisper` installed but not integrated into chat pipeline. `/chat/with-audio` endpoint exists though. | 🟡 Partially done |
| 11 | **VisualDecoder untrained** | PROJECT_HONEST_AUDIT §3 | Decoder exists, weights random. CLP trains shared_latent_space but not decoder. | 🟡 Needs training |
| 12 | **Agent auto-routing** — agents registered but pipeline doesn't call them | PROJECT_HONEST_AUDIT §4 | `agent_manager.py` exists, 11 agents registered. ChatService doesn't invoke them. | 🟡 Design decision |
| 13 | **Level5ASI.stub classes** (DistributedCoordinator, etc.) | STUB_TRACKING.md #16-18 | Logged stubs, need real alignment modules | 🟡 P1.1 pending |
| 14 | **IMPLEMENTATION_STATUS.md** — 10 months stale | Self | All status items wrong | 🟡 Should SUPERSEDED |
| 15 | **PHASE_REVIEW6.md §3.2** — incorrect MultimodalPanel/WS status | Self | Files exist, doc wrong | 🟡 Should correct |

### 🟢 Low Priority / Future

| # | Item | Source | Notes |
|:-:|:-----|:-------|:------|
| 16 | Text-to-image (SD/DALL-E) | PROJECT_HONEST_AUDIT §4 | ComfyUI removed. GVV + ThreeLayerVisual are the active paths. |
| 17 | Frontend multimodal UI enhancements | PHASE_REVIEW6 line 9 | Panel exists but could be extended |
| 18 | True singing synthesis | PHASE_REVIEW6 §3.2 | edge-tts only does reading |
| 19 | Authentic music synthesis | PHASE_REVIEW6 §3.2 | Not started |
| 20 | ~25 partially-implemented subsystems | PROJECT_HONEST_AUDIT §3 | Many already removed in Phase 11; remaining need triage |
| 21 | Matrix annotations missing on 157 files | COMPREHENSIVE_AUDIT | 59/216 have headers |
| 22 | Load testing | Multiple | Not started |
| 23 | Archive stale docs | Multiple | Ongoing |

---

## 4. Claims Corrections — Documents That Conflict With Reality

### 4.1 PHASE_REVIEW6.md

| Line | Claim | Reality | Fix Needed |
|:----:|:------|:--------|:-----------|
| 417 | Desktop MultimodalPanel: ❌ 未實現 | ✅ 3 files exist (html + 2 js + tests) | Change to ✅ |
| 418 | WebSocket 串流: ❌ 未實現 | WS handlers exist at msg level; only dedicated route missing | Change to 🟡 (partial) |
| 19 | 4920 tests collected | Current: 4261 | Add footnote: "4261 on 2026-06-26" |
| 7 | 460,281 entries | Could be correct | Verify |

### 4.2 PROJECT_HONEST_AUDIT.md

| Line | Claim | Reality | Fix Needed |
|:----:|:------|:--------|:-----------|
| 159 | ImageGenerationAgent not deleted | ✅ Deleted in Phase 9 | Update text |
| 160-162 | ComfyUIClient, AngelaRealPainter stubs | ✅ Deleted in Phase 10 | Delete or mark REMOVED |
| 163-167 | TactileService, wiring.py, security/, mobile-app/ | ✅ Deleted in Phase 11 | Delete or mark REMOVED |
| 168 | Level5ASI: DistributedCoordinator is stub | Still true | Keep |
| 170 | 25+ partially implemented subsystems | 11 removed in Phase 11b, ~14 remain | Update count |
| 177 | ~55% 無意義堆砌 | Likely lower after Phase 11 | Recalculate |

### 4.3 IMPLEMENTATION_STATUS.md

Every single status item is from **2025-08-21** and wrong. All "🟧 Skeleton" modules have either been completed or deleted. Should be marked **SUPERSEDED**.

---

## 5. Verification Protocol — Before Acting, Check

To prevent re-implementing or incorrect implementation:

| Question | How to Check |
|:---------|:-------------|
| Does this code exist? | `git log --oneline --all --grep="<keyword>"` + `Test-Path <file>` |
| Was this task done before? | Check this MASTER_TASK_MAP.md first |
| Is the document claim accurate? | Check git commit that created the feature |
| Does the test count match? | `python -m pytest tests/ --collect-only -q` |
| Was this subsystem deleted? | `Test-Path <path>` + `git log --all -- <path>` |

---

## 6. Next Steps (Ordered, No Duplicates)

### Immediate (this session)
1. Mark `IMPLEMENTATION_STATUS.md` as SUPERSEDED
2. Correct PHASE_REVIEW6.md §3.2 MultimodalPanel status (✅ not ❌)
3. Verify all PROJECT_HONEST_AUDIT claims against current codebase

### Next Batch
4. Merge auto-repair logic from `tools/legacy_scripts/install_angela.py` into `run_angela.py`
5. Delete `tools/legacy_scripts/` (last 2 orphaned files)
6. Add `/multimodal/stream` WebSocket route (code exists at WS handler level, just needs routing)

### After
7. YOLO object detection (new code needed)
8. Train VisualDecoder (CLP train loop extension)
9. Wire Whisper into ChatService audio pipeline
10. Decide on agent auto-routing approach
11. Reconcile 4,920 vs 4,261 test count (likely depends on environment)

### Never Do
- ❌ Re-implement Phase 9-11 deleted files (comic_composer, security, real_creator, real_comfyui_api, tactile_service, wiring, mobile-app, 11 subsystem dirs)
- ❌ Re-create deleted subsystems (learning/, ops/, dialogue/, evaluation/, etc.)
- ❌ Claim MultimodalPanel doesn't exist (it does, since Jun 22 commit)
