"""
ANGELA-MATRIX: [L4-L5] [αβγδ] [A] [L2]
REPL mode: interactive chat loop with uvicorn daemon.
Extracted from main_api_server.py (A3 god module split).

v2 (2026-09-16): Production-grade terminal output.
  - Visual bar indicators for 8D state values
  - Backend health status in /model and /route
  - /ctx subcommands (state, models, memory, config)
  - Actionable hints when backends or config are broken
  - Categorized /help
"""

import asyncio
import logging
import os
import sys
import threading
import time
from typing import Any, Dict, Optional, Tuple

# Config-driven sleep intervals
try:
    from core.system.config.magic_numbers import _get as _cfg_get
except ImportError:
    _cfg_get = lambda key, default=None: default

logger = logging.getLogger(__name__)

# ─── ANSI color helpers ───────────────────────────────────────────


def _supports_color() -> bool:
    """Check if terminal supports ANSI color."""
    if os.getenv("NO_COLOR") or os.getenv("TERM") == "dumb":
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _color(text: str, code: str) -> str:
    """Wrap text in ANSI color if supported."""
    if not _supports_color():
        return text
    return f"\033[{code}m{text}\033[0m"


def _bold(text: str) -> str:
    return _color(text, "1")


def _green(text: str) -> str:
    return _color(text, "32")


def _yellow(text: str) -> str:
    return _color(text, "33")


def _red(text: str) -> str:
    return _color(text, "31")


def _dim(text: str) -> str:
    return _color(text, "2")


def _cyan(text: str) -> str:
    return _color(text, "36")


# ─── Visual helpers ────────────────────────────────────────────────


def _bar(value: float, width: int = 20) -> str:
    """Render a text-based bar with color: [████████░░░░░░░░░░░░] 0.45"""
    clamped = max(0.0, min(1.0, value))
    filled = round(clamped * width)
    empty = width - filled
    bar_char = "█"
    empty_char = "░"
    if _supports_color():
        if clamped >= 0.7:
            bar_colored = _green(bar_char * filled)
        elif clamped >= 0.4:
            bar_colored = _yellow(bar_char * filled)
        else:
            bar_colored = _red(bar_char * filled)
        return f"[{bar_colored}{empty_char * empty}] {clamped:.2f}"
    return f"[{bar_char * filled}{empty_char * empty}] {clamped:.2f}"


def _badge(text: str, ok: bool) -> str:
    """Render a status badge: ✅ text or ❌ text with color."""
    icon = "✅" if ok else "❌"
    if _supports_color():
        colored_text = _green(text) if ok else _red(text)
        return f"{icon} {colored_text}"
    return f"{icon} {text}"


def _hint(message: str) -> str:
    """Render an actionable hint line."""
    if _supports_color():
        return f"  💡 {_yellow(message)}"
    return f"  💡 {message}"


def _section(title: str) -> str:
    """Render a section header with bold."""
    line = f"── {title} {'─' * max(0, 50 - len(title))}"
    return f"\n{_bold(line)}"


# ─── LLM service singleton ─────────────────────────────────────────


def _get_llm_svc():
    """Get the LLM service (synchronous wrapper)."""
    try:
        from services.angela_llm_service import get_llm_service

        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, get_llm_service())
                return future.result()
        return loop.run_until_complete(get_llm_service())
    except Exception as e:
        logger.warning("LLM service unavailable: %s", e, exc_info=True)
        return None


# ═══════════════════════════════════════════════════════════════════
# Entry points
# ═══════════════════════════════════════════════════════════════════


def run_repl_mode() -> None:
    """Execute the run repl mode operation."""
    from core.system.config.network_defaults import DEFAULT_HOST, get_server_bind

    bind_host, bind_port = get_server_bind()
    server_thread = threading.Thread(target=_run_uvicorn_in_thread, daemon=True)
    server_thread.start()
    print(f"[REPL] Backend starting on http://{DEFAULT_HOST}:{bind_port} ...")
    time.sleep(_cfg_get("cli.repl.startup_delay", 3.0))
    asyncio.run(_run_repl())


def _run_uvicorn_in_thread() -> None:
    """Run uvicorn in thread."""
    import uvicorn
    from core.system.config.network_defaults import get_server_bind
    from services.main_api_server import app

    bind_host, bind_port = get_server_bind()
    uvicorn.run(app, host=bind_host, port=bind_port, log_level="warning")


