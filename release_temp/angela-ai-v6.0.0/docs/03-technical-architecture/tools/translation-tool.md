# TranslationTool: Dictionary-Based Text Translation

## Overview

This document provides an overview of the `translation_tool.py` module (`src/tools/translation_tool.py`). Its primary function is to provide the AI with basic text translation capabilities using a dictionary-based approach.

This tool is useful for enabling the AI to understand and respond to users in different languages and for translating content as needed.

## Key Responsibilities and Features

*   **Dictionary-Based Translation**: The core of the tool is a JSON file (`translation_dictionary.json`) that serves as a bilingual dictionary. This allows for simple and fast lookups for common words and phrases.
*   **Basic Language Detection**: Includes a rudimentary `_detect_language` function to identify the source language (currently distinguishing between Chinese and English) when it is not explicitly provided. This adds a layer of convenience for the user.
*   **Lazy Loading**: The translation dictionary is loaded into memory only when the `translate` function is first called, which helps to improve the application's startup performance.
*   **Model Upgrade Hook (`request_model_upgrade`)**: A key feature is the `request_model_upgrade` function. This serves as a conceptual hook for a meta-learning system like Fragmenta. When a translation is not found or a language pair is unsupported, this function is called. While it currently only prints a message, it is designed to eventually trigger a model upgrade, a request for human annotation, or an automated retraining process in a more advanced version of the system.
*   **Case-Insensitive Matching**: For translations from English to other languages, the tool attempts a case-insensitive lookup if the initial, case-sensitive lookup fails. This adds a degree of flexibility to the translation process.

## How it Works

When the `translate` function is called, it first ensures that the translation dictionary is loaded into memory. It then determines the source and target languages, either from the provided arguments or by using the `_detect_language` function. With the language direction established, it looks up the input text in the appropriate section of the dictionary. If a direct match is found, it returns the translation. If the translation is not found or the requested language pair is not supported, it returns an informative error message and, importantly, calls the `request_model_upgrade` function to signal the need for improvement.

## Integration with Other Modules

*   **`ToolDispatcher`**: This tool is designed to be invoked by the `ToolDispatcher` when the AI's intent is to translate text. The `ToolDispatcher` would extract the text and target language from the user's query and pass them to this tool.
*   **Fragmenta (Conceptual)**: The `request_model_upgrade` function is a forward-looking integration point for a future meta-learning system. This system would monitor these requests and take action to improve the translation model over time.

## Code Location

`src/tools/translation_tool.py`