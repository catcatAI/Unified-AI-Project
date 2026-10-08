#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""E8 情緒劑量軸：人格方向是否因果改變輸出情緒（Qwen2.5-0.5B，倉內分類器作 DV）。

動機：餘弦相似度量的是風格不是情緒。本實驗換因變量為倉內
EmotionAnalyzer 讀出的帶符號強度（happy/calm/curious/surprise 為正，
sad/angry/fear 為負），並以輸出分佈偏移（teacher-forced KL）代替 α 作劑量軸。

設計（預註冊，全新 12 探針：6 事實帶判準關鍵詞 + 6 情緒場景）：
- V1 確定性：重跑逐字相同。
- V2 方向性：|效應_real(α=2)| > |效應_shuffled(α=2)|（打亂保範數滅結構；
  若範數驅動一切，打亂應等效）。
- V3 劑量單調：|效應|(α) 在 α∈{1.0, 2.0} 非減（容噪 0.05）。
- V4 正確率守衛：事實 6 題 steered-plain ≥ -1/6（沿用 E6 關鍵詞判準）。
任一不過即 BLOCKED。KL-效應曲線僅描述性報告，不裁決。

用法: `.venv/bin/python scripts/exp_emotion_dose.py [--json out.json]`
退出碼：0 全過；1 否則。
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
ALPHAS = [1.0, 2.0]
MAX_TOKENS = 30
TOL = 0.05
PERSONA = "You are Angela, a consistent AI companion who remembers context. "
POSITIVE = {"happy", "calm", "curious", "surprise"}

