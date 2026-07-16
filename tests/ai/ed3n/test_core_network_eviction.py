# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [C] [L0]
# =============================================================================
"""
Regression tests for ED3N CoreNetwork connection-cap eviction.

Verifies the connection count stays bounded by ``max_connections`` while still
training on every sample (we shed weakest connections, never truncate the
input dataset). Also confirms the running connection counter stays accurate.
"""

import time

import pytest

from ai.ed3n.core_network import CoreNetwork, RelationGroup, RelationType


def _fresh_core(max_connections: int) -> CoreNetwork:
    core = CoreNetwork.__new__(CoreNetwork)
    core._synonym_group = RelationGroup("synonym")
    core._mapping_group = RelationGroup("mapping")
    core._analogy_group = RelationGroup("analogy")
    core.groups = {
        "synonym": core._synonym_group,
        "mapping": core._mapping_group,
        "analogy": core._analogy_group,
    }
    core.max_connections = max_connections
    core._conn_count = 0
    return core


class TestCoreNetworkEviction:
    def test_connections_bounded_under_budget(self):
        core = _fresh_core(max_connections=500)
        for i in range(20000):
            core.add_relation(f"a{i % 2000}", RelationType.MAPPING, f"b{i % 2000}", weight=0.5)
            core._evict_weakest()
        assert core._conn_count <= 500, core._conn_count
        # Counter must agree with an actual recount.
        assert core._conn_count == core._count_connections(), (
            core._conn_count,
            core._count_connections(),
        )

    def test_eviction_is_bounded_time(self):
        core = _fresh_core(max_connections=500)
        t0 = time.time()
        for i in range(20000):
            core.add_relation(f"a{i % 2000}", RelationType.MAPPING, f"b{i % 2000}", weight=0.5)
            core._evict_weakest()
        elapsed = time.time() - t0
        assert elapsed < 60.0, elapsed

    def test_unbounded_when_budget_zero(self):
        core = _fresh_core(max_connections=0)
        for i in range(2000):
            core.add_relation(f"a{i}", RelationType.MAPPING, f"b{i}", weight=0.5)
        assert core._conn_count == 4000, core._conn_count
