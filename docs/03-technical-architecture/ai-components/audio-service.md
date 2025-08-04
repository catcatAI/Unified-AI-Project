# Audio Service: Speech-to-Text and Text-to-Speech

## Overview

The `AudioService` (`src/services/audio_service.py`) is a core component within the Unified-AI-Project responsible for enabling the AI (Angela) to **process audio input (Speech-to-Text) and generate audio output (Text-to-Speech)**. This module is crucial for facilitating natural language voice interactions, allowing Angela to understand spoken commands and respond verbally.

While the current implementation includes mock logic for audio generation (sine waves) and a placeholder for speech-to-text, it lays the foundation for integrating advanced STT and TTS engines.

## Key Responsibilities and Features

1.  **Speech-to-Text (STT) Conversion (`speech_to_text`)**:
    *   Takes raw audio data (bytes) and a specified language.
    *   (Currently a mock implementation) Returns a transcribed text string, simulating the conversion of spoken words into written text.

2.  **Text-to-Speech (TTS) Conversion (`text_to_speech`)**:
    *   Takes a text string, a language, and an optional voice identifier.
    *   (Currently a mock implementation) Generates placeholder audio data (a sine wave) as bytes, simulating the conversion of written text into spoken audio.
    *   Allows for configuration of a default voice.

## How it Works

The `AudioService` acts as an abstraction layer for underlying STT and TTS technologies. In its current state, it provides the interface for these operations but uses simplified, mock implementations. For STT, it acknowledges the input and returns a generic transcription. For TTS, it generates a basic audio signal (a sine wave) to represent spoken output. Future development would involve integrating with external STT/TTS APIs or local models to provide actual speech processing capabilities.

## Integration with Other Modules

-   **`DialogueManager`**: Would utilize the `AudioService` to convert spoken user input into text for processing and to convert Angela's text responses into spoken audio for output.
-   **`MultiLLMService`**: While not directly integrated, the `AudioService` provides the input (text from speech) and consumes the output (text for speech) that LLMs would process.
-   **`PersonalityManager`**: The chosen voice for TTS could be influenced by Angela's personality profile.
-   **`TimeSystem`**: Could potentially influence the tone or style of spoken responses based on the time of day.

## Code Location

`src/services/audio_service.py`
