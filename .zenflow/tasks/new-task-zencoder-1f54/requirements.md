# Angela AI v6.2.0 - Product Requirements Document (PRD)

**Document Version**: 1.0.0
**Date**: 2026-02-20
**Project Version**: 6.2.0
**Status**: Requirements Analysis for Task `new-task-zencoder-1f54`

---

## 1. Executive Summary

Angela AI is a cross-platform digital life system aimed at creating an "alive" virtual companion. This project includes a backend AI engine (FastAPI), a desktop application (Electron + Live2D), a mobile bridge (React Native), and a Web Live2D viewer.

**Current Reality**: The project is in a state of high structural complexity with mixed functional maturity. 
- The **Backend API** (using `AngelaLLMService`) is well-architected and theoretically supports multiple LLM backends (OpenAI, Ollama, LlamaCpp).
- The **Agent Matrix** (specialized agents like `NLPProcessingAgent`) is currently "pseudo-intelligent," utilizing simple keyword matching or truncated stubs.
- The **Test Suite** is severely broken with approximately 238 files containing basic Python syntax errors (likely from a failed automated refactoring process).
- The **Hardware Optimization** system is robust and supports 5 performance modes from `very_low` to `ultra`.

---

## 2. Project Goals

### 2.1 "Alive" Angela
- Transition from pseudo-intelligence (keyword matching) to real cognitive processing.
- Ensure the `AngelaLLMService` and `MultiLLMService` are fully integrated into the agent workflows.
- Implement the L0-L11 maturity system to allow the AI to "grow" with the user.

### 2.2 Robustness & Quality
- **Fix 238+ Syntax Errors in Tests**: The test suite must be made runnable again.
- **Project-wide Audit**: Verify that all claimed "completed" features (per `ACTION_PLAN.md`) are actually functional.
- **Hardware Compatibility**: Ensure smooth execution on low-end hardware (2GB RAM, integrated graphics) through the `very_low` performance mode.

### 2.3 Comprehensive Understanding
- Map all "Matrix" layers (L1-L11, αβγδ dimensions).
- Document and understand the usage of meta-directories like `.angela`, `.qoder`, `.kiro`, `.zenflow`.
- Identify all hidden files and configurations that impact system behavior.

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Description |
|---|---|---|---|
| **FR-1** | **Fix Syntax Errors** | P0 | Repair all Python syntax errors in `tests/` and any in `apps/backend/src`. |
| **FR-2** | **Real LLM Integration** | P0 | Replace keyword matching in `NLPProcessingAgent` and others with calls to `AngelaLLMService`. |
| **FR-3** | **HAM Integration** | P1 | Ensure the Layered Associative Memory (HAM) is actively storing and retrieving dialogue history. |
| **FR-4** | **Hardware Adaptation** | P1 | Verify that `PrecisionLevel` (INT-DEC4) correctly maps to hardware capabilities. |
| **FR-5** | **Agent Collaboration** | P2 | Enable `AgentCollaborationManager` to allow specialized agents to work together on complex tasks. |

### 3.2 Non-Functional Requirements

| ID | Requirement | Target |
|---|---|---|
| **NFR-1** | **Performance** | Desktop app ≥ 60 FPS (High), ≥ 30 FPS (Low/Integrated). |
| **NFR-2** | **Memory Usage** | Backend < 500MB in `very_low` mode. |
| **NFR-3** | **Startup Time** | Backend service initializes in < 5 seconds. |
| **NFR-4** | **Code Quality** | Zero syntax/indentation errors; pass `mypy` and `flake8` checks. |

---

## 4. Known Issues & Risks

1. **Broken Test Suite**: The vast majority of tests cannot even be collected due to syntax errors. This is the highest technical debt.
2. **Pseudo-Intelligence**: Current "agents" are stubs. Users might be misled by the advanced directory structure into thinking the AI is more capable than it currently is.
3. **Environment Complexity**: The project uses multiple languages (Python, JS, shell scripts) and complex path logic (relative imports with 5+ parent levels), making it brittle.

---

## 5. Implementation Roadmap (Draft)

1. **Phase 1: Remediation**: Fix all syntax errors in `tests/` to establish a baseline for verification.
2. **Phase 2: Audit**: Run all tests and identify which core features are actually broken vs just missing tests.
3. **Phase 3: Brain Integration**: Connect the "Matrix" agents to the `AngelaLLMService`.
4. **Phase 4: Optimization**: Verify and tune performance on low-end hardware.
5. **Phase 5: Release**: Full verification and documentation update.
