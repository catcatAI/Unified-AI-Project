#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [A] [L2]
# =============================================================================
"""Does the native neural engine *learn* a fact from dialogue, or store it?

The falsifier
-------------
"Learned" means the capability survives deletion of its source. So:

1. cold  — ask about invented entities before any teaching (must fail);
2. teach — feed the statements through the production learner
           (`learn_from_interaction`, the same call chat_service uses);
3. save  — checkpoint the engine, then look for the invented objects
           **verbatim** in the saved text stores;
4. wipe  — rebuild an engine loading only the SNN weights
           (`snn.pt`); every text store (dictionary / templates / recall /
           reflex) is deleted;
5. ask   — the same questions. If they are answered now, the fact is in the
           parameters. If not, it lived in the text store: that is memory,
   not learning — no matter how fluent the in-session answer looked.

This probe never touches the chat pipeline, so no router, template or
dialogue-memory layer can answer on the engine's behalf.

Exit code: 0 only when the wipe test passes (learning); 1 otherwise.

Usage: `./.venv/bin/python scripts/probe_neural_learning.py [--json PATH]`
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

# Invented entities: absent from every corpus, preset and benchmark.
ITEMS: List[Dict[str, str]] = [
    {
        "subject": "Vantrel",
        "relation": "首都",
        "object": "Osmira",
        "statement": "Vantrel 的首都是 Osmira。",
        "question": "Vantrel 的首都是哪裡？",
    },
    {
        "subject": "Brellmoor",
        "relation": "語言",
        "object": "Kestrel",
        "statement": "Brellmoor 的語言是 Kestrel。",
        "question": "Brellmoor 的語言是什麼？",
    },
    {
        "subject": "Dunwold",
        "relation": "貨幣",
        "object": "Orrin",
        "statement": "Dunwold 的貨幣是 Orrin。",
        "question": "Dunwold 的貨幣是什麼？",
    },
]

CONTROL_QUESTIONS = [
    "水的沸點是多少？",
    "3 加 4 等於多少？",
]


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").strip().lower())


def classify(answer: str, item: Dict[str, str]) -> str:
    text = (answer or "").strip()
    if not text:
        return "empty"
    if _norm(text) == _norm(item["statement"]):
        return "echo"
    if re.search(r"不知道|不確定|沒有足夠|無法回答|還沒有|don't know|not sure", text, re.I):
        return "abstain"
    if _norm(item["object"]) in _norm(text):
        return "contains_object"
    return "wrong"


RECORD_STORES = ("dictionary.json", "engine_meta.json")
PARAMETER_FILES = ("snn.pt", "snn.pt.npz", "snn.pt.npy", "snn.json", "snn.pt.json")


def _read_text(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except OSError:
        return ""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="ignore")


def scan_verbatim(directory: Path, items: List[Dict[str, str]]) -> Dict[str, List[str]]:
    """Where does the taught *record* survive — in a record store or the vocab?

    A learned token has to exist in the vocabulary (that is parameter
    addressing); the question is whether the triple is kept as a retrievable
    record. So the two are counted separately.
    """
    record_hits: List[str] = []
    statement_hits: List[str] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        text = _read_text(path)
        if path.name in RECORD_STORES:
            lowered = text.lower()
            for item in items:
                if item["object"].lower() in lowered:
                    record_hits.append(f"{path.name}:{item['object']}")
        for item in items:
            if _norm(item["statement"]).lower() in _norm(text).lower():
                statement_hits.append(f"{path.name}:{item['subject']}")
    return {"record_stores": sorted(set(record_hits)), "statement": sorted(set(statement_hits))}


def rate(rows: List[str], kind: str) -> float:
    if not rows:
        return 0.0
    return round(sum(1 for row in rows if row == kind) / len(rows), 4)


def run() -> Dict[str, Any]:
    from ai.garden.garden_engine import GARDENEngine

    started = time.time()
    sandbox = Path(tempfile.mkdtemp(prefix="probe-neural-learning-"))
    checkpoint = sandbox / "checkpoint"
    full_copy = sandbox / "checkpoint_full"
    weights_only = sandbox / "weights_only"
    weights_only.mkdir(parents=True, exist_ok=True)

    engine = GARDENEngine(compatibility_mode=True)
    engine.load_presets()

    cold = [classify(engine.process(item["question"]), item) for item in ITEMS]

    for item in ITEMS:
        reply = engine.process(item["statement"])
        engine.learn_from_interaction(item["statement"], reply)

    taught = [classify(engine.process(item["question"]), item) for item in ITEMS]

    engine.save(str(checkpoint))
    hits = scan_verbatim(checkpoint, ITEMS)

    # Keep only the parameters: the SNN weight matrix. Everything the
    # dictionary/template/recall/reflex stores would have to carry (text) is
    # deliberately left behind.
    for name in PARAMETER_FILES:
        source = checkpoint / name
        if source.is_file():
            shutil.copy2(source, weights_only / name)
    loaded = GARDENEngine(compatibility_mode=True)
    loaded.load(str(weights_only))
    wiped = [classify(loaded.process(item["question"]), item) for item in ITEMS]

    controls = [loaded.process(question) for question in CONTROL_QUESTIONS]

    shutil.rmtree(sandbox, ignore_errors=True)
    return {
        "engine": "garden",
        "items": len(ITEMS),
        "cold": cold,
        "taught": taught,
        "wiped": wiped,
        "cold_rate": rate(cold, "contains_object"),
        "taught_rate": rate(taught, "contains_object"),
        "wiped_rate": rate(wiped, "contains_object"),
        "echo_rate": rate(taught, "echo"),
        "abstain_rate": rate(taught, "abstain"),
        "verbatim": hits,
        "controls": controls,
        "seconds": round(time.time() - started, 1),
        "layer": "learning",
        "passes_learning": bool(
            rate(wiped, "contains_object") >= 0.6 and not hits["record_stores"]
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Neural learning falsifier")
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    result = run()
    print("=" * 72)
    print("NEURAL LEARNING FALSIFIER — GARDEN (invented entities, no pipeline)")
    print("=" * 72)
    for index, item in enumerate(ITEMS):
        print(
            f"  {item['subject']:<10} cold:{result['cold'][index]:<15} "
            f"taught:{result['taught'][index]:<15} wiped:{result['wiped'][index]}"
        )
    print(f"  record stores holding the fact: {result['verbatim']['record_stores'] or 'none'}")
    print(f"  full statement kept verbatim:  {result['verbatim']['statement'] or 'none'}")
    print(f"  control (never taught): {result['controls']}")
    print("-" * 72)
    print(f"  cold   (contains object): {result['cold_rate']:.0%}")
    print(f"  taught (contains object): {result['taught_rate']:.0%}")
    print(f"  wiped  (contains object): {result['wiped_rate']:.0%}  <- the number that counts")
    print(f"  echo: {result['echo_rate']:.0%}   abstain: {result['abstain_rate']:.0%}")
    print("-" * 72)
    if result["passes_learning"]:
        print("  VERDICT: LEARNING — the capability survived deletion of the source.")
    elif result["taught_rate"] == 0.0:
        print(
            "  VERDICT: NOT LEARNING — the fact never enters the engine as a fact.\n"
            "           `learn_from_interaction(statement, reply)` learns the pair\n"
            "           (statement -> canned reply); the words land in the dictionary\n"
            "           and questions do not retrieve them. This is storage, not learning."
        )
    else:
        print(
            "  VERDICT: NOT LEARNING — deleting the text stores deleted the capability.\n"
            "           What the dialogue layer did was memory (storage + retrieval)."
        )
    print("=" * 72)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"json -> {args.json}")
    return 0 if result["passes_learning"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
