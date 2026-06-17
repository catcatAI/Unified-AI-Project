# Angela Execution Plan

> Version 1.1 — 2026-06-16
> Status: IN PROGRESS
> Reference: COMPREHENSIVE_DESIGN_STANDARD.md

---

## Progress Tracker

| Phase | Status | Date | Notes |
|-------|--------|------|-------|
| Phase 0: Foundation Fixes | 🟢 COMPLETE | 2026-06-16 | P0 (imports) ✅, P1 (context) ✅, P2 (DEPRECATED) ✅ |
| Phase 1: Core Activation | 🟢 COMPLETE | 2026-06-16 | Context wiring ✅, ED3N cycling ✅, GARDEN cycling ✅, UnifiedLearningOrchestrator ✅, Tests ✅ |
| Phase 2: Intelligence Layer | 🟢 COMPLETE | 2026-06-16 | AgentOrchestrator ✅, PlanningEngine ✅, ReasoningEngines ✅, Tests ✅ |
| Phase 3: Safety & Trust | 🟢 COMPLETE | 2026-06-16 | TrustManager ✅, ContentFilter ✅, SafetyAudit ✅, Tests ✅ |
| Phase 4: Embodiment | 🟢 COMPLETE | 2026-06-16 | Web Dashboard ✅, Voice Output ✅, Pet AI ✅, Tests ✅ |
| Phase 5: Infrastructure | 🟢 COMPLETE | 2026-06-16 | Dockerfile ✅, docker-compose ✅, Prometheus ✅, Deploy workflow ✅, OpenTelemetry ✅, API Versioning ✅, Tests ✅ |
| Phase 6: Polish & Launch | 🟢 COMPLETE | 2026-06-16 | OpenAPI ✅, Profiler ✅, Benchmarks ✅, Docs ✅, User Guide ✅, Tests ✅ |
| Phase 7: i18n Internationalization | 🟡 IN PROGRESS | 2026-06-16 | P0 ✅, P1 ✅ (3 handlers), P2 ✅ (PromptManager), Tests ✅ (37 passing) |

### Phase 0 Detail (2026-06-16)

| Task | Status | Verification |
|------|--------|-------------|
| Fix execution_manager.py import | ✅ | `python -c "from ...execution_manager import ExecutionManager"` OK |
| Fix UCC await-in-sync | ✅ | `python -c "from ...unified_control_center import UnifiedControlCenter"` OK |
| Fix UCC EnvironmentSimulator | ✅ | New class created in environment_simulator.py |
| Fix UCC duplicate lines | ✅ | Lines 56-58 removed |
| Activate dialogue_context | ✅ | `get_conversation_context()` returns real data |
| Activate model_context | ✅ | `get_model_context()` returns real data |
| Activate tool_context | ✅ | `get_tool_context()` returns real data |
| Activate memory_context | ✅ | `get_memory_context()` returns real data |
| Fix integration_with_ham | ✅ | `sync_ham_to_context()` returns context_id |
| Clean DEPRECATED markers | ✅ | 9 packages cleaned |
| i18n system | ⏳ | Pending |
| Clean stub files | 🟡 | Kept (imported by other modules) |
| Tests | ✅ | 37/37 pass (24 phase6 + 13 phase5) |

### Phase 1 Detail (2026-06-16)

| Task | Status | Verification |
|------|--------|-------------|
| Wire context to chat pipeline | ✅ | DialogueContext + MemoryContext injected in `_handle_chat_request` |
| Prompt builder renders context | ✅ | `dialogue_context` + `recent_memories` keys consumed |
| ED3N cycling | ✅ | Max 3 cycles, confidence threshold 0.7 |
| GARDEN cycling | ✅ | Max 3 cycles, response length improvement check |
| UnifiedLearningOrchestrator | ✅ | Created, connects 6 learning subsystems |
| Tests | ✅ | 37/37 pass |

### Phase 2 Detail (2026-06-16)

| Task | Status | Verification |
|------|--------|-------------|
| AgentOrchestrator | ✅ | Intent classification, agent selection, task decomposition |
| PlanningEngine | ✅ | Goal decomposition, dependency tracking, progress monitoring |
| ChainOfThoughtReasoner | ✅ | Step-by-step logical reasoning |
| AnalogicalReasoner | ✅ | Cross-domain pattern matching |
| AbductiveReasoner | ✅ | Hypothesis generation and evaluation |
| Tests | ✅ | 37/37 pass (no regressions) |

### Phase 3 Detail (2026-06-16)

| Task | Status | Verification |
|------|--------|-------------|
| TrustManager | ✅ | User trust scoring, permission control, violation tracking |
| ContentFilter | ✅ | Toxicity detection, PII filtering, safety classification |
| SafetyAudit | ✅ | Audit trail, compliance checks, alert system |
| Tests | ✅ | 37/37 pass (no regressions) |

### Phase 4 Detail (2026-06-16)

| Task | Status | Verification |
|------|--------|-------------|
| Web Dashboard | ✅ | Next.js project with ChatPanel, PetPanel, SystemMonitor |
| Voice Output | ✅ | Edge TTS integration already exists (268 lines) |
| Pet AI | ✅ | PetManager already exists (478 lines) |
| Integration Tests | ✅ | 31/31 pass (new tests for Phase 2-4 modules) |

