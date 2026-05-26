# ANGELA-MATRIX: L3 [γ] [B] [L0]
"""LLM backend type registry"""

from enum import Enum


class LLMBackend(Enum):
    """支援的 LLM 後端"""

    LLAMA_CPP = "llamacpp"
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"
    NONE = "none"
