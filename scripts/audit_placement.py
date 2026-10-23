# LAYER: surface
# -*- coding: utf-8 -*-
"""Placement audit: does each reply declare the layer that actually produced it?

The rule (docs/06-project-management/MEASUREMENT_MAP.md):

  1. one artifact, one layer;
  2. a layer may not borrow another layer's credit;
  3. direct returns must be labelled (`route` = knowledge/memory/template/...),
     never defaulted to "llm";
  4. the total is the layer table, not a single number.

This runs a fixed set of inputs through the production chat path with the stage
recorder, derives the **declared** layer from `source`/`backend`/`route` and the
**actual** layer from what the traced producer returned, and fails on any
mismatch. An engine name (`unified`) is not a layer: undeclared is a violation.

Usage:
    python scripts/audit_placement.py            # exit 1 on any violation
    python scripts/audit_placement.py --json /tmp/placement.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = REPO_ROOT / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from trace_reply import (  # noqa: E402
    Recorder,
    _norm,
    _patch_stages,
    build_native_service,
    longest_common_run,
)

# backend/source → the layer that name denotes. An engine is NOT a layer.
DECLARED: Dict[str, str] = {
    "composed-template": "surface",
    "template": "surface",
    "dialog": "surface",
    "knowledge": "knowledge",
    "knowledge_base": "knowledge",
    "knowledge_pipeline": "knowledge",
    "dialogue-memory": "memory",
    "memory": "memory",
    "deterministic-math": "reasoning",
    "dual_rail": "reasoning",
    "math": "reasoning",
    "classifier": "reasoning",
    "query_classifier": "reasoning",
    "semantic-qa": "knowledge",  # the unified engine's semantic QA store
    "unified": None,  # engine, not a layer
    "model_bus": None,
    "unknown": None,
}

CASES = [
    "你好",
    "我今天很累",
    "天空為什麼是藍色的?",
    "水的沸點是多少?",
    "2加3等於多少?",
    "Zorblax的首都是Quuxville。",
    "Zorblax的首都是什麼?",
]


def actual_layer(reply: str, question: str, events: List[Dict[str, Any]]) -> str:
    """What actually produced the text? (one layer, from the trace)"""
    for event in events:
        stage = event["stage"]
        text = event.get("returned_text") or ""
        if event["is_none"] or not text:
            continue
        if stage == "route_knowledge" and _norm(text) in _norm(reply):
            return "knowledge"
        if stage == "_try_taught_facts" and _norm(text) in _norm(reply):
            return "memory"
        if stage == "answer" and _norm(text) in _norm(reply):
            return "knowledge"  # SemanticQA: the engine's own knowledge store
    for event in events:
        if event["stage"] in ("_gate_math", "_try_math_verification") and not event["is_none"]:
            return "reasoning"
    if any("composed-template" in str(e.get("returned") or "") for e in events):
        return "surface"
    copied = longest_common_run(question, reply)
    if copied >= max(4, len(_norm(question)) // 2):
        return "surface"
    # Not attributable with the current instrumentation: do not guess a layer.
    return "unknown"


async def audit(as_json: Optional[Path]) -> int:
    import services.llm.router as router_mod
    from api.routes.chat_routes import _handle_chat_request

    service = build_native_service()
    await service.initialize()
    recorder = Recorder()
    _patch_stages(recorder)
    previous = getattr(router_mod, "_llm_service", None)
    router_mod._llm_service = service
    rows: List[Dict[str, Any]] = []
    history: List[Dict[str, str]] = []
    try:
        for index, question in enumerate(CASES):
            recorder.begin(question)
            result = await _handle_chat_request(
                user_message=question,
                user_name="audit",
                history=list(history),
                session_id=f"placement-{os.getpid()}-{index}",
                origin="audit",
            )
            reply = (result or {}).get("response") or (result or {}).get("text") or ""
            backend = str((result or {}).get("backend") or "")
            route = str((result or {}).get("route") or "")
            declared = DECLARED.get(backend)
            if declared is None and route:
                declared = DECLARED.get(route)
            actual = actual_layer(str(reply), question, recorder.events)
            violation = ""
            if declared is None:
                violation = f"undeclared (backend={backend!r} route={route!r})"
            elif declared != actual:
                violation = f"declared {declared} but produced by {actual}"
            rows.append(
                {
                    "input": question,
                    "reply": str(reply)[:100],
                    "backend": backend,
                    "route": route,
                    "declared": declared,
                    "actual": actual,
                    "violation": violation,
                }
            )
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": str(reply)})
    finally:
        router_mod._llm_service = previous

    print(f"{'input':24s} {'declared':11s} {'actual':11s} reply")
    print("-" * 78)
    violations = 0
    for row in rows:
        flag = "OK " if not row["violation"] else "VIOLATION"
        print(
            f"{row['input'][:24]:24s} {str(row['declared']):11s} "
            f"{row['actual']:11s} {row['reply'][:30]}"
        )
        if row["violation"]:
            violations += 1
            print(f"    {flag}: {row['violation']}")
    print("-" * 78)
    print(f"{len(rows) - violations}/{len(rows)} replies declare the layer that produced them")
    if as_json:
        as_json.write_text(
            json.dumps({"rows": rows, "violations": violations}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"JSON: {as_json}")
    return 1 if violations else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()
    return asyncio.run(audit(args.json))


if __name__ == "__main__":
    raise SystemExit(main())
