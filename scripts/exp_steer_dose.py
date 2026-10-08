#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""E4劑量軸：steering 強度與一致性變化的單調關係（全新探針集）。

動機：E4 在 α=2.0 測得平均 -0.102（干預降低一致性）。若該方向真與一致性
機制相關，劑量反應應具結構：本實驗預註冊**單調非增**——α 越大，均值差越小
（0.5→1.0→2.0→4.0，容噪 tol=0.05 逐段比較；四段全順的偶然概率约 1/24）。
全新 6 探針 × 3 改寫，與 E4 探針集零重疊，禁事後撈取。

用法: `.venv/bin/python scripts/exp_steer_dose.py [--json out.json]`
退出碼：0 單調成立；1 不成立/推理失敗。
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
ALPHAS = [0.5, 1.0, 2.0, 4.0]
TOL = 0.05
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
    ("Is the sky blue?", ["Is the sky blue in color?", "Does the sky appear blue?"]),
    ("How many legs does a dog have?", ["A dog has how many legs?", "Count a dog's legs."]),
    ("What sound does a cat make?", ["Which sound do cats produce?", "Do cats meow?"]),
    ("Is water wet?", ["Would you say water is wet?", "Is wetness a property of water?"]),
    ("What color is grass?", ["Grass is what color?", "Tell me the color of grass."]),
    ("Do birds fly?", ["Can birds fly?", "Is flying something birds do?"]),
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

    base_texts = {}
    for probe, paraphrases in TEST_PROBES:
        variants = [probe, *paraphrases]
        base_texts[probe] = [generate(v, None) for v in variants]
    base_disp = {p: dispersion(v) for p, v in base_texts.items()}

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

    facts = [Fact("e4d.determinism", float(deterministic), 1.0, "ge", "bool", "seed-repeat", "")]
    for i in range(len(ALPHAS) - 1):
        facts.append(
            Fact(
                f"e4d.mono_a{ALPHAS[i]}_ge_a{ALPHAS[i+1]}",
                mean_diffs[i] - mean_diffs[i + 1],
                -TOL,
                "ge",
                "cosine",
                "dose-axis",
                f"d({ALPHAS[i]})={mean_diffs[i]:+.3f} d({ALPHAS[i+1]})={mean_diffs[i+1]:+.3f}",
            )
        )
    report = adjudicate(facts)

    print("=" * 72)
    print("E4-DOSE steering strength vs consistency delta (fresh probes, L12)")
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
