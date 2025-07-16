# Lightweight Translation Model (v0.1)

This directory contains the components for a lightweight, dictionary-based translation tool, primarily focused on basic Chinese-English and English-Chinese translations.

## Overview

The Translation Model (v0.1) provides foundational translation capabilities for MikoAI. It is designed as a simple, fast lookup tool for common words and phrases. This initial version serves as a baseline component with conceptual hooks for future evolution and integration with more advanced translation engines, potentially orchestrated by the 'Fragmenta' system.

### Components:

1.  **`data/translation_dictionary.json`**:
    *   The core data file for the v0.1 translator.
    *   Contains JSON objects for `zh_to_en` (Chinese to English) and `en_to_zh` (English to Chinese) mappings.
    *   Example: `{"你好": "Hello", "谢谢": "Thank you"}`

2.  **`translation_tool.py`** (located in the parent `tools` directory):
    *   Implements the main translation logic.
    *   Key function: `translate(text: str, target_language: str, source_language: str = None)`.
    *   Loads the `translation_dictionary.json`.
    *   Includes very basic source language detection if not specified.
    *   Performs dictionary lookups for translation.
    *   Returns the translated text or an appropriate message if the word/phrase is not found or the language pair is unsupported.
    *   Contains a `request_model_upgrade(details: str)` function, a conceptual hook for the Fragmenta system to log when the current model is insufficient and a more advanced one might be needed.

## Usage

The primary way to use this translation tool is via the `ToolDispatcher` (`src/tools/tool_dispatcher.py`). The dispatcher is designed to understand natural language queries that imply a translation request and route them to the `translation_tool.py`.

**Example queries for the ToolDispatcher:**

*   "translate '你好' to English"
*   "translate Hello to Chinese"
*   "'Thank you' in Chinese"

The `translation_tool.py` can also be tested directly by running its `if __name__ == '__main__':` block, which demonstrates various translation scenarios.

### Adding to the Dictionary

To expand the v0.1 model's vocabulary:

1.  Edit `src/tools/translation_model/data/translation_dictionary.json`.
2.  Add new key-value pairs to both the `zh_to_en` and `en_to_zh` sections.
    *   Ensure the key in one dictionary is the value in the other for bidirectional consistency (e.g., if adding `{"高兴": "Happy"}` to `zh_to_en`, add `{"Happy": "高兴"}` to `en_to_zh`).
3.  Save the file. The `translation_tool.py` will load the updated dictionary on its next initialization (typically when the application/ToolDispatcher starts or when the tool is first called).

## Limitations of v0.1

*   **Limited Vocabulary**: Relies solely on the content of `translation_dictionary.json`. It cannot translate words or phrases not present in this dictionary.
*   **No Grammatical Understanding**: Performs direct word/phrase replacement. It does not understand grammar, syntax, or context, so it cannot handle complex sentences or idiomatic expressions correctly.
*   **Basic Language Detection**: The built-in source language detection is very rudimentary and may not be accurate for all inputs. Providing the source language explicitly is recommended for better reliability.
*   **No Phrase Segmentation**: It looks for exact matches in the dictionary. It cannot break down longer sentences into translatable parts.

## Future Enhancements (Conceptual - via Fragmenta)

The `request_model_upgrade` function in `translation_tool.py` is a placeholder. The vision is that a higher-level system (conceptually "Fragmenta"):
*   Monitors the performance and limitations of this v0.1 dictionary tool.
*   When frequent "translation not available" messages occur or when more complex translation needs are detected, Fragmenta could:
    *   Trigger a process to expand the dictionary (e.g., by learning new pairs from user corrections or other sources).
    *   Orchestrate the integration of a more sophisticated, pre-trained neural translation model (e.g., a small MarianMT model) to replace or supplement this dictionary-based approach.
    *   Manage different translation models/tools for different language pairs or domains.

This v0.1 tool provides a basic but functional starting point for translation capabilities within MikoAI.
