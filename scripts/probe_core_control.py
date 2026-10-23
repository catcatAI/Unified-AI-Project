#!/usr/bin/env python3
"""Core vs control vs performance layer — which failures are intelligence problems.

The core cannot be inspected directly: an SNN's weights carry no readable
claim. It can only be measured *indirectly*, by letting it produce the content
and looking at the result. That measurement passes through the performance
layer (routing, templates, memory, retrieval, rules), which can answer
correctly with zero thinking — which is how a template score gets mistaken for
intelligence.

This probe runs the **same frozen items** through the producers and scores
them with the **same** rule:

  performance  NativeBackend (the production path: lookup / rules / templates)
  garden       GARDEN (association engine)
  ed3n         ED3N trained checkpoint (decoder read directly, no reflex)
  tok          token-level spiking decoder (surrogate gradient, next token)
  llm          a local instruct model (control group)

The LLM is the control: it is a neural model of known ability, so it separates

  * an **intelligence problem** — the control also fails (the task is beyond
    this class of model, or the measurement/oracle is wrong);
  * an **SNN gap** — the control passes, the SNN does not;
  * a **performance trick** — the performance layer passes, the core does not
    (correct answer, no thinking).

Only the ``core`` columns (garden/ed3n/tok/llm) count as intelligence. The
performance column is reported for comparison and is never added to it.

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
PRODUCERS = ("performance", "snn", "ed3n", "tok", "llm")
CORE_PRODUCERS = ("snn", "ed3n", "tok", "llm")
SNN_PRODUCERS = ("snn", "ed3n", "tok")
DEFAULT_MODEL = REPO_ROOT / "data" / "models" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
DEFAULT_ED3N = REPO_ROOT / "apps" / "backend" / "data" / "models" / "ed3n_core.json"
DEFAULT_TOKEN_SNN = REPO_ROOT / "apps" / "backend" / "data" / "models" / "token_snn.pt"
OUT = REPO_ROOT / "data" / "intelligence_reports" / "core_control.json"

_PROMPT = (
    "Answer the question with the shortest correct answer. "
    'If you do not know, say "I don\'t know".\n\n'
    "Question: {q}\nAnswer:"
)


def _producer_stats(rows: List[dict], name: str) -> dict:
    """Accuracy (an abstention is not correct), coverage, and distinct answers.

    Accuracy keeps the old rule — an empty answer is not a correct answer — so
    replacing a failed answer with an abstention can never raise a score. It is
    reported next to ``coverage`` because "0%" from 40 wrong answers and "0%"
    from 0 answers are different facts and the old table hid the difference.
    """
    cells = [r[name] for r in rows if not r[name].get("skipped")]
    answered = [c for c in cells if c.get("answered")]
    accuracy = (sum(1 for c in cells if c["passed"]) / len(cells)) if cells else None
    answered_accuracy = (
        sum(1 for c in answered if c["passed"]) / len(answered) if answered else None
    )
    return {
        "accuracy": accuracy,
        "coverage": (len(answered) / len(rows)) if rows else None,
        "accuracy_answered": answered_accuracy,
        "answered": len(answered),
        "distinct": len({c.get("answer", "").strip() for c in answered}),
    }


def _summarize(rows: Dict[str, List[dict]]) -> Dict[str, dict]:
    summary: Dict[str, dict] = {}
    for suite, suite_rows in rows.items():
        cell: Dict[str, object] = {
            "n": len(suite_rows),
            "surface_task": suite in SURFACE_TASK_SUITES,
        }
        for name in PRODUCERS:
            stats = _producer_stats(suite_rows, name)
            cell[name] = stats["accuracy"]
            cell.setdefault("coverage", {})[name] = stats["coverage"]
            cell.setdefault("accuracy_answered", {})[name] = stats["accuracy_answered"]
            cell.setdefault("answered", {})[name] = stats["answered"]
            cell.setdefault("distinct", {})[name] = stats["distinct"]
        cell["surface_only"] = sum(
            1
            for r in suite_rows
            if r["performance"]["passed"] and r["llm"].get("answered") and not r["llm"]["passed"]
        )
        cell["intelligence_problem"] = sum(
            1
            for r in suite_rows
            if not r["performance"]["passed"]
            and not r["llm"]["passed"]
            and not r["llm"].get("skipped")
        )
        cell["snn_gap"] = sum(
            1
            for r in suite_rows
            if r["llm"]["passed"] and not r["snn"]["passed"] and not r["snn"].get("skipped")
        )
        cell["gaps"] = {
            name: sum(
                1
                for r in suite_rows
                if r["llm"]["passed"] and not r[name]["passed"] and not r[name].get("skipped")
            )
            for name in SNN_PRODUCERS
        }
        summary[suite] = cell
    return summary


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


class _TokenSNN:
    """Token-level spiking decoder (surrogate gradient, next-token objective)."""

    def __init__(self, checkpoint: Path) -> None:
        self.ok = False
        self.error = ""
        self._model = None
        if not checkpoint.exists():
            self.error = f"model not found: {checkpoint}"
            return
        try:
            from ai.ed3n.token_snn import TokenSNN

            self._model = TokenSNN.load(checkpoint)
            self.ok = True
        except Exception as exc:  # noqa: BLE001 - reported, not hidden
            self.error = f"{type(exc).__name__}: {exc}"

    def answer(self, item: BenchItem) -> str:
        if not self.ok or self._model is None:
            raise RuntimeError(self.error or "token-snn unavailable")
        return str(self._model.generate(item.q, max_new=48) or "").strip()


class _ED3N:
    """ED3N — the project's other SNN-family core (association + sequence)."""

    def __init__(self, checkpoint: Path) -> None:
        self.ok = False
        self.error = ""
        self._engine = None
        try:
            from ai.ed3n.ed3n_engine import ED3NEngine

            self._engine = ED3NEngine()
            self._engine.load_presets()
            if checkpoint.exists():
                self._engine.load(str(checkpoint))
            # encode() resolves words through the external dictionaries; without
            # this the core runs on 46 preset keys and every sentence collapses
            # to a handful of "m*" keys.
            try:
                self._engine.load_external_dictionaries()
            except Exception as exc:  # noqa: BLE001 - optional derived data
                self.error = f"dictionaries: {type(exc).__name__}: {exc}"
            self.ok = True
        except Exception as exc:  # noqa: BLE001 - reported, not hidden
            self.error = f"{type(exc).__name__}: {exc}"

    def answer(self, item: BenchItem) -> str:
        if not self.ok or self._engine is None:
            raise RuntimeError(self.error or "ed3n unavailable")
        # Read the decoder, not generate(): generate() consults the reflex table
        # first, and a reflex reply is a template — it must not be credited to
        # the core.
        return str(self._engine.step_decoder.generate_text(item.q) or "")


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


