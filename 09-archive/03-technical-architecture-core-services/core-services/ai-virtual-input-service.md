# AIVirtualInputService (AVIS): Simulated GUI Interaction for AI

## Overview

This document provides an overview of the `AIVirtualInputService` module (`src/services/ai_virtual_input_service.py`). Its primary function is to provide a simulated environment that allows the AI to interact with graphical user interfaces (GUIs) by sending virtual mouse and keyboard commands.

This module is crucial for enabling the development, testing, and training of AI agents that operate on GUIs without requiring actual physical interaction. It logs these virtual actions and maintains a simplified virtual UI state, offering a safe and controlled sandbox for UI automation and learning.

## Key Responsibilities and Features

*   **Simulation Mode (`simulation_only`)**: The primary operational mode where all virtual input commands are processed internally, logged, and used to update a simulated UI state. No actual system input is generated. This ensures a safe environment for AI experimentation and learning. Future extensions are envisioned to allow real system control under strict permission levels.
*   **Virtual UI Management**: 
    *   `load_virtual_ui(elements)`: Allows the AI to load or completely replace the current simulated UI with a new set of `VirtualInputElementDescription` objects. This enables dynamic changes to the AI's perceived environment.
    *   `get_current_virtual_ui()`: Provides the AI with a deep copy of the current virtual UI element structure, representing what the AI "sees" on the simulated screen.
    *   `_find_element_by_id()`: A recursive helper method to locate specific UI elements within the virtual UI structure by their unique ID.
*   **Virtual Input Processing**: 
    *   **Mouse Commands (`process_mouse_command`)**: Processes virtual mouse actions such as `move_relative_to_window` (updating cursor position), `click` (simulating clicks on elements or positions), `hover`, and `scroll`. It updates the `virtual_cursor_position` and `virtual_focused_element_id` accordingly.
    *   **Keyboard Commands (`process_keyboard_command`)**: Processes virtual keyboard actions like `type_string` (simulating text input into elements), `press_keys` (simulating key presses), and `special_key` (for special keys like Enter, Tab). It updates the `virtual_focused_element_id` and can modify the `value` attribute of text input elements.
*   **Action Logging (`_log_action`, `get_action_log`, `clear_action_log`)**: Maintains a detailed, timestamped log of all virtual input commands processed by the service, including command details and their simulated outcomes. This log is invaluable for debugging, analysis, and training.
*   **Virtual State Reporting (`get_virtual_state`)**: Provides a summary of the current simulated virtual environment, including the service's mode, the virtual cursor's position, the currently focused element, and the count of logged actions.
*   **Type Definitions**: Relies on structured `TypedDict` types (e.g., `VirtualInputPermissionLevel`, `VirtualMouseCommand`, `VirtualKeyboardCommand`, `VirtualInputElementDescription`) defined in `services.types` to ensure clear and consistent communication of virtual input commands and UI element descriptions.

## How it Works

The `AIVirtualInputService` operates by maintaining an internal, abstract representation of a user interface. When an AI agent issues a virtual input command (e.g., "click button X"), the service interprets this command and simulates its effect on this internal UI model. For instance, a "type_string" command might update the `value` attribute of a virtual text input element. All these simulated interactions are meticulously logged, providing a rich dataset for AI learning and analysis. This allows an AI to "practice" interacting with a UI, learn optimal interaction sequences, and develop robust UI automation strategies without affecting the real system or requiring a visual rendering engine.

## Integration with Other Modules

*   **`services.types`**: Defines the essential data structures for virtual input commands and UI elements, ensuring type safety and clarity.
*   **AI Agents**: Agents designed to perform UI automation or interact with graphical interfaces would be primary consumers of this service, sending it virtual input commands.
*   **Testing Frameworks**: Can be integrated into automated testing pipelines to simulate user interactions and validate UI behavior for AI-driven applications.
*   **`DialogueManager`**: Could potentially use AVIS to simulate user input based on conversational context or to generate responses that involve guiding the user through UI interactions.
*   **`WorldModel`**: The virtual UI state could be considered part of the AI's world model, providing a structured representation of its environment.

## Code Location

`src/services/ai_virtual_input_service.py`