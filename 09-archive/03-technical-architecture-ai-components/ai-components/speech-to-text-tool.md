# Speech-to-Text (STT) Tool

## Overview

The `speech_to_text_tool.py` (`src/tools/speech_to_text_tool.py`) provides the Unified-AI-Project with the capability to **convert spoken audio into written text**. This tool leverages the `speech_recognition` library, which acts as a wrapper for various popular speech recognition APIs and engines.

This module is crucial for enabling the AI to process and understand verbal commands, transcribe spoken content, and facilitate natural language interactions through voice.

## Key Responsibilities and Features

1.  **Speech Recognition (`recognize_speech`)**:
    *   Takes the path to an `audio_file` as input.
    *   Uses the `speech_recognition` library to process the audio and convert it into a text string.
    *   By default, it utilizes Google's Web Speech API for recognition, but the underlying library supports many other engines (e.g., CMU Sphinx, Microsoft Azure Speech, Google Cloud Speech, etc.).

2.  **Model Persistence (Conceptual)**:
    *   Includes placeholder functions (`save_model`, `load_model`) for saving and loading models.
    *   In this context, the "model" refers more to the audio data itself or a specific configuration for the `speech_recognition` library, rather than a traditional machine learning model.

## How it Works

When `recognize_speech` is called, it initializes a `Recognizer` object. It then opens the provided audio file, records the audio data, and sends it to the configured speech recognition engine (e.g., Google's Web Speech API) for transcription. The recognized text is then returned.

## Integration with Other Modules

-   **`AudioService`**: The `AudioService` would likely use this `Speech-to-Text Tool` as its core implementation for converting incoming audio streams or files into text that the AI can process.
-   **`DialogueManager`**: The `DialogueManager` would receive text input from the `AudioService` (which uses this tool) to understand user commands and generate appropriate responses.
-   **`MultiLLMService`**: The transcribed text from this tool would serve as input to LLMs for natural language understanding and response generation.
-   **`CrisisSystem`**: Could potentially use this tool to transcribe spoken input for real-time crisis detection.

## Code Location

`src/tools/speech_to_text_tool.py`
