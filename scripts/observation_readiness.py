#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [β] [B] [L2]
# =============================================================================
"""Is the turn-observation corpus big enough to run P5? (readiness, not a score)

P5 (docs/06-project-management/HIERARCHICAL_PLAN_FILL_GENERATION.md §6.1) is
decided per stratum: **input length bucket × topic bucket**, and the
pre-registered stop condition says a cell below 200 turns means "insufficient
sample — do not run". This script reports exactly that arithmetic on the corpus
the app has written so far. It does not compute the metric, does not filter
records to make cells pass, and never writes into the observation directory.

It also checks the two ways a corpus can look big and still be unusable:

* a state field that is ``null`` for every record (100% uncovered → no signal),
* records from schema v1, which carry neither ``in_len_bucket`` nor ``topic``
  and therefore cannot be stratified at all (they are counted, not discarded).

A field with a single distinct value is reported too, but only as a diagnostic:
§6.1's stop conditions do not mention it, so it does not decide readiness here.
It is printed because a constant field cannot carry information no matter how
many turns are collected, and that should be visible before the run.

Usage:
    python scripts/observation_readiness.py
    python scripts/observation_readiness.py --dir /path/to/observations
    python scripts/observation_readiness.py --json /tmp/readiness.json
Exit code: 0 when every cell reaches the pre-registered minimum and no state
field is fully unobserved; 1 otherwise (including "no data yet").
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = REPO_ROOT / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

# §6.1: "分層後每格 < 200 回合 → 不跑，標「樣本不足」". Not a tunable knob:
# changing it changes the pre-registered experiment, not this script.
PRE_REGISTERED_MIN_PER_CELL = 200

# The schema's own key set. Anything else means the writer changed without this
# reader following, or something wrote text into a structure-only log.
ALLOWED_KEYS = frozenset(
    {
        "v",
        "turn_id",
        "session",
        "day",
        "state",
        "user_move",
        "source",
        "in_len",
        "in_len_bucket",
        "topic",
        "out_len",
        "out_len_bucket",
        "skeleton",
        "skeleton_sig",
        "consent",
    }
)
STRATIFIABLE_FROM = 2  # schema v2 added in_len_bucket + topic


def default_directory(environ: Dict[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    override = str(env.get("ANGELA_TURN_OBSERVATION_DIR", "")).strip()
    if override:
        return Path(override).expanduser()
    from core.data_config import get_data_root

    return get_data_root() / "observations"


def load_records(directory: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Read every ``turns-*.jsonl`` line; malformed lines are reported, not skipped."""
    records: List[Dict[str, Any]] = []
    problems: List[str] = []
    for path in sorted(directory.glob("turns-*.jsonl")):
        with open(path, "r", encoding="utf-8") as handle:
            for lineno, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    problems.append(f"{path.name}:{lineno}: unparsable line ({exc.msg})")
                    continue
                if not isinstance(record, dict):
                    problems.append(f"{path.name}:{lineno}: not a JSON object")
                    continue
                unexpected = sorted(set(record) - ALLOWED_KEYS)
                if unexpected:
                    problems.append(
                        f"{path.name}:{lineno}: unexpected key(s) {', '.join(unexpected)}"
                    )
                records.append(record)
    return records, problems


