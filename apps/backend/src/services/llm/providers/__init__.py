# ANGELA-MATRIX: L3 [γ] [B] [L0]
"""LLM backend provider implementations"""

from .base import BaseLLMBackend
from .registry import LLMBackend
from .llamacpp import LlamaCppBackend
from .ollama import OllamaBackend
from .openai import OpenAIAPIBackend
from .anthropic import AnthropicAPIBackend
from .google import GoogleAPIBackend
from .ed3n import ED3NBackend

__all__ = [
    "BaseLLMBackend",
    "LLMBackend",
    "LlamaCppBackend",
    "OllamaBackend",
    "OpenAIAPIBackend",
    "AnthropicAPIBackend",
    "GoogleAPIBackend",
    "ED3NBackend",
]
