# Angela AI v6.2.0 - Product Requirements Document (PRD)

**Document ID**: PRD-DF61-V1.0  
**Project**: Angela AI (Zencoder)  
**Creation Date**: 2026-02-20  
**Author**: Zencoder (Agent 1, 2, 3, 4 Combined)  
**Status**: ACTIVE

---

## 1. Executive Summary

Angela AI is a cross-platform digital life system aiming to create a "truly living" digital entity. The project consists of a Python FastAPI backend and an Electron-based desktop companion with Live2D integration.

**Actual Situation Analysis**: 
Contrary to the "99.2% complete" marketing description, the system is in a "Pseudo-Intelligent" state. It relies heavily on keyword matching and template responses when LLM backends are not active. The core architecture is solid, and infrastructure (testing, performance management, security) is highly mature, but the "soul" (real AI reasoning) is currently missing or disconnected.

---

## 2. Project Goals & Objectives

### 2.1 Primary Goal
Transition Angela AI from a "Pseudo-Intelligent" template-based system to a "Truly Intelligent" AGI system while maintaining high performance on low-spec hardware.

### 2.2 Core Objectives
1.  **System Familiarization**: Deep dive into the ~3,200 tracked files, understanding the distinction between core logic and legacy/backup code.
2.  **Ensure "Liveness"**: Resolve backend startup timeouts and ensure the system runs smoothly even on entry-level hardware (2GB RAM).
3.  **Real Intelligence Integration**: Implement full support for GPT-4, Claude, and Gemini, moving away from simple `.count()` and keyword matching.
4.  **Code Quality**: Fix the ~238 syntax errors in the test suite and ensure all core services are 100% healthy.
5.  **Role-Based Execution**: Strictly follow the 1-Lead, 2-Executor, 3-Thinker, 4-Checker collaborative workflow.

---

## 3. Detailed Requirements

### 3.1 Functional Requirements (FR)

| ID | Priority | Requirement | Description |
|---|---|---|---|
| FR-1 | P0 | **Real LLM Integration** | Replace keyword fallback with active calls to Ollama, OpenAI, or Anthropic. |
| FR-2 | P0 | **Semantic Understanding** | Integrate `jieba` and vector-based analysis to understand user intent beyond keywords. |
| FR-3 | P0 | **Fix Backend Timeout** | Optimize `lifespan` initialization in `main.py` to prevent launcher timeouts. |
| FR-4 | P1 | **Live2D Liveness** | Ensure animations and emotions are driven by real AI state, not just random/fixed loops. |
| FR-5 | P1 | **Memory Sync** | Deeply integrate HAM (Hierarchical Associative Memory) with the LLM service. |
| FR-6 | P2 | **Syntax Cleanup** | Eliminate all SyntaxErrors/IndentationErrors in `tests/` and `scripts/`. |

### 3.2 Non-Functional Requirements (NFR)

| ID | Category | Requirement | Target |
|---|---|---|---|
| NFR-1 | Performance | **Low-Spec Support** | Fluid operation on 2GB RAM / Entry-level GPU. |
| NFR-2 | Reliability | **Startup Time** | Backend + Frontend full start in < 5 seconds. |
| NFR-3 | Security | **A/B/C Key Sync** | Encryption latency < 5ms for all inter-process comms. |
| NFR-4 | Maintenance | **Git Hygiene** | Clear distinction between hidden files (.kiro, .zenflow) and public docs. |

---

## 4. Current Task Status (Actual vs. Stated)

- **Architecture**: **COMPLETED**. Solid FastAPI/Electron/WebSocket foundation.
- **Performance**: **COMPLETED**. 5-tier mode system is very mature.
- **Security**: **COMPLETED**. A/B/C key system is implemented.
- **Intelligence**: **PARTIAL/FALLBACK**. Stated as "Level 5 AGI" but actually "Level 0-1 Rule-based" in many areas.
- **Testing**: **UNSTABLE**. High volume of tests (300+) but ~80% have syntax issues.

---

## 5. Execution Roles & Responsibilities

1.  **Agent 1 (Lead)**: Strategy, task prioritization, and PRD/Spec approval.
2.  **Agent 2 (Executor)**: Coding, fixing syntax errors, and implementing API integrations.
3.  **Agent 3 (Thinker)**: Analyzing log traces, designing semantic logic, and hardware optimization research.
4.  **Agent 4 (Checker)**: Final audit, running lint/test commands, and verifying PRD compliance.

---

## 6. Success Metrics

- [ ] Core system `pytest` pass rate > 95%.
- [ ] No SyntaxErrors in the entire `Unified-AI-Project` directory.
- [ ] Successful "Truly Intelligent" response verified (not keyword based).
- [ ] Backend starts in under 3 seconds without timeout errors.
