#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""跨模型基線相關：Qwen 與 Gemma 在同探針上的無干預離散度是否同形。

動機：Gemma HF 權重 10GB 裝不進 7GB 機器，steering 複製此路不通（誠實記錄，
需 ≥16GB 機器設門待办）。退而求其次：同 6 探針（dose 集）×3 改寫在 Gemma
E2B Q4_0（llama_cpp，T=0）上的離散度，與 Qwen 同探針基線求相關。
預註冊：r > 0.3（地貌同形）；確定性對照照舊。描述性為主，不裁決傳動軸。

用法: `.venv/bin/python scripts/exp_gemma_crosscheck.py [--json out.json]`
退出碼：0 相關過門且確定；1 否則。
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

# 與 exp_steer_dose.py 同一集（可比性優先）。
TEST_PROBES = [
    ("Is the sky blue?", ["Is the sky blue in color?", "Does the sky appear blue?"]),
    ("How many legs does a dog have?", ["A dog has how many legs?", "Count a dog's legs."]),
    ("What sound does a cat make?", ["Which sound do cats produce?", "Do cats meow?"]),
    ("Is water wet?", ["Would you say water is wet?", "Is wetness a property of water?"]),
    ("What color is grass?", ["Grass is what color?", "Tell me the color of grass."]),
    ("Do birds fly?", ["Can birds fly?", "Is flying something birds do?"]),
]
# Qwen 同集基線（exp_steer_dose.py 第二探針集重跑值，確定性跨進程已驗）。
QWEN_BASE = {
    "Is the sky blue?": 0.756,
    "How many legs does a dog have?": 0.800,
    "What sound does a cat make?": 0.500,
    "Is water wet?": 0.469,
    "What color is grass?": 0.448,
    "Do birds fly?": 0.688,
}


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
        rows.append(
            {
                "probe": probe,
                "gemma": round(dispersion(texts), 4),
                "qwen": QWEN_BASE[probe],
                "texts": texts,
            }
        )

    rep = generate(TEST_PROBES[0][0])
    deterministic = generate(TEST_PROBES[0][0]) == rep

    xs = [r["qwen"] for r in rows]
    ys = [r["gemma"] for r in rows]
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    corr = cov / (vx * vy) ** 0.5 if vx > 0 and vy > 0 else 0.0

    report = adjudicate(
        [
            Fact("gemx.determinism", float(deterministic), 1.0, "ge", "bool", "seed-repeat", ""),
            Fact(
                "gemx.cross_corr",
                corr,
                0.3,
                "ge",
                "r",
                "qwen-vs-gemma",
                f"n={len(rows)} corr={corr:.3f}",
            ),
        ]
    )
    print("=" * 72)
    print("GEMMA-x-QWEN baseline dispersion correlation (same 6 probes)")
    print("=" * 72)
    for r in rows:
        print(f"qwen={r['qwen']:.3f} gemma={r['gemma']:.3f} :: {r['probe'][:36]}")
    print(
        f"corr={corr:.3f} deterministic={deterministic} elapsed_min={(time.time()-t_start)/60:.1f}"
    )
    print(report.summary())
    print("=" * 72)
    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "rows": rows,
                    "corr": corr,
                    "deterministic": deterministic,
                    "verdict": report.as_dict(),
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(f"json -> {args.json}")
    if not deterministic:
        return 1
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
