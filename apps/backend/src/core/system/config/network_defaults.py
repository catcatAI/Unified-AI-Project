"""
Fallback network defaults for hosts, ports, model names, and timeouts.
These values are duplicated in configs/system/llm.default.yaml.
New code should read from tiered_loader.get_config().
This file is kept as an active fallback until all 7 consumers are migrated.

ANGELA-MATRIX: [L3] [β] [B] [L0]
"""

from typing import Dict

# Hosts / Ports
DEFAULT_HOST: str = "127.0.0.1"
COMFYUI_PORT: int = 8188
COMFYUI_URL: str = f"http://{DEFAULT_HOST}:{COMFYUI_PORT}"
OLLAMA_HOST: str = f"http://{DEFAULT_HOST}:11434"
LLAMACPP_HOST: str = f"http://{DEFAULT_HOST}:8080"
OPENAI_API_BASE: str = "https://api.openai.com/v1"
ANTHROPIC_API_BASE: str = "https://api.anthropic.com/v1"
GOOGLE_API_BASE: str = "https://generativelanguage.googleapis.com/v1beta"

# Server bind address/port (ANGELA_SERVER_HOST / ANGELA_SERVER_PORT override).
# Single source of truth for every uvicorn.run() entry point so CLI, REPL and
# __main__ can never drift apart.
SERVER_BIND_HOST: str = "0.0.0.0"
SERVER_PORT: int = 8000

# Loopback hosts trusted for security-sensitive local-only endpoints.
# Configurable because behind a reverse proxy the client host may be a
# trusted proxy IP instead of a literal loopback address.
LOCAL_TRUSTED_HOSTS: tuple = ("127.0.0.1", "::1", "localhost")

# Internal agent-router port (agent_manager). Previously hardcoded twice in
# two different spots which could drift apart; defined once here.
AGENT_ROUTER_PORT: int = 11435

# CORS allowed origins (ANGELA_CORS_ORIGINS env overrides).
# Comma-separated list, e.g. "https://app.example.com,https://admin.example.com".
# Default "*" is permissive for local dev but MUST be restricted in production.
# When allow_credentials=True, browsers reject wildcard "*", so explicit origins
# are required in that mode.
DEFAULT_CORS_ORIGINS: list = ["*"]


def get_cors_origins() -> list:
    """Resolve CORS allowed origins.

    Priority: ANGELA_CORS_ORIGINS env (comma-separated) > DEFAULT_CORS_ORIGINS.
    Strips whitespace and drops empty entries.
    """
    import os

    raw = os.getenv("ANGELA_CORS_ORIGINS", "")
    if raw.strip():
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        if origins:
            return origins
    return DEFAULT_CORS_ORIGINS


def get_server_bind() -> tuple:
    """Resolve (host, port) for server entry points.

    Priority: ANGELA_SERVER_HOST / ANGELA_SERVER_PORT env > defaults above.
    """
    import os

    host = os.getenv("ANGELA_SERVER_HOST", SERVER_BIND_HOST)
    try:
        port = int(os.getenv("ANGELA_SERVER_PORT", str(SERVER_PORT)))
    except ValueError:
        port = SERVER_PORT
    return host, port

# ED3N runs in-process; no external host needed
ED3N_HOST: str = "http://127.0.0.1:0"
DEFAULT_ED3N_MODEL: str = "ed3n-v1"
ED3N_TIMEOUT: float = 30.0

# Model name defaults (backends)
DEFAULT_OPENAI_MODEL: str = "gpt-4"
DEFAULT_ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
DEFAULT_OLLAMA_MODEL: str = "llama3"
DEFAULT_LLAMACPP_MODEL: str = "mistral-7b-instruct"
DEFAULT_GOOGLE_MODEL: str = "gemini-pro"

# Timeouts (seconds)
DEFAULT_TIMEOUT: float = 120.0
LLM_REQUEST_TIMEOUT: float = 120.0
COMFYUI_TIMEOUT: float = 60.0
OLLAMA_TIMEOUT: float = 120.0
OPENAI_TIMEOUT: float = 120.0
ANTHROPIC_TIMEOUT: float = 120.0
GOOGLE_TIMEOUT: float = 120.0
HEALTH_CHECK_TIMEOUT: float = 5.0

# LLM routing
BACKEND_PRIORITY: Dict[str, int] = {
    "ed3n": 5,
    "llamacpp": 10,
    "ollama": 20,
    "openai": 30,
    "anthropic": 40,
    "google": 50,
}


__all__ = [
    "DEFAULT_HOST",
    "SERVER_BIND_HOST",
    "SERVER_PORT",
    "LOCAL_TRUSTED_HOSTS",
    "AGENT_ROUTER_PORT",
    "get_server_bind",
    "DEFAULT_CORS_ORIGINS",
    "get_cors_origins",
    "COMFYUI_PORT",
    "COMFYUI_URL",
    "OLLAMA_HOST",
    "LLAMACPP_HOST",
    "OPENAI_API_BASE",
    "ANTHROPIC_API_BASE",
    "GOOGLE_API_BASE",
    "ED3N_HOST",
    "DEFAULT_ED3N_MODEL",
    "ED3N_TIMEOUT",
    "DEFAULT_OPENAI_MODEL",
    "DEFAULT_ANTHROPIC_MODEL",
    "DEFAULT_OLLAMA_MODEL",
    "DEFAULT_LLAMACPP_MODEL",
    "DEFAULT_GOOGLE_MODEL",
    "DEFAULT_TIMEOUT",
    "LLM_REQUEST_TIMEOUT",
    "COMFYUI_TIMEOUT",
    "OLLAMA_TIMEOUT",
    "OPENAI_TIMEOUT",
    "ANTHROPIC_TIMEOUT",
    "GOOGLE_TIMEOUT",
    "HEALTH_CHECK_TIMEOUT",
    "BACKEND_PRIORITY",
]
