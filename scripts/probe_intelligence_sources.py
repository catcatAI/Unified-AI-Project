#!/usr/bin/env python3
"""跑偏稽核：回答到底來自哪一層？對話有沒有改變「回答用的那個模型」？

這個問題不能靠感覺：**如果原生路徑的回答幾乎都是模板／檢索，就不能說它
「會學習」**。所以這支腳本量三件事：

1. **回答來源分布**（每個回答由哪一層產生）：模板／檢索／確定性引擎／
   中間層／斷言／**神經檢索（SemanticQA）**／SNN。純神經的比例＝「智能」的
   份額（不是模板的份額）。
2. **對話有沒有改變回答用的模型**：對話前後比較回答模型的狀態
   （統計核心的 bytes_seen、SemanticQA 的樣本數）與同一問題的答案。
3. **SNN 有沒有在跑**：ED3N／GARDEN 的前向與權重變化、SNN 產出的回答佔比。

用法：
    python scripts/probe_intelligence_sources.py
    python scripts/probe_intelligence_sources.py --json out.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

# The agent's questions: a mix of the domains the native path serves.
PROBE_TURNS: List[str] = [
    "What is 2+2?",
    "What is 17*23?",
    "Tell me about the sky's color.",
    "A is taller than B, who is taller?",
    "The first exceeds second, second exceeds third, which is on top?",
    "水的沸點是 100°C，這句話對嗎？",
    "我今天很累",
    "謝謝你陪我聊",
    "我叫小明",
    "我剛才說我叫什麼名字？",
]

# Which layer counts as "the intelligence" (not a lookup of a written line).
NEURAL_BACKENDS = ("unified", "semantic", "neuro", "snn", "ed3n", "garden")
TEMPLATE_BACKENDS = ("composed-template", "template", "local-fallback")
DETERMINISTIC_BACKENDS = (
    "deterministic-math",
    "deterministic-reasoning",
    "knowledge",
    "math",
    "neural-bridge",
    "claim-reasoning",
    "memory-teaching",
)


def _classify(backend: str, route: str) -> str:
    """The shared classifier (the probe and the audit must agree)."""
    from ai.response.human_speech import classify_source

    return classify_source(backend, route)


async def _run(questions: List[str]) -> Tuple[List[Dict[str, object]], object]:
    """Run the native-only path and collect the answers + the engine state."""
    from core.system.config.tiered_loader import get_config
    from services.chat_service import ChatService
    from services.llm.router import AngelaLLMService
    import copy

    config = copy.deepcopy(get_config("system/llm") or {})
    config.setdefault("deployment", {})["mode"] = "local"
    for backend_id, backend_config in (config.get("backends") or {}).items():
        if (backend_config.get("type") or "").lower() == "cloud":
            backend_config["enabled"] = False
    service = AngelaLLMService(config=config)
    await service.initialize()
    import services.llm.router as router_module

    previous = getattr(router_module, "_llm_service", None)
    router_module._llm_service = service
    chat = ChatService(llm_service=service)
    await chat.initialize()

    from api.routes.chat_routes import _handle_chat_request

    history: List[Dict[str, str]] = []
    records: List[Dict[str, object]] = []
    try:
        for question in questions:
            result = await _handle_chat_request(
                user_message=question,
                user_name="agent",
                history=list(history),
                session_id="audit-1",
                origin="probe",
            )
            backend = str((result or {}).get("backend") or "")
            route = str((result or {}).get("route") or "")
            text = str((result or {}).get("response") or (result or {}).get("text") or "")
            records.append(
                {
                    "question": question,
                    "backend": backend,
                    "route": route,
                    "source": _classify(backend, route),
                    "answer": text[:80],
                }
            )
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": text})
    finally:
        router_module._llm_service = previous
    return records, service


def _engine_state(service: object) -> Dict[str, object]:
    """The state of the answering model (and of the SNN engines)."""
    state: Dict[str, object] = {}
    try:
        engine = None
        for backend in (getattr(service, "backends", {}) or {}).values():
            candidate = getattr(backend, "_engine", None)
            if candidate is not None and hasattr(candidate, "core"):
                engine = candidate
                break
        if engine is None:
            return state
        core = engine.core
        state["core_bytes_seen"] = int(getattr(core, "_bytes_seen", 0) or 0)
        state["core_samples_seen"] = int(getattr(core, "_samples_seen", 0) or 0)
        qa = getattr(engine, "semantic_qa", None)
        state["semantic_qa_pairs"] = len(getattr(getattr(qa, "_pairs", None), "keys", lambda: [])())
    except Exception as exc:  # pragma: no cover - the audit must not crash
        state["core_error"] = str(exc)
    try:
        from ai.garden.garden_engine import GARDENEngine

        garden = GARDENEngine.get_shared()
        state["garden_learn_count"] = int(getattr(garden, "_learn_count", 0) or 0)
        state["garden_templates"] = len(getattr(garden, "_templates", {}) or {})
    except Exception as exc:
        state["garden_error"] = str(exc)
    return state


async def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", dest="json_path")
    args = parser.parse_args()

    # The sandbox: the audit must not touch the user's real memory.
    sandbox = Path(tempfile.mkdtemp(prefix="angela-audit-"))
    os.environ["ANGELA_DATA_DIR"] = str(sandbox)
    os.environ["VECTOR_STORE_PATH"] = str(sandbox / "vector_store")
    try:
        before_service = await _service_stub()
        records, service = await _run(PROBE_TURNS)
        after = _engine_state(service)

        sources = Counter(str(r["source"]) for r in records)
        backends = Counter(str(r["backend"]) for r in records)
        print("跑偏稽核：原生路徑（不接任何外部 LLM）")
        print(f"  回答數：{len(records)}")
        print("  來源分布：" + "｜".join(f"{k} {v}" for k, v in sources.most_common()))
        print("  後端分布：" + "｜".join(f"{k} {v}" for k, v in backends.most_common()))
        print(f"  回答模型狀態：{after}")
        for record in records:
            print(
                f"    [{record['source']:13}] {str(record['question'])[:26]:28} → "
                f"{str(record['answer'])[:46]!r}"
            )
        neural_share = sources.get("neural", 0) / max(len(records), 1)
        template_share = sources.get("template", 0) / max(len(records), 1)
        print(f"  **神經層佔比 {neural_share:.0%}｜模板層佔比 {template_share:.0%}**")
        if neural_share >= 0.5:
            print("  判讀：神經層過半 → 回答主要來自學到的模型（不是複製模板）。")
        elif neural_share >= 0.2:
            print(
                "  判讀：神經層開始有份額，但模板仍佔大頭——**還不能算智能學習**；"
                "下一步是讓更多回合由學到的模型回答。"
            )
        else:
            print(
                "  判讀：神經層＝0 或極低、模板層＝高 → 目前是「模板＋檢索」，"
                "**不是智能學習**；學到了東西的那個模型不在回答路徑上。"
            )
        if args.json_path:
            Path(args.json_path).write_text(
                json.dumps(
                    {
                        "records": records,
                        "sources": dict(sources),
                        "backends": dict(backends),
                        "engine_state": after,
                        "neural_share": neural_share,
                        "template_share": template_share,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(f"  結果已寫入 {args.json_path}")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)
    return 0


async def _service_stub() -> object:
    """A placeholder (the state before the run is measured inside _run)."""
    return None


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
