# Crisis System

## Overview

The `CrisisSystem` (`src/core_ai/crisis_system.py`) is a vital component within the Unified-AI-Project, designed to **detect, assess, and manage potential crisis situations** during AI interactions. Its primary goal is to ensure the safety, well-being, and ethical operation of the AI (Angela) and its users, by implementing predefined protocols when sensitive or critical indicators are detected.

This module is crucial for maintaining a responsible AI system, especially in scenarios where user input might indicate distress, harm, or other critical events that require immediate and appropriate responses.

## Key Responsibilities and Features

1.  **Crisis Detection (`assess_input_for_crisis`)**:
    *   Analyzes incoming user input (and potentially context) for predefined crisis keywords or patterns.
    *   Assigns a `crisis_level` (0 for no crisis, higher numbers for increasing severity) based on the detected indicators.

2.  **Crisis Level Management**: 
    *   Maintains the AI's current `crisis_level`.
    *   Crisis levels can escalate based on new input but typically require explicit resolution to de-escalate.

3.  **Protocol Triggering (`_trigger_protocol`)**: 
    *   Activates specific, predefined `crisis_protocols` based on the detected `crisis_level`.
    *   Protocols can range from simple logging to notifying human moderators, or triggering specific AI responses (handled by the `DialogueManager`).

4.  **Crisis Resolution (`resolve_crisis`)**: 
    *   Provides a mechanism to manually or automatically resolve an active crisis, resetting the `crisis_level` to zero.

5.  **Configurable Keywords and Protocols**: 
    *   Crisis keywords and their associated protocols are loaded from an external JSON configuration file (e.g., `configs/crisis_system_config.json`). This allows for flexible and updatable crisis definitions without code changes.

6.  **Integration with Other Core AI Systems**: 
    *   References `EmotionSystem` and `MemoryManager`, suggesting potential future integrations where emotional state or past crisis incidents could influence crisis assessment and response.

## How it Works

Upon receiving input, the `CrisisSystem` scans the text for configured crisis keywords. If found, it updates the internal `crisis_level` and triggers the corresponding protocol. The protocols are defined in a configuration file and dictate the system's immediate response. The system maintains the `crisis_level` until explicitly resolved, ensuring sustained awareness of critical situations.

## Integration with Other Modules

-   **`DialogueManager`**: The `DialogueManager` would typically call `assess_input_for_crisis` to evaluate user input and then use the returned `crisis_level` to inform its response generation, potentially triggering specific crisis-response dialogues.
-   **`PersonalityManager`**: Crisis protocols might be influenced by Angela's personality, determining how she communicates during a crisis.
-   **`EmotionSystem`**: The `CrisisSystem` could inform the `EmotionSystem` of a crisis, leading to changes in Angela's emotional state and expression.
-   **`HAMMemoryManager`**: Crisis incidents and their resolutions could be stored in HAM for future learning and analysis, allowing the AI to improve its crisis management over time.

## Code Location

`src/core_ai/crisis_system.py`
