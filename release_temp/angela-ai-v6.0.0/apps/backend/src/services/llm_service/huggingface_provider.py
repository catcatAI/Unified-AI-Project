import asyncio
import logging
from typing import Any

# Use a try-except block for heavy dependencies to provide a clear error message if not installed.
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
except ImportError:
    raise ImportError(
        "The 'transformers' and 'torch' libraries are required for this provider. Please install them with 'pip install transformers torch'.",
    )

from .base_provider import BaseLLMProvider, LLMResponse

# Configure logger
logger = logging.getLogger(__name__)


class HuggingFaceLocalProvider(BaseLLMProvider):
    """An LLM provider for running local Hugging Face models for text generation.
    This provider includes a cache to avoid reloading models into memory.
    """

    def __init__(self):
        # Determine device (use GPU if available, otherwise CPU)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(
            f"HuggingFaceLocalProvider initialized. Using device: {self.device}",
        )
        # Cache for loaded models and tokenizers to avoid reloading on every call
        self._model_cache: dict[str, Any] = {}

    @property
    def provider_name(self) -> str:
        return "huggingface_local"

    def _load_model(self, model_name: str):
        """Synchronous function to load a model and tokenizer from Hugging Face.
        This is designed to be run in a separate thread to avoid blocking the asyncio event loop.
        """
        if model_name in self._model_cache:
            logger.debug(f"Model '{model_name}' found in cache.")
            return self._model_cache[model_name]

        logger.info(
            f"Loading model '{model_name}' to {self.device}. This may take a while...",
        )
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(model_name).to(self.device)
            self._model_cache[model_name] = (model, tokenizer)
            logger.info(f"Model '{model_name}' loaded successfully.")
            return model, tokenizer
        except Exception as e:
            logger.error(f"Failed to load model '{model_name}': {e}", exc_info=True)
            raise

    def _run_generation(self, model, tokenizer, prompt: str, **kwargs: Any) -> str:
        """Synchronous function to run the text generation pipeline.
        This is designed to be run in a separate thread.
        """
        logger.debug(f"Running generation for model on device '{self.device}'.")
        inputs = tokenizer(prompt, return_tensors="pt").to(self.device)

        # Sensible defaults for generation
        params = {
            "max_new_tokens": 256,
            "temperature": 0.7,
            "do_sample": True,
            "pad_token_id": tokenizer.eos_token_id,
            **kwargs,
        }

        outputs = model.generate(**inputs, **params)
        # Decode the output, skipping special tokens and the original prompt
        response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # The generated output often includes the prompt, so we remove it.
        if response_text.startswith(prompt):
            return response_text[len(prompt) :].strip()
        return response_text

    async def generate(self, model: str, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generates text using a local Hugging Face model, running sync operations in a thread pool."""
        try:
            # Load model and tokenizer in a thread to not block the event loop
            model_obj, tokenizer_obj = await asyncio.to_thread(self._load_model, model)

            # Run the synchronous generation function in a thread
            response_text = await asyncio.to_thread(
                self._run_generation,
                model_obj,
                tokenizer_obj,
                prompt,
                **kwargs,
            )

            return LLMResponse(
                text=response_text,
                model_name=model,
                usage={},  # Token usage is not straightforward to get from model.generate
                provider_name=self.provider_name,
            )
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during Hugging Face model generation: {e}",
                exc_info=True,
            )
            raise
