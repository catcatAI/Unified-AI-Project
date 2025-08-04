# Personality Manager

## Overview

The `PersonalityManager` (`src/core_ai/personality/personality_manager.py`) is a crucial component within the Unified-AI-Project responsible for defining, loading, managing, and dynamically adjusting the AI's (Angela's) personality. It allows Angela to exhibit a wide range of behaviors, communication styles, and emotional responses, making her interactions more nuanced and engaging.

This module is central to shaping Angela's identity and ensuring consistency in her persona across different interactions and scenarios.

## Key Responsibilities and Features

1.  **Personality Profile Management**: 
    *   Scans a designated directory (defaulting to `configs/personality_profiles/`) for JSON files, each representing a distinct personality profile.
    *   Each profile can define various traits, such as communication style, emotional tendencies, knowledge biases, and initial conversational prompts.

2.  **Dynamic Profile Loading (`load_personality`)**: 
    *   Allows the system to load a specific personality profile by name.
    *   Supports a default profile fallback if a requested profile is not found.

3.  **Trait Retrieval (`get_current_personality_trait`)**: 
    *   Provides a flexible method to retrieve specific personality traits from the currently loaded profile, supporting nested trait access (e.g., `communication_style.tone_presets.default`).

4.  **Initial Prompt Generation (`get_initial_prompt`)**: 
    *   Returns a personality-specific initial prompt, which can be used to kickstart conversations with Angela in a manner consistent with her current persona.

5.  **Dynamic Personality Adjustment (`apply_personality_adjustment`)**: 
    *   Enables other modules (e.g., `LearningManager` based on user feedback or interaction analysis) to dynamically modify Angela's personality traits at runtime.
    *   This feature is key to Angela's ability to adapt and evolve her persona over time, making her more responsive and realistic.

## How it Works

The `PersonalityManager` initializes by scanning a predefined directory for JSON-formatted personality profiles. Each profile is loaded and made available. The system can then explicitly load a specific personality, which becomes the `current_personality`. Other modules can query this `current_personality` for specific traits or apply adjustments to it. The `apply_personality_adjustment` method allows for granular updates to nested personality attributes, ensuring that changes are applied precisely.

## Integration with Other Modules

-   **`DialogueManager`**: Heavily relies on the `PersonalityManager` to fetch initial prompts, determine conversational tone, and influence response generation based on Angela's current personality.
-   **`LearningManager`**: Can suggest and apply personality adjustments based on learned insights from user interactions or system performance.
-   **`EmotionSystem`**: Personality traits can influence emotional responses, and vice-versa, creating a feedback loop for more realistic AI behavior.
-   **`CrisisSystem`**: Personality might influence how Angela reacts to and communicates during crisis situations.

## Code Location

`src/core_ai/personality/personality_manager.py`
