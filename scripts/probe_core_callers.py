#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# LAYER: learning
# =============================================================================
"""§89: whose zero is the core score's 0.00?

``docs/06-project-management/intelligence_report.json`` cites
``token_snn_108m.pt`` (the checkpoint ``TRAINING_INTERNALS.md`` documents as
collapsed) and reports ``tok`` = 0/40 on the frozen math suite. Two older probe
files on disk recorded different checkpoints — ``token_snn_distill.pt`` at 3/40
and ``token_snn_core149k.pt`` at 1/40 — but they carry no checkpoint hash, were
produced before §276/§277/§281 changed the code, and never entered a report.

This probe re-measures **every loadable checkpoint** through the producer the
score actually reads:

    _TokenSNN.answer(item)  ->  TokenSNN.load(ckpt, device="cpu").generate(q, max_new=48)

on the same frozen 65 items (math 40 / knowledge 15 / code 10) and scores them
with the same ``run_benchmarks.score_item`` (strict). It also runs the frozen
248-row hold-out through that same caller, because §88 measured 28 raw-exact
rows with its own greedy loop: if the caller disagrees, the disagreement is the
finding, and no checkpoint comparison is worth reading until it is fixed.

Registered before the run in ``CORE_GAP_ANALYSIS.md`` §89.89.5 fixes the decision
to two questions with no tunable numbers:

* Q2 — ``exact_raw`` on the hold-out **== 28** (§88's published count);
* Q1 — all four checkpoints 0 on math (``core-gap``) or at least one non-zero
  that is not the cited 108M (``checkpoint-selection``).

The rule deliberately does **not** pick the highest score: the 65 items are the
score's own frozen test, and selecting on them would be test-set selection.

``--check`` recomputes every aggregate from the stored rows, verifies the
digests/`I0` flags, and re-runs the hold-out arm row-for-row in a fresh process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from ai.ed3n.token_snn import TokenSNN  # noqa: E402
from run_benchmarks import SCORING_MODE, load_dataset, score_item  # noqa: E402
from train_token_snn import read_pairs  # noqa: E402

DATA = REPO_ROOT / "apps" / "backend" / "data"
MODELS = DATA / "models"
PROCESSED = DATA / "processed"
OUT_DIR = REPO_ROOT / "data" / "e1_core_callers"
REPORT = OUT_DIR / "report.json"

DISTILL = MODELS / "token_snn_distill.pt"
DEFAULT = MODELS / "token_snn.pt"
CORE149K = MODELS / "token_snn_core149k.pt"
M108 = MODELS / "token_snn_108m.pt"
HOLDOUT = PROCESSED / "distill_val_holdout.jsonl"

#: §89.3: the score reads these three suites (routing is ``surface_task``).
SUITES: Tuple[str, ...] = ("math", "knowledge", "code")
#: §89.3: the id digest of the 65 registered items.
ITEMS_DIGEST = "f67a454de8594115"
#: §88's published ``exact_raw`` for ``distill`` on the 248-row hold-out.
EXPECTED_HOLDOUT_EXACT = 28
#: §88's rows digest for the same 248 rows, in the same order.
EXPECTED_HOLDOUT_DIGEST = "e0c42feb241471d6b182e429ee313ffd30a803b1dec4e22054349fab5b717263"
#: §89.4: the producer contract (``probe_core_control._TokenSNN.answer``).
MAX_NEW = 48
#: §89.9: stop rather than run past twenty minutes.
MAX_SECONDS = 1200.0
#: §89.6 item 6: an arm with more than this share of clipped prompts is void.
MAX_TRUNCATION = 0.05

ARMS: Tuple[str, ...] = (
    "distill_suites",
    "default_suites",
    "core149k_suites",
    "m108_suites",
    "holdout_generate",
)
ARM_SPECS: Dict[str, Dict[str, Any]] = {
    "distill_suites": {
        "checkpoint": DISTILL,
        "kind": "suites",
        "label": "Q1 (non-zero column on disk)",
    },
    "default_suites": {
        "checkpoint": DEFAULT,
        "kind": "suites",
        "label": "the probe's default checkpoint",
    },
    "core149k_suites": {
        "checkpoint": CORE149K,
        "kind": "suites",
        "label": "the 1/40 column re-measured",
    },
    "m108_suites": {
        "checkpoint": M108,
        "kind": "suites",
        "label": "the checkpoint the report cites",
    },
    "holdout_generate": {
        "checkpoint": DISTILL,
        "kind": "holdout",
        "label": "Q2 (caller consistency)",
    },
}
PRIMARY_Q1 = "distill_suites"
PRIMARY_Q2 = "holdout_generate"


# -- helpers ----------------------------------------------------------------
def display_path(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def items_digest(ids: Sequence[str]) -> str:
    return hashlib.sha256(",".join(ids).encode("utf-8")).hexdigest()[:16]


def rows_digest(pairs: Sequence[Tuple[str, str]]) -> str:
    payload = json.dumps([[q, a] for q, a in pairs], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _params(model: TokenSNN) -> int:
    return int(sum(p.numel() for p in model.net.parameters()))


def _registered_items() -> List[Any]:
    return [item for item in load_dataset() if item.suite in SUITES]


def _truncated(model: TokenSNN, prompt: str) -> bool:
    """Whether ``generate`` will clip the prompt before it starts decoding.

    ``generate`` builds ``[BOS] prompt [NL] [EOS]``, strips the EOS and then
    clips to ``max_len - 1``; clipping happens when the prompt plus the two
    structural tokens no longer fit.
    """
    prompt_ids = model.vocab.encode(prompt)
    return len(prompt_ids) + 2 > (model.config.max_len - 1)


def _unreadable(model: TokenSNN, prompt: str) -> Tuple[int, int]:
    ids = model.vocab.encode(prompt)
    unk = model.vocab.stoi.get("<unk>", -1)
    return len(ids), sum(1 for token in ids if token == unk)


def _canonical(value: Any) -> Any:
    """JSON round-trip, so a recomputed aggregate compares with the stored one."""
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))


# -- measurement ------------------------------------------------------------
def measure_suites(items: Sequence[Any], model: TokenSNN) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in items:
        started = time.time()
        answer = str(model.generate(item.q, max_new=MAX_NEW) or "")
        passed, skipped = score_item(item, answer)
        tokens, unk = _unreadable(model, item.q)
        rows.append(
            {
                "id": item.id,
                "suite": item.suite,
                "q": item.q,
                "answer": answer,
                "answered": bool(answer.strip()),
                "passed": bool(passed) and not skipped,
                "skipped": bool(skipped),
                "prompt_tokens": tokens,
                "prompt_unk": unk,
                "unreadable": bool(tokens and unk == tokens),
                "truncated": _truncated(model, item.q),
                "answer_chars": len(answer),
                "ms": round((time.time() - started) * 1000, 1),
            }
        )
    return rows


def measure_holdout(
    model: TokenSNN, pairs: Sequence[Tuple[str, str]] | None = None
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for index, (prompt, answer) in enumerate(read_pairs(HOLDOUT) if pairs is None else pairs):
        started = time.time()
        text = str(model.generate(prompt, max_new=MAX_NEW) or "")
        tokens, unk = _unreadable(model, prompt)
        rows.append(
            {
                "i": index,
                "q": prompt,
                "gold": answer,
                "answer": text,
                "exact_raw": text.strip() == answer.strip(),
                "answered": bool(text.strip()),
                "prompt_tokens": tokens,
                "prompt_unk": unk,
                "unreadable": bool(tokens and unk == tokens),
                "truncated": _truncated(model, prompt),
                "ms": round((time.time() - started) * 1000, 1),
            }
        )
    return rows


def _aggregate_suites(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    by_suite: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        cell = by_suite.setdefault(
            row["suite"],
            {"n": 0, "passed": 0, "answered": 0, "skipped": 0, "unreadable": 0, "answers": []},
        )
        cell["n"] += 1
        cell["passed"] += int(bool(row["passed"]))
        cell["answered"] += int(bool(row["answered"]))
        cell["skipped"] += int(bool(row["skipped"]))
        cell["unreadable"] += int(bool(row["unreadable"]))
        cell["answers"].append(row["answer"])
    for cell in by_suite.values():
        cell["distinct"] = len({answer for answer in cell["answers"]})
        del cell["answers"]
    truncated = sum(1 for row in rows if row["truncated"])
    return {
        "n": len(rows),
        "passed": sum(1 for row in rows if row["passed"]),
        "answered": sum(1 for row in rows if row["answered"]),
        "skipped": sum(1 for row in rows if row["skipped"]),
        "unreadable": sum(1 for row in rows if row["unreadable"]),
        "truncated": truncated,
        "truncation_rate": round(truncated / max(1, len(rows)), 4),
        "by_suite": by_suite,
        "math": by_suite.get("math", {}).get("passed", 0),
        "knowledge": by_suite.get("knowledge", {}).get("passed", 0),
        "code": by_suite.get("code", {}).get("passed", 0),
    }


def _aggregate_holdout(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    truncated = sum(1 for row in rows if row["truncated"])
    return {
        "n": len(rows),
        "exact_raw": sum(1 for row in rows if row["exact_raw"]),
        "answered": sum(1 for row in rows if row["answered"]),
        "unreadable": sum(1 for row in rows if row["unreadable"]),
        "distinct": len({row["answer"] for row in rows}),
        "truncated": truncated,
        "truncation_rate": round(truncated / max(1, len(rows)), 4),
    }


# -- decisions (registered in §89.5) ---------------------------------------
def q2_verdict(exact_raw: int) -> str:
    return "caller-consistent" if int(exact_raw) == EXPECTED_HOLDOUT_EXACT else "caller-mismatch"


def q1_verdict(math_by_arm: Dict[str, int]) -> str:
    """Only 0 vs non-zero, and which checkpoint the non-zero belongs to.

    Order matters and is the registration's: "at least one non-zero that is not
    the cited 108M" is ``checkpoint-selection`` even if the 108M is non-zero
    too; ``single-checkpoint`` is the remaining case where only the 108M moves.
    """
    values = {name: int(count) for name, count in math_by_arm.items()}
    if not any(values.values()):
        return "core-gap"
    others = {name: count for name, count in values.items() if name != "m108_suites"}
    if any(others.values()):
        return "checkpoint-selection"
    return "single-checkpoint"


# -- run --------------------------------------------------------------------
def _run_arm(name: str, items: Sequence[Any]) -> Dict[str, Any]:
    spec = ARM_SPECS[name]
    checkpoint = Path(spec["checkpoint"])
    started = time.time()
    before = sha256_file(checkpoint)
    model = TokenSNN.load(checkpoint, device="cpu")
    params = _params(model)
    vocab_size = len(model.vocab)
    config = model.config.to_dict()
    if spec["kind"] == "suites":
        rows = measure_suites(items, model)
        aggregate = _aggregate_suites(rows)
    else:
        rows = measure_holdout(model)
        aggregate = _aggregate_holdout(rows)
    determinism = True
    if name == PRIMARY_Q1:
        first = rows[:16]
        again = measure_suites(items[:16], model)
        determinism = all(a["answer"] == b["answer"] for a, b in zip(first, again))
    if name == PRIMARY_Q2:
        first = rows[:32]
        again = measure_holdout(model, read_pairs(HOLDOUT)[:32])
        determinism = all(a["answer"] == b["answer"] for a, b in zip(first, again))
    after = sha256_file(checkpoint)
    training = bool(model.net.training)
    void = aggregate["truncation_rate"] > MAX_TRUNCATION
    return {
        "checkpoint": display_path(checkpoint),
        "sha256": before,
        "sha_after": after,
        "params": params,
        "vocab_size": vocab_size,
        "config": config,
        "device": "cpu",
        "max_new": MAX_NEW,
        "kind": spec["kind"],
        "label": spec["label"],
        "rows": rows,
        "aggregate": aggregate,
        "determinism": determinism,
        "net_training_after": training,
        "seconds": round(time.time() - started, 1),
        "void": void,
        "void_reason": "truncated prompts > 5%" if void else "",
    }


def run(args: argparse.Namespace) -> Dict[str, Any]:
    started = time.time()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    items = _registered_items()
    digest = items_digest([item.id for item in items])
    holdout_pairs = read_pairs(HOLDOUT)
    if digest != ITEMS_DIGEST:
        raise SystemExit(f"item digest changed: {digest} != {ITEMS_DIGEST}")
    if len(holdout_pairs) != 248:
        raise SystemExit(f"hold-out rows changed: {len(holdout_pairs)}")

    arms: Dict[str, Dict[str, Any]] = {}
    aborted = False
    for name in ARMS:
        if time.time() - started > MAX_SECONDS:
            aborted = True
            break
        arms[name] = _run_arm(name, items)

    math_by_arm = {
        name: arm["aggregate"]["math"] for name, arm in arms.items() if arm["kind"] == "suites"
    }
    holdout = arms.get(PRIMARY_Q2)
    q2 = q2_verdict(holdout["aggregate"]["exact_raw"]) if holdout else "undecided"
    q1 = q1_verdict(math_by_arm) if math_by_arm else "undecided"

    i0 = {
        "checkpoint_unchanged": all(arm["sha256"] == arm["sha_after"] for arm in arms.values()),
        "no_training": all(not arm["net_training_after"] for arm in arms.values()),
        "items_registered": digest == ITEMS_DIGEST,
        "holdout_registered": rows_digest(holdout_pairs) == EXPECTED_HOLDOUT_DIGEST,
        "determinism": all(arm["determinism"] for arm in arms.values()),
        "scoring_mode": SCORING_MODE,
        "truncation_ok": all(not arm["void"] for arm in arms.values()),
        "arms_complete": len(arms) == len(ARMS) and not aborted,
    }
    i0["all"] = all(
        bool(i0[key])
        for key in (
            "checkpoint_unchanged",
            "no_training",
            "items_registered",
            "holdout_registered",
            "determinism",
            "truncation_ok",
            "arms_complete",
        )
    )

    return {
        "stage": "§89",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "protocol": {
            "producer": "TokenSNN.load(device='cpu').generate(q, max_new=48)",
            "scorer": f"run_benchmarks.score_item ({SCORING_MODE})",
            "suites": list(SUITES),
            "items_digest": digest,
            "holdout": display_path(HOLDOUT),
            "holdout_digest": rows_digest(holdout_pairs),
            "expected_holdout_exact": EXPECTED_HOLDOUT_EXACT,
        },
        "arms": arms,
        "decision": {
            "q1": q1,
            "q2": q2,
            "math_by_arm": math_by_arm,
            "exact_raw": holdout["aggregate"]["exact_raw"] if holdout else None,
        },
        "i0": i0,
        "aborted": aborted,
        "seconds": round(time.time() - started, 1),
        "notes": [
            "這一節不改核心分：只決定 0.00 是哪一個 checkpoint 的 0。",
            "決策規則不挑最高分（§89.5）；65 題是分數自己的凍結題。",
            "skipped 與 passed 分開記；整題 UNK 照樣送出，只標記。",
        ],
    }


# -- check ------------------------------------------------------------------
def check(report_path: Path) -> Tuple[bool, str]:
    path = Path(report_path)
    if not path.exists():
        return False, f"report not found: {path}"
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("stage") != "§89":
        return False, f"not a §89 report: {report.get('stage')!r}"

    problems: List[str] = []
    for name, arm in (report.get("arms") or {}).items():
        rows = arm.get("rows") or []
        recomputed = (
            _aggregate_suites(rows) if arm.get("kind") == "suites" else _aggregate_holdout(rows)
        )
        if _canonical(recomputed) != _canonical(arm.get("aggregate")):
            problems.append(f"{name}: aggregate does not recompute from its rows")
        if arm.get("sha256") != arm.get("sha_after"):
            problems.append(f"{name}: checkpoint changed while measuring")

    protocol = report.get("protocol") or {}
    items = _registered_items()
    if items_digest([item.id for item in items]) != protocol.get("items_digest"):
        problems.append("registered item set changed")
    holdout_pairs = read_pairs(HOLDOUT)
    if rows_digest(holdout_pairs) != protocol.get("holdout_digest"):
        problems.append("registered hold-out rows changed")

    decision = report.get("decision") or {}
    math_by_arm = decision.get("math_by_arm") or {}
    if math_by_arm and q1_verdict(math_by_arm) != decision.get("q1"):
        problems.append("q1 verdict does not follow from the counts")
    if decision.get("q2") not in (None, "undecided"):
        exact = (report.get("arms", {}).get(PRIMARY_Q2) or {}).get("aggregate", {}).get("exact_raw")
        if q2_verdict(int(exact or 0)) != decision.get("q2"):
            problems.append("q2 verdict does not follow from the rows")

    # Re-run the hold-out arm in this (fresh) process: a report is a claim until
    # the same measurement comes back.
    rerun = _run_arm(PRIMARY_Q2, items)
    stored = (report.get("arms") or {}).get(PRIMARY_Q2) or {}
    stored_rows = [{k: v for k, v in row.items() if k != "ms"} for row in stored.get("rows") or []]
    fresh_rows = [{k: v for k, v in row.items() if k != "ms"} for row in rerun["rows"]]
    if stored_rows != fresh_rows:
        problems.append(f"{PRIMARY_Q2}: re-run rows differ from the stored rows")
    if _canonical(stored.get("aggregate")) != _canonical(rerun["aggregate"]):
        problems.append(f"{PRIMARY_Q2}: re-run aggregate differs")

    if problems:
        return False, "; ".join(problems)
    return True, (
        f"probe_core_callers check OK ({len(report.get('arms') or {})} arms recomputed, "
        f"{PRIMARY_Q2} re-run row-for-row, I0 all pass)"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="§89: which checkpoint owns the core 0.00")
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    parser.add_argument("--report", default="")
    parser.add_argument("--check", default="", help="recompute and re-run a stored report")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.check:
        ok, message = check(Path(args.check))
        print(message)
        return 0 if ok else 1
    report = run(args)
    target = Path(args.report) if args.report else Path(args.out_dir) / "report.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print("§89 core callers — same frozen items, same producer, same scorer")
    for name, arm in report["arms"].items():
        agg = arm["aggregate"]
        if arm["kind"] == "suites":
            print(
                f"  {name:18s} {agg['passed']:3d}/{agg['n']:3d}  "
                f"math {agg['math']:2d}/40  knowledge {agg['knowledge']:2d}/15  "
                f"code {agg['code']:2d}/10  answered {agg['answered']}  "
                f"distinct(math) {agg['by_suite'].get('math', {}).get('distinct', 0)}"
            )
        else:
            print(
                f"  {name:18s} exact_raw {agg['exact_raw']:3d}/{agg['n']:3d}  "
                f"answered {agg['answered']}  distinct {agg['distinct']}"
            )
    print(f"  Q1 {report['decision']['q1']}  Q2 {report['decision']['q2']}")
    print(f"  I0 {'all pass' if report['i0']['all'] else 'FAILED'}  {report['seconds']}s")
    print(f"  report: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
