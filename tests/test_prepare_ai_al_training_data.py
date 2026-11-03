"""Contract for the AI+AL joint training-data preparation."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "prepare_ai_al_training_data.py"


def _load():
    spec = importlib.util.spec_from_file_location("prepare_ai_al_training_data_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prep():
    return _load()


def test_state_goes_on_both_sides_of_the_pair(prep):
    """The model must answer *from* a state and emit the state it moves to."""
    rows = prep.load_records()
    assert rows, "the pilot dataset produced no rows"
    row = rows[0]
    state_in, user_text = row["input"].split(" | ", 1)
    assert state_in.startswith("<al_in> ")
    assert "mode=" in state_in and "intent=" in state_in
    assert " | " in rows[0]["input"]
    response, state_out = row["output"].split("\n", 1)
    assert state_out.startswith("<al_out> ")
    assert response and not response.startswith("<al_")
    assert user_text


def test_every_pilot_record_becomes_exactly_one_row(prep):
    source = json.loads(prep.SRC.read_text(encoding="utf-8"))
    rows = prep.load_records()
    assert len(rows) == source["total_samples"]
    assert len({r["sample_id"] for r in rows}) == len(rows)


def test_split_is_deterministic_and_disjoint(prep):
    rows = prep.load_records()
    first = prep._split(rows, 0.2)
    second = prep._split(list(rows), 0.2)
    assert first == second, "the split must not depend on iteration state"
    train, val = first
    assert train and val, "both sides need rows on a dataset this size"
    assert {r["sample_id"] for r in train}.isdisjoint(r["sample_id"] for r in val)
    assert len(train) + len(val) == len(rows)


def test_benchmark_question_is_dropped(prep, tmp_path, monkeypatch):
    rows = prep.load_records()
    bench = tmp_path / "bench.json"
    bench.write_text(
        json.dumps(
            {"suites": {"s": {"items": [{"q": rows[0]["input"].split(" | ", 1)[1]}]}}},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(prep, "BENCH", bench)
    built = prep.build(0.2)
    assert built["manifest"]["leaked"] == 1
    assert built["manifest"]["records"] == len(rows)
    kept = built["train"] + built["val"]
    assert len(kept) == len(rows) - 1
    assert rows[0]["sample_id"] not in {r["sample_id"] for r in kept}


def test_write_then_check_roundtrip(prep, tmp_path, monkeypatch):
    monkeypatch.setattr(prep, "OUT_DIR", tmp_path)
    monkeypatch.setattr(prep, "TRAIN_OUT", tmp_path / "ai_al_train.jsonl")
    monkeypatch.setattr(prep, "VAL_OUT", tmp_path / "ai_al_val.jsonl")
    monkeypatch.setattr(prep, "MANIFEST_OUT", tmp_path / "ai_al_manifest.json")
    assert prep.main([]) == 0
    assert prep.main(["--check"]) == 0
    manifest = json.loads((tmp_path / "ai_al_manifest.json").read_text(encoding="utf-8"))
    assert manifest["train"] + manifest["val"] == manifest["records"]
    assert manifest["leaked"] == 0
    # a hand-edited file must fail the check
    path = tmp_path / "ai_al_train.jsonl"
    path.write_text(path.read_text(encoding="utf-8") + "{}\n", encoding="utf-8")
    assert prep.main(["--check"]) == 1


def test_dt_rides_the_input_line_only_when_the_source_exposes_it(prep, tmp_path):
    """Round-4 schema: dt is serialised into ``<al_in> ... intent=x dt=1.00``
    from the source's ``dt`` field; the output side and a round-1-3 source
    stay exactly as they were."""
    spec = importlib.util.spec_from_file_location(
        "generate_al_dataset_prepare_test", REPO_ROOT / "scripts" / "generate_al_dataset.py"
    )
    assert spec and spec.loader
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    src = tmp_path / "with_dt.json"
    src.write_text(json.dumps(gen.build(rows=12, seed=3, expose_dt=True)), encoding="utf-8")
    rows = prep.load_records(src)
    assert rows
    for row in rows:
        state_in, _user_text = row["input"].split(" | ", 1)
        assert " dt=" in state_in
        # the response is a state, never a timestep
        # the response may span lines; the state block is always the last line
        state_out = row["output"].rsplit("\n", 1)[1]
        assert state_out.startswith("<al_out> ") and " dt=" not in state_out
    manifest = prep.build(0.2, src)["manifest"]
    assert " dt |" in manifest["format"]["input"]

    # the pilot source (rounds 1-3 schema) keeps the old input line
    assert all(" dt=" not in r["input"] for r in prep.load_records())
    plain_manifest = prep.build(0.2)["manifest"]
    assert " dt |" not in plain_manifest["format"]["input"]


def test_out_paths_are_configurable(prep, tmp_path):
    """The loop's *next* batch must be able to write elsewhere — overwriting
    the files the current round trained on would poison the audit trail."""
    train = tmp_path / "round9_train.jsonl"
    val = tmp_path / "round9_val.jsonl"
    man = tmp_path / "round9_manifest.json"
    argv = ["--train-out", str(train), "--val-out", str(val), "--manifest-out", str(man)]
    assert prep.main(argv) == 0
    assert train.exists() and val.exists() and man.exists()
    assert prep.main([*argv, "--check"]) == 0
    train.write_text(train.read_text(encoding="utf-8") + "{}\n", encoding="utf-8")
    assert prep.main([*argv, "--check"]) == 1


def test_state_line_decimals_set_the_printable_precision(prep, tmp_path):
    """3dp is what a 1e-3 grader needs; 2dp stays the default for old rounds."""
    state = {
        "valence": -0.10532,
        "arousal": 0.595303,
        "dominance": -0.435188,
        "fatigue": 0.285198,
        "stress": 0.123456,
        "health": 0.525106,
        "routing_mode": "neutral",
    }
    two = prep._state_line(state, "math_query", "in", dt=0.5)
    three = prep._state_line(state, "math_query", "in", dt=0.5, decimals=3)
    assert "v=-0.11 " in two and "dt=0.50" in two
    assert "v=-0.105 " in three and "dt=0.500" in three
    # clamped: the format string must never be breakable from the CLI
    assert prep._state_line(state, "math_query", "in", decimals=99) == (
        prep._state_line(state, "math_query", "in", decimals=6)
    )
    assert "v=-0.11 " in prep._state_line(state, "math_query", "in", decimals=0)


def test_build_records_the_decimal_places_it_used(prep, tmp_path):
    src = tmp_path / "src.json"
    src.write_text(
        json.dumps(
            {
                "examples": [
                    {
                        "sample_id": "s1",
                        "input_text": "2 + 2",
                        "expected_response": "4",
                        "al_state_in": {
                            "valence": 0.1111,
                            "arousal": 0.2222,
                            "dominance": 0.3333,
                            "fatigue": 0.4444,
                            "stress": 0.5555,
                            "health": 0.6666,
                            "routing_mode": "neutral",
                        },
                        "al_state_out": {
                            "valence": 0.1234,
                            "arousal": 0.2345,
                            "dominance": 0.3456,
                            "fatigue": 0.4567,
                            "stress": 0.5678,
                            "health": 0.6789,
                            "routing_mode": "neutral",
                        },
                        "intent": "math_query",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    built = prep.build(0.0, src, decimals=3)
    assert built["manifest"]["format"]["decimals"] == 3
    assert "v=0.111" in built["train"][0]["input"]
    assert "v=0.123" in built["train"][0]["output"]
    assert prep.build(0.0, src)["manifest"]["format"]["decimals"] == 2


def test_manifest_source_round_trips_relative_paths(prep, tmp_path):
    """--check must compare against the source the build recorded, not the pilot."""
    src = tmp_path / "round.json"
    src.write_text(json.dumps({"examples": []}), encoding="utf-8")
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps({"source": str(src)}), encoding="utf-8")
    assert prep._manifest_source(manifest) == src
    (manifest).write_text(json.dumps({"source": "does/not/exist.json"}), encoding="utf-8")
    assert prep._manifest_source(manifest) == prep.REPO_ROOT / "does/not/exist.json"
    manifest.write_text("not json", encoding="utf-8")
    assert prep._manifest_source(manifest) is None
