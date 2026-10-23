#!/usr/bin/env python3
"""Prepare the core's training data (raw -> processed) with a leak check.

The "training" step has to come before "learning from dialogue", but it must
not be teaching to the test. Three rules:

1. **Normalize**: every source row becomes ``{"input", "output"}``. Alpaca
   keeps its ``instruction`` (the old loader read ``input`` only, which is
   empty for most rows, so the trainer saw almost nothing).
2. **Dedup**: identical (normalized input, output) pairs collapse; the first
   source wins.
3. **No benchmark leakage**: any row whose input matches a benchmark question,
   or shares an 8-gram shingle with one, is dropped and counted. The benchmark
   is frozen afterwards; a score on data the core was trained on would be a
   fake score.

The split is deterministic (sha1 of the input): 95/5 by default. The manifest
records counts, source hashes and the leak check, so a later run can be
compared and audited.

Usage:
    python scripts/prepare_core_training_data.py
    python scripts/prepare_core_training_data.py --limit 20000
    python scripts/prepare_core_training_data.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW = REPO_ROOT / "apps" / "backend" / "data" / "raw_datasets"
OUT_DIR = REPO_ROOT / "apps" / "backend" / "data" / "processed"
BENCH = REPO_ROOT / "benchmarks" / "data" / "native_bench_v1.json"
PARAPHRASE = REPO_ROOT / "benchmarks" / "data" / "paraphrase_v1.json"

SOURCES = (
    "alpaca_data.json",
    "arithmetic_train_dataset.json",
    "logic_train.json",
    "association_train.json",
)

_PUNCT = re.compile(r"[^\w\s]+", re.UNICODE)
_SHINGLE = 8


def _norm(text: str) -> str:
    return " ".join(_PUNCT.sub(" ", str(text or "")).lower().split())


def _pair(item: dict) -> dict:
    instruction = str(item.get("instruction") or item.get("question") or item.get("prompt") or "")
    context = str(item.get("input") or "")
    problem = str(item.get("problem") or item.get("proposition") or "")
    text_in = problem or (f"{instruction}\n{context}".strip() if context else instruction)
    out = item.get("output") or item.get("response") or item.get("answer")
    return {"input": text_in.strip(), "output": str(out if out is not None else "").strip()}


def _benchmark_texts() -> List[str]:
    texts: List[str] = []
    if BENCH.exists():
        data = json.loads(BENCH.read_text(encoding="utf-8"))
        for suite in (data.get("suites") or {}).values():
            for item in suite.get("items") or []:
                if item.get("q"):
                    texts.append(_norm(item["q"]))
    if PARAPHRASE.exists():
        data = json.loads(PARAPHRASE.read_text(encoding="utf-8"))
        for split in (data.get("splits") or {}).values():
            items = split.get("items") if isinstance(split, dict) else split
            for item in items or []:
                if isinstance(item, dict) and item.get("q"):
                    texts.append(_norm(item["q"]))
    return [t for t in texts if t]


def _shingles(text: str) -> set:
    words = text.split()
    if len(words) < _SHINGLE:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i : i + _SHINGLE]) for i in range(len(words) - _SHINGLE + 1)}


def _is_leak(text: str, bench: List[str], bench_shingles: set) -> bool:
    if not text:
        return False
    for candidate in bench:
        # Whole-question containment in either direction (the bench question is
        # often embedded in a longer instruction).
        if len(candidate) >= 12 and (candidate in text or text in candidate):
            return True
    return bool(_shingles(text) & bench_shingles)


def _load(path: Path) -> Iterable[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return raw
    return raw.get("examples") or []


def build(limit: int = 0) -> Tuple[List[dict], dict]:
    bench = _benchmark_texts()
    bench_shingles: set = set()
    for question in bench:
        bench_shingles |= _shingles(question)

    seen: set = set()
    rows: List[dict] = []
    report: Dict[str, dict] = {}
    dropped = {"empty": 0, "duplicate": 0, "benchmark_leak": 0}

    for name in SOURCES:
        path = RAW / name
        if not path.exists():
            report[name] = {"present": False}
            continue
        kept = 0
        total = 0
        for item in _load(path):
            total += 1
            if limit and kept >= limit:
                break
            pair = _pair(item)
            text_in, text_out = _norm(pair["input"]), _norm(pair["output"])
            if not text_in or not text_out:
                dropped["empty"] += 1
                continue
            if _is_leak(text_in, bench, bench_shingles):
                dropped["benchmark_leak"] += 1
                continue
            key = (text_in, text_out)
            if key in seen:
                dropped["duplicate"] += 1
                continue
            seen.add(key)
            rows.append({"input": pair["input"], "output": pair["output"], "source": name})
            kept += 1
        report[name] = {
            "present": True,
            "rows": total,
            "kept": kept,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()[:16],
        }

    return rows, {"sources": report, "dropped": dropped, "benchmark_questions": len(bench)}


def split(
    rows: List[dict], val_ratio: float, seed: str = "core-v1"
) -> Tuple[List[dict], List[dict]]:
    train, val = [], []
    for row in rows:
        digest = hashlib.sha1(f"{seed}:{_norm(row['input'])}".encode()).hexdigest()
        bucket = int(digest[:8], 16) / 0xFFFFFFFF
        (val if bucket < val_ratio else train).append(row)
    return train, val


def _write(path: Path, rows: List[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    path.write_text(payload, encoding="utf-8")
    return hashlib.sha256(payload.encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="prepare core training data")
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    parser.add_argument("--limit", type=int, default=0, help="max kept rows per source")
    parser.add_argument("--val-ratio", type=float, default=0.05)
    parser.add_argument("--check", action="store_true", help="verify the manifest")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    manifest_path = out_dir / "core_train_manifest.json"

    if args.check:
        if not manifest_path.exists():
            print("no manifest; run the preparation first")
            return 1
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for name in ("core_train.jsonl", "core_val.jsonl"):
            path = out_dir / name
            if not path.exists():
                print(f"MISSING {name}")
                return 1
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != manifest["files"].get(name):
                print(f"HASH MISMATCH {name}")
                return 1
        print(f"OK: {manifest['files']} (leak check recorded: {manifest['report']['dropped']})")
        return 0

    rows, report = build(limit=args.limit)
    train, val = split(rows, args.val_ratio)
    files = {
        "core_train.jsonl": _write(out_dir / "core_train.jsonl", train),
        "core_val.jsonl": _write(out_dir / "core_val.jsonl", val),
    }
    manifest = {
        "generated_by": "scripts/prepare_core_training_data.py",
        "seed": "core-v1",
        "val_ratio": args.val_ratio,
        "train": len(train),
        "val": len(val),
        "total": len(rows),
        "files": files,
        "report": report,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("train", "val", "total")}, ensure_ascii=False))
    print("dropped:", report["dropped"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
