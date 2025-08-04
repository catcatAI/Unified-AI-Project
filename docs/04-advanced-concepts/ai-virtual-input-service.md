# AI Virtual Input Service (AVIS): Simulated UI Interaction

## Overview

The `ai_virtual_input_service.py` (`src/services/ai_virtual_input_service.py`) module implements the **AI Virtual Input Service (AVIS)**. This service provides a simulated environment that enables the AI to **interact with graphical user interfaces (GUIs)** by sending virtual mouse and keyboard commands. It logs these actions and maintains a simplified virtual state of the UI.

AVIS is a critical component for the AI's ability to "see" and "act" on a user interface, laying the groundwork for advanced AI capabilities such as automated UI testing, intelligent automation, and human-computer interaction research within a controlled simulation.

## Key Responsibilities and Features

1.  **Virtual Input Simulation**: 
    *   Processes virtual mouse commands (`process_mouse_command`) such as moving the cursor, clicking, hovering, and scrolling.
    *   Processes virtual keyboard commands (`process_keyboard_command`) including typing strings, pressing individual keys, and handling special keys.
    *   Operates primarily in a `simulation_only` mode, logging intended actions without affecting the actual system.

2.  **Virtual UI Management**: 
    *   `load_virtual_ui`: Allows loading or replacing the current virtual UI with a new set of `VirtualInputElementDescription` elements.
    *   `get_current_virtual_ui`: Provides a snapshot of the AI's current perception of the simulated UI, enabling the AI to "see" the interface.
    *   Includes a recursive helper `_find_element_by_id` to locate specific elements within the virtual UI hierarchy.

3.  **Action Logging**: 
    *   Maintains a detailed `action_log` of all processed virtual input commands, including timestamps, command details, and outcomes.
    *   `get_action_log`: Retrieves a copy of the complete action history.
    *   `clear_action_log`: Resets the action history.

4.  **Virtual State Management**: 
    *   Tracks the `virtual_cursor_position` (relative to the abstract window/screen).
    *   Manages the `virtual_focused_element_id`, indicating which UI element is currently in focus.
    *   `get_virtual_state`: Provides a summary of the current simulated virtual state.

5.  **Permission Levels (`VirtualInputPermissionLevel`)**: 
    *   Defines different operational modes (e.g., `simulation_only`), with future potential for actual system control under strict permissions.

## How it Works

The AVIS operates by receiving virtual input commands from the AI. In `simulation_only` mode, these commands are processed internally, updating the service's virtual state (e.g., cursor position, focused element) and logging the actions. The AI can then query the `get_current_virtual_ui` method to understand the simulated UI's current state, effectively creating a feedback loop for AI-driven UI interaction within a safe, controlled environment.

## Integration with Other Modules

-   **AI Agents**: AI agents (e.g., `AgentManager`, `ToolDispatcher`) would send virtual input commands to AVIS to interact with simulated UIs.
-   **`types.py` (services)**: Relies on `VirtualInputPermissionLevel`, `VirtualMouseCommand`, `VirtualKeyboardCommand`, `VirtualMouseEventType`, `VirtualKeyboardActionType`, and `VirtualInputElementDescription` for defining input structures.
-   **Logging**: Integrates with the project's logging system to record all processed actions.

## Code Location

`src/services/ai_virtual_input_service.py`
