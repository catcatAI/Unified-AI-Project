# Daily Language Model (DLM)

## Overview

The `DailyLanguageModel` (`src/core_ai/language_models/daily_language_model.py`) is a specialized AI component within the Unified-AI-Project responsible for **interpreting natural language user input and identifying the user's intent**, particularly for the purpose of dispatching tasks to appropriate tools. It acts as a crucial bridge between raw human language and the structured actions the AI system can perform.

Unlike the `MultiLLMService` which provides a general interface to various LLMs, the `DailyLanguageModel` focuses on a specific application of LLMs: **tool selection and parameter extraction** based on conversational context.

## Key Responsibilities and Features

1.  **Intent Recognition for Tool Dispatching (`recognize_intent`)**:
    *   Analyzes user input to determine if it corresponds to a known tool's functionality.
    *   Constructs a detailed prompt for an underlying Large Language Model (LLM), providing the user's query and a list of available tools with their descriptions and expected parameters.
    *   Parses the LLM's JSON response to extract the identified `tool_name` and its corresponding `parameters`.
    *   Handles cases where no suitable tool is found, returning a `None` tool indication.

2.  **Prompt Engineering**: 
    *   Dynamically generates a highly structured prompt that guides the LLM to output a specific JSON format, ensuring reliable parsing of the LLM's response.
    *   Includes detailed instructions within the prompt for parameter extraction based on the selected tool, demonstrating sophisticated prompt engineering techniques.

3.  **Integration with `MultiLLMService`**: 
    *   Leverages the `MultiLLMService` to communicate with various commercial and open-source LLMs for intent recognition. This allows the `DailyLanguageModel` to remain flexible regarding the specific LLM used.

4.  **Robustness**: 
    *   Includes error handling for LLM response parsing (e.g., `json.JSONDecodeError`) and for cases where the LLM selects an unavailable tool.

## How it Works

When `recognize_intent` is called with a user query and a list of available tools, the `DailyLanguageModel`:

1.  **Constructs a Prompt**: It creates a carefully crafted prompt that instructs the LLM to act as a router, selecting the best tool and extracting its parameters in a JSON format.
2.  **Queries LLM**: It sends this prompt to the configured `MultiLLMService`.
3.  **Parses Response**: It attempts to parse the LLM's text response as a JSON object.
4.  **Validates & Returns Intent**: It validates the parsed JSON, ensuring a valid tool name is selected (or `NO_TOOL`) and extracts the parameters. The result is a structured dictionary indicating the AI's understanding of the user's intent and the tool to be used.

## Integration with Other Modules

-   **`DialogueManager`**: The primary consumer of the `DailyLanguageModel`. The `DialogueManager` uses the DLM to understand user intent and decide whether to dispatch a tool or generate a simple response.
-   **`ToolDispatcher`**: The DLM's output directly feeds into the `ToolDispatcher`, which then executes the identified tool with the extracted parameters.
-   **`MultiLLMService`**: Provides the underlying LLM capabilities that the DLM utilizes for its intent recognition.

## Code Location

`src/core_ai/language_models/daily_language_model.py`
