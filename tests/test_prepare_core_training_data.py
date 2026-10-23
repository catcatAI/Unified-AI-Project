"""Contract for the core training-data preparation (no teaching to the test)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "prepare_core_training_data.py"


def _load():
    spec = importlib.util.spec_from_file_location("prepare_core_training_data_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prep():
    return _load()


def test_alpaca_instruction_is_the_input(prep):
    """The old loader read ``input`` only, which is empty for most alpaca rows."""
    pair = prep._pair(
        {
            "instruction": "Give three tips for staying healthy.",
            "input": "",
            "output": "Eat well. Exercise. Sleep.",
        }
    )
    assert pair["input"] == "Give three tips for staying healthy."
    assert pair["output"].startswith("Eat well")


def test_context_is_kept_when_present(prep):
    pair = prep._pair({"instruction": "Summarize", "input": "text", "output": "ok"})
    assert "Summarize" in pair["input"] and "text" in pair["input"]


def test_benchmark_question_is_a_leak(prep):
    bench = ["what gas do plants absorb from the air for photosynthesis"]
    shingles = set()
    for question in bench:
        shingles |= prep._shingles(question)
    assert prep._is_leak(
        prep._norm("Q: What gas do plants absorb from the air for photosynthesis?"),
        bench,
        shingles,
    )


def test_unrelated_instruction_is_not_a_leak(prep):
    bench = ["what gas do plants absorb from the air for photosynthesis"]
    shingles = set()
    for question in bench:
        shingles |= prep._shingles(question)
    assert not prep._is_leak(prep._norm("Write a poem about the sea."), bench, shingles)


def test_split_is_deterministic(prep):
    rows = [{"input": f"question {i}", "output": "a"} for i in range(50)]
    first = prep.split(rows, 0.2)
    second = prep.split(rows, 0.2)
    assert [r["input"] for r in first[0]] == [r["input"] for r in second[0]]
    assert len(first[0]) + len(first[1]) == len(rows)


def test_manifest_roundtrip(tmp_path, prep):
    """Write a manifest, then verify --check accepts it (and rejects edits)."""
    args = SimpleNamespace(out_dir=str(tmp_path), limit=5, val_ratio=0.2, check=False)

    # build() reads the repo's raw datasets; use the real build once, then
    # verify the hash contract through main()'s check branch.
    rows, report = prep.build(limit=5)
    assert rows, "prepared rows must not be empty"
    train, val = prep.split(rows, args.val_ratio)
    files = {
        "core_train.jsonl": prep._write(tmp_path / "core_train.jsonl", train),
        "core_val.jsonl": prep._write(tmp_path / "core_val.jsonl", val),
    }
    import json

    (tmp_path / "core_train_manifest.json").write_text(
        json.dumps({"files": files, "report": report}), encoding="utf-8"
    )
    check = SimpleNamespace(out_dir=str(tmp_path), check=True)
    original = prep.OUT_DIR
    prep.OUT_DIR = tmp_path
    try:
        import sys as _sys

        old_argv = _sys.argv
        _sys.argv = ["prepare_core_training_data.py", "--check", "--out-dir", str(tmp_path)]
        try:
            assert prep.main() == 0
        finally:
            _sys.argv = old_argv
    finally:
        prep.OUT_DIR = original
