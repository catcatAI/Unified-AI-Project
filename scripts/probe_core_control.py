#!/usr/bin/env python3
"""Core vs control vs performance layer — which failures are intelligence problems.

The core cannot be inspected directly: an SNN's weights carry no readable
claim. It can only be measured *indirectly*, by letting it produce the content
and looking at the result. That measurement passes through the performance
layer (routing, templates, memory, retrieval, rules), which can answer
correctly with zero thinking — which is how a template score gets mistaken for
intelligence.

This probe runs the **same frozen items** through three producers and scores
them with the **same** rule:

  performance  NativeBackend (the production path: lookup / rules / templates)
  core:sn n    GARDEN (the project's SNN-family core)
  core:llm     a local instruct model (control group)

The LLM is the control: it is a neural model of known ability, so it separates

  * an **intelligence problem** — the control also fails (the task is beyond
    this class of model, or the measurement/oracle is wrong);
  * an **SNN gap** — the control passes, the SNN does not;
  * a **performance trick** — the performance layer passes, the core does not
    (correct answer, no thinking).

Only the two ``core`` columns count as intelligence. The performance column is
reported for comparison and is never added to it.

Usage:
    python scripts/probe_core_control.py                       # all suites
    python scripts/probe_core_control.py --suites knowledge,math
    python scripts/probe_core_control.py --limit 5 --json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_benchmarks import BenchItem, NativeBackend, load_dataset, score_item  # noqa: E402

DEFAULT_SUITES = ("knowledge", "math", "code", "routing")
#: Suites whose oracle is an internal label (the routing classifier's own
#: output). No core can satisfy it without being told the label space, so it is
#: a *performance-layer* task and is never read as an intelligence score.
SURFACE_TASK_SUITES = ("routing",)
DEFAULT_MODEL = REPO_ROOT / "data" / "models" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
OUT = REPO_ROOT / "data" / "intelligence_reports" / "core_control.json"

_PROMPT = (
    "Answer the question with the shortest correct answer. "
    'If you do not know, say "I don\'t know".\n\n'
    "Question: {q}\nAnswer:"
)


class _LLM:
    """Local instruct model — the neural control group (not a competitor)."""

    def __init__(self, model_path: Path) -> None:
        self.ok = False
        self.error = ""
        self._llm = None
        if not model_path.exists():
            self.error = f"model not found: {model_path}"
            return
        try:
            from llama_cpp import Llama  # type: ignore

            self._llm = Llama(model_path=str(model_path), n_ctx=1024, verbose=False, n_threads=4)
            self.ok = True
        except Exception as exc:  # noqa: BLE001 - reported, not hidden
            self.error = f"{type(exc).__name__}: {exc}"

    def answer(self, item: BenchItem) -> str:
        if not self.ok or self._llm is None:
            raise RuntimeError(self.error or "llm unavailable")
        out = self._llm(
            _PROMPT.format(q=item.q),
            max_tokens=96,
            temperature=0.0,
            stop=["\n\n", "Question:"],
        )
        return str((out.get("choices") or [{}])[0].get("text") or "").strip()


class _Garden:
    """The SNN-family core. No prompt-following: it emits what it learned."""

    def __init__(self) -> None:
        self.ok = False
        self.error = ""
        self._engine = None
        try:
            from ai.garden.garden_engine import GARDENEngine

            self._engine = GARDENEngine()
            self.ok = True
        except Exception as exc:  # noqa: BLE001 - reported, not hidden
            self.error = f"{type(exc).__name__}: {exc}"

    def answer(self, item: BenchItem) -> str:
        if not self.ok or self._engine is None:
            raise RuntimeError(self.error or "garden unavailable")
        return str(self._engine.generate(item.q) or "")


def _run_rows(items: List[BenchItem], suites: Dict[str, List[BenchItem]]) -> dict:
    native = NativeBackend()
    llm = _LLM(DEFAULT_MODEL)
    garden = _Garden()

    rows: Dict[str, List[dict]] = {}
    provenance = {
        "performance": "lookup/rules/templates (NativeBackend)",
        "snn": f"GARDEN engine ({'ok' if garden.ok else garden.error})",
        "llm": f"{DEFAULT_MODEL.name} ({'ok' if llm.ok else llm.error})",
    }

    for item in items:
        row = {"id": item.id, "suite": item.suite, "q": item.q}
        for name, producer in (("performance", native), ("snn", garden), ("llm", llm)):
            started = time.time()
            try:
                if name == "performance":
                    text = asyncio.run(producer.answer(item))
                else:
                    text = producer.answer(item)
                passed, skipped = score_item(item, text)
                row[name] = {
                    "answer": text[:300],
                    "passed": bool(passed) and not skipped,
                    "skipped": bool(skipped),
                    "ms": round((time.time() - started) * 1000, 1),
                }
            except Exception as exc:  # noqa: BLE001 - unavailability != wrong
                row[name] = {
                    "answer": "",
                    "passed": False,
                    "skipped": True,
                    "error": f"{type(exc).__name__}: {exc}",
                    "ms": round((time.time() - started) * 1000, 1),
                }
        rows.setdefault(item.suite, []).append(row)

    def rate(rows_: List[dict], name: str) -> Optional[float]:
        scored = [r[name] for r in rows_ if not r[name].get("skipped")]
        if not scored:
            return None
        return sum(1 for r in scored if r["passed"]) / len(scored)

    summary: Dict[str, dict] = {}
    for suite, suite_rows in rows.items():
        summary[suite] = {
            "n": len(suite_rows),
            "surface_task": suite in SURFACE_TASK_SUITES,
            "performance": rate(suite_rows, "performance"),
            "snn": rate(suite_rows, "snn"),
            "llm": rate(suite_rows, "llm"),
            "surface_only": sum(
                1
                for r in suite_rows
                if r["performance"]["passed"]
                and not r["llm"].get("skipped")
                and not r["llm"]["passed"]
            ),
            "intelligence_problem": sum(
                1
                for r in suite_rows
                if not r["performance"]["passed"]
                and not r["llm"]["passed"]
                and not r["llm"].get("skipped")
            ),
            "snn_gap": sum(
                1
                for r in suite_rows
                if r["llm"]["passed"] and not r["snn"]["passed"] and not r["snn"].get("skipped")
            ),
        }

    return {
        "provenance": provenance,
        "suites": summary,
        "rows": rows,
        "notes": [
            "只有 snn/llm 兩欄算智能；performance 欄只供對照，永不併入。",
            "surface_only：表現層答對、LLM 答不出＝正確答案沒有思考。",
            "intelligence_problem：表現層與 LLM 都答不出＝能力或量測/正解本身的問題。",
            "snn_gap：LLM 答對、SNN 答不出＝SNN 專屬缺口（不是任務不可解）。",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="core vs LLM control vs performance")
    parser.add_argument("--suites", default=",".join(DEFAULT_SUITES))
    parser.add_argument("--limit", type=int, default=0, help="max items per suite")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()

    wanted = {s.strip() for s in args.suites.split(",") if s.strip()}
    items = [item for item in load_dataset() if item.suite in wanted]
    if args.limit:
        kept: Dict[str, int] = {}
        limited: List[BenchItem] = []
        for item in items:
            if kept.get(item.suite, 0) < args.limit:
                limited.append(item)
                kept[item.suite] = kept.get(item.suite, 0) + 1
        items = limited

    result = _run_rows(items, {})
    result["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("核心 vs 對照組（LLM）vs 表現層 — 同一題組、同一評分")
        for name, desc in result["provenance"].items():
            print(f"  {name:12} {desc}")
        print(f"\n  {'suite':10} {'n':>4} {'表現層':>8} {'SNN':>8} {'LLM':>8}")
        for suite, cell in result["suites"].items():

            def fmt(v: Optional[float]) -> str:
                return "未量" if v is None else f"{v:.0%}"

            tag = "（表現層任務，不讀作智能）" if cell.get("surface_task") else ""
            print(
                f"  {suite:10} {cell['n']:4d} {fmt(cell['performance']):>8}"
                f" {fmt(cell['snn']):>8} {fmt(cell['llm']):>8}  {tag}"
            )
            print(
                f"             ↳ 只有表現層會={cell['surface_only']}"
                f"　都答不出={cell['intelligence_problem']}"
                f"　LLM會SNN不會={cell['snn_gap']}"
            )
        print("\n只有 SNN/LLM 兩欄算智能；表現層只供對照。")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if not args.json:
        print(f"\n已寫入 {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
