# Environment Setup Utilities

## Overview

The `env_utils.py` (`src/shared/utils/env_utils.py`) module provides essential utility functions for **managing environment variable files** within the Unified-AI-Project. Its primary purpose is to streamline the setup and configuration of development and deployment environments, ensuring that necessary API keys and settings are correctly handled.

This module is crucial for maintaining consistent and secure environment configurations across different development machines and deployment targets.

## Key Functions

1.  **`setup_env_file(project_root: Path = Path("."), env_example_name: str = ".env.example", env_name: str = ".env") -> bool`**:
    *   Checks for the existence of the `.env` file in the specified `project_root`.
    *   If `.env` does not exist, it copies the content from a provided `env_example_name` (defaulting to `.env.example`) to create the `.env` file.
    *   Logs informative messages about the process, including warnings if the `.env` file needs manual editing for API keys.
    *   Returns `True` if the `.env` file already exists or was successfully created, `False` otherwise.

2.  **`add_env_variable(key: str, value: str, project_root: Path = Path("."), env_name: str = ".env") -> bool`**:
    *   Adds or updates a specific environment variable (`key=value`) within the `.env` file.
    *   If the key already exists, its value is updated; otherwise, the new key-value pair is appended to the file.
    *   Ensures that the `.env` file exists before attempting to modify it.
    *   Returns `True` on successful addition/update, `False` on failure.

## How it Works

The `setup_env_file` function is typically called during the initial project setup. It automates the creation of the `.env` file, which is commonly used to store sensitive information (like API keys) that should not be committed to version control. The `add_env_variable` function provides programmatic control over the `.env` file, allowing scripts or automated processes to update specific environment variables without manual intervention.

## Integration and Importance

-   **Project Setup Scripts**: Directly used by project setup scripts (e.g., `setup_env.sh`, `setup_env.bat`) to ensure that the `.env` file is correctly initialized.
-   **Configuration Management**: Works in conjunction with `config_loader.py` and `key_manager.py` to provide a comprehensive solution for managing application configurations and secrets.
-   **Developer Experience**: Simplifies the onboarding process for new developers by automating a common setup step.
-   **Security Best Practices**: Encourages the use of `.env` files for sensitive data, aligning with security best practices by keeping credentials out of source control.

## Code Location

`src/shared/utils/env_utils.py`
