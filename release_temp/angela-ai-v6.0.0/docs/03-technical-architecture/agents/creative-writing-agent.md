# CreativeWritingAgent: Specialized Agent for Text Generation and Polishing

## Overview

This document provides an overview of the `CreativeWritingAgent` module (`src/agents/creative_writing_agent.py`). This agent is a specialized sub-agent designed to handle creative writing tasks, such as generating marketing copy, short stories, or polishing existing text.

## Purpose

The `CreativeWritingAgent` extends the AI's natural language generation capabilities by focusing on creative and stylistic text manipulation. It can be delegated tasks that require more nuanced, imaginative, and contextually appropriate text outputs, offloading these specialized functions from the main AI system.

## Key Responsibilities and Features

*   **Inheritance from `BaseAgent`**: The `CreativeWritingAgent` inherits from `BaseAgent`, leveraging its foundational functionalities for service initialization, HSP network connection, and boilerplate task handling. This ensures consistency and reduces redundant code.
*   **Defined Capabilities**: The agent advertises specific capabilities on the Heterogeneous Service Protocol (HSP) network, making its services discoverable by other AI components:
    *   **`generate_marketing_copy`**: Generates marketing copy for a given product and target audience, with an optional style (e.g., 'witty', 'professional', 'urgent').
    *   **`polish_text`**: Improves the grammar, style, and clarity of a given text.
*   **LLM-Powered Generation**: Directly utilizes the `MultiLLMService` (obtained from the core services) to perform the actual text generation and polishing tasks. This allows the agent to benefit from the advanced capabilities of various large language models.
*   **Prompt Management**: Loads specific prompts and prompt templates for its creative writing tasks from a `prompts.yaml` configuration file. This enables flexible and configurable text generation behavior without modifying the agent's core logic.
*   **HSP Task Handling**: Overrides the `handle_task_request` method from `BaseAgent` to process incoming HSP tasks related to its creative writing capabilities. It constructs appropriate prompts for the LLM based on the task payload and sends back the generated text as an HSP task result.

## How it Works

When the `CreativeWritingAgent` receives an HSP task request for one of its advertised capabilities (e.g., `generate_marketing_copy`), it extracts the necessary parameters from the task payload. It then constructs a specific prompt for the `MultiLLMService` using its loaded prompt templates and the extracted parameters. The `MultiLLMService` processes this prompt, and the agent then formats the LLM's response as an `HSPTaskResultPayload` and sends it back to the original requester via the `HSPConnector`.

## Integration with Other Modules

*   **`BaseAgent`**: Provides the foundational framework for the agent, handling common lifecycle and communication aspects.
*   **`MultiLLMService`**: The core LLM interface used for all text generation and manipulation tasks.
*   **HSP Communication Types**: Utilizes `HSPTaskRequestPayload`, `HSPTaskResultPayload`, and `HSPMessageEnvelope` for structured communication over the HSP network.
*   **`PyYAML`**: Used for loading prompt configurations from `prompts.yaml`.

## Code Location

`src/agents/creative_writing_agent.py`