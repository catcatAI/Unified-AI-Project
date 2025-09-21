# ConfigLoader: Centralized Application Configuration Management

## Overview

This document provides an overview of the `config_loader.py` module (`src/config_loader.py`). This module offers centralized functions for loading and accessing application configuration and simulated resource settings from YAML files.

## Purpose

The `config_loader` module is designed to manage application-wide configurations and simulated environment settings. Its primary purpose is to ensure that all modules within the Unified-AI-Project can access consistent configuration data, promoting maintainability, ease of deployment, and adaptability. It also supports a "demo mode" based on specific configuration flags.

## Key Responsibilities and Features

*   **Main Configuration Loading (`load_config`, `get_config`)**:
    *   Loads the primary application configuration from `configs/config.yaml`.
    *   Employs a singleton pattern (using the `_config` global variable) to ensure that the configuration is loaded only once during the application's lifetime, providing efficient and consistent access.
*   **Simulated Resources Loading (`load_simulated_resources`, `get_simulated_resources`)**:
    *   Loads simulated hardware and environment settings from `configs/simulated_resources.yaml`.
    *   Also uses a singleton pattern (via `_simulated_resources`) for optimized access to these settings.
*   **Demo Mode Detection (`is_demo_mode`)**: Provides a utility function to quickly check if the application is configured to run in a demo mode. This is determined by the `use_simulated_resources` flag within the main configuration.
*   **Mock Placeholder Value Retrieval (`get_mock_placeholder_value`)**: Offers a convenient way to retrieve specific mock values from the simulated resources configuration. This is particularly useful for testing, development, or demonstration purposes where real external services might not be available.

## How it Works

The `config_loader` module uses global variables (`_config` and `_simulated_resources`) to store the loaded configurations as singletons. When `load_config` or `load_simulated_resources` is called for the first time, it reads the respective YAML file, parses its content, and stores the data in the corresponding global variable. Subsequent calls to `get_config` or `get_simulated_resources` simply return the already loaded data, avoiding redundant file I/O and parsing.

## Integration with Other Modules

*   **`PyYAML`**: The external library used for parsing the YAML configuration files.
*   **`core_services`**: This module will likely use `load_config` during its initialization phase to retrieve essential application settings.
*   **`ResourceAwarenessService`**: Could potentially use `get_simulated_resources` to obtain its initial simulated hardware profile.
*   **Any Module Requiring Configuration**: Any module within the Unified-AI-Project that needs to access application settings, check for demo mode, or retrieve mock data will interact with this `config_loader` module.

## Code Location

`src/config_loader.py`