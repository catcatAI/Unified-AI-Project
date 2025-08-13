# DemoLearningManager: Automated Learning and Cleanup for Demo Mode

## Overview

This document provides an overview of the `DemoLearningManager` module (`src/core_ai/demo_learning_manager.py`). This module is designed to automatically manage learning, initialization, and cleanup functions when specific demo keys or conditions are detected.

## Purpose

The `DemoLearningManager` provides a specialized and controlled environment for demonstration and testing purposes. Its core purpose is to enable the system to automatically collect valuable learning data, set up mock services for isolated testing, and perform necessary cleanup operations when operating in a demo mode. This ensures a consistent, clean, and efficient environment for demonstrations and rapid iteration during development or showcasing.

## Key Responsibilities and Features

*   **Demo Credential Detection (`detect_demo_credentials`)**: Identifies if provided API keys or other credentials match predefined demo patterns configured in `configs/demo_credentials.yaml`. This is the trigger for activating demo mode.
*   **Demo Mode Activation (`activate_demo_mode`)**:
    *   Sets the internal `demo_mode` flag to `True`.
    *   Orchestrates the execution of a series of configurable actions, which can include `enable_demo_mode` (creating a flag file), `initialize_learning` (setting up data structures and monitoring), `setup_mock_services` (creating mock service configurations), and `configure_auto_cleanup` (scheduling cleanup tasks).
*   **Learning Data Collection (`_collect_learning_data`, `record_user_interaction`, `record_error_pattern`)**:
    *   **System Metrics**: Periodically collects system performance metrics such as memory usage, storage usage, and active connections.
    *   **User Interactions**: Records detailed user interactions, including the action performed, context, result, and any user feedback.
    *   **Error Patterns**: Tracks and aggregates error occurrences, noting their type, message, context, resolution, and frequency.
    *   All collected data is persistently stored in `learning_data.json` within the configured storage path.
*   **Learning Insights (`get_learning_insights`)**: Analyzes the rich collected data to provide actionable insights into user interaction patterns, common error frequencies, and performance trends. It also generates proactive recommendations based on these insights to improve system stability and user experience.
*   **Automatic Cleanup (`_configure_auto_cleanup`, `_perform_cleanup`)**: Configures and executes automatic cleanup operations for temporary files, cache data, log files, and demo-specific artifacts. Cleanup policies, including retention periods, are configurable.
*   **Mock Service Setup (`_setup_mock_services`)**: Facilitates isolated testing by creating a configuration file for mock services when the system is operating in demo mode.
*   **Shutdown (`shutdown`)**: Upon system shutdown, it performs final cleanup operations (if configured) and generates a comprehensive learning report summarizing the demo session's insights.

## How it Works

Upon initialization, the `DemoLearningManager` loads its configuration from `configs/demo_credentials.yaml`. When `detect_demo_credentials` identifies a demo key, the `activate_demo_mode` method is triggered. This method then orchestrates the various learning and cleanup tasks, often running background monitoring loops for continuous data collection and scheduled cleanup. The collected data is analyzed to provide insights, and cleanup ensures the demo environment remains pristine.

## Integration with Other Modules

*   **`src.shared.utils.cleanup_utils`**: Leverages utility functions from this module for performing various cleanup operations.
*   **`psutil`**: Used for collecting system performance metrics, specifically memory usage.
*   **`yaml` and `json`**: Utilized for loading configuration from YAML files and for saving/loading learning data in JSON format.

## Code Location

`src/core_ai/demo_learning_manager.py`