# Jules - Asynchronous Development Capability - Design Specification v0.2

## 1. Introduction

"Jules" represents a specialized **Asynchronous Development Capability** integrated within the Unified-AI-Project, orchestrated by the core AI persona, Angela. Its primary purpose is to enable Angela to autonomously handle software development tasks, such as fixing bugs, implementing small features, and other related software engineering activities. Jules operates by allowing Angela to interact with a simulated development environment, aiming to produce outputs like code changes and version control commands.

This specification (v0.2) reframes Jules from a standalone agent to a core capability set of Angela, aligning with the architectural vision of Angela as the central commander. The guiding vision remains: "Jules tackles bugs, small feature requests, and other software engineering tasks, with direct export to GitHub," with Angela being the entity leveraging these Jules capabilities.

## 2. Core Purpose and Vision

The Jules capability set aims to empower Angela to:
*   **Automate Development Tasks:** Assist human developers by taking on well-defined, small to medium-sized coding tasks under Angela's coordination.
*   **Simulate Development Workflow:** Provide a simulated environment where AI-driven development processes, managed by Angela, can be researched and refined.
*   **Integrate with Unified-AI-Project:** Leverage the existing and future capabilities of the Unified-AI-Project, such as dialogue management, learning systems, and tool execution frameworks, all orchestrated by Angela.
*   **Asynchronous Operation:** Enable Angela to manage development tasks that may take time, providing updates, and working without constant real-time supervision.

While "direct export to GitHub" is a long-term vision for outputs generated via the Jules capability, the initial focus will be on Angela simulating the actions and generating the *commands* or *patches* that would be used for such an export.

## 3. Core Capabilities (Utilized by Angela)

Angela, when employing her Jules development capabilities, will require access to and control over functionalities enabling:

### 3.1. Task Understanding & Intake
*   **Input:** Angela receives task descriptions (e.g., bug reports, feature requests) via the `DialogueManager` or a dedicated tasking interface.
*   **Processing:** Angela, using her core NLP and reasoning abilities (potentially augmented by specialized LLM prompts for coding tasks), parses the task to identify objectives, constraints, relevant code components, and success criteria.
*   **Output:** A structured representation of the task, managed by Angela.

### 3.2. Code Comprehension
*   **Input:** File paths, code snippets, or references to modules within the project, identified by Angela as relevant to the task.
*   **Processing:** Angela utilizes tools like `LightweightCodeModel` (`src/core_ai/code_understanding/lightweight_code_model.py`) to understand code structure, identify functions, classes, dependencies, and potentially analyze control flow or data structures.
*   **Output:** An internal representation of the code relevant to the task, accessible to Angela.

### 3.3. Planning & Strategy
*   **Input:** Structured task representation and code comprehension outputs, available to Angela.
*   **Processing:** Angela develops a step-by-step plan to address the task. This plan might involve:
    *   Reading files.
    *   Modifying code (identifying lines/blocks to change).
    *   Writing new code.
    *   Executing code for testing.
    *   Generating commit messages.
    *   Generating git commands.
*   **Output:** A sequence of actions to be performed, managed and overseen by Angela.
*   **Example Plan Step Types (Conceptual):**
    *   `{"type": "avis_read_file", "path": "path/to/file.py", "output_key": "file_content_variable"}`: Instructs AVIS to read the content of a virtual file and store it in the task's accumulated outputs under `file_content_variable`.
    *   `{"type": "llm_analyze_code", "inputs": {"code_var": "file_content_variable"}, "instruction": "Identify function 'foo'", "output_key": "analysis_result"}`
    *   `{"type": "llm_generate_code_modification", "inputs": {"code_var": "file_content_variable", "analysis_var": "analysis_result"}, "instruction": "Add a parameter 'new_param' to function 'foo'", "output_key": "modified_code"}`
    *   `{"type": "avis_write_file", "path": "path/to/file.py", "content_var": "modified_code"}` (or a more granular `avis_apply_modification` step)
    *   `{"type": "sandbox_run_test", "script_path": "tests/test_file.py"}`
    *   `{"type": "generate_commit_message", "inputs": {"task_description_var": "original_description", "changes_summary_var": "llm_generated_summary"}}`
    *   `{"type": "generate_git_commands", "inputs": {"commit_message_var": "generated_commit_message", "branch_name": "feat/task-123"}}`


### 3.4. Simulated Environment Interaction
Angela, through the Jules capability set, interacts with a simulated environment provided by Unified-AI-Project services:
*   **File System Operations (Simulated):**
    *   Angela uses the `AIVirtualInputService` (AVIS) to simulate reading, writing, and modifying files within a virtual project structure. This is done via `AVISFileOperationCommand` requests.
    *   For reading, AVIS is expected to return the file content (e.g., via `AVISFileOperationResponse.content`).
    *   For writing, AVIS would update its internal virtual file system.
