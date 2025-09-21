# Key Management

## Overview

The `UnifiedKeyManager` (`src/shared/key_manager.py`) is a critical security component within the Unified-AI-Project responsible for **centralized management of API keys and sensitive credentials**. It provides a robust mechanism for handling keys across different operational modes (development, production, and a specialized demo mode), ensuring secure access to external services and internal encrypted data.

This module is essential for maintaining the confidentiality and integrity of sensitive information, particularly the `MIKO_HAM_KEY` which encrypts Angela's core memory.

## Key Responsibilities and Features

1.  **Centralized Key Retrieval**: 
    *   Provides a unified interface (`get_key`) to retrieve various API keys and secrets.
    *   Prioritizes fetching keys from environment variables for production and secure deployments.

2.  **Demo Mode Management**: 
    *   Automatically detects if the system is running in a "demo mode" based on configurable patterns (e.g., specific environment variables).
    *   In demo mode, it uses predefined `fixed_keys` from a configuration file (`configs/unified_demo_config.yaml`) instead of live credentials.
    *   Can execute `auto_actions` (like setting up learning environments or triggering cleanup) specifically for demo scenarios.

3.  **Environment Variable Integration**: 
    *   Seamlessly integrates with system environment variables, which is the recommended way to manage secrets in production.
    *   In demo mode, it can temporarily set environment variables to simulate a configured environment.

4.  **Configuration Loading**: 
    *   Loads key management and demo mode configurations from a YAML file, allowing for flexible and externalized management of these settings.

5.  **HAM Key Generation and Management (`generate_ham_key`)**: 
    *   Specifically handles the `MIKO_HAM_KEY`, which is crucial for encrypting and decrypting the Hierarchical Abstractive Memory (HAM).
    *   In production, it generates a new, unique `Fernet` key for HAM encryption.
    *   In demo mode, it uses a fixed, predefined HAM key, facilitating reproducible demo environments.

## How it Works

The `UnifiedKeyManager` initializes by loading its configuration and detecting the operational mode. When `get_key` is called, it first checks if demo mode is active and if a fixed key is defined for the requested `key_name`. If not, it attempts to retrieve the key from system environment variables. The `generate_ham_key` method provides a secure way to obtain the HAM encryption key, either by generating a new one or using a fixed demo key.

## Integration and Importance

-   **Security**: Centralizes key management, reducing the risk of hardcoding sensitive information and promoting secure practices.
-   **Flexibility**: Allows for easy switching between different operational environments (dev, demo, prod) without code changes.
-   **`HAMMemoryManager`**: Directly relies on the `UnifiedKeyManager` to obtain the encryption key for HAM, ensuring the security of Angela's memories.
-   **External Integrations**: Provides API keys for services like LLMs, Atlassian, and Rovo Dev, enabling secure communication with external platforms.
-   **Testing**: Facilitates testing by providing a controlled way to inject specific keys or simulate different security contexts.

## Code Location

`src/shared/key_manager.py`
