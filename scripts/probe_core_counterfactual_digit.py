#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# LAYER: learning
# =============================================================================
"""§94: is §93's boundary the operand's width, or the size of the move?

§93 changed a digit and found a sharp edge: rows whose operands are all single
digit survive (10/14 and 9/14), rows with any operand > 9 never do (0/18 and
0/20 of the originally-correct rows). That reading carries one confound, and it
is the first one a careful reader raises: the single-digit perturbations move a
number by **1**, the multi-digit ones move it by **10 or 100**. So the edge
might be the size of the jump, not the width of the operand.

This stage removes that confound by changing exactly one thing - the
perturbation - and leaving the population, the grammar, the checkpoints, the
measurement call and the decision shape alone:

* every row gets **one** operand moved by exactly **one unit**: the units digit,
  +/-1, digit count preserved (14 -> 15, 19 -> 18, 10 -> 11);
* rows are then split by the width of the operand that carried the move:
  - ``control``   - the moved operand is single digit -> jump 1, width 1
  - ``treatment`` - the moved operand is >= 2 digits   -> jump 1, width >= 2

Both groups move the number by the same absolute amount, so "how far the number
moved" cannot explain a difference between them. What can is the operand's
width. The operand is chosen mechanically (first multi-digit operand, else the
first operand), never by whether the row was answered correctly, so the split is
not downstream of the scores.

Predictions, written before scoring (CORE_GAP_ANALYSIS.md §94.5):

* P1 - the verdict is ``operand-width``: treatment survival <= 25% while the
  control keeps >= 50% of its originally-correct rows.
* P2 - the control reproduces §93's single-digit survivors (roughly 10/14 and
  9/14, different rows because the move is one operand instead of all).
* P3 - ``answer_changed`` >= 80% in both groups: the answers do move, so a low
  survival cannot be "it ignored the prompt".

If P1 fails in the direction of ``change-size`` (treatment survival >= 50%),
then §93's boundary was the jump and §93.9/§93.10 have to be revised: the edge
would be "how far the number moved", not "the 9x9 table". That revision is
written into the same section, not into a new one.

This is **not** a fourth instrument chasing power. §93 already had power (32 and
34 originally-correct rows); this is a confound check on §93's own conclusion.
No training, no threshold change, no core-score change.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import probe_core_counterfactual as base  # noqa: E402
import probe_core_counterfactual_grammar as gram  # noqa: E402
import probe_core_counterfactual_shape as sh  # noqa: E402
from probe_core_callers import measure_holdout, rows_digest, sha256_file  # noqa: E402
from probe_core_recipe_ab import load_model  # noqa: E402
from train_token_snn import read_pairs  # noqa: E402

TRAIN = sh.TRAIN
HOLDOUT = sh.HOLDOUT
CHECKPOINTS = sh.CHECKPOINTS
OUT_DIR = REPO_ROOT / "data" / "e6_digit"

ARMS = sh.ARMS
DECIDING_ARM = sh.DECIDING_ARM

#: §94 - §93's floor and the same 25/50 shape, plus the gap that makes
#: ``operand-width`` require the control to actually behave differently.
MIN_CORRECT = sh.MIN_CORRECT
IMITATES_SHARE = 0.25
COMPUTES_SHARE = 0.50
MIN_GAP = 0.30

TREATMENT = "treatment-multidigit"
CONTROL = "control-single"


# -- the perturbation (§94.2) ----------------------------------------------
def _width(slot: str) -> int:
    """Digits left of the decimal point. ``"14"`` -> 2, ``"0.5"`` -> 1."""
    return len(slot.split(".")[0].lstrip("-"))


def _units_step(slot: str) -> Optional[int]:
    """+1 unless the units digit is 9, in which case -1.

    Both keep the digit count: 14->15, 19->18, 10->11. A decimal slot is not
    moved, because "the units digit" is not meaningful for a constant scale and
    this corpus keeps constants in ``constant_slots`` anyway.
    """
    if "." in slot:
        return None
    return -1 if int(slot[-1]) == 9 else 1


def perturb_units(
    prompt: str, family: Dict[str, Any], train_prompts: set
) -> Optional[Dict[str, Any]]:
    """Move one operand's units digit by one; keep the gold truthful.

    The guards are §92's: the new gold must actually differ, the integer /
    decimal class must be preserved, the perturbed prompt must not occur in
    training, and **every** expression that fits the family's training rows must
    agree on the new gold (otherwise "the truth" would depend on which
    equivalent fit was picked).
    """
    slots = base.slot_values(prompt)
    keep = [i for i in range(len(slots)) if i not in family["constant_slots"]]
    if not keep:
        return None
    x = [float(slots[i]) for i in keep]
    node = gram.as_node(family["node"])
    gold_before = gram.evaluate(node, x)
    if gold_before is None:
        return None

    movable = [index for index in keep if _units_step(slots[index]) is not None]
    if not movable:
        return None
    # Mechanical choice, independent of the answer: the first multi-digit
    # operand; if the row has none, the first operand (that is the control).
    multi = [index for index in movable if _width(slots[index]) >= 2]
    chosen = multi[0] if multi else movable[0]
    step = _units_step(slots[chosen])
    if step is None:
        return None

    new_value = float(slots[chosen]) + step
    moved_text = base._format_like(slots[chosen], new_value)
    if moved_text == slots[chosen] or _width(moved_text) != _width(slots[chosen]):
        return None

    new_slots = list(slots)
    new_slots[chosen] = moved_text
    text = base._rewrite(prompt, new_slots)
    if text == prompt or text in train_prompts:
        return None

    position = keep.index(chosen)
    new_x = list(x)
    new_x[position] = new_value
    gold_after = gram.evaluate(node, new_x)
    if gold_after is None:
        return None
    if abs(gold_after - gold_before) <= 1e-9:
        return None
    gold_is_integer = abs(gold_before - round(gold_before)) <= 1e-9
    if (abs(gold_after - round(gold_after)) <= 1e-9) != gold_is_integer:
        return None
    others = [gram.as_node(other) for other in family.get("nodes") or [family["node"]]]
    for other in others:
        value = gram.evaluate(other, new_x)
        if value is None or not base._agrees(value, f"{gold_after}"):
            return None

    return {
        "q": text,
        "gold": base._gold_text(gold_after, gold_before),
        "step": step,
        "strategy": f"units:{position}",
        "moved_width": _width(moved_text),
        "moved_slot": moved_text,
        "expression": family["expression"],
    }


# -- population (§94.3) -----------------------------------------------------
def build_rows(
    families: Dict[str, Dict[str, Any]], selected: Sequence[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Attach the units move to §93's 177 rows; nothing else is reselected."""
    train_prompts = {q for family in families.values() for q, _ in family["rows"]}
    rows: List[Dict[str, Any]] = []
    dropped: Dict[str, int] = {}
    for row in selected:
        family = families[row["template"]]
        moved = perturb_units(row["q"], family, train_prompts)
        if moved is None:
            reason = "no-units-move"
            dropped[reason] = dropped.get(reason, 0) + 1
            continue
        rows.append(
            {
                **row,
                "q_cf": moved["q"],
                "gold_cf": moved["gold"],
                "step": moved["step"],
                "strategy": moved["strategy"],
                "moved_width": moved["moved_width"],
                "moved_slot": moved["moved_slot"],
                "node": family["node"],
            }
        )
    return rows, dropped


