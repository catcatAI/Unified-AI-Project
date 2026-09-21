# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
BlockFactory — wraps existing subsystems as MSBA semantic blocks.

Creates 8 blocks (no linguistic — Phase 1 uses rules):
  temporal, biological, emotional, cognitive,
  social, mathematical, knowledge, causal
"""

import logging
from typing import Dict, Optional

from .block_coordinator import BlockCoordinator
from .semantic_block import SemanticBlock
from .types import HitSource

logger = logging.getLogger(__name__)


def create_default_blocks(
    state_matrix: object = None,
    core_network: object = None,
    tensor_snn: object = None,
    emotion_system: object = None,
    causal_engine: object = None,
    meta_controller: object = None,
    ham_memory: object = None,
    dictionary_layer: object = None,
    vector_dict: object = None,
) -> Dict[str, SemanticBlock]:
    """
    Create the 8 default semantic blocks.

    Each block wraps an existing subsystem via BlockCoordinator.
    """
    blocks = {}

    # 1. Temporal Block
    blocks["temporal"] = SemanticBlock(
        block_id="temporal",
        block_name="Temporal",
        hit_sources=[
            HitSource("tense_past", "past_tense"),
            HitSource("tense_present", "present_tense"),
            HitSource("tense_future", "future_tense"),
            HitSource("temporal_relation", "temporal_relation"),
        ],
        coordinator=BlockCoordinator(engine=core_network, block_id="temporal"),
        capacity=8,
    )

    # 2. Biological Block
    blocks["biological"] = SemanticBlock(
        block_id="biological",
        block_name="Biological",
        hit_sources=[
            HitSource("energy", "energy"),
            HitSource("comfort", "comfort"),
            HitSource("arousal", "arousal"),
            HitSource("rest_need", "rest_need"),
            HitSource("hormonal", "hormonal_state"),
        ],
        coordinator=BlockCoordinator(engine=core_network, block_id="biological"),
        capacity=10,
    )

    # 3. Emotional Block
    blocks["emotional"] = SemanticBlock(
        block_id="emotional",
        block_name="Emotional",
        hit_sources=[
            HitSource("happiness", "happiness"),
            HitSource("sadness", "sadness"),
            HitSource("anger", "anger"),
            HitSource("fear", "fear"),
            HitSource("disgust", "disgust"),
            HitSource("surprise", "surprise"),
            HitSource("trust", "trust"),
            HitSource("anticipation", "anticipation"),
        ],
        coordinator=BlockCoordinator(engine=core_network, block_id="emotional"),
        capacity=12,
    )

    # 4. Cognitive Block
    blocks["cognitive"] = SemanticBlock(
        block_id="cognitive",
        block_name="Cognitive",
        hit_sources=[
            HitSource("curiosity", "curiosity"),
            HitSource("focus", "focus"),
            HitSource("confusion", "confusion"),
            HitSource("learning", "learning"),
            HitSource("calibration", "calibration"),
        ],
        coordinator=BlockCoordinator(engine=core_network, block_id="cognitive"),
        capacity=10,
    )

    # 5. Social Block
    blocks["social"] = SemanticBlock(
        block_id="social",
        block_name="Social",
        hit_sources=[
            HitSource("attention", "attention"),
            HitSource("bond", "bond"),
            HitSource("trust_social", "trust"),
            HitSource("presence", "presence"),
            HitSource("interaction_history", "interaction_history"),
        ],
        coordinator=BlockCoordinator(engine=core_network, block_id="social"),
        capacity=10,
    )

    # 6. Mathematical Block
    blocks["mathematical"] = SemanticBlock(
        block_id="mathematical",
        block_name="Mathematical",
        hit_sources=[
            HitSource("logic", "logic"),
            HitSource("precision", "precision"),
            HitSource("abstraction", "abstraction"),
            HitSource("certainty", "certainty"),
            HitSource("complexity", "complexity"),
            HitSource("fatigue", "fatigue"),
        ],
        coordinator=BlockCoordinator(engine=core_network, block_id="mathematical"),
        capacity=10,
    )

    # 7. Knowledge Block
    blocks["knowledge"] = SemanticBlock(
        block_id="knowledge",
        block_name="Knowledge",
        hit_sources=[
            HitSource("entity_store", "entity"),
            HitSource("relation_store", "relation"),
            HitSource("fact_store", "fact"),
        ],
        coordinator=BlockCoordinator(
            engine=tensor_snn or core_network,
            block_id="knowledge",
        ),
        capacity=8,
    )

    # 8. Causal Block
    blocks["causal"] = SemanticBlock(
        block_id="causal",
        block_name="Causal",
        hit_sources=[
            HitSource("cause_effect", "cause"),
            HitSource("confounders", "confounder"),
            HitSource("intervention", "intervention"),
            HitSource("prediction", "prediction"),
        ],
        coordinator=BlockCoordinator(engine=core_network, block_id="causal"),
        capacity=8,
    )

    logger.info("Created %d MSBA blocks", len(blocks))
    return blocks


def create_linguistic_block() -> SemanticBlock:
    """
    Phase 1: Rule-based linguistic block.
    Phase 2: Replace with spaCy POS tagging + dependency parsing.
    """
    return SemanticBlock(
        block_id="linguistic",
        block_name="Linguistic",
        hit_sources=[
            HitSource("tense_marker", "tense_marker"),
            HitSource("aspect", "aspect"),
            HitSource("modality", "modality"),
            HitSource("discourse_role", "discourse_role"),
            HitSource("register", "register"),
        ],
        coordinator=None,  # Rule-based, no SNN
        capacity=8,
    )
