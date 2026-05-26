"""
ANGELA-MATRIX: [L4-L5] [αβγδ] [A] [L2]
REPL mode: interactive chat loop with uvicorn daemon.
Extracted from main_api_server.py (A3 god module split).
"""

import asyncio
import logging
import sys
import threading
import time
from typing import Any, List, Optional, Tuple


def run_repl_mode():
    server_thread = threading.Thread(target=_run_uvicorn_in_thread, daemon=True)
    server_thread.start()
    print("[REPL] Backend starting on http://127.0.0.1:8000 ...")
    time.sleep(3)
    asyncio.run(_run_repl())


def _run_uvicorn_in_thread():
    from services.main_api_server import app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")


async def _run_repl():
    from api.lifespan import _get_chat_service

    logging.disable(logging.WARNING)

    print("[REPL] Angela brain initializing...")
    service = await _get_chat_service()
    await service.initialize()
    print("[REPL] Angela ready! (exit/quit to stop)\n")
    print("[Hint] Type /help for commands, /state to view 8D matrix\n")

    loop = asyncio.get_event_loop()
    cmd_history: List[str] = []
    while True:
        try:
            user_input = await loop.run_in_executor(None, lambda: input("\n\U0001F4AC  \u4f60: "))
        except (EOFError, KeyboardInterrupt):
            print("\n[REPL] Shutting down...")
            break

        text = user_input.strip()
        if text.lower() in ("exit", "quit"):
            print("[REPL] Good bye!")
            break
        if not text:
            continue

        if text.startswith("/") or text.startswith(":"):
            intent_name, response_text = _handle_repl_command(text, service, cmd_history)
            if response_text is not None:
                print(f"\U0001F4AD Angela [{intent_name}]: {response_text}")
                continue

        print("\U0001F4AD Angela: ", end="", flush=True)
        response = await service.generate_response(text)
        print(response)
        cmd_history.append(text)
        if len(cmd_history) > 100:
            cmd_history = cmd_history[-100:]


def _handle_repl_command(text: str, service: Any, history: List[str]) -> Tuple[str, Optional[str]]:
    parts = text.lstrip("/:").split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd in ("h", "help"):
        return ("system", _build_help_text())

    if cmd in ("s", "state"):
        return ("system", _format_state_snapshot(service))

    if cmd in ("m", "mem", "memory"):
        return ("system", _format_memory_summary(service, args))

    if cmd in ("c", "clear"):
        return ("system", "\033[2J\033[H")

    if cmd in ("cfg", "config"):
        return ("system", _format_config_summary(service))

    if cmd in ("i", "intent"):
        return ("system", _format_intent_registry())

    if cmd in ("r", "route"):
        return ("system", _format_llm_routing(service))

    if cmd in ("tickle", "tkl"):
        return ("system", _handle_tickle_command(args))

    if cmd in ("model", "m") and args:
        return ("system", _handle_model_command(args, service))

    if cmd in ("drive", "gd", "cloud"):
        return ("system", _handle_drive_command(args))

    if cmd in ("hist", "history"):
        lines = [f"  {i+1}. {h[:60]}" for i, h in enumerate(history[-10:])]
        return ("system", f"Recent history:\n" + "\n".join(lines) if lines else "(empty)")

    return ("unknown", None)


def _build_help_text() -> str:
    return """Angela REPL Commands:
  /help, /h        — This help
  /state, /s        — 8D state matrix snapshot
  /memory, /m [q]   — Memory summary (optional search)
  /tickle, /tkl [part] [intensity] — Trigger tickle reflex
  /model [list|stats|switch <name>|auto] — LLM model management
  /drive [status|auth|list|search <q>|sync|analyze|logout] — Google Drive
  /clear, /c        — Clear screen
  /config, /cfg     — Current YAML config summary
  /intent, /i       — Intent registry overview
  /route, /r        — LLM routing status
  /history          — Recent command history
  /eval <expr>      — Evaluate Python expression
  exit/quit         — Stop REPL"""


