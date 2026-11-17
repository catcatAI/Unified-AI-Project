#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# LAYER: learning
# =============================================================================
"""§91: when the numbers change, does the answer follow the arithmetic?

§90.13 measured 34.5/248 (13.9%) exact on the same-distribution hold-out with
``train_exact_200`` at 0.785–0.830 and 199/248 wrong answers that are pure
numbers of the right shape (``24249`` for ``52438``). Two readings survive that
evidence:

* **computes** — the model applies the row's operation to its own operands;
* **imitates** — it reproduces the *surface* of a memorised (or near) training
  row and emits a plausible number.

This probe separates them with a counterfactual: keep the question, change the
operands to values that never occur in training, and ask whether the answer
tracks the arithmetic. An imitator cannot pass; a calculator passes at the same
rate as on the original rows.

The truth for the perturbed row is not written by hand. It comes from the
**training corpus itself**: rows are grouped by digit-template, and a family is
usable only if exactly one expression from a pre-registered candidate list
reproduces *every* training row of that family. Families with no fit, or with
two fits, are dropped and counted — never patched.

Everything here is diagnostic: it trains nothing, changes no checkpoint, and
touches no threshold. See ``CORE_GAP_ANALYSIS.md`` §91 for the registration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from probe_core_callers import MAX_NEW, measure_holdout, rows_digest, sha256_file  # noqa: E402
from probe_core_recipe_ab import load_model  # noqa: E402
from train_token_snn import read_pairs  # noqa: E402

DATA = REPO_ROOT / "apps" / "backend" / "data"
PROCESSED = DATA / "processed"
TRAIN = PROCESSED / "distill_train.jsonl"
HOLDOUT = PROCESSED / "distill_val_holdout.jsonl"
CHECKPOINTS = REPO_ROOT / "data" / "e2_recipe_ab" / "final_epoch" / "checkpoints"
OUT_DIR = REPO_ROOT / "data" / "e3_counterfactual"

ARMS: Tuple[Tuple[str, int], ...] = (("snn", 0), ("snn", 1), ("gru", 0), ("gru", 1))
#: §91.5 — the verdict is spoken for the SNN arm (the production cell); GRU is
#: reported beside it and cannot change the verdict.
DECIDING_ARM = "snn"

#: §91.1 — a family needs enough rows for "reproduces every row" to mean something.
MIN_FAMILY_ROWS = 8
#: §91.5 — below this many correct original rows the comparison is underpowered.
MIN_CORRECT = 10
#: §91.3 — deterministic perturbation ladders (never randomised). Each step keeps
#: the operand's digit count, so the perturbed row stays inside the corpus's own
#: magnitude class; otherwise "cannot compute" and "never saw a 6-digit product"
#: would be the same measurement.
BUMP_LADDER: Tuple[int, ...] = (1, 2, 3, 4)
MULTIPLE_LADDER: Tuple[int, ...] = (1, 2, 3, 4, 5)
#: §91.4 — positive control: train rows the model memorised, same treatment.
CONTROL_ROWS = 60
#: §91.1 — a family may lose at most this share of its rows to unusable golds.
MAX_NON_NUMERIC_SHARE = 0.05

NUM_RE = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?")


# -- the corpus-derived oracle (§91.1) --------------------------------------
def numeric_gold(gold: str) -> Optional[float]:
    """``None`` for golds that are not a bare number (one corpus row says
    ``"30% of 200 is 60."`` instead of ``"60"``). Such rows cannot be scored
    numerically, so they are excluded from fitting — counted, never repaired."""
    try:
        value = float(gold.strip())
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def constant_factor(rows: Sequence[Sequence[float]], golds: Sequence[float]) -> Optional[float]:
    """``k`` such that ``gold = k * x0`` holds on every row (corpus-solved).

    Only offered when every row agrees on ``k``; a family whose values vary in
    the ratio has no such ``k`` and gets ``None``.
    """
    ratios = []
    for x, gold in zip(rows, golds):
        if not x or abs(x[0]) <= 1e-12:
            return None
        ratios.append(gold / x[0])
    if not ratios:
        return None
    first = ratios[0]
    if any(abs(r - first) > 1e-6 * max(1.0, abs(first)) for r in ratios):
        return None
    return first if abs(first) > 1e-9 else None


def _candidates(
    extra: Optional[Sequence[Tuple[str, Callable[[Sequence[float]], Optional[float]]]]] = None,
) -> List[Tuple[str, Callable[[Sequence[float]], Optional[float]]]]:
    """The pre-registered hypothesis set, in a fixed order.

    Every entry is a closed-form expression over the row's operands in prompt
    order. A family is usable only when **exactly one** entry reproduces all of
    its training rows, so the order matters only for reporting, never for
    selection.
    """

    def safe(
        fn: Callable[[Sequence[float]], float],
    ) -> Callable[[Sequence[float]], Optional[float]]:
        def wrapped(x: Sequence[float]) -> Optional[float]:
            try:
                value = float(fn(x))
            except (ZeroDivisionError, IndexError, ValueError):
                return None
            return value if math.isfinite(value) else None

        return wrapped

    return [
        ("x0+x1", safe(lambda x: x[0] + x[1])),
        ("x0-x1", safe(lambda x: x[0] - x[1])),
        ("x1-x0", safe(lambda x: x[1] - x[0])),
        ("x0*x1", safe(lambda x: x[0] * x[1])),
        ("x0/x1", safe(lambda x: x[0] / x[1])),
        ("x1/x0", safe(lambda x: x[1] / x[0])),
        ("x0%x1", safe(lambda x: math.fmod(x[0], x[1]))),
        ("x0*x1/100", safe(lambda x: x[0] * x[1] / 100.0)),
        ("x0*x1*x2", safe(lambda x: x[0] * x[1] * x[2])),
        ("x0*x1/x2", safe(lambda x: x[0] * x[1] / x[2])),
        ("x0*x1*x1", safe(lambda x: x[0] * x[1] * x[1])),
        ("x0*x1*x1/2", safe(lambda x: x[0] * x[1] * x[1] / 2.0)),
        ("x0*x1*x2/2", safe(lambda x: x[0] * x[1] * x[2] / 2.0)),
        ("x0+x1*x2", safe(lambda x: x[0] + x[1] * x[2])),
        ("(x0+x1)*x2", safe(lambda x: (x[0] + x[1]) * x[2])),
        ("(x0+x1)/x2", safe(lambda x: (x[0] + x[1]) / x[2])),
        ("x0*x1+x2", safe(lambda x: x[0] * x[1] + x[2])),
        ("x0*x1-x2", safe(lambda x: x[0] * x[1] - x[2])),
        ("x0/x1/x2", safe(lambda x: x[0] / x[1] / x[2])),
        ("x0/(x1*x2)", safe(lambda x: x[0] / (x[1] * x[2]))),
        ("x0*x1*x2*x3", safe(lambda x: x[0] * x[1] * x[2] * x[3])),
        ("x0*x1/(x2*x3)", safe(lambda x: x[0] * x[1] / (x[2] * x[3]))),
        ("x0+x1+x2", safe(lambda x: x[0] + x[1] + x[2])),
        ("x0-x1-x2", safe(lambda x: x[0] - x[1] - x[2])),
        ("x0-x1*x2", safe(lambda x: x[0] - x[1] * x[2])),
        ("x0+x1+x2+x3", safe(lambda x: x[0] + x[1] + x[2] + x[3])),
    ] + list(extra or [])


def digit_template(prompt: str) -> str:
    return NUM_RE.sub("#", prompt.lower().strip())


def slot_values(prompt: str) -> List[str]:
    return [match.group(0) for match in NUM_RE.finditer(prompt)]


def _value(text: str) -> float:
    return float(text)


def _agrees(value: Optional[float], gold: str) -> bool:
    """Two decimal places, the corpus's own resolution (§91.1)."""
    if value is None:
        return False
    try:
        expected = float(gold)
    except ValueError:
        return False
    return abs(round(value, 2) - round(expected, 2)) <= 1e-9


