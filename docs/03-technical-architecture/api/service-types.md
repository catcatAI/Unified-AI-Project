# Service Types: Data Structures for Core Services and Simulated Environments

## Overview

This document provides a comprehensive overview of the TypedDicts and Literal types defined in the `src/services/types.py` module. These types define the fundamental data structures for representing virtual input (mouse and keyboard commands, UI element descriptions) and simulated hardware resources within the Unified-AI-Project.

This module is crucial for ensuring clear, type-safe, and consistent data handling and communication between core services like `AIVirtualInputService` and `ResourceAwarenessService`, and other AI components that interact with these simulated environments.

## Key Responsibilities and Features

### Virtual Input Types

These types are primarily used by the `AIVirtualInputService` to define how the AI interacts with and perceives a simulated graphical user interface:

*   **`VirtualInputElementDescription`**: Describes a single UI element in a virtual environment. It includes `element_id`, `element_type`, `label`, `value`, various state flags (`is_focused`, `is_enabled`, `is_visible`), generic `attributes`, and a recursive `children` field for hierarchical UI structures.
*   **`VirtualInputPermissionLevel` (Literal)**: Defines the operational modes for virtual input, such as `"simulation_only"` (commands are logged but not executed on the real system), `"requires_user_confirmation"`, and `"full_control_trusted"`.
*   **`VirtualMouseEventType` (Literal)**: Enumerates the specific types of virtual mouse actions that can be performed (e.g., `"move_relative_to_window"`, `"click"`, `"double_click"`, `"right_click"`, `"hover"`, `"drag_start"`, `"drag_end"`, `"scroll"`).
*   **`VirtualMouseCommand`**: Defines the structured command for a virtual mouse action. It includes the `action_type` (from `VirtualMouseEventType`), optional `target_element_id`, relative coordinates (`relative_x`, `relative_y`), `click_type`, and various scroll/drag parameters.
*   **`VirtualKeyboardActionType` (Literal)**: Enumerates the specific types of virtual keyboard actions (e.g., `"type_string"`, `"press_keys"`, `"release_keys"`, `"special_key"`).
*   **`VirtualKeyboardCommand`**: Defines the structured command for a virtual keyboard action. It includes the `action_type` (from `VirtualKeyboardActionType`), optional `target_element_id`, `text_to_type`, and a list of `keys` to press/release.

### Simulated Resource Types

These types are primarily used by the `ResourceAwarenessService` to describe the characteristics of a simulated hardware environment:

*   **`SimulatedDiskConfig`**: Describes the configuration of a simulated disk, including `space_gb`, `warning_threshold_percent`, `critical_threshold_percent`, and `lag_factor_warning`/`critical`.
*   **`SimulatedCPUConfig`**: Describes the configuration of a simulated CPU, primarily its `cores` count.
*   **`SimulatedRAMConfig`**: Describes the configuration of simulated RAM, specifying `ram_gb`.
*   **`SimulatedHardwareProfile`**: Aggregates the individual hardware configurations (`disk`, `cpu`, `ram`) and a boolean `gpu_available` into a single, comprehensive hardware profile.
*   **`SimulatedResourcesRoot`**: The top-level structure for a simulated resources configuration file, containing the `simulated_hardware_profile`.

## How it Works

These TypedDicts and Literal types serve as the formal data contracts for the `AIVirtualInputService` and `ResourceAwarenessService`. They define the expected shape and values of data that flows into and out of these services. This strong typing enables static analysis, ensures data integrity, and facilitates clear communication between different parts of the AI system that interact with simulated GUIs or query simulated hardware resources.

## Integration with Other Modules

*   **`AIVirtualInputService`**: Directly uses the `VirtualInputElementDescription`, `VirtualMouseCommand`, and `VirtualKeyboardCommand` types for its core functionality.
*   **`ResourceAwarenessService`**: Directly uses the `SimulatedHardwareProfile` and its nested configuration types (`SimulatedDiskConfig`, `SimulatedCPUConfig`, `SimulatedRAMConfig`) for loading and providing hardware information.
*   **AI Components**: Any AI component that needs to interact with a simulated GUI (e.g., for testing, training, or automation) or query simulated hardware resources would use these types to construct and interpret data.

## Code Location

`src/services/types.py`