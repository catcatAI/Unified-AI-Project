#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# LAYER: learning
# =============================================================================
"""§93: the counterfactual, on the one population where power exists.

§91 and §92 both came back `underpowered`: 8/6 and 9/7 correct original rows on
the rows an oracle could fit from the training corpus, against a registered floor
of 10. §92.9 measured why the floor could not be reached there: the 248 hold-out
rows mix two populations.

* templates with >= 8 training rows: fittable, measurable, and the model is
  almost always wrong (9 and 7 of 135);
* templates with 0-7 training rows: not fittable at all, and the model is right
  most often (25 and 28 of 113).

This stage changes one thing: the family key. Instead of ``digit_template``
(which keeps the nouns, so "Lina has 7 drawers with 8 seeds" and "Ken has 8 bins
with 3 ribbons" are different templates), the key is the *shape* - every run of
ASCII letters becomes ``w``. The 286-row word-problem shape then has enough rows
to fit, and the rows it covers are the ones the model answers correctly, so the
counterfactual can be decided instead of being underpowered.

What this answers, and what it does not:

* it answers "given a correct answer on this population, does it survive a
  digit change?" - which is exactly the computes/imitates question;
* it does **not** estimate the model's overall accuracy, and it does **not**
  relabel §91 or §92. The multi-digit arithmetic population stays unmeasurable
  at this capability, and that is recorded, not papered over;
* the population was chosen after §92.9 showed where power exists, and that is
  declared. The original-accuracy leg is therefore **not blind** (§90's stored
  answers already say 32 and 34 rows are correct). The counterfactual leg is
  blind: no perturbed answer has been looked at.

Everything else - the grammar, the fit rule, the perturbation guards, the
thresholds, the decision rule - is §92's, imported rather than copied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import probe_core_counterfactual as base  # noqa: E402
import probe_core_counterfactual_grammar as gram  # noqa: E402
from probe_core_callers import rows_digest, sha256_file  # noqa: E402
from probe_core_recipe_ab import load_model  # noqa: E402
from train_token_snn import read_pairs  # noqa: E402

TRAIN = gram.TRAIN
HOLDOUT = gram.HOLDOUT
CHECKPOINTS = gram.CHECKPOINTS
OUT_DIR = REPO_ROOT / "data" / "e5_shape"

ARMS = gram.ARMS
DECIDING_ARM = gram.DECIDING_ARM

#: §93 — §92's constants, unchanged. The floor still speaks.
MIN_FAMILY_ROWS = gram.MIN_FAMILY_ROWS
MIN_CORRECT = gram.MIN_CORRECT
BUMP_LADDER = gram.BUMP_LADDER
MULTIPLE_LADDER = gram.MULTIPLE_LADDER
CONTROL_ROWS = gram.CONTROL_ROWS

#: ASCII letters only: CJK strings keep their characters, so a Chinese template
#: never merges with a different Chinese template through this rule.
LETTERS = re.compile(r"[A-Za-z]+")
SHAPE_TOKEN = "w"


def shape_template(prompt: str) -> str:
    """The §93 family key: digits and punctuation kept, ASCII words collapsed."""
    return LETTERS.sub(SHAPE_TOKEN, base.digit_template(prompt))


# -- families (§93.1) -------------------------------------------------------
def build_families(
    train: Sequence[Tuple[str, str]],
    key: str = "shape",
) -> Dict[str, Dict[str, Any]]:
    """Group the corpus by ``key`` and fit each family with §92's oracle.

    ``key`` is ``"shape"`` or ``"template"``; the latter exists so the contracts
    can show the two partitions side by side on the same corpus. The family
    dict is built with ``fit`` first and the row list assigned afterwards: some
    fit statuses carry a row *count* under ``"rows"``, and spreading that over
    the corpus rows would replace the list with an int.
    """
    to_key = shape_template if key == "shape" else base.digit_template
    grouped: Dict[str, List[Tuple[str, str]]] = {}
    for prompt, answer in train:
        grouped.setdefault(to_key(prompt), []).append((prompt, answer))
    families: Dict[str, Dict[str, Any]] = {}
    for name, rows in grouped.items():
        if len(rows) < MIN_FAMILY_ROWS:
            continue
        widths = {len(base.slot_values(prompt)) for prompt, _ in rows}
        if len(widths) != 1:
            families[name] = {"status": "ragged-slots", "n": len(rows), "rows": rows}
            continue
        families[name] = {
            **gram.fit_family(rows, widths.pop()),
            "n": len(rows),
            "rows": rows,
        }
    return families


# -- selection (§93.2) ------------------------------------------------------
def select_rows(
    pairs: Sequence[Tuple[str, str]], families: Dict[str, Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    train_prompts = {q for family in families.values() for q, _ in family["rows"]}
    selected: List[Dict[str, Any]] = []
    dropped: Dict[str, int] = {}
    for index, (prompt, gold) in enumerate(pairs):
        name = shape_template(prompt)
        family = families.get(name)
        if family is None or family.get("status") != "usable":
            dropped["family-not-usable"] = dropped.get("family-not-usable", 0) + 1
            continue
        moved = gram.perturb(prompt, family, BUMP_LADDER, MULTIPLE_LADDER, train_prompts)
        if moved is None:
            dropped["no-perturbation"] = dropped.get("no-perturbation", 0) + 1
            continue
        selected.append(
            {
                "i": index,
                "template": name,
                "expression": moved["expression"],
                "node": family["node"],
                "constant_slots": list(family["constant_slots"]),
                "q": prompt,
                "gold": gold,
                "q_cf": moved["q"],
                "gold_cf": moved["gold"],
                "step": moved["step"],
                "strategy": moved["strategy"],
            }
        )
    return selected, dropped


# -- entry points -----------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument("--plan", action="store_true", help="coverage only: no model, no scores")
    ap.add_argument("--check", default="")
    return ap


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
        "oracle": "shape",
        "shape_rule": "ascii-letters -> w (digits and punctuation kept)",
        "train_rows": len(train),
        "train_digest": rows_digest(train),
        "holdout_rows": len(holdout),
        "holdout_digest": rows_digest(holdout),
        "min_family_rows": MIN_FAMILY_ROWS,
        "families_considered": len(families),
        "families_by_status": by_status,
        "usable_family_rows_in_train": usable_rows,
        "families_fitted": {
            name: {
                "n": family["n"],
                "status": family["status"],
                "expression": family.get("expression"),
                "equivalent": family.get("equivalent"),
                "operands": family.get("operands"),
            }
            for name, family in sorted(families.items())
        },
        "holdout_rows_selected": len(selected),
        "holdout_rows_dropped": dropped,
        "by_expression": gram._count(selected, "expression"),
        "by_strategy": gram._count(selected, "strategy"),
    }
    print(
        f"shape families {len(families)} {by_status} -> usable rows {usable_rows}; "
        f"hold-out selected {len(selected)}/{len(holdout)} dropped {dropped}",
        flush=True,
    )
    for expression, count in sorted(
        gram._count(selected, "expression").items(), key=lambda kv: -kv[1]
    ):
        print(f"  {expression:20s} {count}", flush=True)
    gram.write_report(Path(args.out_dir), report)
    return report


def run(args: argparse.Namespace) -> Dict[str, Any]:
    train = read_pairs(TRAIN)
    holdout = read_pairs(HOLDOUT)
    families = build_families(train)
    selected, dropped = select_rows(holdout, families)
    control = gram.control_rows(families)
    print(
        f"selected {len(selected)} hold-out rows, control {len(control)} train rows",
        flush=True,
    )
    report: Dict[str, Any] = {
        "stage": "scored",
        "oracle": "shape",
        "shape_rule": "ascii-letters -> w (digits and punctuation kept)",
        "train_digest": rows_digest(train),
        "holdout_digest": rows_digest(holdout),
        "selected_digest": hashlib.sha256(
            json.dumps([[row["q"], row["q_cf"]] for row in selected], ensure_ascii=False).encode(
                "utf-8"
            )
        ).hexdigest(),
        "selected": len(selected),
        "dropped": dropped,
        "control": len(control),
        "families_by_status": gram._count(
            [{"s": family["status"]} for family in families.values()], "s"
        ),
        "runs": [],
    }
    out_dir = Path(args.out_dir)
    started = time.time()
    for kind, seed in ARMS:
        print(f"\n== {kind} seed {seed} ==", flush=True)
        row = gram.run_arm(kind, seed, selected, control)
        print(
            f"   original {row['original']['correct']}/{row['original']['n']}"
            f"  counterfactual {row['counterfactual']['correct']}/{row['counterfactual']['n']}"
            f"  changed {row['answer_changed']['changed']}/{row['answer_changed']['n']}"
            f"  control {row['control_original']['correct']}->{row['control_counterfactual']['correct']}"
            f"  ({row['seconds']}s)",
            flush=True,
        )
        report["runs"].append(row)
        gram.write_report(out_dir, report)
    report["seconds"] = round(time.time() - started, 1)
    report["decision"] = gram.verdict(report["runs"])
    path = gram.write_report(out_dir, report)
    print(f"\nwrote {path}", flush=True)
    print(json.dumps(report["decision"], ensure_ascii=False, indent=2), flush=True)
    return report


def check(report_path: Path) -> Tuple[bool, str]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    problems: List[str] = []
    if report.get("stage") != "scored":
        return False, "this is a --plan report; there is nothing to check"
    if report.get("oracle") != "shape":
        problems.append("this report was not produced by the shape oracle")
    if report["holdout_digest"] != rows_digest(read_pairs(HOLDOUT)):
        problems.append("hold-out rows changed since the run")
    train = read_pairs(TRAIN)
    if report["train_digest"] != rows_digest(train):
        problems.append("training rows changed since the run")
    families = build_families(train)
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
        for row in rows:
            if row["q"].strip() == row["q_cf"].strip():
                problems.append(f"{run['arm']} seed{run['seed']}: row {row['i']} was not perturbed")
                break
            if str(row["gold"]).strip() == str(row["gold_cf"]).strip():
                problems.append(f"{run['arm']} seed{run['seed']}: row {row['i']} gold unchanged")
                break
            operands = _operands(row)
            expected = gram.evaluate(gram.as_node(row["node"]), operands)
            if expected is None or not base._agrees(expected, str(row["gold_cf"])):
                problems.append(
                    f"{run['arm']} seed{run['seed']}: row {row['i']} gold_cf is not "
                    "what the fitted expression says"
                )
                break
            name = row.get("template") or shape_template(row["q"])
            family = families.get(name)
            if family is None or family["status"] != "usable":
                problems.append(
                    f"{run['arm']} seed{run['seed']}: row {row['i']} family no longer fits"
                )
                break
            disagreeing = [
                node
                for node in family["nodes"]
                if gram.evaluate(gram.as_node(node), operands) is None
                or not base._agrees(
                    gram.evaluate(gram.as_node(node), operands), str(row["gold_cf"])
                )
            ]
            if disagreeing:
                problems.append(
                    f"{run['arm']} seed{run['seed']}: row {row['i']} fits disagree on gold_cf"
                )
                break
    if gram.verdict(report["runs"])["verdict"] != report["decision"]["verdict"]:
        problems.append("decision does not recompute")
    first = report["runs"][0]
    model = load_model(first["arm"], REPO_ROOT / first["checkpoint"])
    rerun = gram.measure_holdout(model, [(row["q"], row["gold"]) for row in first["rows"]])
    differing = sum(1 for a, b in zip(rerun, first["rows"]) if a["answer"] != b["answer"])
    if differing:
        problems.append(f"original answers regenerated differently on {differing} rows")
    if problems:
        return False, "; ".join(problems)
    return True, (
        f"check OK ({len(report['runs'])} arms recomputed, "
        f"{first['arm']} seed{first['seed']} original rows re-run row-for-row)"
    )


def _operands(row: Dict[str, Any]) -> List[float]:
    slots = base.slot_values(row["q_cf"])
    constant = set(row["constant_slots"])
    return [float(value) for index, value in enumerate(slots) if index not in constant]


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