def fit_family(
    rows: Sequence[Tuple[str, str]],
) -> Dict[str, Any]:
    """Fit one digit-template family; drop it unless exactly one expression fits."""
    slots = [slot_values(q) for q, _ in rows]
    width = len(slots[0])
    if any(len(s) != width for s in slots):
        return {"status": "ragged-slots"}
    constant = [i for i in range(width) if len({s[i] for s in slots}) == 1]
    keep = [i for i in range(width) if i not in constant]
    if not keep:
        return {"status": "no-operands"}
    if len(keep) > 4:
        return {"status": "too-many-operands", "operands": len(keep)}
    scored = [
        (row, values, numeric_gold(gold)) for row, values, (_, gold) in zip(rows, slots, rows)
    ]
    keep_numeric = [(row, values, gold) for row, values, gold in scored if gold is not None]
    non_numeric = len(scored) - len(keep_numeric)
    if not keep_numeric:
        return {"status": "no-numeric-gold", "non_numeric": non_numeric}
    if non_numeric / len(scored) > MAX_NON_NUMERIC_SHARE:
        return {
            "status": "too-many-non-numeric",
            "non_numeric": non_numeric,
            "rows": len(scored),
        }
    operands = [[_value(values[i]) for i in keep] for _, values, _ in keep_numeric]
    golds = [gold for _, _, gold in keep_numeric]
    extra: List[Tuple[str, Callable[[Sequence[float]], Optional[float]]]] = []
    k = constant_factor(operands, golds)
    if k is not None:
        extra.append((f"x0*{k:g}", (lambda value: (lambda x: value * x[0]))(k)))
    fitted: List[str] = []
    for name, fn in _candidates(extra):
        if name.count("x") < len(keep):
            continue
        ok = True
        for x, gold in zip(operands, golds):
            if not _agrees(fn(x), f"{gold}"):
                ok = False
                break
        if ok:
            fitted.append(name)
    if not fitted:
        return {"status": "no-expression", "constant_slots": constant, "operands": len(keep)}
    if len(fitted) > 1:
        return {
            "status": "ambiguous",
            "fits": fitted,
            "constant_slots": constant,
            "operands": len(keep),
        }
    return {
        "status": "usable",
        "expression": fitted[0],
        "constant_slots": constant,
        "operands": len(keep),
        "non_numeric": non_numeric,
    }