async def _run_repl() -> None:
    """Run repl."""
    from api.lifespan import _get_chat_service

    logging.disable(logging.WARNING)

    print("[REPL] Angela brain initializing...")
    service = await _get_chat_service()
    await service.initialize()

    # ── Boot status banner ──
    _print_boot_status(service)

    loop = asyncio.get_running_loop()
    cmd_history: list[str] = []
    while True:
        try:
            user_input = await loop.run_in_executor(None, lambda: input("\n💬  你: "))
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
                print(f"💬 Angela [{intent_name}]: {response_text}")
                continue

        print("💬 Angela: ", end="", flush=True)
        response = await service.generate_response(text)
        print(getattr(response, "text", response))
        cmd_history.append(text)
        if len(cmd_history) > 100:
            cmd_history = cmd_history[-100:]


def _print_boot_status(service: Any) -> None:
    """Print a concise status summary on REPL startup."""
    print(_section("Boot Status"))

    # LLM
    llm_svc = _get_llm_svc()
    if llm_svc and getattr(llm_svc, "is_available", False):
        active = getattr(llm_svc, "active_backend", None)
        backends = list(getattr(llm_svc, "backends", {}).keys())
        mode = getattr(llm_svc, "llm_mode", "unknown")
        print(f"  LLM:      {_badge(f'{active} (mode={mode})', True)}")
        print(f"            Backends: {backends}")
    else:
        print(f"  LLM:      {_badge('No backend available', False)}")
        print(_hint("Add Ollama: install from https://ollama.ai, then 'ollama pull qwen3.5:0.8b'"))
        print(
            _hint(
                "Or add API key: set OPENAI_API_KEY in .env and deployment.mode: local+llm in llm.default.yaml"
            )
        )

    # Memory
    if hasattr(service, "memory_manager") and service.memory_manager:
        print(f"  Memory:   {_badge('initialized', True)}")
    else:
        print(f"  Memory:   {_badge('not initialized', False)}")
        print(_hint("Install vector DB extras: pip install -e 'apps/backend[vector]'"))

    # State
    try:
        sm = service.state_matrix
        alpha = getattr(sm, "alpha", None)
        energy = alpha.values.get("energy", 0.5) if alpha and hasattr(alpha, "values") else 0.5
        print(f"  State:    {_bar(energy)} (α.energy)")
    except Exception:
        print("  State:    (unavailable)")

    print()


# ═══════════════════════════════════════════════════════════════════
# Command router
# ═══════════════════════════════════════════════════════════════════


def _handle_repl_command(text: str, service: Any, history: list[str]) -> Tuple[str, Optional[str]]:
    """Handle repl command request."""
    parts = text.lstrip("/:")
    tokens = parts.split(maxsplit=1)
    cmd = tokens[0].lower()
    args = tokens[1] if len(tokens) > 1 else ""

    # ── Navigation ──
    if cmd in ("h", "help"):
        return ("system", _build_help_text())

    if cmd in ("c", "clear"):
        return ("system", "\033[2J\033[H")

    if cmd in ("hist", "history"):
        lines = [f"  {i+1}. {h[:60]}" for i, h in enumerate(history[-10:])]
        return ("system", "Recent history:\n" + "\n".join(lines) if lines else "(empty)")

    # ── System info ──
    if cmd in ("s", "state"):
        return ("system", _format_state_snapshot(service))

    if cmd in ("cfg", "config"):
        return ("system", _format_config_summary(service))

    if cmd in ("i", "intent"):
        return ("system", _format_intent_registry())

    if cmd in ("r", "route"):
        return ("system", _format_llm_routing(service))

    # ── Memory ──
    if cmd in ("m", "mem", "memory"):
        return ("system", _format_memory_summary(service, args))

    # ── Context overview with subcommands ──
    if cmd in ("ctx", "context"):
        return ("system", _format_context_overview(service, args))

    # ── Model management ──
    if cmd == "model":
        return ("system", _handle_model_command(args, service))

    # ── Drive ──
    if cmd in ("drive", "gd", "cloud"):
        return ("system", _handle_drive_command(args))

    # ── Tickle ──
    if cmd in ("tickle", "tkl"):
        return ("system", _handle_tickle_command(args))

    # ── Eval ──
    if cmd == "eval":
        return ("system", _handle_eval_command(args))

    return ("unknown", None)


# ═══════════════════════════════════════════════════════════════════
# /help — categorized
# ═══════════════════════════════════════════════════════════════════


def _build_help_text() -> str:
    return """Angela REPL — Command Reference

  📋 System
    /help, /h              Show this help
    /clear, /c             Clear screen
    /history               Recent command history

  🧠 State & Context
    /state, /s             8D state matrix with visual bars
    /ctx                   Full context overview (state + memory + models + config)
    /ctx state             State matrix only
    /ctx models            LLM backends only
    /ctx memory            Memory status only
    /ctx config            Config summary only

  🤖 AI Models
    /model list            List all backends with health status
    /model switch <name>   Switch active backend
    /model stats           Show usage statistics
    /model auto            Enable auto-routing
    /route, /r             LLM routing detail + deployment mode

  🧩 Config & Intents
    /config, /cfg          Config summary (mode, intents, providers, thresholds)
    /intent, /i            Intent registry with keywords

  💾 Memory
    /memory, /m [query]    Search memories (default: recent experiences)

  🔧 Other
    /tickle, /tkl          Tickle reflex system
    /drive, /gd            Google Drive operations
    /eval <expr>           Evaluate a Python expression

  exit / quit             Stop REPL"""


