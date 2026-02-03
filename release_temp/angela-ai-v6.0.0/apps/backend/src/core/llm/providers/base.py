from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers (Ollama, Gemini, OpenAI, etc.).
    """

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generates a text response for the given prompt.
        """
        pass

    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """
        Generates a vector embedding for the given text.
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Checks if the provider is reachable and functioning.
        """
        pass
