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

    def test_counter_tracks_forward_created_connections(self):
        """forward()/_apply_relation_activation() creates connections on unseen
        key pairs; the running counter must reflect them so eviction triggers
        correctly during training (regression for counter drift)."""
        core = _fresh_core(max_connections=0)
        before = core._conn_count
        # Simulate forward() activating a brand-new pair in the mapping group.
        core._apply_relation_activation("newx", "newy", RelationType.MAPPING, 0.7)
        after = core._conn_count
        assert after > before, "forward-created connections must increment counter"
        assert after == core._count_connections(), (
            after,
            core._count_connections(),
        )
        # A second call on the same pair must NOT double-count.
        core._apply_relation_activation("newx", "newy", RelationType.MAPPING, 0.7)
        assert core._conn_count == after, "existing pair must not re-increment"
        assert core._conn_count == core._count_connections()

    def test_add_directed_enforces_budget(self):
        """Regression: add_directed() (the sequence-trainer path) must enforce
        max_connections like adjust_connection() does.  Previously it grew the
        graph past the 200k cap with no eviction."""
        core = _fresh_core(max_connections=100)
        for i in range(2000):
            core.add_directed(f"s{i % 500}", f"t{i % 500}", weight=0.5)
        assert core._conn_count <= 100, core._conn_count
        assert core._conn_count == core._count_connections(), (
            core._conn_count,
            core._count_connections(),
        )

    def test_adjust_connection_does_not_pollute_other_groups(self):
        """Regression: adjust_connection() must update only the group where the
        connection exists.  The any-group existence check + every-group write
        polluted other relation types (a mapping weight fired as a synonym)."""
        core = _fresh_core(max_connections=1000)
        # k1-k2 connected ONLY in the synonym group.
        core.add_relation("k1", RelationType.SYNONYM, "k2", weight=0.5)
        assert "k2" in core.groups["synonym"].neurons["k1"].connections
        # k1 and k2 also exist as SEPARATE Neuron objects in mapping, unconnected.
        from ai.ed3n.core_network import Neuron

        core.groups["mapping"].add_neuron(Neuron(key="k1", group_type="mapping"))
        core.groups["mapping"].add_neuron(Neuron(key="k2", group_type="mapping"))
        core.adjust_connection("k1", "k2", 0.2)
        assert core.groups["synonym"].neurons["k1"].connections["k2"] == 0.7
        assert "k2" not in core.groups["mapping"].neurons["k1"].connections, (
            "mapping group must not gain a spurious connection"
        )

    def test_add_directed_fresh_pair_counts_one(self):
        """add_directed() on a fresh pair creates a single one-sided edge
        (no reverse-decay edge since old==0).  Regression: reverse_new was
        referenced unbound when old==0 (UnboundLocalError)."""
        core = _fresh_core(max_connections=1000)
        core.add_directed("s0", "t0", weight=0.5)
        assert "t0" in core.groups["mapping"].neurons["s0"].connections
        assert "s0" not in core.groups["mapping"].neurons["t0"].connections, (
            "fresh directed edge must NOT create a reverse edge"
        )
        assert core._conn_count == core._count_connections() == 1

    def test_from_dict_recomputes_conn_count(self):
        """Regression: CoreNetwork.from_dict() must recompute _conn_count from the
        restored graph. A stale 0 counter would make the memory-budget eviction
        logic believe the loaded network is empty (never evict) and let further
        training grow the counter from 0, defeating the cap."""
        core = _fresh_core(max_connections=0)
        for i in range(500):
            core.add_relation(f"a{i}", RelationType.MAPPING, f"b{i}", weight=0.5)
        assert core._conn_count == 1000
        restored = CoreNetwork.from_dict(core.to_dict())
        assert restored._conn_count == 1000, (
            "from_dict must recompute the connection counter",
            restored._conn_count,
        )
        assert restored._conn_count == restored._count_connections()

