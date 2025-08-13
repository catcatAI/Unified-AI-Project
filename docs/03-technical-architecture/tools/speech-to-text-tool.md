# SpeechToTextTool: Recognizing Speech from Audio

## Overview

This document provides an overview of the `speech_to_text_tool.py` module (`src/tools/speech_to_text_tool.py`). This tool is designed to provide the AI with the capability to transcribe spoken language from an audio file into text.

## Purpose

The `SpeechToTextTool` is a fundamental component for enabling voice-based interaction with the AI. It allows the AI to understand and process spoken commands, questions, and dialogue, making it a crucial element for any voice-enabled application.

## Key Responsibilities and Features

*   **Speech Recognition (`recognize_speech`)**: The core function of the tool. It takes the path to an `audio_file`, uses the `speech_recognition` library to process the audio, and then leverages Google's speech recognition service to perform the transcription.
*   **Model/Data Persistence (Conceptual)**: 
    *   **`save_model`**: Saves the raw WAV data of a `speech_recognition.AudioData` object to a file.
    *   **`load_model`**: Loads raw WAV data from a file into a `speech_recognition.AudioData` object. (Note: This is not for saving and loading a trained speech recognition model, but rather for persisting the audio data itself).

## How it Works

The `recognize_speech` function utilizes the `speech_recognition` library to handle the complexities of audio processing and API interaction. It reads the audio data from the specified file and sends this data to Google's speech recognition API for transcription. The text returned by the API is then returned by the function.

## Integration with Other Modules

*   **`ToolDispatcher`**: This tool can be invoked by the `ToolDispatcher` when the AI's intent is to transcribe an audio file.
*   **`speech_recognition`**: The core external library that provides the speech recognition functionality.
*   **`AudioService`**: This service would likely be the primary consumer of this tool, using it to implement its speech-to-text capabilities.

## Code Location

`src/tools/speech_to_text_tool.py`