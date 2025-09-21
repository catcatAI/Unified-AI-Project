# CrisisSystem: AI Crisis Detection and Management

## Overview

This document provides an overview of the `CrisisSystem` module (`src/core_ai/crisis_system.py`). This module is designed to detect and manage potential crisis situations, which may involve safety protocols, user well-being checks, or handing off to other support systems.

## Purpose

The `CrisisSystem` serves as a critical safety mechanism within the AI. Its primary purpose is to ensure the safety and well-being of users interacting with the AI, and to effectively manage situations where the AI detects potential distress, harmful intent, or other critical events. It acts as a safety net and a mechanism for escalating critical situations to appropriate protocols or human intervention.

## Key Responsibilities and Features

*   **Crisis Detection (`assess_input_for_crisis`)**:
    *   Analyzes incoming user input (primarily text) for predefined `crisis_keywords` and `negative_words`.
    *   Assigns an internal `crisis_level` (0 for no crisis, with higher numbers indicating increasing severity).
    *   The `crisis_level` is designed to only escalate through this method; de-escalation requires an explicit call to `resolve_crisis`.
*   **Crisis Protocols (`_trigger_protocol`)**:
    *   Based on the detected `crisis_level`, the system triggers predefined protocols. These protocols are highly configurable via a JSON file (`crisis_system_config.json`) and can range from simple internal logging to notifying human moderators or initiating other safety measures.
*   **Crisis Resolution (`resolve_crisis`)**: Provides a method to manually or automatically resolve a crisis situation. Calling this method resets the internal `crisis_level` to 0, indicating that the crisis has been addressed.
*   **Configuration Management**: Loads its operational parameters, including `crisis_keywords`, `negative_words`, `default_crisis_level_on_keyword`, and `crisis_protocols`, from a configuration dictionary or a specified JSON file.
*   **Logging**: Logs all crisis events and the triggered protocols, providing an audit trail for review and analysis.

## How it Works

The `CrisisSystem` continuously monitors incoming user input. If it detects specific keywords or sentiment indicators that suggest a potential crisis, it increases its internal `crisis_level`. Based on this level, it triggers predefined protocols, which can range from simple logging to notifying human moderators or initiating other safety measures. The crisis state persists until explicitly resolved by a call to `resolve_crisis`.

## Integration with Other Modules

*   **`DialogueManager`**: The `DialogueManager` would typically feed user input to the `CrisisSystem` for real-time assessment of potential crisis situations.
*   **`EmotionSystem`**: Could potentially provide more nuanced sentiment analysis or emotional state information to the `CrisisSystem`, enhancing its detection capabilities.
*   **`HAMMemoryManager`**: Could be used to log crisis events, store context related to crises, or even trigger memory-based interventions.

## Code Location

`src/core_ai/crisis_system.py`