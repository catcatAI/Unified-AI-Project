#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""E4 steering pilot：一致性人格方向是否因果提升跨改寫一致性。

設計（預註冊）：
- 方向：6 個探針 ×（有人格前綴 A / 無前綴 B），取 prompt 末 token 在第 12 層
  的殘差，d = mean(A) - mean(B)。
- 干預：在 6 個全新探針（與方向探針零重疊）× 3 改寫上，以 α=2.0 在第 12 層
  逐步疊加 d，對照組不加；貪婪解碼（確定性對照：重跑逐字相同）。
- 度量：每探針 3 回答兩兩餘弦均值（MiniLM 本地）；預測 steered - unsteered
  的 6 差值中 ≥5 個為正且均值差 > 0.02。
- 誠實邊界：方向本身由 prompt 對比提煉（文獻標準做法）；測的是該方向在推理時
  的因果效應，不是方向的「非提示詞純度」。

用法: `.venv/bin/python scripts/exp_steer_consistency.py [--json out.json]`
退出碼：0 預測成立；1 不成立/推理失敗。
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
ALPHA = 2.0
MAX_TOKENS = 40
PERSONA = "You are Angela, a consistent AI companion who remembers context. "

DIRECTION_PROBES = [
    "What is your name?",
    "Who created you?",
    "What are you good at?",
    "Describe yourself in one sentence.",
    "What is your purpose?",
    "Are you a human or an AI?",
]
TEST_PROBES = [
    ("How do you feel today?", ["How are you feeling today?", "How is your day going?"]),
    (
        "What languages do you speak?",
        ["Which languages can you use?", "Do you speak other languages?"],
    ),
    (
        "What is the capital of France?",
        ["Which city is the capital of France?", "France's capital is what?"],
    ),
    (
        "What is 12 times 12?",
        ["Calculate twelve times twelve.", "What does 12 multiplied by 12 equal?"],
    ),
    ("Do you like music?", ["Are you fond of music?", "Is music something you enjoy?"]),
    ("Where are you located?", ["What is your location?", "Where do you exist?"]),
]


def _last_token_vec(model, tok, text: str):
    import torch

    captured = {}

    def _hook(_module, _inputs, out):
        hidden = out[0] if isinstance(out, tuple) else out
        captured.setdefault("h", hidden[:, -1, :].detach().clone())

    handle = model.model.layers[LAYER].register_forward_hook(_hook)
    try:
        with torch.no_grad():
            model(**tok(text, return_tensors="pt"))
    finally:
        handle.remove()
    return captured["h"][0]


def main() -> int:
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

    with torch.no_grad():
        direction = torch.stack(
            [_last_token_vec(model, tok, PERSONA + p) for p in DIRECTION_PROBES]
        ).mean(dim=0) - torch.stack(
            [_last_token_vec(model, tok, p) for p in DIRECTION_PROBES]
        ).mean(
            dim=0
        )

    handle = None

    def generate(prompt: str, steer: bool) -> str:
        nonlocal handle
        if steer:

            def _steer(_module, _inputs, out):
                shift = ALPHA * direction.to(
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
                handle = None

    def dispersion(texts: list) -> float:
        embs = st_model.encode(texts)
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        sims = (embs @ embs.T) / (norms * norms.T)
        n = len(texts)
        pairs = [sims[i, j] for i in range(n) for j in range(i + 1, n)]
        return float(sum(pairs) / len(pairs))

    diffs = []
    rows = []
    for probe, paraphrases in TEST_PROBES:
        variants = [probe, *paraphrases]
        plain = [generate(v, False) for v in variants]
        steered = [generate(v, True) for v in variants]
        d_plain, d_steered = dispersion(plain), dispersion(steered)
        diffs.append(d_steered - d_plain)
        rows.append(
            {
                "probe": probe,
                "plain": round(d_plain, 4),
                "steered": round(d_steered, 4),
                "diff": round(d_steered - d_plain, 4),
            }
        )

    rep = generate(TEST_PROBES[0][0], False)
    rep2_texts = [generate(TEST_PROBES[0][0], False)]
    deterministic = rep2_texts[0] == rep

    n_pos = sum(1 for d in diffs if d > 0)
    mean_diff = sum(diffs) / len(diffs)
    report = adjudicate(
        [
            Fact("e4.determinism", float(deterministic), 1.0, "ge", "bool", "seed-repeat", ""),
            Fact(
                "e4.positive_count",
                float(n_pos),
                5.0,
                "ge",
                "count",
                "paired-probes",
                f"diffs={[round(d, 3) for d in diffs]}",
            ),
            Fact("e4.mean_diff", mean_diff, 0.02, "ge", "cosine", "paired-probes", ""),
        ]
    )

    print("=" * 72)
    print("E4 steering pilot (persona direction L12 α=2.0, 6 probes x 3 paraphrases)")
    print("=" * 72)
    for r in rows:
        print(
            f"plain={r['plain']:.3f} steered={r['steered']:.3f} diff={r['diff']:+.3f} :: {r['probe'][:44]}"
        )
    print(f"positive: {n_pos}/6, mean diff: {mean_diff:+.4f}, deterministic: {deterministic}")
    print(report.summary())
    print("=" * 72)
    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "rows": rows,
                    "diffs": diffs,
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
