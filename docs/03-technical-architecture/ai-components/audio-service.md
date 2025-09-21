# AudioService: Speech-to-Text and Text-to-Speech Capabilities

## Overview

This document provides an overview of the `AudioService` module (`src/services/audio_service.py`). This service provides functionalities for both speech-to-text (STT) and text-to-speech (TTS) conversions, and includes a mock sentiment analysis feature.

## Purpose

The `AudioService` is designed to enable the AI to interact with users through spoken language. It acts as a crucial interface for processing audio input (transcribing speech) and generating audio output (synthesizing speech), which are fundamental for any voice-enabled application.

## Key Responsibilities and Features

*   **Speech-to-Text (`speech_to_text`)**:
    *   Takes `audio_data` (raw bytes of audio) and an optional `language` parameter.
    *   Currently, this is a mock implementation that returns a static transcription string. In a production environment, it would integrate with a real STT engine.
*   **Speech-to-Text with Sentiment Analysis (`speech_to_text_with_sentiment_analysis`)**:
    *   Takes `audio_data` and an optional `language`.
    *   Its behavior is conditional on the application's `demo_mode` setting:
        *   If `demo_mode` is disabled, it raises a `NotImplementedError`, indicating that real sentiment analysis integration is not yet available.
        *   If `demo_mode` is enabled, it returns a mock sentiment payload (e.g., always reporting a "positive" sentiment with high confidence).
    *   Leverages `src.config_loader.is_demo_mode` to determine its operational mode.
*   **Text-to-Speech (`text_to_speech`)**:
    *   Takes `text` (the string to be converted to speech), an optional `language`, and a `voice` identifier.
    *   Currently, this is a mock implementation that generates a simple sine wave as placeholder audio data. In a production system, it would integrate with a real TTS engine to produce natural-sounding speech.

## How it Works

The `AudioService` acts as an abstraction layer over underlying STT and TTS engines. In its current mock state, it simulates these functionalities to allow for the development and testing of other AI components that rely on audio processing. For STT, it returns a predefined string. For TTS, it generates a simple audio waveform. The sentiment analysis feature demonstrates how the service would integrate with a demo mode, providing mock data when enabled, which is useful for showcasing functionality without requiring complex external dependencies.

## Integration with Other Modules

*   **`src.config_loader`**: Used to check the application's `demo_mode` status, influencing the behavior of the sentiment analysis feature.
*   **`SpeechToTextTool`**: In a full implementation, the `speech_to_text` method would likely utilize a real `SpeechToTextTool` for actual transcription.
*   **`DialogueManager`**: This service would be a key dependency for the `DialogueManager` to enable voice input and output for conversational interactions.

## Code Location

`src/services/audio_service.py`