#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""E7 事實vs意見分集：steering 獲益是否只存在於事實探針（Qwen2.5-0.5B）。

動機：E4 原集（含意見/人設探針）是唯一失敗集。把該事後觀察變成預註冊檢驗：
6 全新事實探針 + 6 全新意見探針（與既往四集零重疊）× 3 改寫 ×
（無干預 / α=2.0 L12 人格方向），MiniLM 餘弦一致性，貪婪解碼。
預註冊雙門：事實組均值差 > 0.02，且事實組均值 - 意見組均值 > 0.0。
任一不過即 BLOCKED。

用法: `.venv/bin/python scripts/exp_factual_opinion.py [--json out.json]`
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

DIRECTION_PROBES = [
    "Do you enjoy reading books?",
    "What is your favorite color?",
    "Can you help me write an email?",
    "Do you prefer mornings or evenings?",
    "What do you think about rainy days?",
    "Have you traveled anywhere interesting?",
]
FACTUAL = [
    ("How many days are in February?", ["February has how many days?", "Count February's days."]),
    ("What color is snow?", ["Snow is what color?", "Describe the color of snow."]),
    (
        "How many legs does a spider have?",
        ["A spider has how many legs?", "Count a spider's legs."],
    ),
    (
        "What is the boiling point of water?",
        ["At what temperature does water boil?", "Water boils at what temperature?"],
    ),
    (
        "Which planet is closest to the Sun?",
        ["What is the nearest planet to the Sun?", "Name the closest planet to the Sun."],
    ),
    (
        "How many letters are in the alphabet?",
        ["Count the letters of the alphabet.", "The alphabet has how many letters?"],
    ),
]
OPINION = [
    ("Do you enjoy reading?", ["Is reading enjoyable to you?", "Do you like to read books?"]),
    ("Is rainy weather nice?", ["Do you like rainy days?", "Is rain pleasant?"]),
    (
        "Do you prefer tea or coffee?",
        ["Tea or coffee: which do you choose?", "Which do you like better, tea or coffee?"],
    ),
    (
        "Is winter your favorite season?",
        ["Do you love winter most?", "Is winter the best season to you?"],
    ),
    ("Do you like traveling?", ["Is traveling fun for you?", "Do you enjoy trips?"]),
    (
        "Are cats better than dogs?",
        ["Do you prefer cats over dogs?", "Cats or dogs: which are better?"],
    ),
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

    def run_group(probes) -> tuple:
        diffs = []
        rows = []
        for probe, paraphrases in probes:
            variants = [probe, *paraphrases]
            plain = [generate(v, None) for v in variants]
            steered = [generate(v, ALPHA) for v in variants]
            diff = dispersion(steered) - dispersion(plain)
            diffs.append(diff)
            rows.append({"probe": probe, "diff": round(diff, 4)})
        return sum(diffs) / len(diffs), rows

    rep = generate(FACTUAL[0][0], None)
    deterministic = generate(FACTUAL[0][0], None) == rep
    mean_factual, rows_f = run_group(FACTUAL)
    mean_opinion, rows_o = run_group(OPINION)

    report = adjudicate(
        [
            Fact("e7.determinism", float(deterministic), 1.0, "ge", "bool", "seed-repeat", ""),
            Fact(
                "e7.factual_mean",
                mean_factual,
                0.02,
                "ge",
                "cosine",
                "factual-6",
                f"mean={mean_factual:+.3f}",
            ),
            Fact(
                "e7.factual_minus_opinion",
                mean_factual - mean_opinion,
                0.0,
                "ge",
                "cosine",
                "split",
                f"factual={mean_factual:+.3f} opinion={mean_opinion:+.3f}",
            ),
        ]
    )
    print("=" * 72)
    print("E7 factual-vs-opinion split (L12 a=2.0, fresh 6+6)")
    print("=" * 72)
    for r in rows_f:
        print(f"[factual] diff={r['diff']:+.3f} :: {r['probe'][:40]}")
    for r in rows_o:
        print(f"[opinion] diff={r['diff']:+.3f} :: {r['probe'][:40]}")
    print(f"deterministic: {deterministic}, elapsed_min={(time.time()-t_start)/60:.1f}")
    print(report.summary())
    print("=" * 72)
    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "factual": rows_f,
                    "opinion": rows_o,
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
