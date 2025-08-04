# Dialogue Manager

## Overview

The `DialogueManager` (`src/core_ai/dialogue/dialogue_manager.py`) serves as the central orchestrator for Angela's interactions with users. It is the primary interface through which users communicate with the AI, and it intelligently routes user requests to the appropriate internal AI services or external tools.

This module is essentially the "brain" that brings together all the disparate AI components to provide a coherent, intelligent, and personalized user experience. It embodies Angela's conversational capabilities and her ability to understand, process, and respond to a wide range of user inputs.

## Key Responsibilities and Features

1.  **Central Coordination**: The `DialogueManager` acts as a hub, coordinating interactions between numerous core AI services:
    *   `PersonalityManager`: For personalized responses and tone.
    *   `HAMMemoryManager`: To store and retrieve conversational context and learned facts.
    *   `MultiLLMService`: To generate natural language responses.
    *   `EmotionSystem`: To influence responses based on emotional state.
    *   `CrisisSystem`: To detect and respond to critical situations.
    *   `TimeSystem`: To provide time-aware responses.
    *   `FormulaEngine`: To execute predefined logical formulas.
    *   `ToolDispatcher`: To invoke specialized tools based on user intent.
    *   `LearningManager`: To learn from interactions and adjust personality.
    *   `ServiceDiscoveryModule`: To find and utilize available agent capabilities.
    *   `HSPConnector`: For inter-AI communication and task delegation.
    *   `AgentManager`: To manage the lifecycle of sub-agents.

2.  **Intent Classification and Task Delegation**: It intelligently analyzes user input to classify intent:
    *   **Complex Project Delegation**: If a user's input matches a predefined trigger (e.g., `"project:"`), the `DialogueManager` delegates the complex task to the `ProjectCoordinator` for decomposition and multi-agent orchestration.
    *   **Simple Response/Tool Dispatch**: For simpler queries, it attempts to dispatch the request to a suitable tool via the `ToolDispatcher`.

3.  **Conversational Memory and Learning**: 
    *   Automatically stores both user utterances and AI responses in the `HAMMemoryManager`, building a rich conversational history.
    *   Integrates with the `LearningManager` to analyze user input for potential personality adjustments, allowing Angela to adapt her conversational style over time.

4.  **HSP Integration**: 
    *   Registers a callback (`_handle_incoming_hsp_task_result`) with the `HSPConnector` to receive and process task results from other agents or services on the HSP network. These results are then passed to the `ProjectCoordinator`.

5.  **Session Management**: 
    *   Manages active user sessions, allowing for context-aware conversations.
    *   Generates personalized session greetings based on the time of day and Angela's current personality.

## Workflow

When a user provides input, the `DialogueManager` follows a general flow:

1.  **Receive Input**: User input is received (e.g., via API or CLI).
2.  **Intent Check**: It first checks if the input triggers a complex project delegation to the `ProjectCoordinator`.
3.  **Tool Dispatch**: If not a complex project, it attempts to find and dispatch a relevant tool via the `ToolDispatcher`.
4.  **Response Generation**: Based on the tool's output or if no tool is found, it generates a natural language response, potentially using the `MultiLLMService`.
5.  **Memory Storage**: Both user input and AI response are stored in `HAMMemoryManager`.
6.  **Learning & Adjustment**: The `LearningManager` analyzes the interaction for learning opportunities, which might lead to personality adjustments.
7.  **Return Response**: The final response is returned to the user.

## Code Location

`src/core_ai/dialogue/dialogue_manager.py`