def _format_state_snapshot(service: Any) -> str:
    try:
        sm = service.state_matrix
        lines = ["--- 8D State Matrix ---"]
        for axis in ("alpha", "beta", "gamma", "delta", "epsilon", "theta", "zeta"):
            ax = getattr(sm, axis, None)
            if ax and hasattr(ax, "values"):
                vals = list(ax.values.items())[:4]
                vals_str = ", ".join(f"{k}={v:.2f}" for k, v in vals)
                lines.append(f"  [{axis}] {vals_str}")
        eta = service.eta_state
        if eta:
            lines.append(f"  [eta] exec={eta.execution_count}, success={eta.success_rate:.1%}, drift={eta.structural_drift:.3f}")
        theta = sm.theta if hasattr(sm, "theta") else None
        if theta:
            lines.append(f"  [theta] novelty={theta.values.get('novelty',0):.2f}, correction={theta.values.get('correction_urge',0):.2f}")
        return "\n".join(lines)
    except Exception as e:
        return f"State unavailable: {e}"


def _format_memory_summary(service: Any, search: str) -> str:
    try:
        if hasattr(service, "memory_manager") and service.memory_manager:
            loop = asyncio.new_event_loop()
            results = loop.run_until_complete(service.memory_manager.query_core_memory(
                keywords=[search] if search else ["experience"], limit=5
            ))
            loop.close()
            if not results:
                return "(no memories found)"
            lines = [f"Memory {i+1}: {r.get('content','')[:80]}" for i, r in enumerate(results)]
            return "\n".join(lines)
        return "(memory manager not initialized)"
    except Exception as e:
        return f"Memory error: {e}"


def _format_config_summary(service: Any) -> str:
    try:
        cfg = service._angela_config
        intents = list(cfg.get_intents().keys())
        thresholds = cfg.get_complexity_thresholds()
        llm = cfg.get_llm_config()
        providers = list(llm.get("providers", {}).keys()) if llm else []
        routing = cfg.get_routing_policy()
        chain = routing.get("fallback_chain", [])
        return f"Intents: {intents}\nComplexity thresholds: {thresholds}\nLLM providers: {providers}\nFallback chain: {chain}"
    except Exception as e:
        return f"Config error: {e}"


def _format_intent_registry() -> str:
    try:
        from core.intent_registry import IntentRegistry
        reg = IntentRegistry()
        lines = ["Intent Registry:"]
        for p in reg.patterns:
            lines.append(f"  {p.name} (pri={p.priority}): {p.keywords[:5]}")
        return "\n".join(lines)
    except Exception as e:
        return f"Intent registry error: {e}"


def _format_llm_routing(service: Any) -> str:
    try:
        from services.angela_llm_service import get_llm_service
        llm_svc = get_llm_service()
        backends = list(llm_svc.backends.keys()) if hasattr(llm_svc, "backends") else []
        active = getattr(llm_svc, "active_backend", None)
        chain = getattr(llm_svc, "_angela_fallback_chain", [])
        stats = getattr(llm_svc, "stats", {})
        return f"Backends: {backends}\nActive: {active}\nFallback chain: {chain}\nStats: {stats}"
    except Exception as e:
        return f"LLM routing error: {e}"


def _handle_tickle_command(args: str) -> str:
    parts = args.strip().split()
    if not parts:
        from core.autonomous.tickle_reflex_system import get_reflex_system
        reflex = get_reflex_system()
        all_parts = reflex.get_all_body_parts()
        sensitive = reflex.get_sensitive_parts()
        thresholds = reflex.get_intensity_thresholds()
        return (f"Tickle Reflex System\nParts: {all_parts}\nSensitive: {sensitive}\n"
                f"Thresholds: {thresholds}\n\nUsage: /tickle <part> [intensity 0-1]")

    body_part = parts[0]
    intensity = float(parts[1]) if len(parts) > 1 else 0.5

    import asyncio
    from core.autonomous.tickle_reflex_system import get_reflex_system

    reflex = get_reflex_system()

    async def run_tickles():
        return await reflex.trigger_tickles(
            body_part=body_part,
            intensity=intensity,
            duration_seconds=1.0,
            origin="REPL"
        )

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(run_tickles())
    finally:
        loop.close()

    phase1 = result.get("phase1", {})
    phase2 = result.get("phase2", {})
    anim = phase1.get("animation", {})
    return (f"[Tickle] {body_part} intensity={intensity:.1f}\n"
            f"Level: {result.get('intensity_level', '?')}\n"
            f"Output: {phase1.get('output_mode', '?')}\n"
            f"Animation: {anim.get('motion_name', '?')} ({anim.get('duration_ms', 0)}ms)\n"
            f"Expression: {anim.get('expression', '?')}\n"
            f"Phase2 triggered: {phase2.get('triggered', False)}\n"
            f"Elapsed: {result.get('elapsed_ms', 0)}ms")


