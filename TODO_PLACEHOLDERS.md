# Project Placeholders and TODOs Summary

This document outlines the placeholders and TODO items found within the Unified-AI-Project codebase.

## 1. Configuration Placeholders

These are values intended to be replaced by actual secrets or configurations, typically via environment variables. They are generally structural and not code to be written.

*   **File:** `configs/api_keys.yaml`
    *   `GEMINI_API_KEY_PLACEHOLDER` (L7): Placeholder for Google Gemini API Key.
    *   `OPENAI_API_KEY_PLACEHOLDER` (L11): Placeholder for OpenAI API Key.
    *   `FIREBASE_CREDENTIALS_PATH_PLACEHOLDER` (L18): Placeholder for Firebase Admin SDK JSON credentials file path.
    *   `BASE_URL_PLACEHOLDER` (L22): Placeholder for a general base URL.
    *   `ANOTHER_SERVICE_API_KEY_PLACEHOLDER` (L24, commented out): Example placeholder.
    *   `SOME_COMPLEX_SERVICE_CLIENT_ID_PLACEHOLDER` (L28, commented out): Example placeholder.
    *   `SOME_COMPLEX_SERVICE_CLIENT_SECRET_PLACEHOLDER` (L29, commented out): Example placeholder.
    *   `SOME_COMPLEX_SERVICE_REGION_PLACEHOLDER` (L30, commented out): Example placeholder.
    *   **Note:** The file itself states these are for documentation and structural reference.

## 2. Missing Feature/Logic Implementation (TODOs)

These are comments indicating planned work or missing functionality that requires code implementation.

*   **File:** `src/core_ai/code_understanding/lightweight_code_model.py`
    *   **Line:** ~177 (Original TODO location in `get_tool_structure`)
    *   **Placeholder:** `# COMPLETED: Logic to resolve tool_name to a filepath has been implemented.`
    *   **Context:** Was in the `get_tool_structure` method.
    *   **Required Functionality:** (Implemented in `feat/lcm-tool-name-resolution`) The `get_tool_structure` method now resolves `tool_path_or_name` by checking if it's a direct path, then attempting to find `name.py`, `tool_name.py`, or `name_tool.py` in the configured `tools_directory`.

*   **File:** `src/core_ai/service_discovery/service_discovery_module.py`
    *   **Original TODO Context:** Logic for staleness/expiration of capabilities.
    *   **Status:** LARGELY IMPLEMENTED / VERIFIED.
    *   **Details:** The module was found to be an existing HSP-specific implementation, already including `TrustManager` integration and staleness logic. A minor refinement was made to include `description` in the essential fields check during capability advertisement processing. The core logic for handling HSP capabilities, staleness, and trust is functional.
    *   **Future Enhancements (Optional):**
        1.  Implement an active pruning mechanism for stale capabilities (the method `_prune_stale_capabilities` exists but is not currently called periodically).
        2.  Consider adding JSON schema validation for incoming `HSPCapabilityAdvertisementPayload` if/when official schemas become available and resolvable.

*   **File:** `src/hsp/connector.py`
    *   **Original TODO Context (Line ~63):** Manual reconnection logic in `_on_mqtt_disconnect`.
    *   **Status:** CLARIFIED / HANDLED BY LIBRARY.
    *   **Details:** Reconnection strategy is handled by the Paho MQTT client's built-in features. Verification and enhanced logging were completed (`feat/hsp-connector-robustness`).
    *   **Original TODO Context (Line ~128, in `_build_hsp_envelope`):** `"payload_schema_uri": None, # TODO: Add schema URIs when defined`
    *   **Status:** PENDING (Placeholder in place).
    *   **Details:** The `payload_schema_uri` field is currently populated with conventional placeholder URIs (e.g., 'hsp:schema:payload/Fact/0.1') based on message type and version (`feat/hsp-payload-schema-uri-placeholder`).
    *   **Required Functionality:** Update this to populate the `payload_schema_uri` field with actual, resolvable URIs once the HSP message payload schemas are formally defined, published, and hosted externally/internally.
    *   **Original TODO Context (Line ~260, in `_handle_hsp_message_str`):** Logic for sending 'received' ACKs.
    *   **Status:** CLARIFIED / IMPLEMENTED.
    *   **Details:** The connector sends 'received' ACKs when `qos_parameters.requires_ack` is true. Functionality verified and tested (`feat/hsp-ack-handling`). Future enhancements could include 'processed' ACKs or NACKs.

*   **File:** `src/interfaces/electron_app/renderer.js`
    *   **Line:** ~137 (Original location of TODO comment)
    *   **Placeholder:** `# COMPLETED: Button to trigger/select HSP service has been added.`
    *   **Context:** Was inside the `loadHspServices` function.
    *   **Required Functionality:** (Implemented in `feat/electron-hsp-use-service-button`) A "Use Service" button is now added to each service in the HSP services list. Clicking it populates the "Target Capability ID" field in the HSP Task Request form and clears the parameters field.