def summarize(
    records: Iterable[Dict[str, Any]],
    *,
    state_fields: Iterable[str],
    min_per_cell: int = PRE_REGISTERED_MIN_PER_CELL,
) -> Dict[str, Any]:
    """The pre-registered arithmetic, computed exactly and without smoothing."""
    fields = tuple(state_fields)
    strata: Dict[Tuple[str, str], int] = {}
    state_present: Dict[str, int] = {}
    state_values: Dict[str, set] = {field: set() for field in fields}
    state_missing_records = 0
    legacy = 0
    versions: Dict[str, int] = {}
    total = 0

    for record in records:
        total += 1
        versions[str(record.get("v", "?"))] = versions.get(str(record.get("v", "?")), 0) + 1

        length_bucket = record.get("in_len_bucket")
        topic = record.get("topic")
        if length_bucket is None or topic is None:
            legacy += 1
        else:
            key = (str(length_bucket), str(topic))
            strata[key] = strata.get(key, 0) + 1

        state = record.get("state")
        if not isinstance(state, dict):
            state_missing_records += 1
            continue
        for field in fields:
            value = state.get(field)
            if value is not None:
                state_present[field] = state_present.get(field, 0) + 1
                state_values[field].add(json.dumps(value, sort_keys=True, default=str))

    deficits = [
        {"in_len_bucket": length, "topic": topic, "turns": count, "missing": min_per_cell - count}
        for (length, topic), count in sorted(strata.items(), key=lambda kv: (kv[0][0], kv[0][1]))
        if count < min_per_cell
    ]
    uncovered = [field for field in fields if state_present.get(field, 0) == 0]
    constant = [field for field in fields if len(state_values[field]) == 1]

    reasons: List[str] = []
    if total == 0:
        reasons.append("no observations recorded yet")
    if legacy:
        reasons.append(
            f"{legacy} record(s) predate schema v{STRATIFIABLE_FROM} and cannot be "
            "stratified (missing in_len_bucket/topic)"
        )
    if deficits:
        reasons.append(f"{len(deficits)} of {len(strata)} cell(s) below {min_per_cell} turns")
    if uncovered:
        reasons.append(f"state field(s) never observed: {', '.join(uncovered)}")

    return {
        "total_turns": total,
        "versions": versions,
        "legacy_unstratifiable": legacy,
        "strata": [
            {"in_len_bucket": length, "topic": topic, "turns": count}
            for (length, topic), count in sorted(
                strata.items(), key=lambda kv: (kv[0][0], kv[0][1])
            )
        ],
        "cell_count": len(strata),
        "min_per_cell": min_per_cell,
        "deficits": deficits,
        "state_present": {field: state_present.get(field, 0) for field in fields},
        "state_distinct": {field: len(state_values[field]) for field in fields},
        "constant_state_fields": constant,
        "state_missing_records": state_missing_records,
        "uncovered_state_fields": uncovered,
        "ready": not reasons,
        "verdict": "ready" if not reasons else "insufficient sample",
        "reasons": reasons,
    }


def print_report(summary: Dict[str, Any], problems: List[str]) -> None:
    print("=" * 72)
    print("TURN OBSERVATION READINESS (P5, pre-registered §6.1)")
    print("=" * 72)
    print(f"turns: {summary['total_turns']}  schema: {summary['versions']}")
    print(
        f"cells: {summary['cell_count']}  minimum per cell: {summary['min_per_cell']} "
        f"(pre-registered; not configurable here)"
    )

    if summary["strata"]:
        print("\n  input bucket × topic")
        for row in summary["strata"]:
            print(f"    {row['in_len_bucket']:>5} × {row['topic']:<10} " f"{row['turns']:>6} turns")

    print("\n  state coverage (non-null turns / distinct values)")
    for field, count in summary["state_present"].items():
        print(f"    {field:<18} {count:>6} / {summary['state_distinct'][field]:>4} distinct")
    if summary["state_missing_records"]:
        print(f"    (state object absent in {summary['state_missing_records']} turn(s))")
    if summary["constant_state_fields"]:
        print(
            "    constant (cannot carry information; diagnostic only): "
            + ", ".join(summary["constant_state_fields"])
        )

    if problems:
        print("\n  schema problems")
        for problem in problems:
            print(f"    {problem}")

    print("\nverdict:", summary["verdict"].upper())
    for reason in summary["reasons"]:
        print(f"  - {reason}")
    if summary["ready"]:
        print("  every cell reached the pre-registered minimum; P5 may be run")
    else:
        print("  do not run P5; a smaller sample cannot give a directional answer")


def main() -> int:
    from ai.lifecycle.turn_observation import STATE_FIELDS

    parser = argparse.ArgumentParser(description="P5 turn-observation readiness")
    parser.add_argument(
        "--dir",
        type=Path,
        default=None,
        help="observation directory (default: ANGELA_TURN_OBSERVATION_DIR or <data root>/observations)",
    )
    parser.add_argument("--json", type=Path, default=None, help="also write the summary here")
    args = parser.parse_args()

    directory = args.dir or default_directory()
    records, problems = load_records(directory)
    summary = summarize(records, state_fields=STATE_FIELDS)
    summary["directory"] = str(directory)
    summary["schema_problems"] = problems

    print_report(summary, problems)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return 0 if summary["ready"] and not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
