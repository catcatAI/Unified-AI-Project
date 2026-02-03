from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """Standard response format for all LLM providers."""

    text: str = Field(description="The generated text response from the model.")
    model_name: str = Field(
        description="The name of the model that generated the response.",
    )
    usage: dict[str, int] = Field(
        default_factory=dict,
        description="Token usage information, e.g., {'prompt_tokens': 50, 'completion_tokens': 100}.",
    )
    provider_name: str = Field(
        description="The name of the provider that served the model.",
    )


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers, ensuring a unified interface
    for text generation.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """The unique name of the provider (e.g., 'openai', 'huggingface_local')."""

    @abstractmethod
    async def generate(self, model: str, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generates a text completion for a given prompt using a specified model.

        Args:
            model (str): The specific model to use for generation (e.g., 'gpt-4', 'llama3-8b').
            prompt (str): The input text prompt.
            **kwargs: Provider-specific arguments (e.g., temperature, max_tokens).

        Returns:
            LLMResponse: A standardized response object.

        """
