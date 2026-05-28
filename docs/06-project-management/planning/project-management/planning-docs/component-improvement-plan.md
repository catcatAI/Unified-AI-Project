# Proposal: Plan for Completing Unfinished Components

## 1. Overview

This document outlines a concrete plan for "completing" or "perfecting" the two components identified as unfinished: the **`FactExtractorModule`** and the **`HAMMemoryManager`**. The goal is to make these components more robust, configurable, and production-ready, which is a prerequisite for building more advanced features like the `AlphaDeepModel` that depend on them.

This plan is based on a detailed analysis of their current source code.

## 2. `FactExtractorModule` Improvements

**Location:** `apps/backend/src/core_ai/learning/fact_extractor_module.py`

The current module is a good prototype but relies on hardcoded values that limit its flexibility. The following improvements are proposed:

*   **Task 1.1: Make Model ID Configurable.**
    *   **Problem:** The `model_id` is currently hardcoded as `"fact_extraction_model_placeholder"`.
    *   **Solution:** Modify the `__init__` method to accept an optional `model_id` string. In the `extract_facts` method, use this instance variable instead of the hardcoded placeholder. This allows different instances of the module to use different LLMs.

*   **Task 1.2: Enable Configurable LLM Parameters.**
    *   **Problem:** The call to the LLM service has `params` commented out.
    *   **Solution:** Allow a `params` dictionary to be passed during initialization and used in the `chat_completion` call. This enables tuning of parameters like `temperature` for better performance.

*   **Task 1.3: Externalize Prompt Templates.**
    *   **Problem:** The extraction prompt is hardcoded inside the `_construct_fact_extraction_prompt` method.
    *   **Solution:** Move the prompt template to a configuration file, such as `apps/backend/configs/prompts.yaml`. The module would then load this prompt at runtime. This allows for easier prompt engineering without code changes.

*   **Task 1.4: Improve Logging.**
    *   **Problem:** The module uses `print()` for logging errors and status.
    *   **Solution:** Replace all `print()` calls with the standard `logging` module (`logger.info`, `logger.warning`, `logger.error`) for consistency with the rest of the application.

## 3. `HAMMemoryManager` (Deep Mapping) Improvements

**Location:** `apps/backend/src/core_ai/memory/ham_memory_manager.py`

The `HAMMemoryManager` is the core of the "Deep Mapping" process. The following improvements will make its mapping capabilities more powerful and useful for downstream systems like the `AlphaDeepModel`.

*   **Task 2.1: Enhance Text Abstraction (`_abstract_text`).**
    *   **Problem:** The current method only performs basic keyword extraction and summarization. It doesn't capture the rich relational context the user desires.
    *   **Solution:** Enhance the method to perform more sophisticated Natural Language Understanding (NLU). This could involve using an NLP library like `spacy` or making a dedicated LLM call to extract named entities and the relationships between them. The output "gist" would then be a much richer, structured object.

*   **Task 2.2: Add Raw Gist Recall Method.**
    *   **Problem:** The `recall_gist` method returns a human-readable string, which is not useful for other programmatic systems that need the raw, structured data.
    *   **Solution:** Create a new method, `recall_raw_gist(memory_id: str) -> Optional[dict]`, that performs all the same decryption and decompression steps but returns the final abstracted dictionary object instead of the "rehydrated" string.

*   **Task 2.3: Improve Multi-Modal Data Handling.**
    *   **Problem:** The `store_experience` method converts any non-text data to a simple string (`str(raw_data)`), losing all its structure.
    *   **Solution:** Add explicit handling for different `data_type` values. For example, if `data_type` is `structured_data` or `learned_fact`, the method should serialize it directly (e.g., with `json.dumps`) rather than converting it to a simple string.

## 4. Proposed Order of Implementation

It is recommended to implement these changes in the following order:

1.  **`FactExtractorModule` Improvements (Tasks 1.1 - 1.4):** These are relatively straightforward and will make the module more robust.
2.  **`HAMMemoryManager` - Add Raw Gist Recall Method (Task 2.2):** This is a crucial prerequisite for building and testing other components that consume HAM's output.
3.  **`HAMMemoryManager` - Other Improvements (Tasks 2.1, 2.3):** These are more involved and can be tackled after the foundational improvements are in place.

This plan provides a clear path forward for maturing these key components of the AI system.
