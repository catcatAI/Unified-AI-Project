# Project Management

> **Version**: 7.5.0-dev | **Status**: Active Development (H5 complete, ~62% maturity)

This section covers project planning, status, and management for the **Angela AI / Unified AI Project** — a hybrid AGI ecosystem with closed-loop learning architecture.

## Active Plan Files

All plans live in `docs/06-project-management/plans/`:

| Plan File | Focus |
|-----------|-------|
| `MASTER_CONSOLIDATED_PLAN.md` | Consolidated master plan — version governance, security, modularization |
| `MASTER_FINALIZATION_PLAN.md` | Finalization roadmap |
| `ED3N_MATURITY_PLAN.md` | ED3N external dictionary decoupling neural network — Phase 1-4 production-readiness |
| `GARDEN_MODEL_PLAN.md` | GARDEN-1G lightweight local model architecture |
| `CARD_IMPORT_PIPELINE_PLAN.md` | Card import pipeline (222+ cards from G-slot) |
| `CARD_INTEGRATION_PLAN_REVIEW.md` | Card integration audit/review |
| `ANGELA_CARD_INTEGRATION_PLAN.md` | Angela card system integration |
| `ANGELA_LLM_SNN_ARCHITECTURE_PLAN.md` | LLM + SNN hybrid architecture |
| `ANGELA_TRANSLATION_LEARNING_PLAN.md` | Translation learning layer |
| `REPAIR_PLAN.md` | Systematic debt/security repair |
| `REMAINING_ISSUES_PLAN.md` | Outstanding issues tracking |
| `TEST_RESTRUCTURE_PLAN.md` | Test suite restructure |
| `PHASE6_NEXT_PLAN.md` | Phase 6 / next sprint planning |
| `PHASE_REVIEW.md` — `PHASE_REVIEW5.md` | Phase review reports (PR1-PR5) |
| `COMPREHENSIVE_AUDIT_REPORT.md` | Full codebase audit (V1-V3) |
| `PLAN_REVIEW.md` | Cross-plan review |

## Development Roadmap (H1-H9)

The project uses **H-level milestones** (not phases). Current status per H-level:

| Level | Focus | Status | Score Target |
|-------|-------|--------|:------------:|
| **H1-H4** | HIGH vulnerability repair + test fixes | ✅ Complete | 51% → 55% |
| **H5** | Stub implementation (36/37 strict stubs, 2837 tests) | ✅ Complete | 55% → 62% |
| **H6** | (Combined into H5/H7) | — | — |
| **H7** | Long file refactoring (132→50 files), doc consistency | 🔴 Active | 62% → 68% |
| **H7.1** | Core documentation alignment (5 docs) | 🔴 Active | 68% → 72% |
| **H7.2** | Deprecated archive cleanup | 🟡 Planned | 72% → 73% |
| **H8** | Test quality (boundary/perf/coverage) | 🟡 Planned | 73% → 78% |
| **H9** | ANGELA-MATRIX annotation + plugin docs | 🟢 Planned | 78% → 82% |

## Active AI Systems

| System | Description | Status |
|--------|-------------|--------|
| **ED3N** | External Dictionary Decoupling Neural Network — trie-based reflex + SNN spiking core, 4 phases complete | ✅ Phase 1-4 |
| **GARDEN-1G** | Giant Associative Relation Decoupled Evolutionary Network — lightweight ~1GB local model | ✅ Implemented |
| **Model Bus** | Capability-based routing (greeting→ED3N, math→ED3N, knowledge→GARDEN, creative→cloud) | ✅ Wired |
| **Query Classifier** | 22 rules → 8 domains (REFLEX/GREETING/MATH/LOGIC/KNOWLEDGE/CREATIVE/COMMAND/UNKNOWN) | ✅ Active |
| **Training Coordinator** | Domain ownership, deconfliction, reflex pattern sync | ✅ Active |

## Current State

- **Version**: 7.5.0-dev — all 14 version locations synchronized
- **Tests**: 2837 tests, 0 collection errors
- **HIGH vulnerabilities**: 0 remaining (all repaired in H1-H4)
- **Modules**: 564 Python files (~69K lines), 204 stub modules (36%)
- **CI**: 9 workflows, `tests/unit/` integrated
- **Architecture**: ModuleManager hotplug system, HSP protocol, HAM memory, 5-tier model scaling (ED3N→ECOSYSTEM)

## Key Metrics Dashboard

| Metric | Value |
|--------|-------|
| Test count | 2837 (+93 from H5 sprint) |
| Stub modules | 36/37 strict stubs implemented |
| Empty except blocks | 0 (20 remainder are intentional) |
| Files >200 lines | 138 (target: 50 in H7) |
| Type annotation coverage | ~87% |
| Version consistency | 14/14 |
| `import core` time | ~0.5s (lazy imports) |

## Risk Management

Key technical risks currently tracked:
- **132 files >200 lines** — H7 refactoring in progress (neuroplasticity, endocrine, state_matrix, router)
- **Coverage ~6.8%** — H8 will add boundary/perf/coverage gates
- **ANGELA-MATRIX annotation 0/6** — H9 will enforce standard
- **70+ uncommitted changes** — ordered cleanup planned

For detailed risk register see `MASTER_CONSOLIDATED_PLAN.md` (S/A/B/C/D/E task hierarchy).