# ═══════════════════════════════════════════════════════════════════
# /state — visual bars
# ═══════════════════════════════════════════════════════════════════


def _format_state_snapshot(service: Any) -> str:
    """Format state snapshot with visual bars."""
    try:
        sm = service.state_matrix
        lines = [_section("8D State Matrix")]

        axes_display = [
            ("α alpha ", "alpha", "energy, comfort, arousal"),
            ("β beta  ", "beta", "focus, curiosity, learning"),
            ("γ gamma ", "gamma", "happiness, trust, anticipation"),
            ("δ delta ", "delta", "bond, trust, attention"),
            ("ε epsln ", "epsilon", "precision, confidence"),
            ("θ theta ", "theta", "novelty, correction urge"),
            ("ζ zeta  ", "zeta", "(reserved)"),
        ]

        for label, axis_name, description in axes_display:
            ax = getattr(sm, axis_name, None)
            if ax and hasattr(ax, "values"):
                vals = ax.values
                # Average all sub-values for the bar
                avg = sum(vals.values()) / len(vals) if vals else 0.0
                detail = ", ".join(f"{k}={v:.2f}" for k, v in list(vals.items())[:4])
                lines.append(f"  {label} {_bar(avg)}  {detail}")
            else:
                lines.append(f"  {label} (no data)")

        # Eta (execution)
        eta = service.eta_state
        if eta:
            lines.append("")
            lines.append(_section("η Eta (Execution)"))
            lines.append(
                f"  exec_count  {_bar(min(eta.execution_count / 100, 1.0))}  count={eta.execution_count}"
            )
            lines.append(f"  success     {_bar(eta.success_rate)}  rate={eta.success_rate:.1%}")
            lines.append(
                f"  drift       {_bar(eta.structural_drift)}  drift={eta.structural_drift:.4f}"
            )

        return "\n".join(lines)
    except Exception as e:
        logger.warning("State snapshot failed: %s", e, exc_info=True)
        return f"State unavailable: {e}"


# ═══════════════════════════════════════════════════════════════════
# /config — rich with warnings
# ═══════════════════════════════════════════════════════════════════


def _format_config_summary(service: Any) -> str:
    """Format config summary with deployment mode and warnings."""
    try:
        cfg = service._angela_config

        lines = [_section("Configuration")]

        # Deployment mode — most important
        deployment = {}
        try:
            deployment = cfg.get_authority("llm", {}).get("deployment", {})
        except Exception:
            pass
        mode = deployment.get("mode", "unknown")
        selection = deployment.get("selection", "available")
        mode_icon = {"local": "🏠", "local+llm": "🔗", "llm": "☁️", "auto": "🤖"}.get(mode, "❓")
        lines.append(f"  Deployment:  {mode_icon} mode={mode}  selection={selection}")

        # Web search
        web_search = {}
        try:
            web_search = cfg.get_authority("llm", {}).get("web_search", {})
        except Exception:
            pass
        ws_enabled = web_search.get("enabled", True)
        ws_provider = web_search.get("provider", "duckduckgo")
        lines.append(f"  Web Search:  {'✅' if ws_enabled else '❌'} {ws_provider}")

        # LLM settings
        try:
            llm_cfg = cfg.get_authority("llm", {}).get("settings", {})
            temp = llm_cfg.get("defaults", {}).get("temperature", 0.7)
            max_tok = llm_cfg.get("defaults", {}).get("max_tokens", 512)
            llm_mode = llm_cfg.get("llm_mode", "standard")
            mem_enh = llm_cfg.get("enable_memory_enhancement", True)
            lines.append(
                f"  LLM:         mode={llm_mode}  temp={temp}  max_tokens={max_tok}  memory_enhance={mem_enh}"
            )
        except Exception:
            pass

        # Backends summary
        backends_cfg = {}
        try:
            backends_cfg = cfg.get_authority("llm", {}).get("backends", {})
        except Exception:
            pass
        if backends_cfg:
            enabled = [
                k
                for k, v in backends_cfg.items()
                if isinstance(v, dict) and v.get("enabled", False)
            ]
            disabled = [
                k
                for k, v in backends_cfg.items()
                if isinstance(v, dict) and not v.get("enabled", True)
            ]
            lines.append(f"  Backends:    {len(enabled)} enabled, {len(disabled)} disabled")
            for bid in enabled:
                b = backends_cfg[bid]
                btype = b.get("type", "?")
                provider = b.get("provider", "?")
                lines.append(f"    ✅ {bid:<22s} type={btype}  provider={provider}")
            for bid in disabled:
                b = backends_cfg[bid]
                provider = b.get("provider", "?")
                lines.append(f"    ⬜ {bid:<22s} (disabled, provider={provider})")

        # Intents
        intents = list(cfg.get_intents().keys())
        lines.append(f"  Intents:     {len(intents)} registered")

        # Thresholds
        try:
            thresholds = cfg.get_complexity_thresholds()
            if thresholds:
                lines.append(f"  Thresholds:  {thresholds}")
        except Exception:
            pass

        # Learned configs
        try:
            from pathlib import Path

            learned_dir = Path(__file__).resolve().parents[2] / "data" / "angela_learned"
            if learned_dir.exists():
                learned_files = list(learned_dir.glob("*.yaml"))
                lines.append(f"  Learned:     {len(learned_files)} file(s)")
        except Exception:
            pass

        # Warnings
        warnings = []
        if mode in ("local+llm", "llm", "auto"):
            # Check if API keys exist
            has_openai = bool(os.getenv("OPENAI_API_KEY"))
            has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
            has_google = bool(os.getenv("GOOGLE_API_KEY"))
            cloud_backends = [
                k
                for k, v in backends_cfg.items()
                if isinstance(v, dict) and v.get("type") == "cloud" and v.get("enabled")
            ]
            if cloud_backends and not any([has_openai, has_anthropic, has_google]):
                warnings.append("⚠️  Cloud backends enabled but no API keys found in environment!")
                warnings.append(
                    _hint("Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY in .env")
                )

        if warnings:
            lines.append("")
            lines.append(_section("Warnings"))
            lines.extend(warnings)

        return "\n".join(lines)
    except Exception as e:
        logger.warning("Config summary failed: %s", e, exc_info=True)
        return f"Config error: {e}"


