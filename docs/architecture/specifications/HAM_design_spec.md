# Hierarchical Abstractive Memory (HAM) - Design Specification v0.2.1

## 1. Introduction

The Hierarchical Abstractive Memory (HAM) model is designed for MikoAI to efficiently store and process vast amounts of experiential data. It employs a layered approach, transforming raw sensory input into compact, abstract representations for long-term storage and reasoning, while allowing reconstruction for interaction. This system aims to provide scalability, efficiency, and a foundation for complex learning, evolution, and integration with systems like a Translation Model and the conceptual Fragmenta layer.

## 2. Core Architecture

The HAM model consists of two primary layers:

*   **Surface Layer (SL):** Interfaces with the external environment and other MikoAI modules. Handles raw data input/output, initial processing (abstraction, compression, encryption), and the "rehydration" (decryption, decompression, reconstruction) of abstract data into usable forms. This corresponds to the methods within `HAMMemoryManager`.
*   **Core Layer (CL):** Represents the persistent storage mechanism (e.g., the JSON file). It stores highly abstracted, compressed, and encrypted representations of experiences. This layer is optimized for efficient storage and deep-level pattern recognition and reasoning.

## 3. Data Flow

### 3.1. Storage Process (SL to CL)

1.  **Input Reception (SL):** Raw data (e.g., text dialogue, user commands, observed events) is received by `HAMMemoryManager.store_experience`.
2.  **Preprocessing (SL):** Basic cleaning, normalization (implicitly part of abstraction).
3.  **Abstraction (SL):** Raw data is transformed into an abstract "gist" by `_abstract_text` if `data_type` indicates text.
    *   **v0.2.1 Implemented Mechanism - Text:**
        *   Primary focus on **summarization** (first sentence) and **keyword extraction** (top 5 frequent words, excluding basic English stopwords).
        *   Placeholders for advanced language-specific features: `radicals_placeholder` (for Chinese-like text) and `pos_tags_placeholder` (for English-like text) are generated as dummy values to indicate conceptual support, but actual linguistic processing for these is not implemented in `_abstract_text`.
        *   Metadata (timestamp, source, language if provided in input metadata, emotion tag if provided) is preserved.
    *   The output of abstraction is a structured dictionary, e.g., `{"summary": "...", "keywords": ["test", "dialogue"], "original_length": len(text), "radicals_placeholder": None, "pos_tags_placeholder": [{"test": "NOUN_placeholder"}, {"dialogue": "NOUN_placeholder"}]}`.
4.  **Checksum Calculation (SL):** A SHA256 checksum of the (JSON-serialized) abstracted gist is calculated and added to the metadata.
5.  **Compression (SL):** The abstracted data (gist as JSON string) is compressed using `zlib` (`_compress`).
6.  **Encryption (SL):** The compressed data is encrypted using Fernet symmetric encryption (`_encrypt`).
    *   Relies on the `MIKO_HAM_KEY` environment variable. If not set, a temporary session key is generated with warnings.
7.  **Storage (CL):** The encrypted, compressed, abstract data package is written to the Core Layer (JSON file via `_save_core_memory_to_file`).
    *   *v0.2.1 Storage Format:* The JSON file has a top-level structure: `{"next_memory_id": <int>, "store": {"mem_id1": <HAMDataPackageInternal_B64_Representation>, ...}}`.
    *   Each `<HAMDataPackageInternal_B64_Representation>` includes `timestamp`, `data_type`, `encrypted_package_b64` (base64 encoded string of the encrypted bytes), and `metadata` (which contains the `sha256_checksum`).

### 3.2. Retrieval and Reconstruction Process (CL to SL)

1.  **Query Reception (SL/CL):** A query is initiated (e.g., by memory ID, keywords, metadata filters) via `recall_gist` or `query_core_memory`.
2.  **Core Layer Retrieval (CL):** Data is read from the JSON file (`_load_core_memory_from_file` on init, or implicitly accessed via `self.core_memory_store`).
    *   **Fragmenta Integration Note:** The `query_core_memory` method's `limit` parameter allows returning multiple candidate items, which can serve Fragmenta's need for top N matches.
3.  **Decryption (SL):** Retrieved `encrypted_package_b64` is base64 decoded, then decrypted using Fernet (`_decrypt`).
4.  **Decompression (SL):** Data is decompressed using `zlib` (`_decompress`).
5.  **Checksum Verification (SL):** The SHA256 checksum of the decompressed data (original abstracted gist) is recomputed and compared against the checksum stored in its metadata. Mismatches are logged as warnings.
6.  **Rehydration/Reconstruction (SL):**
    *   If the `data_type` indicates text, the JSON string of the abstracted gist is parsed. The `_rehydrate_text_gist` method then formats this into a human-readable string including summary, keywords, and placeholder features.
    *   For non-text data, the decompressed string is returned directly.
7.  **Output (SL):** Reconstructed data is provided as part of a `HAMRecallResult` object.
    *   **Verification through Comparison (Conceptual):** The spec mentions a conceptual `compare_rehydrated_memory` method for the SL to perform verification of recalled data against a context. This is not part of `HAMMemoryManager` itself but a higher-level process.

## 4. `HAMMemoryManager` API (Python Class) - v0.2.1 (Reflecting Implementation)

