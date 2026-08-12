# Formula Engine

## Overview

The `FormulaEngine` (`src/core_ai/formula_engine/__init__.py`) is a core component within the Unified-AI-Project responsible for managing and executing predefined rules or "formulas" based on specific input conditions. It allows the AI to respond to certain patterns or contexts with predetermined actions, providing a layer of deterministic behavior within the otherwise dynamic AI system.

This module is essential for implementing:

-   **Rule-based responses**: Enabling the AI to react predictably to specific user commands or system events.
-   **Automated tasks**: Triggering predefined actions when certain conditions are met.
-   **Configurable behaviors**: Allowing system administrators or designers to define and modify AI behaviors without altering core code.

## Key Responsibilities and Features

1.  **Formula Loading and Management (`_load_formulas`)**:
    *   Loads formula definitions from an external JSON file (defaulting to `configs/formula_configs/default_formulas.json`).
    *   Each formula is defined by a `FormulaConfigEntry` (TypedDict) which includes:
        *   `name`: Unique identifier for the formula.
        *   `conditions`: A list of strings that, if found in the input, will trigger the formula.
        *   `action`: The name of the action to be performed when the formula matches.
        *   `description`: A human-readable explanation of the formula's purpose.
        *   `parameters`: Optional dictionary of parameters to be passed to the action.
        *   `priority`: An integer indicating the formula's priority (lower number = higher priority).
        *   `enabled`: A boolean to enable or disable the formula.
        *   `version`: Version of the formula.
    *   Formulas are sorted by priority, ensuring that higher-priority rules are matched first.

2.  **Input Matching (`match_input`)**:
    *   Takes a text input and attempts to find a matching formula based on its defined `conditions`.
    *   Performs a case-insensitive substring match for conditions within the input text.
    *   Returns the first matched formula based on priority.

3.  **Formula Execution (`execute_formula`)**:
    *   "Executes" a matched formula by returning its `action_name` and `action_params`.
    *   This allows other modules (e.g., `DialogueManager`) to then dispatch the specified action to the appropriate tool or service.

## How it Works

The `FormulaEngine` maintains a list of loaded formulas. When `match_input` is called with a user query or system event, it iterates through its sorted list of formulas. For each formula, it checks if any of its defined conditions are present in the input. If a match is found, and the formula is enabled, that formula is returned. The `execute_formula` method then provides the necessary details for the calling module to perform the action associated with the matched formula.

## Integration with Other Modules

-   **`DialogueManager`**: The primary consumer of the `FormulaEngine`. It uses the engine to identify and respond to specific user commands or patterns with predefined actions.
-   **`ToolDispatcher`**: The `FormulaEngine` often works in conjunction with the `ToolDispatcher`, where the `action` defined in a formula corresponds to a tool that the `ToolDispatcher` can invoke.
-   **Configuration System**: Relies on external JSON files for flexible and dynamic formula definitions.

## Code Location

`src/core_ai/formula_engine/__init__.py`
