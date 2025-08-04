# Translation Model: Lightweight Dictionary-Based Translation

## Overview

The `translation_model` directory (`src/tools/translation_model/`) contains components for a **lightweight, dictionary-based translation tool** within the Unified-AI-Project. This initial version (v0.1) primarily focuses on basic Chinese-English and English-Chinese translations, serving as a foundational capability for MikoAI.

It is designed for simple, fast lookups of common words and phrases, with conceptual hooks for future integration with more advanced neural translation engines, potentially orchestrated by the 'Fragmenta' system.

## Key Components

1.  **`data/translation_dictionary.json`**:
    *   The core data file for the v0.1 translator.
    *   Contains JSON objects for `zh_to_en` (Chinese to English) and `en_to_zh` (English to Chinese) mappings.
    *   Example: `{"你好": "Hello", "谢谢": "Thank you"}`.

2.  **`translation_tool.py`** (located in the parent `src/tools` directory):
    *   Implements the main translation logic.
    *   Key function: `translate(text: str, target_language: str, source_language: str = None)`.
    *   Loads the `translation_dictionary.json`.
    *   Includes very basic source language detection if not specified.
    *   Performs dictionary lookups for translation.
    *   Returns the translated text or an appropriate message if the word/phrase is not found or the language pair is unsupported.
    *   Contains a `request_model_upgrade(details: str)` function, a conceptual hook for the Fragmenta system to log when the current model is insufficient and a more advanced one might be needed.

## Usage

The primary way to use this translation tool is via the `ToolDispatcher` (`src/tools/tool_dispatcher.py`). The dispatcher is designed to understand natural language queries that imply a translation request and route them to the `translation_tool.py`.

### Adding to the Dictionary

To expand the v0.1 model's vocabulary:

1.  Edit `src/tools/translation_model/data/translation_dictionary.json`.
2.  Add new key-value pairs to both the `zh_to_en` and `en_to_zh` sections, ensuring bidirectional consistency.
3.  Save the file. The `translation_tool.py` will load the updated dictionary on its next initialization.

## Limitations of v0.1

-   **Limited Vocabulary**: Relies solely on the content of `translation_dictionary.json`. It cannot translate words or phrases not present.
-   **No Grammatical Understanding**: Performs direct word/phrase replacement. It does not understand grammar, syntax, or context, so it cannot handle complex sentences or idiomatic expressions correctly.
-   **Basic Language Detection**: The built-in source language detection is very rudimentary and may not be accurate for all inputs. Providing the source language explicitly is recommended for better reliability.
-   **No Phrase Segmentation**: It looks for exact matches in the dictionary. It cannot break down longer sentences into translatable parts.

## Future Enhancements (Conceptual - via Fragmenta)

The `request_model_upgrade` function in `translation_tool.py` is a placeholder. The vision is that a higher-level system (conceptually "Fragmenta"):

-   Monitors the performance and limitations of this v0.1 dictionary tool.
-   When frequent "translation not available" messages occur or when more complex translation needs are detected, Fragmenta could:
    *   Trigger a process to expand the dictionary.
    *   Orchestrate the integration of a more sophisticated, pre-trained neural translation model.
    *   Manage different translation models/tools for different language pairs or domains.

## Current Status

Tests currently show failures indicating instability in core model components. Work is ongoing to improve reliability and functionality.

## Code Location

`src/tools/translation_model/`
