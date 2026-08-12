# RAGManager: Retrieval-Augmented Generation

## Overview

This document provides an overview of the `RAGManager` module (`src/core_ai/rag/rag_manager.py`). This module is responsible for managing the process of Retrieval-Augmented Generation (RAG) by handling the creation of vector embeddings for documents and performing efficient similarity searches.

## Purpose

The `RAGManager` provides the AI with a powerful mechanism for retrieving relevant information from a large corpus of documents to augment its responses. This is a key component for building more knowledgeable and context-aware AI systems that can ground their responses in factual information, reducing hallucinations and improving the accuracy of their outputs.

## Key Responsibilities and Features

*   **Vector Embeddings**: Utilizes a `SentenceTransformer` model (defaulting to `all-MiniLM-L6-v2`) to convert text documents into dense, numerical vector representations, also known as embeddings.
*   **Vector Indexing**: Employs `faiss`, a high-performance library from Facebook AI, to create and manage an index of the document vectors. This allows for extremely efficient similarity searches, even with a large number of documents.
*   **Document Storage**: Maintains a simple dictionary that maps the original text of the documents to their corresponding index in the `faiss` index.
*   **Similarity Search (`search`)**: Provides a `search` method that takes a query, converts it into a vector embedding, and then uses the `faiss` index to find the `k` most similar documents. It returns a list of tuples, where each tuple contains a retrieved document and its similarity score.

## How it Works

When a new document is added to the `RAGManager`, its text is first passed through the `SentenceTransformer` model to generate a vector embedding. This vector is then added to the `faiss` index, which is optimized for fast retrieval. When a search query is received, it is also converted into a vector using the same model. The `faiss` library is then used to efficiently compare the query vector against all the vectors in the index, returning the ones that are closest in the vector space. The `RAGManager` then retrieves the original text of these documents and returns them to the caller.

## Integration with Other Modules

*   **`ToolDispatcher`**: The `search` method of the `RAGManager` is exposed as a `rag_query` tool by the `ToolDispatcher`, allowing the AI to easily perform RAG searches as part of its toolset.
*   **`SentenceTransformer`**: The core external library used for generating the high-quality sentence and document embeddings.
*   **`faiss`**: The core external library that provides the efficient similarity search functionality.
*   **`numpy`**: Used for numerical operations, particularly for handling the vector embeddings.

## Code Location

`src/core_ai/rag/rag_manager.py`