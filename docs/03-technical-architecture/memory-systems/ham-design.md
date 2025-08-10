# Hierarchical Abstractive Memory (HAM) - Design Specification v0.2

## 1. Introduction

The Hierarchical Abstractive Memory (HAM) model is designed for MikoAI to
efficiently store and process vast amounts of experiential data. It employs a
layered approach, transforming raw sensory input into compact, abstract
representations for long-term storage and reasoning, while allowing
reconstruction for interaction. This system aims to provide scalability,
efficiency, and a foundation for complex learning, evolution, and integration
with systems like a Translation Model and the conceptual Fragmenta layer.

## 2. Core Architecture

The HAM model consists of two primary layers:

- **Surface Layer (SL):** Interfaces with the external environment and other
  MikoAI modules. Handles raw data input/output, initial processing
  (abstraction, compression, encryption), and the "rehydration" (decryption,
  decompression, reconstruction) of abstract data into usable forms.
- **Core Layer (CL):** Stores highly abstracted, compressed, and encrypted
  representations of experiences. This layer is optimized for efficient storage
  and deep-level pattern recognition and reasoning.

## 3. Data Flow

### 3.1. Storage Process (SL to CL)

1.  **Input Reception (SL):** Raw data (e.g., text dialogue in various
    languages, user commands, observed events) is received.
2.  **Preprocessing (SL):** Basic cleaning, normalization.
3.  **Abstraction (SL):** Raw data is transformed into an abstract "gist."
    - **v0.2 Mechanism - Text:**
      - **Current Implementation (Placeholders):** The `_abstract_text` method currently performs basic summarization and keyword extraction. Advanced features like radical extraction for Chinese text and detailed linguistic feature (e.g., Part-of-Speech tags, Named Entities) extraction for English text are **conceptual placeholders** for future development.
      - **Chinese Text (Conceptual):** Extract **radicals** (e.g., using a library like
        `hanzidentifier` or a custom radical lookup). Store as a list or
        frequency map of radicals. Additional keywords can also be extracted.
      - **English Text (Conceptual):** Extract **linguistic features** (e.g., Part-of-Speech
        tags, Named Entities, keywords using TF-IDF or a lightweight NLP library
        like spaCy if feasible, or rule-based keyword extraction). Store as a
        structured dictionary of features.
      - A concise summary can still be generated.
      - Metadata (timestamp, source, language, emotion tag) is preserved.
    - The output is a structured dictionary, e.g.,
      `{"summary": "...", "language": "zh", "radicals": ["水", "木"], "keywords": ["京都", "旅行"], "original_length": len(text)}`
      or
      `{"summary": "...", "language": "en", "pos_tags": [...], "entities": [...], "keywords": ["Kyoto", "travel"]}`.
4.  **Compression (SL):** The abstracted data (gist + metadata) is compressed.
    - _v0.2 Mechanism:_ `zlib` library (remains suitable).
5.  **Encryption (SL):** The compressed data is encrypted.
    - _v0.2 Mechanism:_ Use **Fernet symmetric encryption** from the
      `cryptography` library. Keys are managed via the `MIKO_HAM_KEY`
      environment variable. For development, if not set, a temporary key is
      generated (data not persistent across sessions if this temporary key is
      used).
6.  **Storage (CL):** The encrypted, compressed, abstract data package is sent
    to the Core Layer.
    - _v0.2 Storage Format:_ JSON objects with fields like `id`, `timestamp`,
      `encrypted_package_b64` (base64 encoded Fernet token), `metadata` (which
      includes `sha256_checksum` and other tags like language).

### 3.2. Retrieval and Reconstruction Process (CL to SL)

1.  **Query Reception (SL/CL):** A query is initiated (e.g., by keywords,
    features, semantic concepts).
2.  **Core Layer Retrieval (CL):**
    - Search based on metadata (language, timestamp, source) and indexed
      components of the abstracted gist (e.g., specific radicals, keywords,
      entities).
    - **Fragmenta Integration:** HAM's `query_core_memory` method will be
      capable of returning **multiple candidate gists** (e.g., top N matches
      based on query relevance) to the Fragmenta layer for further processing
      (e.g., vector/quantum-layer selection, fusion, or reasoning).
3.  **Decryption (SL):** Retrieved data package is decrypted using Fernet.
4.  **Decompression (SL):** Data is decompressed using `zlib`.
5.  **Rehydration/Reconstruction (SL):**
    - The abstract gist (radicals, linguistic features, summary) is presented.
    - **Verification through Comparison:** For critical queries or when
      ambiguity is high, the system can rehydrate multiple retrieved gists.
      These rehydrated versions (or their key features) are then compared
      against the original query or a target context. This comparison helps
      confirm relevance, identify discrepancies, or flag incomplete/erroneous
      recall. The comparison logic could involve feature overlap scores,
      embedding similarity (if embeddings are used for gists), or even prompting
      an LLM for a semantic similarity score.
6.  **Output (SL):** Reconstructed data is provided.

## 4. `HAMMemoryManager` API (Python Class) - v0.2 Updates

- `store_experience(self, raw_data: Any, data_type: str, metadata: Optional[DialogueMemoryEntryMetadata] = None) -> Optional[str]`:
  - Stores a new experience into the HAM. The raw_data is processed (abstracted, checksummed, compressed, encrypted) and then stored.
  - Integrates with `VectorMemoryStore` for semantic indexing.
- `recall_gist(self, memory_id: str) -> Optional[HAMRecallResult]`:
  - Recalls an abstracted gist of an experience by its memory ID and returns a human-readable rehydrated version.
  - Returns a `HAMRecallResult` object, which includes the rehydrated string gist and metadata.
