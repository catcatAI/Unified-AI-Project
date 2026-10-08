#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""E4-CONFIRM：低劑量獲益在第三探針集上是否重現（L12，α∈{1.0,2.0}）。

動機：劑量軸在第二探針集呈倒 U（α≤2 正、α=4 負）。本輪用**第三探針集**
（與前兩集零重疊）檢驗低劑量獲益是否重現，門檻與 E4 同（每 α 均值差 > 0.02）。
任一 α 未過即 BLOCKED，不合併、不撈取。

用法: `.venv/bin/python scripts/exp_steer_confirm.py [--json out.json]`
退出碼：0 兩 α 全過；1 否則。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))

QWEN = (
    "/home/cxuo/.cache/huggingface/hub/models--Qwen--Qwen2.5-0.5B-Instruct"
    "/snapshots/7ae557604adf67be50417f59c2c2f167def9a775"
)
MINILM = (
    "/home/cxuo/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2"
    "/snapshots/e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
)
LAYER = 12
ALPHAS = [1.0, 2.0]
MAX_TOKENS = 30
PERSONA = "You are Angela, a consistent AI companion who remembers context. "

DIRECTION_PROBES = [
    "Do you enjoy reading books?",
    "What is your favorite color?",
    "Can you help me write an email?",
    "Do you prefer mornings or evenings?",
    "What do you think about rainy days?",
    "Have you traveled anywhere interesting?",
]
TEST_PROBES = [
    ("Is fire hot?", ["Does fire feel hot?", "Is fire cold or hot?"]),
    ("How many days are in a week?", ["A week has how many days?", "Count the days of a week."]),
    ("What do bees make?", ["What substance do bees produce?", "Do bees make honey?"]),
    ("Is ice cold?", ["Does ice feel cold?", "Is ice hot or cold?"]),
    ("What color is the sun?", ["The sun is what color?", "Describe the color of the sun."]),
    ("Do fish swim?", ["Can fish swim?", "Is swimming something fish do?"]),
]


def main() -> int:
    t_start = time.time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    import numpy as np
    import torch
    from core.facts import Fact, adjudicate
    from sentence_transformers import SentenceTransformer
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(QWEN, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(QWEN, local_files_only=True, dtype=torch.float32)
    model.eval()
    st_model = SentenceTransformer(MINILM, local_files_only=True)

    def last_vec(text: str):
        captured = {}

        def _hook(_m, _i, out):
            hidden = out[0] if isinstance(out, tuple) else out
            captured.setdefault("h", hidden[:, -1, :].detach().clone())

        handle = model.model.layers[LAYER].register_forward_hook(_hook)
        try:
            with torch.no_grad():
                model(**tok(text, return_tensors="pt"))
        finally:
            handle.remove()
        return captured["h"][0]

    with torch.no_grad():
        direction = torch.stack([last_vec(PERSONA + p) for p in DIRECTION_PROBES]).mean(
            dim=0
        ) - torch.stack([last_vec(p) for p in DIRECTION_PROBES]).mean(dim=0)

    def generate(prompt: str, alpha: float | None) -> str:
        handle = None
        if alpha is not None:

            def _steer(_m, _i, out):
                shift = alpha * direction.to(
                    out[0].device if isinstance(out, tuple) else out.device
                )
                if isinstance(out, tuple):
                    return (out[0] + shift,) + out[1:]
                return out + shift

            handle = model.model.layers[LAYER].register_forward_hook(_steer)
        try:
            inp = tok(prompt, return_tensors="pt")
            with torch.no_grad():
                out = model.generate(**inp, max_new_tokens=MAX_TOKENS, do_sample=False)
            return tok.decode(out[0][inp["input_ids"].shape[1] :], skip_special_tokens=True)
        finally:
            if handle is not None:
                handle.remove()

    def dispersion(texts: list) -> float:
        embs = st_model.encode(texts)
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        sims = (embs @ embs.T) / (norms * norms.T)
        n = len(texts)
        pairs = [sims[i, j] for i in range(n) for j in range(i + 1, n)]
        return float(sum(pairs) / len(pairs))

    base_disp = {}
    for probe, paraphrases in TEST_PROBES:
        variants = [probe, *paraphrases]
        base_disp[probe] = dispersion([generate(v, None) for v in variants])

    mean_diffs = []
    for alpha in ALPHAS:
        diffs = []
        for probe, paraphrases in TEST_PROBES:
            variants = [probe, *paraphrases]
            steered = [generate(v, alpha) for v in variants]
            diffs.append(dispersion(steered) - base_disp[probe])
        mean_diffs.append(sum(diffs) / len(diffs))

    rep = generate(TEST_PROBES[0][0], None)
    deterministic = generate(TEST_PROBES[0][0], None) == rep

    facts = [Fact("e4c.determinism", float(deterministic), 1.0, "ge", "bool", "seed-repeat", "")]
    for a, d in zip(ALPHAS, mean_diffs):
        facts.append(Fact(f"e4c.mean_diff_a{a}", d, 0.02, "ge", "cosine", "confirm-probes", ""))
    report = adjudicate(facts)

    print("=" * 72)
    print("E4-CONFIRM low-dose replication on third probe set (L12)")
    print("=" * 72)
    for a, d in zip(ALPHAS, mean_diffs):
        print(f"alpha={a:<4} mean_diff={d:+.4f}")
    print(f"deterministic: {deterministic}, elapsed_min={(time.time()-t_start)/60:.1f}")
    print(report.summary())
    print("=" * 72)
    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "alphas": ALPHAS,
                    "mean_diffs": mean_diffs,
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
