# ToolDispatcher: Centralized Tool Routing and Execution

## Overview

This document provides an overview of the `ToolDispatcher` module (`src/tools/tool_dispatcher.py`). Its primary function is to act as a central router for invoking various tools and capabilities within the AI system. It abstracts the process of tool selection and execution, allowing the AI to seamlessly use a wide range of tools, including a calculator, logic evaluator, translator, code inspector, CSV analyzer, image generator, and a Retrieval-Augmented Generation (RAG) query engine.

## Key Responsibilities and Features

*   **Tool Registry**: Maintains a dictionary of available tools (`self.tools`) and their corresponding descriptions (`self.tool_descriptions`). This registry is the single source of truth for all tools that the dispatcher can access.
*   **Intent Recognition**: Utilizes a `DailyLanguageModel` (`self.dlm`) to perform intent recognition on natural language queries. This allows the dispatcher to intelligently infer which tool the user intends to use, even when not explicitly stated.
*   **Explicit Dispatch**: Supports direct dispatching to a specific tool when an `explicit_tool_name` is provided, bypassing the intent recognition step for more direct control.
*   **Tool Execution Wrappers**: Implements dedicated wrapper methods (e.g., `_execute_math_calculation`, `_execute_logic_evaluation`, `_execute_translation`) for each tool. These wrappers are responsible for:
    *   Handling parameter extraction and validation.
    *   Calling the actual tool functions with the correct arguments.
    *   Formatting the tool's output into a standardized `ToolDispatcherResponse`.
*   **Flexible Parameter Handling**: Intelligently extracts and passes parameters to the appropriate tool functions, accommodating different function signatures and parameter naming conventions.
*   **Dynamic Tool Management**: Includes methods (`add_tool`, `replace_tool`, `add_model`, `replace_model`) that allow for the dynamic addition or replacement of tools and models at runtime. This is achieved using Python's `exec` function, providing a powerful mechanism for extending the AI's capabilities without requiring a system restart.
*   **Conditional RAG Integration**: Conditionally integrates with the `RAGManager` (if it is available in the environment) to provide a powerful `rag_query` tool for retrieval-augmented generation tasks.

## How it Works

When a query is received, the `ToolDispatcher` first determines which tool to use. If an explicit tool name is provided, it directly calls that tool's wrapper. If not, it leverages the `DailyLanguageModel` to analyze the query and infer the user's intent. Once a tool is selected, the dispatcher calls the corresponding wrapper function. This wrapper extracts the necessary parameters from the query or the provided arguments, invokes the actual tool function, and then standardizes the result (or any errors) into a `ToolDispatcherResponse` object. This structured response is then returned to the calling component.

## Integration with Other Modules

*   **`DailyLanguageModel`**: A core dependency used for intent recognition from natural language queries.
*   **`MultiLLMService`**: Passed to the `DailyLanguageModel` to power its language understanding capabilities.
*   **Various Tool Modules**: The `ToolDispatcher` directly integrates with and dispatches requests to a suite of tool modules, including `math_tool`, `logic_tool`, `translation_tool`, `code_understanding_tool`, `csv_tool`, and `image_generation_tool`.
*   **`RAGManager`**: An optional but important integration for providing retrieval-augmented generation capabilities.
*   **`ToolDispatcherResponse`**: The standardized response format defined in `src.shared.types.common_types`, used for all tool responses.

## Code Location

`src/tools/tool_dispatcher.py`