# ═══════════════════════════════════════════════════════════════════
# /intent — clean table
# ═══════════════════════════════════════════════════════════════════


def _format_intent_registry() -> str:
    """Format intent registry as a clean table."""
    try:
        from core.intent_registry import IntentRegistry

        reg = IntentRegistry()
        lines = [_section("Intent Registry")]

        if not reg.patterns:
            lines.append("  (no patterns registered)")
            return "\n".join(lines)

        # Header
        lines.append(f"  {'Name':<16s} {'Pri':>3s}  Keywords")
        lines.append(f"  {'─'*16} {'─'*3}  {'─'*40}")

        for p in reg.patterns:
            kw = ", ".join(p.keywords[:6])
            if len(p.keywords) > 6:
                kw += f" (+{len(p.keywords) - 6} more)"
            lines.append(f"  {p.name:<16s} {p.priority:>3d}  {kw}")

        lines.append(f"\n  Total: {len(reg.patterns)} intents")
        return "\n".join(lines)
    except Exception as e:
        logger.warning("Intent registry failed: %s", e, exc_info=True)
        return f"Intent registry error: {e}"


# ═══════════════════════════════════════════════════════════════════
# /route — backend detail + health
# ═══════════════════════════════════════════════════════════════════


def _format_llm_routing(service: Any) -> str:
    """Format LLM routing with backend health details."""
    try:
        llm_svc = _get_llm_svc()
        if llm_svc is None:
            lines = [_section("LLM Routing"), "  ❌ LLM service not available"]
            lines.append(_hint("Check if the backend server is running"))
            return "\n".join(lines)

        is_available = getattr(llm_svc, "is_available", False)
        active = getattr(llm_svc, "active_backend", None)
        active_type = getattr(llm_svc, "active_backend_type", None)
        llm_mode = getattr(llm_svc, "llm_mode", "unknown")
        chain = getattr(llm_svc, "_angela_fallback_chain", [])
        backends = getattr(llm_svc, "backends", {})
        stats = getattr(llm_svc, "stats", {})

        lines = [_section("LLM Routing")]
        lines.append(f"  Overall:    {_badge('available', is_available)}")
        lines.append(f"  Mode:       {llm_mode}")
        lines.append(f"  Active:     {active_type.name if active_type else '(none)'}")
        if chain:
            lines.append(f"  Fallback:   {' → '.join(str(c) for c in chain)}")

        # Backend table
        if backends:
            lines.append("")
            lines.append(_section("Registered Backends"))
            lines.append(f"  {'Backend':<24s} {'Type':<8s} {'Status':<10s} {'Active'}")
            lines.append(f"  {'─'*24} {'─'*8} {'─'*10} {'─'*6}")

            for btype, bobj in backends.items():
                name = btype.name if hasattr(btype, "name") else str(btype)
                backend_type = (
                    getattr(bobj, "_config", {}).get("type", "?")
                    if hasattr(bobj, "_config")
                    else "?"
                )
                is_active = active_type is not None and btype == active_type
                marker = " ★" if is_active else ""
                # Try health check
                health = "?"
                try:
                    import asyncio as _aio

                    h = _aio.get_event_loop()
                    if h.is_running():
                        health = "ok"  # skip health check in running loop
                    else:
                        health = "ok" if h.run_until_complete(bobj.check_health()) else "fail"
                except Exception:
                    pass
                status = _badge("active" if is_active else health, health == "ok" or is_active)
                lines.append(f"  {name:<24s} {backend_type:<8s} {status}{marker}")

        # Stats
        if stats:
            lines.append("")
            lines.append(_section("Statistics"))
            for k, v in stats.items():
                lines.append(f"  {k}: {v}")

        # Hints
        lines.append("")
        if not is_available:
            lines.append(_hint("No backend passed health check"))
            lines.append(_hint("For local: ensure Ollama is running (ollama serve)"))
            lines.append(
                _hint(
                    "For cloud: set API key in .env and deployment.mode: local+llm in llm.default.yaml"
                )
            )
        elif llm_mode == "local":
            lines.append(_hint("Running in local-only mode. Cloud backends are gated."))
            lines.append(
                _hint(
                    "To enable cloud: change deployment.mode to 'local+llm' or 'auto' in llm.default.yaml"
                )
            )

        return "\n".join(lines)
    except Exception as e:
        logger.warning("LLM routing failed: %s", e, exc_info=True)
        return f"LLM routing error: {e}"


