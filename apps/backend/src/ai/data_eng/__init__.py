# =============================================================================
# ANGELA-MATRIX: [L3] [αβγ] [B] [L2]
# =============================================================================
"""
data_eng — Unified data-engineering pipeline.

Consolidates data-engineering functions that were previously scattered across
GARDEN, ED3N, the training coordinator, download scripts, the document chunker,
and the response composer.  Every sub-module owns ONE canonical implementation
and existing call sites delegate here, so prefix dedup, semantic dedup,
hash/domain dedup, word-form merging, sentence splitting, vocabulary-growth
gating and download-key count-suffixing are defined exactly once.

Intentional design (capacity / precision-loss, not truncation):
  - Dedup is "precision loss" (merge similar word forms into an existing key),
    not destructive truncation — except handling from the caller for dataset.
  - All vocabulary caps are parameterized and read from magic_numbers so a
    single config source governs growth.
"""

from ai.data_eng.dedup import (
    count_suffix_key,
    download_dedup_key,
    hash_domain_dedup,
    prefix_dedup,
    prefix_overlap,
    semantic_dedup,
    surface_dedup,
)
from ai.data_eng.grow import (
    batch_cap_ok,
    growth_cap_ok,
    growth_gate_batch,
    resolved_max_entries,
)
from ai.data_eng.chunk import (
    split_paragraphs,
    split_sections,
    split_sentence_blocks,
    split_sentences,
)
from ai.data_eng.assemble import (
    decode_slot_budget,
    select_anchored_keys,
)

__all__ = [
    # dedup
    "count_suffix_key",
    "download_dedup_key",
    "hash_domain_dedup",
    "prefix_dedup",
    "semantic_dedup",
    "surface_dedup",
    # grow
    "batch_cap_ok",
    "growth_cap_ok",
    "growth_gate_batch",
    "resolved_max_entries",
    # chunk
    "split_paragraphs",
    "split_sections",
    "split_sentences",
    "split_sentence_blocks",
    # assemble
    "decode_slot_budget",
    "select_anchored_keys",
]