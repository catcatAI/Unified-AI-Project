# HSP Payloads: Capability and Task

These payloads are used for service discovery and task execution.

## `CapabilityAdvertisement`

- **Purpose:** An AI advertises a skill, service, or tool it can offer to the
  network.
- **Key Fields:**
  - `capability_id` (string): Unique ID for this capability offering (e.g.,
    `ai_gamma_translate_v1.2`).
  - `ai_id` (string, DID/URI): ID of the AI offering the capability.
  - `name` / `description` (string): Human-readable details.
  - `version` (string): The version of the capability.
  - `input_schema_uri` / `output_schema_uri` (string, optional): Links to
    schemas defining the input and output data structures.
  - `availability_status` (string, enum: "online", "offline", "degraded").
  - `tags` (array of strings, optional): Keywords for discovery.

- **Example:**
  ```json
  {
    "capability_id": "ai_gamma_translate_v1.2",
    "ai_id": "did:hsp:ai_gamma",
    "name": "Text Translation Service",
    "version": "1.2.0",
    "input_schema_uri": "hsp:schemas:translation_input_v1",
    "availability_status": "online",
    "tags": ["nlp", "translation"]
  }
  ```

## `TaskRequest`

- **Purpose:** An AI requests another AI to perform a task using an advertised
  capability.
- **Key Fields:**
  - `request_id` (string, UUID): Unique ID for this request.
  - `requester_ai_id` (string, DID/URI): The AI making the request.
  - `target_ai_id` (string, DID/URI, optional): A specific target AI.
  - `capability_id_filter` (string): The ID of the capability being requested.
  - `parameters` (object): Input parameters conforming to the capability's input
    schema.
  - `priority` (integer, optional): Task priority.
  - `deadline_timestamp` (string, ISO 8601 UTC, optional): Task deadline.

- **Example:**
  ```json
  {
    "request_id": "taskreq_uuid_abcde",
    "requester_ai_id": "did:hsp:ai_delta",
    "target_ai_id": "did:hsp:ai_gamma",
    "capability_id_filter": "ai_gamma_translate_v1.2",
    "parameters": {
      "text_to_translate": "Hello world",
      "target_language": "fr"
    }
  }
  ```

## `TaskResult`

- **Purpose:** The outcome of a `TaskRequest`.
- **Key Fields:**
  - `result_id` (string, UUID): Unique ID for this result.
  - `request_id` (string, UUID): The ID of the original `TaskRequest`.
  - `executing_ai_id` (string, DID/URI): The AI that performed the task.
  - `status` (string, enum: "success", "failure", "in_progress").
  - `payload` (object, optional): The result data (on success).
  - `error_details` (object, optional): Error information (on failure).

- **Example:**
  ```json
  {
    "result_id": "taskres_uuid_fghij",
    "request_id": "taskreq_uuid_abcde",
    "executing_ai_id": "did:hsp:ai_gamma",
    "status": "success",
    "payload": {
      "translated_text": "Bonjour le monde"
    }
  }
  ```
