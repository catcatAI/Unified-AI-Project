# DependencyManager: Centralized Dependency Management with Lazy Loading

## Overview

This document provides an overview of the `DependencyManager` module (`src/core_ai/dependency_manager.py`). This module implements a centralized system for managing optional dependencies and their fallback mechanisms within the Unified AI Project.

## Purpose

The primary purpose of the `DependencyManager` is to enhance the robustness and flexibility of the Unified AI Project. It ensures that the system can operate effectively even when some optional dependencies are not available in the current environment. This is achieved by providing graceful degradation through fallback mechanisms and offering a clear, centralized overview of the system's dependency status.

## Key Responsibilities and Features

*   **Centralized Management**: Manages a comprehensive list of core and optional dependencies. These dependencies and their configurations are defined in a dedicated YAML configuration file (`configs/dependency_config.yaml`).
*   **Lazy Loading**: Dependencies are not loaded at startup. Instead, they are only imported dynamically when they are explicitly requested via the `get_dependency()` method. This approach significantly minimizes startup time and reduces overall resource consumption.
*   **Fallback Mechanisms**: Supports the definition of alternative (fallback) modules for primary dependencies. If a primary dependency fails to load or is not available, the manager automatically attempts to load its configured fallback, ensuring continuous functionality.
*   **Environment-Specific Behavior**: The manager can adapt its behavior based on the current operating environment (e.g., `development`, `production`). This allows for different fallback policies or dependency requirements depending on the deployment context.
*   **Dependency Status Tracking**: Internally maintains `DependencyStatus` objects for each dependency. These objects track whether a dependency is successfully loaded, if a fallback is currently in use, or if an error occurred during the loading process.
*   **Status Reporting (`get_dependency_report`)**: Generates a human-readable report that summarizes the availability of all tracked dependencies. This report includes details on which fallbacks are active and the reasons for any unavailable dependencies.
*   **OS-Specific Handling**: Includes specialized logic for certain dependencies (e.g., it may skip direct import attempts for `tensorflow` on Windows to prevent known compatibility issues).

## How it Works

Upon initialization, the `DependencyManager` loads its configuration from `configs/dependency_config.yaml`. It then pre-populates its internal state with `DependencyStatus` objects for all defined dependencies, but it does not attempt to load the actual modules at this stage. When another component of the AI system requests a dependency using `get_dependency()`, the manager first attempts to import the primary module. If this fails, and if fallbacks are permitted in the current environment configuration, it then attempts to load a configured fallback module. The `DependencyStatus` for each module is updated dynamically upon its first request, reflecting its current availability.

## Integration with Other Modules

*   **`configs/dependency_config.yaml`**: This YAML file serves as the primary configuration source, defining all dependencies, their import names, and any associated fallback modules.
*   **`importlib`**: The standard Python library used by the `DependencyManager` for dynamically importing modules at runtime.
*   **`yaml`**: Used for parsing the YAML-formatted configuration file.
*   **System Components**: Any module or component within the Unified AI Project that relies on optional external libraries or services is expected to interact with this `DependencyManager` to safely access those resources, ensuring system stability and adaptability.

## Code Location

`src/core_ai/dependency_manager.py`