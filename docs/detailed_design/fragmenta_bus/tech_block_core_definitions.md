# Tech Block Core Definitions

**Version:** 0.1
**Date:** July 11, 2024
**Parent Plan:** `docs/implementation_guides/Fragmenta_Bus_Implementation_Plan.md`
**Authors:** Jules (AI Agent)

## 1. Introduction

This document provides the detailed design specifications for the core data structures and interfaces related to **Tech Blocks** within the Fragmenta Multi-Bus System. These definitions are foundational for creating and managing individual processing units (Tech Blocks) that form the building blocks of more complex Modules.

## 2. Core Data Structures (`TypedDicts`)

These data structures will be defined in a shared location, likely `src/fragmenta_bus/common/data_models.py` or a similar path.

### 2.1. `TechBlockInput`

Represents the standardized input payload for any Tech Block.

```python
from typing import TypedDict, Any, Optional, Dict

class TechBlockInput(TypedDict):
    """
    Standardized input structure for a Tech Block.
    """
    data: Any  # The primary data payload for the block to process.
               # The specific structure of 'data' is defined by the block's input_schema.
    config: Optional[Dict[str, Any]] # Block-specific configuration overrides for this execution.
                                    # Keys and values should conform to block's expected config.
    # Potentially add other common fields like 'trace_id', 'user_context' if needed globally.
```
*   **`data`**: The main payload. Its specific type and structure will vary per Tech Block and should be validated against the `input_schema` defined in the block's manifest.
*   **`config`**: Optional dictionary for any runtime configuration that might alter the block's behavior for a specific execution (e.g., `{"llm_model": "gpt-4o", "temperature": 0.5}`).

### 2.2. `TechBlockOutput`

Represents the standardized output payload from any Tech Block.

```python
from typing import TypedDict, Any, Optional, Dict, Literal

class TechBlockOutput(TypedDict):
    """
    Standardized output structure for a Tech Block.
    """
    result: Optional[Any] # The primary output data from the block's execution.
                          # Structure defined by the block's output_schema.
                          # Optional because an error might prevent result generation.
    status: Literal["success", "error", "warning"] # Execution status.
    error_message: Optional[str]    # Detailed error message if status is "error".
    warning_messages: Optional[List[str]] # List of warnings if status is "warning" or "success" with caveats.
    metadata: Optional[Dict[str, Any]] # Additional metadata about the execution (e.g., execution_time_ms, tokens_used).
```
*   **`result`**: The primary output. Optional if an error occurs.
*   **`status`**: Indicates successful execution, an error, or success with warnings.
*   **`error_message`**: Provides details if an error occurred.
*   **`warning_messages`**: Provides details for any non-critical issues.
*   **`metadata`**: Can include performance metrics, resource usage, or other execution-specific information.

### 2.3. `TechBlockManifest`

Provides metadata describing a Tech Block. This is crucial for discovery, validation, and orchestration by the bus system.

```python
from typing import TypedDict, List, Dict, Any

class TechBlockManifest(TypedDict):
    """
    Metadata manifest describing a Tech Block.
    Used for registration, discovery, and validation.
    """
    id: str                 # Unique identifier for the Tech Block (e.g., "text.summarization.abstractive_v1")
                            # Format: <domain>.<functionality>.<implementation_details_version>
    name: str               # Human-readable name (e.g., "Abstractive Text Summarizer")
    version: str            # Semantic version of the Tech Block implementation (e.g., "1.0.2")
    description: str        # Brief explanation of what the Tech Block does.

    input_schema: Dict[str, Any]  # JSON Schema definition for the 'data' field of TechBlockInput.
                                  # Used for validation and interface contract.
    output_schema: Dict[str, Any] # JSON Schema definition for the 'result' field of TechBlockOutput.
                                   # Used for validation and interface contract.

    config_schema: Optional[Dict[str, Any]] # JSON Schema for the 'config' field of TechBlockInput.
                                            # Defines acceptable runtime configuration parameters.

    dependencies: Optional[List[str]] # List of other Tech Block IDs or external service IDs this block depends on.
                                      # e.g., ["llm.inference.gpt3.5_turbo", "service.database.user_profiles"]

    resource_requirements: Optional[Dict[str, Any]] # Estimated resource needs.
                                                    # e.g., {"cpu_cores": 1, "ram_mb": 512, "gpu_needed": False, "network_access": True}

    tags: Optional[List[str]] # Keywords for categorization and discovery (e.g., ["nlp", "summarization", "llm"])
    author: Optional[str]
    created_at: Optional[str] # ISO 8601 datetime string
```
*   **`id`**: A namespaced, unique ID.
*   **`input_schema`, `output_schema`, `config_schema`**: JSON Schema objects defining the expected structure and types for inputs, outputs, and runtime configurations. This enables automatic validation and clear interface contracts.
*   **`dependencies`**: Helps the system understand prerequisites.
*   **`resource_requirements`**: Aids the Technical Bus in resource allocation and scheduling.

