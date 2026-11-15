# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""Contract tests for §71's roster-line intervention.

These pin the parts that must not drift silently: the three edits are matched
(one clause changes, byte and token count preserved), the sign-flip null is the
stated one, the branch precedence is fixed, and a stored verdict re-derives from
its own per-row numbers. No carrier is loaded and nothing is trained.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "probe_pantry_intervene.py"

ACTORS = [
    "Alex",
    "Betty",
    "Chris",
    "David",
    "Elena",
    "Frank",
    "Grace",
    "Hana",
    "Ivan",
    "Judy",
    "Kevin",
    "Lena",
]
COLOURS = ["白色", "紅色", "藍色", "綠色", "灰色", "黑色", "橘色", "紫色"]
LIFT_SEED_TEST = 31


def _load():
    spec = importlib.util.spec_from_file_location("probe_pantry_intervene", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe_pantry_intervene"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _load()


LINE = "今天值班表上寫著：白色是 Hana、紅色是 Grace。"


def _session(session_id: str = "s0", line: str = LINE, actors=("Hana", "Grace")) -> dict:
    return {
        "session_id": session_id,
        "session_meta": {"roster_turn": 1},
        "environment": {"actors": list(actors)},
        "turns": [
            {"turn_id": 0, "user_input": "下午 17:45 點冷萃咖啡放茶水間。"},
            {"turn_id": 1, "user_input": line},
            {"turn_id": 2, "user_input": "清潔阿姨說 18:45 看到白色的圍裙。"},
            {"turn_id": 3, "user_input": "你認為誰是兇手？"},
        ],
    }


# --------------------------------------------------------------------------- #
# parse and render
# --------------------------------------------------------------------------- #
def test_parse_reads_colour_name_pairs(probe):
    assert probe.clauses_of(_session()) == [("白色", "Hana"), ("紅色", "Grace")]


def test_parse_refuses_a_line_that_is_not_the_template(probe):
    with pytest.raises(SystemExit):
        probe.clauses_of(_session(line="Hana 和 Grace 值班。"))


def test_render_round_trips(probe):
    clauses = probe.clauses_of(_session())
    assert probe.render_clauses(clauses) == LINE


# --------------------------------------------------------------------------- #
# the three edits are matched
# --------------------------------------------------------------------------- #
def test_swap_replaces_one_name_with_a_same_length_outsider(probe):
    session = _session()
    edited, target = probe.edit_swap(session, ACTORS)
    before = probe.clauses_of(session)
    after = probe.clauses_of(edited)
    assert len(before) == len(after)
    changed = [index for index in range(len(before)) if before[index] != after[index]]
    assert len(changed) == 1
    index = changed[0]
    assert before[index][0] == after[index][0]  # the colour is untouched
    old, new = before[index][1], after[index][1]
    assert len(old.encode("utf-8")) == len(new.encode("utf-8"))
    assert new not in [name for _, name in before]
    assert target == tuple(sorted([name for _, name in after]))
    assert probe.clause_key(edited) == target


def test_swap_is_deterministic_for_the_same_session(probe):
    session = _session()
    first, first_target = probe.edit_swap(session, ACTORS)
    second, second_target = probe.edit_swap(session, ACTORS)
    assert first == second
    assert first_target == second_target


def test_swap_skips_when_no_same_length_outsider_exists(probe):
    # Hana and Grace are no outsiders at all, so every byte-length class the
    # roster uses is exhausted: the arm is skipped (§71.9), not weakened.
    assert probe.edit_swap(_session(), ["Hana", "Grace"]) is None


def test_swap_uses_the_class_that_still_has_an_outsider(probe):
    # All five 4-byte names are on the roster, but the 5-byte class still has
    # outsiders, so the swap must happen on the 5-byte clause rather than skip.
    line = "今天值班表上寫著：白色是 Alex、紅色是 Hana、藍色是 Ivan、綠色是 Judy、灰色是 Lena、黑色是 Betty。"
    actors = ["Alex", "Hana", "Ivan", "Judy", "Lena", "Betty"]
    session = _session(line=line, actors=actors)
    edited, target = probe.edit_swap(session, ACTORS)
    before = probe.clauses_of(session)
    after = probe.clauses_of(edited)
    changed = [index for index in range(len(before)) if before[index] != after[index]]
    assert len(changed) == 1
    assert before[changed[0]][1] == "Betty"
    assert after[changed[0]][1] not in [name for _, name in before]
    assert len(after[changed[0]][1].encode("utf-8")) == len("Betty".encode("utf-8"))
    assert target == probe.clause_key(edited)


def test_swap_skips_a_roster_that_exhausts_every_length_class(probe):
    line = "今天值班表上寫著：白色是 Alex、紅色是 Hana、藍色是 Ivan、綠色是 Judy、灰色是 Lena。"
    session = _session(line=line, actors=["Alex", "Hana", "Ivan", "Judy", "Lena"])
    assert probe.edit_swap(session, ACTORS) is None


def test_reverse_keeps_the_set_and_reverses_the_order(probe):
    session = _session()
    edited = probe.edit_reverse(session)
    assert probe.clause_key(edited) == probe.clause_key(session)
    assert [name for _, name in probe.clauses_of(edited)] == ["Grace", "Hana"]
    assert probe.roster_key(edited) == probe.roster_key(session)


def test_colour_edit_keeps_names_and_order_and_uses_a_new_colour(probe):
    session = _session()
    edited = probe.edit_colour(session, COLOURS)
    before = probe.clauses_of(session)
    after = probe.clauses_of(edited)
    assert [name for _, name in after] == [name for _, name in before]
    changed = [index for index in range(len(before)) if before[index][0] != after[index][0]]
    assert len(changed) == 1
    assert after[changed[0]][0] not in [colour for colour, _ in before]
    assert len(after[changed[0]][0]) == len(before[changed[0]][0])


def test_every_edit_preserves_the_other_turns_and_the_line_length(probe):
    session = _session()
    edited_versions = [
        probe.edit_swap(session, ACTORS)[0],
        probe.edit_reverse(session),
        probe.edit_colour(session, COLOURS),
    ]
    for edited in edited_versions:
        for index, turn in enumerate(edited["turns"]):
            if index == session["session_meta"]["roster_turn"]:
                continue
            assert turn == session["turns"][index]
        turn = session["session_meta"]["roster_turn"]
        assert len(edited["turns"][turn]["user_input"].encode("utf-8")) == len(
            session["turns"][turn]["user_input"].encode("utf-8")
        )


def test_edits_keep_the_token_count(probe):
    session = _session()
    original = session["turns"][1]["user_input"]
    for edited in (
        probe.edit_swap(session, ACTORS)[0],
        probe.edit_reverse(session),
        probe.edit_colour(session, COLOURS),
    ):
        assert len(edited["turns"][1]["user_input"]) == len(original)


# --------------------------------------------------------------------------- #
# distances and the null
# --------------------------------------------------------------------------- #
def test_movement_is_zero_for_identical_and_two_for_opposite(probe):
    same = torch.tensor([[1.0, 0.0], [0.0, 1.0]])
    assert probe.movement(torch, same, same) == [0.0, 0.0]
    opposite = torch.tensor([[-1.0, 0.0], [0.0, -1.0]])
    assert probe.movement(torch, same, opposite) == [2.0, 2.0]


def test_sign_flip_finds_a_positive_mean_and_not_a_symmetric_one(probe):
    positive = probe.sign_flip([0.2] * 40, permutations=199, seed=3)
    assert positive["mean"] == pytest.approx(0.2)
    assert positive["p_value"] == pytest.approx(1.0 / 200.0)

    symmetric = probe.sign_flip([0.2, -0.2] * 20, permutations=199, seed=3)
    assert symmetric["mean"] == pytest.approx(0.0)
    assert symmetric["p_value"] > 0.4


def test_sign_flip_is_reproducible(probe):
    differences = [0.3, 0.1, -0.05, 0.2, 0.05]
    first = probe.sign_flip(differences, permutations=99, seed=7)
    second = probe.sign_flip(differences, permutations=99, seed=7)
    assert first == second


# --------------------------------------------------------------------------- #
# the neighbourhood and retention
# --------------------------------------------------------------------------- #
def _clusters(per_cluster: int = 20):
    generator = torch.Generator().manual_seed(5)
    left = torch.randn(per_cluster, 6, generator=generator) * 0.02
    left[:, 0] += 3.0
    right = torch.randn(per_cluster, 6, generator=generator) * 0.02
    right[:, 1] += 3.0
    reference = torch.cat([left, right], dim=0)
    keys = [("a", "b")] * per_cluster + [("c", "d")] * per_cluster
    ids = [f"r{index}" for index in range(2 * per_cluster)]
    edited = left.clone() + torch.randn(per_cluster, 6, generator=generator) * 0.01
    return reference, keys, ids, edited


def test_neighbourhood_rewards_landing_on_the_edited_roster(probe):
    reference, keys, ids, edited = _clusters()
    rows = len(edited)
    block = probe.neighbourhood(
        torch,
        edited,
        [("a", "b")] * rows,
        [("c", "d")] * rows,
        reference,
        keys,
        ids,
        [f"e{index}" for index in range(rows)],
        permutations=99,
        seed=11,
    )
    assert block["mean"] > 0.0
    assert block["p_value"] == pytest.approx(1.0 / 100.0)
    assert block["top1_rate"] == 1.0
    assert block["rows_compared"] == rows


def test_neighbourhood_finds_nothing_when_the_edit_lands_elsewhere(probe):
    reference, keys, ids, edited = _clusters()
    rows = len(edited)
    block = probe.neighbourhood(
        torch,
        edited,
        [("c", "d")] * rows,  # claims the right cluster is the target for a left state
        [("a", "b")] * rows,
        reference,
        keys,
        ids,
        [f"e{index}" for index in range(rows)],
        permutations=99,
        seed=11,
    )
    assert block["mean"] < 0.0
    assert block["p_value"] > 0.9


def test_neighbourhood_counts_rows_without_a_reference(probe):
    reference, keys, ids, edited = _clusters()
    rows = len(edited)
    block = probe.neighbourhood(
        torch,
        edited,
        [("x", "y")] * rows,
        [("c", "d")] * rows,
        reference,
        keys,
        ids,
        [f"e{index}" for index in range(rows)],
        permutations=99,
        seed=11,
    )
    assert block["rows_compared"] == 0
    assert block["rows_missing_reference"] == rows


def test_retention_excludes_the_edited_session_itself(probe):
    reference, keys, ids, edited = _clusters()
    rows = len(edited)
    own = [("a", "b")] * rows
    with_self = probe.retention(
        torch, edited, own, reference, keys, ids, [f"r{index}" for index in range(rows)]
    )
    without_self = probe.retention(
        torch, edited, own, reference, keys, ids, [f"e{index}" for index in range(rows)]
    )
    assert with_self["n_rows"] == rows
    assert without_self["n_rows"] == rows
    assert with_self["per_row"] != without_self["per_row"]


# --------------------------------------------------------------------------- #
# gates and the fork
# --------------------------------------------------------------------------- #
def _edit_block(mean: float, rows: int = 200) -> dict:
    return {"mean": mean, "per_row": [mean] * rows, "n_rows": rows}


def _diff(probe, value: float, *, rows: int = 120, seed: int = 1) -> dict:
    """A block whose stored p_value really is the sign flip of its own rows."""
    return probe.sign_flip([value] * rows, permutations=999, seed=seed)


def _report(
    probe,
    *,
    movement: float = 0.05,
    lift_mean: float = 0.02,
    lift_p: float = 0.001,
    rows: int = 120,
    reverse: float = 0.0,
    colour: float = 0.0,
    ok: bool = True,
) -> dict:
    return {
        "k": 2,
        "edits": {},
        "movement": {
            "swap": _edit_block(movement),
            "reverse": _edit_block(movement),
            "colour": _edit_block(movement),
        },
        "lift": {
            "mean": lift_mean,
            "p_value": lift_p,
            "n_rows": rows,
            "rows_compared": rows,
            "rows_missing_reference": 0,
            "top1_rate": 0.3,
            "chance": 0.015,
            "distinct_reference_rosters": 66,
            "permutations": 999,
            "seed": 1,
            "differences": [lift_mean] * rows,
        },
        "retention": {
            "reverse": {"difference": _diff(probe, reverse, rows=rows, seed=LIFT_SEED_TEST)},
            "colour": {"difference": _diff(probe, colour, rows=rows, seed=LIFT_SEED_TEST + 1)},
        },
        "instrument": {
            "carrier_unchanged": ok,
            "checkpoint_unchanged": ok,
            "determinism_ok": ok,
            "texts_changed": ok,
            "token_counts_matched": ok,
            "swap_rows": 200,
            "swap_skipped": 0,
        },
    }


def test_gates_read_the_registered_floors(probe):
    gate = probe.gates(_report(probe))
    assert gate["J0_instrument"]["pass"] is True
    assert gate["J1_edit_moves_the_state"]["pass"] is True
    assert gate["J2_swap_lands_on_the_edited_roster"]["pass"] is True
    assert gate["J3_order_and_colour_keep_the_roster"]["pass"] is True


def test_branch_takes_the_first_matching_reading(probe):
    assert probe.branch(probe.gates(_report(probe)))["id"] == "J1-roster-line-sets-the-roster"

    broken = _report(probe, ok=False)
    assert probe.branch(probe.gates(broken))["id"] == "J0-instrument"

    still = _report(probe, movement=1e-9)
    assert probe.branch(probe.gates(still))["id"] == "J3-state-ignores-the-turn-text"

    underpowered = _report(probe, rows=10)
    assert probe.branch(probe.gates(underpowered))["id"] == "J4-neighbourhood-underpowered"

    surface = _report(probe, reverse=-0.2)
    assert probe.branch(probe.gates(surface))["id"] == "J2-the-trace-is-the-line-not-the-roster"

    no_lift = _report(probe, lift_mean=-0.01, lift_p=0.9)
    assert probe.branch(probe.gates(no_lift))["id"] == "J2-the-trace-is-the-line-not-the-roster"


def test_zero_swap_rows_fails_the_instrument_gate(probe):
    report = _report(probe)
    for name in ("swap",):
        report["movement"][name] = {"mean": None, "per_row": [], "n_rows": 0}
    report["instrument"]["swap_rows"] = 0
    report["instrument"]["swap_skipped"] = 200
    gate = probe.gates(report)
    assert gate["J0_instrument"]["pass"] is False
    assert gate["J0_instrument"]["swap_rows"] == 0
    assert probe.branch(gate)["id"] == "J0-instrument"


def test_registered_constants_are_pinned(probe):
    assert probe.EDIT_MOVEMENT_FLOOR == 1e-3
    assert probe.LIFT_ALPHA == 0.001
    assert probe.LIFT_PERMUTATIONS == 1000
    assert probe.LIFT_SEED == 20261124
    assert probe.RETENTION_FLOOR == -0.01
    assert probe.MIN_LIFT_ROWS == 50
    assert probe.ROSTER_PREFIX == "今天值班表上寫著："


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def test_check_accepts_a_consistent_verdict(probe, tmp_path):
    report = _report(probe)
    report["gates"] = probe.gates(report)
    report["branch"] = probe.branch(report["gates"])
    report["instrument_ok"] = True
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    assert probe.check(path) == []


def test_check_rejects_an_invented_p_value(probe, tmp_path):
    report = _report(probe)
    report["gates"] = probe.gates(report)
    report["branch"] = probe.branch(report["gates"])
    report["instrument_ok"] = True
    report["lift"]["p_value"] = 0.5
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    problems = probe.check(path)
    assert any("does not follow from its own differences" in item for item in problems)


def test_check_accepts_a_recorded_zero_family(probe, tmp_path):
    report = _report(probe)
    report["movement"]["swap"] = {"mean": None, "per_row": [], "n_rows": 0}
    report["instrument"]["swap_rows"] = 0
    report["instrument"]["swap_skipped"] = 200
    report["gates"] = probe.gates(report)
    report["branch"] = probe.branch(report["gates"])
    report["instrument_ok"] = False
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    problems = probe.check(path)
    assert not any("movement.swap" in item for item in problems)
    assert any("instrument_ok is false" in item for item in problems)


def test_check_rejects_a_stale_gate(probe, tmp_path):
    report = _report(probe)
    report["gates"] = probe.gates(report)
    report["branch"] = probe.branch(report["gates"])
    report["instrument_ok"] = True
    report["movement"]["swap"]["mean"] = 1e-9  # now below the movement floor
    report["movement"]["swap"]["per_row"] = [1e-9] * 200
    path = tmp_path / "verdict.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    problems = probe.check(path)
    assert any("J1_edit_moves_the_state.pass is stale" in item for item in problems)
