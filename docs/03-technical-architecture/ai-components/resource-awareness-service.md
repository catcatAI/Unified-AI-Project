# Resource Awareness Service

## Overview

The `ResourceAwarenessService` (`src/services/resource_awareness_service.py`) is a crucial component within the Unified-AI-Project that provides the AI (Angela) with an **understanding of its simulated hardware resources**. This service allows the AI to make informed decisions based on its operational environment, such as optimizing task execution, managing memory usage, or adapting its behavior when resources are constrained.

This module is essential for enabling the AI to operate efficiently and robustly within defined computational limits, and for simulating realistic resource-dependent behaviors.

## Key Responsibilities and Features

1.  **Simulated Hardware Profile Loading**: 
    *   Loads a detailed simulated hardware profile from a YAML configuration file (defaulting to `configs/simulated_resources.yaml`).
    *   The profile includes configurations for `disk` (space, warning/critical thresholds, lag factors), `cpu` (number of cores), `ram` (total GB), and `gpu_available` status.

2.  **Robust Configuration Handling**: 
    *   Gracefully handles scenarios where the configuration file is not found or is malformed.
    *   Automatically falls back to a safe, minimal default profile if loading fails, ensuring the service remains operational.

3.  **Resource Information Retrieval**: 
    *   Provides methods to retrieve the entire `SimulatedHardwareProfile` or specific components like `SimulatedDiskConfig`, `SimulatedCPUConfig`, and `SimulatedRAMConfig`.

## How it Works

The `ResourceAwarenessService` initializes by attempting to load a simulated hardware profile from a specified YAML file. It parses this file and stores the configuration internally. If any issues arise during loading (e.g., file not found, invalid format), it defaults to a predefined safe profile. Other AI modules can then query this service to understand the AI's current resource constraints, allowing them to adjust their operations accordingly.

## Integration with Other Modules

-   **`ProjectCoordinator`**: Could use resource awareness to optimize task scheduling and resource allocation for complex projects, ensuring that tasks are assigned to agents with sufficient simulated resources.
-   **`HAMMemoryManager`**: Might use disk space information to manage memory persistence strategies, potentially offloading less critical data if disk space is low.
-   **`MultiLLMService`**: Could adapt its model selection or generation parameters based on available CPU/GPU resources, choosing smaller or less computationally intensive models when resources are limited.
-   **`ExecutionMonitor`**: Could integrate with this service to provide more realistic monitoring of simulated resource usage during task execution.

## Code Location

`src/services/resource_awareness_service.py`
