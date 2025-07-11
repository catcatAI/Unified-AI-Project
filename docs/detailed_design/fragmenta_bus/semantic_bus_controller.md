# Semantic Bus Controller: Detailed Design

**Version:** 0.1
**Date:** July 11, 2024
**Parent Plan:** `docs/implementation_guides/Fragmenta_Bus_Implementation_Plan.md`
**Depends on:**
*   `docs/detailed_design/fragmenta_bus/tech_block_core_definitions.md`
*   `docs/detailed_design/fragmenta_bus/technical_bus_controller_and_library.md`
*   `docs/detailed_design/fragmenta_bus/module_bus_and_blueprints.md`
**Authors:** Jules (AI Agent)

## 1. Introduction

This document provides the detailed design for the `SemanticBusController`. This is the highest-level controller in the Fragmenta Multi-Bus System. It acts as the primary interface for external systems (like the `DialogueManager` or other task dispatchers) to request complex AI functionalities. The `SemanticBusController` interprets these requests, selects appropriate Modules (via their blueprints), orchestrates their execution using the `ModuleBusController`, manages overarching context, and synthesizes the final results.

## 2. Core Responsibilities

1.  **Request Interpretation:** Receive high-level semantic requests (e.g., from user queries, system events) and interpret them to understand the underlying intent and required capabilities.
2.  **Blueprint Selection/Strategy Planning:** Based on the interpreted intent, select one or more `ModuleBlueprint`(s) that can fulfill the request. This may involve a simple mapping or more complex planning if multiple modules need to be chained or coordinated.
3.  **Context Management:** Gather and prepare the necessary context for the selected Module(s). This includes user context, session context, relevant data from `ContextCore` (if available), and overall narrative state.
4.  **Module Invocation:** Use the `ModuleBusController` to execute the chosen Module(s) with the prepared input data and context.
5.  **Result Synthesis & Formatting:** Process the output from the `ModuleBusController` and format it into a final response suitable for the original requester.
6.  **Error Handling & Fallbacks:** Manage errors gracefully during the entire process, potentially invoking fallback strategies or modules.

## 3. `SemanticBusController` Detailed Design

**Proposed Filepath:** `src/fragmenta_bus/semantic_bus/controller.py`

### 3.1. Helper Component: `IntentToBlueprintMapper` (Conceptual)

The `SemanticBusController` will likely need a helper component to map intents to `ModuleBlueprint` IDs. This could be:
*   A simple dictionary/registry.
*   A rule-based system.
*   A small ML model (e.g., a classifier trained on intents and corresponding blueprint IDs).
*   A more sophisticated planning component that can generate sequences of blueprints.

**Proposed Filepath for Mapper (if separate):** `src/fragmenta_bus/semantic_bus/intent_mapper.py`

```python
# Conceptual: src/fragmenta_bus/semantic_bus/intent_mapper.py
from typing import Dict, Any, Optional, List, TypedDict

class IntentMappingRule(TypedDict):
    intent_pattern: str # Could be regex, keyword list, or more complex structure
    blueprint_id: str   # Single blueprint
    # Or, for more complex strategies:
    # blueprint_sequence: List[str]
    # required_context_fields: List[str]
    priority: Optional[int]

class IntentToBlueprintMapper:
    _mappings: List[IntentMappingRule] # Loaded from config

    def __init__(self, mapping_rules: List[IntentMappingRule]):
        self._mappings = sorted(mapping_rules, key=lambda r: r.get("priority", 0), reverse=True)

    def map_intent(self, intent: str, available_blueprints: List[str]) -> Optional[str]: # Returns single blueprint_id for now
        """
        Maps an intent string to a ModuleBlueprint ID.
        Simple example: exact match or first regex match.
        """
        # This is a very basic placeholder logic
        for rule in self._mappings:
            # A real implementation would use more robust pattern matching
            if rule["intent_pattern"].lower() in intent.lower():
                if rule["blueprint_id"] in available_blueprints:
                    return rule["blueprint_id"]
        return None
```

### 3.2. Class Definition: `SemanticBusController`

