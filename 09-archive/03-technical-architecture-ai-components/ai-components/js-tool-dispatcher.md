# JavaScript Tool Dispatcher

## Overview

The `JSToolDispatcher` (`src/tools/js_tool_dispatcher/index.js`) is a specialized component within the Unified-AI-Project designed to **integrate and execute tools implemented in JavaScript (Node.js)**. It extends the AI's capabilities beyond Python-based tools, allowing for the leverage of the vast JavaScript ecosystem for specific functionalities.

This module is crucial for scenarios where certain tasks are more efficiently handled by JavaScript, or where existing JavaScript libraries and APIs need to be integrated into the AI's operational toolkit.

## Key Responsibilities and Features

1.  **JavaScript Tool Integration**: 
    *   Provides an entry point for the AI to interact with and utilize tools written in JavaScript.
    *   Enables the execution of Node.js-based scripts as part of the AI's task execution flow.

2.  **Tool Registry Management**: 
    *   Loads tool definitions from a `tool_registry.json` file.
    *   The registry specifies each tool's `name`, `description`, `scriptPath`, `handlerFunction`, `enabled` status, `parameters`, and `returns` schema.

3.  **Tool Dispatching (`dispatch`)**: 
    *   Takes a `toolName` and `params` (parameters) as input.
    *   Locates the corresponding JavaScript tool based on the registry.
    *   Executes the specified `handlerFunction` within the JavaScript tool's script, passing the provided parameters.
    *   Handles errors during tool execution and returns a structured success or failure response.

4.  **Tool Listing (`listTools`)**: 
    *   Returns a list of all available JavaScript tools that are registered with the dispatcher.

## How it Works

The `JSToolDispatcher` initializes by reading its `tool_registry.json` file, which defines all the JavaScript tools it can manage. When a request to `dispatch` a tool comes in, it looks up the tool in its internal registry. If found and enabled, it executes the specified JavaScript function (or module) with the provided parameters. The results or errors from the JavaScript execution are then returned to the calling AI component.

## Integration with Other Modules

-   **`ToolDispatcher` (Python)**: The Python-based `ToolDispatcher` would likely be the primary caller of the `JSToolDispatcher`, acting as a router that decides whether a task should be handled by a Python tool or a JavaScript tool.
-   **`DailyLanguageModel`**: Could be trained to recognize intents that map to JavaScript tools, allowing natural language queries to trigger these functionalities.
-   **`ProjectCoordinator`**: Complex tasks might involve steps that require the unique capabilities of JavaScript-based tools, orchestrated by the `ProjectCoordinator`.

## Code Location

`src/tools/js_tool_dispatcher/`

-   `index.js`: The main JavaScript dispatcher logic.
-   `tool_registry.json`: Configuration file for registered JavaScript tools.
