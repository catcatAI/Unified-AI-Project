# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================
"""
Neural Bridge — 最少轉譯直接連結 StateMatrix ↔ GARDEN/ED3N SNN.

Both StateMatrix (axis → key → [0,1]) and SNN outputs (concept_key → [0,1])
are "key → [0,1] value" dictionaries with a naturally compatible numeric
domain. This package provides the minimal-translation connection: a pure
symbolic key mapping (no vector projection, no embedding) so state axis
values pass into the SNN as input activations and SNN output activations
flow back into the state matrix. Values are clamped [0,1] on both sides and
pass through unchanged (zero numeric translation).
"""
