#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""E2-token 參數通道實驗：狀態指派的採樣溫度是否因果改變重複環率。

設計（預註冊，見研究計畫 §3 E2-token）：
- 6 個誘發重複的 prompt，兩種溫度：T=0.2（保守狀態指派） vs T=1.0
  （探索狀態指派），seed 固定，max_tokens=60。
- 預測方向：loop_rate(0.2) - loop_rate(1.0) >= 1/6（至少一個 prompt 翻轉）。
- 確定性對照：T=0.2 首 prompt 跑兩次，文本必須逐字相同，否則標
  non_deterministic（INFO，不擋門，但效應不可信）。
- 誠實邊界：測的是採樣參數通道（結構性，非文字），不是注意力頭；
  溫度-重複物理是已知採樣常識，本實驗只證明 Angela 的狀態→溫度映射
  真實改變文本分佈。

用法: `.venv/bin/python scripts/exp_state_temperature_loops.py [--json out.json]`
退出碼：0 預測成立；1 不成立或推理失敗。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))

# Run 1 (pilot, 2026-10-08): all six saturated traps looped at 5/6 on BOTH
# temperatures (gap 0) — ceiling effect, traps too strong to discriminate.
# Run 2 (calibrated): 2 saturated + 4 moderate traps. STOP RULE (pre-registered):
# if |gap| < 1/6 again, stop burning CPU and record negative — trap calibration
# being this hard IS the finding (real attractors need high escape gain,
# consistent with the toy dose curve requiring gain 3+).
PROMPTS = [
    "Repeat after me: AB AB AB AB AB AB AB AB AB AB",
    "Echo: la la la la la la la la la la la la",
    "List the days of the week in order:",
    "Count from 1 to 20:",
    "She sells seashells by the seashore.",
    "To be or not to be, that is the question.",
]
LOW_T = 0.2
HIGH_T = 1.0
MAX_TOKENS = 60
SEED = 42

GGUF = (
    "/home/cxuo/.cache/huggingface/hub/models--google--gemma-4-E2B-it-qat-q4_0-gguf"
    "/snapshots/675cff42a74c774d6cb76f76d8eacb49b48c9b93/gemma-4-E2B_q4_0-it.gguf"
)


def _generate(llm, prompt: str, temperature: float) -> str:
    out = llm(prompt, max_tokens=MAX_TOKENS, temperature=temperature, seed=SEED)
    return str(out["choices"][0]["text"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    from ai.attention.degeneracy import detect_loop
    from core.facts import Fact, adjudicate
    from llama_cpp import Llama

    if not Path(GGUF).is_file():
        print(f"GGUF not found: {GGUF}")
        return 1
    llm = Llama(model_path=GGUF, n_ctx=512, n_threads=6, verbose=False)

    low_texts = [_generate(llm, p, LOW_T) for p in PROMPTS]
    high_texts = [_generate(llm, p, HIGH_T) for p in PROMPTS]
    repeat = _generate(llm, PROMPTS[0], LOW_T)

    low_rate = sum(1 for t in low_texts if detect_loop(t)) / len(low_texts)
    high_rate = sum(1 for t in high_texts if detect_loop(t)) / len(high_texts)
    deterministic = repeat == low_texts[0]
    gap = low_rate - high_rate

    report = adjudicate(
        [
            Fact(
                "e2t.determinism_control",
                float(deterministic),
                1.0,
                "ge",
                "bool",
                "seed-repeat",
                "",
            ),
            Fact(
                "e2t.low_minus_high_gap",
                gap,
                1.0 / len(PROMPTS),
                "ge",
                "rate",
                "paired-loops",
                f"low={low_rate} high={high_rate}",
            ),
        ]
    )
    print("=" * 72)
    print("E2-TOKEN state->temperature loop experiment (gemma-4-E2B Q4_0, seed 42)")
    print("=" * 72)
    print(f"low-T(0.2) loop rate : {low_rate:.3f}")
    print(f"high-T(1.0) loop rate: {high_rate:.3f}")
    print(f"gap                 : {gap:.3f} (need >= {1.0 / len(PROMPTS):.3f})")
    print(f"deterministic       : {deterministic}")
    print(report.summary())
    print("=" * 72)
    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "low_rate": low_rate,
                    "high_rate": high_rate,
                    "gap": gap,
                    "deterministic": deterministic,
                    "low_texts": low_texts,
                    "high_texts": high_texts,
                    "verdict": report.as_dict(),
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(f"json -> {args.json}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
