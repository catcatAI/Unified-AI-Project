# Cleanup Utilities

## Overview

The `cleanup_utils.py` (`src/shared/utils/cleanup_utils.py`) module provides a collection of utility functions designed to **automate the cleanup of various temporary files, cached data, and log files** within the Unified-AI-Project. This module is essential for maintaining a clean development and operational environment, managing storage space, and ensuring that outdated or unnecessary files do not accumulate.

It helps in streamlining maintenance tasks and contributes to the overall health and efficiency of the project.

## Key Functions

1.  **`cleanup_temp_files(project_root: Path = Path("."))`**:
    *   Deletes temporary files and directories matching predefined patterns (e.g., `tmp_*`, `temp_*`, `*.tmp`, `*.pyc`, `__pycache__`, `.pytest_cache`, `*.log`, `.coverage`).
    *   Recursively searches within the specified `project_root` (defaults to the current directory).

2.  **`cleanup_cache_data(retention_days: int, project_root: Path = Path("."))`**:
    *   Removes cached data that is older than a specified number of `retention_days`.
    *   Targets specific cache directories, including `data/atlassian_cache`, `data/fallback_storage`, and `.cache`.
    *   Deletes files based on their last modification time.

3.  **`cleanup_log_files(retention_days: int, project_root: Path = Path("."))`**:
    *   Deletes log files that are older than a specified number of `retention_days`.
    *   Targets common log file patterns (e.g., `logs/*.log`, `*.log`, `logs/*.log.*`).

4.  **`cleanup_demo_artifacts(retention_days: int, storage_path: Path)`**:
    *   Specifically designed to clean up artifacts generated during demonstrations or testing that are older than `retention_days`.
    *   Requires a specific `storage_path` to target the demo artifacts.

## How it Works

Each cleanup function iterates through files and directories within specified paths or matching defined patterns. It checks the modification timestamp of files against a calculated `cutoff_date` (based on `retention_days`). If a file or directory is older than the cutoff, it is removed. The functions include logging to indicate which files are being deleted and warning messages for any errors encountered during the cleanup process.

## Integration and Importance

-   **Automated Maintenance**: These utilities can be integrated into CI/CD pipelines, scheduled cron jobs, or pre-commit hooks to ensure regular cleanup.
-   **Resource Management**: Prevents disk space exhaustion by removing unnecessary files.
-   **Development Workflow**: Keeps development environments clean and reduces clutter, improving developer productivity.
-   **Data Hygiene**: Helps in maintaining data hygiene by removing outdated or temporary data.

## Code Location

`src/shared/utils/cleanup_utils.py`
