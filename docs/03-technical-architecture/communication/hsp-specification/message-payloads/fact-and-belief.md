# HSP Payloads: Fact and Belief

These payloads are fundamental for knowledge representation and sharing.

## `Fact` / `Assertion`

- **Purpose:** Represents a statement about the world, an entity, or a
  relationship, believed to be true by the originating AI to some degree.
- **Key Fields:**
  - `id` (string, UUID): Unique identifier for this fact instance.
  - `statement_type` (string, enum: "natural_language", "semantic_triple",
    "json_ld"): The representation of the core assertion.
  - `statement_nl` (string, optional): The assertion in natural language.
  - `statement_structured` (object, optional): Structured representation (e.g.,
    subject, predicate, object).
  - `source_ai_id` (string, DID/URI): ID of the AI originating this fact.
  - `timestamp_created` (string, ISO 8601 UTC): When the fact was asserted.
  - `confidence_score` (float, 0.0-1.0): The AI's confidence in the fact's
    truth.
  - `valid_from` / `valid_until` (string, ISO 8601 UTC, optional): For temporal
    facts.

- **Example (`semantic_triple`):**
  ```json
  {
    "id": "fact_uuid_12345",
    "statement_type": "semantic_triple",
    "statement_structured": {
      "subject_uri": "hsp:entity:Sky",
      "predicate_uri": "hsp:property:hasColor",
      "object_literal": "blue"
    },
    "source_ai_id": "did:hsp:ai_alpha",
    "timestamp_created": "2024-07-05T10:00:00Z",
    "confidence_score": 0.95
  }
  ```

## `Belief`

- **Purpose:** Similar to `Fact`, but for statements with higher subjectivity,
  uncertainty, or representing hypotheses.
- **Key Fields (in addition to Fact fields):**
  - `belief_holder_ai_id` (string, DID/URI): The AI holding this belief.
  - `justification_type` (string, enum: "text", "inference_chain_id",
    "evidence_ids_list"): The type of reasoning provided.
  - `justification` (string or array): The reasoning itself, or links to
    supporting evidence.

- **Example:**
  ```json
  {
    "id": "belief_uuid_67890",
    "statement_type": "natural_language",
    "statement_nl": "It might rain tomorrow.",
    "belief_holder_ai_id": "did:hsp:ai_beta",
    "timestamp_created": "2024-07-05T11:00:00Z",
    "confidence_score": 0.6,
    "justification_type": "text",
    "justification": "Weather model X showed a 60% chance."
  }
  ```
