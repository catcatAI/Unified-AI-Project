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
from typing import Any, Dict, List, Optional, Tuple

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

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(get_llm_service())
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, get_llm_service())
            return future.result()
    except Exception as e:
        logger.warning("LLM service unavailable: %s", e, exc_info=True)
        return None


# ═══════════════════════════════════════════════════════════════════
# Entry points
# ═══════════════════════════════════════════════════════════════════


def _response_text(response: Any) -> str:
    if isinstance(response, dict):
        value = response.get("text") or response.get("response")
        if value:
            return str(value)
    value = getattr(response, "text", response)
    return str(value)


def run_repl_mode() -> None:
    """Execute the run repl mode operation."""
    os.environ.setdefault("ANGELA_REPL_MODE", "1")
    try:
        asyncio.run(_run_repl())
    except KeyboardInterrupt:
        return


def _build_uvicorn_server() -> Any:
    import uvicorn
    from core.system.config.network_defaults import get_server_bind
    from services.main_api_server import app

    bind_host, bind_port = get_server_bind()
    config = uvicorn.Config(app, host=bind_host, port=bind_port, log_level="warning")
    return uvicorn.Server(config)


async def _wait_for_server(server: Any, server_task: asyncio.Task[Any]) -> None:
    timeout = float(_cfg_get("cli.repl.startup_timeout", 90.0))
    deadline = time.monotonic() + timeout
    while not server.started:
        if server_task.done():
            await server_task
            raise RuntimeError("REPL backend exited before becoming ready")
        if time.monotonic() >= deadline:
            raise TimeoutError(f"REPL backend startup timed out after {timeout:.0f}s")
        await asyncio.sleep(0.05)


async def _read_repl_input(server_task: asyncio.Task[Any]) -> Optional[str]:
    loop = asyncio.get_running_loop()
    future: asyncio.Future[Optional[str]] = loop.create_future()

    def deliver(value: Optional[str]) -> None:
        if not future.done():
            future.set_result(value)

    def read_input() -> None:
        try:
            value: Optional[str] = input("\n💬  你: ")
        except (EOFError, KeyboardInterrupt):
            value = None
        if not loop.is_closed():
            loop.call_soon_threadsafe(deliver, value)

    threading.Thread(target=read_input, daemon=True).start()
    done, _ = await asyncio.wait(
        {future, server_task},
        return_when=asyncio.FIRST_COMPLETED,
    )
    if server_task in done:
        future.cancel()
        await server_task
        return None
    return future.result()


async def _run_repl() -> None:
    from api.lifespan import _get_chat_service

    server = _build_uvicorn_server()
    server_task = asyncio.create_task(server.serve(), name="REPL-Uvicorn")
    # The REPL uses the SAME chat pipeline as the HTTP route, so execution
    # gating, agent routing and session memory behave identically. Calling
    # ChatService directly previously bypassed ExecutionGate entirely (the model
    # answered "Done!" for actions that never ran).
    from api.routes.chat_routes import _handle_chat_request

    repl_session_id = f"repl::{os.getpid()}"
    repl_history: list[Dict[str, str]] = []
    try:
        bind_host, bind_port = server.config.host, server.config.port
        print(f"[REPL] Backend starting on http://{bind_host}:{bind_port} ...")
        await _wait_for_server(server, server_task)

        print("[REPL] Angela brain initializing...")
        service = await _get_chat_service()
        _print_boot_status(service)

        cmd_history: list[str] = []
        while True:
            user_input = await _read_repl_input(server_task)
            if user_input is None:
                print("\n[REPL] Good bye!")
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
            response = await _handle_chat_request(
                user_message=text,
                user_name="user",
                history=list(repl_history),
                session_id=repl_session_id,
                origin="repl",
                extra_context={"conversation_path": "repl"},
            )
            print(_response_text(response))
            repl_history.append({"role": "user", "content": text})
            repl_history.append(
                {
                    "role": "assistant",
                    "content": _response_text(response),
                }
            )
            if len(repl_history) > 40:
                repl_history = repl_history[-40:]
            cmd_history.append(text)
            if len(cmd_history) > 100:
                cmd_history = cmd_history[-100:]
    finally:
        server.should_exit = True
        await server_task


