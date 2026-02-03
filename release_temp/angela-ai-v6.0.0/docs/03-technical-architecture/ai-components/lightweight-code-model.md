# LightweightCodeModel: Static Analysis for Python Code Understanding

## Overview

This document provides an overview of the `LightweightCodeModel` module (`src/core_ai/code_understanding/lightweight_code_model.py`). This module is designed to perform lightweight static analysis of Python code, with a specific focus on understanding the structure of tools within the project.

## Purpose

The `LightweightCodeModel` provides the AI with a crucial metacognitive capability: the ability to introspect and understand the structure of its own Python code, particularly its tools. This is fundamental for enabling the AI to dynamically learn how to use tools, generate documentation for them, or even assist in modifying its own codebase.

## Key Responsibilities and Features

*   **Tool File Listing (`list_tool_files`)**: Scans a specified `tools_directory` (which defaults to `src/tools/`) and identifies all relevant Python files. It intelligently excludes common non-tool files like `__init__.py` and `tool_dispatcher.py` to provide a clean list of actual tool modules.
*   **Static Code Analysis (`analyze_tool_file`)**:
    *   Takes a Python file path as input.
    *   Utilizes Python's built-in `ast` (Abstract Syntax Tree) module to parse the source code without executing it, ensuring safety.
    *   Extracts comprehensive structural information, including class names, method names, function names, associated docstrings, detailed parameter information (names, type annotations, and default values), and return types.
    *   Returns this extracted information in a structured dictionary format, making it easily consumable by other AI components.
*   **Tool Structure Retrieval (`get_tool_structure`)**: 
    *   Serves as the main interface for retrieving a tool's structural information.
    *   It is flexible, accepting either a direct file path to a Python file or a tool name (e.g., "math_tool").
    *   If a tool name is provided, it intelligently attempts to resolve the full file path by looking for common naming conventions (e.g., `tool_name.py`, `tool_tool_name.py`, or `tool_name_tool.py`) within the configured `tools_directory`.
    *   Includes logic to handle ambiguous tool names (where multiple files match a pattern) or cases where no matching file is found, returning `None` and logging warnings.

## How it Works

At its core, the `LightweightCodeModel` leverages Python's `ast` module to perform static analysis. When a request to analyze a tool is made, it reads the tool's Python source file, parses it into an Abstract Syntax Tree, and then traverses this tree to extract all relevant structural metadata. This metadata is then organized into a standardized dictionary, which can be used by other AI components to understand the tool's interface and functionality.

## Integration with Other Modules

*   **`CodeUnderstandingTool`**: This module is the primary consumer of `LightweightCodeModel`, using it to provide introspection capabilities to the AI, allowing the AI to answer questions about its own tools.
*   **Standard Python Libraries**: Relies heavily on `ast` for code parsing, `os` for file system operations, and `glob` for pattern matching and file discovery.

## Code Location

`src/core_ai/code_understanding/lightweight_code_model.py`