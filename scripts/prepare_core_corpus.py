#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L0] [α] [C] [L0]
# =============================================================================
"""Normalise downloaded dialogue corpora and train a 32k BPE tokenizer.

Sources (all from Hugging Face Hub, downloaded under data/datasets/):
  * HuggingFaceH4/ultrachat_200k  — English multi-turn dialogues
  * BAAI/COIG                    — Chinese instruction / dialogue
  * YeungNLP/firefly-train-1.1M  — Chinese instruction / dialogue

Output: data/core_corpus/sessions.jsonl (normalised turns), tokenizer.json,
tokens.npy (flat int32) + lengths.npy (int32 session lengths).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterator, List, Tuple

import numpy as np
from tokenizers import (
    Tokenizer,
    decoders,
    models,
    normalizers,
    pre_tokenizers,
    processors,
    trainers,
)

REPO = Path(__file__).resolve().parent.parent
SOURCES = {
    "ultrachat": REPO / "data" / "datasets" / "ultrachat_200k",
    "coig": REPO / "data" / "datasets" / "coig",
    "firefly": REPO / "data" / "datasets" / "firefly",
}


def _turns_from_obj(obj: object) -> List[Tuple[str, str]]:
    if not isinstance(obj, dict):
        return []
    for key in ("messages", "conversation", "conversations", "dialogue"):
        value = obj.get(key)
        if isinstance(value, list):
            turns: List[Tuple[str, str]] = []
            user = None
            for item in value:
                if not isinstance(item, dict):
                    continue
                role = str(item.get("role") or item.get("from") or "").lower()
                content = str(item.get("content") or item.get("value") or "")
                if not content:
                    continue
                if role in ("user", "human"):
                    user = content
                elif role in ("assistant", "gpt", "bot") and user is not None:
                    turns.append((user, content))
                    user = None
            if turns:
                return turns
    instruction = obj.get("instruction") or obj.get("input")
    if isinstance(instruction, str):
        inp = obj.get("input")
        prompt = instruction + ("\n" + str(inp) if inp else "")
        out = obj.get("output") or obj.get("answer") or obj.get("target")
        if isinstance(out, str) and out.strip():
            return [(prompt, out)]
    return []


def load_sessions(source: str, root: Path, limit: int) -> List[List[Tuple[str, str]]]:
    out: List[List[Tuple[str, str]]] = []
    if not root.exists():
        return out
    files = (
        sorted(root.rglob("*.parquet"))
        + sorted(root.rglob("*.jsonl"))
        + sorted(root.rglob("*.json"))
    )
    for file in files:
        if file.name.endswith("tokenizer.json") or "README" in file.name:
            continue
        try:
            if file.suffix == ".parquet":
                import pyarrow.parquet as pq

                rows = pq.read_table(file, columns=["messages"]).to_pylist()
            else:
                rows = []
                with file.open(encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rows.append(json.loads(line))
                        except ValueError:
                            continue
        except Exception:
            continue
        for row in rows:
            turns = _turns_from_obj(row)
            if turns and any(t.strip() for t, _ in turns):
                out.append(turns)
            if len(out) >= limit:
                break
        if len(out) >= limit:
            break
    return out[:limit]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--per-source", type=int, default=100000)
    p.add_argument("--vocab-size", type=int, default=32768)
    p.add_argument("--out-dir", default=str(REPO / "data" / "core_corpus"))
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    all_sessions: List[List[Tuple[str, str]]] = []
    for name, root in SOURCES.items():
        sessions = load_sessions(name, root, args.per_source)
        print(f"{name}: {len(sessions)} sessions")
        all_sessions.extend(sessions)
    if not all_sessions:
        print("no sessions found — check downloads")
        return 1

    with (out_dir / "sessions.jsonl").open("w", encoding="utf-8") as fh:
        for turns in all_sessions:
            fh.write(json.dumps({"turns": turns}, ensure_ascii=False) + "\n")

    tokenizer = Tokenizer(models.BPE(unk_token="<unk>"))
    tokenizer.normalizer = normalizers.NFC()
    tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tokenizer.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(
        vocab_size=args.vocab_size,
        special_tokens=["<pad>", "<bos>", "<eos>", "<unk>"],
        show_progress=False,
    )

    def iterator() -> Iterator[str]:
        for turns in all_sessions:
            for user, assistant in turns:
                yield user + "\n" + assistant

    tokenizer.train_from_iterator(iterator(), trainer=trainer)
    tokenizer.post_processor = processors.TemplateProcessing(
        single="<bos> $A <eos>", special_tokens=[("<bos>", 1), ("<eos>", 2)]
    )
    tokenizer.save(str(out_dir / "tokenizer.json"))

    flat: List[int] = []
    lengths: List[int] = []
    for turns in all_sessions:
        ids = [1]
        for user, assistant in turns:
            ids += tokenizer.encode(user + "\n" + assistant).ids[:512] + [2]
        if len(ids) > 1:
            flat.extend(ids)
            lengths.append(len(ids))
    np.save(out_dir / "tokens.npy", np.array(flat, dtype=np.int32))
    np.save(out_dir / "lengths.npy", np.array(lengths, dtype=np.int32))
    print(f"sessions={len(lengths)} tokens={len(flat)} vocab={tokenizer.get_vocab_size()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
