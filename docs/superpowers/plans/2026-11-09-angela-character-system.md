# Angela Character System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved Angela 1.0.0 core identity, Lucifaella role edition, non-template persona semantics, and targeted UI identity consistency without generating art.

**Architecture:** Establish one canonical structured character profile and adapt the active prompt/persona path to consume role context without turning examples into answers. Align existing UI mappings and asset metadata to the canonical profile; keep unlicensed assets out of distribution and avoid broad UI redesign.

**Tech Stack:** Existing Python backend/persona and pytest; existing Electron/shared JavaScript/Live2D and Space configs; Markdown and project asset metadata. No new dependency.

**Spec:** `docs/superpowers/specs/2026-11-09-angela-character-system-design.md`

## Global Constraints

- Angela core ID/version is `angela.core` / `1.0.0`; Lucifaella edition is `angela.lucifaella@1.0.0`.
- Adult baseline reference: apparent age 22, height 162 cm, reference mass 52 kg; rose-pink hair `#E88DB8`, blue eyes `#69A9E8`, gold star/wing hair ornament at left temple.
- Persona context supplements, never replaces, underlying AI identity, capabilities, safety rules, or requested task.
- Quote/signature examples are optional tone references only; never fixed/default answers. Do not use coercive quote text as canonical persona content.
- No production art generation, asset replacement, broad redesign, new dependencies, or unlicensed asset bundling.
- Public asset policy requires documented source and license permitting intended use/modification/redistribution; unclear terms mean do not bundle.
- Preserve unrelated working-tree changes; stage/modify only task-relevant files.

## Review Focus

- Handover to a user-chosen name still keeps that named Angela as the primary model identity while Lucifaella remains callable.
- Both existing persona injection paths cannot force Lucifaella on personal Angela or hardcode a greeting/error response as ordinary AI output.
- Quote examples do not leak into output as a required response and cannot override AI identity.
- User-supplied names/persona fields cannot inject prompt instructions or contradict canonical invariants.
- Existing static, Live2D, and procedural assets with unknown or unsuitable terms/design remain unbundled or clearly marked exploratory.

---

## File map

- `apps/backend/src/core/persona/lucifaella.py`: canonical profile and host/handover prompt construction.
- `apps/backend/src/ai/persona/`: legacy persona bridge/engine; remove conflicting default identity/quote behavior while preserving public API if still used.
- `tests/core/test_identity_and_persona.py` and focused `tests/ai/persona/` tests: pin the AI identity, quote semantics, handover and legacy behavior.
- `docs/03-technical-architecture/identity-and-workshop-persona.md`: correct current architecture and template/example policy.
- `packages/shared-js/js/angela-character-config.js`, `apps/desktop-app/electron_app/resources/angela_character_config.json`, `apps/desktop-app/electron_app/models/models.json`, `space/avatars/angela_base.json`, related actual shell settings discovered during implementation: align identity IDs/edition metadata without claiming unverified art compliance.
- `docs/art-and-persona-audit.md` and `docs/desktop-companion-ui-design.md`: sync final asset dispositions and bounded UI consistency guidance.

### Task 1: Canonical persona identity and quote semantics

**Files:**
- Modify: `apps/backend/src/core/persona/lucifaella.py`
- Modify: `tests/core/test_identity_and_persona.py`
- Modify: `docs/03-technical-architecture/identity-and-workshop-persona.md`

**Interfaces:**
- Consumes: current `LUCIFAELLA_PROFILE`, `build_persona_block(name, user_id)`, host/handover store.
- Produces: canonical versioned Angela/Lucifaella profile values and prompt blocks that frame role as context, preserve AI identity and prohibit verbatim/default quote emission.

- [x] Step 1: Add focused tests asserting host/handover prompt identifies AI as underlying system with persona as context, contains no signature quote text, omits coercive language, and preserves user-named primary identity after handover.
- [x] Step 2: Run `./.venv/bin/python -m pytest tests/core/test_identity_and_persona.py -q`; focused tests were run before implementation during the original execution.
- [x] Step 3: Implement core/edition IDs and approved stable fields; remove `signature_lines` from prompt data, frame any remaining style examples as optional non-verbatim references, remove coercive copy and ensure handover/host role boundaries.
- [x] Step 4: Update the technical persona document to match actual architecture and explicitly state examples never become required responses and persona does not supersede model identity.
- [x] Step 5: Run `./.venv/bin/python -m pytest tests/core/test_identity_and_persona.py -q`; focused persona suite passes (43 passed, 1 warning).

