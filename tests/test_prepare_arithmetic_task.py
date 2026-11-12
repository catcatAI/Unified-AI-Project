"""Contract tests for the single definition of the arithmetic task.

These pin the three rules that, when they drift, make an arithmetic score
meaningless without looking wrong:

* the label rule (the test set's own, ``str(round(a / b, 4))`` for division);
* the prompt rule (plain surface for training, decorated sources re-expressed
  rather than silently dropped);
* the leak rule (commutative for ``+``/``*``, exact for ``-``/``/``).

The real corpus/test files are read when present (they are tracked); the
synthetic cases keep the rules testable on their own.
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"{name}_under_test", SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def task():
    return _load("arithmetic_task")


@pytest.fixture(scope="module")
def prepare():
    return _load("prepare_arithmetic_task")


TEST_CSV = REPO_ROOT / "apps" / "backend" / "data" / "raw_datasets" / "arithmetic_test_dataset.csv"
TRAIN_JSON = (
    REPO_ROOT / "apps" / "backend" / "data" / "raw_datasets" / "arithmetic_train_dataset.json"
)


def _test_rows():
    if not TEST_CSV.is_file():
        pytest.skip("frozen arithmetic test CSV not present")
    with TEST_CSV.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


# ---------------------------------------------------------------------------
# label rule
# ---------------------------------------------------------------------------
def test_division_label_matches_test_surface(task):
    # The test CSV writes exact divisions with a decimal point. This is the
    # mismatch that used to make 5,056 training rows "wrong" by formatting.
    assert task.canonical_answer(280, "/", 4) == "70.0"
    assert task.canonical_answer(1496, "/", 88) == "17.0"
    assert task.canonical_answer(0, "/", 145) == "0.0"


def test_non_division_labels_are_integers(task):
    assert task.canonical_answer(7, "+", 3) == "10"
    assert task.canonical_answer(3, "-", 7) == "-4"
    assert task.canonical_answer(851, "*", -54) == "-45954"


def test_zero_division_has_no_label(task):
    assert task.canonical_answer(1, "/", 0) is None
    assert task.canonical_answer(0, "/", 0) is None


def test_real_test_set_uses_the_canonical_rule(task):
    rows = _test_rows()
    assert rows, "test CSV is empty"
    bad = []
    for row in rows:
        problem = task.parse_plain(row["problem"])
        if problem is None:
            bad.append((row["problem"], "unparsable"))
            continue
        want = task.canonical_answer(*problem)
        if want is None or row["answer"].strip() != want:
            bad.append((row["problem"], row["answer"], want))
    assert bad == [], f"{len(bad)} frozen test rows disagree with the label rule: {bad[:5]}"


# ---------------------------------------------------------------------------
# prompt rule
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "prompt,surface,problem",
    [
        ("737 - 578", "plain", (737, "-", 578)),
        ("  12+7 ", "plain", (12, "+", 7)),
        ("737 - 578 =", "suffix", (737, "-", 578)),
        ("31 + 308 equals", "suffix", (31, "+", 308)),
        ("calculate 755 - 176", "prefix", (755, "-", 176)),
        ("what is 532 * 13", "prefix", (532, "*", 13)),
        ("What Is 90 / 10", "prefix", (90, "/", 10)),
    ],
)
def test_supported_prompts_are_parsed_with_their_surface(task, prompt, surface, problem):
    assert task.parse_problem(prompt) == (problem, surface)


@pytest.mark.parametrize(
    "prompt",
    [
        "",
        "not a problem",
        "I have 3 + 4 apples and 10 - 2 oranges",
        "calculate 1 + 2 and 3 + 4",
        "42",
        "3 ^ 4",
    ],
)
def test_unsupported_prompts_are_refused_not_guessed(task, prompt):
    assert task.parse_problem(prompt) is None


def test_canonical_prompt_is_the_test_surface(task):
    assert task.canonical_prompt((280, "/", 4)) == "280 / 4"
    assert task.canonical_prompt((851, "*", -54)) == "851 * -54"


# ---------------------------------------------------------------------------
# leak rule
# ---------------------------------------------------------------------------
def test_problem_key_is_commutative_only_where_the_operation_is(task):
    assert task.problem_key((3, "+", 4)) == task.problem_key((4, "+", 3))
    assert task.problem_key((3, "*", 4)) == task.problem_key((4, "*", 3))
    assert task.problem_key((3, "-", 4)) != task.problem_key((4, "-", 3))
    assert task.problem_key((3, "/", 4)) != task.problem_key((4, "/", 3))


def test_test_keys_use_the_commutative_rule(task):
    keys = task.test_keys([{"problem": "6 + 5"}, {"problem": "10 - 2"}])
    assert task.leaks((5, "+", 6), keys) is True
    assert task.leaks((6, "+", 5), keys) is True
    assert task.leaks((2, "-", 10), keys) is False


# ---------------------------------------------------------------------------
# the transformation itself
# ---------------------------------------------------------------------------
def _row(problem: str, answer: str) -> dict:
    return {"problem": problem, "answer": answer}


def test_build_reexpresses_decorated_rows_and_canonicalises_labels(prepare):
    test_rows = [_row("3 + 4", "7")]
    train_rows = [
        _row("1 + 2", "3"),
        _row("what is 1 + 2", "3"),  # same problem, different surface
        _row("10 / 2", "5"),  # exact division: test surface is "5.0"
        _row("7 * 6 =", "42"),
    ]
    train, val, report = prepare.build(train_rows, test_rows)
    rows = train + val
    assert {"input": "1 + 2", "output": "3"} in rows
    assert {"input": "10 / 2", "output": "5.0"} in rows
    assert {"input": "7 * 6", "output": "42"} in rows
    assert report["counts"]["reexpressed_decorated"] == 2
    assert report["counts"]["label_normalised"] == 1
    assert report["counts"]["duplicate"] == 1


def test_build_drops_exact_and_commutative_test_problems_from_train(prepare):
    test_rows = [_row("3 + 4", "7"), _row("10 - 2", "8")]
    train_rows = [
        _row("3 + 4", "7"),  # exact leak
        _row("4 + 3", "7"),  # commutative leak
        _row("10 - 2", "8"),  # exact leak
        _row("2 - 10", "-8"),  # NOT a leak: subtraction does not commute
        _row("9 * 9", "81"),  # clean
    ]
    train, val, report = prepare.build(train_rows, test_rows)
    prompts = {row["input"] for row in train + val}
    assert prompts == {"9 * 9", "2 - 10"}
    assert report["counts"]["leak_exact"] == 2
    assert report["counts"]["leak_commutative"] == 1
    assert report["leak_check"]["residual_test_problems"] == 0


def test_build_refuses_a_test_set_that_breaks_the_label_rule(prepare):
    # "5" instead of "5.0": rewriting the test would erase what is measured.
    with pytest.raises(ValueError, match="frozen test set"):
        prepare.build([_row("1 + 2", "3")], [_row("10 / 2", "5")])


def test_build_refuses_unparsable_test_rows(prepare):
    with pytest.raises(ValueError, match="frozen test set"):
        prepare.build([_row("1 + 2", "3")], [_row("what is 10 / 2", "5.0")])


def test_build_splits_by_problem_not_by_surface(prepare):
    # "3 + 4" and "4 + 3" are one exercise; they must not straddle train/val.
    train_rows = [_row("3 + 4", "7"), _row("4 + 3", "7")]
    train, val, report = prepare.build(train_rows, [], val_ratio=0.5)
    sides = {"train" if r in train else "val" for r in train + val}
    assert len(sides) == 1, "commutative pair was split across train/val"
    assert report["split_check"]["train_val_shared_problems"] == 0


def test_build_reports_uncovered_test_digit_shapes(prepare):
    # Subtraction does not commute, so operand order is part of the shape.
    test_rows = [_row("42 - 7", "35"), _row("123 + 4", "127")]
    train_rows = [_row("7 - 42", "-35"), _row("1 + 2", "3"), _row("5 + 100", "105")]
    _train, _val, report = prepare.build(train_rows, test_rows)
    assert report["digit_span_coverage"]["-"]["uncovered"] == [[2, 1]]
    # Addition is order-insensitive for coverage: 123 + 4 normalises to (1, 3).
    assert report["digit_span_coverage"]["+"]["uncovered"] == []


def test_curriculum_leak_guard_uses_the_commutative_rule():
    module = _load("train_token_snn_curriculum")
    kept = module.leak_guard([("3 + 4", "7"), ("4 + 3", "7"), ("5 + 6", "11")], {(3, "+", 4)})
    assert kept == [("5 + 6", "11")]


def test_real_corpus_produces_a_leak_free_plain_split(prepare):
    if not TEST_CSV.is_file() or not TRAIN_JSON.is_file():
        pytest.skip("arithmetic corpus not present")
    import json

    train_rows = json.loads(TRAIN_JSON.read_text(encoding="utf-8"))
    test_rows = _test_rows()
    train, val, report = prepare.build(train_rows, test_rows)
    assert report["kept"] > 20_000
    assert report["leak_check"]["residual_test_problems"] == 0
    assert report["split_check"]["train_val_shared_problems"] == 0
    assert report["counts"]["leak_exact"] == 16
    assert report["counts"]["leak_commutative"] == 4
    assert all(row["input"].count(" ") == 2 for row in train + val)
    assert all(row["output"] == row["output"].strip() for row in train + val)
