# PersonalityManager: Dynamic AI Personality Management

## Overview

This document provides an overview of the `PersonalityManager` module (`src/core_ai/personality/personality_manager.py`). This module is responsible for loading, managing, and dynamically applying personality profiles to the AI.

## Purpose

The `PersonalityManager` enables the AI to exhibit consistent, adaptable, and engaging personality traits. By influencing its communication style, emotional responses, and overall behavior, it is crucial for creating a more human-like and personalized interaction experience for users.

## Key Responsibilities and Features

*   **Profile Loading and Management**:
    *   **`_scan_profiles`**: Automatically scans a designated directory (`configs/personality_profiles/`) for JSON files, each representing a distinct personality profile.
    *   **`load_personality`**: Loads a specified personality profile, making it the `current_personality` that the AI will embody. It includes robust error handling, falling back to a default profile if the requested one is not found.
    *   **`list_available_profiles`**: Provides a method to list all discovered personality profiles, including their display names.
*   **Trait Access (`get_current_personality_trait`)**: Offers a flexible method to retrieve specific personality traits from the `current_personality`. It supports accessing nested traits using dot notation (e.g., `communication_style.tone_presets.default`), providing a structured way to define and retrieve complex personality attributes.
*   **Initial Prompt (`get_initial_prompt`)**: Returns the initial greeting or conversational prompt defined within the currently loaded personality profile. This sets the initial tone for interactions.
*   **Dynamic Adjustment (`apply_personality_adjustment`)**: Allows for dynamic, real-time adjustments to the `current_personality` based on external input. This input could come from user feedback, learning insights from the `LearningManager`, or other adaptive mechanisms, enabling the AI's personality to evolve over time.

## How it Works

The `PersonalityManager` initializes by scanning a predefined directory for JSON files, each of which contains a detailed definition of a personality profile. It then loads either a default profile or a specifically requested one, setting it as the `current_personality`. This `current_personality` is a dynamic dictionary containing various traits and their values. Other modules within the AI system can query the `PersonalityManager` to retrieve specific traits, and the `LearningManager` can apply adjustments to these traits, allowing the AI's personality to adapt and grow based on its experiences.

## Integration with Other Modules

*   **`DialogueManager`**: A primary consumer of the `PersonalityManager`, using it to retrieve the AI's initial prompt and to influence its overall conversational style and tone.
*   **`EmotionSystem`**: Would likely interact closely with the `PersonalityManager` to ensure that the AI's emotional responses are consistent with its current personality profile.
*   **`LearningManager`**: Plays a crucial role in applying dynamic adjustments to the AI's personality based on insights gained from user interactions and other learning processes.

## Code Location

`src/core_ai/personality/personality_manager.py`