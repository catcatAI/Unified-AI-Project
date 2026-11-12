#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""Turn the raw arithmetic corpus into a clean, leak-free plain-prompt split.

The raw corpus and the frozen test set disagree (see
:mod:`scripts.arithmetic_task`). This script resolves the disagreement in the
one direction that does not touch the test set: it conforms training data to
the test distribution, and records every removal and relabel.

Outputs (under ``apps/backend/data/processed/arithmetic_plain/``):

* ``train.jsonl`` / ``val.jsonl`` — ``{"input", "output"}`` rows;
* ``manifest.json`` — source hashes, every count, per-operator and digit-span
  coverage, output hashes, and the post-guard leak check.

Rules enforced (each is a hard failure, not a warning):

1. Only supported prompts are kept; every row is emitted in the plain surface
   form the test set uses. Unsupported shapes are counted and dropped, never
   guessed.
2. Labels are the test set's own rule: ``str(round(a / b, 4))`` for ``/``,
   ``str(a op b)`` otherwise. A raw label that differs only in surface form is
   counted as normalised; there is no numeric disagreement to "fix".
3. Rows whose problem (commutative for ``+``/``*``) occurs in the frozen test
   set are removed from **training** — never the other way around.
4. The frozen test set is re-verified against the canonical rule. If it ever
   stops agreeing, this script exits non-zero; it never rewrites the test.

Usage::

    python3 scripts/prepare_arithmetic_task.py
    python3 scripts/prepare_arithmetic_task.py --check   # verify, write nothing
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from arithmetic_task import (  # noqa: E402
    canonical_answer,
    canonical_prompt,
    parse_plain,
    parse_problem,
    problem_key,
    span_pairs,
    test_keys,
)

RAW_DIR = REPO_ROOT / "apps" / "backend" / "data" / "raw_datasets"
DEFAULT_TRAIN = RAW_DIR / "arithmetic_train_dataset.json"
DEFAULT_TEST = RAW_DIR / "arithmetic_test_dataset.csv"
DEFAULT_OUT = REPO_ROOT / "apps" / "backend" / "data" / "processed" / "arithmetic_plain"

