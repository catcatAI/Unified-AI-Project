# RAG Manager: Retrieval-Augmented Generation

## Overview

The `RAGManager` (`src/core_ai/rag/rag_manager.py`) is a crucial component within the Unified-AI-Project that facilitates **Retrieval-Augmented Generation (RAG)**. Its primary function is to enable the AI to retrieve relevant information from a vast corpus of documents and use that information to inform and enhance its generated responses, particularly from Large Language Models (LLMs).

This module is essential for:

-   **Grounding LLM Responses**: Ensuring that AI-generated content is based on factual, retrieved information, reducing hallucinations.
-   **Accessing Up-to-Date Knowledge**: Allowing the AI to query and utilize knowledge that may not have been part of its initial training data.
-   **Improving Contextual Relevance**: Providing LLMs with specific, relevant context for a given query, leading to more accurate and pertinent responses.

## Key Responsibilities and Features

1.  **Document Management (`add_document`)**:
    *   Takes a text document and processes it to generate a high-dimensional vector embedding that captures its semantic meaning.
    *   Stores the document content and its corresponding vector in an efficient index for rapid retrieval.

2.  **Semantic Search (`search`)**:
    *   Given a natural language query, it converts the query into a vector embedding.
    *   Performs a similarity search within its indexed document collection to find the `k` most semantically similar documents.
    *   Returns a list of tuples, each containing the retrieved document content and a similarity score.

## Underlying Technologies

-   **Sentence Transformers (`sentence_transformers`)**:
    *   Used to convert text (documents and queries) into dense vector embeddings. These embeddings represent the semantic meaning of the text, allowing for comparisons based on meaning rather than just keywords.
    *   The default model used is `all-MiniLM-L6-v2`, a compact yet effective model for generating universal sentence embeddings.

-   **FAISS (`faiss`)**:
    *   Facebook AI Similarity Search (FAISS) is a library for efficient similarity search and clustering of dense vectors.
    *   The `RAGManager` uses `faiss.IndexFlatL2`, a basic but highly efficient index for L2 (Euclidean) distance similarity search. This enables very fast retrieval of similar documents from large datasets.

## How it Works

1.  **Indexing Phase**: When a document is added, `SentenceTransformer` converts its text into a numerical vector. This vector is then normalized and added to the FAISS index. The original document content is stored in an internal dictionary, mapped by its index position.
2.  **Retrieval Phase**: When a query is received, it is similarly converted into a vector. This query vector is then used to search the FAISS index for the `k` nearest (most similar) document vectors. The corresponding documents are retrieved from the internal storage and returned along with their similarity scores.

## Integration with Other Modules

-   **`MultiLLMService`**: The retrieved documents from `RAGManager` can be prepended or inserted into the context window of an LLM call, providing the LLM with relevant, up-to-date information to generate more accurate and grounded responses.
-   **`LearningManager`**: Could potentially feed new learned facts or insights into the `RAGManager`'s document collection, continuously expanding the AI's accessible knowledge base.
-   **`DialogueManager`**: Can use RAG to retrieve relevant conversational history or external knowledge to provide more informed and contextually appropriate responses to user queries.

## Code Location

`src/core_ai/rag/rag_manager.py`