def _print_boot_status(service: Any) -> None:
    """Print a concise status summary on REPL startup."""
    print(_section("Boot Status"))

    # LLM
    llm_svc = _get_llm_svc()
    if llm_svc and getattr(llm_svc, "is_available", False):
        active = getattr(llm_svc, "active_backend", None)
        active_name = (
            getattr(active, "name", None) or getattr(active, "model", None) or type(active).__name__
        )
        backends = list(getattr(llm_svc, "backends", {}).keys())
        mode = getattr(llm_svc, "llm_mode", "unknown")
        print(f"  LLM:      {_badge(f'{active_name} (mode={mode})', True)}")
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
    memory_backend = getattr(service, "_ham_memory", None) or getattr(
        service, "_vector_store", None
    )
    if memory_backend:
        print(f"  Memory:   {_badge('initialized', True)}")
    else:
        print(f"  Memory:   {_badge('not initialized', False)}")
        print(_hint("Install vector DB extras: pip install -e 'apps/backend[vector]'"))

    # State
    try:
        from api.lifespan import get_digital_life

        sm = getattr(get_digital_life(), "state_matrix", None)
        alpha = getattr(sm, "alpha", None)
        energy = alpha.values.get("energy", 0.5) if alpha and hasattr(alpha, "values") else 0.5
        print(f"  State:    {_bar(energy)} (α.energy)")
    except Exception:
        print("  State:    (unavailable)")

    print()


# ═══════════════════════════════════════════════════════════════════
# Command router
# ═══════════════════════════════════════════════════════════════════


def _repl_nav_command(cmd: str, history: list[str]) -> Optional[Tuple[str, Optional[str]]]:
    """Navigation: /help, /clear, /history. None = not this group."""
    if cmd in ("h", "help"):
        return ("system", _build_help_text())

    if cmd in ("c", "clear"):
        return ("system", "\033[2J\033[H")

    if cmd in ("hist", "history"):
        lines = [f"  {i+1}. {h[:60]}" for i, h in enumerate(history[-10:])]
        return ("system", "Recent history:\n" + "\n".join(lines) if lines else "(empty)")

    return None


def _repl_info_command(cmd: str, service: Any) -> Optional[Tuple[str, Optional[str]]]:
    """System info: /state, /config, /intent, /route. None = not this group."""
    if cmd in ("s", "state"):
        return ("system", _format_state_snapshot(service))

    if cmd in ("cfg", "config"):
        return ("system", _format_config_summary(service))

    if cmd in ("i", "intent"):
        return ("system", _format_intent_registry())

    if cmd in ("r", "route"):
        return ("system", _format_llm_routing(service))

    return None


def _repl_tool_command(
    cmd: str, args: str, service: Any
) -> Optional[Tuple[str, Optional[str]]]:
    """Tool commands: /memory, /context, /model, /drive, /tickle, /eval.
    None = not this group."""
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

    return None


def _handle_repl_command(text: str, service: Any, history: list[str]) -> Tuple[str, Optional[str]]:
    """Handle repl command request."""
    parts = text.lstrip("/:")
    tokens = parts.split(maxsplit=1)
    cmd = tokens[0].lower()
    args = tokens[1] if len(tokens) > 1 else ""

    # ── Navigation ──
    nav = _repl_nav_command(cmd, history)
    if nav is not None:
        return nav

    # ── System info ──
    info = _repl_info_command(cmd, service)
    if info is not None:
        return info

    # ── Tools ──
    tool = _repl_tool_command(cmd, args, service)
    if tool is not None:
        return tool

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

  🧰 Hardware & Agents
    EDA / AI card       Natural-language requests route to the eda_agent

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


def _cfg_walk(service: Any, *keys: str, default=None) -> Any:
    """Safely walk nested config path, returning default on any error."""
    cfg = service._angela_config
    cur = cfg
    for key in keys:
        try:
            cur = cur.get(key) if isinstance(cur, dict) else getattr(cur, key, None)
        except Exception:
            logger.debug("repl: config key %r unavailable", key, exc_info=True)
            return default
    return cur


def _format_deployment_line(cfg: Any) -> tuple:
    """Format the deployment mode line and return (line, mode)."""
    try:
        deployment = cfg.get_authority("llm", {}).get("deployment", {})
    except Exception:
        deployment = {}
        logger.debug("repl: deployment config unavailable", exc_info=True)
    mode = deployment.get("mode", "unknown")
    selection = deployment.get("selection", "available")
    mode_icon = {"local": "🏠", "local+llm": "🔗", "llm": "☁️", "auto": "🤖"}.get(mode, "❓")
    line = f"  Deployment:  {mode_icon} mode={mode}  selection={selection}"
    return (line, mode)


