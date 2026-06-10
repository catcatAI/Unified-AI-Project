"""
存在系统 (Ontology System)
Level 5 ASI 的三大支柱之一, 负责存在定义、实体关系和世界观管理
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class OntologySystem:
    """存在系统 - 管理概念定义、实体关系和世界观"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.ontology: Dict[str, Any] = {}
        self.relations: Dict[str, Any] = {}
        logger.debug("OntologySystem initialized")

    def register_concept(self, name: str, properties: Optional[Dict[str, Any]] = None) -> None:
        self.ontology[name] = properties or {}

    def query_concept(self, name: str) -> Optional[Dict[str, Any]]:
        return self.ontology.get(name)

    def get_related_concepts(self, concept: str) -> List[Dict[str, Any]]:
        if concept not in self.ontology:
            return []
        related = []
        for other in self.ontology:
            if other != concept:
                common = set(self.ontology[concept].keys()) & set(self.ontology[other].keys())
                if common:
                    related.append({"concept": other, "shared_properties": list(common)})
        return related