# ═══════════════════════════════════════════════════════════════════
# /model — table with health
# ═══════════════════════════════════════════════════════════════════


def _handle_model_command(args: str, service: Any) -> str:
    """Handle model command request with rich output."""
    parts = args.strip().split(maxsplit=1)
    subcmd = parts[0].lower() if parts else "list"
    subarg = parts[1] if len(parts) > 1 else ""

    llm_svc = _get_llm_svc()
    if llm_svc is None:
        return "❌ LLM service not available.\n" + _hint("Check backend server status")

    backends = getattr(llm_svc, "backends", {})
    active = getattr(llm_svc, "active_backend", None)
    active_type = getattr(llm_svc, "active_backend_type", None)

    # ── /model list ──
    if subcmd in ("list", "ls", "l", ""):
        lines = [_section("Available Models")]

        if not backends:
            lines.append("  (no backends registered)")
            lines.append(_hint("Check deployment.mode in llm.default.yaml"))
            lines.append(_hint("For local: ensure Ollama is running"))
            lines.append(_hint("For cloud: set API key in .env"))
            return "\n".join(lines)

        lines.append(f"  {'#':<4s} {'Backend':<24s} {'Type':<8s} {'Status':<12s}")
        lines.append(f"  {'─'*4} {'─'*24} {'─'*8} {'─'*12}")

        idx = 0
        for btype, bobj in backends.items():
            idx += 1
            name = btype.name if hasattr(btype, "name") else str(btype)
            is_active = active_type is not None and btype == active_type
            marker = " ★" if is_active else "  "
            health = "ok"
            try:
                import asyncio as _aio

                h = _aio.get_event_loop()
                if not h.is_running():
                    health = "ok" if h.run_until_complete(bobj.check_health()) else "fail"
            except Exception:
                pass
            status_str = "active" if is_active else health
            lines.append(f"  {idx:<4d} {name:<24s} {'local':<8s} {status_str:<12s}{marker}")

        lines.append("\n  ★ = active backend")
        lines.append(f"  Total: {len(backends)} registered, 1 active")
        return "\n".join(lines)

    # ── /model stats ──
    if subcmd in ("stats", "s"):
        stats = getattr(llm_svc, "stats", {})
        if not stats:
            return "No statistics available yet. Statistics are recorded after LLM calls."
        lines = [_section("LLM Statistics")]
        for k, v in stats.items():
            lines.append(f"  {k}: {v}")
        return "\n".join(lines)

    # ── /model switch ──
    if subcmd in ("switch", "sw", "set"):
        if not subarg:
            available = (
                [btype.name for btype in backends.keys()] if hasattr(backends, "keys") else []
            )
            lines = ["Usage: /model switch <name>"]
            lines.append(f"Available: {available}")
            return "\n".join(lines)

        backend_key = subarg.strip()
        for btype, bobj in backends.items():
            name = btype.name if hasattr(btype, "name") else str(btype)
            if backend_key.lower() in name.lower():
                llm_svc.active_backend = bobj
                llm_svc.active_backend_type = btype
                return f"✅ Switched to {name}"
        available = [
            btype.name if hasattr(btype, "name") else str(btype) for btype in backends.keys()
        ]
        return f"❌ Model '{backend_key}' not found.\nAvailable: {available}"

    # ── /model auto ──
    if subcmd in ("auto", "a"):
        llm_svc.llm_mode = "auto"
        return "✅ Auto-routing enabled. Backend will be selected per-request based on task complexity."

    return "Usage: /model [list|stats|switch <name>|auto]\n\nSubcommands:\n  list (default) — Show all backends with health\n  stats           — Usage statistics\n  switch <name>   — Switch active backend\n  auto            — Enable auto-routing mode"


