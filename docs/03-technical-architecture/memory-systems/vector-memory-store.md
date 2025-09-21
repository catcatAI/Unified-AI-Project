# VectorMemoryStore: Semantic Memory Storage and Retrieval

## Overview

This document provides an overview of the `VectorMemoryStore` module (`src/core_ai/memory/vector_store.py`). This module is responsible for managing a vector store for AI memories, enabling advanced semantic search capabilities.

## Purpose

The `VectorMemoryStore` provides a crucial mechanism for storing and retrieving AI memories based on their semantic meaning rather than just keywords. This is fundamental for building more intelligent and context-aware memory systems that can find relevant information even if the exact keywords are not present in the query, thereby enhancing the AI's understanding and response generation.

## Key Responsibilities and Features

*   **ChromaDB Integration**: Utilizes `chromadb` as the underlying vector database. ChromaDB is an open-source embedding database that makes it easy to build LLM applications by making knowledge, facts, and skills pluggable for LLMs.
*   **Ephemeral Client Configuration**: The store is configured to use `chromadb.EphemeralClient`. This means that, by default, the data is not persisted to disk directly by this module. This configuration is particularly useful for testing environments or in scenarios where persistence is handled by a higher-level component (like `HAMMemoryManager`).
*   **Collection Management**: Automatically creates or retrieves a ChromaDB collection named "ham_memories". This collection is configured to use cosine similarity as the distance metric for vector comparisons, which is a common and effective measure for semantic similarity.
*   **Add Memory (`add_memory`)**: Provides a method to add a new memory to the vector store. Each memory includes its `content` (the text to be embedded), associated `metadata` (additional descriptive information), and a unique `memory_id`.
*   **Semantic Search (`semantic_search`)**: Performs a semantic search based on a `query` string. It returns the `n_results` most semantically similar memories from the collection. The search leverages the vector embeddings to find conceptual matches, not just lexical ones.

## How it Works

Upon initialization, the `VectorMemoryStore` sets up a ChromaDB client and ensures the "ham_memories" collection exists. When the `add_memory` method is called, the provided `content` is automatically converted into a vector embedding by ChromaDB (using its default or a configured embedding function). This embedding, along with the `metadata` and `memory_id`, is then stored in the ChromaDB collection. When `semantic_search` is invoked with a `query`, ChromaDB generates an embedding for the query and then efficiently finds the most similar embeddings within its collection, returning the corresponding memories.

## Integration with Other Modules

*   **`HAMMemoryManager`**: The `HAMMemoryManager` is the primary consumer of this module. It uses the `VectorMemoryStore` to store and retrieve semantic vectors of memories, forming a crucial part of the AI's long-term memory system.
*   **`chromadb`**: The core external library that provides the vector database functionalities.

## Code Location

`src/core_ai/memory/vector_store.py`