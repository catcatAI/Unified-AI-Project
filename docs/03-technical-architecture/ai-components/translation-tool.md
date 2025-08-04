# Translation Tool: Dictionary-Based Language Translation

## Overview

The `translation_tool.py` (`src/tools/translation_tool.py`) provides the Unified-AI-Project with a **lightweight, dictionary-based translation capability**. This tool is designed for quick and efficient translation of common words and phrases between supported languages (primarily Chinese and English in its current form).

It serves as a foundational component for multilingual interactions within the AI, with a built-in mechanism to signal when its capabilities are insufficient, hinting at future integration with more advanced translation models.

## Key Responsibilities and Features

1.  **Dictionary-Based Translation (`translate`)**:
    *   Performs translations by looking up words and phrases in a static JSON dictionary (`src/tools/translation_model/data/translation_dictionary.json`).
    *   Supports bidirectional translation (e.g., Chinese to English and English to Chinese).

2.  **Basic Language Detection (`_detect_language`)**:
    *   Includes a rudimentary function to detect the source language of a given text (currently distinguishes between Chinese and English based on character sets).
    *   This allows the tool to infer the translation direction if the source language is not explicitly provided.

3.  **Model Upgrade Request (`request_model_upgrade`)**:
    *   A conceptual hook that logs a message when the current dictionary-based model cannot provide a translation (e.g., word not found, unsupported language pair).
    *   In a more advanced system, this could trigger a meta-learning process or an alert to integrate a more sophisticated neural machine translation model.

4.  **Error Handling**: 
    *   Manages scenarios such as the translation dictionary not being found or being malformed.
    *   Provides informative messages when a translation is not available or a language pair is unsupported.

## How it Works

Upon initialization, the `translation_tool.py` loads the `translation_dictionary.json` into memory. When the `translate` function is called, it first attempts to determine the source language if not provided. It then constructs a lookup key based on the source and target languages (e.g., `zh_to_en`) and searches for the input text within the corresponding section of the dictionary. If a match is found, the translated text is returned. If not, or if the language pair is unsupported, a `MODEL_UPGRADE_REQUEST` is logged, and an informative message is returned.

## Integration with Other Modules

-   **`ToolDispatcher`**: The `ToolDispatcher` would route user queries requiring translation to the `translation_tool.py`.
-   **`DailyLanguageModel`**: The `DailyLanguageModel` would be responsible for identifying user intent for translation and extracting the text and target language parameters.
-   **`Fragmenta` (Conceptual)**: The `request_model_upgrade` function is a direct link to the broader Fragmenta system, which is envisioned to manage the AI's self-improvement and adaptation, including upgrading its internal models based on performance gaps.
-   **`MultiLLMService`**: While this tool is dictionary-based, a future, more advanced `TranslationAgent` might leverage the `MultiLLMService` for more complex, context-aware translations.

## Code Location

`src/tools/translation_tool.py`
