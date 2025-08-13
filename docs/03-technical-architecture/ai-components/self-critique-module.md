# Self-Critique Module

## Overview

This document provides an overview of the `SelfCritiqueModule` (`src/core_ai/learning/self_critique_module.py`). This module is designed to use a Large Language Model (LLM) to evaluate the quality of the AI's own responses in the context of a conversation.

## Purpose

The primary purpose of the `SelfCritiqueModule` is to provide a mechanism for the AI to self-assess and improve its conversational abilities. By evaluating its responses based on criteria like relevance, helpfulness, coherence, safety, and tone, the module enables a continuous learning and refinement loop. This allows the AI to identify and correct its own mistakes, leading to higher-quality interactions over time.

## Key Responsibilities and Features

*   **Critique Prompt Construction (`_construct_critique_prompt`)**: Dynamically builds a detailed prompt for an LLM. This prompt includes the preceding conversation history, the user's latest input, and the AI's response, and instructs the LLM to act as an impartial evaluator.
*   **Structured JSON Evaluation**: The critique prompt explicitly asks the LLM to return its evaluation in a structured JSON format, containing a numerical score (0.0 to 1.0), a textual reason for the score, and a suggested alternative if the response could be improved.
*   **Interaction Critique (`critique_interaction`)**:
    *   Orchestrates the self-critique process by sending the constructed prompt to the configured LLM interface.
    *   Parses and validates the JSON response from the critic LLM.
    *   If the critique score is below a certain threshold, it can trigger a repair mechanism.
*   **Automated Repair Integration**: If a response is rated poorly, the module integrates with a `TonalRepairEngine` to automatically generate an improved or repaired version of the AI's original response based on the feedback provided in the critique.

## How it Works

The `SelfCritiqueModule` operates by taking a complete conversational turn (user input, AI response, and context history) and framing it as an evaluation task for another LLM. This "critic" LLM is given a specific persona—that of an impartial evaluator—and a clear set of instructions on how to score the response and what format to use for its feedback. After receiving the structured JSON critique, the module parses it. If the score is low, it leverages the `TonalRepairEngine` and the reasoning from the critique to generate a better alternative response. This entire process allows the AI system to gain reflective feedback on its own performance, simulating a human-like ability to review and learn from its mistakes.

## Integration with Other Modules

*   **`MultiLLMService` (`llm_interface`)**: This module is a critical dependency, providing the connection to the LLM that performs the actual critique.
*   **`TonalRepairEngine`**: Used to attempt to fix responses that the `SelfCritiqueModule` identifies as being low-quality.
*   **`CritiqueResult` (Common Type)**: Uses a shared data structure to standardize the output of the critique process, ensuring consistency across the system.

## Code Location

`apps/backend/src/core_ai/learning/self_critique_module.py`
