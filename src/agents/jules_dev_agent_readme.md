# Jules Development Capability (`jules_dev_agent.py`)

## 1. Overview

The `JulesDevelopmentCapability` module (`jules_dev_agent.py`) provides a set of functionalities enabling the core AI persona of the Unified-AI-Project (e.g., "Angela") to perform software development tasks. It is not a standalone agent but rather a specialized capability set that Angela orchestrates.

These tasks include:
*   Processing development task descriptions (e.g., bug reports, feature requests).
*   Analyzing relevant parts of a (simulated) codebase.
*   Formulating a plan to address the task.
*   Simulating the execution of this plan, which may involve:
    *   Reading and modifying virtual files (via `AIVirtualInputService`).
    *   Executing code or tests (via `SandboxExecutor`).
    *   Generating code changes, commit messages, and simulated version control commands.

The "Jules" capabilities are designed for asynchronous operation, allowing Angela to manage development tasks that may require multiple steps and time to complete.

## 2. Purpose and Goals

*   **Empower Core AI:** To provide Angela with the tools and processes to assist human developers by tackling well-defined, small to medium-sized coding tasks in a simulated environment.
*   **Research Platform:** To serve as a platform for researching AI-driven software development, where planning, execution, and simulated environment interaction are managed by a central AI persona.
*   **Demonstrate Orchestrated Integration:** To showcase how various Unified-AI-Project services (`AIVirtualInputService`, `SandboxExecutor`, `LightweightCodeModel`, `LLMInterface`, `HAMMemoryManager`) can be coordinated by a central AI (Angela) to achieve complex development-related behaviors.

**Note:** The current `jules_dev_agent.py` (housing `JulesDevelopmentCapability`) provides a foundational structure. Full implementation of its sophisticated capabilities is an ongoing development effort.

## 3. Core Components & Functionality (Conceptual, Orchestrated by Angela)

The `JulesDevelopmentCapability` class in `jules_dev_agent.py` outlines the following conceptual workflow, which would be invoked and managed by Angela:

1.  **Initialization (`__init__`):**
    *   Takes instances of various Unified-AI-Project services as dependencies. These services are the tools Angela will use through this capability.
    *   Initializes its internal state for managing a task.

2.  **Task Description Processing (`process_development_task_description`):**
    *   Angela provides a natural language description of a development task.
    *   This capability uses an LLM to parse this into a structured `current_task_context` (e.g., type of task, relevant files, goals).

3.  **Codebase Context Analysis (`analyze_code_context_for_task`):**
    *   Given relevant file paths (either from the processed task description or specified by Angela), this capability uses `LightweightCodeModel` (or AVIS for virtual file reading) to understand the structure and content of the code.
    *   The analysis is stored in the `current_task_context`.

4.  **Solution Plan Development (`develop_solution_plan`):**
    *   Based on the `current_task_context` (including the processed task and code analysis), this capability uses an LLM to generate a multi-step plan.
    *   Plan steps might include actions like reading/writing virtual files (e.g., using an `avis_read_file` step type that calls `AIVirtualInputService.process_file_operation_command`), modifying code, running tests, or generating commit messages.
    *   The plan is stored in the `current_task_context`.

5.  **Plan Execution (`execute_step_in_plan`, `execute_full_solution_plan`):**
    *   Angela directs the execution of the plan.
    *   The capability iterates through the plan, executing each step. This involves interactions with `AIVirtualInputService` (for file operations like reading via `process_file_operation_command` or simulated UI actions), `SandboxExecutor` (for code execution), and `LLMInterface` (for code generation/analysis).
    *   These methods are `async` to accommodate potentially long-running operations. Output from one step can be used as input for subsequent steps.

6.  **Output Generation (`generate_development_output`):**
    *   After plan execution, Angela can instruct this capability to compile the results.
    *   This could include a textual diff of changes, a generated commit message, and a list of simulated `git` commands.

7.  **Status Reporting (`get_current_task_status_and_context`):**
    *   Provides Angela with information about the current state of the task being handled by this capability.

8.  **Context Clearing (`clear_current_task_context`):**
    *   Resets the capability's internal context, making it ready for a new task from Angela.


## 4. Dependencies (Services Utilized by this Capability)

The `JulesDevelopmentCapability` relies on several other components of the Unified-AI-Project, which are provided to it during initialization:

*   `AIVirtualInputService` (AVIS): For all interactions with the simulated development environment (virtual files, virtual UI for code editing).
*   `AISimulationControlService` (ASCS): (Implicitly via AVIS) To manage permissions for actions performed via AVIS.
*   `SandboxExecutor`: For safely executing code snippets or test scripts.
*   `LightweightCodeModel`: For understanding the structure of existing code.
*   `HAMMemoryManager`: For persisting task states, plans, learnings, and potentially code snippets.
*   `LLMInterface`: For natural language understanding (task intake), planning, code generation, and commit message generation.
*   `ToolDispatcher`: Jules might invoke other specialized tools if needed.

## 5. How to Run / Test (Conceptual)

The `if __name__ == '__main__':` block in `jules_dev_agent.py` provides a very basic, conceptual example of how the agent's workflow might be invoked. It uses mock services to simulate the interactions.

To run this conceptual example:
```bash
python src/agents/jules_dev_agent.py
```
This will print logs showing the agent's internal state progression through a simulated task.

## 6. Future Development

The `jules_dev_agent.py` file is currently a high-level conceptual placeholder. Significant development is required to implement the actual logic for each step, including:
*   Robust LLM prompting strategies for task parsing, planning, and code generation.
*   Detailed interaction protocols with AVIS for a simulated file system and code editor.
*   Error handling, retries, and state management for multi-step plans.
*   Mechanisms for Jules to learn from past tasks.
*   Actual diff generation and more sophisticated version control command generation.

This agent represents an ambitious direction for the Unified-AI-Project, aiming to create a capable AI assistant for software development tasks.
