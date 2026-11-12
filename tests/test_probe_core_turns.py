# ANGELA-MATRIX: L3 [βγδ] [A] [L2]
"""The P5 turn-volume probe's own gates, tested without running a session.

The probe measures a *carrier*, so the interesting failures are the silent ones:
a turn that was never carried, a version that did not move (an update lost to a
second writer), or a stratum quietly skipped. Each of those is a case below —
the summary must fail, not print a smaller number.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "probe_core_turns.py"


@pytest.fixture(scope="module")
def probe():
    spec = importlib.util.spec_from_file_location("probe_core_turns_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    # The gate reads the standard set's sizes; pin them so the test does not
    # depend on how many items the standard set happens to hold today.
    module._STANDARD_SIZES.clear()
    module._STANDARD_SIZES.update(
        {"state": 324, "multi": 80, "claim": 108, "qa": 492, "dialogue": 100}
    )
    return module


def _record(turn: int, stratum: str, session: str, *, source: str = "core", **over) -> dict:
    payload = {
        "turn": turn,
        "stratum": stratum,
        "session": session,
        "state_source": source,
        "ticks": turn,
        "state_version": turn + 1,
        "dt_s": 1.0,
        "created": turn == 0,
        "state_path": f"/tmp/{session}",
    }
    payload.update(over)
    return payload


def _clean_run(probe, turns_per_stratum: int = 200) -> list:
    records = []
    turn = 0
    for stratum in probe.REQUIRED_STRATA:
        for index in range(turns_per_stratum):
            records.append(_record(turn, stratum, f"core-turns-{stratum}", state_version=index + 1))
            turn += 1
    return records


def test_the_gate_passes_a_clean_run(probe) -> None:
    records = _clean_run(probe)
    summary = probe.summarise(records, target=len(records))

    assert summary["all_pass"] is True
    assert summary["checks"] == {
        "turns": True,
        "no_refusals": True,
        "versions_strictly_increase": True,
        "every_stratum_recorded": True,
        "every_turn_carried_by_the_core": True,
    }
    assert set(summary["by_stratum"]) == set(probe.REQUIRED_STRATA)


def test_a_lost_update_fails_the_gate(probe) -> None:
    """Two writers reading the same version is exactly what R3 prevents."""
    records = _clean_run(probe)
    records[4]["state_version"] = records[3]["state_version"]

    summary = probe.summarise(records, target=len(records))

    assert summary["checks"]["versions_strictly_increase"] is False
    assert summary["all_pass"] is False


def test_a_refused_turn_fails_the_gate(probe) -> None:
    records = _clean_run(probe)
    records[2]["state_source"] = "none"  # the core refused; the prompt carried it

    summary = probe.summarise(records, target=len(records))

    assert summary["checks"]["no_refusals"] is False
    assert summary["checks"]["every_turn_carried_by_the_core"] is False
    assert summary["all_pass"] is False


def test_a_skipped_stratum_fails_the_gate(probe) -> None:
    records = [r for r in _clean_run(probe) if r["stratum"] != "claim"]

    summary = probe.summarise(records, target=len(records))

    assert summary["checks"]["every_stratum_recorded"] is False


def test_short_targets_are_not_padded(probe) -> None:
    """A run under the target must say so rather than round up."""
    records = _clean_run(probe, turns_per_stratum=3)
    summary = probe.summarise(records, target=2000)

    assert summary["checks"]["turns"] is False
    assert summary["turns"] == len(records) == 15


def test_the_order_is_whole_passes_so_every_stratum_is_reached(probe) -> None:
    kinds = {
        "state": [object() for _ in range(324)],
        "multi": [object() for _ in range(80)],
        "claim": [object() for _ in range(108)],
        "qa": [object() for _ in range(492)],
        "dialogue": [object() for _ in range(100)],
    }

    order = probe.arrange(kinds, 2000)

    # Whole passes: never a truncated tail that starves whichever stratum lands
    # last, and never fewer turns than the target claims.
    assert len(order) == 1104 * 2
    counts = {}
    for kind, _ in order:
        counts[kind] = counts.get(kind, 0) + 1
    assert counts == {"state": 648, "multi": 160, "claim": 216, "qa": 984, "dialogue": 200}
    # Interleaved, not five blocks of one kind.
    assert len({kind for kind, _ in order[:10]}) > 1


def test_the_order_is_reproducible_and_covers_each_item_once_per_pass(probe) -> None:
    kinds = {"qa": ["q0", "q1", "q2"], "state": ["s0", "s1"]}

    first = probe.arrange(kinds, 10, seed=3)
    second = probe.arrange(kinds, 10, seed=3)
    other = probe.arrange(kinds, 10, seed=4)

    assert first == second
    assert first != other
    assert len(first) == 10
    assert sorted(item for _, item in first) == sorted(list(kinds["qa"] + kinds["state"]) * 2)


def test_strata_groups_by_kind(probe) -> None:
    class Item:
        def __init__(self, kind: str) -> None:
            self.kind = kind

    grouped = probe.strata([Item("qa"), Item("state"), Item("qa")])

    assert {k: len(v) for k, v in grouped.items()} == {"qa": 2, "state": 1}