OPS = "+-*/"


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_rows(path: Path) -> List[dict]:
    if path.suffix.lower() == ".csv":
        import csv

        with path.open(encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return raw
    return list(raw.get("examples") or [])


def build(
    train_rows: List[dict], test_rows: List[dict], val_ratio: float = 0.05
) -> Tuple[List[dict], List[dict], Dict[str, Any]]:
    """Pure transformation: raw rows in, clean split + report out."""
    if not 0.0 <= val_ratio < 1.0:
        raise ValueError(f"val_ratio must be in [0, 1): {val_ratio}")

    counts: Dict[str, int] = {
        "raw_train": len(train_rows),
        "unsupported_format": 0,
        "zero_division": 0,
        "duplicate": 0,
        "label_normalised": 0,
        "reexpressed_decorated": 0,
        "leak_exact": 0,
        "leak_commutative": 0,
    }
    surfaces: Counter = Counter()

    keys = test_keys(test_rows)
    exact_keys = set()
    for row in test_rows:
        problem = parse_plain(str(row.get("problem") or row.get("input") or ""))
        if problem is not None:
            exact_keys.add(problem)

    # The frozen test set must already use the canonical rule. Refuse to
    # proceed otherwise: rewriting the test would erase the thing being
    # measured.
    test_label_errors: List[Tuple[str, str, str]] = []
    for row in test_rows:
        problem = parse_plain(str(row.get("problem") or row.get("input") or ""))
        if problem is None:
            test_label_errors.append(
                (str(row.get("problem")), str(row.get("answer")), "<unparsable>")
            )
            continue
        want = canonical_answer(*problem)
        got = str(row.get("answer") or "").strip()
        if want is None or got != want:
            test_label_errors.append((canonical_prompt(problem), got, str(want)))
    if test_label_errors:
        raise ValueError(
            f"frozen test set disagrees with the canonical rule: {test_label_errors[:5]}"
        )

    seen: set = set()
    kept: List[Tuple[str, str, Tuple[int, str, int]]] = []
    per_op: Counter = Counter()

    for row in train_rows:
        parsed = parse_problem(str(row.get("problem") or row.get("input") or ""))
        if parsed is None:
            counts["unsupported_format"] += 1
            continue
        problem, surface = parsed
        surfaces[surface] += 1
        if surface != "plain":
            counts["reexpressed_decorated"] += 1
        answer = canonical_answer(*problem)
        if answer is None:
            counts["zero_division"] += 1
            continue

        raw_answer = str(row.get("answer") or row.get("output") or "").strip()
        if raw_answer != answer:
            counts["label_normalised"] += 1

        if problem_key(problem) in keys:
            if problem in exact_keys:
                counts["leak_exact"] += 1
            else:
                counts["leak_commutative"] += 1
            continue

        prompt = canonical_prompt(problem)
        if (prompt, answer) in seen:
            counts["duplicate"] += 1
            continue
        seen.add((prompt, answer))
        kept.append((prompt, answer, problem))
        per_op[problem[1]] += 1

    train: List[dict] = []
    val: List[dict] = []
    for prompt, answer, problem in kept:
        # Split by *problem*, not by prompt: ``3 + 4`` and ``4 + 3`` are the
        # same exercise, and putting one in train and the other in val would
        # report held-out accuracy that was trained on.
        bucket = hashlib.sha1(f"{problem_key(problem)}\x00{answer}".encode("utf-8")).hexdigest()[:8]
        share = int(bucket, 16) / 0xFFFFFFFF
        row = {"input": prompt, "output": answer}
        (val if share < val_ratio else train).append(row)

    # Post-guard leak check: the output must not contain any test problem.
    out_keys = {problem_key(parse_plain(r["input"])) for r in train + val}
    residual = out_keys & keys
    if residual:
        raise ValueError(f"leak guard left {len(residual)} test problems in the split")

    # Guard against a prompt mapping to two answers (impossible with a pure
    # label function, so a hit means the parser above is wrong).
    by_prompt: Dict[str, set] = defaultdict(set)
    for row in train + val:
        by_prompt[row["input"]].add(row["output"])
    conflicts = {p: sorted(v) for p, v in by_prompt.items() if len(v) > 1}
    if conflicts:
        raise ValueError(
            f"conflicting labels after canonicalisation: {list(conflicts.items())[:3]}"
        )

    train_keys = {problem_key(parse_plain(r["input"])) for r in train}
    val_keys = {problem_key(parse_plain(r["input"])) for r in val}
    split_leak = train_keys & val_keys
    if split_leak:
        raise ValueError(f"train/val split shares {len(split_leak)} problems")

    def _ordered(problem: Tuple[int, str, int]) -> Tuple[int, str, int]:
        a, op, b = problem
        return (min(a, b), op, max(a, b)) if op in "+*" else (a, op, b)

    kept_problems = [_ordered(problem) for _p, _a, problem in kept]
    test_problems = [
        _ordered(p) for p in (parse_plain(str(r.get("problem") or "")) for r in test_rows) if p
    ]
    coverage: Dict[str, Dict[str, Any]] = {}
    for op in OPS:
        test_spans = span_pairs(test_problems, op)
        train_spans = span_pairs(kept_problems, op)
        coverage[op] = {
            "test": [list(span) for span in test_spans],
            "train": [list(span) for span in train_spans],
            "uncovered": [list(span) for span in test_spans if span not in set(train_spans)],
        }

    report: Dict[str, Any] = {
        "counts": counts,
        "surfaces": {name: surfaces.get(name, 0) for name in ("plain", "suffix", "prefix")},
        "kept": len(kept),
        "train": len(train),
        "val": len(val),
        "per_operator": {op: per_op.get(op, 0) for op in OPS},
        "digit_span_coverage_rule": "operands smallest-first for + and *; exact order for - and /",
        "digit_span_coverage": coverage,
        "leak_check": {"residual_test_problems": len(residual)},
        "split_check": {"train_val_shared_problems": len(split_leak)},
        "conflicting_prompts": len(conflicts),
    }
    return train, val, report


def _write_jsonl(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default=str(DEFAULT_TRAIN))
    parser.add_argument("--test", default=str(DEFAULT_TEST))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--val-ratio", type=float, default=0.05)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify an existing split against its manifest and source hashes; write nothing",
    )
    args = parser.parse_args()

    train_path = Path(args.train)
    test_path = Path(args.test)
    out_dir = Path(args.out_dir)
    manifest_path = out_dir / "manifest.json"

    if not train_path.is_file() or not test_path.is_file():
        print(f"missing source: {train_path} / {test_path}")
        return 2

    if args.check:
        if not manifest_path.is_file():
            print(f"no manifest at {manifest_path}; run without --check first")
            return 2
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        ok = True
        for name, expected in (manifest.get("files") or {}).items():
            path = out_dir / name
            if not path.is_file():
                print(f"MISSING {path}")
                ok = False
                continue
            actual = _sha256_file(path)
            if actual != expected:
                print(f"HASH MISMATCH {name}: {actual} != {expected}")
                ok = False
        for role, path in (("train", train_path), ("test", test_path)):
            source = (manifest.get("sources") or {}).get(role) or {}
            actual = _sha256_file(path)
            if source.get("sha256") != actual:
                print(f"SOURCE CHANGED {role}: {actual} != {source.get('sha256')}")
                ok = False
        print("arithmetic split: OK" if ok else "arithmetic split: FAILED")
        return 0 if ok else 1

    train_rows = _read_rows(train_path)
    test_rows = _read_rows(test_path)
    try:
        train, val, report = build(train_rows, test_rows, val_ratio=args.val_ratio)
    except ValueError as error:
        print(f"refused: {error}")
        return 1

    train_out = out_dir / "train.jsonl"
    val_out = out_dir / "val.jsonl"
    _write_jsonl(train_out, train)
    _write_jsonl(val_out, val)

    manifest: Dict[str, Any] = {
        "generated_by": "scripts/prepare_arithmetic_task.py",
        "canonical_label_rule": {
            "+": "str(a + b)",
            "-": "str(a - b)",
            "*": "str(a * b)",
            "/": "str(round(a / b, 4))",
        },
        "selection": {"prompt_format": "plain", "val_ratio": args.val_ratio},
        "sources": {
            "train": {
                "path": _rel(train_path),
                "rows": len(train_rows),
                "sha256": _sha256_file(train_path),
            },
            "test": {
                "path": _rel(test_path),
                "rows": len(test_rows),
                "sha256": _sha256_file(test_path),
                "frozen": True,
            },
        },
        "report": report,
        "files": {
            "train.jsonl": _sha256_file(train_out),
            "val.jsonl": _sha256_file(val_out),
        },
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    counts = report["counts"]
    print(
        f"kept {report['kept']} plain rows (train {report['train']} / val {report['val']}); "
        f"dropped unsupported={counts['unsupported_format']} "
        f"leak_exact={counts['leak_exact']} "
        f"leak_commutative={counts['leak_commutative']} duplicate={counts['duplicate']}; "
        f"labels normalised={counts['label_normalised']}, "
        f"decorated re-expressed={counts['reexpressed_decorated']}"
    )
    for op in OPS:
        uncovered = report["digit_span_coverage"][op]["uncovered"]
        if uncovered:
            print(f"WARNING {op}: test digit spans not covered by train: {uncovered}")
    print(f"wrote {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
