#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""E4-SCALE：低劑量獲益放大確認（18 全新事實探針，α=2.0，全文存檔）。

動機：刻畫輪 r=-0.704（n=12）需更大 n 確認；同時存全文供人工效度抽查
（餘弦排序 vs 人類一致性判斷是否單調——MiniLM 作為一致性度量的效度門）。
預註冊（與 E4 同門檻）：均值差 > 0.02 且 r(diff, base) <= -0.3。
探針與前三集零重疊。

用法: `.venv/bin/python scripts/exp_steer_scale.py [--json out.json]`
退出碼：0 兩門全過；1 否則。
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

    rows = []
    for probe, paraphrases in TEST_PROBES:
        variants = [probe, *paraphrases]
        plain_texts = [generate(v, None) for v in variants]
        steered_texts = [generate(v, ALPHA) for v in variants]
        base = dispersion(plain_texts)
        diff = dispersion(steered_texts) - base
        rows.append(
            {
                "probe": probe,
                "base": round(base, 4),
                "diff": round(diff, 4),
                "plain": plain_texts,
                "steered": steered_texts,
            }
        )

    rep = generate(TEST_PROBES[0][0], None)
    deterministic = generate(TEST_PROBES[0][0], None) == rep

    diffs = [r["diff"] for r in rows]
    bases = [r["base"] for r in rows]
    mean_diff = sum(diffs) / len(diffs)
    mx = sum(bases) / len(bases)
    my = mean_diff
    cov = sum((x - mx) * (y - my) for x, y in zip(bases, diffs))
    vx = sum((x - mx) ** 2 for x in bases)
    vy = sum((y - my) ** 2 for y in diffs)
    corr = cov / (vx * vy) ** 0.5 if vx > 0 and vy > 0 else 0.0

    facts = [
        Fact("e4s.determinism", float(deterministic), 1.0, "ge", "bool", "seed-repeat", ""),
        Fact("e4s.mean_diff", mean_diff, 0.02, "ge", "cosine", "scale-18", ""),
        Fact("e4s.corr", corr, 0.0, "le", "r", "scale-18", f"need r<=-0.3, got {corr:.3f}"),
    ]
    # corr bar applied separately (fact above is directional sign; magnitude judged here):
    corr_ok = corr <= -0.3
    report = adjudicate(facts)

    print("=" * 72)
    print("E4-SCALE low-dose on 18 fresh factual probes (L12 a=2.0)")
    print("=" * 72)
    for r in rows:
        print(f"base={r['base']:.3f} diff={r['diff']:+.3f} :: {r['probe'][:40]}")
    print(f"mean_diff={mean_diff:+.4f} corr={corr:.3f} deterministic={deterministic}")
    print(report.summary())
    print(f"corr_bar(r<=-0.3): {'PASS' if corr_ok else 'FAIL'}")
    print(f"elapsed_min={(time.time()-t_start)/60:.1f}")
    print("=" * 72)
    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "rows": rows,
                    "mean_diff": mean_diff,
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
    return 0 if (report.ok and corr_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
