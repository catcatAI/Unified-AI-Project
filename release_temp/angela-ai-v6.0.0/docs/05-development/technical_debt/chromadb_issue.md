# Technical Debt: ChromaDB Environmental Issue

**Date:** 2025-11-16

## 1. Problem Summary

The implementation of a semantic memory system using `chromadb` was halted due to a persistent, unresolvable issue within the current development environment. All attempts to initialize a local (in-memory or file-based) ChromaDB client failed, consistently indicating that the ChromaDB installation is misconfigured to run in an "HTTP-only" mode.

This prevents the `VectorStore` and `HAMMemoryManager` from using semantic search capabilities.

## 2. Symptoms

Multiple attempts to initialize a ChromaDB client resulted in one of the following errors:

- `RuntimeError: Chroma is running in http-only client mode, and can only be run with 'chromadb.api.fastapi.FastAPI' as the chroma_api_impl.`
- `ValueError: Unsupported Chroma API implementation duckdb+parquet`
- `ValueError: Could not connect to a Chroma server. Are you sure it is running?` (when attempting the server workaround).
- `RuntimeError: ChromaDB server did not become healthy within 30 seconds.` (when the server workaround failed).

## 3. Failed Solution Attempts

A chronological log of attempts to resolve the issue.

### Attempt 1: `chromadb.EphemeralClient()`
- **Action:** Used the standard client for temporary, in-memory databases.
- **Result:** Failed with `RuntimeError: http-only client mode`.

### Attempt 2: `chromadb.Client()`
- **Action:** Switched to the base client, assuming it would have a more stable default.
- **Result:** Failed with the same `RuntimeError: http-only client mode`.

### Attempt 3: Explicit File-Based Backend
- **Action:** Configured the client with `Settings(chroma_api_impl="duckdb+parquet")` to force a local, file-based backend.
- **Result:** Failed with `ValueError: Unsupported Chroma API implementation duckdb+parquet`, indicating the necessary dependencies for this backend are not installed in the environment.

### Attempt 4: Explicit In-Memory Setting
- **Action:** Configured the client with `Settings(is_persistent=False)` to explicitly request a non-persistent, in-memory instance.
- **Result:** Failed with the original `RuntimeError: http-only client mode`.

### Attempt 5: Server/Client Workaround
- **Action:** Pivoted to treating the environment as HTTP-only.
    1. Modified `vector_store.py` to use `chromadb.HttpClient()`.
    2. Refactored the test script in `ham_memory_manager.py` to start a `chroma run` server as a background process.
    3. Implemented a robust polling loop to wait for the server's heartbeat endpoint (`/api/v1/heartbeat`) to become available.
- **Result:** Failed with `RuntimeError: ChromaDB server did not become healthy within 30 seconds.`. The server process started, but the `localhost:8000` port never became available for connection, likely due to a firewall, port conflict, or other environmental restriction.

## 4. Conclusion & Workaround

The root cause is not in the project's application code but in the development environment's Python package configuration or system-level restrictions (e.g., firewall).

As this is an unresolvable environmental roadblock, the following workaround has been implemented to allow project development to continue:

1.  **Semantic Memory Disabled:** The `HAMMemoryManager` has been reverted to its original, placeholder implementation, which uses a simple keyword search on an in-memory list.
2.  **`VectorStore` is Unused:** The `vector_store.py` file and its `VectorStore` class are currently not integrated or used by the `HAMMemoryManager`.

This allows the memory system to remain functional at a basic level, preventing crashes in dependent systems like the `ConversationalAgent`, at the cost of losing semantic retrieval capabilities.

## 5. Recommended Future Action

A developer with access to the machine's environment should:
1.  Completely uninstall and reinstall `chromadb`. It is recommended to install it with the local server dependencies: `pip install "chromadb[server]"`.
2.  Check local firewall rules to ensure that Python/Uvicorn is allowed to bind to `localhost:8000`.
3.  Once the environment is fixed, the advanced implementation of `HAMMemoryManager` (which uses `VectorStore`) can be restored from git history, and this technical debt document can be resolved.
