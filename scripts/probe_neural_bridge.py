#!/usr/bin/env python3
"""
中間層（神經橋接）量測 — 接觸 / 對齊 / 合成

這支腳本量三件事，三者都必須誠實：

1. **不迴歸**（控制組＝老師詞彙）：老師自己的詞彙題，中間層必須跟老師
   一樣對。
2. **泛化**（留出集）：老師詞彙解不了的改述。留出集只跑一次，開發期間
   沒有看過、也沒有拿來對齊，所以它是誠實的泛化數字。老師在這上面必定
   只有 2/20（它沒有那些詞），中間層靠編碼器「接觸」概念原型得出答案。
3. **對齊**（開發組）：老師（或人類註解）指出某個詞該歸到哪個概念，
   概念原型往該詞挪一步。開發組在開發期被看過，所以它的數字是樂觀的；
   它用來示範「回饋能修正放錯位置的詞」，不是用來證明泛化。

資料集是分開寫死的，不是從留出集長出來的（否則量測就是自我證明）。

用法：
    python scripts/probe_neural_bridge.py            # 印表格
    python scripts/probe_neural_bridge.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))

# --------------------------------------------------------------------------- #
# 1. 控制組：老師詞彙（中間層不得低於老師）
# --------------------------------------------------------------------------- #
TEACHER_VOCABULARY: List[Tuple[str, str]] = [
    ("The first is higher than second, second higher than third, which is top?", "first"),
    ("X is colder than Y, Y colder than Z, who coldest?", "X"),
    ("Tom is younger than Jerry, Jerry younger than Spike, who youngest?", "Tom"),
    ("A is not as short as B, B not as short as C, who shortest?", "C"),
    ("Sam is bigger than Max, Max bigger than Ben, who biggest?", "Sam"),
    ("The cat is older than the dog, the dog older than the mouse, who youngest?", "mouse"),
    ("A car is faster than a bike, a bike faster than a cart, who slowest?", "cart"),
    (
        "The brick is heavier than the stone, the stone heavier than the feather, who lightest?",
        "feather",
    ),
    (
        "The army is stronger than the militia, the militia stronger than the scouts, who weakest?",
        "scouts",
    ),
    (
        "The CEO is richer than the manager, the manager richer than the clerk, who poorest?",
        "clerk",
    ),
    (
        "The oven is hotter than the fridge, the fridge hotter than the freezer, who coldest?",
        "freezer",
    ),
    ("The train is longer than the bus, the bus longer than the car, who shortest?", "car"),
]

# --------------------------------------------------------------------------- #
# 2. 開發組：對齊回饋的對象（開發期看過，數字樂觀，只示範回饋的效果）
# --------------------------------------------------------------------------- #
DEVELOPMENT_SET: List[Tuple[str, str]] = [
    ("The first exceeds second, second exceeds third, which is on top?", "first"),
    ("X is cooler than Y, Y cooler than Z, who is the coolest?", "X"),
    ("Tom is junior to Jerry, Jerry junior to Spike, who is the youngest?", "Tom"),
    ("A outranks B, B outranks C, who ranks lowest?", "C"),
    ("P outranks Q, Q outranks R, who is the top one?", "P"),
]

# --------------------------------------------------------------------------- #
# 3. 留出集：老師詞彙解不了的改述（只跑一次，不參與調參或對齊）
# --------------------------------------------------------------------------- #
HOLDOUT_PARAPHRASE: List[Tuple[str, str]] = [
    ("Alice surpasses Bob, Bob surpasses Carol, who is at the top?", "Alice"),
    (
        "The sedan is bulkier than the van, the van is bulkier than the truck, who is the smallest?",
        "truck",
    ),
    ("Nina is quicker than Otto, Otto quicker than Pia, who is the fastest?", "Nina"),
    ("Dana is more senior than Eli, Eli more senior than Fay, who is the youngest?", "Fay"),
    (
        "The ruby is more valuable than the sapphire, the sapphire more valuable than the pearl, who is worth the least?",
        "pearl",
    ),
    (
        "The oak is sturdier than the pine, the pine sturdier than the birch, who is the weakest?",
        "birch",
    ),
    (
        "Priya is more junior than Quentin, Quentin more junior than Rosa, who is the most senior?",
        "Rosa",
    ),
    (
        "The desert is more sweltering than the valley, the valley more sweltering than the coast, who is the coolest?",
        "coast",
    ),
    ("Sam is weightier than Max, Max weightier than Ben, who is the lightest?", "Ben"),
    (
        "The pyramid is more aged than the tower, the tower more aged than the hut, who is the youngest?",
        "hut",
    ),
    ("若甲比乙高，乙比丙高，誰最高？", "甲"),
    (
        "The gold bar outweighs the silver bar, the silver bar outweighs the copper bar, who is the heaviest?",
        "gold",
    ),
    ("Ivan is below Peter in height, Peter below Sam, who is the tallest?", "Sam"),
    (
        "The blue team is more skilled than the red team, the red team more skilled than the green team, who is the least skilled?",
        "green",
    ),
    (
        "The north team is superior to the south team, the south team superior to the east team, who is at the bottom?",
        "east",
    ),
    ("Gina is more youthful than Hugo, Hugo more youthful than Iris, who is the oldest?", "Iris"),
    (
        "The winter coat is warmer than the spring coat, the spring coat warmer than the summer coat, who is the coldest?",
        "summer",
    ),
    ("A > B, B > C, who is the smallest?", "C"),
    (
        "The kettle is not as compact as the pot, the pot not as compact as the jug, who is the smallest?",
        "jug",
    ),
    (
        "The pipe is thicker than the hose, the hose thicker than the wire, who is the thinnest?",
        "wire",
    ),
]

# --------------------------------------------------------------------------- #
# 4. 對齊回饋集：詞 → 概念（老師詞彙沒有的詞，需要外部指點）
#    這是「根據反饋的資訊來與神經網路對齊」的來源。
#    與留出集不相交（留出集不參與任何回饋）。
# --------------------------------------------------------------------------- #
# (phrase, dimension, direction)；dimension "*" = 只有方向（聚合側）
ALIGNMENT_FEEDBACK: List[Tuple[str, str, str]] = [
    ("outranks", "size", "greater"),
    ("exceeds", "size", "greater"),
    ("cooler", "temperature", "lesser"),
    ("junior", "age", "lesser"),
    ("coldest", "*", "least"),
    ("youngest", "*", "least"),
    ("richest", "*", "greatest"),
    ("poorest", "*", "least"),
    ("weakest", "*", "least"),
]


def _hits(answers: List[Optional[str]], expected: List[str]) -> int:
    hits = 0
    for answer, want in zip(answers, expected):
        if answer and want.lower() in str(answer).lower():
            hits += 1
    return hits


def _misses(
    answers: List[Optional[str]], questions: List[Tuple[str, str]]
) -> List[Tuple[str, str, Optional[str]]]:
    return [
        (q, want, got)
        for (q, want), got in zip(questions, answers)
        if not (got and want.lower() in str(got).lower())
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", dest="json_path", help="write the result as JSON")
    args = parser.parse_args()

    from ai.reasoning.neural_bridge import NeuralBridge
    from ai.symbolic_reasoner import route_reasoning

    started = time.time()

    def teacher_answers(questions: List[Tuple[str, str]]) -> List[Optional[str]]:
        return [route_reasoning(q) for q, _ in questions]

    def bridge_answers(
        bridge: NeuralBridge, questions: List[Tuple[str, str]]
    ) -> List[Optional[str]]:
        return [bridge.answer(q) for q, _ in questions]

    def score(bridge: NeuralBridge, questions: List[Tuple[str, str]]) -> int:
        return _hits(bridge_answers(bridge, questions), [w for _, w in questions])

    bridge = NeuralBridge()

    # -- 1. the control group --------------------------------------------- #
    control_teacher = _hits(teacher_answers(TEACHER_VOCABULARY), [w for _, w in TEACHER_VOCABULARY])
    control_bridge = score(bridge, TEACHER_VOCABULARY)

    # -- 2. the development set (the alignment demo) ---------------------- #
    dev_before = score(bridge, DEVELOPMENT_SET)

    # -- 3. the hold-out (no feedback, no tuning) ------------------------- #
    holdout_teacher = _hits(teacher_answers(HOLDOUT_PARAPHRASE), [w for _, w in HOLDOUT_PARAPHRASE])
    holdout_before = score(bridge, HOLDOUT_PARAPHRASE)

    # -- 4. the alignment (the feedback loop) ----------------------------- #
    aligned = 0
    delta = 0.0
    for phrase, dimension, direction in ALIGNMENT_FEEDBACK:
        concept = direction if dimension == "*" else (dimension, direction)
        stats = bridge.align_phrase(phrase, concept)
        aligned += int(stats["aligned"])
        delta += float(stats["delta"])

    dev_after = score(bridge, DEVELOPMENT_SET)
    holdout_after = score(bridge, HOLDOUT_PARAPHRASE)
    control_after = score(bridge, TEACHER_VOCABULARY)
    holdout_misses = _misses(bridge_answers(bridge, HOLDOUT_PARAPHRASE), HOLDOUT_PARAPHRASE)

    elapsed = time.time() - started
    result = {
        "control": {
            "size": len(TEACHER_VOCABULARY),
            "teacher": control_teacher,
            "bridge": control_bridge,
            "bridge_aligned": control_after,
        },
        "development": {
            "size": len(DEVELOPMENT_SET),
            "bridge_before_align": dev_before,
            "bridge_after_align": dev_after,
        },
        "holdout": {
            "size": len(HOLDOUT_PARAPHRASE),
            "teacher": holdout_teacher,
            "bridge": holdout_before,
            "bridge_aligned": holdout_after,
            "misses": [{"question": q, "expected": w, "got": g} for q, w, g in holdout_misses],
        },
        "alignment": {
            "feedbacks": len(ALIGNMENT_FEEDBACK),
            "aligned": aligned,
            "delta": round(delta, 6),
        },
        "elapsed_sec": round(elapsed, 2),
    }

    print("中間層量測（老師 = 確定性引擎；中間層 = 接觸→對齊→合成）")
    print(
        "  控制組（老師詞彙 {n} 題）: 老師 {t}/{n}｜中間層 {b}/{n}｜對齊後 {ba}/{n}".format(
            n=result["control"]["size"],
            t=control_teacher,
            b=control_bridge,
            ba=control_after,
        )
    )
    print(
        "  開發組（對齊對象 {n} 題）: 對齊前 {b}/{n}｜對齊後 {a}/{n}（開發期看過，數字樂觀）".format(
            n=result["development"]["size"], b=dev_before, a=dev_after
        )
    )
    print(
        "  留出集（老師解不了的改述 {n} 題）: 老師 {t}/{n}｜中間層 {b}/{n}｜對齊後 {ba}/{n}".format(
            n=result["holdout"]["size"],
            t=holdout_teacher,
            b=holdout_before,
            ba=holdout_after,
        )
    )
    print(
        "  對齊: {f} 筆回饋 → 對齊 {a} 筆，總位移 {d:+.4f}".format(
            f=len(ALIGNMENT_FEEDBACK), a=aligned, d=delta
        )
    )
    if holdout_misses:
        print("  留出集未答（誠實的接觸失敗，非迴歸）:")
        for question, want, got in holdout_misses:
            print(f"    - {question[:54]:56} 期望 {want!r} 實得 {got!r}")
    print(f"  耗時 {elapsed:.1f}s")

    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
        print(f"  結果已寫入 {args.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
