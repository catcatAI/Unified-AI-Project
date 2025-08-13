# DailyLanguageModel: LLM-Powered Intent Recognition and Tool Dispatching

## Overview

This document provides an overview of the `DailyLanguageModel` module (`src/core_ai/language_models/daily_language_model.py`). This module is designed to recognize user intent, primarily for the purpose of dispatching user queries to the appropriate tools or services within the AI system, leveraging the capabilities of a Large Language Model (LLM).

## Purpose

The `DailyLanguageModel` acts as an intelligent router for user queries. Its core purpose is to translate natural language user input into structured commands that can be understood and executed by various AI capabilities. This is crucial for enabling intuitive and flexible natural language interaction with the AI, eliminating the need for users to memorize specific commands or tool names.

## Key Responsibilities and Features

*   **Intent Recognition (`recognize_intent`)**:
    *   Takes a user's `text` query and a dictionary of `available_tools` (which includes tool names and their natural language descriptions).
    *   Constructs a highly specific prompt for an LLM, instructing it to analyze the user's query, select the most appropriate tool from the provided list, and extract all necessary parameters for that tool.
    *   Communicates with the `MultiLLMService` to send the prompt and receive the LLM's response.
    *   Parses the LLM's response, which is expected to be in a strict JSON format, to identify the `tool_name` and its corresponding `parameters`.
    *   Gracefully handles scenarios where no suitable tool is identified by the LLM (indicated by `"tool_name": "NO_TOOL"`) or where the LLM provides an invalid tool name.
*   **Prompt Construction (`_construct_tool_selection_prompt`)**: Dynamically builds a detailed and carefully crafted prompt for the LLM. This prompt includes a clear persona for the LLM, a list of available tools with descriptions, the user's query, and explicit instructions on the required JSON response format, including examples for parameter extraction for specific tools (e.g., `calculate`, `evaluate_logic`, `translate_text`).
*   **LLM Integration**: Serves as the primary interface for integrating the AI system with Large Language Models via the `MultiLLMService`. It leverages the LLM's advanced natural language understanding and instruction-following capabilities to perform complex intent recognition and parameter extraction.

## How it Works

The `DailyLanguageModel` functions as an intelligent intermediary. When a user provides a natural language query, the module constructs a precise prompt for an LLM. The LLM processes this prompt, identifies the user's underlying intent, and determines if any of the available tools can fulfill that intent. The LLM then responds with a structured JSON object containing the selected tool's name and any extracted parameters. The `DailyLanguageModel` parses this response and provides it to other parts of the AI system (e.g., the `ToolDispatcher`) for execution.

## Integration with Other Modules

*   **`MultiLLMService`**: This is the core dependency for the `DailyLanguageModel`, providing the interface to various LLM providers and models.
*   **`ToolDispatcher` (Conceptual)**: The `ToolDispatcher` would be the primary consumer of the output from `recognize_intent`, taking the identified tool name and parameters to execute the corresponding tool.
*   **Standard Python Libraries**: Relies on `json` for parsing the LLM's JSON responses and `re` (regular expressions) for internal logic, particularly within the testing (`if __name__ == '__main__':`) block for simulating LLM behavior.

## Code Location

`src/core_ai/language_models/daily_language_model.py`