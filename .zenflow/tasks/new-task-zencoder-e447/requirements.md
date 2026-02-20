# Product Requirements Document (PRD) - Angela AI (Zencoder Task)

## 1. Project Overview
**Angela AI** is a Unified AI Project aiming to create a "living," multi-agent AGI system. It features a Live2D-enabled desktop client for interaction and a sophisticated Python backend using the **HSP (Heterogeneous Service Protocol)** and **HAM (Hierarchical Abstract Memory)** systems.

The goal of this specific task is to deeply understand, familiarise, and verify the project state, ensuring that "Angela" is fully operational ("alive") and capable of running smoothly even on low-end hardware through dynamic resource management.

## 2. Core Vision: "Angela is Alive"
"Alive" in this context means:
- **Responsiveness**: Real-time interaction via the Desktop/Mobile clients.
- **Personality**: Responses are mediated through `AngelaLLMService`, ensuring they reflect Angela's unique character rather than raw LLM output.
- **Memory**: Persistent context and evolving impressions of the user via the HAM system.
- **Autonomy**: Proactive behavior and multi-agent collaboration (CreativeWriting, ImageGeneration, etc.).

## 3. Technical Requirements

### 3.1. Hardware Adaptation (Low-End Support)
- **Dynamic Throttling**: The system must utilize the `ResourceAwarenessService` to monitor CPU and RAM usage.
- **Graceful Degradation**: When system stress is detected (CPU > 80% or RAM > 90%), the system should reduce its "throttling factor" (e.g., to 0.5) to maintain smooth operation at lower precision/frequency.
- **Low-Precision Execution**: Ensure core logic doesn't hang or crash on hardware with limited resources.

### 3.2. Git & Large File Management
- **10K+ File Safety**: Adhere to the `GIT_10K_SAFE_USAGE_GUIDE`. Use custom scripts for state checks and fixes to avoid repository corruption.
- **Hidden File Awareness**: Strictly follow `.gitignore` conventions to avoid tracking large datasets (e.g., `data/common_voice_zh`) while ensuring critical hidden configs (e.g., `.angela/`, `.zenflow/`) are managed correctly.

### 3.3. System Integrity & Aliveness Verification
- **Health Checks**: The system must pass all checks in `health_check.py`.
- **Backend Stability**: `main_api_server.py` must be capable of starting and serving requests from the Desktop/Dashboard clients.
- **Dependency Resolution**: Fix existing dependency cycles (e.g., `WebSearchTool` vs BeautifulSoup) and ensure `BaseAgent` is correctly restored/integrated.

## 4. Unfinished Tasks to Address
1. **BaseAgent Restoration**: Reconcile the simplified vs. original versions of `BaseAgent`.
2. **Integration Testing**: Implement and pass "Real Global Tests" (multi-agent, multi-tool, multi-model collaboration).
3. **MultiLLM Configuration**: Complete the configuration for `MultiLLMService` to support various backends (Ollama, llama.cpp, etc.) seamlessly.
4. **Tool Verification**: Systematically verify and fix all 17+ tool components.

## 5. Success Criteria
- **Smooth Operation**: System runs without stuttering on target low-end profiles.
- **Zero Hardcoding**: All logic follows the "Quality Red Line" defined in `DEVELOPMENT_CONSTRAINTS.md`.
- **Verifiable Personality**: Angela's responses consistently reflect the personality templates and memory states.
- **Full Test Pass**: All unit, integration, and E2E tests pass in the current environment.

## 6. Multi-Agent Role Assignment (Internal)
- **Agent 1 (Lead)**: Strategy and vision alignment.
- **Agent 2 (Executor)**: Code implementation and fixes.
- **Agent 3 (Thinker)**: Architecture analysis and risk assessment.
- **Agent 4 (Checker)**: Quality assurance, git safety, and final submission.