def _handle_model_command(args: str, service: Any) -> str:
    parts = args.strip().split(maxsplit=1)
    subcmd = parts[0].lower() if parts else "list"
    subarg = parts[1] if len(parts) > 1 else ""

    try:
        from services.angela_llm_service import get_llm_service
        llm_svc = get_llm_service()

        if subcmd in ("list", "ls", "l"):
            backends = list(llm_svc.backends.keys()) if hasattr(llm_svc, "backends") else []
            active = getattr(llm_svc, "active_backend", None)
            return f"Available models: {backends}\nActive: {active}"

        if subcmd in ("stats", "s"):
            stats = getattr(llm_svc, "stats", {})
            return f"LLM Stats: {stats}"

        if subcmd in ("switch", "sw", "set"):
            if not subarg:
                return "Usage: /model switch <name>\nAvailable: " + str(list(getattr(llm_svc, "backends", {}).keys()))
            backend_key = subarg.strip()
            for btype, bobj in getattr(llm_svc, "backends", {}).items():
                if backend_key.lower() in btype.name.lower():
                    llm_svc.active_backend = bobj
                    return f"[OK] Switched to {btype.name}"
            return f"[FAIL] Model '{backend_key}' not found"

        if subcmd in ("auto", "a"):
            routing = getattr(llm_svc, "_angela_routing", {})
            return f"Auto routing enabled. Policy: {routing}"

        return f"Unknown subcommand: {subcmd}\nUsage: /model [list|stats|switch <name>|auto]"

    except Exception as e:
        return f"Model command error: {e}"


