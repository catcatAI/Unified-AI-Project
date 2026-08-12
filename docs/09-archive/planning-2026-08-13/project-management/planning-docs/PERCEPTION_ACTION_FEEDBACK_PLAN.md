# Perception–Action–Feedback (Behavioral Closed Loop) Plan

Version: v0.1
Date: 2025-08-06
Owners: Core Dev / Architecture / PM

## 1. Purpose
Establish a practical behavioral closed loop so the system learns not only "what to say" but "when and how to act," and how outcomes shape future choices. This plan operationalizes the loop across perception → decision (tool/model selection) → action (tool calls) → feedback (KPI/Trust) → policy adjustment.

## 2. Scope
- Backend runtime (FastAPI) and core services (core_services)
- ToolDispatcher, DialogueManager, TrustManager
- HAM (memory), LIS (incident/antibody), Observability (/api/v1/hot/status)
- Tests + docs

## 3. Alignment
- Technical Roadmap §2.4 Perception–Action–Feedback (planning/core-development/TECHNICAL_ROADMAP.md)
- STATUS & ACTIONS (rolling) (planning/project-management/planning-docs/STATUS_AND_ACTIONS.md)
- AGI & Data Life Plan (planning/project-management/planning-docs/AGI_AND_DATA_LIFE_IMPLEMENTATION_PLAN.md)
- Observability Guide (Unified-AI-Project/docs/05-development/observability-guide.md)

## 4. Action–Tool Policy: Logging Schema (v0.1)
Record per tool invocation:
- tool_name: string
- params_hash: string (stable hash of normalized parameters)
- outcome: string | object (truncated JSON, or code for outcome class)
- success: boolean
- latency_ms: number
- cost_units: number (optional, model/tool cost)
- user_context: { user_id?: string, session_id?: string }
- correlation_id: string (if available via HSP/DM)
- timestamp: ISO-8601

### 4.1 Persistence (HAM)
- raw_data: JSON string of full record
- metadata (proposed keys):
  - ham_meta_action_policy: true
  - ham_meta_tool_name: <tool_name>
  - ham_meta_success: true|false
  - ham_meta_timestamp: ISO-8601

## 5. Observability & Dashboard Mapping
- /api/v1/hot/status → metrics.learning.tools (best-effort aggregation):
  - total_invocations: number
  - success_rate: number (0..1)
  - recent_failures: number (last N window)
  - avg_latency: number | null
- Dashboard schema (see Observability Guide) maps fields via JSONPath-like paths, e.g.:
  - metrics.learning.tools.success_rate → KPI "Tool Success %"

## 6. Policy Adjustment
- TrustManager deltas from success signals (initially: tool return OK, evaluator pass)
- Routing adjustments (models/tools) under guardrails (caps, thresholds)
- Record routing decisions (model/tool + rationale) for audit

## 7. Self-Start / Unknown Tokens Strategy (from 114)
- Decision policy:
  - Prefer internal self-improvement loop first (reuse context, re-evaluate, audit/backtrack)
  - If insufficient evidence or context sparse → selectively pull external data (APIs/tools) under cost/latency guardrails
- No-user-data mode:
  - Use simulation/synthetic data (e.g., TextWorld-like tasks) + model API (e.g., Grok 3) for policy training
  - Log all actions via Action–Tool Policy; replay for improvement; avoid PII by design

## 8. Implementation Timeline
- Week 1 (current)
  - Finalize schema; enrich /api/v1/hot/status (metrics.learning.tools) with placeholder aggregation
  - Docs: Observability guide + examples
- Week 2
  - Implement ToolDispatcher logging to HAM per invocation (guarded try/catch)
  - Add smoke tests for /status metrics and basic aggregation
- Week 3
  - Wire initial success signals to TrustManager deltas; add routing decision logs
  - Extend tests (policy changes reflected in metrics/logs)

## 8. Testing
- Unit: params_hash generation; logging correctness under errors
- Integration: tool calls produce HAM entries; /status exposes aggregates
- E2E: policy changes (trust/routing) respond to KPI deltas under guardrails

## 9. Risks & Mitigations
- Overhead: sample or batch writes; cache status aggregates
- Data quality: normalize params; cap outcome size; redact PII in user_context
- Instability: gate policy changes; stage rollout; enable quick rollback via hot reload

## 10. Open Questions
- Exact HAM metadata keys naming; retention policy for action logs
- Aggregation window sizes for recent_failures/avg_latency
- Cost accounting units and sources

## 11. To be integrated (113.txt)
- Placeholder: add additional insights/tasks once 113.txt content is available

## 12. References
- CROSS_MODULE_IMPACT_MATRIX.md
- TECHNICAL_ROADMAP.md §2.4
- STATUS_AND_ACTIONS.md (rolling)
- AGI_AND_DATA_LIFE_IMPLEMENTATION_PLAN.md
- observability-guide.md
