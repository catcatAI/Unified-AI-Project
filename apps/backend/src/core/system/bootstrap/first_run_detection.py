"""
First-Run Environment Detection
Detects at server startup whether any usable LLM backend exists and emits
actionable warnings instead of failing silently later.

Complements the REPL boot hints (cli/repl.py) — this module covers the
main server (main.py lifespan), which previously started without any
warning when no API key / no Ollama was configured.
"""

import logging
import os
from typing import Any, Dict, List

from core.system.config.tiered_loader import get_config

logger = logging.getLogger(__name__)

# Backend name → env var(s) that must be set for the backend to be usable.
_CLOUD_BACKEND_ENV_KEYS: Dict[str, List[str]] = {
    "openai": ["OPENAI_API_KEY"],
    "anthropic": ["ANTHROPIC_API_KEY"],
    "google": ["GEMINI_API_KEY"],
}

# Local HTTP backends → default host if the config has no base_url.
_LOCAL_BACKEND_HOSTS: Dict[str, str] = {
    "ollama": "http://localhost:11434",
    "llama_cpp": "http://localhost:8080",
}

# Local backends that are always available (no external process needed).
_ALWAYS_AVAILABLE_PROVIDERS = {"unified", "ed3n", "garden"}


def _first_env_value(env_keys: List[str]) -> bool:
    """Return True if any of *env_keys* is set to a non-empty value."""
    return any(bool(os.getenv(k)) for k in env_keys)


def _probe_local_http(host: str, timeout: float = 1.0) -> bool:
    """Cheap TCP-then-HTTP probe of a local model server."""
    try:
        import urllib.request

        # Only http(s) probes may reach urlopen: a file:// or custom-scheme
        # string must never be opened verbatim.
        if not host.startswith(("http://", "https://")):
            return False
        req = urllib.request.Request(host, method="GET")
        with urllib.request.urlopen(req, timeout=timeout):  # nosec B310 - scheme checked above
            return True
    except Exception:
        return False


def _classify_backend(
    name: str, cfg: Dict[str, Any], allow_cloud: bool, deployment_mode: str
) -> str:
    """Classify one backend entry. Returns 'usable' | 'unreachable' | 'blocked:<msg>'."""
    enabled = cfg.get("enabled", True)
    if not enabled:
        return "skip"
    kind = str(cfg.get("type", "")).lower()
    provider = str(cfg.get("provider", "")).lower()

    if kind == "local":
        if provider in _ALWAYS_AVAILABLE_PROVIDERS:
            return "usable"
        host = cfg.get("base_url") or _LOCAL_BACKEND_HOSTS.get(provider, "")
        if host and _probe_local_http(host):
            return "usable"
        return "unreachable"

    if kind != "cloud":
        # Unknown kind: treat conservatively as usable (don't false-alarm).
        return "usable"

    # Cloud backend: requires deployment gate + API key.
    env_keys = _CLOUD_BACKEND_ENV_KEYS.get(provider, [])
    if not allow_cloud:
        return f"blocked:{name} (deployment.mode={deployment_mode} gates it)"
    if env_keys and not _first_env_value(env_keys):
        return f"blocked:{name} (missing {'/'.join(env_keys)})"
    return "usable"


def _build_warnings(unreachable_local: List[str], blocked_cloud: List[str]) -> List[str]:
    """Build actionable warning messages when no usable backend exists."""
    warnings: List[str] = []
    for b in unreachable_local:
        warnings.append(
            f"⚠️  Local backend '{b}' is not responding "
            f"(is the server running? e.g. `ollama serve`)"
        )
    if blocked_cloud:
        for b in blocked_cloud:
            warnings.append(f"⚠️  Cloud backend {b}")
        warnings.append(
            "💡 Fix: set OPENAI_API_KEY in .env and set "
            "deployment.mode: local+llm in configs/system/llm.default.yaml"
        )
    warnings.append(
        "💡 Fix: install Ollama (https://ollama.ai) then "
        "`ollama pull qwen3.5:0.8b` for a local backend"
    )
    return warnings


def detect_first_run() -> Dict[str, Any]:
    """Inspect deployment config + environment for usable backends.

    Returns a summary dict:
        usable_backends : names that should work right now
        blocked_cloud   : enabled cloud backends missing their API key
        unreachable_local: enabled local HTTP backends that did not answer
        deployment_mode : resolved deployment.mode value
        ok              : True if at least one usable backend exists
        warnings        : actionable messages (empty when ok)
    """
    usable: List[str] = []
    blocked_cloud: List[str] = []
    unreachable_local: List[str] = []

    llm_cfg = get_config("system/llm") or {}
    deployment_mode = (llm_cfg.get("deployment") or {}).get("mode", "auto")
    backends = llm_cfg.get("backends") or {}

    allow_cloud = deployment_mode in ("local+llm", "llm", "auto")

    for name, cfg in backends.items():
        if not isinstance(cfg, dict):
            continue
        verdict = _classify_backend(name, cfg, allow_cloud, deployment_mode)
        if verdict == "skip":
            continue
        if verdict == "usable":
            usable.append(name)
        elif verdict == "unreachable":
            unreachable_local.append(name)
        elif verdict.startswith("blocked:"):
            blocked_cloud.append(verdict[len("blocked:") :])

    warnings: List[str] = []
    if not usable:
        warnings = _build_warnings(unreachable_local, blocked_cloud)

    return {
        "usable_backends": usable,
        "blocked_cloud": blocked_cloud,
        "unreachable_local": unreachable_local,
        "deployment_mode": deployment_mode,
        "ok": bool(usable),
        "warnings": warnings,
    }


def log_first_run_warnings(summary: Dict[str, Any]) -> None:
    """Log actionable warnings when no usable LLM backend was detected."""
    if summary.get("ok"):
        logger.info(
            "✅ [FirstRun] Usable backends: %s (mode=%s)",
            summary["usable_backends"],
            summary["deployment_mode"],
        )
        return
    logger.warning("🚨 [FirstRun] No usable LLM backend detected at startup")
    for w in summary.get("warnings", []):
        logger.warning(w)
