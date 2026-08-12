# Status & Actions (Rolling)

Owner: PM / Tech Leads
Cadence: Weekly (append new section)

## Week of 2025-08-04

### Status (Concise)
- Backend: hot reload/migration/drain endpoints implemented; tools/personality reload; status endpoint returns HSP/MCP + initialized snapshot.
- AudioService: demo sentiment path implemented.
- Docs: API endpoints updated; new hot-reload doc; planning consolidation proposal drafted.

### Risks / Issues
- LIS E2E not wired; observability partial; knowledge graph TBD.
- Tests coverage not yet expanded for new hot endpoints.

### Actions (This week)
- Extend /api/v1/hot/status with metrics (HSP/MCP + learning/LIS/HAM summaries) and docs/tests.
- Prepare LIS minimal demo path and tests.
- Update documentation-index.md to reference canonical roadmap and AGI plan.

### Decisions / Requests
- Confirm observability schema (status.metrics) and dashboard JSON structure.
- Confirm LIS minimal demo API surface and test scope.

---

## Week of 2025-08-22 — Frontend/API integration carryover (from implementation_plan.md)

### Actions (Carryover)
- Verify frontend uses real API data end-to-end (remove mock data paths); audit pages:
  - Agents: /api/v1/agents, /api/v1/agents/{id}, /api/v1/agents/{id}/action
  - Models: /api/v1/models, /api/v1/models/{id}/metrics, /api/v1/models/{id}/training
  - Images: /api/v1/images/* endpoints
  - System metrics: /api/v1/system/metrics/detailed, /api/v1/health
- Update TS interfaces/hooks if schema drifted; add smoke tests for critical screens.
- Add a dashboard panel based on observability-guide schema (HSP/MCP/learning/memory/LIS).

### Risks / Notes
- Schema drift between backend and frontend; mitigate by generating/validating OpenAPI or adding contract tests.
- Keep mock data path switch behind a flag for quick fallback.

---

## Week of 2025-08-15 — Insights consolidated from 112 & 113

### Strategic Notes (from 113)
- Niche-first + ecosystem expansion: MVP = Desktop Pet + Coin Loop + Economic AI; expand features and developer SDK later.
- Multi-surface presence: prioritize CLI + Web (Electron UI optional), enabling low-friction adoption.
- Resource-aware goals: correctness 95–98%, hallucination 2–5%, latency 10–18s, memory <6GB.

### MVP Track (6–8 weeks, 4–6h/day)
- No-user-data training cycle (from 114):
  - Build simulation/synthetic pipelines; define replay & evaluation; integrate model API
  - Start with minimal tasks (desktop pet dialogue/coin loop/economic AI), log policy events for replays
- Core modules: desktop pet dialogue, coin loop, economic AI.
- Architecture: async tasks + event-driven interrupts; toolization for perception-heavy subtasks.
- Validation: audit path (rules + re-evaluation), buffered backtracking + staging area.


### Status (Concise)
- Architecture discussion identified a key AGI bottleneck: separation between LLM and action layer prevents a fully closed perception–action–feedback loop.
- Current codebase now supports hot reload/migration, basic observability, and will be extended to surface learning/memory/LIS summaries.

### Insights (from 112.txt)
- LLM ↔ Tools have a necessary isolation layer for safety, but AGI behaviors require a training-time closed loop that includes tool invocation decisions and outcomes.
- Instruction tuning + tool calling format + RLHF/RLAIF can teach “when to call tools”, “how to use results”, and “when not to call”.
- For long-term behaviors, the loop must internalize action policies, success signals, and state changes (beyond pure text IO).

### Risks / Issues
- Tool layer remains passive; outcomes are not systematically captured as training signals.
- Lack of end-to-end incident→antibody→effectiveness updates (LIS) limits corrective learning.
- Integration debt: features added faster than integration/closure rate.

### Actions (This week / Next)
- Observability
  - Extend /api/v1/hot/status metrics (HSP/MCP, learning/trust, memory/HAM, LIS) — in progress.
  - Define dashboard JSON schema for metrics; publish example payloads.
- Feedback & Data capture
  - Start logging a minimal “Action-Tool Policy” record into HAM for each tool call: {tool_name, params, outcome, success(bool), latency, cost, user_context}.
  - Map success signals to TrustManager and simple KPI counters; surface in status.metrics.
- LIS E2E
  - Minimal demo: anomaly → incident store → antibody selection/generation → effectiveness update.
  - Tests: filters by type/severity/time/tags and a simple effectiveness delta.
- Safety & Ops
  - Keep blue/green reload path hardened; drain on when reloading tool/policy components.

### Decisions / Requests
- Approve the Action-Tool Policy logging schema and where to persist (HAM metadata keys).
- Approve initial success signals (e.g., tool return OK, evaluator pass) to drive trust/KPI deltas.

### Action–Tool Policy: Logging Schema (Draft)
- Record per tool invocation:
  - tool_name: string
  - params_hash: string (stable hash of normalized params)
  - outcome: string | object (truncated JSON, or code for outcome class)
  - success: boolean
  - latency_ms: number
  - cost_units: number (optional, model/tool cost)
  - user_context: { user_id?: string, session_id?: string }
  - correlation_id: string (if available via HSP/DM)
  - timestamp: ISO-8601
- Persist in HAM as raw_data (JSON string) with metadata keys:
  - ham_meta_action_policy: true
  - ham_meta_tool_name: <tool_name>
  - ham_meta_success: true/false
  - ham_meta_timestamp: ISO-8601
- Minimal aggregation surfaced via /api/v1/hot/status → metrics.learning/tools:
  - total_invocations, success_rate, recent_failures (last N), avg_latency

### Rollout Timeline
- Week 1 (current):
  - Finalize schema; implement best-effort aggregation in HotReloadService.status() (metrics.learning.tools)
  - Docs: Observability guide + dashboard schema
- Week 2:
  - Implement ToolDispatcher logging to HAM (per invocation) with guarded try/catch
  - Add smoke tests for /status metrics and basic aggregation
- Week 3:
  - Wire initial success signals to TrustManager deltas
  - Add routing decision logs (model/tool + rationale)

- Confirm roadmap structure (TECHNICAL_ROADMAP.md) and rolling status approach.
- Decide dashboard JSON schema for later visualization (optional).
