# AI Virtual Input System - Design Specification v0.4

## 1. Introduction

This document outlines the design for the AI Virtual Input System (AVIS), a system enabling the Unified-AI-Project to simulate and (with strict permissions) execute mouse and keyboard interactions within a computer's graphical user interface (GUI). The primary goal is to allow the AI to perform tasks that require GUI manipulation, expanding its capabilities beyond text-based interactions and tool usage.

This system is foundational for exploring how an AI's behavior, decision-making, and problem-solving strategies evolve when granted more direct agency within a typical computing environment.

**Key Goals:**
*   Enable simulation of GUI interactions for research and development.
*   Provide a framework for potential future direct GUI control by the AI.
*   Explore AI decision-making in environments requiring visual-spatial reasoning and action sequences.
*   Prioritize safety and control, especially regarding actual system input.

## 2. Scope

*   **Initial Focus (Simulation):** The primary development focuses on creating a robust simulation layer. The AI issues virtual mouse/keyboard commands, and AVIS logs these, updating an internal model of a virtual UI, virtual cursor, focus, etc., without directly affecting the host OS.
*   **Code Execution (v0.4):** AVIS now supports AI-driven code execution. The AI can input code into a virtual UI element, trigger execution, and view results. This is mediated by the `AISimulationControlService`, which handles permissions and secure execution.
*   **Future Capability (Actual Control):** The design anticipates future extension for actual system input control (e.g., `pynput`). This will be subject to a stricter permissions model (see Section 7) and developed with extreme caution.

## 3. System Architecture Overview (v0.4)

AVIS interfaces with several key components:

*   **`AIVirtualInputService` (AVIS Core):**
    *   Manages the virtual UI state (`virtual_ui_elements`).
    *   Processes simulated mouse/keyboard commands, updating its internal state.
    *   Handles requests for code execution by interacting with `AISimulationControlService`.
    *   Provides methods for an AI agent to "perceive" the virtual UI and its state.
*   **`AISimulationControlService` (ASCS):**
    *   A new service responsible for:
        *   Managing AI operational permissions (e.g., `can_execute_code`, `can_read_sim_hw_status`).
        *   Interfacing with `ResourceAwarenessService` to fetch current simulated hardware status.
        *   Orchestrating the execution of AI-provided code strings using a sandboxed execution mechanism (e.g., `run_in_bash_session`).
        *   Returning execution results (`stdout`, `stderr`, exit codes) to AVIS.
*   **`ResourceAwarenessService` (External):**
    *   Provides information about the simulated hardware environment (CPU, disk, etc.). ASCS queries this service.
*   **AI Agent / Test Harness (External):**
    *   The entity (e.g., a higher-level AI agent, a test script) that interacts with AVIS.
    *   It loads virtual UI configurations into AVIS.
    *   It sends commands to AVIS to simulate user actions or request code execution.
    *   It queries AVIS to get the current UI state, permissions, and hardware status.

## 4. Core Concepts

### 4.1. Element-Based Interaction (Primary Paradigm)
The AI will primarily interact with GUI elements symbolically rather than through raw coordinates. Commands will target elements identified by a unique `element_id`.
*   **Example:** `click_element(element_id='login_button')` is preferred over `click_at_pixel(x=752, y=480)`.

### 4.2. Coordinate System
*   **Relative Coordinates:** When precise positioning is needed (e.g., within a specific element like a canvas, or for general mouse movement not tied to an element), relative coordinates (typically floats between 0.0 and 1.0) will be used.
    *   **Element-Relative:** Coordinates are relative to the bounds of a specified `target_element_id`. For example, `(0.5, 0.5)` would be the center of the element.
    *   **Window/Screen-Relative (for general movement):** Coordinates or deltas are relative to the current window or screen context (e.g., `move_mouse_relative(delta_x_ratio=0.1, delta_y_ratio=-0.05)`).
*   **Absolute Coordinates:** Direct use of absolute screen coordinates is generally discouraged due to its brittleness across different screen resolutions, window sizes, and UI layouts. If supported in the future for actual control, it will be under strict permissions.