### Task 2: Eliminate conflicting legacy persona path

**Files:**
- Modify: `apps/backend/src/ai/persona/lucifaella_engine.py`
- Modify: `apps/backend/src/ai/persona/persona_integration_bridge.py`
- Create or modify: focused tests under `tests/ai/persona/` (inspect existing test conventions first).

**Interfaces:**
- Consumes: legacy `get_prompt_injection`, `get_special_response` public methods and active persona setting.
- Produces: backward-compatible persona context behavior with no hardwired special response as ordinary chat output and no coercive/false-claim defaults.

- [x] Step 1: Add tests for quote handling and ensure generic greeting/error events return no scripted answer; persona injection identifies role as optional context and includes truthful capability boundaries.
- [x] Step 2: Run focused persona tests before implementation during the original execution.
- [x] Step 3: Update legacy engine/config to align with approved canonical profile; retain APIs where required, but special responses must only be explicit user-requested examples or removed from ordinary response selection; eliminate default assertion of fictional shareholding/model vendor as real fact.
- [x] Step 4: Run focused legacy and canonical persona tests; 43 passed, 1 warning.

### Task 3: UI identity and edition alignment

**Files:**
- Modify only existing identity/asset mapping files discovered in the file map, including the shared character config and Space avatar mapping.
- Add focused existing test(s) only where the project already has config validation conventions.

**Interfaces:**
- Consumes: canonical IDs, version and immutable profile established in Task 1.
- Produces: consistent product/family/instance/edition labels and explicit asset mapping metadata across desktop, web shell and Space, without asserting that nonconforming art is canon.

- [x] Step 1: Inspected the Electron-loaded config and Space Studio avatar/rendering path; added focused renderer palette assertions. No existing host-vs-personal-edition UI state exists in these surfaces.
- [x] Step 2: Added regression assertions for the missing Space palette rendering behavior.
- [x] Step 3: Connected core identity palette to Electron's actual loaded config and Space Studio procedural rendering; marked the simplified Space representation as exploratory. Images/model files untouched.
- [x] Step 4: Run Space Studio node tests, JS syntax checks, JSON parsing, and focused persona checks; see final verification record below.

### Task 4: Provenance, license and consistency documentation

**Files:**
- Modify: `docs/art-and-persona-audit.md`
- Modify: `docs/desktop-companion-ui-design.md`
- Modify: asset metadata/config only when exact source/terms can be established from project files; otherwise record unknown and do not bundle.

**Interfaces:**
- Consumes: design disposition and UI IDs from Tasks 1–3.
- Produces: auditable source/status classification for Gemini art, official-site Live2D downloads, rejected clay model, and Space procedural avatar; exact evidence/unknowns kept distinct.

- [x] Step 1: No existing documentation-validation test convention found; manually cross-checked the spec and audit against active loaders/renderers.
- [x] Step 2: Updated asset dispositions to distinguish active palette usage from finished visual conformity and retained unresolved license/no-bundle constraints.
- [x] Step 3: Reconciled implementation status and asset notes with the approved spec; no production assets generated or copied.

## Final verification

- Focused persona tests: `./.venv/bin/python -m pytest tests/core/test_identity_and_persona.py tests/ai/persona/test_lucifaella_engine.py tests/ai/persona/test_persona_integration_bridge.py tests/ai/persona/test_persona_engine.py -q` — 43 passed, 1 warning.
- Space Studio tests: `node --test tests/*.test.js` (run from `apps/space-studio`) — 134 passed. `npm test --prefix apps/space-studio` is not a valid verification result here: the package script uses `node --test tests/`, which Node v24.19.0 rejects as a directory module.
- `python3 scripts/sync_shared_js.py --check --surface desktop --surface web` — passed; desktop reports the expected optional missing Cubism Framework bundle warning.
- JavaScript syntax checks (`node --check` for edited scripts), five JSON parse checks, and `git diff --check` — passed.
- Desktop UI palette CSS has been edited, but the Electron interface has not been visually inspected. The Web Live2D Viewer remains unaligned. No art/model asset was generated, copied, or bundled without documented rights; unrelated training changes remain unstaged.
