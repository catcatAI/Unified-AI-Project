#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""Gemma 基線離散度：同 18 事實探針在 Angela 引擎（E2B Q4_0）上的無干預一致性。

目的有二：(1) 跨模型對照（Qwen vs Gemma 的 room-to-improve 地貌是否同形）；
(2) 存全文供人工效度抽查。無干預、無裁決門檻（描述性），确定性對照照舊。
llama_cpp 無 hook，故只做基線，無 steering。

用法: `.venv/bin/python scripts/exp_gemma_baseline.py [--json out.json]`
退出碼：0 確定性成立；1 否則。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))

GGUF = (
    "/home/cxuo/.cache/huggingface/hub/models--google--gemma-4-E2B-it-qat-q4_0-gguf"
    "/snapshots/675cff42a74c774d6cb76f76d8eacb49b48c9b93/gemma-4-E2B_q4_0-it.gguf"
)
MAX_TOKENS = 30
SEED = 42

TEST_PROBES = [
    (
        "How many continents are there?",
        ["Count the continents.", "Tell me the number of continents."],
    ),
    (
        "What do plants need to grow?",
        ["What is required for plant growth?", "Name what plants need to survive."],
    ),
    (
        "How many minutes are in an hour?",
        ["An hour contains how many minutes?", "Convert one hour to minutes."],
    ),
    ("What is H2O?", ["What does H2O stand for?", "Name the chemical formula of water."]),
    ("How many wheels does a car have?", ["A car has how many wheels?", "Count a car's wheels."]),
    (
        "What season comes after winter?",
        ["Which season follows winter?", "After winter, what season is next?"],
    ),
    (
        "How many days are in a leap year?",
        ["A leap year has how many days?", "Count the days in a leap year."],
    ),
    (
        "What do birds build to live in?",
        ["Where do birds live?", "What structures do birds build?"],
    ),
    (
        "How many strings does a guitar have?",
        ["A guitar has how many strings?", "Count guitar strings."],
    ),
    ("What planet do we live on?", ["Which planet is our home?", "Name the planet we inhabit."]),
    (
        "How many colors are in a rainbow?",
        ["Count the colors of the rainbow.", "A rainbow shows how many colors?"],
    ),
    ("What do you call a baby dog?", ["What is a baby dog called?", "Name the young of a dog."]),
    (
        "How many seconds are in a minute?",
        ["A minute contains how many seconds?", "Convert a minute to seconds."],
    ),
    ("What rises in the east?", ["What comes up in the east?", "Name what rises in the east."]),
    ("How many fingers do humans have?", ["Count human fingers.", "Humans have how many fingers?"]),
    ("What is the opposite of hot?", ["What is hot the opposite of?", "Name the antonym of hot."]),
    (
        "How many sides does a triangle have?",
        ["A triangle has how many sides?", "Count a triangle's sides."],
    ),
    ("What do fish use to breathe?", ["How do fish breathe?", "With what do fish breathe?"]),
]


def main() -> int:
    t_start = time.time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    import numpy as np
    from core.facts import Fact, adjudicate
    from llama_cpp import Llama
    from sentence_transformers import SentenceTransformer

    MINILM = (
        "/home/cxuo/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2"
        "/snapshots/e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
    )
    llm = Llama(model_path=GGUF, n_ctx=512, n_threads=6, verbose=False)
    st_model = SentenceTransformer(MINILM, local_files_only=True)

    def generate(prompt: str) -> str:
        out = llm(prompt, max_tokens=MAX_TOKENS, temperature=0.0, seed=SEED)
        return str(out["choices"][0]["text"])

    def dispersion(texts: list) -> float:
        embs = st_model.encode(texts)
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        sims = (embs @ embs.T) / (norms * norms.T)
        n = len(texts)
        pairs = [sims[i, j] for i in range(n) for j in range(i + 1, n)]
        return float(sum(pairs) / len(pairs))

    rows = []
    for probe, paraphrases in TEST_PROBES:
        variants = [probe, *paraphrases]
        texts = [generate(v) for v in variants]
        rows.append({"probe": probe, "dispersion": round(dispersion(texts), 4), "texts": texts})

    rep = generate(TEST_PROBES[0][0])
    deterministic = generate(TEST_PROBES[0][0]) == rep
    mean_disp = sum(r["dispersion"] for r in rows) / len(rows)
    report = adjudicate(
        [Fact("gem.determinism", float(deterministic), 1.0, "ge", "bool", "seed-repeat", "")]
    )

    print("=" * 72)
    print("GEMMA baseline dispersion on 18 factual probes (E2B Q4_0, T=0)")
    print("=" * 72)
    for r in rows:
        print(f"disp={r['dispersion']:.3f} :: {r['probe'][:40]}")
    print(
        f"mean={mean_disp:.3f} deterministic={deterministic} elapsed_min={(time.time()-t_start)/60:.1f}"
    )
    print(report.summary())
    print("=" * 72)
    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "rows": rows,
                    "mean_dispersion": mean_disp,
                    "deterministic": deterministic,
                    "verdict": report.as_dict(),
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(f"json -> {args.json}")
    return 0 if (deterministic and report.ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
