# LAYER: surface
# -*- coding: utf-8 -*-
"""Trace one reply: every stage that touched it, and what it returned.

The question this answers is not "did it pass" but "where did this sentence
come from". A reply returned verbatim by a lookup (memory, curated KB, a
canned preset) is *not* evidence of intelligence — regardless of how good the
sentence sounds. So the trace records, in order:

    stage            which function ran
    returned         exactly what it returned (None = it declined)
    source           the label the producer attached (memory/knowledge/template...)
    copied_from_input  longest verbatim run shared with the user's message
    elapsed          how long it took

Usage:
    python scripts/trace_reply.py "Who invented the light bulb?"
    python scripts/trace_reply.py --turns "Zorblax's capital is Quuxville.;What is the capital of Zorblax?" --json /tmp/trace.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = REPO_ROOT / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))


def _norm(text: str) -> str:
    return " ".join(str(text or "").lower().split())


def longest_common_run(left: str, right: str) -> int:
    """Length of the longest verbatim (normalized) run; 0 means no copy."""
    a, b = _norm(left), _norm(right)
    if not a or not b:
        return 0
    best = 0
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    return best


class Recorder:
    """Wrap callables so every call is logged, without touching production code."""

    def __init__(self) -> None:
        self.question = ""
        self.events: List[Dict[str, Any]] = []
        self._wrapped = False

    def begin(self, question: str) -> None:
        self.question = question
        self.events = []

    def wrap(self, owner: Any, name: str, source: str = "") -> None:
        original = getattr(owner, name, None)
        if original is None or getattr(original, "_traced", False):
            return
        recorder = self

        if asyncio.iscoroutinefunction(original):

            async def traced(*args, **kwargs):  # type: ignore[no-redef]
                started = time.perf_counter()
                try:
                    value = await original(*args, **kwargs)
                except Exception as exc:
                    recorder._add(name, source, f"<raised {type(exc).__name__}: {exc}>")
                    raise
                recorder._add(name, source, value, (time.perf_counter() - started) * 1000)
                return value

        else:

            def traced(*args, **kwargs):  # type: ignore[no-redef]
                started = time.perf_counter()
                try:
                    value = original(*args, **kwargs)
                except Exception as exc:
                    recorder._add(name, source, f"<raised {type(exc).__name__}: {exc}>")
                    raise
                recorder._add(name, source, value, (time.perf_counter() - started) * 1000)
                return value

        traced._traced = True  # type: ignore[attr-defined]
        setattr(owner, name, traced)

    def _add(
        self,
        name: str,
        source: str,
        value: Any,
        elapsed_ms: float = 0.0,
    ) -> None:
        preview: Any = value
        value_text = ""
        if isinstance(value, dict):
            value_text = str(value.get("response") or value.get("text") or "")
            preview = {
                k: value.get(k)
                if isinstance(value.get(k), (str, int, float, bool, type(None)))
                else str(value.get(k))
                for k in ("response", "text", "source", "backend", "model", "route")
                if k in value
            }
        elif isinstance(value, str):
            value_text = value
        elif isinstance(value, (tuple, list)) and value and isinstance(value[0], str):
            # e.g. SemanticQA.answer -> (answer, similarity)
            value_text = value[0]
        if isinstance(preview, str):
            text = preview
        else:
            try:
                text = json.dumps(preview, ensure_ascii=False)
            except TypeError:
                text = str(preview)
        self.events.append(
            {
                "stage": name,
                "source": source,
                "returned": text[:400],
                "returned_text": value_text[:400],
                "is_none": value is None,
                "copied_from_input": longest_common_run(self.question, text or ""),
                "elapsed_ms": round(elapsed_ms, 1),
            }
        )


def _patch_stages(recorder: Recorder) -> None:
    if recorder._wrapped:
        return
    recorder._wrapped = True
    """Attach the recorder to every stage that can produce the final text."""
    from api.routes import chat_routes

    for name in (
        "_try_taught_facts",
        "_gate_math",
        "_try_math_verification",
        "_handle_execution_gate",
        "_try_agent_routing",
        "_generate_llm_response",
        "_analyze_emotion_and_crisis",
    ):
        recorder.wrap(chat_routes, name, "chat_routes")

    try:
        from ai import knowledge_base

        recorder.wrap(knowledge_base, "route_knowledge", "ai.knowledge_base")
    except Exception:
        pass
    try:
        from ai import symbolic_reasoner

        recorder.wrap(symbolic_reasoner, "route_reasoning", "ai.symbolic_reasoner")
    except Exception:
        pass
    try:
        from ai.unified_engine.semantic_qa import SemanticQA

        recorder.wrap(SemanticQA, "answer", "ai.unified_engine.semantic_qa")
    except Exception:
        pass
    try:
        from ai.arithmetic import deterministic_router

        for name in ("try_math", "try_reasoning", "try_neural_bridge"):
            recorder.wrap(deterministic_router, name, "ai.arithmetic")
    except Exception:
        pass


def build_native_service():
    """No external backend: only the project's own engines (LLM-free path)."""
    import copy

    from core.system.config.tiered_loader import get_config
    from services.llm.router import AngelaLLMService

    config = copy.deepcopy(get_config("system/llm") or {})
    config.setdefault("deployment", {})["mode"] = "local"
    for backend_config in (config.get("backends") or {}).values():
        provider = str(backend_config.get("provider") or "").lower()
        if provider not in ("unified", "ed3n", "garden", "local", "project"):
            backend_config["enabled"] = False
    return AngelaLLMService(config=config)


