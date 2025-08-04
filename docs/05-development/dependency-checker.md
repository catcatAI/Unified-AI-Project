# Dependency Checker

## Overview

The `dependency_checker.py` (`src/tools/dependency_checker.py`) is a utility script designed to **verify the installation and availability of project dependencies**. It reads a predefined list of core and optional dependencies from a configuration file (`dependency_config.yaml`) and attempts to import each package to confirm its presence and functionality.

This tool is crucial for developers to quickly diagnose environment setup issues, ensure consistent development environments, and confirm that all necessary components for the AI system are correctly installed.

## Key Responsibilities and Features

1.  **Dependency Verification**: 
    *   Checks both `core` and `optional` dependencies defined in `dependency_config.yaml`.
    *   Attempts to `import` each specified package to confirm its availability in the current Python environment.

2.  **Configuration-Driven**: 
    *   The list of dependencies, their import names, and optional installation details are loaded from an external YAML configuration file.
    *   This allows for easy updates to dependency requirements without modifying the script itself.

3.  **Installation Command Generation**: 
    *   For any missing dependencies, the script generates a `pip install` command, simplifying the process of installing prerequisites.

4.  **Human-Readable Status Report**: 
    *   Prints a clear, color-coded (conceptually) report indicating the status (✓ available, ✗ missing) of each dependency.
    *   Includes error messages if an import fails and suggests installation commands.

5.  **Integration with Live `DependencyManager`**: 
    *   If the `DependencyManager` (from `src/core_ai/dependency_manager.py`) is available, the script also prints a report from the live manager, providing a dynamic view of dependency status.

## How it Works

The script loads the `dependency_config.yaml` file. It then iterates through the defined core and optional dependencies. For each dependency, it calls `check_package` which attempts to import the corresponding Python package. If the import fails, it records the error. Finally, it compiles and prints a summary report to the console, guiding the user on how to resolve any missing dependencies.

## Integration and Importance

-   **Developer Onboarding**: Simplifies the setup process for new developers by providing a quick way to validate their environment.
-   **CI/CD Pipelines**: Can be integrated into continuous integration pipelines to ensure that build and test environments have all required dependencies.
-   **Troubleshooting**: Helps in diagnosing runtime errors related to missing packages.
-   **System Health**: Contributes to the overall health monitoring of the AI system by verifying the availability of its foundational components.

## Code Location

`src/tools/dependency_checker.py`
