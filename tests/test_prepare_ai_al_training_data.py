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