async def trace(questions: List[str], as_json: Optional[Path]) -> int:
    import services.llm.router as router_mod
    from api.routes.chat_routes import _handle_chat_request

    service = build_native_service()
    await service.initialize()
    recorder = Recorder()
    _patch_stages(recorder)
    previous = getattr(router_mod, "_llm_service", None)
    router_mod._llm_service = service
    history: List[Dict[str, str]] = []
    payload: List[Dict[str, Any]] = []
    try:
        for index, question in enumerate(questions):
            recorder.begin(question)
            session_id = f"trace-{os.getpid()}-{index}"
            result = await _handle_chat_request(
                user_message=question,
                user_name="tracer",
                history=list(history),
                session_id=session_id,
                origin="trace",
            )
            text = (result or {}).get("response") or (result or {}).get("text") or ""
            print(f"\n{'=' * 78}\nINPUT   {question}\nOUTPUT  {text}")
            print(
                f"source={(result or {}).get('source')!r} "
                f"backend={(result or {}).get('backend')!r} "
                f"route={(result or {}).get('route')!r}"
            )
            print(f"{'stage':38s} {'returned':52s} copy")
            print(f"{'-' * 78}")
            for event in recorder.events:
                returned = event["returned"].replace("\n", " ")
                print(
                    f"{event['stage'][:38]:38s} {returned[:52]:52s} "
                    f"{event['copied_from_input']:4d}"
                )
            shortcircuits = [
                e["stage"] for e in recorder.events if not e["is_none"]
            ]
            copied = longest_common_run(question, text)
            lookup = [
                e
                for e in recorder.events
                if e["stage"] in ("route_knowledge", "_try_taught_facts")
                and not e["is_none"]
                and _norm(e.get("returned_text") or "") in _norm(text)
            ]
            verdict = []
            if lookup and _norm(lookup[0].get("returned_text") or "") in _norm(text):
                verdict.append("lookup")
            if copied >= max(4, len(_norm(question)) // 2):
                verdict.append("echo")
            if "template" in str((result or {}).get("backend") or ""):
                verdict.append("template")
            if not verdict:
                verdict.append("not-a-copy")
            payload.append(
                {
                    "input": question,
                    "output": text,
                    "source": (result or {}).get("source"),
                    "backend": (result or {}).get("backend"),
                    "route": (result or {}).get("route"),
                    "verdict": verdict,
                    "stages_returning_a_value": shortcircuits,
                    "reply_copied_from_input": copied,
                    "reply_looks_like_input_echo": copied >= max(4, len(_norm(question)) // 2),
                    "events": recorder.events,
                }
            )
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": text})
    finally:
        router_mod._llm_service = previous

    print(f"\n{'=' * 78}\nVERDICT SUMMARY (how each sentence came about)")
    print(f"{'input':28s} {'backend':20s} {'verdict':22s} evidence")
    print(f"{'-' * 78}")
    for row in payload:
        evidence = ""
        if "lookup" in row["verdict"]:
            evidence = "a stage returned a stored value that appears in the reply"
        elif "echo" in row["verdict"]:
            evidence = f"{row['reply_copied_from_input']} chars copied from the question"
        elif "template" in row["verdict"]:
            evidence = "produced by the template path"
        else:
            evidence = "no copy/lookup/template found"
        print(
            f"{row['input'][:28]:28s} {str(row['backend'])[:20]:20s} "
            f"{'+'.join(row['verdict'])[:22]:22s} {evidence}"
        )

    if as_json:
        as_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nJSON: {as_json}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", nargs="?", default="")
    parser.add_argument(
        "--turns",
        default="",
        help="several turns separated by ';' so multi-turn (teaching) can be traced",
    )
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    questions = [q.strip() for q in args.turns.split(";") if q.strip()] if args.turns else []
    if not questions and args.question:
        questions = [args.question]
    if not questions:
        parser.error("give a question or --turns")
    return asyncio.run(trace(questions, args.json))


if __name__ == "__main__":
    raise SystemExit(main())
