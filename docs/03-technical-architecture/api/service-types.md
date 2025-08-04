# Service Types: Data Structures for Service Layer

## Overview

The `types.py` (`src/services/types.py`) module defines the **TypedDicts** used across various services within the Unified-AI-Project. These type definitions are crucial for ensuring data consistency, clarity, and type safety when interacting with services related to virtual input (simulated GUI interactions) and simulated hardware resources.

This module acts as a central repository for the schemas of data objects passed between different service components, facilitating robust development and integration.

## Key Type Definitions

### 1. Virtual Input Types

These types are primarily used by the `AIVirtualInputService` to describe UI elements and commands for simulated mouse and keyboard interactions.

-   **`VirtualInputElementDescription`**:
    *   Describes a single UI element within a virtual environment.
    *   Fields include `element_id`, `element_type` (e.g., "button", "text_field"), `label`, `value`, `is_focused`, `is_enabled`, `is_visible`, `attributes` (for additional properties), and `children` (for nested elements).

-   **`VirtualInputPermissionLevel`**:
    *   A Literal type defining the permission levels for virtual input actions:
        *   `"simulation_only"`: Actions are only simulated and logged.
        *   `"requires_user_confirmation"`: Actions require explicit user confirmation before execution.
        *   `"full_control_trusted"`: Full control is granted (highly restricted and for trusted environments).

-   **`VirtualMouseEventType`**:
    *   A Literal type defining the various types of virtual mouse actions (e.g., "move_relative_to_window", "click", "double_click", "scroll").

-   **`VirtualMouseCommand`**:
    *   Defines the structure of a command to perform a virtual mouse action.
    *   Includes `action_type`, `target_element_id`, relative coordinates (`relative_x`, `relative_y`), `click_type`, `scroll_direction`, `scroll_amount_ratio`, `scroll_pages`, and drag-related parameters.

-   **`VirtualKeyboardActionType`**:
    *   A Literal type defining the various types of virtual keyboard actions (e.g., "type_string", "press_keys", "special_key").

-   **`VirtualKeyboardCommand`**:
    *   Defines the structure of a command to perform a virtual keyboard action.
    *   Includes `action_type`, `target_element_id`, `text_to_type` (for typing strings), and `keys` (for pressing individual or combinations of keys).

### 2. Simulated Resource Types

These types are primarily used by the `ResourceAwarenessService` to define and communicate the AI's simulated hardware profile.

-   **`SimulatedDiskConfig`**:
    *   Describes the configuration of a simulated disk, including `space_gb`, `warning_threshold_percent`, `critical_threshold_percent`, and `lag_factor` for different states.

-   **`SimulatedCPUConfig`**:
    *   Describes the configuration of a simulated CPU, primarily its `cores` count.

-   **`SimulatedRAMConfig`**:
    *   Describes the configuration of simulated RAM, specifically `ram_gb`.

-   **`SimulatedHardwareProfile`**:
    *   A composite type representing the entire simulated hardware profile.
    *   Includes `profile_name`, and nested configurations for `disk`, `cpu`, `ram`, and `gpu_available` status.

-   **`SimulatedResourcesRoot`**:
    *   The root structure for loading simulated resources configuration, containing the `simulated_hardware_profile`.

## Importance and Usage

These TypedDicts serve several important purposes:

-   **Type Safety**: They provide clear type hints, allowing for static analysis and reducing runtime errors related to incorrect data structures.
-   **Documentation**: They act as self-documenting schemas for the data exchanged between services.
-   **Consistency**: They enforce a consistent data format across the service layer, making integration and development more predictable.
-   **Clarity**: They improve code readability by explicitly defining the expected keys and types of dictionaries.

## Code Location

`src/services/types.py`