def _empty() -> Dict[str, Any]:
    return {"n": 0, "correct": 0, "both": 0, "answer_changed": 0, "answers": []}


def run_arm(kind: str, seed: int, rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    path = CHECKPOINTS / f"{kind}_seed{seed}.pt"
    model = load_model(kind, path)
    started = time.time()
    before = measure_holdout(model, [(row["q"], row["gold"]) for row in rows])
    after = measure_holdout(model, [(row["q_cf"], row["gold_cf"]) for row in rows])

    groups: Dict[str, Dict[str, Any]] = {CONTROL: _empty(), TREATMENT: _empty()}
    detail: List[Dict[str, Any]] = []
    for row, first, second in zip(rows, before, after):
        key = TREATMENT if row["moved_width"] >= 2 else CONTROL
        cell = groups[key]
        cell["n"] += 1
        cell["correct"] += int(first["exact_raw"])
        cell["both"] += int(first["exact_raw"] and second["exact_raw"])
        changed = first["answer"].strip() != second["answer"].strip()
        cell["answer_changed"] += int(changed)
        detail.append(
            {
                "i": row["i"],
                "template": row["template"],
                "group": key,
                "moved_width": row["moved_width"],
                "moved_slot": row["moved_slot"],
                "step": row["step"],
                "expression": row["expression"],
                "q": row["q"],
                "gold": row["gold"],
                "answer": first["answer"],
                "correct": first["exact_raw"],
                "q_cf": row["q_cf"],
                "gold_cf": row["gold_cf"],
                "answer_cf": second["answer"],
                "correct_cf": second["exact_raw"],
                "changed": changed,
            }
        )
    for cell in groups.values():
        cell["answers"] = sorted(set(cell["answers"]))
        cell["survival"] = round(cell["both"] / cell["correct"], 4) if cell["correct"] else 0.0
    return {
        "arm": kind,
        "seed": seed,
        "checkpoint": str(path.relative_to(REPO_ROOT)),
        "sha256": sha256_file(path),
        "seconds": round(time.time() - started, 1),
        "original": {
            "n": len(rows),
            "correct": sum(1 for row in before if row["exact_raw"]),
        },
        "counterfactual": {
            "n": len(rows),
            "correct": sum(1 for row in after if row["exact_raw"]),
        },
        "groups": groups,
        "rows": detail,
    }


# -- decision (§94.4) -------------------------------------------------------
def wilson(hits: int, total: int, z: float = 1.96) -> Tuple[float, float]:
    if total <= 0:
        return 0.0, 0.0
    p = hits / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    spread = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return max(0.0, centre - spread), min(1.0, centre + spread)


def verdict(runs: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    deciding = [run for run in runs if run["arm"] == DECIDING_ARM]
    per_seed: List[Dict[str, Any]] = []
    for run in deciding:
        treatment = run["groups"][TREATMENT]
        control = run["groups"][CONTROL]
        if treatment["correct"] < MIN_CORRECT:
            label = "underpowered"
        elif treatment["survival"] >= COMPUTES_SHARE:
            label = "change-size"
        elif (
            treatment["survival"] <= IMITATES_SHARE
            and control["survival"] >= COMPUTES_SHARE
            and control["survival"] - treatment["survival"] >= MIN_GAP
        ):
            label = "operand-width"
        else:
            label = "mixed"
        low, high = wilson(treatment["both"], treatment["correct"])
        per_seed.append(
            {
                "seed": run["seed"],
                "treatment": {
                    "n": treatment["n"],
                    "original": treatment["correct"],
                    "both": treatment["both"],
                    "survival": treatment["survival"],
                    "wilson": [round(low, 4), round(high, 4)],
                },
                "control": {
                    "n": control["n"],
                    "original": control["correct"],
                    "both": control["both"],
                    "survival": control["survival"],
                },
                "label": label,
            }
        )
    labels = {entry["label"] for entry in per_seed}
    if "underpowered" in labels:
        overall = "underpowered"
    elif len(labels) == 1:
        overall = labels.pop()
    else:
        overall = "mixed"
    return {
        "verdict": overall,
        "arm": DECIDING_ARM,
        "per_seed": per_seed,
        "rule": {
            "underpowered": f"fewer than {MIN_CORRECT} original-correct rows in the treatment group",
            "change-size": f"treatment survival >= {COMPUTES_SHARE} (the jump, not the width)",
            "operand-width": (
                f"treatment survival <= {IMITATES_SHARE}, control survival >= "
                f"{COMPUTES_SHARE}, and the gap >= {MIN_GAP}"
            ),
            "mixed": "between the two",
        },
    }


# -- entry points -----------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument("--plan", action="store_true", help="coverage only: no model")
    ap.add_argument("--check", default="")
    return ap


def _prepare() -> Tuple[
    List[Tuple[str, str]],
    List[Tuple[str, str]],
    Dict[str, Dict[str, Any]],
    List[Dict[str, Any]],
    Dict[str, int],
]:
    train = read_pairs(TRAIN)
    holdout = read_pairs(HOLDOUT)
    families = sh.build_families(train)
    selected, _ = sh.select_rows(holdout, families)
    rows, dropped = build_rows(families, selected)
    return train, holdout, families, rows, dropped


def plan(args: argparse.Namespace) -> Dict[str, Any]:
    train, holdout, families, rows, dropped = _prepare()
    groups = {CONTROL: 0, TREATMENT: 0}
    for row in rows:
        groups[TREATMENT if row["moved_width"] >= 2 else CONTROL] += 1
    report = {
        "stage": "plan",
        "oracle": "digit-units",
        "perturbation": "one operand, units digit +/-1, digit count preserved",
        "train_rows": len(train),
        "train_digest": rows_digest(train),
        "holdout_rows": len(holdout),
        "holdout_digest": rows_digest(holdout),
        "population": "§93 selection (shape-keyed, already registered)",
        "selected": len(rows),
        "dropped": dropped,
        "groups": groups,
        "by_moved_width": _count(rows, "moved_width"),
        "by_strategy": _count(rows, "strategy"),
        "by_expression": _count(rows, "expression"),
        "by_step": _count(rows, "step"),
    }
    print(
        f"§93 population {len(rows)} rows -> treatment {groups[TREATMENT]}, "
        f"control {groups[CONTROL]}, dropped {dropped}",
        flush=True,
    )
    for key in ("by_moved_width", "by_expression", "by_step"):
        print(f"  {key}: {report[key]}", flush=True)
    gram.write_report(Path(args.out_dir), report)
    return report


def run(args: argparse.Namespace) -> Dict[str, Any]:
    train, holdout, families, rows, dropped = _prepare()
    groups = {CONTROL: 0, TREATMENT: 0}
    for row in rows:
        groups[TREATMENT if row["moved_width"] >= 2 else CONTROL] += 1
    print(
        f"population {len(rows)} rows (treatment {groups[TREATMENT]}, "
        f"control {groups[CONTROL]}, dropped {dropped})",
        flush=True,
    )
    report: Dict[str, Any] = {
        "stage": "scored",
        "oracle": "digit-units",
        "train_digest": rows_digest(train),
        "holdout_digest": rows_digest(holdout),
        "selected": len(rows),
        "dropped": dropped,
        "groups": groups,
        "by_moved_width": _count(rows, "moved_width"),
        "runs": [],
    }
    out_dir = Path(args.out_dir)
    started = time.time()
    for kind, seed in ARMS:
        print(f"\n== {kind} seed {seed} ==", flush=True)
        row = run_arm(kind, seed, rows)
        treat = row["groups"][TREATMENT]
        ctrl = row["groups"][CONTROL]
        print(
            f"   original {row['original']['correct']}/{row['original']['n']}"
            f"  counterfactual {row['counterfactual']['correct']}/{row['counterfactual']['n']}",
            flush=True,
        )
        print(
            f"   treatment ({treat['n']} rows, {treat['correct']} originally correct): "
            f"both {treat['both']}  changed {treat['answer_changed']}",
            flush=True,
        )
        print(
            f"   control   ({ctrl['n']} rows, {ctrl['correct']} originally correct): "
            f"both {ctrl['both']}  changed {ctrl['answer_changed']}",
            flush=True,
        )
        report["runs"].append(row)
        gram.write_report(out_dir, report)
    report["seconds"] = round(time.time() - started, 1)
    report["decision"] = verdict(report["runs"])
    path = gram.write_report(out_dir, report)
    print(f"\nwrote {path}", flush=True)
    print(json.dumps(report["decision"], ensure_ascii=False, indent=2), flush=True)
    return report


def _count(rows: Sequence[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        name = str(row[key])
        counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items()))


def check(report_path: Path) -> Tuple[bool, str]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("stage") != "scored":
        return False, "this is a --plan report; there is nothing to check"
    if report.get("oracle") != "digit-units":
        return False, "this report was not produced by the units instrument"
    problems: List[str] = []
    train, holdout, families, rows, dropped = _prepare()
    if report["holdout_digest"] != rows_digest(holdout):
        problems.append("hold-out rows changed since the run")
    if report["train_digest"] != rows_digest(train):
        problems.append("training rows changed since the run")
    if report["selected"] != len(rows) or report["dropped"] != dropped:
        problems.append("selection does not recompute")
    by_i = {row["i"]: row for row in rows}
    for run in report["runs"]:
        for key, column in (("original", "correct"), ("counterfactual", "correct_cf")):
            got = sum(1 for row in run["rows"] if row[column])
            if got != run[key]["correct"]:
                problems.append(f"{run['arm']} seed{run['seed']}: {key} does not recompute")
        for group, cell in run["groups"].items():
            members = [row for row in run["rows"] if row["group"] == group]
            if len(members) != cell["n"]:
                problems.append(f"{run['arm']} seed{run['seed']}: {group} count changed")
                break
            if sum(1 for row in members if row["correct"]) != cell["correct"]:
                problems.append(f"{run['arm']} seed{run['seed']}: {group} originals changed")
                break
            if sum(1 for row in members if row["correct"] and row["correct_cf"]) != cell["both"]:
                problems.append(f"{run['arm']} seed{run['seed']}: {group} both changed")
                break
            if sum(1 for row in members if row["changed"]) != cell["answer_changed"]:
                problems.append(f"{run['arm']} seed{run['seed']}: {group} changed count")
                break
        path = REPO_ROOT / run["checkpoint"]
        if not path.is_file():
            problems.append(f"missing checkpoint {run['checkpoint']}")
        elif sha256_file(path) != run["sha256"]:
            problems.append(f"sha256 changed for {run['checkpoint']}")
        for row in run["rows"]:
            source = by_i.get(row["i"])
            if source is None:
                problems.append(f"row {row['i']} is no longer selected")
                break
            if source["q_cf"] != row["q_cf"] or source["gold_cf"] != row["gold_cf"]:
                problems.append(f"row {row['i']} perturbation does not recompute")
                break
            if row["moved_width"] != _width(row["moved_slot"]):
                problems.append(f"row {row['i']} width is inconsistent")
                break
            if (row["group"] == TREATMENT) != (row["moved_width"] >= 2):
                problems.append(f"row {row['i']} group is inconsistent with its width")
                break
            expected_width = len(str(abs(int(float(row["moved_slot"])))))
            if expected_width != row["moved_width"]:
                problems.append(f"row {row['i']} moved a digit count")
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
