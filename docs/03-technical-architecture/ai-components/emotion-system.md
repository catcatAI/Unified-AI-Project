# Emotion System

## Overview

The `EmotionSystem` (`src/core_ai/emotion_system.py`) is a foundational component within the Unified-AI-Project responsible for managing and simulating the AI's (Angela's) emotional state. Its primary goal is to enable Angela to exhibit more human-like and contextually appropriate emotional responses, thereby enriching user interactions and contributing to a more immersive experience in "Angela's World."

This module allows Angela's internal state to be influenced by external stimuli (user input) and, in turn, to subtly affect her communication style and decision-making processes.

## Key Responsibilities and Features

1.  **Emotional State Management**: 
    *   Maintains Angela's `current_emotion`, which can be updated based on various factors.
    *   Initializes the emotion based on the `PersonalityManager`'s default tone, ensuring consistency with Angela's core persona.

2.  **Input-Driven Emotion Updates (`update_emotion_based_on_input`)**: 
    *   Analyzes incoming user input (currently via simple keyword matching) to detect emotional cues.
    *   Adjusts Angela's `current_emotion` (e.g., to "empathetic" if keywords like "sad" are detected, or "playful" for "happy" keywords).
    *   Includes a mechanism to revert to the personality's default tone if no strong emotional cues are present, preventing the AI from getting stuck in an inappropriate emotional state.

3.  **Personalized Emotional Expression (`get_current_emotion_expression`)**: 
    *   Provides cues for how Angela should express her current emotion, primarily through `text_ending` modifiers (e.g., " (gently)", " (playfully) ✨").
    *   These expressions are configurable via an `emotion_map` in the system's configuration.

4.  **Integration with Personality**: 
    *   Works in conjunction with the `PersonalityManager` to ensure that emotional responses are consistent with Angela's overall personality profile.
    *   The personality profile can define default emotional tones and influence how emotions are expressed.

## How it Works

The `EmotionSystem` is initialized with a personality profile and a configuration that includes an `emotion_map`. When `update_emotion_based_on_input` is called, it processes the user's text input. Based on predefined keywords, it determines if a change in Angela's emotional state is warranted. If so, `current_emotion` is updated. The `get_current_emotion_expression` method then provides a textual modifier that can be appended to Angela's responses, reflecting her current emotional state.

## Integration with Other Modules

-   **`DialogueManager`**: The primary consumer of the `EmotionSystem`. The `DialogueManager` uses the current emotion to influence the tone and style of Angela's responses.
-   **`PersonalityManager`**: Provides the foundational personality profile, including default emotional tones, which the `EmotionSystem` uses as a baseline.
-   **`LearningManager`**: Could potentially provide more sophisticated emotional analysis of user input or feedback, leading to more nuanced emotional updates.
-   **`CrisisSystem`**: Emotional state might influence how Angela perceives and reacts to crisis situations.

## Code Location

`src/core_ai/emotion_system.py`
