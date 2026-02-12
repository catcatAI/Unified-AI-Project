"""
Angela AI v6.0 - Metamorphosis Module
蜕变模块

Version transition system for Angela AI.
Angela AI的版本切换系统。

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-04
"""

import logging
logger = logging.getLogger(__name__)

from .soul_core import (
    SoulCore,
    SoulSignature,
    IdentityCore,
    MemoryEssence,
    SoulCoreManager,
    SoulComponent,
    create_soul_core,
)

from .body_adapter import (
    BodyAdapter,
    StateSnapshot,
    TransferRecord,
    AdaptationRule,
    TransferStatus,
    CompatibilityLevel,
    BodyAdapterFactory,
    create_body_adapter,
)

from .transition_anim import (
    TransitionAnimator,
    TransitionManager,
    TransitionConfig,
    TransitionProgress,
    TransitionFrame,
    TransitionPhase,
    TransitionType,
    create_transition_manager,
)

__version__ = "6.0.0"
__author__ = "Angela AI Development Team"

__all__ = [
    # Soul Core
    "SoulCore",
    "SoulSignature",
    "IdentityCore",
    "MemoryEssence",
    "SoulCoreManager",
    "SoulComponent",
    "create_soul_core",
    
    # Body Adapter
    "BodyAdapter",
    "StateSnapshot",
    "TransferRecord",
    "AdaptationRule",
    "TransferStatus",
    "CompatibilityLevel",
    "BodyAdapterFactory",
    "create_body_adapter",
    
    # Transition Animation
    "TransitionAnimator",
    "TransitionManager",
    "TransitionConfig",
    "TransitionProgress",
    "TransitionFrame",
    "TransitionPhase",
    "TransitionType",
    "create_transition_manager",
]
