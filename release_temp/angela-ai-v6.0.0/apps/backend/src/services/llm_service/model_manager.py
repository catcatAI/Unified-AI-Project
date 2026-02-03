import logging
from typing import Any

from .base_provider import BaseLLMProvider, LLMResponse

# Configure logger
logger = logging.getLogger(__name__)

# A simple configuration mapping model name prefixes to provider names.
# In a real-world application, this would likely come from a configuration file (e.g., YAML or .env).
MODEL_PROVIDER_MAP = {
    "gpt-4": "openai",
    "gpt-3.5-turbo": "openai",
    "distilgpt2": "huggingface_local",
    "gpt2": "huggingface_local",
    "mock-model": "mock_provider",  # Added for testing
}


class LLMManager:
    """Manages multiple LLM providers and routes generation requests to the appropriate one.
    This acts as a facade, providing a single point of entry for all LLM-related tasks.
    """

    def __init__(self):
        self.providers: dict[str, BaseLLMProvider] = {}
        self._load_providers()

    def register_provider(self, provider_name: str, provider_instance: BaseLLMProvider):
        """Allows for manually registering a provider, primarily for testing."""
        if provider_name in self.providers:
            logger.warning(
                f"Provider '{provider_name}' is already registered and will be overwritten.",
            )
        self.providers[provider_name] = provider_instance
        logger.info(f"Provider '{provider_name}' manually registered.")

    def _load_providers(self):
        """Dynamically discovers and loads all provider classes from the llm_service package."""
        import importlib
        import inspect
        import pkgutil

        import apps.backend.src.services.llm_service as providers_package

        logger.info(
            f"Dynamically loading LLM providers from package: {providers_package.__name__}",
        )

        for _, module_name, _ in pkgutil.walk_packages(
            path=providers_package.__path__,
            prefix=providers_package.__name__ + ".",
        ):
            try:
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module):
                    # Check if it's a class, a subclass of BaseLLMProvider, and not BaseLLMProvider itself
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, BaseLLMProvider)
                        and obj is not BaseLLMProvider
                    ):
                        logger.debug(f"Found LLM provider class: {obj.__name__}")
                        try:
                            provider_instance = obj()
                            provider_name = provider_instance.provider_name
                            if provider_name in self.providers:
                                logger.warning(
                                    f"Duplicate provider name '{provider_name}' found. Overwriting.",
                                )

                            self.providers[provider_name] = provider_instance
                            logger.info(
                                f"Successfully loaded and registered provider: '{provider_name}'",
                            )
                        except Exception as e:
                            logger.warning(
                                f"Could not instantiate provider {obj.__name__}: {e}. It will be unavailable.",
                            )

            except Exception as e:
                logger.error(
                    f"Failed to load providers from module {module_name}: {e}",
                    exc_info=True,
                )

    def _get_provider_for_model(self, model_name: str) -> BaseLLMProvider:
        """Determines which provider to use for a given model name based on the config map."""
        # This simple prefix-matching allows for variations like 'gpt-4-turbo'.
        for prefix, provider_name in MODEL_PROVIDER_MAP.items():
            if model_name.startswith(prefix):
                provider = self.providers.get(provider_name)
                if not provider:
                    raise ValueError(
                        f"Provider '{provider_name}' for model '{model_name}' is configured but was not loaded successfully.",
                    )
                return provider

        logger.error(f"No provider configured for model '{model_name}'.")
        raise ValueError(f"No provider configured for model '{model_name}'.")

    async def generate(self, model: str, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generates a completion by routing the request to the correct LLM provider."""
        logger.info(
            f"Received generation request for model '{model}'. Routing to appropriate provider.",
        )

        # Handle simulated model directly
        if model == "simulated-llm":
            simulated_response_text = f"Simulated response from {model} for: '{prompt}'"
            if "hello" in prompt.lower():
                simulated_response_text = "Hello there! How can I assist you today?"
            elif "how are you" in prompt.lower():
                simulated_response_text = (
                    "I am an AI, so I don't have feelings, but I am functioning well!"
                )
            elif "error" in prompt.lower():
                simulated_response_text = (
                    "I detected an error in your prompt. Please rephrase."
                )
            return LLMResponse(
                text=simulated_response_text,
                model_name=model,
                usage={
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": len(simulated_response_text.split()),
                },
                provider_name="simulated",
            )

        try:
            provider = self._get_provider_for_model(model)
            logger.debug(
                f"Routing request for model '{model}' to provider '{provider.provider_name}'.",
            )
            return await provider.generate(model=model, prompt=prompt, **kwargs)
        except Exception as e:
            logger.error(
                f"Failed to generate completion for model '{model}': {e}",
                exc_info=True,
            )
            # Re-raise the exception to be handled by the calling layer (e.g., the API endpoint)
            raise
