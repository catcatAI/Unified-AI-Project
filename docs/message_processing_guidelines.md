# Message Processing Guidelines

When processing messages with defined formats, such as `HSPMessageEnvelope` or `ToolDispatcherResponse` within this project, it's crucial to adopt robust practices to ensure reliability and maintainability. This document outlines key considerations and provides conceptual examples.

## Core Principles

Effective message processing involves several key stages:

1.  **Validation:** Ensure the incoming message conforms to the expected structure and data types.
2.  **Routing:** Direct the message to the appropriate handler based on its type or content.
3.  **Safe Payload Access:** Access message fields defensively to avoid runtime errors.
4.  **Error Handling:** Implement strategies to manage unexpected issues or malformed messages.
5.  **Business Logic:** Apply the core logic specific to the message's purpose.

## Detailed Steps and Considerations

### 1. Validate the Incoming Message

Before processing, validate the message structure:

*   **Presence of Required Fields:** Check if all mandatory fields (as defined in the `TypedDict` or schema) are present.
*   **Correct Data Types:** Verify that field values match their expected Python types (e.g., a field typed as `str` should indeed be a string).
*   **Constrained Values:** For fields using `Literal` types or `Enum`s, ensure the provided value is one of the allowed options.
*   **Structural Integrity:** For nested structures (e.g., a dictionary within a dictionary), validate their internal layout as well.

**Note on `TypedDict` vs. Pydantic:**
While this project primarily uses `TypedDict` for defining message structures (which aids static analysis), `TypedDict` itself does not perform runtime validation. Runtime checks must be implemented manually. Libraries like Pydantic excel at this by automatically validating data against model definitions upon instantiation, significantly reducing boilerplate validation code. Consider Pydantic for new complex data structures or when robust runtime validation is critical.

### 2. Route Based on Message Type/Content

Use specific fields in the message to determine how it should be handled:

*   For `HSPMessageEnvelope`, the `message_type` field is the primary routing key.
*   For `ToolDispatcherResponse`, the `status` field often dictates the subsequent actions.
*   This routing can be implemented using `if/elif/else` chains or a more extensible approach like a dictionary mapping message types/statuses to handler functions.

### 3. Safely Access Payload Fields

When dealing with message payloads, especially those typed as `Any` or `Dict[str, Any]`:

*   **Use `.get()` for Dictionaries:** Access dictionary keys using the `.get("key_name", default_value)` method to avoid `KeyError` if a key is missing. Provide a sensible default or handle the `None` case explicitly.
*   **Check for Key Existence:** Alternatively, use `if "key_name" in my_dict:` before accessing `my_dict["key_name"]`.
*   **Type Checking/Casting:** If you expect a field to be of a particular type (e.g., a nested list or dictionary), check its type using `isinstance()` before performing operations specific to that type. Use `typing.cast` judiciously when you are certain about the type after a check, to help with static analysis.

### 4. Implement Robust Error Handling

Anticipate potential issues:

*   **Wrap processing logic in `try...except` blocks:** Catch specific exceptions like `KeyError`, `TypeError`, `ValueError` (e.g., during data conversion attempts), and potentially more general `Exception`s.
*   **Log Errors:** When an error occurs, log it comprehensively. Include:
    *   A clear error message.
    *   The type of exception.
    *   Relevant parts of the message that caused the error (being extremely careful not to log sensitive information like API keys or PII).
    *   Traceback information (if helpful for debugging).
*   **Strategy for Unprocessable Messages:**
    *   **Discard:** If the message is irrelevant or hopelessly malformed.
    *   **Dead-Letter Queue (DLQ):** In more complex systems, move unprocessable messages to a separate queue for later inspection.
    *   **Negative Acknowledgement (NACK):** In request/response patterns, send a NACK back to the sender indicating the processing failure, possibly with an error code.

### 5. Apply Business Logic

Once the message is validated and its structure is understood, execute the core logic intended for that message. This is the "work" your component is supposed to do based on the received information.

## Conceptual Python Example

This snippet demonstrates processing an `HSPMessageEnvelope` using `TypedDict`.

