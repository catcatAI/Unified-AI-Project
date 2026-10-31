#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""Run one AI+AL training round, then auto-produce the next batch (round-2 second half).

ISSUES_2026-10-29 §六.6 registered the missing half of round 2 as
"「訓練完自動產下一批 AL 資料」的循環". This script is that loop:

1. run the training command given after ``--`` (streamed to a log file);
2. only if it exits 0, generate the next AI+AL dataset — a **fresh, disjoint**
   slice of the AI corpus (``--skip`` past every row earlier rounds used; a
   new seed alone would repeat the same questions, which is wasted training);
3. prepare it into its own train/val/manifest files (never overwriting the
   files the finished round trained on), with a leak check and a ``--check``
   roundtrip;
4. write a loop manifest recording command, exit codes, paths and hashes.

Deliberately **not** done: launching the following round. What that round
changes (capacity / objective / data schema) stays a human decision — the
loop removes the hand-work, not the judgement (CORE_GAP_ANALYSIS §10.4: the
next variable is capacity+objective, not more data).

Usage:
    scripts/ai_al_round_loop.py --round 3 -- \
        ./.venv/bin/python scripts/train_token_snn.py --vocab token ... \
        --out data/checkpoints/ai_al_round3.pt \
        --report data/intelligence_reports/ai_al_round3.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED = REPO_ROOT / "apps" / "backend" / "data" / "processed"
REPORTS = REPO_ROOT / "data" / "intelligence_reports"


