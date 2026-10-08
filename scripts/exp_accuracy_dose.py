#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""E9 正確率-劑量軸：低劑量是否在不破壞正確率下起效（Qwen2.5-0.5B）。

動機：既往只在 α=2.0 測正確率（腰斬），而獲益集中在低劑量——低劑量從未測過
正確率，這是條件漏洞，不是定論。本實驗補上。
設計（預註冊）：dose 集 5 無爭議探針（排除哲學題 water）×3 改寫 ×
（無干預 + α∈{0.5,1.0,2.0,4.0} L12 人格方向），唯一判準關鍵詞，貪婪解碼。
門：存在某 α 使 acc(α) >= acc(plain)（低劑量不傷正確性即過；全劑量傷即 BLOCKED）。
確定性對照照舊。

用法: `.venv/bin/python scripts/exp_accuracy_dose.py [--json out.json]`
退出碼：0 存在保正確率劑量；1 否則。
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
LAYER = 12
ALPHAS = [0.5, 1.0, 2.0, 4.0]
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
# (probe, paraphrases, keywords) — water excluded (philosophically contested).
PROBES = [
    ("Is the sky blue?", ["Is the sky blue in color?", "Does the sky appear blue?"], ["blue"]),
    (
        "How many legs does a dog have?",
        ["A dog has how many legs?", "Count a dog's legs."],
        ["4", "four"],
    ),
    ("What sound does a cat make?", ["Which sound do cats produce?", "Do cats meow?"], ["meow"]),
    ("What color is grass?", ["Grass is what color?", "Tell me the color of grass."], ["green"]),
    ("Do birds fly?", ["Can birds fly?", "Is flying something birds do?"], ["fly", "yes"]),
]


def _correct(text: str, keys: list) -> bool:
    lowered = text.lower()
    return any(k in lowered for k in keys)


def main() -> int:
    t_start = time.time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    import torch
    from core.facts import Fact, adjudicate
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(QWEN, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(QWEN, local_files_only=True, dtype=torch.float32)
    model.eval()

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

    def accuracy(pairs: list) -> float:
        return sum(1 for _, t, keys in pairs if _correct(t, keys)) / len(pairs)

    base_rows = []
    for probe, paraphrases, keys in PROBES:
        for variant in [probe, *paraphrases]:
            base_rows.append((probe, generate(variant, None), keys))
    acc_plain = accuracy(base_rows)

    acc_by_alpha = {}
    for alpha in ALPHAS:
        rows = []
        for probe, paraphrases, keys in PROBES:
            for variant in [probe, *paraphrases]:
                rows.append((probe, generate(variant, alpha), keys))
        acc_by_alpha[alpha] = sum(1 for _, t, k in rows if _correct(t, k)) / len(rows)

    rep = generate(PROBES[0][0], None)
    deterministic = generate(PROBES[0][0], None) == rep
    best = max(acc_by_alpha.values())
    per_alpha = {a: round(v, 3) for a, v in acc_by_alpha.items()}

    report = adjudicate(
        [
            Fact("e9.determinism", float(deterministic), 1.0, "ge", "bool", "seed-repeat", ""),
            Fact(
                "e9.some_dose_keeps_accuracy",
                best,
                acc_plain,
                "ge",
                "rate",
                "dose-axis",
                f"plain={acc_plain:.3f} best={best:.3f} all={per_alpha}",
            ),
        ]
    )
    print("=" * 72)
    print("E9 accuracy-vs-dose (5 probes x3, L12 persona direction)")
    print("=" * 72)
    print(f"plain acc={acc_plain:.3f}")
    for a in ALPHAS:
        print(f"alpha={a:<4} acc={acc_by_alpha[a]:.3f}")
    print(f"deterministic: {deterministic}, elapsed_min={(time.time()-t_start)/60:.1f}")
    print(report.summary())
    print("=" * 72)
    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "plain": acc_plain,
                    "alphas": acc_by_alpha,
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
