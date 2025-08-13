# ImageGenerationAgent: Specialized Agent for Image Creation

## Overview

This document provides an overview of the `ImageGenerationAgent` module (`src/agents/image_generation_agent.py`). This agent is a specialized sub-agent designed for generating images from textual prompts.

## Purpose

The `ImageGenerationAgent` provides the AI with the capability to create visual content based on textual descriptions. This agent can be delegated tasks that involve generating images for various purposes, such as creative content, visual aids for reports, or design elements for user interfaces.

## Key Responsibilities and Features

*   **Inheritance from `BaseAgent`**: The `ImageGenerationAgent` inherits from `BaseAgent`, leveraging its foundational functionalities for service initialization, HSP network connection, and boilerplate task handling. This ensures consistency and reduces redundant code.
*   **Defined Capabilities**: The agent advertises a specific capability on the Heterogeneous Service Protocol (HSP) network, making its services discoverable by other AI components:
    *   **`create_image`**: Creates an image from a text prompt and an optional style (e.g., 'photorealistic', 'cartoon', 'abstract').
*   **Tool Integration**: Directly uses the `ToolDispatcher` to invoke the `create_image` tool. This allows the agent to perform its core function without directly managing the complexities of an image generation API.
*   **HSP Task Handling**: Overrides the `handle_task_request` method from `BaseAgent` to process incoming HSP tasks related to image generation. It extracts the `prompt` and `style` parameters from the task payload, dispatches them to the `ToolDispatcher`, and sends back the image generation result as an HSP task result.

## How it Works

The `ImageGenerationAgent` extends `BaseAgent` and specializes in image generation. When it receives an HSP task request for its `create_image` capability, it extracts the prompt and style from the task payload. It then uses its `ToolDispatcher` instance to call the `create_image` tool with these parameters. The result obtained from the `ImageGenerationTool` (which, in the current implementation, provides a placeholder image URL) is then formatted as an `HSPTaskResultPayload` and sent back to the original requester via the `HSPConnector`.

## Integration with Other Modules

*   **`BaseAgent`**: Provides the foundational framework for the agent, handling common lifecycle and communication aspects.
*   **`ToolDispatcher`**: Used to invoke the `create_image` tool, acting as an intermediary between the agent's request and the tool's execution.
*   **`ImageGenerationTool`**: The actual tool that performs the image generation (accessed indirectly via `ToolDispatcher`).
*   **HSP Communication Types**: Utilizes `HSPTaskRequestPayload`, `HSPTaskResultPayload`, and `HSPMessageEnvelope` for structured communication over the HSP network.

## Code Location

`src/agents/image_generation_agent.py`