def _handle_drive_command(args: str) -> str:
    import httpx
    from core.config_loader import get_angela_config

    parts = args.strip().split(maxsplit=1)
    subcmd = parts[0].lower() if parts else "status"
    subarg = parts[1] if len(parts) > 1 else ""

    cfg = get_angela_config()
    ops = cfg.get_drive_all_operations()

    def resolve_op(cmd: str) -> Optional[str]:
        for op_name, op_cfg in ops.items():
            if cmd in op_cfg.get("aliases", []):
                return op_name
        return None

    op = resolve_op(subcmd)
    base = "http://127.0.0.1:8000/api/v1/drive"

    try:
        if op == "status" or subcmd in ("status", "s"):
            resp = httpx.get(f"{base}/status", timeout=10)
            d = resp.json()
            auth = d.get("authenticated", False)
            quota = d.get("quota", {})
            lines = [
                f"Google Drive: {'\u2705 \u5df2\u8a8d\u8b49' if auth else '\u274c \u672a\u8a8d\u8b49'}",
                f"  \u7528\u6236: {quota.get('user', 'N/A')}",
                f"  \u5df2\u7528: {quota.get('used', 'N/A')} / {quota.get('total', 'N/A')}",
                f"  \u72c0\u614b: {d.get('status', 'unknown')}",
            ]
            return "\n".join(lines)

        if op == "auth" or (subcmd in ("auth", "a") and subarg in ("", "url")):
            resp = httpx.get(f"{base}/auth/url", timeout=10)
            url = resp.json().get("url", "")
            return f"\u6388\u6b0a URL\uff1a\n{url}\n\n\u8acb\u7528\u700f\u89bd\u5668\u6253\u958b\u9019\u500b\u93c8\u7d50\uff0c\u6388\u6b0a\u5f8c\u628a\u56de\u50b3\u7684 code \u8cbc\u7d66\u6211\u3002"

        if op == "auth" or subcmd in ("callback", "cb"):
            resp = httpx.post(f"{base}/auth/callback", json={"code": subarg}, timeout=15)
            if resp.status_code == 200:
                return "\u2705 Google Drive \u8a8d\u8b49\u6210\u529f\uff01"
            return f"\u274c \u8a8d\u8b49\u5931\u6557\uff1a{resp.text}"

        if op == "logout" or subcmd in ("logout", "out"):
            httpx.post(f"{base}/auth/logout", timeout=5)
            return "\u2705 \u5df2\u767b\u51fa Google Drive\u3002"

        if op == "list" or subcmd in ("list", "ls", "l"):
            n = int(subarg) if subarg.isdigit() else 10
            resp = httpx.get(f"{base}/files?page_size={n}", timeout=15)
            files = resp.json().get("files", [])
            if not files:
                return "\U0001f4c2 \u96f2\u7aef\u786c\u789f\u662f\u7a7a\u7684\u3002"
            lines = [f"\U0001f4c4 {f.get('name')} ({f.get('mimeType', '').split('.')[-1]})" for f in files]
            return "\U0001f4c2 Google Drive \u6a94\u6848\u5217\u8868\uff1a\n" + "\n".join(lines)

        if op == "list" or subcmd in ("search", "q"):
            resp = httpx.post(f"{base}/files/search", json={"query": subarg, "page_size": 10}, timeout=15)
            files = resp.json().get("files", [])
            if not files:
                return f"\U0001f50d \u627e\u4e0d\u5230\u5305\u542b\u300c{subarg}\u300d\u7684\u6a94\u6848\u3002"
            lines = [f"\U0001f4c4 {f.get('name')} ({f.get('mimeType', '').split('.')[-1]})" for f in files]
            return f"\U0001f50d \u641c\u5c0b\u300c{subarg}\u300d\u7d50\u679c\uff1a\n" + "\n".join(lines)

        if op == "sync" or subcmd in ("sync", "download", "dl"):
            resp = httpx.get(f"{base}/files?page_size=10", timeout=15)
            files = resp.json().get("files", [])
            if not files:
                return "\u6c92\u6709\u627e\u5230\u53ef\u4ee5\u540c\u6b65\u7684\u6a94\u6848\u3002"
            resp = httpx.post(f"{base}/files/sync", json={"file_ids": [f["id"] for f in files[:5]]}, timeout=60)
            r = resp.json()
            return (f"\u2705 \u540c\u6b65\u5b8c\u6210\uff01\u4e0b\u8f09\u4e86 {r.get('synced', 0)} \u500b\u6a94\u6848\uff0c"
                    f"\u8df3\u904e {r.get('skipped', 0)} \u500b\uff08\u5df2\u5b58\u5728\uff09\uff0c"
                    f"\u5132\u5165\u8a18\u61b6 {r.get('memorized_count', 0)} \u500b\u3002")

        if op == "analyze" or subcmd in ("analyze", "ana"):
            resp = httpx.post(f"{base}/analyze", json={"limit": 3}, timeout=60)
            r = resp.json()
            _trunc = 1500
            try:
                from core.config_loader import get_angela_config
                _cfg = get_angela_config()
                _trunc = _cfg.get_authority("angela_core", {}).get("state_constants", {}).get("file_content_truncation", 1500)
            except Exception:
                pass
            return f"\U0001f4ca \u5206\u6790\u7d50\u679c\uff1a\n{r.get('analysis', '\u7121\u6cd5\u5206\u6790')[:_trunc]}"

        return (
            "Google Drive \u547d\u4ee4\u7528\u6cd5\uff1a\n"
            "  /drive status     \u2014 \u9023\u63a5\u72c0\u614b\n"
            "  /drive auth       \u2014 \u53d6\u5f97\u6388\u6b0a URL\n"
            "  /drive callback <code>  \u2014 \u7528\u6388\u6b0a\u78bc\u5b8c\u6210\u8a8d\u8b49\n"
            "  /drive list [n]   \u2014 \u5217\u51fa\u6a94\u6848\uff08\u9810\u8a2d10\u500b\uff09\n"
            "  /drive search <q>  \u2014 \u641c\u5c0b\u6a94\u6848\n"
            "  /drive sync        \u2014 \u4e0b\u8f09\u4e26\u5132\u5165\u8a18\u61b6\n"
            "  /drive analyze     \u2014 \u5206\u6790\u6a94\u6848\u5167\u5bb9\n"
            "  /drive logout      \u2014 \u767b\u51fa"
        )

    except httpx.ConnectError:
        return "\u274c \u7121\u6cd5\u9023\u63a5\u5f8c\u7aef\uff0c\u8acb\u5148\u555f\u52d5\u4f3a\u670d\u5668\uff08launch_angela.bat --repl\uff09"
    except Exception as e:
        return f"\u274c Drive \u932f\u8aa4\uff1a{e}"