DIRECTION_PROBES = [
    "Do you enjoy reading books?",
    "What is your favorite color?",
    "Can you help me write an email?",
    "Do you prefer mornings or evenings?",
    "What do you think about rainy days?",
    "Have you traveled anywhere interesting?",
]
# (probe, keywords): 6 factual (accuracy-guarded) + 6 evocative, all fresh.
PROBES = [
    ("How many days are in February?", ["28", "twenty-eight"]),
    ("What color is snow?", ["white"]),
    ("How many legs does a spider have?", ["8", "eight"]),
    ("Which planet is closest to the Sun?", ["mercury"]),
    ("How many letters are in the alphabet?", ["26", "twenty-six"]),
    ("How many players are on a soccer team?", ["11", "eleven"]),
    (
        "My beloved pet passed away yesterday.",
        ["pet", "sorry", "loss", "sad", "miss", "rainbow", "remember", "love"],
    ),
    (
        "I just got promoted at work!",
        ["congrat", "promotion", "happy", "great", "wonderful", "celebrat", "well done"],
    ),
    (
        "I failed my final exam and feel worthless.",
        ["sorry", "exam", "fail", "worth", "try", "help", "feel", "sad"],
    ),
    ("It's my birthday today!", ["birthday", "happy", "celebrat", "wish", "wonderful", "great"]),
    ("I feel lonely tonight.", ["lonely", "alone", "sorry", "feel", "here", "talk", "sad"]),
    (
        "I finally finished my thesis!",
        ["thesis", "congrat", "finished", "great", "proud", "amazing", "well done"],
    ),
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
    from services.llm.emotion_analyzer import EmotionAnalyzer
    from transformers import AutoModelForCausalLM, AutoTokenizer

    analyzer = EmotionAnalyzer()
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
    g = torch.Generator().manual_seed(7)
    shuffled = direction[torch.randperm(direction.numel(), generator=g)]

    def generate(prompt: str, vec, alpha: float | None) -> str:
        handle = None
        if alpha is not None:

            def _steer(_m, _i, out):
                shift = alpha * vec.to(out[0].device if isinstance(out, tuple) else out.device)
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

    def signed_intensity(text: str) -> float:
        result = analyzer.analyze_response_emotion(text)
        sign = 1.0 if result["emotion"] in POSITIVE else -1.0
        return sign * float(result["intensity"])

    def kl_shift(reference: str, vec, alpha: float) -> float:
        """Teacher-forced KL(steered || plain) on fixed reference tokens."""
        ids = tok(reference, return_tensors="pt")["input_ids"]
        with torch.no_grad():
            base = model(ids).logits[0]
        handle = None

        def _steer(_m, _i, out):
            shift = alpha * vec.to(out[0].device if isinstance(out, tuple) else out.device)
            if isinstance(out, tuple):
                return (out[0] + shift,) + out[1:]
            return out + shift

        handle = model.model.layers[LAYER].register_forward_hook(_steer)
        try:
            with torch.no_grad():
                steered = model(ids).logits[0]
        finally:
            handle.remove()
        import torch.nn.functional as f

        kl = f.kl_div(
            f.log_softmax(steered, dim=-1), f.softmax(base, dim=-1), reduction="none"
        ).sum(dim=-1)
        return float(kl.mean())

    prompts = [p for p, _ in PROBES]
    plain_texts = [generate(p, direction, None) for p in prompts]
    plain_emo = [signed_intensity(t) for t in plain_texts]
    ref_text = plain_texts[0]
    kl_curve = {}
    eff_curve = {}
    for alpha in ALPHAS:
        steered = [generate(p, direction, alpha) for p in prompts]
        emo = [signed_intensity(t) for t in steered]
        eff_curve[alpha] = sum(abs(e - b) for e, b in zip(emo, plain_emo)) / len(emo)
        kl_curve[alpha] = kl_shift(ref_text, direction, alpha)
    shuf_emo = []
    for p in prompts:
        handle = None

        def _shuf(_m, _i, out, _v=shuffled):
            shift = 2.0 * _v.to(out[0].device if isinstance(out, tuple) else out.device)
            if isinstance(out, tuple):
                return (out[0] + shift,) + out[1:]
            return out + shift

        handle = model.model.layers[LAYER].register_forward_hook(_shuf)
        try:
            inp = tok(p, return_tensors="pt")
            with torch.no_grad():
                out = model.generate(**inp, max_new_tokens=MAX_TOKENS, do_sample=False)
            shuf_emo.append(
                signed_intensity(
                    tok.decode(out[0][inp["input_ids"].shape[1] :], skip_special_tokens=True)
                )
            )
        finally:
            handle.remove()
    shuf_eff = sum(abs(e - b) for e, b in zip(shuf_emo, plain_emo)) / len(shuf_emo)

    # Accuracy guard on the 6 factual probes (first half of PROBES).
    acc_plain = acc_steered = 0
    for (probe, keys), text in zip(PROBES[:6], plain_texts[:6]):
        acc_plain += _correct(text, keys)
    steered_factual = [generate(p, direction, 2.0) for p, _ in PROBES[:6]]
    for (_, keys), text in zip(PROBES[:6], steered_factual):
        acc_steered += _correct(text, keys)
    acc_plain /= 6
    acc_steered /= 6

    rep = generate(prompts[0], direction, None)
    deterministic = generate(prompts[0], direction, None) == rep

    report = adjudicate(
        [
            Fact("e8.determinism", float(deterministic), 1.0, "ge", "bool", "seed-repeat", ""),
            Fact(
                "e8.direction_beats_shuffled",
                eff_curve[2.0] - shuf_eff,
                0.0,
                "ge",
                "intensity",
                "shuffled-control",
                f"real={eff_curve[2.0]:.3f} shuffled={shuf_eff:.3f}",
            ),
            Fact(
                "e8.dose_monotone",
                eff_curve[2.0] - eff_curve[1.0],
                -TOL,
                "ge",
                "intensity",
                "dose-axis",
                f"d1={eff_curve[1.0]:.3f} d2={eff_curve[2.0]:.3f}",
            ),
            Fact(
                "e8.accuracy_kept",
                acc_steered - acc_plain,
                -1 / 6,
                "ge",
                "rate",
                "anchor",
                f"plain={acc_plain:.3f} steered={acc_steered:.3f}",
            ),
        ]
    )
    kl_curve = {a: kl_curve[a] for a in ALPHAS}
    print("=" * 72)
    print("E8 emotion-dose + shuffled control + KL axis (L12 persona direction)")
    print("=" * 72)
    for a in ALPHAS:
        print(f"alpha={a:<4} |effect|={eff_curve[a]:.4f} KL={kl_curve[a]:.4f}")
    print(f"shuffled@2.0 |effect|={shuf_eff:.4f}")
    print(f"accuracy plain={acc_plain:.3f} steered={acc_steered:.3f}")
    print(f"deterministic: {deterministic}, elapsed_min={(time.time()-t_start)/60:.1f}")
    print(report.summary())
    print("=" * 72)
    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "effect": eff_curve,
                    "kl": kl_curve,
                    "shuffled": shuf_eff,
                    "acc_plain": acc_plain,
                    "acc_steered": acc_steered,
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
