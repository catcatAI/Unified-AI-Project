#!/usr/bin/env python3
"""智能定義的門禁 — 一個定義，一個數字，一個地方。

專案原本有十一套自稱 intelligence 的評分系統（能力階梯、INTELLIGENCE_ASSESSMENT
的 ×10 公式、AI_SUBSTRATE 的 4.3/10、人話 rubric、neural_share、成熟度階級、
美術品質階梯……）。同一個詞在不同檔案裡指不同的量尺，於是「智能幾分」永遠
可以挑一個對自己有利的數字。

本門禁守著 `apps/backend/src/ai/meta/intelligence.py` 這份統一定義：

1. `intelligence.definition_wellformed` — 每個能力維度都有可執行的量測指令
   （腳本存在）、分數型別屬於六型、權重為正；且至少一個維度是「驗證／實際」
   分（架構分與框架分不算能力）。
2. `intelligence.ladders_namespaced` — 五個階梯各有命名空間，不再共用 L0；
   智能階梯只有一個。
3. `intelligence.report_consistent` — 報告（`data/intelligence_reports/unified.json`）
   若宣稱「已量測」，分數必須落在 0–10、階梯必須與 `band_for()` 一致；若
   「未定義」，必須寫出原因（量測無效時不可以給數字）。
4. `intelligence.docs_cite_definition` — 權威文件
   （`docs/06-project-management/INTELLIGENCE_ASSESSMENT.md`）必須引用統一定義
   模組，並且明講「只有一個智能總分」。

用法：`python scripts/check_intelligence_definition.py [--json out.json]`
退出碼：0 全綠；1 有違規。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Dict, List

REPO = Path(__file__).resolve().parents[1]
DEFINITION = REPO / "apps" / "backend" / "src" / "ai" / "meta" / "intelligence.py"
REPORT = REPO / "docs" / "06-project-management" / "intelligence_report.json"
CANONICAL_DOC = REPO / "docs" / "06-project-management" / "INTELLIGENCE_ASSESSMENT.md"

EXPECTED_NAMESPACES = {"L0..L3", "Q0..Q4", "X0..X11", "R1..R3", "claimed..production"}


def _load_definition():
    spec = importlib.util.spec_from_file_location("intelligence_definition", DEFINITION)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["intelligence_definition"] = module
    spec.loader.exec_module(module)
    return module


def _command_script(command: str) -> str:
    """The script path of a `python <script> ...` measurement command."""
    parts = command.split()
    for index, part in enumerate(parts):
        if Path(part).suffix == ".py" and index > 0 and "python" in parts[index - 1]:
            return part
    return ""


def check() -> List[str]:
    problems: List[str] = []
    if not DEFINITION.is_file():
        return [f"the unified definition is missing: {DEFINITION.relative_to(REPO)}"]

    try:
        definition = _load_definition()
    except Exception as exc:  # noqa: BLE001 - any import failure is a violation
        return [f"the unified definition cannot be imported: {exc}"]

    # 1. The dimensions.
    counted = 0
    for dimension in definition.DIMENSIONS:
        if dimension.score_type not in definition.SCORE_TYPES:
            problems.append(f"{dimension.id}: unknown score type {dimension.score_type!r}")
        if dimension.score_type in definition.COUNTED_SCORE_TYPES:
            counted += 1
        if dimension.weight <= 0:
            problems.append(f"{dimension.id}: weight must be positive")
        script = _command_script(dimension.command)
        if not script:
            problems.append(f"{dimension.id}: the command has no script path")
        elif not (REPO / script).is_file():
            problems.append(f"{dimension.id}: the measurement script is missing: {script}")
    if counted == 0:
        problems.append("no dimension carries a verified/actual score (only readiness scores)")

    # 2. The ladders.
    namespaces = set(definition.LADDER_NAMESPACES)
    if namespaces != EXPECTED_NAMESPACES:
        problems.append(
            "the ladder namespaces changed: "
            f"missing={sorted(EXPECTED_NAMESPACES - namespaces)} "
            f"extra={sorted(namespaces - EXPECTED_NAMESPACES)}"
        )
    meanings = list(definition.LADDER_NAMESPACES.values())
    if len(meanings) != len(set(meanings)):
        problems.append("two ladders share the same meaning (a namespace is duplicated)")
    intelligence_ladders = [
        name for name, text in definition.LADDER_NAMESPACES.items() if "智能" in text
    ]
    if intelligence_ladders != ["L0..L3"]:
        problems.append(
            f"there must be exactly one intelligence ladder (L0..L3); found {intelligence_ladders}"
        )
    if len(definition.LADDER_BANDS) < 2:
        problems.append("the intelligence ladder must have at least two bands")
    for low, high, name, summary in definition.LADDER_BANDS:
        if not name or not summary:
            problems.append(f"ladder band {low}-{high} is incomplete")
        if not (0 <= low < 10 and 0 < high <= 10 and low < high):
            problems.append(f"ladder band {low}-{high} is out of range")

    # 3. The report.
    if not REPORT.is_file():
        problems.append(
            f"the unified report is missing ({REPORT.relative_to(REPO)}); "
            "run: python scripts/report_intelligence.py --json " + str(REPORT.relative_to(REPO))
        )
    else:
        try:
            report = json.loads(REPORT.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - an unreadable report is a violation
            report = None
            problems.append(f"the unified report is unreadable: {exc}")
        if report is not None:
            result = report.get("result") or {}
            status = result.get("status")
            score = result.get("score")
            if status == "measured":
                if not isinstance(score, (int, float)) or not (0 <= score <= 10):
                    problems.append(f"the measured score is out of range: {score!r}")
                else:
                    expected_band, _summary = definition.band_for(float(score))
                    if result.get("band") != expected_band:
                        problems.append(
                            f"the report's band {result.get('band')!r} does not match "
                            f"band_for({score}) = {expected_band!r}"
                        )
                    scores = report.get("scores") or {}
                    expected_level, _missing = definition.attained_level(scores)
                    if result.get("attained_level") != expected_level:
                        problems.append(
                            f"the report's attained level {result.get('attained_level')!r} "
                            f"does not match attained_level(scores) = {expected_level!r} "
                            "(the average band and the attained level are different things)"
                        )
            elif status == "undefined":
                if score is not None:
                    problems.append("an undefined measurement must not report a score")
                if not (result.get("reason") or "").strip():
                    problems.append("an undefined measurement must state the reason")
            else:
                problems.append(f"unknown report status: {status!r}")

    # 4. The canonical document.
    if not CANONICAL_DOC.is_file():
        problems.append(f"the canonical document is missing: {CANONICAL_DOC.relative_to(REPO)}")
    else:
        text = CANONICAL_DOC.read_text(encoding="utf-8")
        if "ai/meta/intelligence.py" not in text and "ai.meta.intelligence" not in text:
            problems.append(
                "the canonical document does not cite the unified definition "
                "(ai/meta/intelligence.py)"
            )
        if not re.search(r"(只有一個智能總分|唯一的智能總分|the single intelligence score)", text):
            problems.append(
                "the canonical document does not state that there is exactly one "
                "intelligence score"
            )
        if "統一定義" not in text:
            problems.append("the canonical document has no 統一定義 section")

    return problems


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args(argv)

    problems = check()
    print("=" * 72)
    print("INTELLIGENCE DEFINITION GATE")
    print("=" * 72)
    if problems:
        print(f"violations={len(problems)}")
        for problem in problems:
            print(f"  ✗ {problem}")
    else:
        print("violations=0 — one definition, one number, one place")
    print("=" * 72)
    if args.json:
        args.json.write_text(
            json.dumps({"violations": problems}, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