def build_families(train: Sequence[Tuple[str, str]]) -> Dict[str, Dict[str, Any]]:
    grouped: Dict[str, List[Tuple[str, str]]] = {}
    for prompt, answer in train:
        grouped.setdefault(digit_template(prompt), []).append((prompt, answer))
    families: Dict[str, Dict[str, Any]] = {}
    for template, rows in grouped.items():
        if len(rows) < MIN_FAMILY_ROWS:
            continue
        families[template] = {"rows": rows, "n": len(rows), **fit_family(rows)}
    return families


def expression_value(expression: str, x: Sequence[float]) -> Optional[float]:
    """Evaluate a fitted expression; ``x0*<k>`` carries its corpus-solved k."""
    match = re.fullmatch(r"x0\*(-?\d+(?:\.\d+)?)", expression)
    if match:
        return float(match.group(1)) * float(x[0])
    for name, fn in _candidates():
        if name == expression:
            return fn(x)
    raise KeyError(expression)


# -- the counterfactual (§91.3) ---------------------------------------------
def _format_like(original: str, value: float) -> str:
    decimals = len(original.split(".")[1]) if "." in original else 0
    if decimals == 0:
        return str(int(round(value)))
    return f"{value:.{decimals}f}"


def _int_digits(value: float) -> int:
    return len(str(abs(int(value)))) if abs(value) >= 1 else 1


