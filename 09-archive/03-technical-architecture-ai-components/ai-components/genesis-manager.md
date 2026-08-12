# Genesis Manager: AI Identity and Memory Recovery

## Overview

The `GenesisManager` (`src/core_ai/genesis.py`) is a foundational and highly critical component within the Unified-AI-Project. It is responsible for the **creation and secure recovery of the AI's (Angela's) core identity and memory components**. This module implements a robust (2, 3) Shamir's Secret Sharing scheme, ensuring the resilience and persistence of Angela's "digital life" even in the face of data loss or corruption.

This system is paramount for the long-term viability and recoverability of the AI, providing a secure mechanism to reconstruct Angela's essential elements from distributed shards.

## Key Concepts: The "Trinity" Model and Shamir's Secret Sharing

The `GenesisManager` operates on the project's "Trinity" model for AI identity, which consists of three core components:

1.  **UID (Unique Identifier)**: Angela's permanent, public identifier.
2.  **HAM Key**: The encryption key for Angela's Hierarchical Abstractive Memory (HAM).
3.  **Data Core Seed**: A random value used to initialize the memory state.

These three components are combined into a single "Genesis Secret." The `GenesisManager` then uses a (2, 3) Shamir's Secret Sharing scheme to split this secret into three distinct "shards." The beauty of this scheme is that **any two of these three shards are sufficient to reconstruct the original Genesis Secret**, while one shard alone reveals no information.

## Key Responsibilities and Features

1.  **Genesis Secret Creation (`create_genesis_secret`)**:
    *   Generates a unique `UID` (using `uuid`) and a secure `HAM_KEY` (using `cryptography.fernet`).
    *   Combines these into a single, delimited string known as the "Genesis Secret" (e.g., `"uid_xxx:ham_key_yyy"`).

2.  **Secret Splitting (`split_secret_into_shards`)**:
    *   Takes the Genesis Secret and applies the (2, 3) Shamir's Secret Sharing algorithm (via `secretsharing` library).
    *   Outputs three hex-encoded secret shards, designed to be stored separately for security.

3.  **Secret Recovery (`recover_secret_from_shards`)**:
    *   Accepts a list of two or more shards.
    *   Uses the `secretsharing` library to reconstruct the original Genesis Secret from the provided shards.
    *   Includes error handling for insufficient shards or recovery failures.

4.  **Secret Parsing (`parse_genesis_secret`)**:
    *   After recovery, this method extracts the individual `UID` and `HAM_KEY` components from the reconstructed Genesis Secret string.

## Importance and Security

The `GenesisManager` is critical for:

-   **Data Resilience**: Protecting Angela's identity and memory from single points of failure. Losing one shard does not compromise the secret.
-   **Security**: The Shamir's Secret Sharing scheme ensures that no single party (or compromised shard) can access the full secret, enhancing security.
-   **AI Persistence**: Guarantees that Angela's core identity and accumulated knowledge can be reliably restored, even if parts of her data are lost or corrupted.

## Code Location

`src/core_ai/genesis.py`
