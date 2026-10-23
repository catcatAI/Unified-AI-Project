# LAYER: surface
# -*- coding: utf-8 -*-
"""Where do the *correct* benchmark replies actually come from?

`run_benchmarks.py` says a reply is correct when it contains the gold answer.
That says nothing about *how* the sentence was produced: a curated lookup is
correct, and so is a rule-based classifier label. This census runs the *same*
`NativeBackend` the benchmark scores, records which internal producer returned
the value, and cross-tabulates:

    correct  ×  provenance (lookup / computed / classifier / echo / other)

The only cell that can count as the system producing an answer is
**correct ∧ computed|other**. Everything else is a layer (knowledge store,
calculator, classifier) doing its job — useful, but not intelligence.

The instrument must sit on the scored path: measuring the chat pipeline instead
produced different answers (18/40 vs 32/40 math) and would have been a
different experiment wearing the benchmark's name.

Usage:
    python scripts/census_reply_provenance.py
    python scripts/census_reply_provenance.py --suites knowledge,math --json /tmp/census.json
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = REPO_ROOT / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from trace_reply import longest_common_run  # noqa: E402


def _load_bench_module():
    spec = importlib.util.spec_from_file_location(
        "run_benchmarks", REPO_ROOT / "scripts" / "run_benchmarks.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _norm(text: str) -> str:
    return " ".join(str(text or "").lower().split())


class ProducerLog:
    """Record which producer functions returned a value during one answer."""

    def __init__(self) -> None:
        self.hits: List[str] = []

    def wrap(self, owner: Any, name: str, label: str) -> None:
        original = getattr(owner, name, None)
        if original is None or getattr(original, "_census", False):
            return
        log = self
        if asyncio.iscoroutinefunction(original):

            async def traced(*args, **kwargs):
                value = await original(*args, **kwargs)
                if value is not None:
                    log.hits.append(label)
                return value

        else:

            def traced(*args, **kwargs):
                value = original(*args, **kwargs)
                if value is not None:
                    log.hits.append(label)
                return value

        traced._census = True  # type: ignore[attr-defined]
        setattr(owner, name, traced)


def _install_producers(log: ProducerLog) -> None:
    from ai import knowledge_base

    log.wrap(knowledge_base, "route_knowledge", "lookup")
    from services import math_verifier

    log.wrap(math_verifier, "compute_arithmetic", "computed")
    try:
        from ai.memory import formula_solver

        log.wrap(formula_solver, "solve", "computed")
    except Exception:
        pass
    from ai.core.query_classifier import QueryClassifier

    log.wrap(QueryClassifier, "classify", "classifier")


def _classify(suite: str, reply: str, question: str, hits: List[str]) -> Dict[str, Any]:
    copied = longest_common_run(question, reply)
    echo = copied >= max(4, len(_norm(question)) // 2)
    if hits:
        content = hits[0]
    elif echo:
        content = "echo"
    elif not str(reply).strip():
        content = "abstain"
    else:
        content = "other"
    return {"content": content, "copied": copied}


async def run(suites: List[str], as_json: Optional[Path]) -> int:
    bench = _load_bench_module()
    items = [i for i in bench.load_dataset() if i.suite in suites]
    log = ProducerLog()
    _install_producers(log)
    backend = bench.NativeBackend()
    rows: List[Dict[str, Any]] = []
    for item in items:
        log.hits = []
        try:
            reply = await backend.answer(item)
        except Exception as exc:  # keep the row, mark it as an error
            reply = ""
            error = f"{type(exc).__name__}: {exc}"
        else:
            error = ""
        passed, skipped = bench.score_item(item, reply)
        prov = _classify(item.suite, str(reply), item.q, log.hits)
        rows.append(
            {
                "id": item.id,
                "suite": item.suite,
                "correct": bool(passed) and not skipped,
                "skipped": bool(skipped),
                "error": error,
                "producers": list(log.hits),
                **prov,
                "reply": str(reply)[:120],
            }
        )

    print(f"{'suite':10s} {'n':>3s} {'correct':>7s}  provenance of the correct ones")
    print("-" * 78)
    summary: Dict[str, Any] = {}
    for suite in suites:
        cells = [r for r in rows if r["suite"] == suite and not r["skipped"]]
        correct = [r for r in cells if r["correct"]]
        prov = Counter(r["content"] for r in correct)
        summary[suite] = {
            "n": len(cells),
            "correct": len(correct),
            "correct_provenance": dict(prov),
            "all_provenance": dict(Counter(r["content"] for r in cells)),
        }
        detail = "  ".join(f"{k}={v}" for k, v in sorted(prov.items())) or "-"
        print(f"{suite:10s} {len(cells):3d} {len(correct):7d}  {detail}")

    total_correct = sum(1 for r in rows if r["correct"])
    produced = sum(1 for r in rows if r["correct"] and r["content"] in ("computed", "other"))
    print("-" * 78)
    if total_correct:
        print(
            f"correct replies: {total_correct}; produced by the system "
            f"(computed/other): {produced} ({produced / total_correct * 100:.0f}%)"
        )
        print(
            "Retrieved / echoed / classified: "
            f"{total_correct - produced} ({(total_correct - produced) / total_correct * 100:.0f}%)"
        )
    else:
        print("correct replies: 0")
    print(
        "A correct lookup is the knowledge layer working, not intelligence. The "
        "score must not hide that split."
    )

    if as_json:
        as_json.write_text(
            json.dumps({"suites": summary, "rows": rows}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"JSON: {as_json}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suites", default="knowledge,math,code,routing")
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()
    suites = [s.strip() for s in args.suites.split(",") if s.strip()]
    return asyncio.run(run(suites, args.json))


if __name__ == "__main__":
    raise SystemExit(main())