```python
from typing import Dict, Any, Optional, List, TypedDict, Union
# Assuming common types are correctly imported
from ...common.data_models import (
    SemanticTaskRequest, SemanticTaskResponse, TechBlockOutput, UserContext # UserContext needs definition
)
from ..module_bus.controller import ModuleBusController, ModuleExecutionError, ModuleAssemblyError
# from .intent_mapper import IntentToBlueprintMapper # If implemented

# Define UserContext if not already defined elsewhere
class UserContext(TypedDict, total=False):
    user_id: Required[str]
    session_id: Optional[str]
    persona_id: Optional[str] # Current AI persona
    preferences: Optional[Dict[str, Any]]
    # ... other relevant user/session state from DialogueManager or ContextCore

class SemanticBusController:
    _module_bus: ModuleBusController
    _intent_mapper: Any # IntentToBlueprintMapper or similar logic
    # _context_core_client: Optional[ContextCoreManager] # If ContextCore is available

    def __init__(self, module_bus: ModuleBusController, intent_mappings_config: Optional[List[Dict]] = None): #, context_core_client=None):
        self._module_bus = module_bus
        # self._context_core_client = context_core_client

        # Initialize intent mapper (example)
        if intent_mappings_config:
            # self._intent_mapper = IntentToBlueprintMapper(intent_mappings_config)
            self._intent_mapper_config = intent_mappings_config # Store config for now
            print("Intent mapper configured (conceptual).")
        else:
            # self._intent_mapper = IntentToBlueprintMapper([]) # Default empty mapper
            self._intent_mapper_config = []
            print("Intent mapper initialized with no rules (conceptual).")


    def _determine_blueprint_id_for_request(self, request: SemanticTaskRequest) -> Optional[str]:
        """
        Determines which ModuleBlueprint to use based on the request's intent.
        Placeholder for more sophisticated logic, possibly using IntentToBlueprintMapper.
        """
        intent = request.get("intent")
        if not intent:
            # Fallback or error if intent is missing
            # For now, try to find a generic blueprint if one is registered with a known ID.
            # This is highly dependent on how blueprints are named and registered.
            if self._module_bus.get_blueprint("generic_query_handler_v1"):
                 return "generic_query_handler_v1"
            return None

        # Conceptual use of a mapper
        # available_bps = [bp['id'] for bp in self._module_bus._blueprint_registry.values()] # Accessing protected for example
        # selected_bp_id = self._intent_mapper.map_intent(intent, available_bps)
        # return selected_bp_id

        # Simple hardcoded example for now:
        if "summarize" in intent.lower():
            if self._module_bus.get_blueprint("document_processing.summarize_text_v1"):
                return "document_processing.summarize_text_v1"
        elif "translate" in intent.lower():
            if self._module_bus.get_blueprint("translation.translate_text_v1"):
                 return "translation.translate_text_v1"

        # Fallback to a generic handler if specific intent not mapped
        if self._module_bus.get_blueprint("generic_query_handler_v1"):
            return "generic_query_handler_v1"

        return None


    async def process_semantic_request(
        self,
        request: SemanticTaskRequest,
        user_context: UserContext
    ) -> SemanticTaskResponse:
        """
        Main entry point to process a high-level semantic request.
        """
        blueprint_id = self._determine_blueprint_id_for_request(request)

        if not blueprint_id:
            return SemanticTaskResponse(
                task_id=request["task_id"],
                status="error",
                error_message=f"Could not determine appropriate module blueprint for intent: {request.get('intent')}",
                result=None
            )

        # Prepare initial input data for the module
        # This might involve fetching additional data from ContextCore based on user_context and request.data
        module_initial_input_data = request.get("data")

        # Prepare module execution context (can include parts of user_context or task-specific info)
        module_execution_context = {
            "user_id": user_context.get("user_id"),
            "session_id": user_context.get("session_id"),
            "current_persona_id": user_context.get("persona_id"),
            # Potentially add access to a ContextCore client/interface here
            # "context_core": self._context_core_client
        }

        try:
            # Invoke the module via ModuleBus
            module_output: TechBlockOutput = await self._module_bus.invoke_module(
                blueprint_id=blueprint_id,
                initial_module_input_data=module_initial_input_data,
                module_execution_context=module_execution_context,
                instance_id_prefix=f"{request['task_id']}_{blueprint_id}"
            )

            # Synthesize the final response
            if module_output["status"] == "success":
                return SemanticTaskResponse(
                    task_id=request["task_id"],
                    status="success",
                    result=module_output.get("result"), # The module's final output
                    metadata=module_output.get("metadata")
                )
            else:
                return SemanticTaskResponse(
                    task_id=request["task_id"],
                    status="error",
                    error_message=module_output.get("error_message", "Module execution failed."),
                    result=None,
                    metadata=module_output.get("metadata")
                )

        except ModuleAssemblyError as e:
            return SemanticTaskResponse(task_id=request["task_id"], status="error", error_message=f"Module assembly error: {e}", result=None)
        except ModuleExecutionError as e: # Should be caught by invoke_module ideally, but as a fallback
            return SemanticTaskResponse(task_id=request["task_id"], status="error", error_message=f"Module execution error: {e}", result=None)
        except Exception as e:
            # Log actual exception e with traceback
            error_type = type(e).__name__
            return SemanticTaskResponse(
                task_id=request["task_id"],
                status="error",
                error_message=f"Unexpected error in SemanticBus: {error_type} - {str(e)}",
                result=None
            )

```
*   The `SemanticTaskRequest` and `SemanticTaskResponse` would also be defined in `common.data_models.py`.

