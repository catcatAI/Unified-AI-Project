#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# LAYER: learning
# =============================================================================
"""B1: does one token-SNN checkpoint produce any correct frozen answer?

`probe_core_control.py` answers this for five producers at once, but it loads
GARDEN, ED3N, the external dictionaries and the LLM control in the same
process. On this machine that reached 67% of system RAM and had to be killed
(recorded as a void run in BETA_TRAINING_PLAN §E.1). This probe measures the
same question with **one** producer, so it stays inside the RAM cap:

    python scripts/probe_p2_tok_core.py \
        --checkpoint data/checkpoints/p2_base.pt \
        --out data/intelligence_reports/p2_tok_core.json

It uses the same frozen items (`run_benchmarks.load_dataset`) and the same
strict scorer (`run_benchmarks.score_item(..., mode="strict")`) as the core
measurement. It reports, per suite, `correct / answered / n` and how many
prompt atoms fell to `<unk>`: an item the vocabulary cannot read is
unanswerable by construction and is not counted as a wrong answer.

This is a coverage/correctness measurement, not a pass line. No threshold is
applied here and no score is invented; the core score still comes from the
provenance-carrying report.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

DEFAULT_CHECKPOINT = REPO_ROOT / "data" / "checkpoints" / "p2_base.pt"
DEFAULT_OUT = REPO_ROOT / "data" / "intelligence_reports" / "p2_tok_core.json"
SUITES = ("knowledge", "math", "code", "routing")


def summarize(rows: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Per-suite counts. ``answered`` means a non-empty generation, not correct."""
    out: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        cell = out.setdefault(
            row["suite"],
            {
                "n": 0,
                "correct": 0,
                "answered": 0,
                "prompt_tokens": 0,
                "prompt_unk": 0,
            },
        )
        cell["n"] += 1
        cell["correct"] += int(bool(row["passed"]))
        cell["answered"] += int(bool(row["answered"]))
        cell["prompt_tokens"] += int(row["prompt_tokens"])
        cell["prompt_unk"] += int(row["prompt_unk"])
    for cell in out.values():
        cell["unk_share"] = (
            round(cell["prompt_unk"] / cell["prompt_tokens"], 4) if cell["prompt_tokens"] else 0.0
        )
    return out


def totals(suites: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    keys = ("n", "correct", "answered", "prompt_tokens", "prompt_unk")
    summed = {k: sum(int(cell[k]) for cell in suites.values()) for k in keys}
    summed["unk_share"] = (
        round(summed["prompt_unk"] / summed["prompt_tokens"], 4) if summed["prompt_tokens"] else 0.0
    )
    return summed


def check_report(report: Dict[str, Any]) -> List[str]:
    """Arithmetic contracts: the summary must agree with the item rows."""
    problems: List[str] = []
    if report.get("scoring") != "strict":
        problems.append("scoring must be strict")
    rows = report.get("items") or []
    if not rows:
        return problems + ["report has no items"]
    if summarize(rows) != report.get("suites"):
        problems.append("suite summary does not match the item rows")
    if totals(report["suites"]) != report.get("totals"):
        problems.append("totals do not match the suite summary")
    for row in rows:
        if row["passed"] and not row["answered"]:
            problems.append(f"{row['id']}: passed with an empty answer")
        if row["prompt_unk"] > row["prompt_tokens"]:
            problems.append(f"{row['id']}: unk count exceeds token count")
    return problems


def run(
    checkpoint: Path,
    suites: Iterable[str],
    max_new: int,
    limit: int,
) -> Dict[str, Any]:
    import torch
    from ai.ed3n.token_snn import TokenSNN
    from run_benchmarks import load_dataset, score_item

    model = TokenSNN.load(checkpoint)
    unk = model.vocab.stoi.get("<unk>", -1)
    wanted = set(suites)
    items = [item for item in load_dataset() if item.suite in wanted]
    if limit:
        kept: Dict[str, int] = {}
        limited = []
        for item in items:
            if kept.get(item.suite, 0) < limit:
                limited.append(item)
                kept[item.suite] = kept.get(item.suite, 0) + 1
        items = limited

    rows: List[Dict[str, Any]] = []
    started = time.time()
    for index, item in enumerate(items, 1):
        ids = model.vocab.encode(item.q)
        pred = str(model.generate(item.q, max_new=max_new) or "").strip()
        passed, skipped = score_item(item, pred, mode="strict")
        rows.append(
            {
                "id": item.id,
                "suite": item.suite,
                "q": item.q,
                "gold": item.ground_truth,
                "pred": pred,
                "passed": bool(passed),
                "skipped": bool(skipped),
                "answered": bool(pred),
                "prompt_tokens": len(ids),
                "prompt_unk": sum(1 for i in ids if i == unk),
            }
        )
        if index % 10 == 0:
            print(f"  {index}/{len(items)}", flush=True)

    suite_cells = summarize(rows)
    return {
        "checkpoint": str(checkpoint),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "device": str(model.device),
        "torch": torch.__version__,
        "scoring": "strict",
        "max_new": max_new,
        "seconds": round(time.time() - started, 1),
        "suites": suite_cells,
        "totals": totals(suite_cells),
        "items": rows,
        "note": (
            "correct/answered are per suite; an item whose prompt is entirely <unk> "
            "is unanswerable by construction and must not be read as a wrong answer. "
            "No pass line is applied and this is not the core score."
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="B1 token-SNN frozen-item coverage")
    ap.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--suites", default=",".join(SUITES))
    ap.add_argument("--max-new", type=int, default=48)
    ap.add_argument("--limit", type=int, default=0, help="max items per suite (0 = all)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", default="", help="validate an existing report and exit")
    args = ap.parse_args(argv)

    if args.check:
        report = json.loads(Path(args.check).read_text(encoding="utf-8"))
        problems = check_report(report)
        if problems:
            print("❌ " + "; ".join(problems))
            return 1
        print(f"✅ {args.check}: arithmetic agrees with the item rows")
        return 0

    checkpoint = Path(args.checkpoint)
    if not checkpoint.is_file():
        print(f"checkpoint not found: {checkpoint}")
        return 1
    suites = [s.strip() for s in args.suites.split(",") if s.strip()]
    report = run(checkpoint, suites, args.max_new, args.limit)
    problems = check_report(report)
    if problems:
        print("❌ " + "; ".join(problems))
        return 1

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"checkpoint {checkpoint}  device={report['device']}  strict  {report['seconds']}s")
        print(f"  {'suite':10} {'n':>4} {'correct':>8} {'answered':>9} {'unk':>7}")
        for suite, cell in report["suites"].items():
            print(
                f"  {suite:10} {cell['n']:4d} {cell['correct']:8d} "
                f"{cell['answered']:9d} {cell['unk_share']:7.1%}"
            )
        t = report["totals"]
        print(
            f"  {'total':10} {t['n']:4d} {t['correct']:8d} {t['answered']:9d} "
            f"{t['unk_share']:7.1%}"
        )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if not args.json:
        try:
            print(f"wrote {out.relative_to(REPO_ROOT)}")
        except ValueError:
            print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
