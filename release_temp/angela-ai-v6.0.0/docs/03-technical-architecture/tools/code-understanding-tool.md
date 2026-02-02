# CodeUnderstandingTool: Introspecting the AI's Own Tools

## Overview

This document provides an overview of the `CodeUnderstandingTool` module (`src/tools/code_understanding_tool.py`). This tool is designed to inspect and understand the structure of other Python tools within the project.

## Purpose

The `CodeUnderstandingTool` provides the AI with a powerful metacognitive capability: the ability to introspect its own tools. This allows the AI to dynamically understand what tools it has at its disposal, what their functions are, what parameters they accept, and what they return. This is a crucial feature for enabling the AI to learn how to use new tools without requiring hardcoded information.

## Key Responsibilities and Features

*   **Tool Listing (`list_tools`)**: Provides a simple method to list the names of all available Python tools located in the `src/tools/` directory.
*   **Tool Description (`describe_tool`)**: 
    *   Accepts the name of a tool as input.
    *   Utilizes the `LightweightCodeModel` to perform a static analysis of the specified tool's source code.
    *   Extracts key structural information, including the tool's classes, methods, parameters (with types and defaults), return types, and docstrings.
    *   Formats this structured information into a clear, human-readable description that explains how to use the tool.
*   **Execution Routing (`execute`)**: The main entry point for the tool. It routes requests to either the `list_tools` or `describe_tool` method based on the `action` parameter.

## How it Works

The `CodeUnderstandingTool` relies on the `LightweightCodeModel` to perform the complex task of code analysis. When the `describe_tool` method is called, it passes the name of the target tool to the `LightweightCodeModel`. The `LightweightCodeModel` then reads the corresponding Python file, parses it into an Abstract Syntax Tree (AST), and traverses the tree to extract the relevant structural information. The `CodeUnderstandingTool` then takes this structured data and formats it into a comprehensive, human-readable string that effectively serves as a dynamically generated user manual for the tool.

## Integration with Other Modules

*   **`LightweightCodeModel`**: This is the core dependency that performs the static code analysis.
*   **`ToolDispatcher`**: The `CodeUnderstandingTool` is designed to be invoked by the `ToolDispatcher`. This allows the AI to use natural language to ask questions about its own capabilities (e.g., "What tools do you have?" or "How do I use the math_tool?").

## Code Location

`src/tools/code_understanding_tool.py`