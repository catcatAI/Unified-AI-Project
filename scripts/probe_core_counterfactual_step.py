#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# LAYER: learning
# =============================================================================
"""§95: does a 10-unit move die because it is big, or because it leaves support?

§93 bumped the leading digit (14 -> 24, a move of 10) on rows whose operands were
multi-digit and found 0 survivors. §94 moved one operand by a single unit and
found 5 of 11 and 7 of 15 of the *same* rows alive. That refuted "the edge is the
operand's width" but left two explanations sharing every death and every survival:

* **jump size** - a move of 10 leaves the model's competence, a move of 1 does
  not;
* **support** - a move of 10 takes the operand pair outside the set of pairs the
  model was trained on (the word-problem family only ever uses x0 in 2..9 and x1
  in 3..15), while a move of 1 can stay inside it.

§94 could not separate them because its perturbations left support *and* grew the
jump at the same time. This stage holds support fixed and varies only the size:

* population: the ``x0*x1`` rows of §93's selection whose original pair is inside
  the trained support (x0 in 2..9, x1 in 3..15);
* the same operand (x1, the multiplicand) is moved by **+/-1** and by **+/-10**,
  the sign chosen mechanically so that both endpoints stay inside the support;
* every perturbed pair is checked to be a pair that actually occurs in training
  (0 of the 24 are unseen), so "inside support" is exact rather than a box;
* grammar, checkpoints, measurement call, guards and ``max_new`` are §92's.

Because both moves keep both endpoints inside the trained support, the only
difference between the two arms is the magnitude of the move. If the 10-unit arm
survives like the 1-unit arm, jump size does not explain §93 and the support
reading stands; if it dies while the 1-unit arm lives, the edge is magnitude and
§94.8's reading has to be corrected in place.

This does **not** decide "stored products vs a multiplication algorithm": inside
the trained support both predict success, and the section says so. No training, no
threshold change, no core-score change.
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
OUT_DIR = REPO_ROOT / "data" / "e7_step"

ARMS = sh.ARMS
DECIDING_ARM = sh.DECIDING_ARM

#: §95 - §93's floor, and a two-sided rule: "survives" and "dies" are the same
#: 50/25 shape §91-§94 used, so no threshold is invented for this stage.
MIN_CORRECT = sh.MIN_CORRECT
SURVIVES_SHARE = 0.50
DIES_SHARE = 0.25

FAMILY_EXPRESSION = "x0*x1"
SUPPORT_X0 = (2, 9)
SUPPORT_X1 = (3, 15)

PAIRED = "paired-in-support"
LEAVES = "leaves-support"


# -- the support and the moves (§95.2) --------------------------------------
def in_support(x0: int, x1: int) -> bool:
    """The joint support of the word-problem family, not a per-value range."""
    return SUPPORT_X0[0] <= x0 <= SUPPORT_X0[1] and SUPPORT_X1[0] <= x1 <= SUPPORT_X1[1]


def step_sign(x1: int, delta: int) -> Optional[int]:
    """The signed step that keeps both ``x1`` and ``x1 + step`` inside support.

    ``delta=1`` always has one (3..15 is closed under moving towards the middle),
    ``delta=10`` only for 3..5 (up) and 13..15 (down), and never for 6..12.
    """
    for sign in (1, -1):
        step = sign * delta
        if SUPPORT_X1[0] <= x1 + step <= SUPPORT_X1[1]:
            return step
    return None


def move(
    prompt: str, family: Dict[str, Any], slot: int, delta: int, train_prompts: set
) -> Optional[Dict[str, Any]]:
    """Move one slot by ``delta`` and keep the gold truthful (§92's guards)."""
    slots = base.slot_values(prompt)
    keep = [i for i in range(len(slots)) if i not in family["constant_slots"]]
    if slot not in keep:
        return None
    if "." in slots[slot]:
        return None
    x = [float(slots[i]) for i in keep]
    node = gram.as_node(family["node"])
    gold_before = gram.evaluate(node, x)
    if gold_before is None:
        return None

    before = float(slots[slot])
    after = before + delta
    moved_text = base._format_like(slots[slot], after)
    if moved_text == slots[slot]:
        return None
    new_slots = list(slots)
    new_slots[slot] = moved_text
    text = base._rewrite(prompt, new_slots)
    if text == prompt or text in train_prompts:
        return None

    new_x = list(x)
    new_x[keep.index(slot)] = after
    gold_after = gram.evaluate(node, new_x)
    if gold_after is None or abs(gold_after - gold_before) <= 1e-9:
        return None
    before_integer = abs(gold_before - round(gold_before)) <= 1e-9
    if (abs(gold_after - round(gold_after)) <= 1e-9) != before_integer:
        return None
    for other in [gram.as_node(node_) for node_ in family.get("nodes") or [family["node"]]]:
        value = gram.evaluate(other, new_x)
        if value is None or not base._agrees(value, f"{gold_after}"):
            return None

    return {
        "q": text,
        "gold": base._gold_text(gold_after, gold_before),
        "delta": delta,
        "slot": slot,
    }


# -- population (§95.3) -----------------------------------------------------
def build_rows(
    families: Dict[str, Dict[str, Any]], selected: Sequence[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, int]]:
    """Paired rows (both moves legal) plus the descriptive leaves-support group."""
    train_prompts = {q for family in families.values() for q, _ in family["rows"]}
    paired: List[Dict[str, Any]] = []
    leaves: List[Dict[str, Any]] = []
    dropped: Dict[str, int] = {}
    for row in selected:
        family = families[row["template"]]
        if family.get("expression") != FAMILY_EXPRESSION:
            dropped["not-multiplication"] = dropped.get("not-multiplication", 0) + 1
            continue
        slots = base.slot_values(row["q"])
        keep = [i for i in range(len(slots)) if i not in family["constant_slots"]]
        if sorted(keep) != list(range(len(slots))):
            dropped["constant-operand"] = dropped.get("constant-operand", 0) + 1
            continue
        x0, x1 = int(float(slots[0])), int(float(slots[1]))
        if not in_support(x0, x1):
            dropped["outside-support"] = dropped.get("outside-support", 0) + 1
            continue

        sign1 = step_sign(x1, 1)
        sign10 = step_sign(x1, 10)
        moved1 = move(row["q"], family, keep[1], sign1, train_prompts) if sign1 else None
        if moved1 is None:
            dropped["no-one-unit-move"] = dropped.get("no-one-unit-move", 0) + 1
            continue
        if sign10 is None:
            # The descriptive group: a 10-unit move that must leave support.
            out_sign = 10 if x1 + 10 > SUPPORT_X1[1] else -10
            moved_out = move(row["q"], family, keep[1], out_sign, train_prompts)
            if moved_out is None:
                dropped["no-ten-unit-move"] = dropped.get("no-ten-unit-move", 0) + 1
            else:
                leaves.append(
                    {
                        **row,
                        "x0": x0,
                        "x1": x1,
                        "delta_out": moved_out["delta"],
                        "q_out": moved_out["q"],
                        "gold_out": moved_out["gold"],
                    }
                )
            continue
        moved10 = move(row["q"], family, keep[1], sign10, train_prompts)
        if moved10 is None:
            dropped["no-ten-unit-move"] = dropped.get("no-ten-unit-move", 0) + 1
            continue
        paired.append(
            {
                **row,
                "x0": x0,
                "x1": x1,
                "delta1": moved1["delta"],
                "delta10": moved10["delta"],
                "q1": moved1["q"],
                "gold1": moved1["gold"],
                "q10": moved10["q"],
                "gold10": moved10["gold"],
                "pair10": [x0, x1 + moved10["delta"]],
            }
        )
    return paired, leaves, dropped


def _empty() -> Dict[str, Any]:
    return {
        "n": 0,
        "original": 0,
        "one": 0,
        "ten": 0,
        "both": 0,
        "answer_changed_one": 0,
        "answer_changed_ten": 0,
    }


def run_arm(
    kind: str,
    seed: int,
    paired: Sequence[Dict[str, Any]],
    leaves: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    path = CHECKPOINTS / f"{kind}_seed{seed}.pt"
    model = load_model(kind, path)
    started = time.time()

    original = measure_holdout(model, [(row["q"], row["gold"]) for row in paired])
    one = measure_holdout(model, [(row["q1"], row["gold1"]) for row in paired])
    ten = measure_holdout(model, [(row["q10"], row["gold10"]) for row in paired])
    out_original = measure_holdout(model, [(row["q"], row["gold"]) for row in leaves])
    out_ten = measure_holdout(model, [(row["q_out"], row["gold_out"]) for row in leaves])

    cell = _empty()
    detail: List[Dict[str, Any]] = []
    for row, first, second, third in zip(paired, original, one, ten):
        cell["n"] += 1
        cell["original"] += int(first["exact_raw"])
        cell["one"] += int(first["exact_raw"] and second["exact_raw"])
        cell["ten"] += int(first["exact_raw"] and third["exact_raw"])
        cell["both"] += int(first["exact_raw"] and second["exact_raw"] and third["exact_raw"])
        changed_one = first["answer"].strip() != second["answer"].strip()
        changed_ten = first["answer"].strip() != third["answer"].strip()
        cell["answer_changed_one"] += int(changed_one)
        cell["answer_changed_ten"] += int(changed_ten)
        detail.append(
            {
                "i": row["i"],
                "template": row["template"],
                "x0": row["x0"],
                "x1": row["x1"],
                "delta1": row["delta1"],
                "delta10": row["delta10"],
                "q": row["q"],
                "gold": row["gold"],
                "answer": first["answer"],
                "correct": first["exact_raw"],
                "q1": row["q1"],
                "gold1": row["gold1"],
                "answer1": second["answer"],
                "correct1": second["exact_raw"],
                "q10": row["q10"],
                "gold10": row["gold10"],
                "answer10": third["answer"],
                "correct10": third["exact_raw"],
                "changed1": changed_one,
                "changed10": changed_ten,
            }
        )
    cell["survival_one"] = round(cell["one"] / cell["original"], 4) if cell["original"] else 0.0
    cell["survival_ten"] = round(cell["ten"] / cell["original"], 4) if cell["original"] else 0.0

    out_cell = _empty()
    out_detail: List[Dict[str, Any]] = []
    for row, first, second in zip(leaves, out_original, out_ten):
        out_cell["n"] += 1
        out_cell["original"] += int(first["exact_raw"])
        out_cell["ten"] += int(first["exact_raw"] and second["exact_raw"])
        out_cell["answer_changed_ten"] += int(first["answer"].strip() != second["answer"].strip())
        out_detail.append(
            {
                "i": row["i"],
                "template": row["template"],
                "x0": row["x0"],
                "x1": row["x1"],
                "delta_out": row["delta_out"],
                "q": row["q"],
                "gold": row["gold"],
                "answer": first["answer"],
                "correct": first["exact_raw"],
                "q_out": row["q_out"],
                "gold_out": row["gold_out"],
                "answer_out": second["answer"],
                "correct_out": second["exact_raw"],
            }
        )
    out_cell["survival_ten"] = (
        round(out_cell["ten"] / out_cell["original"], 4) if out_cell["original"] else 0.0
    )

    return {
        "arm": kind,
        "seed": seed,
        "checkpoint": str(path.relative_to(REPO_ROOT)),
        "sha256": sha256_file(path),
        "seconds": round(time.time() - started, 1),
        PAIRED: cell,
        LEAVES: out_cell,
        "rows": detail,
        "out_rows": out_detail,
    }


# -- decision (§95.4) -------------------------------------------------------
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
        cell = run[PAIRED]
        if cell["original"] < MIN_CORRECT:
            label = "underpowered"
        elif cell["survival_ten"] >= SURVIVES_SHARE:
            label = "support"
        elif cell["survival_ten"] <= DIES_SHARE and cell["survival_one"] >= SURVIVES_SHARE:
            label = "jump-size"
        else:
            label = "mixed"
        low, high = wilson(cell["ten"], cell["original"])
        per_seed.append(
            {
                "seed": run["seed"],
                "original": cell["original"],
                "one": cell["one"],
                "ten": cell["ten"],
                "survival_one": cell["survival_one"],
                "survival_ten": cell["survival_ten"],
                "wilson_ten": [round(low, 4), round(high, 4)],
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
            "underpowered": f"fewer than {MIN_CORRECT} originally-correct paired rows",
            "support": f"10-unit survival >= {SURVIVES_SHARE} with both endpoints in support",
            "jump-size": (
                f"10-unit survival <= {DIES_SHARE} and 1-unit survival >= {SURVIVES_SHARE}"
            ),
            "mixed": "between the two",
        },
    }


# -- entry points -----------------------------------------------------------
def _joint(rows: Sequence[Dict[str, Any]], column: str) -> int:
    """Originally correct **and** correct after the move (the stored cell's meaning)."""
    return sum(1 for row in rows if row["correct"] and row[column])


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
    List[Dict[str, Any]],
    Dict[str, int],
]:
    train = read_pairs(TRAIN)
    holdout = read_pairs(HOLDOUT)
    families = sh.build_families(train)
    selected, _ = sh.select_rows(holdout, families)
    paired, leaves, dropped = build_rows(families, selected)
    return train, holdout, families, paired, leaves, dropped


def _observed_pairs(families: Dict[str, Dict[str, Any]]) -> set:
    seen = set()
    for family in families.values():
        if family.get("expression") != FAMILY_EXPRESSION:
            continue
        for prompt, _ in family["rows"]:
            slots = base.slot_values(prompt)
            if len(slots) < 2:
                continue
            try:
                seen.add((int(float(slots[0])), int(float(slots[1]))))
            except ValueError:
                continue
    return seen


def _geometry(
    paired: Sequence[Dict[str, Any]], families: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    observed = _observed_pairs(families)
    unseen = [row["i"] for row in paired if tuple(row["pair10"]) not in observed]
    signs: Dict[str, int] = {}
    for row in paired:
        key = f"{row['delta10']:+d}"
        signs[key] = signs.get(key, 0) + 1
    return {
        "paired": len(paired),
        "signs_ten": dict(sorted(signs.items())),
        "unseen_pairs": len(unseen),
        "unseen_rows": unseen,
        "by_x1": _count(paired, "x1"),
    }


def _count(rows: Sequence[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        name = str(row[key])
        counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items()))


def plan(args: argparse.Namespace) -> Dict[str, Any]:
    train, holdout, families, paired, leaves, dropped = _prepare()
    geometry = _geometry(paired, families)
    report = {
        "stage": "plan",
        "oracle": "step-size",
        "support": {"x0": list(SUPPORT_X0), "x1": list(SUPPORT_X1)},
        "train_rows": len(train),
        "train_digest": rows_digest(train),
        "holdout_rows": len(holdout),
        "holdout_digest": rows_digest(holdout),
        "population": "§93 selection (shape-keyed, already registered)",
        "selected": len(paired),
        "dropped": dropped,
        "leaves_support": len(leaves),
        **geometry,
    }
    print(
        f"paired {len(paired)} rows (both a 1-unit and a 10-unit move stay in support); "
        f"leaves-support {len(leaves)}; dropped {dropped}",
        flush=True,
    )
    print(
        f"  10-unit signs: {geometry['signs_ten']}  unseen pairs: {geometry['unseen_pairs']}",
        flush=True,
    )
    print(f"  by x1: {geometry['by_x1']}", flush=True)
    gram.write_report(Path(args.out_dir), report)
    return report


def run(args: argparse.Namespace) -> Dict[str, Any]:
    train, holdout, families, paired, leaves, dropped = _prepare()
    geometry = _geometry(paired, families)
    print(
        f"paired {len(paired)} rows, leaves-support {len(leaves)}, dropped {dropped}",
        flush=True,
    )
    report: Dict[str, Any] = {
        "stage": "scored",
        "oracle": "step-size",
        "support": {"x0": list(SUPPORT_X0), "x1": list(SUPPORT_X1)},
        "train_digest": rows_digest(train),
        "holdout_digest": rows_digest(holdout),
        "selected": len(paired),
        "dropped": dropped,
        "leaves_support": len(leaves),
        **geometry,
        "runs": [],
    }
    out_dir = Path(args.out_dir)
    started = time.time()
    for kind, seed in ARMS:
        print(f"\n== {kind} seed {seed} ==", flush=True)
        row = run_arm(kind, seed, paired, leaves)
        cell = row[PAIRED]
        print(
            f"   paired {cell['n']} rows, {cell['original']} originally correct: "
            f"1-unit {cell['one']} ({cell['survival_one']}), "
            f"10-unit {cell['ten']} ({cell['survival_ten']})",
            flush=True,
        )
        print(
            f"   answer changed: 1-unit {cell['answer_changed_one']}/{cell['n']}, "
            f"10-unit {cell['answer_changed_ten']}/{cell['n']}",
            flush=True,
        )
        out_cell = row[LEAVES]
        print(
            f"   leaves-support {out_cell['n']} rows, {out_cell['original']} originally correct: "
            f"10-unit {out_cell['ten']} ({out_cell['survival_ten']})  [descriptive]",
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


def check(report_path: Path) -> Tuple[bool, str]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("stage") != "scored":
        return False, "this is a --plan report; there is nothing to check"
    if report.get("oracle") != "step-size":
        return False, "this report was not produced by the step-size instrument"
    problems: List[str] = []
    train, holdout, families, paired, leaves, dropped = _prepare()
    if report["holdout_digest"] != rows_digest(holdout):
        problems.append("hold-out rows changed since the run")
    if report["train_digest"] != rows_digest(train):
        problems.append("training rows changed since the run")
    if report["selected"] != len(paired) or report["dropped"] != dropped:
        problems.append("selection does not recompute")
    geometry = _geometry(paired, families)
    if report["signs_ten"] != geometry["signs_ten"]:
        problems.append("the 10-unit signs do not recompute")
    if report["unseen_pairs"] != geometry["unseen_pairs"]:
        problems.append("the unseen-pair count does not recompute")
    by_i = {row["i"]: row for row in paired}
    for run in report["runs"]:
        # `one` and `ten` are joint counts (originally correct *and* still correct
        # after the move); only `original` counts the first answer alone.
        for key, column in (("original", "correct"), ("one", "correct1"), ("ten", "correct10")):
            if key == "original":
                got = sum(1 for row in run["rows"] if row["correct"])
            else:
                got = _joint(run["rows"], column)
            if got != run[PAIRED][key]:
                problems.append(f"{run['arm']} seed{run['seed']}: {key} does not recompute")
        out_cell = run[LEAVES]
        for key, column in (("original", "correct"), ("ten", "correct_out")):
            if key == "original":
                got = sum(1 for row in run["out_rows"] if row["correct"])
            else:
                got = _joint(run["out_rows"], column)
            if got != out_cell[key]:
                problems.append(f"{run['arm']} seed{run['seed']}: leaves {key} does not recompute")
        if out_cell["survival_ten"] != (
            round(out_cell["ten"] / out_cell["original"], 4) if out_cell["original"] else 0.0
        ):
            problems.append(f"{run['arm']} seed{run['seed']}: leaves survival is wrong")
        cell = run[PAIRED]
        if cell["survival_one"] != (
            round(cell["one"] / cell["original"], 4) if cell["original"] else 0.0
        ):
            problems.append(f"{run['arm']} seed{run['seed']}: 1-unit survival is wrong")
        if cell["survival_ten"] != (
            round(cell["ten"] / cell["original"], 4) if cell["original"] else 0.0
        ):
            problems.append(f"{run['arm']} seed{run['seed']}: 10-unit survival is wrong")
        if sum(1 for row in run["rows"] if row["changed1"]) != cell["answer_changed_one"]:
            problems.append(f"{run['arm']} seed{run['seed']}: 1-unit changed count")
        if sum(1 for row in run["rows"] if row["changed10"]) != cell["answer_changed_ten"]:
            problems.append(f"{run['arm']} seed{run['seed']}: 10-unit changed count")
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
            if row["q1"] != source["q1"] or row["q10"] != source["q10"]:
                problems.append(f"row {row['i']} perturbation does not recompute")
                break
            if row["delta1"] not in (1, -1) or row["delta10"] not in (10, -10):
                problems.append(f"row {row['i']} moved by the wrong step")
                break
            if not in_support(row["x0"], row["x1"]):
                problems.append(f"row {row['i']} started outside support")
                break
            if not in_support(row["x0"], row["x1"] + row["delta1"]):
                problems.append(f"row {row['i']} left support on the 1-unit move")
                break
            if not in_support(row["x0"], row["x1"] + row["delta10"]):
                problems.append(f"row {row['i']} left support on the 10-unit move")
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