## 3. `TechBlock` Abstract Base Class (ABC)

This ABC defines the contract that all concrete Tech Block implementations must adhere to. It will likely reside in `src/fragmenta_bus/common/tech_block_interface.py`.

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

# Assuming TechBlockInput, TechBlockOutput, TechBlockManifest are defined as above
# in a shared data_models.py or similar.

class TechBlock(ABC):
    """
    Abstract Base Class for all Tech Blocks.
    Defines the essential interface for execution and metadata retrieval.
    """

    def __init__(self, block_id: str, version: str, config: Optional[Dict[str, Any]] = None):
        """
        Constructor for a TechBlock instance.
        Concrete implementations might take specific configuration at instantiation.

        Args:
            block_id (str): The unique ID of this block instance (might differ from manifest ID if configured).
            version (str): The version of this block instance.
            config (Optional[Dict[str, Any]]): Initial configuration for the block instance.
                                                 This is static config for the instance,
                                                 distinct from runtime config in TechBlockInput.
        """
        self._block_id = block_id
        self._version = version
        self._instance_config = config or {}

    @property
    def id(self) -> str:
        return self._block_id

    @property
    def version(self) -> str:
        return self._version

    @abstractmethod
    async def execute(self, input_data: TechBlockInput, context: Optional[Dict[str, Any]] = None) -> TechBlockOutput:
        """
        Executes the core logic of the Tech Block.
        This method must be implemented by all concrete Tech Block classes.
        It should be designed to be potentially asynchronous if I/O operations are involved.

        Args:
            input_data (TechBlockInput): The standardized input payload.
                                         The 'data' field within should conform to this block's input_schema.
            context (Optional[Dict[str, Any]]): Optional execution context that might be provided by the
                                                calling Bus (e.g., user_id, session_id, access to shared services).

        Returns:
            TechBlockOutput: The standardized output payload, including the result and execution status.
        """
        pass

    @abstractmethod
    def get_manifest(self) -> TechBlockManifest:
        """
        Returns the TechBlockManifest associated with this type of Tech Block.
        The manifest provides metadata about the block's capabilities, inputs, outputs, etc.
        This should typically return a class-level or statically defined manifest.

        Returns:
            TechBlockManifest: The metadata manifest for this Tech Block.
        """
        pass

    # Optional: Helper methods for validation against schemas, common error handling, etc.
    # def _validate_input(self, data: Any) -> bool: ...
    # def _validate_output(self, result: Any) -> bool: ...
```
*   The `__init__` method allows for instance-specific configuration, while `execute` can take further runtime configuration via `TechBlockInput.config`.
*   `execute` is marked `async` to encourage non-blocking design for I/O-bound operations.
*   `get_manifest` is crucial for the Bus system to understand how to use the block.

## 4. Location and Naming Conventions

*   **Core Definitions:** `src/fragmenta_bus/common/data_models.py` (for TypedDicts), `src/fragmenta_bus/common/tech_block_interface.py` (for ABC).
*   **Concrete Tech Blocks:** Could reside in `src/fragmenta_bus/tech_blocks/implementations/` categorized by domain (e.g., `nlp/`, `data_processing/`, `services/`).
    *   Example: `src/fragmenta_bus/tech_blocks/implementations/nlp/summarizer_block.py` containing `SummarizerTechBlock(TechBlock)`.

## 5. Next Steps in Detailed Design

With these core definitions, the next steps would involve designing:
1.  `TechBlockLibrary`: For registering and discovering Tech Blocks.
2.  `TechnicalBusController`: For executing individual Tech Blocks and sequences.
3.  Concrete examples of simple Tech Blocks.

This document provides the foundational types and interfaces upon which the rest of the Tech Block ecosystem and the Bus architecture will be built.
