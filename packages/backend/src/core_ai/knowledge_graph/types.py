from typing import Any, Dict, List, Optional, Required, TypedDict


class KGEntityAttributes(TypedDict, total=False):
    start_char: int
    end_char: int
    is_conceptual: bool
    source_text: str
    rule_added: str
    # Other attributes can be added as needed

class KGEntity(TypedDict):
    id: Required[str]
    label: Required[str]
    type: Required[str] # e.g., "ORG", "PERSON", "GPE", "LOC", "CONCEPT", etc.
    attributes: KGEntityAttributes
    # Optional: description: Optional[str], confidence: Optional[float]

class KGRelationshipAttributes(TypedDict, total=False):
    pattern: str # Name of the pattern or rule that extracted this
    trigger_token: Optional[str]
    trigger_text: Optional[str]
    # Optional: confidence: Optional[float], sentence_id: Optional[int]

class KGRelationship(TypedDict):
    source_id: Required[str] # ID of the source KGEntity
    target_id: Required[str] # ID of the target KGEntity
    type: Required[str]      # Type of the relationship (e.g., "is_a", "works_for", verb_lemma)
    weight: Optional[float]  # Or confidence score
    attributes: KGRelationshipAttributes

class KnowledgeGraphMetadata(TypedDict):
    source_text_length: Required[int]
    processed_with_model: Required[str]
    entity_count: Required[int]
    relationship_count: Required[int]
    # Optional: processing_time_ms: Optional[float], source_document_id: Optional[str]

class KnowledgeGraph(TypedDict):
    entities: Required[Dict[str, KGEntity]]
    relationships: Required[List[KGRelationship]]
    metadata: Required[KnowledgeGraphMetadata]
