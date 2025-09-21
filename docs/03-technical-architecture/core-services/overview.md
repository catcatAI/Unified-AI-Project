# Core Services Overview

This document provides an overview of the core services within the Unified-AI-Project. The central initialization and management logic for these services is primarily handled by `apps/backend/src/core_ai/genesis.py` and orchestrated through `apps/backend/src/services/main_api_server.py`.

## 1. Purpose and Role

This module is designed to:

- **Centralize Initialization:** Provide a single entry point
  (`initialize_services()`) for setting up all core AI components and their
  dependencies.
- **Manage Singletons:** Maintain global singleton instances of key services,
  ensuring that different parts of the application access the same, consistent
  service objects.
- **Orchestrate Dependencies:** Handle the complex interdependencies between
  various AI modules and foundational services.
- **Facilitate Access:** Offer a convenient way (`get_services()`) to retrieve
  initialized service instances.
- **Ensure Graceful Shutdown:** Provide a mechanism (`shutdown_services()`) for
  orderly termination of services.

## 2. Key Functions

### `initialize_services(

    ai_id: str = DEFAULT_AI_ID,
    hsp_broker_address: str = DEFAULT_MQTT_BROKER,
    hsp_broker_port: int = DEFAULT_MQTT_PORT,
    llm_config: Optional[LLMInterfaceConfig] = None,
    operational_configs: Optional[Dict[str, Any]] = None,
    use_mock_ham: bool = False

)`

This is the primary function called at application startup. It performs the
following steps:

1.  **Configuration Handling:** Merges default operational and LLM
    configurations with any provided custom configurations.
2.  **Foundational Services Initialization:** Initializes core components that
    other modules depend on:
    - `LLMInterface`: Manages interactions with Large Language Models.
    - `HAMMemoryManager`: Handles Hierarchical Abstract Memory operations.
    - `PersonalityManager`: Manages AI personality profiles.
    - `TrustManager`: Manages trust scores for various entities.
    - `MCPConnector`: Facilitates communication with the Message Communication
      Protocol.
    - _(Note: Includes logic for a `TempMockHAM` for testing/CLI convenience.)_
3.  **HSP Related Services Initialization:** Sets up components for Human-System
    Protocol (HSP) communication:
    - `HSPConnector`: Manages connections and message exchange over HSP.
    - **Location:** `apps/backend/src/hsp/connector.py`
    - `ServiceDiscoveryModule`: Discovers and manages available capabilities
      within the HSP network.
    - _(Registers callbacks for capability advertisements and fact processing.)_
4.  **Core AI Logic Modules Initialization:** Initializes the main AI
    functionalities, often injecting previously initialized foundational
    services:
    - `FactExtractorModule`: Extracts facts from content.
    - `ContentAnalyzerModule`: Analyzes content (e.g., using spaCy).
    - `LearningManager`: Manages the AI's learning processes.
    - `EmotionSystem`: Handles AI emotional responses.
    - `CrisisSystem`: Manages crisis detection and response.
    - `TimeSystem`: Provides time-related functionalities.
    - `FormulaEngine`: Executes predefined formulas.
    - `ToolDispatcher`: Dispatches and manages AI tools.
    - `AgentManager`: Manages the lifecycle of various AI agents.
    - **`apps/backend/src/core_ai/dialogue/dialogue_manager.py`**: The `DialogueManager` is the
  first point of contact for user queries. It identifies complex project
  requests and delegates them to the `ProjectCoordinator`. For simpler queries,
  it can provide a direct response.

### `get_services() -> Dict[str, Any]`

Returns a dictionary containing all the initialized service instances. This
allows other parts of the application to easily access the singleton instances
without re-initializing them.

### `shutdown_services()`

Performs a graceful shutdown of active services, specifically:

- Shuts down all active agents managed by `AgentManager`.
- Disconnects the `HSPConnector` if it's connected.

## 3. Architecture and Dependencies

`core_services.py` acts as a central dependency injector. Modules are
initialized in a specific order to ensure their dependencies are met. For
example, `LearningManager` depends on `HAMMemoryManager`, `FactExtractorModule`,
`PersonalityManager`, etc., which are initialized beforehand.

## 4. Configuration

Default configurations for AI ID, MQTT broker, operational parameters, and LLM
settings are defined within this module. These can be overridden by passing
custom configurations to `initialize_services()`, allowing for flexible
deployment and testing scenarios.

## 5. Usage Example

```python
import core_services

# Initialize all services
core_services.initialize_services(ai_id="my_custom_ai", use_mock_ham=True)

# Get access to specific services
llm_interface = core_services.get_services()["llm_interface"]
dialogue_manager = core_services.get_services()["dialogue_manager"]

# Use the services
# response = dialogue_manager.process_user_input("Hello!")

# Shut down services when done
core_services.shutdown_services()
```