# ═══════════════════════════════════════════════════════════════════
# /ctx — subcommands
# ═══════════════════════════════════════════════════════════════════


def _format_context_overview(service: Any, args: str) -> str:
    """Format context overview with subcommands."""
    subcmd = args.strip().lower() if args else ""

    if subcmd == "state":
        return _format_state_snapshot(service)
    if subcmd == "models":
        return _format_llm_routing(service)
    if subcmd == "memory":
        return _format_memory_summary(service, "")
    if subcmd == "config":
        return _format_config_summary(service)

    # Full overview
    lines = [_section("Context Overview")]

    # 1) State
    try:
        sm = service.state_matrix
        alpha = getattr(sm, "alpha", None)
        beta = getattr(sm, "beta", None)
        gamma = getattr(sm, "gamma", None)
        energy = alpha.values.get("energy", 0.5) if alpha and hasattr(alpha, "values") else 0.5
        focus = beta.values.get("focus", 0.5) if beta and hasattr(beta, "values") else 0.5
        happy = gamma.values.get("happiness", 0.5) if gamma and hasattr(gamma, "values") else 0.5

        lines.append(
            f"  State:     energy {_bar(energy)}  focus {_bar(focus)}  happy {_bar(happy)}"
        )
    except Exception:
        lines.append("  State:     (unavailable)")

    # 2) Memory
    try:
        if hasattr(service, "memory_manager") and service.memory_manager:
            loop = asyncio.new_event_loop()
            results = loop.run_until_complete(
                service.memory_manager.query_core_memory(keywords=["experience"], limit=5)
            )
            loop.close()
            lines.append(f"  Memory:    ✅ initialized — {len(results)} recent memories queryable")
        else:
            lines.append("  Memory:    ❌ not initialized")
            lines.append(_hint("Install extras: pip install -e 'apps/backend[vector]'"))
    except Exception:
        lines.append("  Memory:    (error)")

    # 3) LLM
    try:
        llm_svc = _get_llm_svc()
        if llm_svc and getattr(llm_svc, "is_available", False):
            active_type = getattr(llm_svc, "active_backend_type", None)
            name = active_type.name if active_type else "unknown"
            n_backends = len(getattr(llm_svc, "backends", {}))
            llm_mode = getattr(llm_svc, "llm_mode", "unknown")
            lines.append(f"  LLM:       ✅ active={name}  backends={n_backends}  mode={llm_mode}")
        else:
            lines.append("  LLM:       ❌ no backend available")
            lines.append(_hint("See /model list for details"))
    except Exception:
        lines.append("  LLM:       (error)")

    # 4) Config
    try:
        cfg = service._angela_config
        deployment = {}
        try:
            deployment = cfg.get_authority("llm", {}).get("deployment", {})
        except Exception:
            pass
        mode = deployment.get("mode", "unknown")
        intents = list(cfg.get_intents().keys())
        lines.append(f"  Config:    mode={mode}  intents={len(intents)}")
    except Exception:
        lines.append("  Config:    (unavailable)")

    lines.append("")
    lines.append("Subcommands: /ctx state | /ctx models | /ctx memory | /ctx config")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# /memory
# ═══════════════════════════════════════════════════════════════════


def _format_memory_summary(service: Any, search: str) -> str:
    """Format memory summary."""
    try:
        if hasattr(service, "memory_manager") and service.memory_manager:
            loop = asyncio.new_event_loop()
            results = loop.run_until_complete(
                service.memory_manager.query_core_memory(
                    keywords=[search] if search else ["experience"], limit=8
                )
            )
            loop.close()
            if not results:
                return "(no memories found)"

            lines = [
                _section(
                    f"Memory ({len(results)} results"
                    + (f', query="{search}"' if search else ", recent experiences")
                    + ")"
                )
            ]

            for i, r in enumerate(results):
                content = r.get("content", "")[:100]
                cat = r.get("category", "?")
                importance = r.get("importance", 0)
                score = r.get("score", r.get("similarity", 0))
                lines.append(f"  [{i+1}] {cat:<12s}  imp={importance:.2f}  sim={score:.2f}")
                lines.append(f"      {content}")

            lines.append("\n  💡 Usage: /memory <keyword> to search")
            return "\n".join(lines)
        else:
            lines = [_section("Memory")]
            lines.append("  ❌ Memory manager not initialized")
            lines.append(_hint("Install vector DB extras: pip install -e 'apps/backend[vector]'"))
            return "\n".join(lines)
    except Exception as e:
        logger.warning("Memory summary failed: %s", e, exc_info=True)
        return f"Memory error: {e}"


