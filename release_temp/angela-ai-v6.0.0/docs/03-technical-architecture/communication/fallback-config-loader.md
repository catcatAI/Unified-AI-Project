# HSP Fallback Protocol Configuration Loader

## Overview

This document provides an overview of the `FallbackConfigLoader` module, defined in `src/hsp/utils/fallback_config_loader.py`. This module is responsible for loading, managing, and validating configuration settings for the Heterogeneous Service Protocol (HSP) fallback communication system.

## Purpose

The primary purpose of the `FallbackConfigLoader` is to provide a robust and centralized mechanism for configuring the behavior of the AI's resilient communication. It allows developers to define fallback protocol settings (like priorities, host/port, file paths, and logging levels) through external YAML files, while also providing sensible default values. This ensures that the fallback system is always operational with valid settings, even if custom configuration files are missing or malformed.

## Key Responsibilities and Features

*   **Default Configuration (`DEFAULT_CONFIG`)**: Contains a comprehensive set of default configuration parameters for all supported fallback protocols (HTTP, File, Memory) and primary HSP (MQTT) communication. This ensures the system can run out-of-the-box.
*   **Flexible Configuration Loading (`load_config`)**: Automatically searches for a configuration file (e.g., `hsp_fallback_config.yaml`) in predefined locations. If found, it loads the file and merges its settings with the `DEFAULT_CONFIG`, allowing custom settings to override defaults. If no file is found or an error occurs, it gracefully falls back to using only the default configuration.
*   **Recursive Configuration Merging (`_merge_configs`)**: A private helper method that intelligently merges nested dictionary structures from the default and override configurations, ensuring that all settings are correctly applied.
*   **Configuration Accessors**: Provides a suite of public methods (e.g., `get_fallback_config()`, `get_hsp_config()`, `get_protocol_config()`, `get_message_config()`, `get_logging_config()`) that allow other modules to easily retrieve specific subsets of the loaded configuration.
*   **Configuration Validation (`validate_config`)**: Offers a method to programmatically check the loaded configuration for validity. It ensures that critical settings (like protocol priorities and enabled flags) are of the correct data type and within expected ranges, logging errors for any invalid entries.
*   **Configuration Saving (`save_config`)**: Allows the current configuration (or a provided configuration) to be saved to a YAML file, facilitating persistent changes and easy sharing of settings.

## How it Works

Typically, a single instance of `FallbackConfigLoader` is created at application startup. When its `load_config()` method is called, it attempts to locate and parse a YAML configuration file. If successful, it merges these settings with its internal `DEFAULT_CONFIG`. Otherwise, it proceeds with only the defaults. Other modules then query this loader instance using its getter methods to retrieve the specific configuration parameters they need to operate. The `validate_config` method can be used to perform a sanity check on the configuration before it is put into use.

## Integration with Other Modules

*   **`FallbackProtocolManager` and `BaseFallbackProtocol` Implementations**: These modules are the primary consumers of the configuration provided by this loader, using it to set up their communication parameters and behavior.
*   **PyYAML Library**: The module uses the `yaml` library for parsing and serializing YAML configuration files.

## Code Location

`apps/backend/src/hsp/utils/fallback_config_loader.py`