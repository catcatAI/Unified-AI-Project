# PolicyRouter: Heuristic-Based LLM Model Routing

## Overview

This document provides an overview of the `PolicyRouter` module (`src/core_ai/language_models/router.py`). This module implements a heuristic-based router designed to score and select the most suitable Large Language Model (LLM) based on a given `RoutingPolicy`.

## Purpose

The primary purpose of the `PolicyRouter` is to intelligently select the optimal LLM for a specific task. By considering various criteria such as model capabilities, context window size, cost, and latency, it ensures efficient resource utilization and optimal performance. This intelligent routing mechanism is crucial for dynamically matching tasks with the most appropriate LLM, thereby enhancing the overall efficiency and effectiveness of the AI system.

## Key Responsibilities and Features

*   **Model Routing (`route`)**: The core method that takes a `RoutingPolicy` object as input and returns a dictionary containing the best-suited LLM model along with a list of all scored candidates. This allows for transparency in the routing decision.
*   **Heuristic-Based Scoring**: Assigns a numerical score to each available LLM based on a set of predefined heuristics. These heuristics are designed to prioritize models that align best with the task's requirements:
    *   **Capability Match**: Prioritizes models that explicitly support required features such as tool use, JSON mode, or vision capabilities.
    *   **Context Window Heuristic**: Favors models with a context window size that is sufficiently large for the estimated input size of the task.
    *   **Task Bias per Provider**: Incorporates biases for certain model providers based on the `task_type` (e.g., giving higher scores to specific providers for translation, code generation, or reasoning tasks).
    *   **Cost/Latency Hints**: Considers optional cost ceilings and latency targets, preferring models that are more cost-effective or those that are likely to meet performance requirements.
*   **`RoutingPolicy` Dataclass**: Defines the comprehensive set of criteria used for model selection. This dataclass includes:
    *   `task_type`: The category of the task (e.g., "translation", "code", "reasoning", "image", "vision", "general").
    *   `input_chars`: The estimated character count of the input, used for context window matching.
    *   `needs_tools`, `needs_vision`: Boolean flags indicating whether the task requires tool-use or vision capabilities.
    *   `latency_target`, `cost_ceiling`: Optional numerical targets for desired latency and maximum acceptable cost.

## How it Works

Upon receiving a `RoutingPolicy`, the `PolicyRouter` first retrieves a list of all enabled and available LLM profiles from the `ModelRegistry`. For each of these profiles, it calculates a score based on how well the model's characteristics (capabilities, context window, provider bias, cost, etc.) align with the criteria defined in the `RoutingPolicy`. The models are then sorted in descending order of their scores, and the highest-scoring model is identified as the "best" option for the given task.

## Integration with Other Modules

*   **`ModelRegistry`**: This module is the primary source of up-to-date information about available LLM models and their detailed profiles.
*   **`MultiLLMService`**: While not directly imported, the `PolicyRouter` implicitly relies on the `MultiLLMService` to provide the actual LLM models that are listed in the `ModelRegistry`.
*   **`DailyLanguageModel`**: Modules like `DailyLanguageModel` (for intent recognition) would typically use this `PolicyRouter` to intelligently select the appropriate LLM for processing user queries.

## Code Location

`src/core_ai/language_models/router.py`