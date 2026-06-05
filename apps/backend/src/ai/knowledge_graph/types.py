# ANGELA-MATRIX: L0[基础层] [A] L1

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class KGEntity:
    id: str
    name: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KGRelationship:
    source_id: str
    target_id: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeGraph:
    entities: Dict[str, KGEntity] = field(default_factory=dict)
    relationships: List[KGRelationship] = field(default_factory=list)


class KnowledgeGraphTypes:
    Entity = KGEntity
    Relationship = KGRelationship
    Graph = KnowledgeGraph