def _run_rows(
    items: List[BenchItem],
    suites: Dict[str, List[BenchItem]],
    ed3n_checkpoint: Path = DEFAULT_ED3N,
    token_checkpoint: Path = DEFAULT_TOKEN_SNN,
) -> dict:
    native = NativeBackend()
    llm = _LLM(DEFAULT_MODEL)
    garden = _Garden()
    ed3n = _ED3N(ed3n_checkpoint)
    token = _TokenSNN(token_checkpoint)

    rows: Dict[str, List[dict]] = {}
    provenance = {
        "performance": "lookup/rules/templates (NativeBackend)",
        "snn": f"GARDEN engine ({'ok' if garden.ok else garden.error})",
        "ed3n": f"{ed3n_checkpoint.name} ({'ok' if ed3n.ok else ed3n.error})",
        "tok": f"{token_checkpoint.name} ({'ok' if token.ok else token.error})",
        "llm": f"{DEFAULT_MODEL.name} ({'ok' if llm.ok else llm.error})",
    }

    for item in items:
        row = {"id": item.id, "suite": item.suite, "q": item.q}
        for name, producer in (
            ("performance", native),
            ("snn", garden),
            ("ed3n", ed3n),
            ("tok", token),
            ("llm", llm),
        ):
            started = time.time()
            try:
                if name == "performance":
                    text = asyncio.run(producer.answer(item))
                else:
                    text = producer.answer(item)
                passed, skipped = score_item(item, text)
                row[name] = {
                    "answer": text[:300],
                    "answered": bool(str(text).strip()),
                    "passed": bool(passed) and not skipped,
                    "skipped": bool(skipped),
                    "ms": round((time.time() - started) * 1000, 1),
                }
            except Exception as exc:  # noqa: BLE001 - unavailability != wrong
                row[name] = {
                    "answer": "",
                    "answered": False,
                    "passed": False,
                    "skipped": True,
                    "error": f"{type(exc).__name__}: {exc}",
                    "ms": round((time.time() - started) * 1000, 1),
                }
        rows.setdefault(item.suite, []).append(row)

    summary = _summarize(rows)

    return {
        "provenance": provenance,
        "suites": summary,
        "rows": rows,
        "notes": [
            "只有 snn/ed3n/tok/llm 四欄算智能；performance 欄只供對照，永不併入。",
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
    parser.add_argument("--ed3n-checkpoint", default=str(DEFAULT_ED3N))
    parser.add_argument("--token-checkpoint", default=str(DEFAULT_TOKEN_SNN))
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

    result = _run_rows(items, {}, Path(args.ed3n_checkpoint), Path(args.token_checkpoint))
    result["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("核心 vs 對照組（LLM）vs 表現層 — 同一題組、同一評分")
        for name, desc in result["provenance"].items():
            print(f"  {name:12} {desc}")
        print(
            f"\n  {'suite':10} {'n':>4} {'表現層':>8} {'GARDEN':>8} {'ED3N':>8}"
            f" {'TOK-SNN':>8} {'LLM':>8}"
        )
        for suite, cell in result["suites"].items():

            def fmt(v: Optional[float]) -> str:
                return "未量" if v is None else f"{v:.0%}"

            tag = "（表現層任務，不讀作智能）" if cell.get("surface_task") else ""
            print(
                f"  {suite:10} {cell['n']:4d} {fmt(cell['performance']):>8}"
                f" {fmt(cell['snn']):>8} {fmt(cell['ed3n']):>8}"
                f" {fmt(cell['tok']):>8} {fmt(cell['llm']):>8}  {tag}"
            )
            print(
                f"             ↳ 只有表現層會={cell['surface_only']}"
                f"　都答不出={cell['intelligence_problem']}"
                f"　LLM會SNN不會={cell['snn_gap']}"
            )
            answered = cell.get("answered") or {}
            print(
                "               coverage："
                + "  ".join(f"{name} {answered.get(name, 0)}/{cell['n']}" for name in PRODUCERS)
            )
        print("\n只有 SNN/ED3N/TOK-SNN/LLM 四欄算智能；表現層只供對照。")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if not args.json:
        try:
            shown = out.relative_to(REPO_ROOT)
        except ValueError:
            shown = out
        print(f"\n已寫入 {shown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
