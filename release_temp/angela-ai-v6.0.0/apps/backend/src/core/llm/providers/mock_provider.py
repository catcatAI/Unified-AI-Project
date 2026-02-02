from typing import List
from .base import BaseLLMProvider

class MockLLMProvider(BaseLLMProvider):
    async def generate(self, prompt: str, **kwargs) -> str:
        return "This is a simulated response from the Mock Provider. The system logic is working correctly."

    async def get_embedding(self, text: str) -> List[float]:
        return [0.1, 0.2, 0.3]

    async def health_check(self) -> bool:
        return True
