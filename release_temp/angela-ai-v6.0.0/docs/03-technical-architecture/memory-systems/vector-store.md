# VectorStore: ChromaDB Wrapper for Semantic Memory

This document provides an overview of the `VectorStore` module (`src/core_ai/memory/vector_store.py`).

## Purpose

The `VectorStore` class serves as a robust and user-friendly interface for managing vector embeddings and their associated data using ChromaDB. Its primary purpose is to facilitate the implementation of semantic search, Retrieval Augmented Generation (RAG), and other advanced AI functionalities that rely on finding information based on semantic similarity rather than traditional keyword matching. By abstracting away the complexities of direct ChromaDB interaction, it provides a streamlined way to integrate vector storage capabilities into the AI system.

## Key Responsibilities and Features

*   **Initialization (`__init__`)**:
    *   Initializes a `chromadb.EphemeralClient` by default, which runs in-memory. This can be switched to a `chromadb.HttpClient` by setting the `CHROMA_HTTP_CLIENT=1` environment variable.
    *   Retrieves or creates a named collection (defaulting to `main_collection`) within the ChromaDB instance, serving as the container for documents and their embeddings.
    *   Includes comprehensive error handling to manage potential issues during the ChromaDB client or collection initialization, especially for dependency issues (e.g., `numpy` version conflicts).
*   **Add Documents (`add_documents`)**:
    *   Provides a method to add one or more documents to the vector store.
    *   Each document requires a unique `id`, its `embeddings` (a list of floating-point numbers representing its vector), `metadatas` (a dictionary for additional descriptive attributes), and optionally the original `documents` content (text).
    *   Logs the successful addition of documents.
*   **Query (`query`)**:
    *   Enables semantic similarity search by taking `query_embeddings` as input.
    *   Allows specifying the desired number of results (`n_results`) and applying `where` clauses for metadata-based filtering, enabling precise retrieval.
    *   Returns a structured dictionary containing the query results, including the IDs, embeddings, metadatas, and original document content of the matched items.
*   **Delete Documents (`delete_documents`)**:
    *   Facilitates the removal of documents from the collection based on a list of their unique `ids`.
    *   Logs the number of documents successfully deleted.
*   **Update Document (`update_document`)**:
    *   Allows for the modification of an existing document identified by its `id`.
    *   Supports updating the document's `embedding`, `metadata`, or `document` content individually or in combination.
    *   Includes a warning mechanism if the update method is called without any data to modify.

## How it Works

The `VectorStore` class acts as an intermediary layer between the AI application and the ChromaDB vector database. Upon instantiation, it sets up a persistent connection to ChromaDB and ensures a target collection is ready. When `add_documents` is called, the provided data (IDs, embeddings, metadata, and optional content) is passed directly to the ChromaDB collection, which internally handles the storage, indexing, and management of these vector representations. For retrieval, the `query` method sends query embeddings to ChromaDB, which then performs a similarity search across its indexed vectors and returns the most relevant results. The class also provides methods for lifecycle management of documents within the store, such as `update_document` and `delete_documents`.

## Integration with Other Modules

*   **`chromadb`**: This is the fundamental external library that provides the underlying vector database functionalities for storing and querying embeddings.
*   **`logging`**: Used throughout the module for logging operational information, warnings, and errors, which is crucial for monitoring and debugging.
*   **`HAMMemoryManager` (Conceptual)**: Modules responsible for managing the AI's hierarchical associative memory would likely integrate with this `VectorStore` to provide semantic search and retrieval capabilities for memories, allowing for more nuanced and context-aware memory recall.
*   **Retrieval Augmented Generation (RAG) Systems**: Any RAG-based AI component would utilize this `VectorStore` to efficiently retrieve relevant contextual information from a large corpus of data, which can then be used to augment LLM responses.

## Code Location

`src/core/memory/vector_store.py`