- `recall_raw_gist(self, memory_id: str) -> Optional[Dict[str, Any]]`:
  - Recalls the raw, structured gist dictionary of an experience by its ID.
  - For programmatic use by other AI components that need the structured data, bypassing the human-readable rehydration step.
- `query_core_memory(self, keywords: Optional[List[str]] = None, date_range: Optional[Tuple[datetime, datetime]] = None, data_type_filter: Optional[str] = None, metadata_filters: Optional[Dict[str, Any]] = None, user_id_for_facts: Optional[str] = None, limit: int = 5, sort_by_confidence: bool = False, return_multiple_candidates: bool = False, semantic_query: Optional[str] = None) -> List[HAMRecallResult]`:
  - Enhanced query function supporting various filters: keywords, date range, data type, metadata, user ID.
  - **New in v0.2:** `semantic_query`: Allows semantic search using the integrated `VectorMemoryStore` (ChromaDB).
  - `return_multiple_candidates`: If True, returns a list of top N candidate gists.
- `increment_metadata_field(self, memory_id: str, field_name: str, increment_by: int = 1) -> bool`:
  - Efficiently increments a numerical value in a record's metadata without
    requiring a full recall-modify-store cycle.
  - Primarily used by `LearningManager` to increase the `corroboration_count`
    for a fact when a duplicate is received, as part of the anti-resonance
    mechanism.


## 5. Core Layer Storage (v0.2)

- Remains JSON file-based for the prototype (`ham_core_memory.json`).
- The structure of stored items will accommodate Fernet encrypted packages
  (stored as base64 strings).
- Metadata will explicitly include `language`.

## 6. Abstraction Mechanism (v0.2 Detail for Text)

- **Chinese Text:**
  - **Radical Extraction:** Use a Python library (e.g., `hanzidentifier`, or a
    simpler custom lookup if full library is too heavy) to get radicals for each
    character. Store as a list or frequency map.
  - **Keyword Extraction:** Standard keyword extraction (e.g., TF-IDF if a
    corpus is available, or simple frequency after stopword removal).
- **English Text:**
  - **Linguistic Feature Extraction:**
    - POS Tagging & Named Entity Recognition: Use a lightweight NLP library
      (e.g., `spaCy` with a small model, or `NLTK` if environment allows, or
      simplified rule-based patterns for common entities).
    - Keywords: As above.
- **Summarization:** Retain simple first-sentence or keyword-based summarization
  for v0.2 prototype.
- **Output:** Structured dictionary containing language, summary, original
  length, and language-specific features (radicals or linguistic features).

## 7. Error Handling & Data Integrity (v0.2)

- Log errors during encryption, decryption, compression, decompression,
  abstraction.
- **Data Integrity**: For data integrity, when storing a package in CL, a
  **SHA256 checksum** of the original abstracted data (before
  compression/encryption) is computed and stored within the package's metadata.
  Upon retrieval and full de-processing (after decryption and decompression),
  the checksum is recomputed and compared against the stored value to detect
  potential corruption. A mismatch will result in a critical warning.
- **Anti-Resonance and Information Quality Verification**: To combat "idiot
  resonance" where popularity is mistaken for accuracy, the HAM system supports
  a quality-based verification model implemented in the `LearningManager`. When
  a duplicate fact is detected, its confidence is **not** increased. Instead,
  its `corroboration_count` metadata field is incremented via the
  `increment_metadata_field` method. This explicitly separates the measure of a
  fact's prevalence from its assessed quality, preventing the amplification of
  potentially incorrect information.
- The comparison mechanism in `compare_rehydrated_memory` (or similar logic in
  SL) will help identify incomplete or erroneous recall, triggering potential
  re-querying or clarification dialogues.

## 8. Support for Translation Model

- HAM will store abstracted text representations along with their original
  language metadata.
- When the Translation Model is invoked, it can query HAM for text in a source
  language (using `language_filter`). The abstracted gist (e.g., keywords,
  entities, radicals) can provide rich semantic context to the Translation
  Model, potentially improving translation quality beyond just raw text input.
- Translated text can itself be stored in HAM as a new experience, linked to the
  original, with its own language tag and abstracted features.

## 9. Semantic Search and Vector Database Integration (Implemented in v0.2)

The HAM system now integrates a vector memory store (`VectorMemoryStore`) using ChromaDB to enable semantic search capabilities. This significantly enhances the `query_core_memory` method, allowing for more nuanced and context-aware retrieval of memories.

- **VectorMemoryStore (`src/core_ai/memory/vector_store.py`):** Encapsulates ChromaDB logic for storing and querying vector embeddings of memories.
- **Semantic Search in `query_core_memory`:** The `query_core_memory` method now accepts a `semantic_query` parameter. When provided, it performs a vector similarity search against the stored embeddings to find relevant memories, complementing keyword and metadata-based filtering.
- **Embedding Generation:** Memories are converted into vector embeddings (e.g., using Sentence Transformers or similar models) before being stored in the `VectorMemoryStore`.

## 10. Future Considerations (Post v0.2)

- **Key Management for Fernet:** More robust key rotation and storage.
- **Generative Reconstruction in SL:** Use LLMs to elaborate on abstract gists.
- **Multi-Modal Data Abstraction:** Define specific abstraction methods for
  images (e.g., object tags, scene descriptions, embeddings) and audio (e.g.,
  transcript, audio fingerprints, speaker ID).

This document will be updated as the HAM system evolves.


--- 
*Last Updated: 2025-08-10*