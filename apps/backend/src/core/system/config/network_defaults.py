"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
Centralized network defaults for hosts, ports, model names, and timeouts.
Replaces hardcoded values across the codebase.
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
    "llamacpp": 10,
    "ollama": 20,
    "openai": 30,
    "anthropic": 40,
    "google": 50,
}


__all__ = [
    "DEFAULT_HOST",
    "COMFYUI_PORT",
    "COMFYUI_URL",
    "OLLAMA_HOST",
    "LLAMACPP_HOST",
    "OPENAI_API_BASE",
    "ANTHROPIC_API_BASE",
    "GOOGLE_API_BASE",
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
