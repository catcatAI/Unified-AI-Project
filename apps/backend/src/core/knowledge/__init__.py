# =============================================================================
# ANGELA-MATRIX: [L5] [αβγδ] [B] [L5]
# =============================================================================
"""
Knowledge module: unified knowledge graph for cross-domain representation and reasoning.

Provides:
  - UnifiedKnowledgeGraph: Core knowledge graph for entity linking,
    relation extraction, knowledge fusion, and temporal updates
"""

from core.knowledge.unified_knowledge_graph_impl import UnifiedKnowledgeGraph

__all__ = [
    "UnifiedKnowledgeGraph",
]