*   **File:** `src/core_services.py`
    *   **Context:** The `HSPConnector` instance in `initialize_services` subscribes to topics like `f"{CAP_ADVERTISEMENT_TOPIC}/#"` and `f"{FACT_TOPIC_GENERAL}/#"`.
    *   **TODO:** Define the constants `CAP_ADVERTISEMENT_TOPIC` and `FACT_TOPIC_GENERAL`. These are currently used as f-string components without prior definition in `core_services.py`. They should be defined, perhaps in `src/hsp/constants.py` or loaded from a configuration, and then imported/used in `core_services.py`.
    *   **Status:** COMPLETED.
    *   **Resolution:** Constants `CAP_ADVERTISEMENT_TOPIC` and `FACT_TOPIC_GENERAL` were defined in `src/hsp/constants.py` and imported for use in `src/core_services.py` by commit associated with branch `feat/hsp-topic-constants`.

*   **File:** `src/hsp/connector.py` (Related to `core_services.py`)
    *   **Context:** `HSPConnector.register_on_task_result_callback` currently allows only one callback to be registered for task results. Both `DialogueManager` and `FragmentaOrchestrator` might need to process task results.
    *   **TODO:** Enhance `HSPConnector` to support multiple callbacks for task results (e.g., a list of callbacks) or implement a central dispatcher mechanism within `core_services.py` that receives all task results and routes them to the appropriate module (DM or Fragmenta) based on `correlation_id` or other metadata. This is to prevent one module's registration from overwriting another's.
    *   **Status:** COMPLETED.
    *   **Resolution:** `HSPConnector` was modified to change `_on_task_result_callback` to `_on_task_result_callbacks` (a list). The `register_on_task_result_callback` method now appends to this list, and `unregister_on_task_result_callback` was added. The message handling logic iterates through all registered callbacks. The warning in `core_services.py` about overwriting was removed. Unit tests for this functionality were added in `tests/hsp/test_hsp_connector.py`.

*   **File:** `src/fragmenta/fragmenta_orchestrator.py`
    *   **Context:** The `process_complex_task` method has basic state management for handling asynchronous HSP calls.
    *   **TODO:** Enhance state management for more complex scenarios, such as tasks involving multiple sequential or parallel HSP calls, or mixed local and HSP steps. This might require a more formal plan execution engine within Fragmenta.
    *   **Status:** Pending.
    *   **Context:** Error handling for HSP tasks (e.g., timeouts, complex failure payloads from peers) is currently basic.
    *   **TODO:** Implement more robust error handling and potentially retry strategies for HSP sub-tasks dispatched by Fragmenta. Consider how HSP task timeouts should be managed.
    *   **Status:** Pending.

## 3. Code/Data Comments & Clarifications

These are comments that were picked up by the search but are not actionable code placeholders requiring new implementation. They are either logic that handles TODOs, commented-out debug lines, TODOs within example data, or general clarifications.

*   **File:** `scripts/data_processing/process_copilot_logs.py`
    *   Line ~46: `if prompt.startswith("# TODO:") or prompt.startswith("// TODO:")` (Logic for filtering input data)
    *   Line ~47: `# print(f"Skipping row {row_num+2}: Prompt is a TODO comment ('{prompt}').")` (Commented-out debug code)
    *   Line ~96: `2024-05-20T10:10:00Z,"# TODO: Add more comprehensive error handling here",...` (Example TODO within a dummy CSV string in the script)

*   **File:** `src/core_ai/dialogue/dialogue_manager.py`
    *   Line ~618 (approx): `raise NotImplementedError("Tool logic not implemented yet.")` and `# TODO: Implement actual tool logic here`. These are found within a multi-line string that serves as an example/template for an LLM to generate tool code. They are part of the *template's content*, not direct TODOs for the Dialogue Manager itself.

*   **File:** `src/shared/types/common_types.py`
    *   Line ~216: `# TODO: Consider a transformation step if strict snake_case is required internally for these.` (Comment suggesting a potential future refactor for field naming in `OllamaChatHistoryEntry`)
    *   Line ~410: `id: str # The memory_id (mem_XXXXXX)` (A clarifying comment for a field, not a placeholder to be filled.)

## 4. Data Anomalies (Previously "Data Placeholders")

Anomalies observed within data files.

*   **File:** `data/processed_data/dialogue_context_memory.json`
    *   **Observation:** The string `"XXX"` has been found as a substring within some `encrypted_package_b64` values.
    *   **Clarification (as of July 8, 2024):** Initial hypotheses suggested "XXX" might be a special placeholder or a "Deep Mapping" token. However, further investigation, detailed in `docs/architecture/DEEP_MAPPING_AND_PERSONALITY_SIMULATION.md` and summarized in `docs/PROJECT_STATUS_SUMMARY.md` (Section 2), has concluded that these "XXX" sequences are **coincidental substrings** within normally processed (abstracted, compressed, encrypted) HAM data.
    *   **Current Understanding:** These occurrences are not indicative of a deliberate "Deep Mapping" token system or placeholders for missing data in that sense. They are artifacts of the standard data transformation pipeline. While the concept of advanced Deep Mapping remains a potential future architectural goal, it is not represented by these "XXX" findings. Any perceived incompleteness or issues with such data packages should be investigated as potential data integrity or processing artifacts rather than special markers.

This summary provides a clear overview of outstanding tasks and points of interest related to placeholders and TODOs in the project.
