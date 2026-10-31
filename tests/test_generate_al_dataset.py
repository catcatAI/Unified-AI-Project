"""Contract tests for the round-1 AL data generator (no teaching to the test).

The generator's whole claim is that it does *not* invent AL dynamics: the
transition is the contract's operator (``al-engine-contract.md`` §5), the
targets are fitted to the 10 hand-written pilot rows, and the routing mode is
carried over because all 10 pilot rows keep it. These tests pin each of those
claims, plus the three data gates (range, mode, benchmark leakage).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "generate_al_dataset.py"
PILOT = REPO_ROOT / "apps" / "backend" / "data" / "processed" / "ai_al_pilot_dataset.json"


def _load():
    spec = importlib.util.spec_from_file_location("generate_al_dataset_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load()


def test_pilot_keeps_its_mode():
    """The mode-carry rule is an observation, not a choice."""
    rows = json.loads(PILOT.read_text(encoding="utf-8"))["examples"]
    assert rows, "the pilot dataset must not be empty"
    assert all(r["al_state_in"]["routing_mode"] == r["al_state_out"]["routing_mode"] for r in rows)


def test_target_table_is_fitted_from_the_pilot(gen):
    baseline, targets, n_rows = gen._pilot_tables()
    assert n_rows == 10
    assert set(baseline) == set(gen._FIELDS)
    assert len(targets) == n_rows  # one target per pilot intent row
    assert all(set(t) == set(gen._FIELDS) for t in targets.values())


def test_transition_relaxes_toward_the_target(gen):
    state = {f: 0.0 for f in gen._FIELDS}
    target = {f: 1.0 for f in gen._FIELDS}
    near = gen.transition(state, target, dt=0.0)
    far = gen.transition(state, target, dt=4.0)
    # dt=0 must be the identity; a larger dt must land closer to the target
    assert all(abs(near[f] - 0.0) < 1e-6 for f in gen._FIELDS)
    assert all(abs(far[f] - 1.0) < abs(0.0 - 1.0) for f in gen._FIELDS)
    # and monotone in dt: no field may move away from the target
    steps = [gen.transition(state, target, dt=d) for d in (0.25, 0.5, 1.0, 2.0)]
    for f in gen._FIELDS:
        values = [s[f] for s in steps]
        assert values == sorted(values), f"{f} does not relax monotonically"


def test_transition_never_leaves_the_legal_range(gen):
    """Clamping is per field: push every field to both walls of its range."""
    for field, (lo, hi) in gen._RANGE.items():
        for wall in (lo, hi):
            state = {f: 0.5 for f in gen._FIELDS}
            state[field] = wall
            target = {f: 0.5 for f in gen._FIELDS}
            target[field] = -wall  # pull hard in the opposite direction
            out = gen.transition(state, target, dt=0.01)
            for f in gen._FIELDS:
                glo, ghi = gen._RANGE[f]
                assert glo <= out[f] <= ghi, f"{f} left its range: {out[f]}"


def test_build_is_deterministic_under_a_seed(gen):
    first = gen.build(rows=30, seed=7)
    second = gen.build(rows=30, seed=7)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert gen.build(rows=30, seed=8) != first


def test_generated_rows_pass_the_gates(gen):
    built = gen.build(rows=60, seed=7)
    bench = gen._benchmark_norms()
    # core_train was already leak-filtered; this re-check must agree with it
    assert built["provenance"]["benchmark_leaked"] == 0
    seen = set()
    for ex in built["examples"]:
        # range + mode gates
        for field, (lo, hi) in gen._RANGE.items():
            assert lo <= ex["al_state_in"][field] <= hi
            assert lo <= ex["al_state_out"][field] <= hi
        assert ex["al_state_in"]["routing_mode"] == ex["al_state_out"]["routing_mode"]
        # leakage + duplicate gates
        assert gen._norm(ex["input_text"]) not in bench
        assert gen._norm(ex["input_text"]) not in seen
        seen.add(gen._norm(ex["input_text"]))
        assert ex["expected_response"].strip(), "a row with no answer is not trainable"


def test_skip_takes_a_fresh_slice_and_prefixes_ids(gen):
    """A later batch must repeat no question of the first one: same seed on the
    same rows would only resample the state values (wasted training)."""
    base = gen.build(rows=20, seed=7)
    shifted = gen.build(rows=10, seed=7, skip=10, id_prefix="r2_")
    assert [e["input_text"] for e in shifted["examples"]] == [
        e["input_text"] for e in base["examples"][10:]
    ]
    assert {e["input_text"] for e in shifted["examples"]}.isdisjoint(
        e["input_text"] for e in base["examples"][:10]
    )
    assert all(e["sample_id"].startswith("r2_") for e in shifted["examples"])
    assert base["examples"][0]["sample_id"].startswith("r1_")
    # non-defaults are recorded for audit; a default build stays byte-identical
    assert "skip" in shifted["provenance"]
    assert "id_prefix" in shifted["provenance"]
    assert "skip" not in base["provenance"]
    assert "id_prefix" not in base["provenance"]


def test_expose_dt_is_off_by_default_and_changes_nothing_else(gen):
    """Round 4's schema variable: the timestep enters the example only when
    asked (MVE-1's registered upgrade path), and asking does not touch the
    rng stream — same rows, same values, one extra key."""
    plain = gen.build(rows=30, seed=7)
    assert "expose_dt" not in plain["provenance"]
    assert all("dt" not in ex for ex in plain["examples"])

    exposed = gen.build(rows=30, seed=7, expose_dt=True)
    assert exposed["provenance"]["expose_dt"] is True
    assert all(ex["dt"] in gen._DT_LADDER for ex in exposed["examples"])
    assert exposed["total_samples"] == plain["total_samples"]
    for a, b in zip(plain["examples"], exposed["examples"]):
        assert {k: v for k, v in b.items() if k != "dt"} == a


def test_intent_rules_are_the_documented_placeholder(gen):
    assert gen._intent_of("Tell me a joke about penguins") == "humor"
    assert gen._intent_of("Hello there") == "greeting"
    assert gen._intent_of("What is the capital of France") == "knowledge_query"
    assert gen._intent_of("something else entirely") == "unknown"
