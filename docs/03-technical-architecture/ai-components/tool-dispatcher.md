# Tool Dispatcher: Intelligent Tool Routing

## Overview

The `ToolDispatcher` (`src/tools/tool_dispatcher.py`) is a central and intelligent component within the Unified-AI-Project responsible for **routing user queries or AI-generated requests to the most appropriate specialized tool**. It acts as a sophisticated intermediary, interpreting intent and orchestrating the execution of various functionalities available to the AI.

This module is crucial for enabling the AI to perform a wide range of tasks by leveraging a diverse set of tools, from mathematical calculations to code understanding and image generation.

## Key Responsibilities and Features

1.  **Intelligent Tool Routing**: 
    *   Determines which tool is best suited to handle a given `query`.
    *   Can operate in two modes:
        *   **Explicit Dispatch**: Directly calls a tool if its name is provided.
        *   **Inferred Dispatch**: Uses the `DailyLanguageModel` to recognize the user's intent and infer the most suitable tool and its parameters from natural language.

2.  **Intent Recognition Integration**: 
    *   Leverages the `DailyLanguageModel` (`src/core_ai/language_models/daily_language_model.py`) to perform sophisticated intent recognition, extracting the target tool and necessary parameters from complex natural language queries.

3.  **Multi-Tool Integration**: 
    *   Integrates with a wide array of specialized tools, including:
        *   `math_tool` (for arithmetic calculations)
        *   `logic_tool` (for logical expression evaluation)
        *   `translation_tool` (for language translation)
        *   `CodeUnderstandingTool` (for code introspection)
        *   `CsvTool` (for CSV data analysis)
        *   `ImageGenerationTool` (for image creation)
        *   (Potentially `RAGManager` for retrieval-augmented generation)

4.  **Structured Response Handling**: 
    *   All tool executions return a `ToolDispatcherResponse` object, which provides a consistent structure for success, failure, payload, and error messages.

5.  **Dynamic Tool Management (Conceptual)**: 
    *   Includes placeholder methods (`add_model`, `replace_model`, `add_tool`, `replace_tool`) that hint at future capabilities for dynamically adding or updating tools and models at runtime, allowing the AI to expand its own toolkit.

## How it Works

When a `dispatch` request is made, the `ToolDispatcher` first checks if an `explicit_tool_name` is provided. If so, it directly calls the corresponding tool. Otherwise, it passes the user's `query` to the `DailyLanguageModel` for intent recognition. The `DailyLanguageModel` returns the inferred `tool_name` and `parameters`. The `ToolDispatcher` then invokes the identified tool with the extracted parameters, wraps the tool's output in a `ToolDispatcherResponse`, and returns it.

## Integration with Other Modules

-   **`DialogueManager`**: The `DialogueManager` is the primary consumer of the `ToolDispatcher`, using it to execute specific actions or retrieve information based on user commands.
-   **`DailyLanguageModel`**: Provides the core intent recognition capabilities that enable the `ToolDispatcher` to intelligently select tools from natural language.
-   **Specialized Tools**: The `ToolDispatcher` acts as the orchestrator for all the individual tools, providing a unified interface to their functionalities.
-   **`ProjectCoordinator`**: Complex tasks orchestrated by the `ProjectCoordinator` often involve multiple steps that are delegated to specific tools via the `ToolDispatcher`.

## Code Location

`src/tools/tool_dispatcher.py`
