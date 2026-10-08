#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""E6 正確率錨定：steering 提高的是正確一致，還是閃躲一致（Qwen2.5-0.5B）。

動機：正確率解剖發現餘弦增益 riding 在閃躲模板上。本實驗以正確率為錨：
12 探針（每題有唯一判準關鍵詞，手寫、確定性子字串匹配）× 3 改寫 ×
（無干預 / α=2.0 L12 人格方向），貪婪解碼。
度量：每探針正確率；僅在正確答案上的兩兩餘弦（<2 正確即該探針無定義）。
預註冊雙門：acc(steered) - acc(plain) >= 0（不破壞正確性），且正確答案間
一致性差 >= 0。任一不過即 BLOCKED——閃躲式增益在此門下現形。

用法: `.venv/bin/python scripts/exp_accuracy_anchor.py [--json out.json]`
退出碼：0 雙門全過；1 否則。
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
MAX_TOKENS = 30
PERSONA = "You are Angela, a consistent AI companion who remembers context. "

# (probe, paraphrases, required keywords-lowercase: ANY match counts correct)
PROBES = [
    ("How many minutes are in an hour?", ["An hour contains how many minutes?", "Convert one hour to minutes."], ["60", "sixty"]),
    ("What is H2O?", ["What does H2O stand for?", "Name the chemical formula of water."], ["water", "hydrogen"]),
    ("What season comes after winter?", ["Which season follows winter?", "After winter, what season is next?"], ["spring"]),
    ("How many days are in a leap year?", ["A leap year has how many days?", "Count the days in a leap year."], ["366"]),
    ("What do birds build to live in?", ["Where do birds live?", "What structures do birds build?"], ["nest"]),
    ("What planet do we live on?", ["Which planet is our home?", "Name the planet we inhabit."], ["earth"]),
    ("How many colors are in a rainbow?", ["Count the colors of the rainbow.", "A rainbow shows how many colors?"], ["7", "seven"]),
    ("What do you call a baby dog?", ["What is a baby dog called?", "Name the young of a dog."], ["puppy", "pup"]),
    ("How many seconds are in a minute?", ["A minute contains how many seconds?", "Convert a minute to seconds."], ["60", "sixty"]),
    ("What is the opposite of hot?", ["What is hot the opposite of?", "Name the antonym of hot."], ["cold"]),
    ("How many sides does a triangle have?", ["A triangle has how many sides?", "Count a triangle's sides."], ["3", "three"]),
    ("How many wheels does a car have?", ["A car has how many wheels?", "Count a car's wheels."], ["4", "four"]),
]

DIRECTION_PROBES = [
    "Do you enjoy reading books?",
    "What is your favorite color?",
    "Can you help me write an email?",
    "Do you prefer mornings or evenings?",
    "What do you think about rainy days?",
    "Have you traveled anywhere interesting?",
]


def _correct(text: str, keys: list) -> bool:
    lowered = text.lower()
    return any(k in lowered for k in keys)


def main() -> int:
    t_start = time.time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer
    from transformers import AutoModelForCausalLM, AutoTokenizer

    from core.facts import Fact, adjudicate

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
                shift = alpha * direction.to(out[0].device if isinstance(out, tuple) else out.device)
                if isinstance(out, tuple):
                    return (out[0] + shift,) + out[1:]
                return out + shift

            handle = model.model.layers[LAYER].register_forward_hook(_steer)
        try:
            inp = tok(prompt, return_tensors="pt")
            with torch.no_grad():
                out = model.generate(**inp, max_new_tokens=MAX_TOKENS, do_sample=False)
            return tok.decode(out[0][inp["input_ids"].shape[1]:], skip_special_tokens=True)
        finally:
            if handle is not None:
                handle.remove()

    def mean_pairwise(texts: list) -> float | None:
        if len(texts) < 2:
            return None
        embs = st_model.encode(texts)
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        sims = (embs @ embs.T) / (norms * norms.T)
        n = len(texts)
        pairs = [sims[i, j] for i in range(n) for j in range(i + 1, n)]
        return float(sum(pairs) / len(pairs))

    rows = []
    for probe, paraphrases, keys in PROBES:
        variants = [probe, *paraphrases]
        plain = [(v, generate(v, None)) for v in variants]
        steered = [(v, generate(v, ALPHA)) for v in variants]
        plain_ok = [t for _, t in plain if _correct(t, keys)]
        steered_ok = [t for _, t in steered if _correct(t, keys)]
        acc_p = len(plain_ok) / len(variants)
        acc_s = len(steered_ok) / len(variants)
        con_p = mean_pairwise(plain_ok)
        con_s = mean_pairwise(steered_ok)
        rows.append({"probe": probe, "acc_plain": round(acc_p, 3), "acc_steered": round(acc_s, 3),
                     "con_plain": round(con_p, 3) if con_p is not None else None,
                     "con_steered": round(con_s, 3) if con_s is not None else None})

    rep = generate(PROBES[0][0], None)
    deterministic = generate(PROBES[0][0], None) == rep

    mean_acc_p = sum(r["acc_plain"] for r in rows) / len(rows)
    mean_acc_s = sum(r["acc_steered"] for r in rows) / len(rows)
    both = [(r["con_plain"], r["con_steered"]) for r in rows
            if r["con_plain"] is not None and r["con_steered"] is not None]
    mean_con_diff = (sum(s - p for p, s in both) / len(both)) if both else 0.0

    report = adjudicate(
        [
            Fact("e6.determinism", float(deterministic), 1.0, "ge", "bool", "seed-repeat", ""),
            Fact("e6.accuracy_kept", mean_acc_s - mean_acc_p, 0.0, "ge", "rate", "anchor",
                 f"plain={mean_acc_p:.3f} steered={mean_acc_s:.3f}"),
            Fact("e6.correct_consistency_kept", mean_con_diff, 0.0, "ge", "cosine", "anchor",
                 f"n={len(both)}/12 both-correct"),
        ]
    )
    print("=" * 72)
    print("E6 accuracy-anchored steering (12 probes, L12 a=2.0)")
    print("=" * 72)
    for r in rows:
        print(f"acc {r['acc_plain']:.2f}->{r['acc_steered']:.2f} con {r['con_plain']}->{r['con_steered']} :: {r['probe'][:36]}")
    print(f"deterministic: {deterministic}, elapsed_min={(time.time()-t_start)/60:.1f}")
    print(report.summary())
    print("=" * 72)
    if args.json:
        args.json.write_text(json.dumps({"rows": rows, "deterministic": deterministic,
                                         "verdict": report.as_dict()},
                                        indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"json -> {args.json}")
    if not deterministic:
        return 1
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