### 3.3. Data Structures (already in `common.data_models.py` or new)

```python
# Potentially in src/fragmenta_bus/common/data_models.py

class SemanticTaskRequest(TypedDict):
    task_id: str                # Unique ID for this request
    intent: str                 # High-level intent (e.g., "summarize_document", "answer_question_about_topic_X")
    data: Any                   # Primary input data for the task (e.g., document content, question text)
    user_id: str                # ID of the user making the request
    session_id: Optional[str]   # Current session ID
    # priority: Optional[int]   # Task priority
    # required_capabilities: Optional[List[str]] # May help in blueprint selection
    # response_format_preferences: Optional[Dict]

class SemanticTaskResponse(TypedDict):
    task_id: str
    status: Literal["success", "error", "partial_success"]
    result: Optional[Any]       # The final synthesized result for the requester
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]] # e.g., blueprints_used, confidence_score
```

### 3.4. Core Logic

1.  **Receive Request:** `process_semantic_request` gets a `SemanticTaskRequest` and `UserContext`.
2.  **Intent Mapping (`_determine_blueprint_id_for_request`):**
    *   Analyzes `request.intent` (and potentially `request.data` structure or `request.required_capabilities`).
    *   Uses the `IntentToBlueprintMapper` (or similar logic) to select the most appropriate `ModuleBlueprint` ID (or a sequence/strategy of blueprints).
    *   This is a critical step and might involve sophisticated NLP or planning if not a simple map.
3.  **Context Preparation:**
    *   Gathers necessary information from `UserContext` (e.g., user ID, preferences).
    *   (Future) Queries `ContextCore` for relevant long-term context, historical data, or knowledge needed for the selected blueprint(s).
    *   Constructs `module_initial_input_data` and `module_execution_context` for the `ModuleBusController.invoke_module` call.
4.  **Module Invocation:** Calls `ModuleBusController.invoke_module` with the selected `blueprint_id` and prepared inputs/context.
5.  **Result Processing:**
    *   Receives `TechBlockOutput`-like response from the `ModuleBusController`.
    *   If successful, extracts the `result` and formats it into `SemanticTaskResponse`.
    *   If error, populates `error_message` in `SemanticTaskResponse`.
    *   May add its own metadata (e.g., which blueprint was used).

## 4. Configuration

*   **Intent-to-Blueprint Mappings:** Configuration files (e.g., YAML) defining rules or mappings for the `IntentToBlueprintMapper`. Likely in `configs/fragmenta_bus/semantic_bus_mappings/`.
    *   Example `intent_mappings.yaml`:
        ```yaml
        mappings:
          - intent_pattern: "summarize"
            blueprint_id: "document_processing.summarize_text_v1"
            priority: 10
          - intent_pattern: "translate_to_french"
            blueprint_id: "translation.translate_text_v1"
            # This blueprint might need initial_input_data like: {"text": "...", "target_language": "fr"}
            priority: 10
          - intent_pattern: ".*" # Fallback
            blueprint_id: "generic_query_handler_v1"
            priority: 0
        ```
*   The `SemanticBusController` would be initialized with a `ModuleBusController` instance and the path to these mapping configurations.

## 5. Integration

*   **`DialogueManager`:** Will be the primary client. It will translate user utterances into `SemanticTaskRequest`s and call `SemanticBusController.process_semantic_request()`. It will then process the `SemanticTaskResponse` to formulate the final reply to the user.
*   **Other System Services:** Any other part of the Unified-AI-Project that needs to perform complex, multi-step AI tasks would also interface with the Semantic Bus.
*   **`ContextCore`:** Essential for providing deep context to the Semantic Bus for blueprint selection and for modules during their execution. The `SemanticBusController` would likely hold a client reference to `ContextCoreManager`.

## 6. Challenges & Future Enhancements

*   **Sophisticated Intent Mapping/Planning:** Simple pattern matching for `_determine_blueprint_id_for_request` might not be sufficient for complex requests. This could evolve into a full planning system that dynamically composes sequences of modules.
*   **Dynamic Context Retrieval:** Efficiently fetching and providing *only* the relevant context from a potentially vast `ContextCore` to modules.
*   **Multi-Module Orchestration:** Current design focuses on invoking one module per request. Handling requests that require chaining multiple modules (e.g., summarize then translate) needs to be designed (either Semantic Bus orchestrates multiple `invoke_module` calls or `ModuleBlueprint` itself supports defining inter-module sequences).
*   **Error Recovery & Fallback Strategies:** More robust strategies for when a selected module fails (e.g., trying an alternative blueprint, returning a graceful error).
*   **User-Specific Blueprint Selection:** Tailoring blueprint selection based on user preferences or history stored in `UserContext` or `ContextCore`.

This `SemanticBusController` completes the core control flow of the multi-bus architecture, providing a high-level entry point for complex AI task execution.