### 3.3. Feedback Mechanism (AI Perception of UI)
For the AI to make informed decisions and use element IDs or relative coordinates effectively, it needs to "perceive" the UI.
*   **Simulation Model (Current AVIS Implementation):**
    *   The AVIS service maintains an internal state representing a simple, single virtual window/UI (`self.virtual_ui_elements`).
    *   This state is a list of `VirtualInputElementDescription` objects, which can be loaded via a method like `avis.load_virtual_ui([...])`.
    *   The AI can "perceive" this current virtual UI by calling a method like `avis.get_current_virtual_ui() -> List[VirtualInputElementDescription]`. This method effectively serves the role of the originally conceptualized `get_screen_elements()` for the simulated environment.
    *   This allows the AI to receive a structured description of available elements, their types, labels, values, states (enabled, visible, focused), and conceptual relative bounds.
*   **Stateful Simulation:** AI actions have defined effects on the AVIS's internal state:
    *   `type_string`: Modifies the `value` attribute of the focused, typable `VirtualInputElementDescription` in `virtual_ui_elements`.
    *   `click`: Updates `virtual_focused_element_id`. Can be extended to modify other element attributes (e.g., a checkbox's 'value').
    *   `hover_element`: Updates `virtual_hovered_element_id` and the virtual cursor position.
    *   Other actions primarily log intent and update virtual cursor/focus as applicable.
    *   The AI can observe these state changes by calling `get_current_virtual_ui()` after performing an action.
*   **Future (for Actual Control & Advanced Simulation):** As previously noted, integration with OS-level accessibility APIs, screen scraping with OCR, or specialized computer vision models would be necessary to parse real application UIs or more complex simulated environments. The "Advanced Feedback Mechanisms" in Section 9 further detail this.

## 5. Supported Virtual Actions (and their effects on simulated state)

The AVIS will support a range of mouse and keyboard actions, and as of v0.4, AI code execution. These actions are represented by commands sent to the AVIS. In simulation mode, these primarily result in logging and updates to the AVIS's internal virtual state.

### 5.1. Mouse Actions
*   `get_current_virtual_ui()`: AI requests a description of currently "visible" UI elements within the AVIS's managed virtual window.
*   `focus_element(element_id: str)`: (Conceptual AVIS command, often handled implicitly by `click`) Sets the virtual input focus (`virtual_focused_element_id` in AVIS) to the specified UI element.
*   `click_element(element_id: str, click_type: Literal['left', 'right', 'double'], relative_x: Optional[float], relative_y: Optional[float])`: Simulates a click. **Effect on State:** Updates `virtual_focused_element_id`. The simulation can be extended for specific elements (e.g., toggling a checkbox `value`) if rules are defined for them in the virtual UI description.
*   `hover_element(element_id: str, relative_x: Optional[float], relative_y: Optional[float])`: Simulates moving the virtual mouse pointer over a specified element. **Effect on State:** Updates `virtual_cursor_position` and sets `virtual_hovered_element_id`. Logs the action.
*   `drag_element_to_position(source_element_id: str, target_window_relative_x: float, target_window_relative_y: float)`: Simulates clicking and dragging an element. (Conceptual, detailed state update TBD).
*   `drag_element_to_element(source_element_id: str, target_element_id: str)`: Simulates clicking and dragging an element onto another. (Conceptual, detailed state update TBD).
*   `scroll_element(element_id: str, direction: Literal['up', 'down', 'left', 'right'], amount_ratio: Optional[float], pages: Optional[int])`: Simulates scrolling. If `element_id` is provided and scrollable, targets that element; otherwise, implies window scroll. **Effect on State:** Logs the action. Actual scroll position change is conceptual in the current simulation.
*   `move_mouse_relative(delta_x_ratio: float, delta_y_ratio: float)`: Moves the virtual mouse pointer by a ratio of the current screen/window dimensions. **Effect on State:** Updates `virtual_cursor_position`.

### 5.2. Keyboard Actions
*   `type_string(text: str, target_element_id: Optional[str])`: Simulates typing. If `target_element_id` is provided and found, it becomes the `virtual_focused_element_id`. If the focused element is typable (e.g., has a `value` attribute), its `value` in `virtual_ui_elements` is updated. **Effect on State:** Updates element `value` and logs.
*   `press_keys(keys: List[str], target_element_id: Optional[str])`: Simulates pressing key combinations (e.g., `['ctrl', 'alt', 't']`). If `target_element_id` is provided, `virtual_focused_element_id` is updated. **Effect on State:** Primarily logs the action and updates focus. Deep simulation of complex shortcut effects on UI state is not yet implemented.
*   `special_key(key_name: Literal['enter', 'tab', 'esc', ...], target_element_id: Optional[str])`: Simulates pressing a single special key. If `target_element_id` is provided, `virtual_focused_element_id` is updated. **Effect on State:** Similar to `press_keys`; logs the action and updates focus. Specific behaviors (e.g., 'Enter' submitting a form) are not deeply simulated.

### 5.3. AI Code Execution Actions (v0.4)

AVIS enables AI-driven code execution through specific UI interactions and internal service calls.

*   **UI Elements for Code Execution:**
    *   `code_editor` (e.g., `element_id="code_editor"`): A virtual `text_area` where the AI can input or modify code (typically Python).
    *   `run_code_button` (e.g., `element_id="run_code_button"`): A virtual `button`. Clicking this triggers the code execution process.
    *   `code_output_display` (e.g., `element_id="code_output_display"`): A read-only virtual `text_area` where `stdout`, `stderr`, and status messages from the code execution are displayed.
*   **Triggering Execution:**
    *   The AI simulates typing code into the `code_editor` element.
    *   The AI simulates a `click` on the `run_code_button`.
*   **AVIS Internal Process:**
    1.  `AIVirtualInputService.process_mouse_command()` detects the click on `run_code_button`.
    2.  It retrieves the current `value` (code string) from the `code_editor` element.
    3.  It calls `AIVirtualInputService.process_code_execution_command(code_string)`.
    4.  `process_code_execution_command` then invokes `AISimulationControlService.execute_ai_code(code_string, current_permissions)`.
    5.  The `AISimulationControlService` (ASCS):
        *   Checks if the AI's `current_permissions` (specifically `can_execute_code`) allow execution.
        *   If permitted, it prepares the code (e.g., writes to a temporary script file) and uses the `run_in_bash_session` tool to execute it in a sandboxed environment.
        *   Captures `stdout`, `stderr`, and the script's exit code.
        *   Returns an `ExecutionResult` TypedDict.
    6.  `AIVirtualInputService` receives the `ExecutionResult`.
    7.  It formats this result into a string and updates the `value` of the `code_output_display` virtual UI element.
    8.  The action (code execution attempt) and its outcome are logged in AVIS's action log.

## 6. API and Data Structures (TypedDicts)

The interaction with AVIS will be through commands defined by TypedDicts. These types are defined in `src/shared/types/common_types.py`.
This section also includes types related to code execution as of v0.4.

*   **`VirtualMouseEventType = Literal["move_relative_to_element", "move_relative_to_window", "click", "scroll", "drag_start", "drag_end", "hover"]`**: Defines valid mouse action types.
*   **`VirtualKeyboardActionType = Literal["type_string", "press_keys", "special_key"]`**: Defines valid keyboard action types.
*   **`VirtualInputPermissionLevel = Literal["simulation_only", "allow_actual_input_restricted", "allow_actual_input_full"]`**: Defines permission levels.
*   **`VirtualInputElementDescription(TypedDict)`**: Describes a UI element.
    *   `element_id: Required[str]`
    *   `element_type: Required[str]` (e.g., "button", "text_field")
    *   `label_text: Optional[str]`
    *   `value: Optional[Any]`
    *   `is_enabled: Optional[bool]`
    *   `is_focused: Optional[bool]`
    *   `is_visible: Optional[bool]`
    *   `bounds_relative: Optional[List[float]]` # [x_ratio, y_ratio, width_ratio, height_ratio]
    *   `children: Optional[List['VirtualInputElementDescription']]` # Recursive
    *   `attributes: Optional[Dict[str, Any]]`
*   **`VirtualMouseCommand(TypedDict)`**:
    *   `action_type: Required[VirtualMouseEventType]`
    *   `target_element_id: Optional[str]`
    *   `relative_x: Optional[float]`
    *   `relative_y: Optional[float]`
    *   `click_type: Optional[Literal['left', 'right', 'double']]`
    *   `scroll_direction: Optional[Literal['up', 'down', 'left', 'right']]`
    *   `scroll_amount_ratio: Optional[float]`
    *   `scroll_pages: Optional[int]`
    *   `drag_to_element_id: Optional[str]`
    *   `drag_to_relative_x: Optional[float]`
    *   `drag_to_relative_y: Optional[float]`
*   **`VirtualKeyboardCommand(TypedDict)`**:
    *   `action_type: Required[VirtualKeyboardActionType]`
    *   `target_element_id: Optional[str]`
    *   `text_to_type: Optional[str]` # For "type_string"
    *   `keys: Optional[List[str]]`    # For "press_keys" (e.g., ["ctrl", "c"])
    *   `key_name: Optional[str]`     # For "special_key" (e.g., "enter", "tab")
*   **`AIPermissionSet(TypedDict)` (v0.4)**: Defines permissions for AI operations, especially code execution.
    *   `can_execute_code: Required[bool]`
    *   `can_read_sim_hw_status: Required[bool]`
    *   *(Future: `allowed_execution_paths`, `allowed_service_imports`, `max_execution_time_ms`)*
*   **`ExecutionRequest(TypedDict)` (v0.4)**: Internal representation for a code execution request.
    *   `request_id: str`
    *   `code_to_execute: str`
    *   `permissions_context: AIPermissionSet`
*   **`ExecutionResult(TypedDict)` (v0.4)**: Outcome of a code execution attempt.
    *   `request_id: str`
    *   `execution_success: bool` (True if execution was attempted, False if pre-checks failed)
    *   `script_exit_code: Optional[int]`
    *   `stdout: str`
    *   `stderr: str`
    *   `status_message: str`

## 7. Permissions Model (v0.4 Update)

The permissions model is evolving with the introduction of code execution. It's managed by `AISimulationControlService` and visible to the AI via AVIS.

1.  **`simulation_only` (AVIS Input Mode - Default):**
    *   Applies to direct mouse/keyboard input simulation by AVIS.
    *   AVIS commands are processed internally, updating virtual UI state.
    *   No actual OS-level mouse or keyboard events are generated.
2.  **AI Operational Permissions (`AIPermissionSet` in ASCS):**
    *   Governs capabilities like code execution and status visibility.
    *   `can_execute_code`: If `False`, ASCS will deny any code execution requests from AVIS.
    *   `can_read_sim_hw_status`: If `False`, ASCS might restrict visibility of detailed hardware status (though AVIS might still show basic availability).
    *   These permissions are loaded by `AISimulationControlService` (e.g., from a configuration) and can be refreshed.
    *   AVIS displays the current AI permissions in a dedicated UI element (e.g., `ai_permissions_display`).
3.  **`allow_actual_input` (Future AVIS Input Mode, Highly Restricted):**
    *   As described previously, for direct OS-level input. This is separate from the AI operational permissions for code execution within the simulation.
    *   Requires explicit runtime grants, secure and auditable.
    *   **Security Warning:** Enabling actual input control has significant security implications.

1.  **`simulation_only` (Default Mode):**
    *   All AVIS commands are processed internally.
    *   Actions are logged, and a virtual UI state (if maintained) is updated.
    *   No actual OS-level mouse or keyboard events are generated.
    *   This is the safe default for all AI operations using AVIS unless explicitly overridden.
2.  **`allow_actual_input` (Future, Highly Restricted Mode):**
    *   This mode requires explicit runtime permission grants. The mechanism for granting this permission must be secure and auditable (e.g., a specific configuration setting that is off by default, requiring manual intervention to enable, plus potentially runtime confirmation prompts for sensitive actions).
    *   Permissions might be further refined (e.g., allow actual input only for specific applications, or only keyboard, not mouse).
    *   **Security Warning:** Enabling actual input control has significant security implications.

## 8. Simulation Environment & Feedback Loop (v0.4 Update)

*   **Virtual Environment State:**
    *   AVIS maintains `self.virtual_ui_elements` (the virtual UI).
    *   AVIS also now maintains `self.current_ai_permissions` and `self.current_sim_hardware_status`, populated from `AISimulationControlService`.
    *   The AI can query the full UI via `avis.get_current_virtual_ui()`.
    *   Dedicated UI elements (`ai_permissions_display`, `sim_hw_status_display`) are updated by AVIS to show current permissions and hardware status. AVIS provides `refresh_simulation_status()` to update these and the internal state.
*   **AI Interaction Loop (Simulated - General):**
    1.  **(Setup)** External agent loads UI into AVIS.
    2.  AI queries AVIS for UI, permissions, HW status.
    3.  AI analyzes this info and decides on an action (mouse, keyboard, or preparing code).
    4.  AI sends command to AVIS.
    5.  AVIS processes, updates internal state, logs, returns outcome.
    6.  AI queries again to see results.
*   **AI Interaction Loop (Code Execution - v0.4):**
    1.  AI types code into the `code_editor` element using `type_string` commands.
    2.  AI clicks the `run_code_button` element using a `click` command.
    3.  AVIS (via `AISimulationControlService`) executes the code (checking permissions).
    4.  AVIS updates the `code_output_display` element with results (`stdout`, `stderr`, status).
    5.  AI reads the `code_output_display` element's value to get feedback.

## 9. Open Questions and Future Considerations

*   **Detailed structure of `VirtualInputElementDescription.attributes`:** What common attributes are needed (e.g., 'href' for links, 'is_checked' for checkboxes, 'is_scrollable')?
*   **Complex Keyboard Actions:** Handling sustained key presses (hold shift, type, release shift), complex shortcuts and their effects on UI state.
*   **Feedback for Actual Control:** How to get reliable element information from real applications (Accessibility APIs, OCR, UI automation frameworks like Selenium for web, etc.). This is the largest challenge for non-simulated control.
*   **Error Handling in AVIS:** How does AVIS report errors more granularly (e.g., `element_id` not found, action not possible on element type, element disabled)? The `AVISActionLogEntry` includes an `outcome` and `outcome_message`.
*   **Focus Management:** Detailed logic for how virtual focus is managed, especially with 'Tab' or programmatic focus changes.
*   **Window Management:** Virtual actions related to windows themselves (focus window, close window, resize - likely out of scope for initial simulation focus).
*   **Security and Safety for Actual Control:** Defining robust mechanisms to prevent misuse or unintended actions if/when actual control is implemented. This includes rate limiting, interrupt mechanisms, and context validation.
*   **Integration with AI's Planning/Task Execution:** How will an AI agent use AVIS as part of a larger plan to achieve a goal?
*   **Advanced Feedback Mechanisms (Deep Mapping & Adaptive Capture):**
    *   **Dynamic Screen Analysis:** Future versions should explore dynamic screen capture and analysis (e.g., using computer vision, OCR, or accessibility APIs) to transform real-time screen output into a structured understanding of UI elements, their properties, and their relationships ("Guanxi," e.g., for folder structures or UI layouts). This "deep mapping" would provide a much richer and more accurate environmental model for the AI.
    *   **Performance-Adaptive Capture:** The screen analysis process can be resource-intensive. The system should ideally adjust the frequency, detail, or scope of screen capture and processing based on available computer performance (CPU, GPU, memory). This requires hardware identification and load monitoring capabilities, which may be a prerequisite foundational service (potentially related to `Fragmenta_design_spec.md`'s hardware awareness concepts).

This v0.3 specification provides a foundational design for the AI Virtual Input System, prioritizing element-based interaction and a simulation-first approach with stateful virtual UI, while acknowledging pathways for more advanced perceptual capabilities and actual control.

**v0.4 Update Scope:** This version (v0.4) introduces capabilities for AI-driven code execution within the AVIS environment, mediated by a new `AISimulationControlService`. This includes UI elements for code input/output, and displays for AI permissions and simulated hardware status.