# ═══════════════════════════════════════════════════════════════════
# /eval
# ═══════════════════════════════════════════════════════════════════


def _handle_eval_command(args: str) -> str:
    """Evaluate a Python expression."""
    if not args:
        return "Usage: /eval <python-expression>\nExample: /eval 2 + 2"
    try:
        result = eval(args)
        return f"→ {result}"
    except Exception as e:
        return f"Eval error: {e}"


# ═══════════════════════════════════════════════════════════════════
# /tickle
# ═══════════════════════════════════════════════════════════════════


def _handle_tickle_command(args: str) -> str:
    """Handle tickle command request."""
    parts = args.strip().split()
    if not parts:
        from core.life.tickle_reflex_system import get_reflex_system

        reflex = get_reflex_system()
        all_parts = reflex.get_all_body_parts()
        sensitive = reflex.get_sensitive_parts()
        thresholds = reflex.get_intensity_thresholds()
        return (
            f"Tickle Reflex System\nParts: {all_parts}\nSensitive: {sensitive}\n"
            f"Thresholds: {thresholds}\n\nUsage: /tickle <part> [intensity 0-1]"
        )

    body_part = parts[0]
    intensity = float(parts[1]) if len(parts) > 1 else 0.5

    from core.life.tickle_reflex_system import get_reflex_system

    reflex = get_reflex_system()

    async def run_tickles() -> Dict[str, Any]:
        return await reflex.trigger_tickles(
            body_part=body_part, intensity=intensity, duration_seconds=1.0, origin="REPL"
        )

    loop = asyncio.new_event_loop()
    try:
        result: Dict[str, Any] = loop.run_until_complete(run_tickles())
    finally:
        loop.close()

    phase1 = result.get("phase1", {})
    phase2 = result.get("phase2", {})
    anim = phase1.get("animation", {})
    return (
        f"[Tickle] {body_part} intensity={intensity:.1f}\n"
        f"Level: {result.get('intensity_level', '?')}\n"
        f"Output: {phase1.get('output_mode', '?')}\n"
        f"Animation: {anim.get('motion_name', '?')} ({anim.get('duration_ms', 0)}ms)\n"
        f"Expression: {anim.get('expression', '?')}\n"
        f"Phase2 triggered: {phase2.get('triggered', False)}\n"
        f"Elapsed: {result.get('elapsed_ms', 0)}ms"
    )


# ═══════════════════════════════════════════════════════════════════
# /drive — Google Drive (unchanged)
# ═══════════════════════════════════════════════════════════════════

_DRIVE_HANDLERS: Dict[str, Any] = {}


def _resolve_drive_op(cmd: str, ops: Dict[str, Any]) -> Optional[str]:
    for op_name, op_cfg in ops.items():
        if cmd in op_cfg.get("aliases", []):
            return op_name
    return None


def _drive_status(subarg: str, base: str) -> str:
    import httpx

    resp = httpx.get(f"{base}/status", timeout=10)
    d = resp.json()
    auth = d.get("authenticated", False)
    quota = d.get("quota", {})
    lines = [
        f"Google Drive: {'✅ 已認證' if auth else '❌ 未認證'}",
        f"  用戶: {quota.get('user', 'N/A')}",
        f"  已用: {quota.get('used', 'N/A')} / {quota.get('total', 'N/A')}",
        f"  狀態: {d.get('status', 'unknown')}",
    ]
    return "\n".join(lines)


def _drive_auth(subarg: str, base: str) -> str:
    import httpx

    if not subarg or subarg == "url":
        resp = httpx.get(f"{base}/auth/url", timeout=10)
        url = resp.json().get("url", "")
        return f"授權 URL：\n{url}\n\n請用瀏覽器打開這個鏈結，授權後把回傳的 code 貼給我。"
    resp = httpx.post(f"{base}/auth/callback", json={"code": subarg}, timeout=15)
    if resp.status_code == 200:
        return "✅ Google Drive 認證成功！"
    return f"❌ 認證失敗：{resp.text}"


