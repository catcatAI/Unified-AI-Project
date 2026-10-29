#!/usr/bin/env python3
"""Prepare the AI+AL joint training data (pilot records -> trainable jsonl).

The AI+AL pilot dataset stores ``input_text -> expected_response`` together
with the AL state before and after the interaction. The text trainer
(``scripts/train_token_snn.py``) only understands ``{"input", "output"}``
pairs, so this script serialises the AL state into both sides of the pair:

* **input**  = ``<al_state_in> | <input_text>``
  the model sees the metabolic/emotional state it is answering *from*.
* **output** = ``<expected_response>`` then a newline then
  ``<al_state_out>`` — the response first (that is what a reader sees), the
  post-interaction state second (the transition the AL engine will apply).

Rules:

1. **Deterministic split**: sha1 of the sample_id decides train/val (80/20,
   at least one row on each side with >1 record). Same input -> same split.
2. **No duplication**: every record appears in exactly one split.
3. **No benchmark leakage**: an input whose normalised text equals a
   benchmark question is dropped and counted (a score on data the model
   trained on is a fake score).

The manifest records counts, the source file hash and the leak count so a
later run can be compared and audited. ``--check`` re-derives everything and
fails if the files on disk drift from the source records.

Usage:
    python scripts/prepare_ai_al_training_data.py
    python scripts/prepare_ai_al_training_data.py --val-ratio 0.3
    python scripts/prepare_ai_al_training_data.py --src <round-1 dataset>
    python scripts/prepare_ai_al_training_data.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "apps" / "backend" / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

SRC = REPO_ROOT / "apps" / "backend" / "data" / "processed" / "ai_al_pilot_dataset.json"
OUT_DIR = REPO_ROOT / "apps" / "backend" / "data" / "processed"
TRAIN_OUT = OUT_DIR / "ai_al_train.jsonl"
VAL_OUT = OUT_DIR / "ai_al_val.jsonl"
MANIFEST_OUT = OUT_DIR / "ai_al_manifest.json"
BENCH = REPO_ROOT / "benchmarks" / "data" / "native_bench_v1.json"

_PUNCT = re.compile(r"[^\w\s]+", re.UNICODE)


def _norm(text: str) -> str:
    return " ".join(_PUNCT.sub(" ", str(text or "")).lower().split())


def _state_line(state: Dict[str, object], intent: str, side: str) -> str:
    """One compact, token-friendly line describing an AL state."""
    return (
        f"<al_{side}> v={float(state['valence']):.2f} a={float(state['arousal']):.2f} "
        f"d={float(state['dominance']):.2f} fatigue={float(state['fatigue']):.2f} "
        f"stress={float(state['stress']):.2f} health={float(state['health']):.2f} "
        f"mode={state['routing_mode']} intent={intent}"
    )


def load_records(path: Path = SRC) -> List[dict]:
    """Read the pilot dataset and turn each example into a training pair."""
    data = json.loads(path.read_text(encoding="utf-8"))
    pairs: List[dict] = []
    for item in data.get("examples", []):
        intent = str(item.get("intent") or "unknown")
        inp = _state_line(item["al_state_in"], intent, "in") + " | " + str(item["input_text"])
        out = (
            str(item["expected_response"]) + "\n" + _state_line(item["al_state_out"], intent, "out")
        )
        pairs.append(
            {
                "sample_id": str(item["sample_id"]),
                "input": inp.strip(),
                "output": out.strip(),
                "intent": intent,
            }
        )
    return pairs


def _split(pairs: List[dict], val_ratio: float) -> Tuple[List[dict], List[dict]]:
    """Deterministic sha1 split; keeps at least one row per side when possible."""
    if len(pairs) < 2:
        return list(pairs), []
    val, train = [], []
    for row in pairs:
        bucket = int(hashlib.sha1(row["sample_id"].encode("utf-8")).hexdigest(), 16) % 100
        (val if bucket < val_ratio * 100 else train).append(row)
    if not val or not train:  # degenerate hash bucketing on a tiny dataset
        train, val = pairs[1:], pairs[:1]
    return train, val


def _benchmark_norms() -> List[str]:
    if not BENCH.exists():
        return []
    data = json.loads(BENCH.read_text(encoding="utf-8"))
    texts = []
    for suite in (data.get("suites") or {}).values():
        for item in suite.get("items") or []:
            if item.get("q"):
                texts.append(_norm(item["q"]))
    return texts


def build(val_ratio: float, src: Path = SRC) -> Dict[str, object]:
    pairs = load_records(src)
    bench = set(_benchmark_norms())
    kept = [p for p in pairs if _norm(p["input"].split("|", 1)[-1]) not in bench]
    leaked = len(pairs) - len(kept)
    train, val = _split(kept, val_ratio)
    return {
        "train": train,
        "val": val,
        "manifest": {
            "source": str(src.relative_to(REPO_ROOT)),
            "source_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
            "records": len(pairs),
            "leaked": leaked,
            "train": len(train),
            "val": len(val),
            "val_ratio": val_ratio,
            "format": {
                "input": "<al_in> v a d fatigue stress health mode intent | <input_text>",
                "output": "<expected_response>\\n<al_out> v a d fatigue stress health mode intent",
            },
            "note": (
                "The response comes first because that is what a reader sees; the "
                "state line after it is the transition the AL engine applies."
            ),
        },
    }


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--val-ratio", type=float, default=0.2, help="held-out share (default 0.2)")
    ap.add_argument(
        "--check",
        action="store_true",
        help="verify the files on disk match a fresh build (no writes)",
    )
    ap.add_argument(
        "--src",
        default=str(SRC),
        help="AL source in the pilot shape (default: the 10 hand-written rows); "
        "point it at scripts/generate_al_dataset.py's output for round 1+",
    )
    args = ap.parse_args(argv)

    src = Path(args.src).expanduser().resolve()
    if not src.is_file():
        print(f"check failed: missing source {src}")
        return 1
    built = build(args.val_ratio, src)
    train_body = "".join(
        json.dumps({"input": r["input"], "output": r["output"]}, ensure_ascii=False) + "\n"
        for r in built["train"]
    )
    val_body = "".join(
        json.dumps({"input": r["input"], "output": r["output"]}, ensure_ascii=False) + "\n"
        for r in built["val"]
    )

    if args.check:
        problems = []
        for path, expected in ((TRAIN_OUT, train_body), (VAL_OUT, val_body)):
            if not path.exists():
                problems.append(f"missing {path.name}")
            elif path.read_text(encoding="utf-8") != expected:
                problems.append(f"{path.name} differs from the source records")
        if problems:
            print("check failed: " + "; ".join(problems))
            return 1
        print(f"check ok: {built['manifest']['train']} train / {built['manifest']['val']} val")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TRAIN_OUT.write_text(train_body, encoding="utf-8")
    VAL_OUT.write_text(val_body, encoding="utf-8")
    MANIFEST_OUT.write_text(
        json.dumps(built["manifest"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    m = built["manifest"]
    print(
        f"records={m['records']} leaked={m['leaked']} "
        f"train={m['train']} val={m['val']}\n"
        f"wrote {TRAIN_OUT.name}, {VAL_OUT.name}, {MANIFEST_OUT.name}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
