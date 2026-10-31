"""Contract tests for the MVE-1 emergence-boundary instrument (CORE_GAP §十一.4).

Claims pinned here (no teaching to the test):

1. the gold family is exactly the four ``dt`` rungs of the contract §5
   operator, monotone toward the target, mode carried;
2. grading is single-gold exact (dt rides the input line since round 4,
   ``gold == family[rung]``) and the rotation control is a derangement — no
   row can ever be graded against its own gold;
3. the gate numbers are the registered threshold (≥5/200 and ≤1/200);
4. the set is deterministic, leak-free, in-window (192 tokens), and its
   prompt is byte-identical to the training pair's prefix;
5. ``generate_al_dataset.py --holdout-cells`` drops exactly the declared
   cells, keeps the rng stream, and is a no-op when off (byte-identical
   defaults, so existing ``--check`` runs keep passing).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "probe_emergence_boundary.py"
GEN_SCRIPT = REPO_ROOT / "scripts" / "generate_al_dataset.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _load("probe_emergence_boundary_test", SCRIPT)


@pytest.fixture(scope="module")
def gen():
    return _load("generate_al_dataset_mve_test", GEN_SCRIPT)


# -- 1. the family is the contract operator, four rungs --------------------


def test_family_is_the_four_contract_rungs(probe, gen):
    baseline, targets, _ = gen._pilot_tables()
    intent = sorted(targets)[0]
    # state pinned to the wall *opposite* the target: every rung moves a
    # visible, distinct distance at 2dp, so four distinct golds are guaranteed
    state = {
        f: (gen._RANGE[f][0] if targets[intent][f] > 0 else gen._RANGE[f][1]) for f in gen._FIELDS
    }
    state["routing_mode"] = "neutral"
    golds = probe.family_golds(state, intent, baseline, targets)
    assert len(golds) == 4 == len(gen._DT_LADDER)
    assert len(set(golds)) == 4, "rungs must be distinguishable at 2dp"
    for gold in golds:
        assert "<al_out>" in gold
        assert "mode=neutral" in gold
        assert f"intent={intent}" in gold
    # monotone approach to the target: each larger dt lands no farther away
    short = {"valence": "v", "arousal": "a", "dominance": "d"}
    target = targets[intent]
    for field in gen._FIELDS:
        key = short.get(field, field)
        values = []
        for gold in golds:
            tok = next(t for t in gold.split() if t.startswith(key + "="))
            values.append(float(tok.split("=", 1)[1]))
        distances = [abs(v - target[field]) for v in values]
        # larger dt -> smaller k -> lands *closer* to the target (descending)
        assert distances == sorted(distances, reverse=True), f"{field} not monotone in dt"


def test_reference_mode_is_never_the_holdout_mode(probe):
    assert probe._ref_mode("conservative") == "exploratory"
    assert probe._ref_mode("exploratory") == "neutral"
    for mode in probe.gen.MVE1_HOLDOUT_CELLS.values():
        assert probe._ref_mode(mode) != mode


# -- 2/3. grading and gate -------------------------------------------------


def test_grade_is_family_exact(probe):
    golds = ["<al_out> v=0.10", "<al_out> v=0.20", "<al_out> v=0.30", "<al_out> v=0.40"]
    assert probe.grade("  <al_out> v=0.30  ", golds) == (True, 2)
    assert probe.grade("<al_out> v=0.31", golds) == (False, None)
    assert probe.grade("", golds) == (False, None)
    assert probe.grade("<al_out> v=0.30 extra", golds) == (False, None)


def test_rotation_control_is_a_derangement(probe):
    rows = [{"sample_id": f"mve1h_{i:04d}"} for i in range(5)]
    rows += [{"sample_id": f"mve1r_{i:04d}"} for i in range(3)]
    rot = probe.rotation_index_map(rows)
    for i, j in enumerate(rot):
        assert j != i, "the control must never grade a row against its own gold"
        assert 0 <= j < len(rows)
        # a rotation must stay inside its own set (holdout vs reference)
        assert probe._set_label(rows[i]) == probe._set_label(rows[j])
    # a per-set rotation is a cycle: every gold in the set is used exactly once
    for label in ("holdout", "reference"):
        idxs = [i for i, e in enumerate(rows) if probe._set_label(e) == label]
        assert sorted(rot[i] for i in idxs) == idxs


def test_gate_matches_the_registered_threshold(probe):
    assert probe.gate(5, 1)["pass"] is True  # the registered MVE-1 numbers
    assert probe.gate(4, 1)["pass"] is False  # 4/200 < 5/200
    assert probe.gate(5, 2)["pass"] is False  # control too high
    assert probe.gate(0, 0)["pass"] is False  # every baseline so far
    g = probe.gate(5, 1)
    assert (g["n"], g["family_min"], g["rotation_max"]) == (200, 5, 1)


def test_pair_fit_is_the_exact_training_window(probe):
    prompt = " ".join(f"w{i}" for i in range(10))
    block = "v=0.00 a=0.00"
    budget = 3 + probe._atoms(prompt) + probe._atoms(block)
    assert probe.pair_fits(prompt, block, budget) is True
    assert probe.pair_fits(prompt, block, budget - 1) is False
    # a digit-heavy block costs one atom per digit (tokenize splits numbers)
    assert probe._atoms("v=-0.35") > probe._atoms("v=0.3")


# -- 4. the set ------------------------------------------------------------


@pytest.fixture(scope="module")
def small_set(probe):
    cells = {"unknown": "conservative", "knowledge_query": "neutral"}
    return probe.build(
        total=10,
        seed=5,
        skip=10000,
        window=2000,
        cells=cells,
        max_len=192,
        min_per_cell=4,
    )


def test_small_set_is_complete_and_in_window(probe, small_set, gen):
    assert small_set["total"] == 10
    assert small_set["reference_total"] == 10
    cells = small_set["provenance"]["cells"]
    for kind, rows in (("holdout", small_set["holdout"]), ("reference", small_set["reference"])):
        for entry in rows:
            assert len(entry["family"]) == 4
            expect_mode = (
                cells[entry["intent"]]
                if kind == "holdout"
                else probe._ref_mode(cells[entry["intent"]])
            )
            assert entry["mode"] == expect_mode
            assert entry["cell"] == f"{entry['intent']}:{entry['mode']}"
            # single-gold: the graded target is exactly the rung the prompt names
            assert entry["gold"] == entry["family"][entry["rung"]]
            assert entry["dt"] == gen._DT_LADDER[entry["rung"]]
            assert probe.pair_fits(entry["prompt"], entry["gold"], 192), entry["sample_id"]


def test_prompt_is_the_training_pair_prefix(probe, small_set, gen):
    """Byte-identical to prepare_ai_al_training_data's pair, response given.

    The input line carries dt (round-4 schema), serialised through the very
    same _state_line the trainer's pairs go through — one code path, so the
    probe cannot drift from the training format.
    """
    for entry in small_set["holdout"]:
        expected_in = (
            probe.prep._state_line(entry["state_in"], entry["intent"], "in", dt=entry["dt"])
            + " | "
            + entry["text"]
        )
        expected = (expected_in + "\n" + entry["response"]).strip()
        assert entry["prompt"] == expected
        assert f"dt={entry['dt']:.2f}" in entry["prompt"]


def test_rung_slots_cycle_so_every_cell_is_balanced(probe, small_set, gen):
    """The rung comes from the append position, not a fresh draw — adding dt
    cannot touch the rng stream, and cycles give each cell an even rung mix."""
    ladder = gen._DT_LADDER
    for kind in ("holdout", "reference"):
        rows = small_set[kind]
        assert [e["rung"] for e in rows] == [i % len(ladder) for i in range(len(rows))]
        for entry in rows:
            state_line = entry["prompt"].split(" | ", 1)[0]
            assert state_line.startswith("<al_in> ")
            assert f"dt={entry['dt']:.2f}" in state_line
            # the output side is a state, never a timestep
            assert " dt=" not in entry["gold"]


def test_set_is_deterministic_and_leak_free(probe, gen, small_set):
    again = probe.build(
        total=10,
        seed=5,
        skip=10000,
        window=2000,
        cells=small_set["provenance"]["cells"],
        min_per_cell=4,
    )
    assert json.dumps(again, sort_keys=True) == json.dumps(small_set, sort_keys=True)
    assert small_set["provenance"]["overlap_with_training"] == 0
    seen = set()
    for entry in small_set["holdout"]:
        assert entry["sample_id"] not in seen
        seen.add(entry["sample_id"])


def test_underfilled_cell_fails_loudly(probe, gen):
    with pytest.raises(SystemExit):
        # a window far too small to fill the per-cell quota
        probe.build(total=10, seed=5, skip=10000, window=10, min_per_cell=4)


# -- 5. the carve ----------------------------------------------------------


def test_carve_drops_exactly_the_declared_cells(gen):
    cells = dict(gen.MVE1_HOLDOUT_CELLS)
    plain = gen.build(rows=400, seed=7)
    carved = gen.build(rows=400, seed=7, holdout_cells=cells)
    expected = [
        ex
        for ex in plain["examples"]
        if cells.get(ex["intent"]) != ex["al_state_in"]["routing_mode"]
    ]
    assert carved["examples"] == expected, "carve must drop only the cells, in place"
    dropped = len(plain["examples"]) - len(carved["examples"])
    assert dropped > 0, "the sample must actually contain held-out cell rows"
    assert carved["provenance"]["holdout_carved"] == dropped
    assert carved["provenance"]["holdout_cells"] == cells


def test_carve_off_leaves_defaults_byte_identical(gen):
    plain = gen.build(rows=60, seed=7)
    assert "holdout_cells" not in plain["provenance"]
    assert "holdout_carved" not in plain["provenance"]
    # --expose-dt is off by default for the same byte-identity reason
    assert "expose_dt" not in plain["provenance"]
    assert all("dt" not in ex for ex in plain["examples"])
    # and the flag parses to a plain dict (empty spec -> off)
    assert gen._parse_holdout_cells("") == {}
    assert gen._parse_holdout_cells("unknown:conservative, knowledge_query:neutral") == {
        "unknown": "conservative",
        "knowledge_query": "neutral",
    }
    with pytest.raises(SystemExit):
        gen._parse_holdout_cells("unknown:sideways")


def test_holdout_cells_declared_in_the_generator(gen):
    cells = gen.MVE1_HOLDOUT_CELLS
    assert "farewell" not in cells  # 16 corpus rows cannot fill a cell
    for intent, mode in cells.items():
        assert mode in gen._MODES
        assert intent in {
            gen._intent_of(s) for s in ("joke", "hello", "why x", "calculate 2+2", "hi")
        }
    # every primitive survives the carve: each intent keeps two modes, and
    # the carve covers all three modes (breadth across the composition space)
    for intent in cells:
        remaining = [m for m in gen._MODES if m != cells[intent]]
        assert len(remaining) == 2
    assert set(cells.values()) == set(gen._MODES)
