# AI Virtual Input System - Design Specification v0.2

## 1. Introduction

This document outlines the design for the AI Virtual Input System (AVIS), a system enabling the Unified-AI-Project to simulate and (with strict permissions) execute mouse and keyboard interactions within a computer's graphical user interface (GUI). The primary goal is to allow the AI to perform tasks that require GUI manipulation, expanding its capabilities beyond text-based interactions and tool usage.

This system is foundational for exploring how an AI's behavior, decision-making, and problem-solving strategies evolve when granted more direct agency within a typical computing environment.

**Key Goals:**
*   Enable simulation of GUI interactions for research and development.
*   Provide a framework for potential future direct GUI control by the AI.
*   Explore AI decision-making in environments requiring visual-spatial reasoning and action sequences.
*   Prioritize safety and control, especially regarding actual system input.

## 2. Scope

*   **Initial Focus (Simulation):** The primary development will focus on creating a robust simulation layer. The AI will issue virtual mouse and keyboard commands, and the AVIS will log these intents, potentially updating an internal model of a virtual UI or cursor state, without directly affecting the host operating system's input devices.
*   **Future Capability (Actual Control):** The design anticipates future extension to allow translation of virtual commands into actual system inputs (e.g., using libraries like `pynput` or `pyautogui`). This capability will be:
    *   Considered lower priority for initial implementation.
    *   Subject to a strict, explicit, and granular permissions system (see Section 6).
    *   Developed with utmost caution regarding security and unintended actions.

## 3. Core Concepts

### 3.1. Element-Based Interaction (Primary Paradigm)
The AI will primarily interact with GUI elements symbolically rather than through raw coordinates. Commands will target elements identified by a unique `element_id`.
*   **Example:** `click_element(element_id='login_button')` is preferred over `click_at_pixel(x=752, y=480)`.

### 3.2. Coordinate System
*   **Relative Coordinates:** When precise positioning is needed (e.g., within a specific element like a canvas, or for general mouse movement not tied to an element), relative coordinates (typically floats between 0.0 and 1.0) will be used.
    *   **Element-Relative:** Coordinates are relative to the bounds of a specified `target_element_id`. For example, `(0.5, 0.5)` would be the center of the element.
    *   **Window/Screen-Relative (for general movement):** Coordinates or deltas are relative to the current window or screen context (e.g., `move_mouse_relative(delta_x_ratio=0.1, delta_y_ratio=-0.05)`).
*   **Absolute Coordinates:** Direct use of absolute screen coordinates is generally discouraged due to its brittleness across different screen resolutions, window sizes, and UI layouts. If supported in the future for actual control, it will be under strict permissions.

### 3.3. Feedback Mechanism (AI Perception of UI)
For the AI to make informed decisions and use element IDs or relative coordinates effectively, it needs to "perceive" the UI.
*   **Initial Simulation Model (v0.1-v0.2 AVIS Implementation):**
    *   The AVIS service can now maintain an internal state representing a simple, single virtual window/UI (`self.virtual_ui_elements`).
    *   This state is a list of `VirtualInputElementDescription` objects, which can be loaded via a method like `avis.load_virtual_ui([...])`.
    *   The AI can "perceive" this current virtual UI by calling a method like `avis.get_current_virtual_ui() -> List[VirtualInputElementDescription]`. This method effectively serves the role of the originally conceptualized `get_screen_elements()` for the simulated environment.
    *   This allows the AI to receive a structured description of available elements, their types, labels, values, states, and conceptual relative bounds.
*   **Stateful Simulation:** Crucially, AI actions like typing into a field (`action_type="type_string"` on a `VirtualKeyboardCommand`) now modify the `value` attribute of the corresponding `VirtualInputElementDescription` within AVIS's internal `virtual_ui_elements` state. Similarly, a click can update the `virtual_focused_element_id`. This means the AI can observe the results of its actions in subsequent calls to `get_current_virtual_ui()`.
*   **Future (for Actual Control & Advanced Simulation):** As previously noted, integration with OS-level accessibility APIs, screen scraping with OCR, or specialized computer vision models would be necessary to parse real application UIs or more complex simulated environments. The "Advanced Feedback Mechanisms" in Section 8 further detail this.

