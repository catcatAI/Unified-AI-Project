"""Contract for the route-② distillation script (no teaching to the test)."""

from __future__ import annotations

import importlib.util
import json
import random
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "distill_core_data.py"


def _load():
    spec = importlib.util.spec_from_file_location("distill_core_data_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def distill():
    return _load()


def _shingles_for(prep, bench):
    shingles = set()
    for question in bench:
        shingles |= prep._shingles(question)
    return shingles


def test_math_answers_are_python_correct(distill):
    """Every programmatic pair must satisfy its own arithmetic."""
    rnd = random.Random(7)
    rows = distill._math_pairs(300, rnd)
    assert len(rows) == 300
    checked = 0
    lead_re = re.compile(r"^(What is|Calculate|Compute|Work out) (.+?)?$")
    for row in rows:
        text, out = row["input"], row["output"]
        # spot-check the plain expression form only (the rest are stories /
        # formulas whose answer is computed inline by the generator itself)
        m = lead_re.match(text)
        if not m or "+" not in text and "-" not in text and "*" not in text:
            continue
        expr = m.group(2).rstrip("?")
        if any(word in expr for word in ("mass", "force", "kg", "has", "train")):
            continue
        try:
            expected = eval(expr, {"__builtins__": {}}, {})  # noqa: S307
        except Exception:  # noqa: BLE001 - not an expression form
            continue
        assert abs(float(out) - float(expected)) < 1e-6, (text, out, expected)
        checked += 1
    assert checked > 20, "expression pairs were not exercised"


def test_benchmark_question_is_dropped_by_the_filter(distill):
    """The contract: an eval item can never reach training."""
    prep = distill.prep
    bench = ["what gas do plants absorb from the air for photosynthesis"]
    shingles = _shingles_for(prep, bench)
    rows = [
        {"input": "What gas do plants absorb from the air for photosynthesis?", "output": "co2"},
        {"input": "Write a poem about the sea.", "output": "waves"},
    ]
    kept, dropped = distill._filter(rows, bench, shingles)
    assert len(kept) == 1 and kept[0]["input"].startswith("Write")
    assert dropped["benchmark_leak"] == 1


def test_filter_drops_empty_and_duplicates(distill):
    prep = distill.prep
    rows = [
        {"input": "", "output": "x"},
        {"input": "q?", "output": ""},
        {"input": "Same question?", "output": "a"},
        {"input": "Same question?", "output": "a"},
    ]
    kept, dropped = distill._filter(rows, [], set())
    assert len(kept) == 1
    assert dropped["empty"] == 2 and dropped["duplicate"] == 1


def test_inputs_are_raw_questions(distill):
    """probe_core_control feeds item.q straight to generate() — no wrapper."""
    rows = distill._math_pairs(50, random.Random(1))
    for row in rows:
        assert not row["input"].startswith(("Q:", "Question:", "Instruction:"))
        assert row["output"].strip() == row["output"]


def test_num2zh_matches_benchmark_form(distill):
    assert distill.num2zh(38) == "三十八"
    assert distill.num2zh(62) == "六十二"
    assert distill.num2zh(20) == "二十"
    assert distill.num2zh(7) == "七"


def test_teacher_answer_grounding_rule(distill):
    """knowledge pairs: an answer absent from the passage must not pass."""
    prep = distill.prep
    lead = "Mars is the fourth planet from the Sun. It is a cold desert world."
    assert prep._norm("Mars") in prep._norm(lead)
    assert prep._norm("Venus") not in prep._norm(lead)


def test_check_accepts_a_written_manifest(tmp_path, distill):
    """--check re-verifies sha256 AND re-runs the leak scan on the files."""
    prep = distill.prep
    bench = ["what gas do plants absorb from the air for photosynthesis"]
    shingles = _shingles_for(prep, bench)
    rows, dropped = distill._filter(
        [
            {"input": "What is 2 + 2?", "output": "4", "source": "math"},
            {
                "input": "What gas do plants absorb from the air for photosynthesis?",
                "output": "co2",
            },
        ],
        bench,
        shingles,
    )
    assert dropped["benchmark_leak"] == 1
    train, val = prep.split(rows, 0.5, seed="distill-test")
    files = {
        distill.TRAIN_NAME: prep._write(tmp_path / distill.TRAIN_NAME, train),
        distill.VAL_NAME: prep._write(tmp_path / distill.VAL_NAME, val),
    }
    (tmp_path / distill.MANIFEST_NAME).write_text(
        json.dumps({"files": files, "total": len(rows), "sources": {"math": {}}}),
        encoding="utf-8",
    )
    args = SimpleNamespace(out_dir=str(tmp_path), check=True)
    assert distill.check(args) == 0

    # tampering must fail both the hash and (if re-hashed) the leak scan
    path = tmp_path / distill.TRAIN_NAME
    tampered = (
        path.read_text(encoding="utf-8")
        + json.dumps(
            {
                "input": "What gas do plants absorb from the air for photosynthesis?",
                "output": "co2",
                "source": "math",
            }
        )
        + "\n"
    )
    path.write_text(tampered, encoding="utf-8")
    assert distill.check(args) == 1