def _format_web_search_line(cfg: Any) -> str:
    """Format web search status line."""
    try:
        web_search = cfg.get_authority("llm", {}).get("web_search", {})
    except Exception:
        web_search = {}
        logger.debug("repl: web_search config unavailable", exc_info=True)
    ws_enabled = web_search.get("enabled", True)
    ws_provider = web_search.get("provider", "duckduckgo")
    return f"  Web Search:  {'✅' if ws_enabled else '❌'} {ws_provider}"


def _format_llm_line(cfg: Any) -> Optional[str]:
    """Format LLM settings line, or None if unavailable."""
    try:
        llm_cfg = cfg.get_authority("llm", {}).get("settings", {})
        defaults = llm_cfg.get("defaults", {})
        temp = defaults.get("temperature", 0.7)
        max_tok = defaults.get("max_tokens", 512)
        llm_mode = llm_cfg.get("llm_mode", "standard")
        mem_enh = cfg.get_authority("llm", {}).get("enable_memory_enhancement", True)
        return (
            f"  LLM:         mode={llm_mode}  temp={temp}  "
            f"max_tokens={max_tok}  memory_enhance={mem_enh}"
        )
    except Exception:
        logger.debug("repl: LLM settings config unavailable", exc_info=True)
        return None


def _format_backends_line(cfg: Any) -> list:
    """Format backends summary lines."""
    try:
        backends_cfg = cfg.get_authority("llm", {}).get("backends", {})
    except Exception:
        backends_cfg = {}
        logger.debug("repl: backends config unavailable", exc_info=True)
    if not backends_cfg:
        return []
    lines = []
    enabled = [
        k for k, v in backends_cfg.items()
        if isinstance(v, dict) and v.get("enabled", False)
    ]
    disabled = [
        k for k, v in backends_cfg.items()
        if isinstance(v, dict) and not v.get("enabled", True)
    ]
    lines.append(f"  Backends:    {len(enabled)} enabled, {len(disabled)} disabled")
    for bid in enabled:
        b = backends_cfg[bid]
        lines.append(f"    ✅ {bid:<22s} type={b.get('type', '?')}  provider={b.get('provider', '?')}")
    for bid in disabled:
        b = backends_cfg[bid]
        lines.append(f"    ⬜ {bid:<22s} (disabled, provider={b.get('provider', '?')})")
    return lines


def _format_thresholds_line(cfg: Any) -> Optional[str]:
    """Format complexity thresholds line, or None if unavailable."""
    try:
        thresholds = cfg.get_complexity_thresholds()
        if thresholds:
            return f"  Thresholds:  {thresholds}"
    except Exception:
        logger.debug("repl: complexity thresholds unavailable", exc_info=True)
    return None


def _format_learned_line() -> Optional[str]:
    """Format learned config scan line, or None if unavailable."""
    try:
        from pathlib import Path
        learned_dir = Path(__file__).resolve().parents[2] / "data" / "angela_learned"
        if learned_dir.exists():
            n = len(list(learned_dir.glob("*.yaml")))
            return f"  Learned:     {n} file(s)"
    except Exception:
        logger.debug("repl: learned-config scan failed", exc_info=True)
    return None


def _collect_warnings(mode: str, backends_cfg: dict) -> list:
    """Collect config warnings for cloud backends without API keys."""
    warnings: list = []
    if mode not in ("local+llm", "llm", "auto"):
        return warnings
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_google = bool(os.getenv("GOOGLE_API_KEY"))
    cloud_backends = [
        k for k, v in backends_cfg.items()
        if isinstance(v, dict) and v.get("type") == "cloud" and v.get("enabled")
    ]
    if cloud_backends and not any([has_openai, has_anthropic, has_google]):
        warnings.append("⚠️  Cloud backends enabled but no API keys found in environment!")
        warnings.append(
            _hint("Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY in .env")
        )
    return warnings


def _format_config_summary(service: Any) -> str:
    """Format config summary with deployment mode and warnings."""
    try:
        cfg = service._angela_config

        lines = [_section("Configuration")]

        dep_line, mode = _format_deployment_line(cfg)
        lines.append(dep_line)
        lines.append(_format_web_search_line(cfg))
        llm_line = _format_llm_line(cfg)
        if llm_line:
            lines.append(llm_line)
        lines.extend(_format_backends_line(cfg))

        # Intents
        intents = list(cfg.get_intents().keys())
        lines.append(f"  Intents:     {len(intents)} registered")

        thr = _format_thresholds_line(cfg)
        if thr:
            lines.append(thr)

        learned = _format_learned_line()
        if learned:
            lines.append(learned)

        # Warnings
        try:
            backends_cfg = cfg.get_authority("llm", {}).get("backends", {})
        except Exception:
            backends_cfg = {}
        warnings = _collect_warnings(mode, backends_cfg)
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


