# HAMErrors: Hierarchical Associative Memory Exception Definitions

## Overview

This document provides an overview of the `ham_errors.py` module (`src/core_ai/memory/ham_errors.py`). This module is dedicated to defining custom exception classes for various errors that can be encountered during Hierarchical Associative Memory (HAM) operations.

## Purpose

The primary purpose of `ham_errors.py` is to provide a structured and specific error handling mechanism for the HAM system. By defining a hierarchy of custom exceptions, it allows for more granular error management throughout the codebase. This makes it easier to identify, catch, and respond to specific types of failures within HAM operations, leading to more robust and maintainable code.

## Key Responsibilities and Features

*   **`HAMMemoryError`**: This is the base exception class for all errors related to HAM memory operations. Any custom exception within the HAM system should inherit from `HAMMemoryError`. This allows developers to catch any HAM-related error with a single `except HAMMemoryError` clause, simplifying broad error handling.
*   **`HAMQueryError`**: A specific exception class designed for errors that occur during HAM memory queries. Examples include issues with invalid query parameters, failures during data retrieval, or problems with query execution against the memory store.
*   **`HAMStoreError`**: A specific exception class for errors encountered during HAM memory storage operations. This covers issues such as data serialization problems, failures when writing to the underlying storage backend, or integrity constraints violations during storage.
*   **`VectorStoreError`**: A specific exception class dedicated to errors related to vector store operations. Given that vector stores are often integrated with HAM for semantic search and retrieval, this exception provides a clear way to signal failures originating from the vector storage layer.

## How it Works

This module functions by defining a clear hierarchy of exception classes. When an error condition arises within a HAM-related operation (e.g., a query fails, or data cannot be stored), the relevant specific exception (e.g., `HAMQueryError` or `HAMStoreError`) is raised. This allows the calling code to implement precise `try-except` blocks, enabling more informative error messages to the user, triggering specific recovery actions, or logging detailed error information for debugging.

## Integration with Other Modules

*   **`HAMMemoryManager`**: This module, along with its various sub-components and utility functions, is the primary consumer of these exception classes. It will raise these exceptions when errors occur during memory operations.
*   **`VectorMemoryStore`**: Specifically, the `VectorMemoryStore` implementation would raise `VectorStoreError` for failures within its domain.
*   **Client Modules**: Any module or component that interacts with the HAM system (e.g., for storing new experiences, querying past memories) would import and catch these exceptions to implement robust error handling and graceful degradation.

## Code Location

`src/core_ai/memory/ham_errors.py`