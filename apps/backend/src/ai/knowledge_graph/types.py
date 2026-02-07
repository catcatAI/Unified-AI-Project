from typing import List, Dict, Optional, Any, TypedDict
from typing_extensions import Required

class KGEntityAttributes(TypedDict, total=False):
    start_char: int
    end_char: int
    is_conceptual: bool
    source_text: str
    rule_added: str

class KGEntity(TypedDict):
    id: Required[str]
    label: Required[str]
    type: Required[str]  # e.g., "ORG", "PERSON", "GPE", "LOC", "CONCEPT", etc.
    attributes: KGEntityAttributes

class KGRelationshipAttributes(TypedDict, total=False):
    pattern: str  # Name of the pattern or rule that extracted this
    trigger_token: Optional[str]
    trigger_text: Optional[str]

class KGRelationship(TypedDict):
    source_id: Required[str]  # ID of the source KGEntity
    target_id: Required[str]  # ID of the target KGEntity
    type: Required[str]       # Type of the relationship (e.g., "is_a", "works_for")
    weight: Optional[float]   # Or confidence score
    attributes: KGRelationshipAttributes

class KnowledgeGraphMetadata(TypedDict):
    source_text_length: Required[int]
    processed_with_model: Required[str]
    entity_count: Required[int]
    relationship_count: Required[int]

class KnowledgeGraph(TypedDict):
    entities: Required[Dict[str, KGEntity]]
    relationships: Required[List[KGRelationship]]
    metadata: Required[KnowledgeGraphMetadata]