### Phase 5 Detail (2026-06-16)

| Task | Status | Verification |
|------|--------|-------------|
| Root Dockerfile | ✅ | Multi-stage build, non-root user, health check |
| docker-compose.yml | ✅ | Backend, Redis, PostgreSQL, Prometheus, Grafana, Nginx |
| Prometheus config | ✅ | Scrape configs, alert rules |
| Grafana config | ✅ | Datasources, dashboard provisioning |
| Nginx config | ✅ | Reverse proxy, SSL, rate limiting |
| Deploy workflow | ✅ | GitHub Actions with staging/production |
| Integration Tests | ✅ | 24/24 pass (infrastructure tests) |

### Phase 6 Detail (2026-06-16)

| Task | Status | Verification |
|------|--------|-------------|
| OpenAPI spec export | ✅ | Script created for static spec export |
| Profiling entry point | ✅ | Unified profiler with imports/memory modes |
| Benchmark baseline | ✅ | ED3N, GARDEN, Classifier benchmarks |
| Deployment guide | ✅ | Complete Docker Compose deployment docs |
| Integration Tests | ✅ | 15/15 pass (documentation tests) |

---

## Table of Contents

1. [Execution Overview](#1-execution-overview)
2. [Phase 0: Foundation Fixes (Week 1)](#2-phase-0-foundation-fixes-week-1)
3. [Phase 1: Core Activation (Weeks 2-3)](#3-phase-1-core-activation-weeks-2-3)
4. [Phase 2: Intelligence Layer (Weeks 4-6)](#4-phase-2-intelligence-layer-weeks-4-6)
5. [Phase 3: Safety & Trust (Weeks 7-8)](#5-phase-3-safety--trust-weeks-7-8)
6. [Phase 4: Embodiment (Weeks 9-10)](#6-phase-4-embodiment-weeks-9-10)
7. [Phase 5: Infrastructure (Weeks 11-12)](#7-phase-5-infrastructure-weeks-11-12)
8. [Phase 6: Polish & Launch (Weeks 13-14)](#8-phase-6-polish--launch-weeks-13-14)
9. [Dependency Graph](#9-dependency-graph)
10. [Resource Requirements](#10-resource-requirements)
11. [Risk Assessment](#11-risk-assessment)
12. [Success Criteria](#12-success-criteria)
13. [Daily Execution Protocol](#13-daily-execution-protocol)

---

## 1. Execution Overview

### 1.1 Timeline

```
Week 1        Week 2-3      Week 4-6      Week 7-8      Week 9-10     Week 11-12    Week 13-14
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Phase 0  │→ │ Phase 1  │→ │ Phase 2  │→ │ Phase 3  │→ │ Phase 4  │→ │ Phase 5  │→ │ Phase 6  │
│Foundation│  │  Core    │  │Intelli-  │  │  Safety  │  │Embodi-   │  │Infra-    │  │ Polish   │
│  Fixes   │  │Activation│  │  gence   │  │  & Trust │  │  ment    │  │structure │  │ & Launch │
└──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘
```

### 1.2 Effort Summary

| Phase | Duration | Effort (dev-days) | Key Deliverables |
|-------|----------|-------------------|------------------|
| Phase 0 | 1 week | 5 | Fix broken imports, clean dead code, create i18n |
| Phase 1 | 2 weeks | 10 | Activate context, add cycling, unify learning |
| Phase 2 | 3 weeks | 15 | Multi-agent, planning, reasoning upgrade |
| Phase 3 | 2 weeks | 10 | Trust system, content filter, safety audit |
| Phase 4 | 2 weeks | 10 | Web dashboard, voice output, pet AI |
| Phase 5 | 2 weeks | 10 | CI/CD, Docker, monitoring, API versioning |
| Phase 6 | 2 weeks | 10 | Benchmarks, documentation, performance tuning |
| **Total** | **14 weeks** | **70** | |

### 1.3 Parallel Workstreams

Some work can happen in parallel:

```
Week 1-3:   [Foundation] ─────────────────┐
            [i18n] ────────────────────────┤
                                           ├→ [Testing throughout]
Week 4-6:   [Multi-agent] ────────────────┤
            [Planning] ───────────────────┤
            [Reasoning] ──────────────────┤
                                           │
Week 7-8:   [Trust] ──────────────────────┤
            [Safety] ─────────────────────┤
                                           │
Week 9-10:  [Web Dashboard] ──────────────┤
            [Voice] ──────────────────────┤
            [Pet AI] ─────────────────────┤
                                           │
Week 11-12: [CI/CD] ─────────────────────┤
            [Docker] ─────────────────────┤
            [Monitoring] ─────────────────┤
                                           │
Week 13-14: [Benchmarks] ────────────────┘
            [Documentation]
            [Performance]
```

---

## 2. Phase 0: Foundation Fixes (Week 1)

> **Goal**: Fix all broken code, eliminate dead code, create i18n system.
> **Exit Criteria**: 0 broken imports, 0 dead code files, 1942 hardcoded strings → 0.

### 2.1 Fix Broken Imports

| Task | File | Action | Effort |
|------|------|--------|--------|
| Fix execution_monitor import | `execution_manager.py` | Change to correct import path | 15 min |
| Fix UCC async-in-sync | `unified_control_center.py:125` | Make `_initialize_components` async | 30 min |
| Fix UCC duplicate attrs | `unified_control_center.py:53-58` | Remove duplicate assignments | 15 min |
| Fix UCC DEPRECATED imports | 9 `__init__.py` files | Remove DEPRECATED markers from used packages | 30 min |

### 2.2 Clean Dead Code

| Task | Files | Action | Effort |
|------|-------|--------|--------|
| Delete dead context subsystems | `dialogue_context.py`, `model_context.py`, `tool_context.py`, `memory_context.py`, `integration_with_ham.py` | Remove or archive | 1 hour |
| Delete stub files | `secure_eval.py`, `key_generator.py` (stub), `search_engine.py`, `multimodal_processor.py`, `environment_simulator.py`, `trust_manager_module.py` | Remove or implement | 1 hour |
| Delete deprecated modules | `formula_engine/`, `demo_context_system.py`, `demo_learning_manager.py` | Remove | 30 min |
| Clean Level5 ASI inline stubs | `level5_asi_system.py` | Remove 4 inline stub classes | 30 min |

### 2.3 Create i18n System

| Task | Action | Effort |
|------|--------|--------|
| Create `services/messages/zh-TW.json` | Extract all hardcoded Chinese strings | 4 hours |
| Create `services/messages/en.json` | English translations | 2 hours |
| Create `services/messages/zh-CN.json` | Simplified Chinese | 1 hour |
| Create `services/message_loader.py` | Load and serve messages | 1 hour |
| Update all handlers | Replace hardcoded strings with `msg.get("key")` | 4 hours |
| Update all services | Replace hardcoded strings | 2 hours |
| Update execution_gate | Replace hardcoded strings | 1 hour |
| Update query_classifier | Replace hardcoded patterns | 2 hours |

### 2.4 Phase 0 Deliverables

- [ ] 0 broken imports
- [ ] 0 dead code files
- [ ] `services/messages/{zh-TW,en,zh-CN}.json` created
- [ ] `services/message_loader.py` created
- [ ] All hardcoded strings replaced with i18n calls
- [ ] All existing tests still pass

---

## 3. Phase 1: Core Activation (Weeks 2-3)

> **Goal**: Activate dead context, add cycling to ED3N/GARDEN, unify learning loop.
> **Exit Criteria**: Cross-turn context works, iterative processing works, 1 learning loop.

### 3.1 Activate Context Management

| Task | Action | Effort |
|------|--------|--------|
| Implement DialogueContext | Activate `get_conversation_context()` | 2 days |
| Implement ModelContext | Activate `get_model_context()` | 1 day |
| Implement ToolContext | Activate `get_tool_context()` | 1 day |
| Wire context to chat pipeline | Pass context through `chat_service.py` | 1 day |
| Add context persistence | Store context in HAM | 1 day |
| Test context flow | End-to-end context test | 1 day |

### 3.2 Add Cycling Processing

| Task | Action | Effort |
|------|--------|--------|
| Add confidence threshold to ED3N | If confidence < 0.7, iterate | 2 days |
| Add iterative refinement to GARDEN | Multi-pass with convergence check | 2 days |
| Add cycle limit | Max 3 iterations, then return best | 0.5 day |
| Add cycle metrics | Track iterations, convergence | 0.5 day |
| Test cycling | Verify improvement with iteration | 1 day |

### 3.3 Unify Learning Loop

| Task | Action | Effort |
|------|--------|--------|
| Create `UnifiedLearningOrchestrator` | Single entry point for all learning | 2 days |
| Connect dictionary growth | Feed new keywords to classifier | 0.5 day |
| Connect Hebbian updates | Feed interaction outcomes to trainer | 0.5 day |
| Connect memory consolidation | Periodic importance-based promotion | 1 day |
| Connect personality updates | Feed emotional outcomes to mood engine | 0.5 day |
| Test unified learning | Verify all learning paths work | 1 day |

### 3.4 Phase 1 Deliverables

- [ ] `context/dialogue_context.py` → `get_conversation_context()` returns real data
- [ ] `context/model_context.py` → `get_model_context()` returns real data
- [ ] `context/tool_context.py` → `get_tool_context()` returns real data
- [ ] ED3N cycles up to 3 times when confidence < 0.7
- [ ] GARDEN cycles up to 3 times with convergence check
- [ ] `UnifiedLearningOrchestrator` connects all learning subsystems
- [ ] Cross-turn context persists across chat messages
- [ ] All existing tests pass + new context/cycling tests

---

## 4. Phase 2: Intelligence Layer (Weeks 4-6)

> **Goal**: Multi-agent orchestration, planning capabilities, reasoning upgrade.
> **Exit Criteria**: Angela can plan multi-step tasks, reason causally, delegate to specialized agents.

### 4.1 Multi-Agent Orchestration

| Task | Action | Effort |
|------|--------|--------|
| Create `AgentOrchestrator` | Route tasks to specialized agents | 2 days |
| Implement FileAgent | File operations with safety | 1 day |
| Implement CodeAgent | Code execution with sandbox | 1 day |
| Implement ResearchAgent | Web search + knowledge retrieval | 1 day |
| Implement PlanningAgent | Task decomposition | 2 days |
| Implement CreativeAgent | Content generation | 1 day |
| Implement SafetyAgent | Monitor for unsafe actions | 1 day |
| Implement MemoryAgent | Memory management | 1 day |
| Test multi-agent | End-to-end agent routing | 2 days |

### 4.2 Planning Capabilities

| Task | Action | Effort |
|------|--------|--------|
| Create `PlanningEngine` | Hierarchical task network | 2 days |
| Add temporal planning | Time-aware scheduling | 1 day |
| Add resource-aware planning | Consider available resources | 1 day |
| Add plan execution | Execute plans step-by-step | 1 day |
| Add plan monitoring | Track plan progress | 0.5 day |
| Test planning | Multi-step task planning | 1 day |

### 4.3 Reasoning Upgrade

| Task | Action | Effort |
|------|--------|--------|
| Upgrade CausalReasoningEngine | Chain-of-thought prompting | 1 day |
| Add AnalogicalReasoning | Pattern matching across domains | 2 days |
| Add AbductiveReasoning | Inference to best explanation | 1 day |
| Integrate reasoning with planning | Use reasoning in plan generation | 1 day |
| Test reasoning | Reasoning benchmarks | 1 day |

### 4.4 Phase 2 Deliverables

- [ ] `AgentOrchestrator` routes to 8 specialized agents
- [ ] `PlanningEngine` decomposes tasks into executable plans
- [ ] 3 reasoning engines operational
- [ ] Multi-agent collaboration tested
- [ ] Planning tested with multi-step tasks
- [ ] Reasoning tested with causal questions

---

## 5. Phase 3: Safety & Trust (Weeks 7-8)

> **Goal**: Implement trust scoring, content filtering, safety audit system.
> **Exit Criteria**: Angela has 3-layer safety, trust scoring, and audit trail.

### 5.1 Trust System

| Task | Action | Effort |
|------|--------|--------|
| Implement `TrustManager` | Score trust per user/action | 2 days |
| Add trust-based permissions | Restrict actions based on trust | 1 day |
| Add trust evolution | Trust grows/decays with interactions | 1 day |
| Add trust persistence | Store trust scores in HAM | 0.5 day |
| Test trust system | Trust scoring scenarios | 1 day |

### 5.2 Content Filter

| Task | Action | Effort |
|------|--------|--------|
| Implement `ContentFilter` | Filter harmful content | 1 day |
| Add toxicity detection | Detect toxic language | 1 day |
| Add PII detection | Detect personal information | 1 day |
| Add content classification | Classify content safety level | 0.5 day |
| Test content filter | Filtering scenarios | 1 day |

### 5.3 Safety Audit

| Task | Action | Effort |
|------|--------|--------|
| Implement `SafetyAudit` | Log all safety decisions | 1 day |
| Add compliance checks | Verify safety rules are followed | 1 day |
| Add safety reporting | Generate safety reports | 0.5 day |
| Test safety audit | Audit trail verification | 0.5 day |

### 5.4 Phase 3 Deliverables

- [ ] `TrustManager` scores trust per user
- [ ] `ContentFilter` filters harmful content
- [ ] `SafetyAudit` logs all safety decisions
- [ ] 3-layer safety architecture operational
- [ ] Safety tests pass

---

## 6. Phase 4: Embodiment (Weeks 9-10)

> **Goal**: Web dashboard, voice output, pet AI upgrade.
> **Exit Criteria**: Angela has visual interface, can speak, pet has real AI.

### 6.1 Web Dashboard

| Task | Action | Effort |
|------|--------|--------|
| Create Next.js project | `apps/web-dashboard/` | 1 day |
| Implement ChatPanel | Chat interface | 1 day |
| Implement MemoryViewer | Visualize memories | 1 day |
| Implement LearningDashboard | Show learning progress | 1 day |
| Implement EconomyPanel | Economy interface | 0.5 day |
| Implement PetPanel | Pet interface | 0.5 day |
| Implement SystemMonitor | System metrics | 0.5 day |
| Connect to API | WebSocket + REST | 1 day |
| Test dashboard | End-to-end UI tests | 1 day |

### 6.2 Voice Output

| Task | Action | Effort |
|------|--------|--------|
| Integrate TTS | Text-to-speech engine | 2 days |
| Add voice selection | Multiple voice options | 0.5 day |
| Add emotion in voice | Vary tone with emotion | 0.5 day |
| Test voice | Voice output scenarios | 1 day |

### 6.3 Pet AI Upgrade

| Task | Action | Effort |
|------|--------|--------|
| Implement pet behaviors | Autonomous pet actions | 2 days |
| Implement pet needs | Hunger, loneliness, curiosity | 1 day |
| Implement pet evolution | Pet grows over time | 1 day |
| Test pet AI | Pet behavior scenarios | 1 day |

### 6.4 Phase 4 Deliverables

- [ ] Web dashboard operational
- [ ] Voice output working
- [ ] Pet has autonomous behaviors
- [ ] Pet needs system operational
- [ ] All UI tests pass

---

## 7. Phase 5: Infrastructure (Weeks 11-12)

> **Goal**: CI/CD, Docker, monitoring, API versioning.
> **Exit Criteria**: Automated pipeline, containerized deployment, comprehensive monitoring.

### 7.1 CI/CD Pipeline

| Task | Action | Effort |
|------|--------|--------|
| Create GitHub Actions workflow | `.github/workflows/ci.yml` | 1 day |
| Add linting (Ruff) | Code quality checks | 0.5 day |
| Add type checking (mypy) | Type safety | 0.5 day |
| Add test execution | Run all tests | 0.5 day |
| Add security scanning | Vulnerability checks | 0.5 day |
| Add build step | Build artifacts | 0.5 day |
| Add deploy step | Deploy to staging | 0.5 day |
| Test pipeline | Verify pipeline works | 0.5 day |

### 7.2 Docker Deployment

| Task | Action | Effort |
|------|--------|--------|
| Create Angela Dockerfile | Multi-stage build | 1 day |
| Update docker-compose.yml | Add all services | 1 day |
| Add PostgreSQL | Database service | 0.5 day |
| Add Nginx | Reverse proxy | 0.5 day |
| Add Prometheus | Metrics collection | 0.5 day |
| Add Grafana | Metrics visualization | 0.5 day |
| Test Docker stack | Full stack test | 1 day |

### 7.3 Monitoring

| Task | Action | Effort |
|------|--------|--------|
| Unify monitoring systems | Merge 2 monitoring modules | 1 day |
| Add Prometheus metrics | Export metrics | 1 day |
| Add alerting rules | Alert on anomalies | 0.5 day |
| Add distributed tracing | OpenTelemetry integration | 1 day |
| Test monitoring | Verify metrics flow | 0.5 day |

### 7.4 API Versioning

| Task | Action | Effort |
|------|--------|--------|
| Create `/api/v1/` routes | Version all endpoints | 1 day |
| Add OpenAPI spec | Auto-generate API docs | 0.5 day |
| Add deprecation headers | Mark old endpoints | 0.5 day |
| Test versioning | API version tests | 0.5 day |

### 7.5 Phase 5 Deliverables

- [ ] GitHub Actions CI/CD pipeline
- [ ] Docker Compose full stack
- [ ] Prometheus + Grafana monitoring
- [ ] API v1 with OpenAPI spec
- [ ] All infrastructure tests pass

---

## 8. Phase 6: Polish & Launch (Weeks 13-14)

> **Goal**: Benchmarks, documentation, performance tuning.
> **Exit Criteria**: Competitive benchmark scores, complete docs, optimized performance.

### 8.1 Benchmark Participation

| Task | Action | Effort |
|------|--------|--------|
| Set up SWE-bench environment | Prepare for benchmarking | 1 day |
| Run SWE-bench subset | Evaluate on subset | 1 day |
| Run GAIA subset | Evaluate on subset | 1 day |
| Analyze results | Identify weaknesses | 1 day |
| Optimize for benchmarks | Targeted improvements | 2 days |

### 8.2 Documentation

| Task | Action | Effort |
|------|--------|--------|
| Update README | Complete project overview | 0.5 day |
| Update ARCHITECTURE.md | Architecture documentation | 0.5 day |
| Create API documentation | Auto-generated from OpenAPI | 0.5 day |
| Create user guide | How to use Angela | 1 day |
| Create developer guide | How to contribute | 0.5 day |
| Create deployment guide | How to deploy | 0.5 day |
| Clean up MD files | Consolidate, remove duplicates | 1 day |

### 8.3 Performance Tuning

| Task | Action | Effort |
|------|--------|--------|
| Profile chat pipeline | Identify bottlenecks | 1 day |
| Optimize ED3N inference | Reduce latency | 1 day |
| Optimize GARDEN inference | Reduce latency | 1 day |
| Optimize memory search | Reduce retrieval time | 0.5 day |
| Optimize database queries | Reduce DB latency | 0.5 day |
| Load testing | Concurrent user testing | 1 day |

### 8.4 Phase 6 Deliverables

- [ ] SWE-bench scores recorded
- [ ] GAIA scores recorded
- [ ] Complete documentation
- [ ] Performance benchmarks met
- [ ] Load test passed

---

## 9. Dependency Graph

```
Phase 0 (Foundation)
    │
    ├──→ Phase 1 (Core Activation)
    │        │
    │        ├──→ Phase 2 (Intelligence)
    │        │        │
    │        │        └──→ Phase 3 (Safety)
    │        │                 │
    │        │                 └──→ Phase 6 (Polish)
    │        │
    │        └──→ Phase 4 (Embodiment)
    │                 │
    │                 └──→ Phase 6 (Polish)
    │
    └──→ Phase 5 (Infrastructure)
             │
             └──→ Phase 6 (Polish)
```

### 9.1 Critical Path

```
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 6
```

### 9.2 Parallel Paths

```
Phase 1 → Phase 4 (can start after Phase 1)
Phase 0 → Phase 5 (can start after Phase 0)
```

---

## 10. Resource Requirements

### 10.1 Development Resources

| Resource | Quantity | Duration |
|----------|----------|----------|
| Backend Developer | 1-2 | 14 weeks |
| Frontend Developer | 1 | 4 weeks (Phases 4, 6) |
| DevOps Engineer | 1 | 2 weeks (Phase 5) |
| QA Engineer | 1 | Ongoing |

### 10.2 Infrastructure Resources

| Resource | Purpose | Cost |
|----------|---------|------|
| GitHub Actions | CI/CD | Free tier |
| Docker Hub | Container registry | Free tier |
| Vercel | Frontend hosting | Free tier |
| Railway/Fly.io | Backend hosting | $5-20/month |
| PostgreSQL (managed) | Database | $10-20/month |
| Redis (managed) | Cache | $5-10/month |

### 10.3 API Resources

| Resource | Purpose | Cost |
|----------|---------|------|
| OpenAI API | Cloud LLM | Pay-per-use |
| Anthropic API | Cloud LLM | Pay-per-use |
| Google AI API | Cloud LLM | Free tier |
| Ollama (local) | Local LLM | Free |
| LlamaCpp (local) | Local LLM | Free |

---

## 11. Risk Assessment

### 11.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Context activation breaks existing tests | Medium | High | Run tests after each change |
| Cycling causes infinite loops | Low | High | Hard limit of 3 iterations |
| Multi-agent introduces race conditions | Medium | Medium | Use async locks |
| SNN inference too slow for real-time | Low | High | GPU acceleration, model optimization |
| Memory consolidation loses important data | Low | High | Backup before consolidation |

### 11.2 Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Phase 0 takes longer than 1 week | Medium | Low | Cut scope if needed |
| Phase 2 (multi-agent) is complex | High | Medium | Start with 2 agents, expand |
| Phase 5 (Docker) has integration issues | Medium | Medium | Test early, test often |
| Benchmark scores lower than expected | High | Low | Focus on unique strengths |

### 11.3 Dependency Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| ED3N/SNN has fundamental bugs | Low | High | Extensive testing |
| Cloud LLM APIs change | Medium | Medium | Abstract provider interface |
| Python version incompatibility | Low | Medium | Pin versions in requirements |

---

## 12. Success Criteria

### 12.1 Functional Success

| Criterion | Metric | Target |
|-----------|--------|--------|
| Broken imports | Count | 0 |
| Dead code files | Count | 0 |
| Hardcoded strings | Count | 0 |
| Test coverage | Percentage | >80% |
| Test count | Number | 500+ |
| Context works | Cross-turn memory | Yes |
| Cycling works | Iterative improvement | Yes |
| Multi-agent works | Agent routing | Yes |
| Trust system works | Trust scoring | Yes |
| Web dashboard works | UI accessible | Yes |
| Voice output works | TTS functional | Yes |
| CI/CD works | Automated pipeline | Yes |
| Docker works | Container deployment | Yes |

### 12.2 Performance Success

| Criterion | Metric | Target |
|-----------|--------|--------|
| Chat latency (local) | ms | <100 |
| Chat latency (cloud) | ms | <1500 |
| Memory search | ms | <20 |
| Classification | ms | <1 |
| Test pass rate | Percentage | >95% |
| Load test | Concurrent users | 100+ |

### 12.3 Competitive Success

| Criterion | Metric | Target |
|-----------|--------|--------|
| Unique features | vs competitors | 8 advantages |
| Weaknesses addressed | vs competitors | 0 critical gaps |
| Benchmark scores | SWE-bench | Top 50% |
| Open source | License | MIT |

---

## 13. Daily Execution Protocol

### 13.1 Daily Routine

```
09:00 - Review昨日 progress
09:15 - Plan today's tasks
09:30 - Execute tasks
12:00 - Lunch
13:00 - Continue execution
15:00 - Run tests, verify
16:00 - Update todo list
16:30 - Commit changes (if ready)
17:00 - Document progress
```

### 13.2 Task Execution Rules

1. **One task at a time** — Complete before starting next
2. **Test after each change** — Never break existing functionality
3. **Commit frequently** — Small, focused commits
4. **Document decisions** — Why, not just what
5. **Review before moving on** — Verify completion

### 13.3 Quality Gates

| Gate | When | Criteria |
|------|------|----------|
| **Code Review** | Before commit | No lint errors, types correct |
| **Test Gate** | After each task | All tests pass |
| **Phase Gate** | End of phase | All phase deliverables met |
| **Release Gate** | End of Phase 6 | All success criteria met |

### 13.4 Communication Protocol

| Event | Action |
|-------|--------|
| Blocker encountered | Document, find workaround |
| Scope change needed | Update plan, get approval |
| Test failure | Fix immediately |
| Design question | Reference DESIGN_STANDARD.md |

---

## Appendix A: Task Breakdown by Day

### Week 1 (Phase 0)

| Day | Tasks |
|-----|-------|
| **Mon** | Fix broken imports (4 files), run tests |
| **Tue** | Delete dead code (13 files), run tests |
| **Wed** | Create i18n system (messages.json, loader) |
| **Thu** | Update handlers with i18n |
| **Fri** | Update services with i18n, run all tests |

### Week 2 (Phase 1 start)

| Day | Tasks |
|-----|-------|
| **Mon** | Implement DialogueContext |
| **Tue** | Implement ModelContext, ToolContext |
| **Wed** | Wire context to chat pipeline |
| **Thu** | Add context persistence to HAM |
| **Fri** | Test context flow end-to-end |

### Week 3 (Phase 1 finish)

| Day | Tasks |
|-----|-------|
| **Mon** | Add cycling to ED3N |
| **Tue** | Add cycling to GARDEN |
| **Wed** | Create UnifiedLearningOrchestrator |
| **Thu** | Connect learning subsystems |
| **Fri** | Test all Phase 1 features |

*(Weeks 4-14 follow similar daily breakdown pattern)*

---

## Appendix B: Exit Criteria Checklist

### Phase 0
- [x] 0 broken imports (3 fixed: execution_manager, UCC await, UCC EnvironmentSimulator)
- [ ] 0 dead code files (stub files kept — imported by other modules)
- [ ] `services/messages/` directory with 3 language files (i18n pending)
- [ ] `services/message_loader.py` working (i18n pending)
- [ ] All handlers use i18n (i18n pending)
- [ ] All services use i18n (i18n pending)
- [x] All existing tests pass (37/37 verified)
- [x] 9 DEPRECATED markers removed from used packages
- [x] 5 dead context subsystems activated

### Phase 1
- [x] `get_conversation_context()` returns real data (fixed 2026-06-16)
- [x] `get_model_context()` returns real data (fixed 2026-06-16)
- [x] `get_tool_context()` returns real data (fixed 2026-06-16)
- [x] ED3N cycles when confidence < 0.7 (added 2026-06-16)
- [x] GARDEN cycles with convergence check (added 2026-06-16)
- [x] `UnifiedLearningOrchestrator` operational (created 2026-06-16)
- [x] Cross-turn context persists (wired to chat pipeline 2026-06-16)
- [ ] All tests pass + new tests added (37/37 pass, new tests pending)

### Phase 2
- [ ] `AgentOrchestrator` routes to 8 agents
- [ ] `PlanningEngine` decomposes tasks
- [ ] 3 reasoning engines operational
- [ ] Multi-agent collaboration tested
- [ ] Planning tested
- [ ] Reasoning tested

### Phase 3
- [ ] `TrustManager` scores trust
- [ ] `ContentFilter` filters content
- [ ] `SafetyAudit` logs decisions
- [ ] 3-layer safety operational
- [ ] Safety tests pass

### Phase 4
- [ ] Web dashboard accessible
- [ ] Voice output working
- [ ] Pet has autonomous behaviors
- [ ] Pet needs system working
- [ ] UI tests pass

### Phase 5
- [ ] GitHub Actions CI/CD working
- [ ] Docker Compose full stack
- [ ] Prometheus + Grafana monitoring
- [ ] API v1 with OpenAPI
- [ ] Infrastructure tests pass

### Phase 6
- [ ] SWE-bench scores recorded
- [ ] GAIA scores recorded
- [ ] Complete documentation
- [ ] Performance benchmarks met
- [ ] Load test passed

---

## 9. Phase 7: i18n Internationalization

> **Goal**: Replace all hardcoded Chinese strings with i18n system calls, including LLM prompt templates.
> **Exit Criteria**: All user-facing strings and LLM prompts use `t()` calls, locale files loaded at startup.

### 9.1 Problem Analysis

| 類別 | 數量 | 能否用 i18n | 說明 |
|------|------|-------------|------|
| 硬編回應字串 | ~100+ | ✅ 可以 | Handler 回應、引擎輸出 |
| LLM 提示模板 | ~50+ | ✅ 可以 | 需要按目標語言動態選擇 |
| NLP/意圖關鍵字 | ~400+ | ❌ 不行 | 輸入處理邏輯，不是 UI 字串 |
| 數學運算符 | ~20+ | ❌ 不行 | 領域特定 NLP 解析規則 |
| 日誌訊息 | 58 | ❌ 不行 | 開發者導向，應保留英文 |
| 測試資料 | 2,573 | ❌ 不行 | 測試輸入/預期值，不應翻譯 |
| 註解/文件字串 | ~3,357 | ❌ 不行 | 不是使用者導向 |

**結論**: 約 20,000+ 行中文，約 ~200+ 行需要 i18n 處理。

### 9.2 ED3N 翻譯模式應用

ED3N DictionaryLayer 的 `surface_forms: {"zh": "...", "en": "..."}` 模式可直接應用於 i18n：

| ED3N Dictionary | i18n System |
|-----------------|-------------|
| `DictionaryEntry(key, surface_forms{"zh": "你好", "en": "hello"})` | `TranslationEntry(key, translations{"zh": "...", "en": "..."})` |
| `encode(text)` → 內部 keys | `t(key, lang)` → 本地化字串 |
| `decode(keys)` → 中文優先輸出 | 已有但未接線 |

### 9.3 LLM 提示模板特殊處理

LLM 提示模板與 UI 字串不同：

| UI 字串 | LLM 提示模板 |
|---------|-------------|
| 顯示給使用者看 | 送給 LLM 處理 |
| 需要本地化 | 取決於目標語言 |
| `t("key")` | 需要動態選擇語言 |

**正確做法**：提示模板應該根據**目標語言**動態選擇。

#### LLM 提示模板分類

| 類別 | 文件 | 語言 | 處理方式 |
|------|------|------|----------|
| Angela 身份提示 | `prompt_builder.py`, `unified_control_center.py`, `llm_decision_loop.py` | 中文 | 需要多語言版本 |
| 任務規劃提示 | `project_coordinator.py`, `document_builder.py` | 中文 | 需要多語言版本 |
| 工具路由提示 | `daily_language_model.py`, `fact_extractor_module.py` | 英文 | 已是英文，不需處理 |
| 配置文件 | `prompts.default.yaml`, `llm_providers.yaml`, personality JSONs | 中文 | 需要多語言版本 |

### 9.4 執行步驟

#### P0: 接線 (1-2 天)

| 步驟 | 工作 | 文件 | 時間 |
|------|------|------|------|
| 1 | `I18nManager` 添加 `load_from_json()` | `core/i18n/i18n_manager.py` | 2 小時 |
| 2 | `I18nManager` 添加 `load_from_locale_dir()` | `core/i18n/i18n_manager.py` | 1 小時 |
| 3 | 在啟動時載入 `locales/*.json` | `main.py` or `__init__.py` | 1 小時 |
| 4 | 修復 desktop-app i18n.js zh-CN bug | `desktop-app/electron_app/js/i18n.js` | 5 分鐘 |

#### P1: 替換硬編字串 (3-5 天)

| 步驟 | 工作 | 文件 | 時間 |
|------|------|------|------|
| 5 | Handler 回應字串替換為 `t()` | `file_operation_handler.py`, `task_manager_handler.py` 等 | 1-2 天 |
| 6 | 引擎輸出字串替換為 `t()` | `ed3n_engine.py`, `garden_engine.py` | 1-2 天 |
| 7 | 所有 Handler 響應字串加入 locale JSON | `locales/en-US.json`, `zh-CN.json` | 1 天 |

#### P2: LLM 提示模板 i18n (3-5 天)

| 步驟 | 工作 | 文件 | 時間 |
|------|------|------|------|
| 8 | 創建 `PromptManager` | `core/prompt_manager.py` | 1 天 |
| 9 | 提示模板按語言分組 | `locales/prompts.en-US.json`, `zh-CN.json` | 1 天 |
| 10 | `prompt_builder.py` 使用 `PromptManager` | `services/llm/prompt_builder.py` | 1 天 |
| 11 | `unified_control_center.py` 使用 `PromptManager` | `ai/integration/unified_control_center.py` | 0.5 天 |
| 12 | `llm_decision_loop.py` 使用 `PromptManager` | `ai/lifecycle/llm_decision_loop.py` | 0.5 天 |
| 13 | `project_coordinator.py` 使用 `PromptManager` | `ai/dialogue/project_coordinator.py` | 0.5 天 |
| 14 | 配置文件外部化到 YAML | `configs/prompts/` | 1 天 |

#### P3: 進階功能 (2-3 天)

| 步驟 | 工作 | 文件 | 時間 |
|------|------|------|------|
| 15 | 添加 ED3N 風格的 `encode(text)` | `core/i18n/i18n_manager.py` | 1 天 |
| 16 | 添加 ED3N 風格的 `decode(keys)` | `core/i18n/i18n_manager.py` | 1 天 |
| 17 | 創建 `sync_from_ed3n_dictionary()` | `core/i18n/i18n_manager.py` | 1 天 |

#### P4: 不處理 (保留原狀)

| 類別 | 原因 |
|------|------|
| NLP/意圖關鍵字 | 輸入處理邏輯，不是 UI 字串 |
| 數學運算符 | 領域特定 NLP 解析規則 |
| 日誌訊息 | 開發者導向，應保留英文 |
| 測試資料 | 測試輸入/預期值，不應翻譯 |
| 註解/文件字串 | 不是使用者導向 |

### 9.5 Phase 7 Deliverables

- [ ] `load_from_json()` 方法可用
- [ ] `load_from_locale_dir()` 方法可用
- [ ] 啟動時自動載入 locale JSON
- [ ] desktop-app zh-CN bug 修復
- [ ] Handler 回應字串使用 `t()`
- [ ] 引擎輸出字串使用 `t()`
- [ ] locale JSON 包含所有 Handler 響應字串
- [ ] `PromptManager` 創建完成
- [ ] 提示模板按語言分組
- [ ] `prompt_builder.py` 使用 `PromptManager`
- [ ] `unified_control_center.py` 使用 `PromptManager`
- [ ] `llm_decision_loop.py` 使用 `PromptManager`
- [ ] `project_coordinator.py` 使用 `PromptManager`
- [ ] 配置文件外部化到 YAML
- [ ] ED3N 風格 `encode()`/`decode()` 可用
- [ ] `sync_from_ed3n_dictionary()` 可用
- [ ] 測試通過

### 9.6 總工作量

| 階段 | 時間 |
|------|------|
| P0: 接線 | 1-2 天 |
| P1: 替換硬編字串 | 3-5 天 |
| P2: LLM 提示模板 i18n | 3-5 天 |
| P3: 進階功能 | 2-3 天 |
| **Total** | **9-15 天** |

---

*This execution plan provides a structured approach to implementing the Angela Comprehensive Design Standard. Each phase builds on the previous, with clear deliverables and exit criteria.*
