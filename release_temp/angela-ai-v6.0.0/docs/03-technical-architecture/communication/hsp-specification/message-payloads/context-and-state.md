# HSP Payloads: Context and State

These payloads are used for sharing environmental information and internal AI
states.

## `EnvironmentalState` / `ContextUpdate`

- **Purpose:** To share information about the shared environment or a relevant
  contextual shift that may be important for other AIs.
- **Key Fields:**
  - `update_id` (string, UUID): Unique ID for this update.
  - `source_ai_id` (string, DID/URI): The AI reporting the update.
  - `phenomenon_type` (string, URI): The type of event or state being described
    (e.g., `hsp:event:UserMoodShift`).
  - `parameters` (object): Specifics of the state (e.g.,
    `{"user_id": "user_X", "new_mood": "anxious"}`).
  - `timestamp_observed` (string, ISO 8601 UTC): When the state was observed.
  - `scope_type` / `scope_id` (string, optional): The scope this update applies
    to (e.g., a specific session or project).

- **Example:**
  ```json
  {
    "update_id": "ctxupd_uuid_klmno",
    "source_ai_id": "did:hsp:ai_epsilon",
    "phenomenon_type": "hsp:event:UserMoodShift",
    "parameters": {
      "user_id": "user_alice",
      "current_mood": "happy"
    },
    "timestamp_observed": "2024-07-05T13:00:00Z",
    "scope_type": "session",
    "scope_id": "session_123"
  }
  ```

## `AIStateSynchronization` (Conceptual)

- **Purpose:** An AI shares parts of its internal model or state with another.
  This is a highly sensitive and complex operation.
- **Status:** This payload is **conceptual for v0.1** and its detailed
  specification is deferred to a future version of HSP.
- **Potential Fields:** `sync_id`, `source_ai_id`, `target_ai_id`,
  `model_component_name`, `state_data_format`, `state_data_chunk`,
  `sequence_number`, `is_last_chunk`.