def _llm_routing_overview(llm_svc: Any) -> List[str]:
    """Format the overview section (overall/mode/active/fallback)."""
    is_available = getattr(llm_svc, "is_available", False)
    active_type = getattr(llm_svc, "active_backend_type", None)
    llm_mode = getattr(llm_svc, "llm_mode", "unknown")
    chain = getattr(llm_svc, "_angela_fallback_chain", [])

    lines = [_section("LLM Routing")]
    lines.append(f"  Overall:    {_badge('available', is_available)}")
    lines.append(f"  Mode:       {llm_mode}")
    lines.append(f"  Active:     {active_type.name if active_type else '(none)'}")
    if chain:
        lines.append(f"  Fallback:   {' → '.join(str(c) for c in chain)}")
    return lines


def _llm_backend_health(bobj: Any) -> str:
    """Best-effort health string for one backend."""
    health = "?"
    try:
        import asyncio as _aio

        try:
            _aio.get_running_loop()
        except RuntimeError:
            health = "ok" if _aio.run(bobj.check_health()) else "fail"
        else:
            health = "ok"  # skip health check in running loop
    except Exception:
        logger.debug("repl: backend health check failed", exc_info=True)
    return health


def _llm_backend_table(llm_svc: Any) -> List[str]:
    """Format the registered-backends table section."""
    backends = getattr(llm_svc, "backends", {})
    active_type = getattr(llm_svc, "active_backend_type", None)
    if not backends:
        return []

    lines = ["", _section("Registered Backends")]
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
        health = _llm_backend_health(bobj)
        status = _badge("active" if is_active else health, health == "ok" or is_active)
        lines.append(f"  {name:<24s} {backend_type:<8s} {status}{marker}")
    return lines


def _llm_stats_section(llm_svc: Any) -> List[str]:
    """Format the statistics section."""
    stats = getattr(llm_svc, "stats", {})
    if not stats:
        return []
    lines = ["", _section("Statistics")]
    for k, v in stats.items():
        lines.append(f"  {k}: {v}")
    return lines


def _llm_hints(llm_svc: Any) -> List[str]:
    """Format trailing hints based on availability/mode."""
    is_available = getattr(llm_svc, "is_available", False)
    llm_mode = getattr(llm_svc, "llm_mode", "unknown")
    lines = [""]
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
    return lines


def _format_llm_routing(service: Any) -> str:
    """Format LLM routing with backend health details."""
    try:
        llm_svc = _get_llm_svc()
        if llm_svc is None:
            lines = [_section("LLM Routing"), "  ❌ LLM service not available"]
            lines.append(_hint("Check if the backend server is running"))
            return "\n".join(lines)

        lines = _llm_routing_overview(llm_svc)
        lines += _llm_backend_table(llm_svc)
        lines += _llm_stats_section(llm_svc)
        lines += _llm_hints(llm_svc)

        return "\n".join(lines)
    except Exception as e:
        logger.warning("LLM routing failed: %s", e, exc_info=True)
        return f"LLM routing error: {e}"


# ═══════════════════════════════════════════════════════════════════
# /model — table with health
# ═══════════════════════════════════════════════════════════════════


def _handle_model_list(backends: Any, active_type: Any) -> str:
    """Format /model list output with backend health checks."""
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

            try:
                _aio.get_running_loop()
            except RuntimeError:
                health = "ok" if _aio.run(bobj.check_health()) else "fail"
        except Exception:
            logger.debug("repl: local backend health check failed", exc_info=True)
        status_str = "active" if is_active else health
        lines.append(f"  {idx:<4d} {name:<24s} {'local':<8s} {status_str:<12s}{marker}")

    lines.append("\n  ★ = active backend")
    lines.append(f"  Total: {len(backends)} registered, 1 active")
    return "\n".join(lines)


def _handle_model_stats(llm_svc: Any) -> str:
    """Format /model stats output."""
    stats = getattr(llm_svc, "stats", {})
    if not stats:
        return "No statistics available yet. Statistics are recorded after LLM calls."
    lines = [_section("LLM Statistics")]
    for k, v in stats.items():
        lines.append(f"  {k}: {v}")
    return "\n".join(lines)


def _handle_model_switch(llm_svc: Any, backends: Any, subarg: str) -> str:
    """Handle /model switch command."""
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


