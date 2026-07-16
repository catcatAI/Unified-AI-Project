# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [C] [L0]
# =============================================================================
"""
Regression tests for GARDEN TensorSNNCore memory bounds (max_vocab eviction).

Verifies the SNN never grows its [V, V] matrix unbounded: once the number of
registered neurons reaches ``max_vocab``, the least-recently-used neurons are
evicted in a single compaction so training can still ingest every sample
without truncating the input dataset or blowing up V**2 memory.
"""

import time

import pytest

from ai.garden.snn_core import TensorSNNCore


class TestSNNMemoryBounds:
    def test_vocab_stays_bounded_under_eviction(self):
        core = TensorSNNCore(max_vocab=2000)
        # Register far more distinct keys than the budget allows.
        n = 8000
        for i in range(n):
            core.add_relation(f"k{i}", f"v{i}", weight=0.5)
        stats = core.get_stats()
        # vocab must never exceed the budget (plus the ~10% slack during eviction).
        assert stats["vocab_size"] <= int(2000 * 1.05), stats["vocab_size"]
        assert stats["total_evictions"] > 0
        # The matrix shape must equal vocab_size (no stale oversized allocation).
        assert stats["weight_matrix_shape"] == [stats["vocab_size"], stats["vocab_size"]]

    def test_forward_works_after_eviction(self):
        core = TensorSNNCore(max_vocab=500)
        for i in range(2000):
            core.add_relation(f"a{i}", f"b{i}", weight=0.8)
        # A still-registered key must forward without shape/broadcast errors.
        core.add_relation("probe", "target", weight=0.9)
        result = core.forward(["probe"])
        assert isinstance(result, dict)

    def test_eviction_is_bounded_time(self):
        core = TensorSNNCore(max_vocab=2000)
        t0 = time.time()
        for i in range(8000):
            core.add_relation(f"x{i}", f"y{i}", weight=0.5)
        elapsed = time.time() - t0
        # 8000 registers with eviction must complete in well under a minute.
        assert elapsed < 60.0, elapsed
