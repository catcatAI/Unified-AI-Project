# LLM Auto-Adaptation & Auto-Routing Plan

This document defines the plan to implement model auto-adaptation (provider/key detection and capability discovery) and auto-routing (policy-driven model selection per request), with full integration into Backend, Frontend, and CLI.

## Goals
- Automatically detect available LLM providers via API keys / configuration at startup.
- Build a unified ModelRegistry with per-model capability metadata (context, modalities, json/tool-use support, cost/latency estimates).
- Implement a Router/PolicyEngine to choose the best model for each task (translation, code, reasoning, image, vision) with latency/cost targets.
- Support fallback chains, rate limiting (simple), and observability for routing decisions.
- Provide API endpoints to list available models and dry-run routing.
- Frontend/CLI support for Auto/Manual selection and model introspection.

## Out-of-Scope (initial)
- Complex credit/cost accounting and billing.
- Streaming observability spans (basic logging only in phase-1).
- Cross-region deployment specifics.

## Architecture Overview

```
+-----------------------+
|  Key Manager          |  Reads ENV / config for API keys
+----------+------------+
           |
+----------v------------+     +---------------------+
| Provider Adapters     |---->| Model Registry      |
| (OpenAI/Anthropic/...)|     | (Model Profile DB)  |
+----------+------------+     +---------------------+
           |                              |
           |   Discover                    | query
           |                               v
           |                    +---------------------+
           |                    | Router/PolicyEngine |
           |                    +---------------------+
           |                               |
           +------------------------------->|
                                 Select best model
```

## Backend Changes

### New Modules (Phase 1)
- `apps/backend/src/core_ai/language_models/providers/` (Conceptual: Providers are currently implemented directly within `multi_llm_service.py` for consolidation.)
  - `base.py` (common interface: chat, embeddings, image where applicable)
  - `openai_adapter.py`, `anthropic_adapter.py`, `gemini_adapter.py`, `azure_openai_adapter.py`, `groq_adapter.py`, `together_adapter.py`, `cohere_adapter.py`, `ollama_adapter.py`
- `apps/backend/src/core_ai/language_models/registry.py`
  - Holds ModelProfile list, merged from adapters' discover()
- `apps/backend/src/core_ai/language_models/router.py`
  - PolicyEngine: input (task_type, input_chars, needs_tools/json, needs_vision, latency_target, cost_ceiling) -> selection

### Integrations / Refactors
- `apps/backend/src/services/multi_llm_service.py`
  - (Partial) Use ModelRegistry + Router to select model when `model_id` not provided. **Note: Full auto-routing integration is pending; currently, `model_id` is still required or defaults to `default_model`.**
  - (Pending) Accept `policy` hints in request.

### New API Endpoints
- `GET /api/v1/models/available` -> ModelProfile list
- `POST /api/v1/models/route` -> dry-run router with `{ task_type, input_chars, needs_tools?, needs_vision?, latency_target?, cost_ceiling? }`
- Extend `POST /api/v1/chat`
  - Accept `model_id?: string`
  - Accept `policy?: { task_type, latency_target, cost_ceiling, needs_tools, needs_vision }`

### Keys & Config
- Detect from ENV:
  - `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_ENDPOINT`, `GROQ_API_KEY`, `TOGETHER_API_KEY`, `COHERE_API_KEY`, `OLLAMA_HOST`.
- Optional `apps/backend/configs/providers.yaml` for non-ENV bootstrap (phase-2).

### Observability
- Log selection: chosen model, candidates, elapsed, retry/fallback.
- (Phase-2) basic metrics (counts, errors, fallback rate).

## Frontend Changes (Phase 2)
- Settings/Models page:
  - Display available models from `/api/v1/models/available`.
  - Auto/Manual toggle (global default) with policy presets.
- Chat/Code pages:
  - Allow override model manually (dropdown) or use Auto.

## CLI Changes (Phase 2)
- New commands:
  - `unified-ai models list` -> calls `/api/v1/models/available`
  - `unified-ai models route --task-type code --input-chars 1200 --json` -> dry-run router
- `unified-ai chat` add `--model` (default `auto`), and `--policy-*` flags (tbd presets).

## Phases & Milestones

### Phase 1 (Backend Core)
- [ ] Implement Provider base + 1-2 adapters (OpenAI, Gemini to start)
- [ ] Implement ModelRegistry with discovery & ModelProfile schema
- [ ] Implement Router/PolicyEngine (initial heuristic)
- [ ] Wire into `multi_llm_service.py` (chat path)
- [ ] Add endpoints: `/api/v1/models/available`, `/api/v1/models/route`
- [ ] Update API_STATUS_REPORT.md, README

### Phase 2 (Frontend/CLI)
- [ ] Frontend Settings/Models UI (Auto/Manual)
- [ ] Chat/Code pages: allow model override + display chosen model
- [ ] CLI: add `models list` and `models route`, and `--model` to `chat`

### Phase 3 (Hardening)
- [ ] Fallback chains and backoff
- [ ] Basic rate limiting per provider
- [ ] Metrics/observability
- [ ] E2E tests

## Acceptance Criteria
- No keys present: `/models/available` returns empty list, router returns clear error.
- With keys: discovery populates ModelRegistry, `/models/available` non-empty.
- `/models/route` returns deterministic selection for standard inputs.
- `POST /chat` with `policy` auto-selects and succeeds; manual `model_id` override works.

## Risks & Mitigations
- Provider API drift -> adapters isolated, tests per provider.
- Inconsistent capability fields -> normalize in ModelProfile.
- Cost/latency estimates inaccurate -> incremental calibration from logs.

## Rollback Strategy
- Feature flag in `multi_llm_service.py` to bypass Router and use fixed default (env `LLM_ROUTER_ENABLED=false`).

---

## Implementation Checklist (Phase 1)
- [ ] Create provider base + OpenAI/Gemini adapters
- [ ] ModelRegistry with discovery pipeline
- [ ] Router with initial heuristics (task mapping)
- [ ] Extend chat service to use router when `model_id` is not specified
- [ ] Expose APIs `/models/available` and `/models/route`
- [ ] Update docs (README, API_STATUS_REPORT.md)

---
*Last Updated: 2025-08-10*