def _drive_logout(subarg: str, base: str) -> str:
    import httpx

    httpx.post(f"{base}/auth/logout", timeout=5)
    return "✅ 已登出 Google Drive。"


def _drive_list(subarg: str, base: str) -> str:
    import httpx

    n = int(subarg) if subarg.isdigit() else 10
    resp = httpx.get(f"{base}/files?page_size={n}", timeout=15)
    files = resp.json().get("files", [])
    if not files:
        return "📂 雲端硬碟是空的。"
    lines = [f"📄 {f.get('name')} ({f.get('mimeType', '').split('.')[-1]})" for f in files]
    return "📂 Google Drive 檔案列表：\n" + "\n".join(lines)


def _drive_search(subarg: str, base: str) -> str:
    import httpx

    resp = httpx.post(f"{base}/files/search", json={"query": subarg, "page_size": 10}, timeout=15)
    files = resp.json().get("files", [])
    if not files:
        return f"🔍 找不到包含「{subarg}」的檔案。"
    lines = [f"📄 {f.get('name')} ({f.get('mimeType', '').split('.')[-1]})" for f in files]
    return f"🔍 搜尋「{subarg}」結果：\n" + "\n".join(lines)


def _drive_sync(subarg: str, base: str) -> str:
    import httpx

    resp = httpx.get(f"{base}/files?page_size=10", timeout=15)
    files = resp.json().get("files", [])
    if not files:
        return "沒有找到可以同步的檔案。"
    resp = httpx.post(
        f"{base}/files/sync", json={"file_ids": [f["id"] for f in files[:5]]}, timeout=60
    )
    r = resp.json()
    return (
        f"✅ 同步完成！下載了 {r.get('synced', 0)} 個檔案，"
        f"跳過 {r.get('skipped', 0)} 個（已存在），"
        f"儲入記憶 {r.get('memorized_count', 0)} 個。"
    )


def _drive_analyze(subarg: str, base: str) -> str:
    import httpx
    from core.config_loader import get_angela_config

    resp = httpx.post(f"{base}/analyze", json={"limit": 3}, timeout=60)
    r = resp.json()
    trunc = 1500
    try:
        cfg = get_angela_config()
        trunc = (
            cfg.get_authority("angela_core", {})
            .get("state_constants", {})
            .get("file_content_truncation", 1500)
        )
    except Exception as e:
        logger.warning("Failed to get config for truncation: %s", e, exc_info=True)
    return f"📊 分析結果：\n{r.get('analysis', '無法分析')[:trunc]}"


_DRIVE_HANDLERS.update(
    {
        "status": _drive_status,
        "s": _drive_status,
        "auth": _drive_auth,
        "a": _drive_auth,
        "callback": _drive_auth,
        "cb": _drive_auth,
        "logout": _drive_logout,
        "out": _drive_logout,
        "list": _drive_list,
        "ls": _drive_list,
        "l": _drive_list,
        "search": _drive_search,
        "q": _drive_search,
        "sync": _drive_sync,
        "download": _drive_sync,
        "dl": _drive_sync,
        "analyze": _drive_analyze,
        "ana": _drive_analyze,
    }
)

_DRIVE_HELP = (
    "Google Drive 命令用法：\n"
    "  /drive status     — 連接狀態\n"
    "  /drive auth       — 取得授權 URL\n"
    "  /drive callback <code>  — 用授權碼完成認證\n"
    "  /drive list [n]   — 列出檔案（預設10個）\n"
    "  /drive search <q>  — 搜尋檔案\n"
    "  /drive sync        — 下載並儲入記憶\n"
    "  /drive analyze     — 分析檔案內容\n"
    "  /drive logout      — 登出"
)


def _handle_drive_command(args: str) -> str:
    """Handle drive command request."""
    import httpx
    from core.config_loader import get_angela_config
    from core.system.config.network_defaults import (
        DEFAULT_HOST,
        get_server_bind,
    )

    parts = args.strip().split(maxsplit=1)
    subcmd = parts[0].lower() if parts else "status"
    subarg = parts[1] if len(parts) > 1 else ""

    ops = get_angela_config().get_drive_all_operations()
    op = _resolve_drive_op(subcmd, ops)

    key = op or subcmd
    handler = _DRIVE_HANDLERS.get(key)
    if handler is None:
        return _DRIVE_HELP

    base = os.getenv(
        "ANGELA_DRIVE_API_URL",
        f"http://{DEFAULT_HOST}:{get_server_bind()[1]}/api/v1/drive",
    )
    try:
        result = handler(subarg, base)
        return str(result) if result is not None else ""
    except httpx.ConnectError:
        return "❌ 無法連接後端，請先啟動伺服器（launch_angela.bat --repl）"
    except Exception as e:
        return f"❌ Drive 錯誤：{e}"
