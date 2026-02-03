import logging
import os
from typing import Any

# Ensure the openai library is imported
try:
    import openai
except ImportError:
    raise ImportError(
        "The 'openai' library is required for this provider. Please install it with 'pip install openai'.",
    )

from .base_provider import BaseLLMProvider, LLMResponse

# Configure logger
logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """An LLM provider that uses the official OpenAI Python client for text generation."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")

        try:
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
            logger.info("OpenAI client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
            raise

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(self, model: str, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generates a text completion using the OpenAI Chat Completions API."""
        logger.debug(f"Generating text with OpenAI model '{model}'.")
        try:
            # Sensible defaults that can be overridden by kwargs
            params = {
                "temperature": 0.7,
                "max_tokens": 2048,
                **kwargs,
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            }

            completion = await self.client.chat.completions.create(**params)

            response_text = completion.choices[0].message.content or ""
            usage = completion.usage

            logger.debug(f"Successfully received response from OpenAI model '{model}'.")

            return LLMResponse(
                text=response_text,
                model_name=model,
                usage=usage.model_dump() if usage else {},
                provider_name=self.provider_name,
            )
        except openai.APIError as e:
            logger.error(
                f"OpenAI API error: {e.status_code} - {e.response}",
                exc_info=True,
            )
            raise  # Re-raise the specific error for higher-level handling
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while calling OpenAI API: {e}",
                exc_info=True,
            )
            raise
