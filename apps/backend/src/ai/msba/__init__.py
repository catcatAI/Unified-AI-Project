# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
Multi-Dimensional Semantic Block Architecture (MSBA).

Seven-layer pipeline:
  Layer 0: Deterministic Seed (all inputs)
  Layer 1: Semantic Block Library (9+ blocks)
  Layer 2: Block Selector (4-signal fusion)
  Layer 3: Intra-Block Hit (parallel)
  Layer 4: Relevance Convergence (cross-attention)
  Layer 5: Multi-Directional Decode (attention fusion)
  Layer 6: Output + Learning (Hebbian feedback)
"""

from .ab_testing import ABTesting
from .block_coordinator import BlockCoordinator
from .block_factory import (
    create_all_blocks,
    create_audio_block,
    create_default_blocks,
    create_linguistic_block,
    create_vision_block,
)
from .block_history_persistence import BlockHistoryPersistence
from .block_selector import BlockSelector
from .checkpointer import MSBACheckpointer
from .cold_start import ColdStartManager
from .intra_block_hit import IntraBlockHitEngine
from .linguistic_block import LinguisticBlock
from .memmapped_block import MemMappedBlock
from .metrics_collector import MetricsCollector
from .multi_dir_decoder import MultiDirectionalDecoder
from .multimodal_blocks import AudioBlock, VisionBlock
from .neuroblender_bridge import NeuroBlenderBridge
from .performance_profiler import PerformanceProfiler
from .pipeline import MSBAPipeline
from .relevance_convergence import RelevanceConvergence
from .semantic_block import SemanticBlock
from .types import (
    BlockHistory,
    BlockHitResult,
    BlockSelection,
    FusedRepresentation,
    HitSource,
    SeedResult,
)
from .weight_migration import WeightMigration

__all__ = [
    # Types
    "BlockHitResult",
    "BlockHistory",
    "BlockSelection",
    "FusedRepresentation",
    "HitSource",
    "SeedResult",
    # Core components
    "BlockCoordinator",
    "SemanticBlock",
    "BlockSelector",
    "IntraBlockHitEngine",
    "RelevanceConvergence",
    "MultiDirectionalDecoder",
    "MSBAPipeline",
    # Phase 2 additions
    "MemMappedBlock",
    "LinguisticBlock",
    "BlockHistoryPersistence",
    # Multimodal blocks
    "VisionBlock",
    "AudioBlock",
    # Weight migration
    "WeightMigration",
    # A/B testing
    "ABTesting",
    # Monitoring
    "MetricsCollector",
    # NeuroBlender integration
    "NeuroBlenderBridge",
    # Performance
    "PerformanceProfiler",
    # Factory functions
    "create_all_blocks",
    "create_default_blocks",
    "create_linguistic_block",
    "create_vision_block",
    "create_audio_block",
    # Support modules
    "ColdStartManager",
    "MSBACheckpointer",
]
