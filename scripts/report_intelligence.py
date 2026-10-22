#!/usr/bin/env python3
"""智能報告 — 單一數字，取代散落各處的三個互斥分數。

原本專案裡有三個互不相干的「智能總分」：6.0/10（FRAMEWORK_OVERVIEW／
MASTER_TASK_MAP）、4.3/10（AI_SUBSTRATE_ASSESSMENT）、3.0/10（開放域泛化）。
它們量的是不同的東西卻都用「智能」這個詞，於是沒有一個數字能被引用。

本腳本用**統一定義**（`apps/backend/src/ai/meta/intelligence.py`）從既有量測
算出**一個**數字，並把量測的誠實度當成門：

- **能力**（六維度 ×10，標註六型分數型別；只有驗證／實際計入）
- **來源**（回答由神經／模板／確定性／檢索各佔多少 → 智能 vs 複製模板）
- **誠實度**（樣本有效性／少量-標準量一致性／非空轉）→ 不過就是「未定義」

用法：
    python scripts/report_intelligence.py                 # 跑量測並印報告
    python scripts/report_intelligence.py --from-cache   # 用既有報告（不重跑）
    python scripts/report_intelligence.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

REPORT_DIR = REPO_ROOT / "data" / "intelligence_reports"
#: The committed artifact (the docs cite this file; data/ is git-ignored).
ARTIFACT = REPO_ROOT / "docs" / "06-project-management" / "intelligence_report.json"
BUDGET_FILE = REPO_ROOT / "scripts" / "native_dialogue_budget.txt"


def _budget_value(key: str, default: str) -> str:
    """Read a value from the committed budget file (the measurement's limits)."""
    if not BUDGET_FILE.is_file():
        return default
    for line in BUDGET_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        if name.strip() == key:
            return value.strip()
    return default


def _run(command: List[str], label: str, out_flag: str = "--json") -> Optional[Path]:
    """Run a measurement script and return the report path it wrote."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORT_DIR / f"{label}.json"
    print(f"  · {label}：{' '.join(command)}")
    result = subprocess.run(
        [*command, out_flag, str(out)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not out.exists():
        print(f"    ⚠️ 量測失敗（exit {result.returncode}）；該維度記為未量")
        print("    " + (result.stdout or "")[-400:].replace("\n", "\n    "))
        return None
    return out


def _load(path: Optional[Path]) -> Optional[dict]:
    if path is None or not path.exists():
        return None
    try:
        if path.is_dir():
            files = sorted(path.glob("*.json"), key=lambda p: p.stat().st_mtime)
            if not files:
                return None
            path = files[-1]
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _bench_suites(bench: Optional[dict]) -> Dict[str, float]:
    """suite → accuracy (0-100) for the native backend."""
    suites: Dict[str, float] = {}
    for result in (bench or {}).get("results") or []:
        if result.get("backend") != "native" or not result.get("comparable"):
            continue
        accuracy = result.get("accuracy")
        if isinstance(accuracy, (int, float)):
            suites[result["suite"]] = float(accuracy)
    return suites


def _weakest(suites: Dict[str, float], names: List[str]) -> Optional[float]:
    """The weakest of the named suites (every sub-gate must pass)."""
    values = [suites[name] for name in names if name in suites]
    if not values or len(values) < len(names):
        return None
    return min(values)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-cache", action="store_true", help="reuse the existing reports")
    parser.add_argument("--json", dest="json_path")
    args = parser.parse_args()

    from ai.meta.intelligence import (
        DIMENSIONS,
        Integrity,
        LADDER_NAMESPACES,
        MIN_NEURAL_SHARE,
        composite,
    )

    print("統一智能報告（能力 × 來源 × 誠實度）")
    scores: Dict[str, float] = {}
    integrity = Integrity()
    sources: Dict[str, int] = {}
    gaps: Dict[str, float] = {}

    # 1. The native benchmark (facts / math / tools).
    bench = None
    if args.from_cache:
        bench = _load(REPORT_DIR / "angela_bench.json")
    else:
        bench = _load(
            _run(
                [
                    sys.executable,
                    "scripts/run_benchmarks.py",
                    "--backend",
                    "native",
                    "--suite",
                    "math,knowledge,knowledge_mc,code,routing",
                ],
                "angela_bench",
                out_flag="--out",
            )
        )
    suites = _bench_suites(bench)
    facts = _weakest(suites, ["knowledge", "knowledge_mc"])
    if facts is not None:
        scores["facts"] = facts / 100.0
    math = _weakest(suites, ["math"])
    if math is not None:
        scores["math"] = math / 100.0
    tools = _weakest(suites, ["code", "routing"])
    if tools is not None:
        scores["tools"] = tools / 100.0

    # 2. The pure-neural reasoning probe (L1's key metric).
    unseen_path = REPORT_DIR / "reasoning_unseen.json"
    if not args.from_cache:
        result = subprocess.run(
            [sys.executable, "scripts/probe_reasoning_unseen.py"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        unseen_path.write_text(
            json.dumps({"stdout": result.stdout}, ensure_ascii=False), encoding="utf-8"
        )
    unseen = _load(unseen_path) or {}
    neural = re.search(r"純神經 semantic_qa[^:]*:\s*(\d+)/100", unseen.get("stdout", ""))
    if neural:
        scores["paraphrase"] = int(neural.group(1)) / 100.0

    # 3. The native dialogue probe (dialogue / boundary + the source share).
    if args.from_cache:
        dialogue = _load(REPORT_DIR / "native_dialogue.json")
    else:
        dialogue = _load(
            _run(
                [
                    sys.executable,
                    "scripts/probe_native_dialogue.py",
                    "--max-turns",
                    _budget_value("max_turns", "1300"),
                    "--max-seconds",
                    _budget_value("max_seconds", "1200"),
                ],
                "native_dialogue",
            )
        )
    if dialogue:
        by_kind = (dialogue.get("standard_set") or {}).get("by_kind") or {}

        def kind_rate(name: str) -> Optional[float]:
            entry = by_kind.get(name) or {}
            value = entry.get("passed_ratio")
            return float(value) if isinstance(value, (int, float)) else None

        conversation = [kind_rate(k) for k in ("qa", "dialogue", "multi")]
        conversation = [value for value in conversation if value is not None]
        if conversation:
            scores["dialogue"] = sum(conversation) / len(conversation)
        claim_rate = kind_rate("claim")
        if claim_rate is not None:
            scores["boundary"] = claim_rate
        state_rate = kind_rate("state")
        if state_rate is not None:
            # The knowledge gap (the standard set's topics that are not in the
            # knowledge base) is *not* a capability — it is a coverage gap and
            # is reported next to the score, not folded into it.
            gaps["知識缺口（標準集 state 類）"] = state_rate
        sources = dict(dialogue.get("sources") or {})
        validity = dialogue.get("validity") or {}
        consistency = dialogue.get("consistency") or {}
        integrity.sample_valid = bool(validity.get("valid", True))
        integrity.consistent = bool(consistency.get("consistent", True))
        integrity.non_vacuous = not bool((dialogue.get("standard_set") or {}).get("truncated"))
        if not integrity.sample_valid:
            integrity.problems.extend(validity.get("problems", []) or ["樣本有效性未過"])
        if not integrity.consistent:
            integrity.problems.extend(
                consistency.get("disagreements", []) or ["少量與標準量不一致"]
            )
        if not integrity.non_vacuous:
            integrity.problems.append("標準集被預算截斷（量測不可比）")

    result = composite(scores, integrity)

    print("\n能力維度（六型分數型別；只有驗證／實際計入）")
    for dimension in DIMENSIONS:
        value = scores.get(dimension.id)
        shown = f"{value * 10:.1f}/10" if value is not None else "未量"
        print(
            f"  {dimension.id:10} {dimension.name:24} {shown:>8}  [{dimension.score_type}]"
            f"  門檻 {dimension.threshold * 10:.0f}/10"
        )
    source_verdict = ""
    if sources:
        total = sum(sources.values()) or 1
        neural_share = sources.get("neural", 0) / total
        print("\n回答來源（智能 vs 複製模板）")
        for name, count in sorted(sources.items(), key=lambda kv: -kv[1]):
            print(f"  {name:14} {count:5}  {count / total:.0%}")
        if neural_share < MIN_NEURAL_SHARE:
            source_verdict = (
                f"神經層佔比 {neural_share:.0%} < {MIN_NEURAL_SHARE:.0%}："
                "目前的能力主要由模板／確定性層提供，不是學到的模型"
            )
        else:
            source_verdict = (
                f"神經層佔比 {neural_share:.0%} ≥ {MIN_NEURAL_SHARE:.0%}："
                "學到的模型確實承擔了一部分回答"
            )
        print(f"  → {source_verdict}")
    if gaps:
        print("\n知識缺口（不計入總分——是覆蓋率，不是能力）")
        for name, rate in gaps.items():
            print(f"  {name:28} {rate:.0%}")
    print("\n智能總分")
    if result.get("status") == "measured":
        print(f"  {result['score']}/10  → 平均落在 {result['band']}（{result['band_summary']}）")
        print(
            f"  達成的階梯：{result['attained_level']}（要「達到」某階，該階關鍵維度必須全部過門檻）"
        )
        if result["level_missing"]:
            print(f"  未達下一階：{'；'.join(result['level_missing'])}")
        if result["failed_dimensions"]:
            print(f"  未達門檻的維度：{'；'.join(result['failed_dimensions'])}")
    else:
        print(f"  未定義：{result.get('reason')}")
    print(f"  誠實度：{result['integrity']}")
    print("\n階梯命名空間（避免 L0 撞名）")
    for namespace, meaning in LADDER_NAMESPACES.items():
        print(f"  {namespace:20} {meaning}")

    payload = {
        "scores": scores,
        "sources": sources,
        "source_verdict": source_verdict,
        "gaps": gaps,
        "bench_suites": suites,
        "integrity": {
            "sample_valid": integrity.sample_valid,
            "consistent": integrity.consistent,
            "non_vacuous": integrity.non_vacuous,
            "problems": integrity.problems,
        },
        "result": result,
    }
    # The committed artifact (a measurement snapshot, cited by the docs).
    ARTIFACT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n  報告已寫入 {ARTIFACT.relative_to(REPO_ROOT)}")

    if args.json_path:
        Path(args.json_path).write_text(
            json.dumps(
                {
                    "scores": scores,
                    "sources": sources,
                    "source_verdict": source_verdict,
                    "gaps": gaps,
                    "bench_suites": suites,
                    "integrity": {
                        "sample_valid": integrity.sample_valid,
                        "consistent": integrity.consistent,
                        "non_vacuous": integrity.non_vacuous,
                        "problems": integrity.problems,
                    },
                    "result": result,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"\n  報告已寫入 {args.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
