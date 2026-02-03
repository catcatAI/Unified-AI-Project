# Code Understanding Module: LightweightCodeModel

## Overview

The `LightweightCodeModel` (`src/core_ai/code_understanding/lightweight_code_model.py`) is a foundational AI component within the Unified-AI-Project responsible for performing static analysis of Python code. Its primary purpose is to enable the AI to understand the structure, components, and basic functionality of the tools and other Python modules within the project.

This module is crucial for AI capabilities that involve code generation, code review, automated documentation, or intelligent tool selection, as it provides the AI with a structured representation of the codebase.

## Key Responsibilities and Features

1.  **Tool File Discovery (`list_tool_files`)**:
    *   Identifies and lists Python files within a specified `tools_directory` (defaulting to `src/tools/`).
    *   Intelligently excludes common non-tool files like `__init__.py` and `tool_dispatcher.py`.

2.  **Code Structure Analysis (`analyze_tool_file`)**:
    *   Parses Python source code files using Python's built-in `ast` (Abstract Syntax Tree) module.
    *   Extracts high-level structural information, including:
        *   **Classes**: Their names, docstrings, and contained methods.
        *   **Functions**: Module-level functions, their docstrings, parameters, and return types.
    *   Provides a structured dictionary representation of the analyzed code, making it machine-readable and processable by other AI components.

3.  **Parameter Extraction (`_extract_method_parameters`)**:
    *   A helper method that meticulously extracts details about function/method parameters, including their names, type annotations, and default values.

4.  **Tool Structure Retrieval (`get_tool_structure`)**:
    *   Serves as the main interface for other modules to query the structure of a specific tool.
    *   Can resolve tool names (e.g., "math_tool") to their corresponding file paths by searching for common naming conventions (e.g., `math_tool.py`, `tool_math.py`).
    *   Supports direct file path input for analysis.

## How it Works

The `LightweightCodeModel` leverages Python's `ast` module to build a tree-like representation of the source code without executing it. By traversing this tree, it can programmatically extract metadata and structural information that is otherwise only available by reading the code manually. This allows the AI to "read" and "understand" code at a structural level.

## Integration with Other Modules

-   **`ToolDispatcher`**: Can use the `LightweightCodeModel` to dynamically understand the parameters and capabilities of available tools.
-   **`Documentation Generation Agents`**: Can leverage this module to automatically generate or update documentation based on the actual code structure and docstrings.
-   **`Code Review Agents`**: Can use the extracted structure to perform static analysis for code quality, style, or security vulnerabilities.
-   **`ProjectCoordinator`**: Can use it to verify the existence and structure of tools before dispatching tasks that require them.

## Code Location

`src/core_ai/code_understanding/lightweight_code_model.py`