```python
from typing import TypedDict, Optional, Any, Dict, Literal, cast

# Assume these types are defined and imported correctly
# from src.hsp.types import HSPMessageEnvelope, HSPFactPayload, HSPTaskResultPayload
# (Using placeholder definitions for this example if not available)

class HSPFactPayload(TypedDict): # Placeholder
    id: Optional[str]
    statement_nl: Optional[str]
    # ... other fields

class HSPTaskResultPayload(TypedDict): # Placeholder
    task_id_ref: Optional[str]
    status: Optional[str]
    # ... other fields

class HSPMessageEnvelope(TypedDict): # Placeholder
    message_type: Optional[str]
    payload: Optional[Any]
    sender_ai_id: Optional[str]
    # ... other fields


class ProcessingStatus(TypedDict):
    success: bool
    message: str
    error_code: Optional[str]

def process_hsp_message(envelope: HSPMessageEnvelope) -> ProcessingStatus:
    # 1. Basic Validation
    if not isinstance(envelope, dict): # Basic check for dict structure
        return {"success": False, "message": "Invalid envelope: not a dictionary.", "error_code": "INVALID_ENVELOPE_STRUCTURE"}

    message_type = envelope.get("message_type")
    payload = envelope.get("payload")
    sender_id = envelope.get("sender_ai_id")

    if not message_type or not isinstance(message_type, str):
        return {"success": False, "message": "Missing or invalid 'message_type' in envelope.", "error_code": "MISSING_MESSAGE_TYPE"}
    if payload is None: # Payload being an empty dict might be valid, but None is not.
        return {"success": False, "message": "Missing 'payload' in envelope.", "error_code": "MISSING_PAYLOAD"}
    if not sender_id or not isinstance(sender_id, str):
        return {"success": False, "message": "Missing or invalid 'sender_ai_id' in envelope.", "error_code": "MISSING_SENDER_ID"}

    # 2. Routing based on message_type
    try:
        if message_type == "HSP::Fact_v0.1":
            if not isinstance(payload, dict):
                return {"success": False, "message": "Fact payload is not a dictionary.", "error_code": "INVALID_FACT_PAYLOAD_STRUCTURE"}

            fact_payload = cast(HSPFactPayload, payload)

            statement_nl = fact_payload.get("statement_nl")
            fact_id = fact_payload.get("id", "unknown_fact_id")

            if not statement_nl or not isinstance(statement_nl, str):
                return {"success": False, "message": f"Fact payload for '{fact_id}' missing or invalid 'statement_nl'.", "error_code": "INVALID_FACT_PAYLOAD_CONTENT"}

            # 3. Business Logic for Fact
            print(f"Processing fact from {sender_id}: {statement_nl}")
            # Example: learning_manager.process_hsp_fact(fact_payload, sender_id, envelope)
            return {"success": True, "message": f"Fact '{fact_id}' processed successfully."}

        elif message_type == "HSP::TaskResult_v0.1":
            if not isinstance(payload, dict):
                return {"success": False, "message": "TaskResult payload is not a dictionary.", "error_code": "INVALID_TASK_RESULT_STRUCTURE"}

            result_payload = cast(HSPTaskResultPayload, payload)
            task_id_ref = result_payload.get("task_id_ref")
            status = result_payload.get("status")

            if not task_id_ref or not isinstance(task_id_ref, str) or \
               not status or not isinstance(status, str):
                return {"success": False, "message": "TaskResult payload missing/invalid 'task_id_ref' or 'status'.", "error_code": "INVALID_TASK_RESULT_CONTENT"}

            # Business Logic for TaskResult
            print(f"Processing TaskResult for '{task_id_ref}', status: {status}")
            # Example: self._handle_incoming_hsp_task_result(result_payload, sender_id, envelope)
            return {"success": True, "message": f"TaskResult for '{task_id_ref}' processed."}

        else:
            return {"success": False, "message": f"Unknown HSP message type: '{message_type}'", "error_code": "UNKNOWN_MESSAGE_TYPE"}

    except Exception as e:
        # 4. General Error Handling for unexpected issues during processing
        print(f"Error processing message type '{message_type}': {e}")
        return {"success": False, "message": f"An unexpected error occurred: {str(e)}", "error_code": "PROCESSING_EXCEPTION"}

```

By following these guidelines, developers can build more resilient and understandable message processing components within the project.
