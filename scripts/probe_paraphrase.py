#!/usr/bin/env python3
"""改述泛化量測 — 中間層（接觸→對齊→合成）在凍結基準上的表現。

三個切分，各自誠實：

1. ``heldout_dimensions``（開發集）— 課程教過的關係詞，用在課程沒教過的維度。
   修 parser 時看過這些題目，所以數字偏樂觀。
2. ``unseen_surfaces``（嚴格診斷）— 課程完全沒教過的關係詞，只能靠編碼器
   「接觸」概念原型。這一格低是誠實的失敗，不是迴歸。
3. ``test``（凍結確認集）— 不同種子、不同實體、不同問句說法，最後跑一次。

每一格都比四條路徑：確定性老師、未教的中間層、教過的中間層、生產路徑
（老師先答，老師不會才交給教過的中間層——與
``ai.arithmetic.deterministic_router.try_neural_bridge`` 相同順序）。

用法：
    python scripts/probe_paraphrase.py
    python scripts/probe_paraphrase.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

BENCHMARK = REPO_ROOT / "benchmarks" / "data" / "paraphrase_v1.json"
CURRICULUM = (
    REPO_ROOT
    / "apps"
    / "backend"
    / "configs"
    / "standard"
    / "reasoning"
    / "paraphrase_curriculum.yaml"
)

_ARTICLES = re.compile(r"^(the|a|an)\s+", re.IGNORECASE)


def _normalise(text: Optional[str]) -> str:
    """Lower-case, article-free (the bridge answers "pine" for "the pine")."""
    value = (text or "").strip().lower()
    return _ARTICLES.sub("", value)


def _hit(answer: Optional[str], expected: str) -> bool:
    return bool(answer) and _normalise(expected) in _normalise(answer)


def _rate(hits: int, total: int) -> float:
    return round(hits / total, 4) if total else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", dest="json_path", help="write the result as JSON")
    args = parser.parse_args()

    from ai.reasoning.neural_bridge import NeuralBridge
    from ai.reasoning.paraphrase_curriculum import (
        apply_curriculum,
        load_curriculum,
    )
    from ai.symbolic_reasoner import route_reasoning

    started = time.time()
    if not BENCHMARK.is_file():
        print(f"missing benchmark: {BENCHMARK}")
        return 1
    payload = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    splits: Dict[str, List[dict]] = payload.get("splits") or {}

    # The integrity check: teaching must not contain an evaluation sentence.
    curriculum_text = CURRICULUM.read_text(encoding="utf-8") if CURRICULUM.is_file() else ""
    problems: List[str] = []
    for name, items in splits.items():
        for item in items:
            if item["q"] in curriculum_text:
                problems.append(f"{name}: the curriculum contains an eval sentence: {item['q']}")

    entries = load_curriculum()
    raw = NeuralBridge()
    taught = NeuralBridge()
    aligned = apply_curriculum(taught)

    # The stronger integrity check: the splits that are supposed to be
    # *untaught* must not have any of their relation words in the curriculum,
    # otherwise "generalisation" would be vocabulary recall.
    for name in ("unseen_surfaces", "heldout_final"):
        for item in splits.get(name) or []:
            surface = (item.get("surface") or "").replace("{A} ", "").replace(" {B}", "")
            if surface and surface in curriculum_text:
                problems.append(f"{name}: the curriculum contains a held-out word: {surface}")

    results: Dict[str, dict] = {}
    for name, items in splits.items():
        rows = []
        for item in items:
            teacher = route_reasoning(item["q"])
            raw_answer = raw.answer(item["q"])
            taught_answer = taught.answer(item["q"])
            # The production order: the teacher first, the middle layer fills
            # in what the teacher cannot see.
            system = teacher if _hit(teacher, item["expected"]) else taught_answer
            rows.append(
                {
                    "id": item["id"],
                    "q": item["q"],
                    "expected": item["expected"],
                    "dimension": item.get("dimension"),
                    "teacher": teacher,
                    "raw": raw_answer,
                    "taught": taught_answer,
                }
            )
            rows[-1]["system"] = system
        total = len(rows)
        teacher_hits = sum(1 for row in rows if _hit(row["teacher"], row["expected"]))
        raw_hits = sum(1 for row in rows if _hit(row["raw"], row["expected"]))
        taught_hits = sum(1 for row in rows if _hit(row["taught"], row["expected"]))
        system_hits = sum(1 for row in rows if _hit(row["system"], row["expected"]))
        misses = [
            {
                "q": row["q"],
                "expected": row["expected"],
                "teacher": row["teacher"],
                "taught": row["taught"],
            }
            for row in rows
            if not _hit(row["system"], row["expected"])
        ]
        results[name] = {
            "size": total,
            "teacher": _rate(teacher_hits, total),
            "raw": _rate(raw_hits, total),
            "taught": _rate(taught_hits, total),
            "system": _rate(system_hits, total),
            "system_hits": system_hits,
            "misses": misses,
        }

    # The dimension is **generalisation to never-taught phrasing**, not
    # recall of taught vocabulary: the applied split (taught words, frozen
    # sentences) is reported next to it, but it is not the score. Teaching a
    # word and then testing that same word is vocabulary recall.
    scored_split = "heldout_final" if "heldout_final" in results else "unseen_surfaces"
    score = (results.get(scored_split) or {}).get("system", 0.0)
    application = (results.get("test") or {}).get("system", 0.0)
    learning_effect = round(
        (results.get("heldout_dimensions") or {}).get("taught", 0.0)
        - (results.get("heldout_dimensions") or {}).get("raw", 0.0),
        4,
    )
    result = {
        "benchmark": payload.get("name"),
        "curriculum": {
            "path": str(CURRICULUM.relative_to(REPO_ROOT)),
            "entries": len(entries),
            "aligned": aligned,
        },
        "splits": results,
        "score": score,
        "score_split": scored_split,
        "application": application,
        "application_split": "test",
        "learning_effect": learning_effect,
        "integrity": {"no_leak": not problems, "problems": problems},
        "elapsed_sec": round(time.time() - started, 2),
    }

    print("改述泛化量測（老師 = 確定性引擎；中間層 = 接觸→對齊→合成）")
    print(
        "  課程：{entries} 句（{path}）→ 對齊 {aligned} 筆".format(
            entries=len(entries),
            path=CURRICULUM.relative_to(REPO_ROOT),
            aligned=aligned,
        )
    )
    labels = {
        "heldout_dimensions": "開發集（教過的詞 × 沒教過的維度）",
        "unseen_surfaces": "開發診斷（沒教過的詞，用來挑同義詞）",
        "test": "套用確認集（教過的詞、新句子）",
        "heldout_final": "最終留出（從未教過、沒調參）",
    }
    for name in ("heldout_dimensions", "unseen_surfaces", "test", "heldout_final"):
        entry = results.get(name)
        if not entry:
            continue
        print(
            "  {label} {size} 題：老師 {t:.0%}｜未教 {r:.0%}｜教過 {ta:.0%}｜"
            "生產 {s:.0%}（{hits}/{size}）".format(
                label=labels.get(name, name),
                size=entry["size"],
                t=entry["teacher"],
                r=entry["raw"],
                ta=entry["taught"],
                s=entry["system"],
                hits=entry["system_hits"],
            )
        )
        for miss in entry["misses"][:6]:
            print(
                f"    - 未達：{miss['q'][:72]:74} 期望 {miss['expected']!r} 得 {miss['teacher']!r}/{miss['taught']!r}"
            )
    print(f"  學習效應（開發集 教過 − 未教）：{learning_effect:+.0%}")
    print(f"  改述泛化分數（{labels.get(scored_split, scored_split)}）：{score:.0%}")
    print(
        f"  套用分數（教過的詞、新句子）：{application:.0%}"
        "（是詞彙回想＋組合，不是泛化，所以不當分數）"
    )
    if problems:
        print("  ⚠️ 完整性問題：")
        for problem in problems:
            print(f"    - {problem}")
    else:
        print("  完整性：課程與評測句子不相交 ✅")
    print(f"  耗時 {result['elapsed_sec']}s")

    if args.json_path:
        output = Path(args.json_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  結果已寫入 {args.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
