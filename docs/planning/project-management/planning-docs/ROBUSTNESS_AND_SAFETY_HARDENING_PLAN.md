# Robustness & Safety Hardening Plan (AGI/ASI Readiness)

Version: v0.1
Date: 2025-08-06
Owners: Core Dev / Safety / PM

## 1. Purpose
Harden the system toward AGI/ASI readiness by introducing architectural guardrails, safety checks, and fault tolerance across perception–action–feedback loops, communications, and memory.

## 2. Scope
- DialogueManager, ToolDispatcher, TrustManager
- Safety audit path (pre-output validation), buffered backtracking, staging area
- HSP/MCP connectors (resilience), HotReloadService (safe reconfiguration)
- HAM/LIS governance (retention, provenance, redaction)

## 3. Pillars
1) Safety-by-design
- Dual-path: execution + audit for critical requests
- Output validation & correction (rules + secondary evaluation)
- Policy guardrails: caps, thresholds, deny-lists

2) Fault-tolerance
- Retries with backoff; circuit breaker metrics surfaced in /status
- Blue/green reload + drain; health checks; chaos drills (dev only)

3) Data governance
- Retention/aging policy in HAM (time + importance + trust)
- Provenance/lineage (who/when/from-where); minimal redaction for PII

## 4. Deliverables
- Audit & backtracking hooks behind flags in DialogueManager
- ToolDispatcher Action–Tool Policy logging (HAM) with /status metrics aggregation
- Safety config (YAML):
  - audit_enabled (scoped), backtracking_limit, staging_checks
  - blocked_tools, max_cost_per_request, max_latency
- Resilience KPIs in /api/v1/hot/status: retry counters, breaker state, reload events
- Governance: minimal lineage metadata keys; retention policy draft

## 5. Implementation Tracks
- T1: Audit & Backtracking (Week 1–2)
  - Add DM audit hook; staging & single-level backtracking; record policy events
- T2: Tool Policy Logging (Week 1–2)
  - Log per-invocation to HAM; aggregate learning.tools in /status
- T3: Resilience Metrics (Week 2–3)
  - Expose retry/breaker stats; record reload events; add smoke tests
- T4: Governance (Week 3+)
  - Add lineage metadata (source_ai_id, provenance, correlation_id); draft retention policies

## 6. Tests
- Unit: audit rule triggers; backtracking limit; policy event integrity
- Integration: /status metrics for breaker/retries & learning.tools
- Chaos (dev): inject transient faults and verify recovery paths

## 7. Risks & Mitigations
- Latency from audit/backtracking → scope to critical requests; sampling
- Over-logging → sample/batch; retention policy and summarization
- Safety rules drift → config-driven; review cadence; add deny-list tests

## 8. References
- CROSS_MODULE_IMPACT_MATRIX.md
- TECHNICAL_ROADMAP §2.4/2.5
- PERCEPTION_ACTION_FEEDBACK_PLAN.md
- observability-guide.md
