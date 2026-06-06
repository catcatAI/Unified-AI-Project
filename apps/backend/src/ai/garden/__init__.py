# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""
GARDEN — Giant Associative Relation Decoupled Evolutionary Network
Lightweight 1GB local model. Second tier in Angela AI's five-tier model scaling architecture.

Hierarchy:
  [Ultra-Lightweight] ED3N (~100KB, edge)
  [Lightweight]       GARDEN-1G (~1GB, local PC)  ← This module
  [Standard]          FOREST-10G (~10GB, workstation)
  [Heavy]             BIOME-100G (~100GB, server)
  [Ultra-Heavy]       ECOSYSTEM-1T (~1TB, cluster)
"""

from apps.backend.src.ai.garden.dictionary import VectorDictionary
from apps.backend.src.ai.garden.snn_core import TensorSNNCore
from apps.backend.src.ai.garden.garden_engine import GARDENEngine
from apps.backend.src.ai.garden.binary_store import BinaryStore
from apps.backend.src.ai.garden.kg_import import KGImporter
from apps.backend.src.ai.garden.hybrid_router import HybridRouter, TierResult, RoutingDecision

__all__ = [
    "VectorDictionary",
    "TensorSNNCore",
    "GARDENEngine",
    "BinaryStore",
    "KGImporter",
    "HybridRouter",
    "TierResult",
    "RoutingDecision",
]
