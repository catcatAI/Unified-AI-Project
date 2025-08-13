# ResourceAwarenessService: Simulated Hardware Resource Awareness

## Overview

This document provides an overview of the `ResourceAwarenessService` module (`src/services/resource_awareness_service.py`). Its primary function is to manage and provide access to the AI's simulated hardware resource profile.

This module is crucial for enabling the AI to be "aware" of its operational environment's resource constraints and capabilities (CPU, RAM, disk, GPU). This awareness is vital for intelligent resource management, adaptive task scheduling, and optimizing AI behavior for specific hardware configurations, especially in simulated or resource-limited deployments.

## Key Responsibilities and Features

*   **Configuration Loading (`_load_profile`)**: Loads the simulated hardware profile from a YAML configuration file (defaulting to `configs/simulated_resources.yaml`). It includes robust error handling for file not found, malformed YAML, or missing required keys, ensuring a fallback to a safe default profile if any issues occur during loading.
*   **Simulated Hardware Profile (`SimulatedHardwareProfile`)**: Represents the comprehensive hardware profile. This includes a `profile_name` and detailed configurations for `disk` (`SimulatedDiskConfig`), `cpu` (`SimulatedCPUConfig`), and `ram` (`SimulatedRAMConfig`), as well as a boolean indicating `gpu_available`. These configurations are defined as TypedDicts in `services.types`.
*   **Specific Configuration Accessors**: Provides dedicated methods to retrieve specific parts of the simulated hardware profile:
    *   `get_simulated_hardware_profile()`: Returns the entire loaded profile.
    *   `get_simulated_disk_config()`: Returns the disk-specific configuration.
    *   `get_simulated_cpu_config()`: Returns the CPU-specific configuration.
    *   `get_simulated_ram_config()`: Returns the RAM-specific configuration.
*   **Safe Default Profile (`_get_safe_default_profile`)**: Implements a minimal, safe default hardware profile. This ensures that the service can always return a valid (though basic) configuration, preventing crashes even if the primary configuration file is absent or corrupted.

## How it Works

The `ResourceAwarenessService` initializes by attempting to load a simulated hardware profile from a specified YAML file. This file describes the characteristics of the AI's operational environment. Once loaded, the service stores this configuration internally. Other modules within the AI system can then query this service to obtain detailed information about the available resources. This allows the AI to make informed, resource-aware decisions, such as dynamically adjusting model sizes, optimizing processing loads, prioritizing tasks, or selecting appropriate algorithms based on the perceived hardware capabilities.

## Integration with Other Modules

*   **`services.types`**: Defines the TypedDicts (`SimulatedHardwareProfile`, `SimulatedDiskConfig`, `SimulatedCPUConfig`, `SimulatedRAMConfig`, `SimulatedResourcesRoot`) that structure the simulated hardware configuration data.
*   **`yaml`**: The external library used for parsing the YAML configuration files.
*   **`ExecutionManager`**: Could utilize the information from this service to inform its resource monitoring, adaptive timeout logic, and potentially resource allocation decisions.
*   **`MultiLLMService`**: Might use the reported GPU availability or RAM/CPU configurations to select LLM models that are best suited for the available hardware resources.
*   **`ProjectCoordinator`**: Could leverage resource awareness for more efficient task scheduling and distribution across different deployment environments.

## Code Location

`src/services/resource_awareness_service.py`