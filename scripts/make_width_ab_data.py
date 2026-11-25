#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# LAYER: learning
# =============================================================================
"""Deterministic synthetic addition splits for the width learnability A/B.

The question is narrow: at the **same** step budget, does the medium token-SNN
(16.7M) learn a rule that the small one (3.5M) does not? The frozen benchmark
items cannot answer it (they are a capability test, and using them for this
would be teaching to the test), so this script generates a separate task with
a rule, a train split and a held-out split of **unseen operand pairs**.

Three difficulties, disjoint by operand range:

* ``d1``: one digit + one digit          (100 pairs)
* ``d2``: two digits + one digit         (900 pairs)
* ``d3``: two digits + two digits        (8,100 pairs)

Split is a salted hash of ``"a+b"``: 20% of the pairs are held out, so the
split is deterministic and reproducible without storing a row list. The rule
is ordinary addition, including carries; nothing here comes from
``benchmarks/`` or ``apps/backend/data/processed``.

Usage::

    python scripts/make_width_ab_data.py --out-dir data/width_ab
    python scripts/make_width_ab_data.py --out-dir data/width_ab --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "data" / "width_ab"

#: name -> (a_low, a_high, b_low, b_high)
SPECS: Dict[str, Tuple[int, int, int, int]] = {
    "d1": (0, 9, 0, 9),
    "d2": (10, 99, 0, 9),
    "d3": (10, 99, 10, 99),
}


def pairs(spec: Tuple[int, int, int, int]) -> List[Tuple[int, int]]:
    a_low, a_high, b_low, b_high = spec
    return [(a, b) for a in range(a_low, a_high + 1) for b in range(b_low, b_high + 1)]


def held_out(a: int, b: int, salt: str, test_per_mille: int) -> bool:
    digest = hashlib.blake2b(f"{salt}:{a}+{b}".encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % 1000 < test_per_mille


def split(
    spec: Tuple[int, int, int, int], salt: str, test_per_mille: int
) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    train: List[Tuple[int, int]] = []
    val: List[Tuple[int, int]] = []
    for a, b in pairs(spec):
        (val if held_out(a, b, salt, test_per_mille) else train).append((a, b))
    return train, val


def rows(pairs_: Iterable[Tuple[int, int]]) -> List[Dict[str, str]]:
    return [{"input": f"{a}+{b}", "output": str(a + b)} for a, b in pairs_]


def dumps(rows_: List[Dict[str, str]]) -> str:
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows_)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build(out_dir: Path, salt: str, test_per_mille: int) -> Dict[str, object]:
    manifest: Dict[str, object] = {
        "salt": salt,
        "test_per_mille": test_per_mille,
        "rule": "a+b (ordinary addition, carries included)",
        "source": "synthetic; no benchmark or processed corpus rows",
        "difficulties": {},
    }
    for name, spec in SPECS.items():
        train, val = split(spec, salt, test_per_mille)
        train_text = dumps(rows(train))
        val_text = dumps(rows(val))
        (out_dir / f"{name}_train.jsonl").write_text(train_text, encoding="utf-8")
        (out_dir / f"{name}_val.jsonl").write_text(val_text, encoding="utf-8")
        manifest["difficulties"][name] = {
            "spec": {"a": [spec[0], spec[1]], "b": [spec[2], spec[3]]},
            "train": len(train),
            "val": len(val),
            "train_sha256": sha(train_text),
            "val_sha256": sha(val_text),
        }
    return manifest


def check(out_dir: Path, manifest: Dict[str, object]) -> List[str]:
    problems: List[str] = []
    for name, cell in manifest["difficulties"].items():
        for part in ("train", "val"):
            path = out_dir / f"{name}_{part}.jsonl"
            if not path.is_file():
                problems.append(f"{path.name}: missing")
                continue
            text = path.read_text(encoding="utf-8")
            if sha(text) != cell[f"{part}_sha256"]:
                problems.append(f"{path.name}: content differs from the manifest")
            if len(text.splitlines()) != cell[part]:
                problems.append(f"{path.name}: row count differs from the manifest")
    return problems


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="synthetic addition splits for the width A/B")
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--salt", default="width-ab-2026-11-21")
    ap.add_argument("--test-per-mille", type=int, default=200, help="held-out share, per 1000")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    out_dir = Path(args.out_dir)
    manifest_path = out_dir / "manifest.json"
    if args.check:
        if not manifest_path.is_file():
            print(f"missing {manifest_path}")
            return 1
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        problems = check(out_dir, manifest)
        if problems:
            print("❌ " + "; ".join(problems))
            return 1
        print(f"✅ {out_dir}: splits agree with the manifest")
        return 0

    if not 0 < args.test_per_mille < 1000:
        print("--test-per-mille must be between 1 and 999")
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = build(out_dir, args.salt, args.test_per_mille)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    for name, cell in manifest["difficulties"].items():
        print(f"  {name}: train={cell['train']} val={cell['val']}")
    print(f"wrote {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
