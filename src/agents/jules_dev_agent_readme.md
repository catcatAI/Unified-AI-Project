# Jules Development Agent (`jules_dev_agent.py`)

## 1. Overview

The `JulesDevAgent` is a conceptual AI agent designed to operate within the Unified-AI-Project framework. Its primary role is to autonomously handle software development tasks, such as:
*   Understanding bug reports or feature requests.
*   Analyzing relevant parts of a (simulated) codebase.
*   Formulating a plan to address the task.
*   Simulating the execution of this plan, which may involve:
    *   Reading and modifying virtual files (via `AIVirtualInputService`).
    *   Executing code or tests (via `SandboxExecutor`).
    *   Generating code changes, commit messages, and simulated version control commands.

Jules is envisioned as an "asynchronous development agent," capable of managing tasks that may require multiple steps and potentially take time to complete.

## 2. Purpose and Goals

*   **Automate Development Tasks:** To assist human developers by tackling well-defined, small to medium-sized coding tasks in a simulated environment.
*   **Research Platform:** To serve as a platform for researching AI-driven software development, planning, and simulated environment interaction.
*   **Demonstrate Integration:** To showcase how various Unified-AI-Project services (`AIVirtualInputService`, `SandboxExecutor`, `LightweightCodeModel`, `LLMInterface`, `HAMMemoryManager`) can be orchestrated to achieve complex agent behavior.

**Note:** This is a conceptual agent. The current `jules_dev_agent.py` provides a placeholder structure with mocked interactions. Full implementation of its capabilities would require significant development.

## 3. Core Components & Functionality (Conceptual)

The `JulesDevAgent` class in `jules_dev_agent.py` outlines the following conceptual workflow:

1.  **Initialization (`__init__`):**
    *   Takes instances of various Unified-AI-Project services as dependencies.
    *   Initializes its internal state.

2.  **Task Intake (`intake_task`):**
    *   Receives a natural language description of a development task.
    *   Conceptually uses an LLM to parse this into a structured task representation.
    *   Stores the task and potentially logs it to memory (HAM).

3.  **Codebase Context Analysis (`analyze_codebase_context`):**
    *   Given relevant file paths for the task, it would use `LightweightCodeModel` (or AVIS for virtual file reading) to understand the structure and content of the code.
    *   This context is crucial for planning.

4.  **Plan Development (`develop_plan`):**
    *   Based on the structured task and code context, Jules uses an LLM to generate a multi-step plan.
    *   Plan steps might include actions like:
        *   Reading a virtual file.
        *   Modifying code (e.g., instructing an LLM to make specific changes).
        *   Writing to a virtual file.
        *   Running a test script in the sandbox.
        *   Generating a commit message.

5.  **Plan Execution (`execute_plan_step`, `run_full_plan`):**
    *   Iterates through the plan, executing each step.
    *   This involves interacting with services like AVIS (for simulated file/UI operations), `SandboxExecutor` (for code execution), and `LLMInterface` (for code generation/modification tasks).
    *   These methods are `async` to accommodate potentially long-running operations.

6.  **Output Generation (`generate_output`):**
    *   After plan execution, Jules compiles the results.
    *   This could include:
        *   A textual diff of the changes made.
        *   A generated commit message.
        *   A list of simulated `git` commands.

7.  **Status Reporting (`report_status`):**
    *   Provides information about its current state (idle, busy) and the status of the active task.

## 4. Dependencies

Jules relies on several other components of the Unified-AI-Project:

*   `DialogueManager`: For task assignment and communication.
*   `AIVirtualInputService` (AVIS): For all interactions with the simulated development environment (virtual files, virtual UI for code editing).
*   `AISimulationControlService` (ASCS): To manage permissions for actions orchestrated by Jules via AVIS.
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
