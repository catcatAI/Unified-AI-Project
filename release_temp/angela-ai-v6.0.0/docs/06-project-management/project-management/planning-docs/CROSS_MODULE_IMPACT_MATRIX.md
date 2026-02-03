# Cross-Module Impact Matrix (Plans ↔ Code)

Version: v0.1
Date: 2025-08-06
Owners: Architecture / PM

This matrix highlights features that influence each other across plans and code. Use it to schedule sequencing and avoid regressions.

## 1) Hot Reload & Status Metrics
- Upstream: HotReloadService (`/api/v1/hot/status`, reload endpoints)
- Downstream:
  - Observability Guide & dashboard (status schema)
  - ToolDispatcher logging (learning.tools aggregation in status)
  - DialogueManager audit flags (drain-aware behavior)
- Risks: schema drift; missing fields → client breakage. Mitigation: treat fields as optional; doc best-effort semantics.

## 2) ToolDispatcher Action–Tool Policy Logging
- Upstream: Tool execution wrappers, HAM availability
- Downstream:
  - Status metrics: `metrics.learning.tools` (total_invocations, success_rate, recent_failures, avg_latency)
  - TrustManager deltas & routing adjustments (Policy Router)
  - LIS (future): use incidents/antibodies to contextualize failures
- Risks: logging overhead; PII in user_context. Mitigation: sampling/batching; redact PII by design.

## 3) LIS E2E (incident → antibody → effectiveness)
- Upstream: ContentAnalyzer/LearningManager events; HAM metadata (LIS_* constants)
- Downstream:
  - Status metrics: `metrics.lis` (recent counts)
  - Knowledge graph lineage (future)
- Risks: data sparsity; correctness of filters. Mitigation: mock/replay datasets; tests for filters/time windows.

## 4) Service Discovery & TrustManager
- Upstream: HSP capability advertisements; Trust initialization
- Downstream:
  - DialogueManager target selection; routing policy
  - Learning loops (reward signals via Trust)
- Risks: stale capabilities; misaligned thresholds. Mitigation: staleness cleanup; document min_trust.

## 5) HSP/MCP Connectors & Fallback
- Upstream: MQTT configs; fallback init
- Downstream:
  - Status `hsp/mcp` connectivity & resilience KPIs
  - Blue/green reload sequence
- Risks: inconsistent topic subscriptions; fallback state drift. Mitigation: standardize subscribe lists; expose breaker/retry counters.

## 6) DialogueManager Audit / Backtracking / Staging
- Upstream: audit rules, secondary evaluation
- Downstream:
  - Policy events into HAM; Trust/routing updates
  - User-visible latency; safety guarantees
- Risks: latency increase; over-triggered audits. Mitigation: scope to critical paths; sampling; flags.

## 7) Observability & Dashboard
- Upstream: status metrics producers (1–6)
- Downstream:
  - Frontend dashboard panels; health SLOs
- Risks: nulls & schema evolution. Mitigation: optional fields; versioned dashboard schema.

## 8) Desktop App Plans
- Upstream: API availability & stability
- Downstream:
  - UX reliability; tracing user flows to status signals
- Risks: mismatch with backend changes. Mitigation: contract tests; deprecation notices in docs.

## Sequencing (Suggested)
1) Implement ToolDispatcher logging → surface learning.tools in status → update Observability examples
2) LIS E2E minimal demo → add lis metrics → tests
3) Dialogue audit/backtracking hooks behind flags → robustness metrics
4) Expand resilience KPIs (breaker/retries/reload events)

## References
- TECHNICAL_ROADMAP.md §2.4/2.5
- PERCEPTION_ACTION_FEEDBACK_PLAN.md
- ROBUSTNESS_AND_SAFETY_HARDENING_PLAN.md
- AGI_AND_DATA_LIFE_IMPLEMENTATION_PLAN.md
- docs/05-development/observability-guide.md
- docs/05-development/hot-reload-and-drain.md