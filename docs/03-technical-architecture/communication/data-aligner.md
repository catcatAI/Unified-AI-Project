# Data Aligner

## Overview

This document provides an overview of the `DataAligner` module, defined in `src/hsp/bridge/data_aligner.py`. This module is a critical component responsible for validating and aligning incoming messages against predefined schemas within the Heterogeneous Service Protocol (HSP).

## Purpose

The primary purpose of the `DataAligner` is to ensure the integrity, conformity, and reliability of data exchanged across the HSP network. It acts as a gatekeeper, preventing malformed, incomplete, or unexpected messages from propagating through the system. By aligning messages to expected structures, it guarantees that downstream modules receive data in a predictable and usable format, which is essential for robust inter-AI communication.

## Key Responsibilities and Features

*   **Message Validation and Alignment (`align_message`)**: This is the main public method. It takes a raw incoming message (expected to be a Python dictionary) and performs a two-step validation process:
    1.  **Envelope Validation**: Basic checks on the overall message structure.
    2.  **Payload Validation**: Delegates to specialized internal methods to validate the `payload` based on the `message_type` specified in the message envelope.
*   **Payload-Specific Validation**: The module contains dedicated private methods (e.g., `_align_fact_payload`, `_align_task_request_payload`) for each known HSP message type. These methods perform checks specific to the expected structure of that payload.
*   **Error Reporting**: If any validation fails, the `DataAligner` returns an `HSPErrorDetails` object, which provides a structured way to report the `error_code`, `error_message`, and the `location` within the message where the error occurred. This facilitates debugging and error handling in other parts of the system.

## How it Works

The `DataAligner` operates by comparing the structure of an incoming message against a set of expected rules or schemas (currently implemented as basic field presence checks, but extensible to full schema validation). It first ensures the message is a dictionary. Then, it checks the `message_type` to determine which specific payload validation rules to apply. If all checks pass, the message is considered "aligned" and is returned; otherwise, a detailed error object is returned, indicating the nature of the discrepancy.

## Integration with Other Modules

*   **HSP Type Definitions (`src/hsp/types.py`)**: The `DataAligner` relies heavily on the `TypedDict` definitions (like `HSPMessageEnvelope`, `HSPFactPayload`, etc.) from the `hsp.types` module. These definitions serve as the implicit schemas against which incoming messages are validated.
*   **`MessageBridge`**: The `MessageBridge` is the primary consumer of the `DataAligner`. All messages received from the external MQTT network are passed through the `DataAligner` before being routed to internal components, ensuring that only valid and well-formed messages enter the AI system.

## Code Location

`apps/backend/src/hsp/bridge/data_aligner.py`
