# Code Understanding Tool

## Overview

The `CodeUnderstandingTool` (`src/tools/code_understanding_tool.py`) is a specialized utility that empowers the AI to **introspect and comprehend the structure and capabilities of other Python tools** within the Unified-AI-Project. By leveraging the `LightweightCodeModel`, this tool provides the AI with a programmatic way to "read" and "understand" its own codebase, which is crucial for advanced self-modification, automated task planning, and intelligent tool selection.

This module is essential for enabling the AI to reason about its own functionalities and adapt its behavior based on the available tools.

## Key Responsibilities and Features

1.  **Tool Listing (`list_tools`)**:
    *   Scans the designated tools directory (defaulting to `src/tools/`) and returns a human-readable list of all available Python tools by their names.

2.  **Detailed Tool Description (`describe_tool`)**:
    *   Given a `tool_name`, it provides a comprehensive, human-readable description of that tool's internal structure.
    *   The description includes:
        *   The tool's file path.
        *   Docstrings for the tool's classes and functions.
        *   Signatures (names, parameters with types and default values, return types) for all methods and module-level functions.

3.  **Integration with `LightweightCodeModel`**: 
    *   Relies heavily on the `LightweightCodeModel` (`src/core_ai/code_understanding/lightweight_code_model.py`) to perform the actual static analysis of Python code files.
    *   The `CodeUnderstandingTool` acts as a user-facing wrapper around the `LightweightCodeModel`'s capabilities.

## How it Works

When `list_tools` is called, the tool uses `LightweightCodeModel` to find all Python files in the tools directory and extracts their names. When `describe_tool` is invoked, it passes the `tool_name` to `LightweightCodeModel` to get a structured representation of the tool's code. It then formats this structured data into a clear, human-readable string, including docstrings and function/method signatures, making it easy for the AI (or a human developer) to understand the tool's functionality.

## Integration with Other Modules

-   **`ToolDispatcher`**: The `ToolDispatcher` could potentially use `list_tools` to dynamically discover available tools and `describe_tool` to understand their parameters before invoking them.
-   **`DailyLanguageModel`**: An advanced `DailyLanguageModel` could use this tool to understand the capabilities of various tools and generate more accurate and context-aware tool calls.
-   **`ProjectCoordinator`**: When planning complex tasks, the `ProjectCoordinator` might query this tool to identify suitable sub-tools for specific steps.
-   **`CreationEngine`**: After the `CreationEngine` generates new tool code, the `CodeUnderstandingTool` could be used to verify the structure and ensure it meets expected standards.

## Code Location

`src/tools/code_understanding_tool.py`
