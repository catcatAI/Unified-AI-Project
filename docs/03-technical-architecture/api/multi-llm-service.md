# MultiLLMService: Unified Interface for Multiple Large Language Models

## Overview

This document provides a comprehensive overview of the `MultiLLMService` module (`src/services/multi_llm_service.py`). Its primary function is to offer a unified and consistent interface for interacting with various Large Language Model (LLM) providers, including OpenAI GPT, Google Gemini, Anthropic Claude, Ollama, Azure OpenAI, Cohere, and Hugging Face models.

This module is crucial for abstracting away the complexities and differences of diverse LLM APIs, enabling AI components to seamlessly generate text, engage in chat completions, and stream responses without needing to manage provider-specific integrations. It centralizes model configuration, API key management, rate limiting, and usage statistics.

## Key Responsibilities and Features

*   **Unified API Interface**: Provides core asynchronous methods (`chat_completion` for single-turn responses and `stream_completion` for streaming responses) that offer a consistent way to interact with any supported LLM provider.
*   **Multiple Provider Support**: Implements dedicated classes for each LLM provider (e.g., `OpenAIProvider`, `AnthropicProvider`, `GoogleProvider`, `OllamaProvider`, `AzureOpenAIProvider`, `CohereProvider`, `HuggingFaceProvider`), all inheriting from `BaseLLMProvider`. Each handles the specific API calls and message format conversions for its respective LLM.
*   **Configuration Management (`load_config`)**: Loads detailed model configurations (including `model_name`, `api_key`, `base_url`, `max_tokens`, `temperature`, `cost_per_1k_tokens`, `context_window`, and `enabled` status) from a `multi_llm_config.json` file. It also supports retrieving API keys from environment variables for security.
*   **Rate Limiting**: Integrates `aiolimiter` to enforce configurable rate limits per provider, preventing API abuse and ensuring fair usage across different LLM services.
*   **Usage Statistics and Monitoring**: Tracks comprehensive usage statistics for each model, including `total_requests`, `total_tokens`, `total_cost`, `average_latency`, and `error_count`. This data is valuable for cost analysis, performance monitoring, and debugging.
*   **Model Routing (Conceptual Integration)**: Designed to integrate with `ModelRegistry` and `PolicyRouter` (from `src/core_ai/language_models`) to intelligently select the most appropriate LLM model for a given task based on dynamic criteria like model capabilities, cost, and current load.
*   **Health Check (`health_check`)**: Provides a method to periodically check the operational status of each configured LLM model by sending a simple test message and reporting its health and response latency.
*   **Global Singleton Instance**: Offers `get_multi_llm_service()` and `initialize_multi_llm_service()` functions to manage a single, globally accessible instance of the service, promoting consistent LLM access throughout the application.
*   **Data Structures**: Defines key data structures as dataclasses: `ModelProvider` (Enum for supported providers), `ModelConfig` (for model-specific settings), `ChatMessage` (standardized chat message format), and `LLMResponse` (standardized LLM response format including usage and cost).

## How it Works

The `MultiLLMService` acts as a central facade. It loads and manages configurations for various LLMs. When a request for text generation or chat completion is received, it selects the appropriate provider (either explicitly specified or determined by a routing mechanism). It then creates or retrieves an instance of that provider's client, handles any necessary message format conversions, dispatches the request, and processes the response. All interactions are logged, and usage metrics are collected, providing a transparent and manageable interface to the diverse world of LLMs.

## Integration with Other Modules

*   **`src.core_ai.language_models.registry` and `src.core_ai.language_models.router`**: For advanced, policy-driven LLM model selection.
*   **`aiolimiter`**: Used for asynchronous rate limiting to manage API call volumes.
*   **External LLM Libraries**: Integrates with various Python client libraries for specific LLM APIs (e.g., `openai`, `anthropic`, `google.generativeai`, `cohere`, `azure.ai.inference`).
*   **AI Components**: All AI components that require natural language generation or understanding capabilities (e.g., `DialogueManager`, `CreativeWritingAgent`, `FactExtractorModule`) would use this service as their primary interface to LLMs.

## Code Location

`src/services/multi_llm_service.py`