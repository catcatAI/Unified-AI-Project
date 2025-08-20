# Technical Roadmap (Canonical)

Version: v1.0 (Initial consolidation)
Date: 2025-08-06
Owners: Core Development / Architecture

## 0. Objectives (Why this roadmap)
- Deliver a resilient, evolving AI runtime with hot reload/migration and rich observability.
- Establish a cohesive "Data Life" stack: ingest → transform → memory → retrieval → learn → feedback.
- Advance toward practical AGI behaviors through multi-agent orchestration (HSP), learning loops (LIS/HAM), and safe creation (Sandbox/Tools).

## 1. Current State (Concise)
- Messaging & Orchestration: `HSPConnector` in place with fallback and `ServiceDiscoveryModule`; `DialogueManager` + `ToolDispatcher` integrated; `TrustManager` influences selection.
- Memory & Learning: `HAMMemoryManager` + `LIS` scaffolding with typed metadata; `LearningManager` + `FactExtractorModule` + `ContentAnalyzerModule` present; `TaskExecutionEvaluator` basic.
- Safety & Extensibility: `CreationEngine` + `SandboxExecutor`; hot reload (LLM/tools/personality/`HSPConnector`); drain endpoints.
- Gaps: End-to-end LIS loop; richer observability; durable knowledge graph; stronger evaluation; expanded world modeling.

## 2. Near / Mid / Long Term

### 2.1 Near-term (1–2 sprints)
- Observability (M1)
  - Extend /api/v1/hot/status with HSP/MCP metrics, learning/LIS/HAM summaries.
  - Docs + smoke tests; optional dashboard JSON.
- LIS E2E (M2 - kickoff)
  - Minimal flow: anomaly → incident → antibody → effectiveness eval → upgrade/retire.
  - HAMLISCache query consistency; tests for filters (type/severity/time/tags).
- Hot reload hardening
  - Tool reload accuracy (diff summary), personality reload hook propagation; status surfacing.

### 2.2 Mid-term (2–6 sprints)
- Knowledge structure
  - Lightweight graph over HAM metadata; lineage and causal references for facts/incidents/antibodies.
- Learning & routing
  - Trust- and KPI-informed routing adjustments (models/tools); closed-loop tuning.
- World model & reasoning
  - Minimal causal reasoning hooks; environment simulation stubs aligned with tasks.

### 2.3 Long-term (6+ sprints)
- Fragmenta & meta-learning
  - Task planning cycles with self-critique; meta-formulas beyond placeholders.
- Scalable memory & governance
  - Tiered retention/aging; auditability; privacy controls; drift detection.
- Multi-modal integration
  - Tight integration of vision/audio artifacts into HAM/LIS structures.

## 2.4 Perception–Action–Feedback (Behavioral Closed Loop)

Decision policy (from 114):
- Try internal self-improvement loop first (re-evaluate/audit/backtrack)
- If evidence insufficient or context sparse → pull external data via tools/APIs under cost/latency guardrails

Objective: internalize tool invocation and outcomes into a closed training/feedback loop, so the system learns not only “what to say” but “when and how to act," and how outcomes shape future choices.

Near-term (M1–M2):
- Capture Action–Tool Policy records for every tool call: {tool_name, params_hash, latency, outcome, success(bool), cost, user_context, timestamp} into HAM (metadata keyed, e.g., ham_meta_action_policy_*)
- Surface minimal KPIs in /api/v1/hot/status (metrics.learning/tools): counts, success ratios, recent failures.
- Map success signals to TrustManager deltas; log routing decisions (model/tool) with rationale.

Mid-term:
- Use KPI and Trust deltas to adjust routing policies (models/tools) under guardrails.
- Introduce basic credit assignment for multi-step tasks (link outcomes to prior calls via correlation_id) and summarize back into HAM.

Long-term:
- RLHF/RLAIF-style loops over real tasks: feed structured outcomes into periodic fine-tuning or policy adapters; stabilize via simulation replays.
- Expand to multi-modal actions; include safety constraints as explicit negative rewards.

---

## 2.5 Correctness Strategy & KPIs (from 113.txt insights)

- Approach: "Five-method" stack for high correctness under limited resources:
  - Dynamic context sizing; Input chunking; Multi-mechanism processing
  - Buffered backtracking + Staging area (output validation/correction before user delivery)
  - Dual-system (execution + audit) for critical tasks
- Asynchronous tasks + event-driven interruptions fit FastAPI/Electron architecture and HSP events.
- Toolization for perception-heavy subtasks (e.g., counting/vision) to reduce hallucinations.

KPIs (resource-constrained targets):
- Correctness 95–98% (best 99%), Hallucination 2–5%, Latency 10–18s, Memory <6GB
- Micro-gains without large infra: simple rules engine or external KB (e.g., wiki API) +1–2% (10–15h)

Integration points:
- Audit path invokes secondary check (rules + re-evaluation) and may trigger backtracking; record as new policy event.
- Routing + Trust adjustments gated by guardrails (caps/thresholds) and surfaced in /api/v1/hot/status.

---

## 3. Architectural Pillars (Cross-cutting)
- HSP + Fallback: resilient inter-agent comms; capability ads; correlation-tracked tasks.
- HAM + LIS: typed, queryable memory with incident/antibody lifecycle.
- Creation + Safety: generation via CreationEngine; isolation via SandboxExecutor; hot reload & drain.
- Multi-LLM: provider abstraction; routing policy; explicit cost/latency targets.

## 4. Workstreams & Deliverables
- WS-Observability: enriched status endpoint; docs; test suite; (optional dashboard schema).
- WS-LIS E2E: minimal API/demo; query cohesion; eval-based antibody updates.
- WS-Knowledge Graph: lineage links; simple graph queries atop HAM metadata.
- WS-Routing & Learning: feedback into model/tool selection; trust adjustments with guardrails.
- WS-Safety & Ops: reload blue/green patterns; de-risk migrations with drain + health; error budgets.

## 5. Risks & Mitigations
- Metric overhead → sampling, cached summaries, off-thread aggregation.
- Sparse data for LIS → mock/replay streams; progressive hardening.
- Instability from auto-tuning → gated toggles, staged rollout, quick rollback via hot reload.

## 6. Acceptance Criteria (Phase checkpoints)
- /api/v1/hot/status exposes comms + learning/memory/LIS snapshots; docs and examples match.
- LIS demo shows measureable effectiveness change and queryable history.
- Routing responds to KPI deltas; auditable via logs/status.

## 7. Future Vision (Brief)

Comparative notes (from 115):
- Differentiation: niche-first + ecosystem expansion; toolization; safe operations (hot reload/migration/drain)
- Benchmarking: high-correctness path (audit/backtrack/dual-system) vs AI VTuber (content-first) vs commercial AGI (heavy infra)
- Upgrade path (L3→L4): knowledge write-back, meta-learning, self-task generation (gated by resources)

A continuously-learning, resilient multi-agent system where information has lineage and purpose (Data Life), behaviors adapt under constraints (trust, safety, cost), and capabilities expand safely (creation + sandbox). For deeper vision and philosophy see:
- Philosophy and Vision (planning/philosophy/PHILOSOPHY_AND_VISION.md)
- AGI Concepts (planning/philosophy/agi-concepts.md)

## 8. References
- AGI & Data Life Implementation Plan (planning/project-management/planning-docs/AGI_AND_DATA_LIFE_IMPLEMENTATION_PLAN.md)
- Architecture Deep Dive (planning/core-development/architecture-deep-dive.md)
- LLM Routing & Adaptation (planning/core-development/LLM_ROUTING_AND_ADAPTATION_PLAN.md)
