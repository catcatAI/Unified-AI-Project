# VectorStore: ChromaDB Wrapper for Vector Storage

## Overview

This document provides an overview of the `VectorStore` module (`src/core/memory/vector_store.py`). This module implements a wrapper around ChromaDB, providing a simplified and robust interface for managing vector embeddings and associated documents.

## Purpose

The `VectorStore` aims to abstract the complexities of interacting directly with ChromaDB, offering a consistent API for common vector database operations. It enhances reliability by attempting to connect to a persistent HTTP client first and falling back to an in-memory ephemeral client if the primary connection fails. This ensures that the application can continue to function, albeit with potentially reduced persistence.

## Key Responsibilities and Features

*   **ChromaDB Client Management**: Manages the lifecycle of the ChromaDB client, including connection attempts and fallback mechanisms.
*   **Collection Management**: Interacts with a specified ChromaDB collection for all data operations.
*   **Document Addition (`add_documents`)**: Allows for adding new documents, along with their vector embeddings and metadata, to the store.
*   **Vector Querying (`query`)**: Supports querying the vector store with embeddings to find the most similar documents, with options for filtering and limiting results.
*   **Document Deletion (`delete_documents`)**: Provides functionality to remove documents from the store based on their unique identifiers.
*   **Document Update (`update_document`)**: Enables partial or full updates to existing documents, including their embeddings, metadata, or content.
*   **Robust Initialization**: Implements a fallback mechanism from `chromadb.HttpClient` to `chromadb.EphemeralClient` to ensure operational continuity.

## How it Works

The `VectorStore` class initializes by attempting to establish a connection to a ChromaDB instance via `chromadb.HttpClient` on `localhost:8000`. If this connection fails (e.g., the ChromaDB server is not running), it gracefully falls back to using `chromadb.EphemeralClient`, which creates an in-memory database. This ensures that the application can always operate, even if the persistent database is unavailable. All subsequent operations (add, query, delete, update) are performed on the `collection` object obtained from the active client.

## Integration with Other Modules

*   **`HAMMemoryManager`**: Likely a primary consumer, using `VectorStore` for storing and retrieving vector embeddings of memories.
*   **`ImportanceScorer`**: May interact with `VectorStore` to store and retrieve importance scores associated with memories.
*   **Other AI Components**: Any module requiring vector storage and retrieval capabilities can utilize this `VectorStore` wrapper.

## Code Location

`D:/Projects/Unified-AI-Project/apps/backend/src/core/memory/vector_store.py`
