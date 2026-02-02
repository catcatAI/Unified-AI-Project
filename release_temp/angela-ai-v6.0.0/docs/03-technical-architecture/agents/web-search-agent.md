# WebSearchAgent: Specialized Agent for Web Search

## Overview

This document provides an overview of the `WebSearchAgent` module (`src/agents/web_search_agent.py`). This agent is a specialized sub-agent designed for searching the web for information.

## Purpose

The `WebSearchAgent` provides the AI with the capability to gather information from online sources using the `WebSearchTool`. This agent can be delegated tasks that involve retrieving specific facts, researching topics, or staying updated on current events.

## Key Responsibilities and Features

*   **Inheritance from `BaseAgent`**: (Intended) The agent is designed to inherit from `BaseAgent` to leverage its foundational functionalities for service initialization, HSP network connection, and task handling boilerplate. However, there are some inconsistencies in the current implementation (see Notes below).
*   **Tool Integration**: Directly uses the `WebSearchTool` to perform web searches. This allows the agent to focus on orchestrating the search process and interpreting results, rather than managing the low-level details of web scraping or API calls.
*   **Defined Capabilities**: (Intended) The agent is designed to advertise a `search_web` capability, which takes a `query` as a parameter.
*   **Task Handling (`handle_task_request`)**: (Intended) Processes incoming tasks for web search. It extracts the search query from the task parameters and passes it to the `WebSearchTool`.

## Notes on Current Implementation Inconsistencies

Based on the provided code, there are some inconsistencies with the `BaseAgent`'s expected interface:

*   **`__init__` Signature**: The `WebSearchAgent`'s `__init__` method passes `**kwargs` to `super().__init__`. The `BaseAgent` constructor, however, explicitly expects `agent_id` and `capabilities` as positional arguments. This might lead to runtime errors or unexpected behavior.
*   **Capability Definition**: The `WebSearchAgent` defines a `get_capabilities` method, but the `BaseAgent` expects capabilities to be passed directly during its initialization.
*   **`handle_task_request` Signature**: The `WebSearchAgent`'s `handle_task_request` method has a signature of `(capability_name, parameters)`, which does not match the `BaseAgent`'s expected signature of `(task_payload, sender_ai_id, envelope)`.
*   **`agent.run()`**: The `if __name__ == "__main__":` block calls `agent.run()`, which is not a method defined in the `BaseAgent` class.

These inconsistencies suggest that the `WebSearchAgent` might be an older version or an incomplete implementation that needs to be updated to fully conform to the `BaseAgent` interface.

## How it Works

(Intended) The `WebSearchAgent` would extend `BaseAgent` and specialize in web search. When it receives an HSP task request for its `search_web` capability, it would extract the search query from the task payload. It would then use its `WebSearchTool` instance to perform the search. The results from the `WebSearchTool` would then be formatted as an HSP task result and sent back to the requester.

## Integration with Other Modules

*   **`BaseAgent`**: (Intended) Provides the foundational agent framework.
*   **`WebSearchTool`**: The actual tool that performs the web search.
*   **HSP Communication Types**: (Intended) Utilizes HSP data structures for communication.

## Code Location

`src/agents/web_search_agent.py`