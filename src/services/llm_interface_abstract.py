import abc
from typing import Any, Dict, List, Optional
from src.shared.types.common_types import LLMModelInfo

class AbstractLLMInterface(abc.ABC):
    """
    Abstract Base Class for LLM Interfaces.
    Defines the core interface for interacting with Large Language Models.
    """

    @abc.abstractmethod
    def generate_response(self, prompt: str, model_name: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates a text response from the LLM based on the given prompt.

        Args:
            prompt (str): The input prompt for the LLM.
            model_name (Optional[str]): The specific model to use. If None, uses the default configured model.
            params (Optional[Dict[str, Any]]): Additional generation parameters (e.g., temperature, max_tokens).

        Returns:
            str: The generated text response.
        """
        pass

    @abc.abstractmethod
    def list_available_models(self) -> List[LLMModelInfo]:
        """
        Lists available models from the configured LLM provider.

        Returns:
            List[LLMModelInfo]: A list of LLMModelInfo objects, each describing an available model.
        """
        pass
