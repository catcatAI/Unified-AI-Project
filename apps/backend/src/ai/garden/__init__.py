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

from .dictionary import VectorDictionary
from .snn_core import TensorSNNCore
from .garden_engine import GARDENEngine
from .binary_store import BinaryStore
from .kg_import import KGImporter
from .vector_decoder import VectorDecoder

__all__ = [
    "VectorDictionary",
    "TensorSNNCore",
    "GARDENEngine",
    "BinaryStore",
    "KGImporter",
    "VectorDecoder",
]
