# EmotionSystem: Managing AI Emotional State and Expression

## Overview

This document provides an overview of the `EmotionSystem` module (`src/core_ai/emotion_system.py`). This module is designed to manage the AI's internal emotional state, influence its responses, and integrate with its personality profiles.

## Purpose

The primary purpose of the `EmotionSystem` is to enable the AI to exhibit more human-like and contextually appropriate emotional responses. By allowing the AI to adapt its communication style and behavior based on perceived emotional cues from user input, it aims to make interactions more engaging, natural, and empathetic.

## Key Responsibilities and Features

*   **Emotion State Management**: Maintains a `current_emotion` state for the AI. This state is initialized either from a provided `personality_profile`'s default tone or a general system default (e.g., "neutral").
*   **Emotion Update (`update_emotion_based_on_input`)**:
    *   Analyzes incoming user input (primarily text) for keywords that suggest various emotional states (e.g., "sad", "happy", "angry").
    *   Updates the AI's `current_emotion` based on the detected cues. The current implementation uses a simple keyword-based detection mechanism, which can be expanded for more nuanced sentiment analysis.
*   **Emotion Expression (`get_current_emotion_expression`)**:
    *   Provides specific cues or modifiers for expressing the AI's `current_emotion`. This primarily includes a `text_ending` (e.g., " (gently)", " (playfully) ✨", " (with a sigh)") that can be appended to the AI's generated responses.
    *   These emotional expressions are configurable via an internal `emotion_map`.
*   **Personality Integration**: The system can be initialized with a `personality_profile` dictionary. This profile can define a default emotional tone for the AI, which influences its initial state and potentially its emotional responses over time.

## How it Works

The `EmotionSystem` operates by continuously monitoring user input. Based on simple keyword matching within the input text, it updates the AI's internal emotional state. This updated emotional state then influences how the AI expresses itself. For instance, if the system detects keywords associated with sadness in the user's input, it might transition to an "empathetic" emotion, which in turn could cause its subsequent responses to be appended with a gentle or understanding `text_ending`.

## Integration with Other Modules

*   **`PersonalityManager`**: The `EmotionSystem` is designed to be closely integrated with the `PersonalityManager`. The `PersonalityManager` would be responsible for providing the `personality_profile` data, which sets the foundational emotional characteristics of the AI.
*   **`DialogueManager`**: The `DialogueManager` would be a primary consumer of the `EmotionSystem`. By querying the `EmotionSystem` for the current emotional state and its corresponding expression cues, the `DialogueManager` can generate responses that are not only contextually relevant but also emotionally appropriate, leading to more natural and engaging conversations.

## Code Location

`src/core_ai/emotion_system.py`