def _bump(text: str, value: float, step: int) -> Optional[float]:
    """Raise the leading digit by ``step``, keeping the integer digit count."""
    scale = 10 ** (_int_digits(value) - 1)
    new = value + step * scale
    if _int_digits(new) != _int_digits(value):
        return None
    if _format_like(text, new) == text:
        return None
    return new


def perturb(
    prompt: str,
    family: Dict[str, Any],
    attempts: Sequence[int],
    train_prompts: set,
) -> Optional[Dict[str, Any]]:
    """Rewrite the operands so the arithmetic changes but its shape does not.

    Ratio families move the numerator by a multiple of the denominator (the
    quotient stays an integer and shifts by a known amount); everything else
    raises each operand's leading digit, so the digit count — and therefore the
    magnitude class of both the operands and the answer — is unchanged. A step
    is accepted only when the gold changes, the integer/decimal class is
    preserved, and the perturbed prompt never occurs in training.
    """
    template = family["template"]
    slots = slot_values(prompt)
    keep = [i for i in range(len(slots)) if i not in family["constant_slots"]]
    x = [_value(slots[i]) for i in keep]
    gold_before = expression_value(family["expression"], x)
    if gold_before is None:
        return None
    gold_is_integer = abs(gold_before - round(gold_before)) <= 1e-9
    expression = family["expression"]

    strategies: List[Tuple[str, Sequence[int]]] = []
    if expression in ("x0/x1", "x1/x0"):
        strategies.append(("numerator", attempts))
    else:
        strategies.append(("all", attempts))
        # differences are translation-invariant: bumping every operand leaves the
        # gold unchanged, so the same ladder moves one side at a time instead.
        strategies.append(("first", attempts))

    for strategy, steps in strategies:
        for step in steps:
            new_slots = list(slots)
            if strategy == "numerator":
                numerator, denominator = (0, 1) if expression == "x0/x1" else (1, 0)
                moved = x[:]
                moved[numerator] = x[numerator] + step * x[denominator]
                new_x = moved
            else:
                targets = range(len(x)) if strategy == "all" else range(min(1, len(x)))
                bumped = [
                    _bump(slots[keep[position]], value, step) if position in targets else value
                    for position, value in enumerate(x)
                ]
                if any(value is None for value in bumped):
                    continue
                new_x = [float(value) for value in bumped]
            for position, value in zip(keep, new_x):
                new_slots[position] = _format_like(slots[position], value)
            text = _rewrite(prompt, new_slots)
            if text in train_prompts:
                continue
            gold_after = expression_value(expression, new_x)
            if gold_after is None:
                continue
            if abs(gold_after - gold_before) <= 1e-9:
                continue
            if (abs(gold_after - round(gold_after)) <= 1e-9) != gold_is_integer:
                continue
            return {
                "q": text,
                "gold": _gold_text(gold_after, gold_before),
                "step": step,
                "strategy": strategy,
                "expression": expression,
            }
    return None


def _gold_text(value: float, like: float) -> str:
    if abs(like - round(like)) <= 1e-9 and abs(value - round(value)) <= 1e-9:
        return str(int(round(value)))
    text = f"{round(value, 2):.2f}".rstrip("0").rstrip(".")
    return text or "0"


def _rewrite(prompt: str, slots: Sequence[str]) -> str:
    out: List[str] = []
    last = 0
    for match, text in zip(NUM_RE.finditer(prompt), slots):
        out.append(prompt[last : match.start()])
        out.append(text)
        last = match.end()
    out.append(prompt[last:])
    return "".join(out)