*   **Code Editing (Simulated):**
    *   This could involve AVIS reading a file, an LLM proposing changes, and then AVIS writing the modified content back. More advanced AVIS commands might support targeted modifications if the virtual environment is rich enough (e.g., element-based editing in a virtual IDE view).
*   **Code Execution & Testing:**
    *   Angela uses the `SandboxExecutor` (via AVIS or `AISimulationControlService`) to run modified code or tests and observe the output (`stdout`, `stderr`, exit codes).
    *   This is crucial for Angela to verify changes and guide iterative development.

### 3.5. Output Generation
*   **Code Drafting:** Angela generates new or modified code snippets based on her plan, using her LLM capabilities.
*   **Commit Messages:** Angela creates descriptive commit messages summarizing the changes made.
*   **Version Control Commands (Simulated):** Angela generates the text for git commands (e.g., `git add <file>`, `git commit -m "..."`, `git push origin <branch>`).

### 3.6. Asynchronous Task Management
*   Angela, managing the Jules capability, should be able to handle tasks that are not instantaneous. This might involve:
    *   Reporting progress via `DialogueManager`.
    *   Handling interruptions or requests for updates.
    *   Storing and resuming task state (potentially using `HAMMemoryManager`).
    *   Interacting with `FragmentaOrchestrator` if tasks become very complex and require coordination across multiple long-running sub-processes under her oversight.

## 4. Key Interactions with Unified-AI-Project Modules (Orchestrated by Angela)

Angela, when leveraging the Jules development capabilities, will orchestrate interactions between various modules:

*   **`DialogueManager`:**
    *   The primary interface for users to assign tasks to Angela.
    *   Angela, through `DialogueManager`, understands the request and decides if her "Jules capabilities" are appropriate.
    *   Angela reports progress and results back via `DialogueManager`.
*   **`AIVirtualInputService` (AVIS) & `AISimulationControlService` (ASCS):**
    *   Angela directs AVIS to perform all simulated interactions with a "development environment" (file views, code editor views).
    *   ASCS governs Angela's permissions for actions like simulated code execution when using these capabilities.
*   **`SandboxExecutor`:**
    *   Used by Angela (likely via AVIS/ASCS) for executing code snippets, running tests, or performing other sandboxed operations.
*   **`LightweightCodeModel` & other Code Understanding Tools:**
    *   Essential tools for Angela to analyze and understand the codebase she's working on.
*   **`HAMMemoryManager`:**
    *   Used by Angela to store task states, learned information about codebases, successful solution patterns related to development tasks, etc.
*   **`ToolDispatcher`:**
    *   Angela might use existing or new tools (e.g., a "git command generator tool," a "diff generator tool") via the dispatcher as part of her Jules capability.
*   **`FragmentaOrchestrator`:**
    *   For very large or complex development tasks that Angela breaks down, she might employ `FragmentaOrchestrator` to manage the execution of these sub-tasks.
*   **`LLMInterface`:**
    *   Central for many of Angela's internal processes when using Jules capabilities: task parsing, planning, code generation, commit message generation.

## 5. Relationship to `SimpleCodingAgent`

*   The `SimpleCodingAgent` (`src/agents/simple_coding_agent.py`) is a very basic, scripted agent designed to test AVIS's code execution loop.
*   The "Jules capability" represents a far more sophisticated function set within Angela. While `SimpleCodingAgent` follows a fixed script, Angela would dynamically generate her actions based on the task, her understanding of the code, and her plan when using her Jules skillset.
*   Angela, using Jules capabilities, would perform a much wider range of actions (file manipulation, complex code changes, test execution, version control command generation) compared to the `SimpleCodingAgent`'s narrow focus. The `SimpleCodingAgent` can be seen as a test utility for a subset of actions Angela might take.

## 6. Success Criteria (Conceptual for Angela using Jules capabilities)

*   Angela can successfully receive a simple coding task (e.g., "Fix a typo in function X in file Y.py" or "Add a parameter Z to function X").
*   Angela can use code understanding tools to locate the relevant code.
*   Angela can formulate a plan to modify the code.
*   Angela can use AVIS to simulate making the necessary code changes in a virtual file.
*   Angela can use `SandboxExecutor` to simulate running the modified code or a simple test.
*   Angela can generate a plausible commit message and git commands for the change.

## 7. Future Considerations

*   Actual integration with GitHub (API interaction for creating branches, committing files, opening PRs), managed by Angela.
*   More sophisticated testing capabilities (e.g., Angela running existing test suites, generating new tests).
*   Angela learning from feedback and past tasks to improve her software development capabilities.
*   Angela handling more complex tasks, including debugging and multi-file changes.
*   User interaction with Angela for clarification or decision-making during a development task.

This v0.2 specification reframes Jules as a core capability of Angela, ensuring a unified command structure within the Unified-AI-Project. Implementation would be iterative, enhancing Angela's skillset over time.
