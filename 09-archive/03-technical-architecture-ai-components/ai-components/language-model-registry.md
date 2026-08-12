# ModelRegistry: Centralized LLM Model Management and Discovery

## Overview

This document provides an overview of the `ModelRegistry` module (`src/core_ai/language_models/registry.py`). This module is responsible for building and managing a structured list of `ModelProfile` objects, derived from the `MultiLLMService.model_configs`, indicating the availability and capabilities of various Large Language Models (LLMs).

## Purpose

 The primary purpose of the `ModelRegistry` is to provide a centralized and structured way to understand the capabilities and runtime availability of all LLMs integrated into the system. This is crucial for enabling dynamic model selection, efficient resource management, and ensuring that the AI only attempts to utilize models that are properly configured, accessible, and possess the necessary capabilities for a given task.

## Key Responsibilities and Features

*   **`ModelProfile` Dataclass**: Defines a standardized and comprehensive structure for representing an LLM's profile. This includes essential attributes such as:
    *   `model_id`, `provider`, `model_name`
    *   Operational status: `enabled` (configured to be used) and `available` (runtime accessibility).
    *   Performance metrics: `context_window`, `max_tokens`, `cost_per_1k_tokens`.
    *   `capabilities`: A dictionary detailing specific features like `json_mode`, `tool_use`, and `vision` support.
*   **Availability Check (`_is_available`)**: Implements the logic to determine if a model is currently available for use. This check considers whether the model is enabled in the configuration and if a required API key is present (for cloud-based providers) or if it's a local provider (like OLLAMA) that doesn't require a key.
*   **Profile Listing (`list_profiles`)**: Iterates through the `MultiLLMService`'s model configurations. For each configuration, it constructs a `ModelProfile` object, populating its attributes and dynamically determining its availability and specific capabilities based on its provider.
*   **Dictionary Conversion (`profiles_dict`)**: Provides a convenient method to retrieve all generated `ModelProfile` objects as a list of dictionaries, facilitating easy serialization or consumption by other parts of the system.

## How it Works

The `ModelRegistry` is initialized with the `model_configs` obtained from the `MultiLLMService`. It then systematically processes each model configuration. During this process, it performs checks to determine the model's runtime availability (e.g., verifying API key presence for cloud services). It also assigns a set of capabilities (e.g., JSON mode, tool use, vision) based on the model's underlying provider. All this information is then encapsulated within `ModelProfile` objects, which are made available through the registry's methods.

## Integration with Other Modules

*   **`MultiLLMService`**: Serves as the primary source of raw model configurations that the `ModelRegistry` processes.
*   **`ModelConfig` and `ModelProvider`**: These are essential data structures and enums imported from `MultiLLMService` that define the basic configuration and provider types for LLMs.
*   **LLM-Dependent Modules**: Any module that needs to dynamically select an LLM, query its capabilities, or manage LLM resources (e.g., `DailyLanguageModel` for intent recognition, `ToolDispatcher` for tool execution) would interact with this `ModelRegistry` to get up-to-date information on available models.

## Code Location

`src/core_ai/language_models/registry.py`