## 4. Supported Virtual Actions (and their effects on simulated state)

The AVIS will support a range of mouse and keyboard actions. These actions are represented by commands sent to the AVIS. In simulation mode, these primarily result in logging and updates to the AVIS's internal virtual state.

### 4.1. Mouse Actions
*   `get_current_virtual_ui()`: (Replaces conceptual `get_screen_elements()`) AI requests a description of currently "visible" UI elements within the AVIS's managed virtual window.
*   `focus_element(element_id: str)`: (Conceptual AVIS command, or handled by `click`) Sets the virtual input focus (`virtual_focused_element_id` in AVIS) to the specified UI element. A `click` action also updates this focus.
*   `click_element(element_id: str, click_type: Literal['left', 'right', 'double'], relative_x: Optional[float], relative_y: Optional[float])`: Simulates a click. **Effect on State:** Updates `virtual_focused_element_id`. Future enhancements could allow clicks to modify attributes of the clicked element or other elements in the `virtual_ui_elements` based on predefined rules for simulated interactive elements (e.g., toggling a checkbox's 'value' or 'is_checked' attribute).
*   `hover_element(element_id: str, relative_x: Optional[float], relative_y: Optional[float])`: Simulates moving the virtual mouse pointer over a specified element, potentially at a relative position within it.
*   `drag_element_to_position(source_element_id: str, target_window_relative_x: float, target_window_relative_y: float)`: Simulates clicking and dragging an element to a specified relative position within the current window/screen.
*   `drag_element_to_element(source_element_id: str, target_element_id: str)`: Simulates clicking and dragging an element onto another target element.
*   `scroll_element(element_id: str, direction: Literal['up', 'down', 'left', 'right'], amount_ratio: Optional[float], pages: Optional[int])`: Simulates scrolling within a scrollable element. `amount_ratio` is a ratio of the scrollable area (e.g., 0.1 for 10%), or `pages` for page-based scrolling.
*   `move_mouse_relative(delta_x_ratio: float, delta_y_ratio: float)`: Moves the virtual mouse pointer by a ratio of the current screen/window dimensions from its current position.

### 4.2. Keyboard Actions
*   `type_string(text: str, target_element_id: Optional[str])`: Simulates typing a string of characters. If `target_element_id` is provided, AVIS first attempts to find and (virtually) focus that element. If successful and the element is typable (e.g., has a `value` attribute), its `value` in the `virtual_ui_elements` state is updated. Otherwise, it types into the currently virtually focused element if it's typable.
*   `press_keys(keys: List[str], target_element_id: Optional[str])`: Simulates pressing one or more keys. If `target_element_id` is provided, `virtual_focused_element_id` is updated. **Effect on State:** Primarily updates focus; direct modification of element values by key presses (other than `type_string`) is not deeply simulated yet (e.g., 'Enter' submitting a form).
*   `special_key(key_name: Literal['enter', 'tab', 'esc', ...], target_element_id: Optional[str])`: Simulates pressing a special non-character key. If `target_element_id` is provided, `virtual_focused_element_id` is updated. **Effect on State:** Similar to `press_keys`; specific behaviors of special keys on UI elements (e.g., 'Tab' changing focus, 'Enter' activating a button) are not deeply simulated in v0.1 but are logged.

## 5. API and Data Structures (TypedDicts)

The interaction with AVIS will be through commands defined by TypedDicts. These types will be defined in `src/shared/types/common_types.py` (or a dedicated `virtual_input_types.py`).

*   **`VirtualMouseEventType = Literal[...]`**: Defines valid mouse action types (e.g., "click", "move_relative_to_element", "scroll").
*   **`VirtualKeyboardActionType = Literal[...]`**: Defines valid keyboard action types (e.g., "type_string", "press_keys").
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
    *   `text_to_type: Optional[str]`
    *   `keys: Optional[List[str]]` (e.g., ["ctrl", "c"], ["enter"])

## 6. Permissions Model

A simple, two-tier permissions model will be implemented initially:

1.  **`simulation_only` (Default Mode):**
    *   All AVIS commands are processed internally.
    *   Actions are logged, and a virtual UI state (if maintained) is updated.
    *   No actual OS-level mouse or keyboard events are generated.
    *   This is the safe default for all AI operations using AVIS unless explicitly overridden.
2.  **`allow_actual_input` (Future, Highly Restricted Mode):**
    *   This mode requires explicit runtime permission grants. The mechanism for granting this permission must be secure and auditable (e.g., a specific configuration setting that is off by default, requiring manual intervention to enable, plus potentially runtime confirmation prompts for sensitive actions).
    *   Permissions might be further refined (e.g., allow actual input only for specific applications, or only keyboard, not mouse).
    *   **Security Warning:** Enabling actual input control has significant security implications and risks unintended system interactions. This feature must be developed with extreme caution, robust safety checks, and clear user consent and control mechanisms. AVIS should never default to this mode.

## 7. Simulation Environment & Feedback Loop

*   **Virtual Environment State:** The AVIS service now maintains an internal list of `VirtualInputElementDescription` objects (`virtual_ui_elements`) representing the current state of the simulated window. This state can be loaded using `avis.load_virtual_ui()`.
*   **AI Interaction Loop (Simulated v0.2):**
    1.  **(Setup)** An external process or test harness loads an initial UI state into AVIS using `avis.load_virtual_ui(initial_elements)`.
    2.  AI (via a tool or agent logic) queries AVIS for the current UI state: `current_elements = avis.get_current_virtual_ui()`.
    3.  AI analyzes `current_elements` to identify target elements and decide on an action.
    4.  AI sends a `VirtualMouseCommand` or `VirtualKeyboardCommand` to `avis.process_mouse_command()` or `avis.process_keyboard_command()`.
    5.  AVIS (in simulation mode):
        *   Logs the command.
        *   Updates its internal `virtual_ui_elements` state if the action has a defined effect (e.g., typing into a text field updates its `value`; clicking an element updates `virtual_focused_element_id`).
        *   Returns a status indicating the outcome of the simulated action (e.g., whether a field's value was updated).
    6.  The AI can then call `get_current_virtual_ui()` again to perceive the results of its action on the virtual UI.

## 8. Open Questions and Future Considerations

*   **Detailed structure of `VirtualInputElementDescription.attributes`:** What common attributes are needed (e.g., 'href' for links, 'is_checked' for checkboxes)?
*   **Complex Keyboard Actions:** Handling sustained key presses (hold shift, type, release shift), complex shortcuts.
*   **Feedback for Actual Control:** How to get reliable element information from real applications (Accessibility APIs, OCR, UI automation frameworks like Selenium for web, etc.). This is the largest challenge for non-simulated control.
*   **Error Handling:** How does AVIS report errors (e.g., `element_id` not found, action not possible on element type)?
*   **Focus Management:** Detailed logic for how virtual focus is managed.
*   **Window Management:** Virtual actions related to windows themselves (focus window, close window, resize - likely out of scope for v0.1).
*   **Security and Safety for Actual Control:** Defining robust mechanisms to prevent misuse or unintended actions if/when actual control is implemented. This includes rate limiting, interrupt mechanisms, and context validation.
*   **Integration with AI's Planning/Task Execution:** How will an AI agent use AVIS as part of a larger plan to achieve a goal?
*   **Advanced Feedback Mechanisms (Deep Mapping & Adaptive Capture):**
    *   **Dynamic Screen Analysis:** Future versions should explore dynamic screen capture and analysis (e.g., using computer vision, OCR, or accessibility APIs) to transform real-time screen output into a structured understanding of UI elements, their properties, and their relationships ("Guanxi," e.g., for folder structures or UI layouts). This "deep mapping" would provide a much richer and more accurate environmental model for the AI.
    *   **Performance-Adaptive Capture:** The screen analysis process can be resource-intensive. The system should ideally adjust the frequency, detail, or scope of screen capture and processing based on available computer performance (CPU, GPU, memory). This requires hardware identification and load monitoring capabilities, which may be a prerequisite foundational service (potentially related to `Fragmenta_design_spec.md`'s hardware awareness concepts).

This v0.1 specification provides a foundational design for the AI Virtual Input System, prioritizing element-based interaction and a simulation-first approach, while acknowledging pathways for more advanced perceptual capabilities.