*   `store_experience(self, raw_data: Any, data_type: str, metadata: Optional[DialogueMemoryEntryMetadata] = None) -> Optional[str]`:
    *   `language` is not a direct parameter; it should be included in the `metadata` argument if relevant (e.g., `metadata={"language": "en", ...}`).
    *   Returns `Optional[str]` (memory ID) as storage can fail (e.g., due to simulated disk limits).
*   `recall_gist(self, memory_id: str) -> Optional[HAMRecallResult]`:
    *   Returns a `HAMRecallResult` TypedDict (defined in `src/shared/types/common_types.py`) or `None`.
    *   `HAMRecallResult` includes `id`, `timestamp`, `data_type`, `rehydrated_gist` (string), and `metadata`.
*   `query_core_memory(self, keywords: Optional[List[str]] = None, date_range: Optional[Tuple[datetime, datetime]] = None, data_type_filter: Optional[str] = None, metadata_filters: Optional[Dict[str, Any]] = None, user_id_for_facts: Optional[str] = None, limit: int = 5, sort_by_confidence: bool = False) -> List[HAMRecallResult]`:
    *   `keywords`: Searches within the (stringified) metadata.
    *   `data_type_filter`: Supports prefix matching (e.g., "learned_fact" matches "learned_fact_X").
    *   `metadata_filters`: For exact matches on metadata fields. Language filtering would be done via `metadata_filters={"language": "en"}`.
    *   `user_id_for_facts`: Specific filter for "learned_fact" types.
    *   `limit`: Controls the maximum number of results.
    *   `sort_by_confidence`: Sorts results by `metadata.confidence` if applicable.
*   **Conceptual Method (Not in `HAMMemoryManager`):** `compare_rehydrated_memory` remains a conceptual SL process.

## 5. Core Layer Storage (v0.2.1 Implementation)

*   JSON file-based (`core_storage_filename` parameter, e.g., `ham_core_memory.json`).
*   Top-level structure: `{"next_memory_id": <int>, "store": {"mem_id1": <package>, "mem_id2": <package>}}`.
*   Each `<package>` contains `timestamp`, `data_type`, `encrypted_package_b64` (string), and `metadata`.
*   `language` information, if relevant, must be part of the `metadata` provided to `store_experience`.
*   The `HAMMemoryManager` can be integrated with a `ResourceAwarenessService` to simulate disk usage limits and associated write lag.

## 6. Abstraction Mechanism (v0.2.1 Implemented Detail for Text)

*   **Summarization:** Basic first-sentence extraction.
*   **Keyword Extraction:** Top 5 frequent words (lowercase, punctuation stripped, basic English stopwords removed).
*   **Advanced Linguistic Features (Chinese Radicals, English POS/NER):**
    *   The `_abstract_text` method includes `radicals_placeholder` and `pos_tags_placeholder` fields in the output gist.
    *   However, these are filled with **dummy/placeholder values** in the current implementation. Actual extraction of Chinese radicals or detailed English POS/NER tags using libraries like `hanzidentifier` or `spaCy` is **not implemented** within `_abstract_text`.
    *   The spec should accurately reflect this: the system is architected to *potentially* hold such features, but the current v0.2.1 implementation of abstraction provides only placeholders for them.
*   **Output:** Structured dictionary containing summary, keywords, original length, and potentially `None` or placeholder lists for `radicals_placeholder` and `pos_tags_placeholder`.

## 7. Error Handling & Data Integrity (v0.2.1 Implementation)

*   Logs errors during SL processing (encryption, decryption, compression, decompression, abstraction).
*   **SHA256 Checksum:** Calculated on the JSON string of the abstracted gist (before compression/encryption) and stored in metadata. Verified upon full retrieval and de-processing. Mismatches log a critical warning.
*   The conceptual `compare_rehydrated_memory` is not part of `HAMMemoryManager`.

## 8. Support for Translation Model

*   HAM stores abstracted text representations. If `language` is provided in the `metadata` during storage, it can be used for filtering.
*   The `query_core_memory` can use `metadata_filters={"language": "en"}`.
*   Abstracted gists (keywords, summary) can provide context to a Translation Model.
*   Translated text can be stored as new experiences.

## 9. Future Considerations (Post v0.2.1)
*   **Key Management for Fernet:** More robust key rotation and secure storage (beyond environment variables for production).
*   **Actual Linguistic Feature Extraction:** Implement actual Chinese radical extraction and English POS/NER tagging in `_abstract_text` using appropriate libraries, replacing current placeholders.
*   **Semantic Embeddings for Abstraction:** Integrate Sentence Transformers or similar for richer semantic gists and enabling vector similarity search in `query_core_memory`.
*   **Generative Reconstruction in SL:** Use LLMs to elaborate on abstract gists for more natural rehydration.
*   **Multi-Modal Data Abstraction:** Define and implement specific abstraction methods for images, audio, etc.
*   **Review `latin-1` usage:** The use of `latin-1` for `encrypted_package.decode('latin-1')` during serialization and `.encode('latin-1')` during deserialization for the base64 string is unconventional. Standard base64 operations typically use `ascii` or `utf-8` for the intermediate string representation. This should be reviewed for correctness and potential issues with certain byte sequences, although it might function correctly if applied consistently.

This document will be updated as the HAM system evolves.