# -- measurement ------------------------------------------------------------
def _score(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    correct = sum(1 for row in rows if row["exact_raw"])
    return {
        "n": len(rows),
        "correct": correct,
        "rate": round(correct / len(rows), 4) if rows else 0.0,
        "answered": sum(1 for row in rows if row["answered"]),
    }


def select_rows(
    pairs: Sequence[Tuple[str, str]],
    families: Dict[str, Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Hold-out rows whose family is usable and whose perturbation succeeded."""
    train_prompts = {q for family in families.values() for q, _ in family["rows"]}
    selected: List[Dict[str, Any]] = []
    dropped: Dict[str, int] = {}
    for index, (prompt, gold) in enumerate(pairs):
        template = digit_template(prompt)
        family = families.get(template)
        if family is None or family.get("status") != "usable":
            dropped["family-not-usable"] = dropped.get("family-not-usable", 0) + 1
            continue
        family = {**family, "template": template}
        moved = perturb(prompt, family, BUMP_LADDER + MULTIPLE_LADDER, train_prompts)
        if moved is None:
            dropped["no-perturbation"] = dropped.get("no-perturbation", 0) + 1
            continue
        selected.append(
            {
                "i": index,
                "template": template,
                "expression": moved["expression"],
                "q": prompt,
                "gold": gold,
                "q_cf": moved["q"],
                "gold_cf": moved["gold"],
                "step": moved["step"],
            }
        )
    return selected, dropped


def run_arm(
    kind: str,
    seed: int,
    selected: Sequence[Dict[str, Any]],
    control: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    path = CHECKPOINTS / f"{kind}_seed{seed}.pt"
    model = load_model(kind, path)
    started = time.time()

    original = measure_holdout(model, [(row["q"], row["gold"]) for row in selected])
    counterfactual = measure_holdout(model, [(row["q_cf"], row["gold_cf"]) for row in selected])
    control_original = measure_holdout(model, [(row["q"], row["gold"]) for row in control])
    control_counterfactual = measure_holdout(
        model, [(row["q_cf"], row["gold_cf"]) for row in control]
    )

    by_family: Dict[str, Dict[str, Any]] = {}
    for row, before, after in zip(selected, original, counterfactual):
        cell = by_family.setdefault(
            row["expression"], {"n": 0, "original": 0, "counterfactual": 0, "changed": 0}
        )
        cell["n"] += 1
        cell["original"] += int(before["exact_raw"])
        cell["counterfactual"] += int(after["exact_raw"])
        cell["changed"] += int(before["answer"].strip() != after["answer"].strip())

    changed = sum(
        1
        for before, after in zip(original, counterfactual)
        if before["answer"].strip() != after["answer"].strip()
    )
    return {
        "arm": kind,
        "seed": seed,
        "checkpoint": str(path.relative_to(REPO_ROOT)),
        "sha256": sha256_file(path),
        "seconds": round(time.time() - started, 1),
        "original": _score(original),
        "counterfactual": _score(counterfactual),
        "answer_changed": {"n": len(selected), "changed": changed},
        "control_original": _score(control_original),
        "control_counterfactual": _score(control_counterfactual),
        "by_expression": by_family,
        "rows": [
            {
                "i": row["i"],
                "expression": row["expression"],
                "q": row["q"],
                "gold": row["gold"],
                "answer": before["answer"],
                "correct": before["exact_raw"],
                "q_cf": row["q_cf"],
                "gold_cf": row["gold_cf"],
                "answer_cf": after["answer"],
                "correct_cf": after["exact_raw"],
                "step": row["step"],
            }
            for row, before, after in zip(selected, original, counterfactual)
        ],
    }


# -- decision (§91.5) -------------------------------------------------------
def verdict(runs: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    deciding = [run for run in runs if run["arm"] == DECIDING_ARM]
    if not deciding:
        return {"verdict": "not-decided-missing-arm", "arm": DECIDING_ARM}
    results: List[Dict[str, Any]] = []
    for run in deciding:
        original = int(run["original"]["correct"])
        counter = int(run["counterfactual"]["correct"])
        if original < MIN_CORRECT:
            label = "underpowered"
        elif counter >= max(5, 0.5 * original):
            label = "computes"
        elif counter < 0.25 * original:
            label = "imitates"
        else:
            label = "mixed"
        results.append(
            {
                "seed": run["seed"],
                "original": original,
                "counterfactual": counter,
                "n": run["original"]["n"],
                "label": label,
            }
        )
    labels = {cell["label"] for cell in results}
    if labels == {"computes"}:
        overall = "computes"
    elif labels == {"imitates"}:
        overall = "imitates"
    elif "underpowered" in labels:
        overall = "underpowered"
    else:
        overall = "mixed"
    return {
        "verdict": overall,
        "arm": DECIDING_ARM,
        "per_seed": results,
        "rule": {
            "computes": "counterfactual >= max(5, 50% of original), every deciding seed",
            "imitates": "counterfactual < 25% of original, every deciding seed",
            "mixed": "between the two",
            "underpowered": f"fewer than {MIN_CORRECT} correct original rows",
        },
    }


# -- run --------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument("--plan", action="store_true", help="coverage only: no model, no scores")
    ap.add_argument("--check", default="")
    return ap


def write_report(out_dir: Path, report: Dict[str, Any]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def plan(args: argparse.Namespace) -> Dict[str, Any]:
    train = read_pairs(TRAIN)
    holdout = read_pairs(HOLDOUT)
    families = build_families(train)
    by_status: Dict[str, int] = {}
    for family in families.values():
        by_status[family["status"]] = by_status.get(family["status"], 0) + 1
    selected, dropped = select_rows(holdout, families)
    usable_rows = sum(f["n"] for f in families.values() if f["status"] == "usable")
    report = {
        "stage": "plan",
        "train_rows": len(train),
        "train_digest": rows_digest(train),
        "holdout_rows": len(holdout),
        "holdout_digest": rows_digest(holdout),
        "min_family_rows": MIN_FAMILY_ROWS,
        "families_considered": len(families),
        "families_by_status": by_status,
        "usable_family_rows_in_train": usable_rows,
        "holdout_rows_selected": len(selected),
        "holdout_rows_dropped": dropped,
        "by_expression": _count(selected, "expression"),
        "families": {
            template: {key: value for key, value in family.items() if key not in ("rows",)}
            for template, family in sorted(families.items())
        },
    }
    print(
        f"families {len(families)} {by_status} -> usable rows in train {usable_rows}; "
        f"hold-out selected {len(selected)}/{len(holdout)} dropped {dropped}",
        flush=True,
    )
    for expression, count in sorted(_count(selected, "expression").items(), key=lambda kv: -kv[1]):
        print(f"  {expression:14s} {count}", flush=True)
    write_report(Path(args.out_dir), report)
    return report


def _count(rows: Sequence[Dict[str, Any]], key: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for row in rows:
        out[str(row[key])] = out.get(str(row[key]), 0) + 1
    return out


def _control_rows(families: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deterministic sample of memorised training rows, same treatment (§91.4)."""
    train_prompts = {q for family in families.values() for q, _ in family["rows"]}
    pool: List[Tuple[str, str, Dict[str, Any]]] = []
    for template in sorted(families):
        family = families[template]
        if family["status"] != "usable":
            continue
        for prompt, gold in family["rows"]:
            pool.append((prompt, gold, family))
    step = max(1, len(pool) // CONTROL_ROWS)
    chosen: List[Dict[str, Any]] = []
    for prompt, gold, family in pool[::step][:CONTROL_ROWS]:
        moved = perturb(
            prompt,
            {**family, "template": digit_template(prompt)},
            BUMP_LADDER + MULTIPLE_LADDER,
            train_prompts,
        )
        if moved is None:
            continue
        chosen.append({"q": prompt, "gold": gold, "q_cf": moved["q"], "gold_cf": moved["gold"]})
    return chosen


def run(args: argparse.Namespace) -> Dict[str, Any]:
    train = read_pairs(TRAIN)
    holdout = read_pairs(HOLDOUT)
    families = build_families(train)
    selected, dropped = select_rows(holdout, families)
    control = _control_rows(families)
    print(f"selected {len(selected)} hold-out rows, control {len(control)} train rows", flush=True)

    report: Dict[str, Any] = {
        "stage": "scored",
        "train_digest": rows_digest(train),
        "holdout_digest": rows_digest(holdout),
        "selected_digest": hashlib.sha256(
            json.dumps([[r["q"], r["q_cf"]] for r in selected], ensure_ascii=False).encode("utf-8")
        ).hexdigest(),
        "selected": len(selected),
        "dropped": dropped,
        "control": len(control),
        "families_by_status": _count([{"s": f["status"]} for f in families.values()], "s"),
        "runs": [],
    }
    out_dir = Path(args.out_dir)
    started = time.time()
    for kind, seed in ARMS:
        print(f"\n== {kind} seed {seed} ==", flush=True)
        row = run_arm(kind, seed, selected, control)
        print(
            f"   original {row['original']['correct']}/{row['original']['n']}"
            f"  counterfactual {row['counterfactual']['correct']}/{row['counterfactual']['n']}"
            f"  changed {row['answer_changed']['changed']}/{row['answer_changed']['n']}"
            f"  control {row['control_original']['correct']}->{row['control_counterfactual']['correct']}"
            f"  ({row['seconds']}s)",
            flush=True,
        )
        report["runs"].append(row)
        write_report(out_dir, report)
    report["seconds"] = round(time.time() - started, 1)
    report["decision"] = verdict(report["runs"])
    path = write_report(out_dir, report)
    print(f"\nwrote {path}", flush=True)
    print(json.dumps(report["decision"], ensure_ascii=False, indent=2), flush=True)
    return report


def check(report_path: Path) -> Tuple[bool, str]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    problems: List[str] = []
    if report.get("stage") != "scored":
        return False, "this is a --plan report; there is nothing to check"
    if report["holdout_digest"] != rows_digest(read_pairs(HOLDOUT)):
        problems.append("hold-out rows changed since the run")
    if report["train_digest"] != rows_digest(read_pairs(TRAIN)):
        problems.append("training rows changed since the run")
    for run in report["runs"]:
        rows = run["rows"]
        for key, column in (("original", "correct"), ("counterfactual", "correct_cf")):
            got = sum(1 for row in rows if row[column])
            if got != run[key]["correct"]:
                problems.append(f"{run['arm']} seed{run['seed']}: {key} does not recompute")
        changed = sum(1 for row in rows if row["answer"].strip() != row["answer_cf"].strip())
        if changed != run["answer_changed"]["changed"]:
            problems.append(f"{run['arm']} seed{run['seed']}: changed count does not recompute")
        path = REPO_ROOT / run["checkpoint"]
        if not path.is_file():
            problems.append(f"missing checkpoint {run['checkpoint']}")
        elif sha256_file(path) != run["sha256"]:
            problems.append(f"sha256 changed for {run['checkpoint']}")
        # every perturbed prompt must differ, and its gold must differ too
        for row in rows:
            if row["q"].strip() == row["q_cf"].strip():
                problems.append(f"{run['arm']} seed{run['seed']}: row {row['i']} was not perturbed")
                break
            if str(row["gold"]).strip() == str(row["gold_cf"]).strip():
                problems.append(f"{run['arm']} seed{run['seed']}: row {row['i']} gold unchanged")
                break
    if verdict(report["runs"])["verdict"] != report["decision"]["verdict"]:
        problems.append("decision does not recompute")
    first = report["runs"][0]
    model = load_model(first["arm"], REPO_ROOT / first["checkpoint"])
    rerun = measure_holdout(model, [(row["q"], row["gold"]) for row in first["rows"]])
    differing = sum(1 for a, b in zip(rerun, first["rows"]) if a["answer"] != b["answer"])
    if differing:
        problems.append(f"original answers regenerated differently on {differing} rows")
    if problems:
        return False, "; ".join(problems)
    return True, (
        f"check OK ({len(report['runs'])} arms recomputed, "
        f"{first['arm']} seed{first['seed']} original rows re-run row-for-row)"
    )


def main() -> int:
    args = build_parser().parse_args()
    if args.check:
        ok, message = check(Path(args.check))
        print(message)
        return 0 if ok else 1
    if args.plan:
        plan(args)
        return 0
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