def _sha256(path: Path) -> Optional[str]:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _rel(path: Path) -> str:
    """Repo-relative when possible (also used under a tmp path in tests)."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _flag_value(cmd: List[str], flag: str) -> Optional[str]:
    try:
        return cmd[cmd.index(flag) + 1]
    except (ValueError, IndexError):
        return None


def _run(cmd: List[str], log) -> int:
    log.write(f"\n$ {' '.join(cmd)}\n")
    log.flush()
    return subprocess.run(cmd, cwd=REPO_ROOT, stdout=log, stderr=subprocess.STDOUT).returncode


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--round", type=int, required=True, help="the round being trained now")
    ap.add_argument("--log", default="", help="training log (default per round)")
    ap.add_argument(
        "--next-skip",
        type=int,
        default=4000,
        help="AI rows to skip for the next batch (default 4000: round 1 took the "
        "first 4000 accepted rows of core_train.jsonl)",
    )
    ap.add_argument("--next-rows", type=int, default=4000, help="rows in the next batch")
    ap.add_argument("--next-seed", type=int, default=7, help="state-sampling seed")
    ap.add_argument(
        "--next-holdout-cells",
        default="",
        help="MVE-1 carve for the next batch: comma-separated intent:mode cells "
        "to exclude (default off — pass the same spec the round trained under)",
    )
    ap.add_argument(
        "--next-expose-dt",
        action="store_true",
        help="put dt in the next batch's input line (default off; MVE-1 round-4+ "
        "schema — the staged batch must match the schema the round adopted)",
    )
    ap.add_argument(
        "--generate-only",
        action="store_true",
        help="produce the next batch without running training (recovery/manual mode)",
    )
    ap.add_argument("train_cmd", nargs=argparse.REMAINDER, help="training command after --")
    args = ap.parse_args(argv)

    # fail before training, not after it: a bad cell spec would otherwise be
    # discovered only once the hours-long run has already finished
    modes = ("exploratory", "neutral", "conservative")  # generate_al_dataset._MODES
    for part in (p.strip() for p in args.next_holdout_cells.split(",")):
        if not part:
            continue
        intent, sep, mode = part.partition(":")
        if not sep or not intent or mode not in modes:
            ap.error(f"bad --next-holdout-cells entry {part!r} (want intent:mode)")

    rnd = args.round
    nxt = rnd + 1
    log_path = Path(args.log) if args.log else REPORTS / f"ai_al_round{rnd}_loop.log"
    loop_manifest = REPORTS / f"ai_al_round{rnd}_loop.json"
    dataset = PROCESSED / f"ai_al_round{nxt}_dataset.json"
    train_out = PROCESSED / f"ai_al_round{nxt}_train.jsonl"
    val_out = PROCESSED / f"ai_al_round{nxt}_val.jsonl"
    manifest_out = PROCESSED / f"ai_al_round{nxt}_manifest.json"
    id_prefix = f"r{nxt}_"

    train_cmd = args.train_cmd
    if train_cmd and train_cmd[0] == "--":
        train_cmd = train_cmd[1:]
    if not args.generate_only and not train_cmd:
        ap.error("pass the training command after -- (or use --generate-only)")

    REPORTS.mkdir(parents=True, exist_ok=True)
    started = time.time()
    record: Dict[str, object] = {
        "round": rnd,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "log": _rel(log_path),
        "train_cmd": train_cmd,
        "train_rc": None,
        "checkpoint": _flag_value(train_cmd, "--out"),
        "report": _flag_value(train_cmd, "--report"),
        "next_batch": {
            "round": nxt,
            "dataset": _rel(dataset),
            "skip": args.next_skip,
            "rows": args.next_rows,
            "seed": args.next_seed,
            "id_prefix": id_prefix,
            **({"holdout_cells": args.next_holdout_cells} if args.next_holdout_cells else {}),
            **({"expose_dt": True} if args.next_expose_dt else {}),
            "note": (
                "fresh disjoint slice of core_train.jsonl; AL states come from the "
                "same contract §5 operator (registered placeholder — the state-line "
                "schema vs production snapshot is the open field-gap, ISSUES §五.6)"
            ),
        },
        "generated": False,
        "checked": False,
        "next_step": None,
    }

    train_rc = 0
    if not args.generate_only:
        with log_path.open("w", encoding="utf-8") as log:
            log.write(f"# ai_al round {rnd} loop — {time.ctime()}\n")
            train_rc = _run(train_cmd, log)
        record["train_rc"] = train_rc
        if train_rc != 0:
            record["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            record["next_step"] = "training failed — no batch generated; fix and re-run"
            loop_manifest.write_text(
                json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            print(f"training rc={train_rc} — next batch NOT generated (see {log_path})")
            return train_rc

    # Training succeeded (or --generate-only): produce the next batch.
    gen_extra: List[str] = []
    if args.next_holdout_cells:
        gen_extra += ["--holdout-cells", args.next_holdout_cells]
    if args.next_expose_dt:
        gen_extra += ["--expose-dt"]
    steps = [
        (
            "generate",
            [
                sys.executable,
                "scripts/generate_al_dataset.py",
                "--rows",
                str(args.next_rows),
                "--seed",
                str(args.next_seed),
                "--skip",
                str(args.next_skip),
                "--id-prefix",
                id_prefix,
                "--out",
                str(dataset),
                *gen_extra,
            ],
        ),
        (
            "prepare",
            [
                sys.executable,
                "scripts/prepare_ai_al_training_data.py",
                "--src",
                str(dataset),
                "--train-out",
                str(train_out),
                "--val-out",
                str(val_out),
                "--manifest-out",
                str(manifest_out),
            ],
        ),
        (
            "check",
            [
                sys.executable,
                "scripts/prepare_ai_al_training_data.py",
                "--check",
                "--src",
                str(dataset),
                "--train-out",
                str(train_out),
                "--val-out",
                str(val_out),
                "--manifest-out",
                str(manifest_out),
            ],
        ),
    ]
    with log_path.open("a", encoding="utf-8") as log:
        for name, cmd in steps:
            rc = _run(cmd, log)
            record[name + "_rc"] = rc
            if rc != 0:
                record["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
                record["next_step"] = f"{name} failed (rc={rc}) — see log"
                loop_manifest.write_text(
                    json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
                )
                print(f"{name} rc={rc} — loop stopped (see {log_path})")
                return rc

    record["generated"] = True
    record["checked"] = True
    for key, path in (
        ("dataset_sha256", dataset),
        ("train_sha256", train_out),
        ("val_sha256", val_out),
        ("manifest_sha256", manifest_out),
    ):
        record["next_batch"][key] = _sha256(path)  # type: ignore[index]
    record["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    record["seconds"] = round(time.time() - started, 1)
    record["next_step"] = (
        f"round {nxt} data ready ({train_out.name}) — launching it stays a "
        "human decision (CORE_GAP §10.4)"
    )
    loop_manifest.write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"round {rnd}: train rc=0, next batch ready — "
        f"{record['next_batch'].get('dataset')}\n"  # type: ignore[union-attr]
        f"manifest: {_rel(loop_manifest)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