def _handle_model_command(args: str, service: Any) -> str:
    """Handle model command request with rich output."""
    parts = args.strip().split(maxsplit=1)
    subcmd = parts[0].lower() if parts else "list"
    subarg = parts[1] if len(parts) > 1 else ""

    llm_svc = _get_llm_svc()
    if llm_svc is None:
        return "❌ LLM service not available.\n" + _hint("Check backend server status")

    backends = getattr(llm_svc, "backends", {})
    active_type = getattr(llm_svc, "active_backend_type", None)

    # ── /model list ──
    if subcmd in ("list", "ls", "l", ""):
        return _handle_model_list(backends, active_type)

    # ── /model stats ──
    if subcmd in ("stats", "s"):
        return _handle_model_stats(llm_svc)

    # ── /model switch ──
    if subcmd in ("switch", "sw", "set"):
        return _handle_model_switch(llm_svc, backends, subarg)

    # ── /model auto ──
    if subcmd in ("auto", "a"):
        llm_svc.llm_mode = "auto"
        return "✅ Auto-routing enabled. Backend will be selected per-request based on task complexity."

    return "Usage: /model [list|stats|switch <name>|auto]\n\nSubcommands:\n  list (default) — Show all backends with health\n  stats           — Usage statistics\n  switch <name>   — Switch active backend\n  auto            — Enable auto-routing mode"


# ═══════════════════════════════════════════════════════════════════
# /ctx — subcommands
# ═══════════════════════════════════════════════════════════════════


def _format_ctx_state_line(service: Any) -> str:
    """Format state matrix line for /ctx overview."""
    try:
        sm = service.state_matrix
        alpha = getattr(sm, "alpha", None)
        beta = getattr(sm, "beta", None)
        gamma = getattr(sm, "gamma", None)
        energy = alpha.values.get("energy", 0.5) if alpha and hasattr(alpha, "values") else 0.5
        focus = beta.values.get("focus", 0.5) if beta and hasattr(beta, "values") else 0.5
        happy = gamma.values.get("happiness", 0.5) if gamma and hasattr(gamma, "values") else 0.5
        return f"  State:     energy {_bar(energy)}  focus {_bar(focus)}  happy {_bar(happy)}"
    except Exception:
        return "  State:     (unavailable)"


def _format_ctx_memory_line(service: Any) -> str:
    """Format memory line for /ctx overview."""
    try:
        if hasattr(service, "memory_manager") and service.memory_manager:
            loop = asyncio.new_event_loop()
            results = loop.run_until_complete(
                service.memory_manager.query_core_memory(keywords=["experience"], limit=5)
            )
            loop.close()
            return f"  Memory:    ✅ initialized — {len(results)} recent memories queryable"
        return "  Memory:    ❌ not initialized\n" + _hint(
            "Install extras: pip install -e 'apps/backend[vector]'"
        )
    except Exception:
        return "  Memory:    (error)"


def _format_ctx_llm_line() -> str:
    """Format LLM line for /ctx overview."""
    try:
        llm_svc = _get_llm_svc()
        if llm_svc and getattr(llm_svc, "is_available", False):
            active_type = getattr(llm_svc, "active_backend_type", None)
            name = active_type.name if active_type else "unknown"
            n_backends = len(getattr(llm_svc, "backends", {}))
            llm_mode = getattr(llm_svc, "llm_mode", "unknown")
            return f"  LLM:       ✅ active={name}  backends={n_backends}  mode={llm_mode}"
        return "  LLM:       ❌ no backend available\n" + _hint("See /model list for details")
    except Exception:
        return "  LLM:       (error)"


def _format_ctx_config_line(service: Any) -> str:
    """Format config line for /ctx overview."""
    try:
        cfg = service._angela_config
        deployment = {}
        try:
            deployment = cfg.get_authority("llm", {}).get("deployment", {})
        except Exception:
            logger.debug("repl: /ctx config deployment unavailable", exc_info=True)
        mode = deployment.get("mode", "unknown")
        intents = list(cfg.get_intents().keys())
        return f"  Config:    mode={mode}  intents={len(intents)}"
    except Exception:
        return "  Config:    (unavailable)"


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
    lines.append(_format_ctx_state_line(service))
    lines.append(_format_ctx_memory_line(service))
    lines.append(_format_ctx_llm_line())
    lines.append(_format_ctx_config_line(service))
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
                content = r.get("content", "")
                if isinstance(content, dict):
                    content = " | ".join(str(v) for v in content.values() if v)
                content = str(content)[:100]
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
        result = eval(args)  # nosec B307 - local /eval command, same trust as shell
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


if __name__ == "__main__":
    run_repl_mode()
