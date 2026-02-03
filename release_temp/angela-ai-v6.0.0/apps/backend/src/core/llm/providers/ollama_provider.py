import aiohttp
import json
import logging
from typing import List, Dict, Any
from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

class OllamaProvider(BaseLLMProvider):
    """
    Provider for local Ollama models.
    Default URL: http://localhost:11434
    """
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model

    async def generate(self, prompt: str, **kwargs) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": 2048,
                "num_thread": 2,
                "stop": kwargs.get("stop", []), # Support stop tokens
                "num_predict": kwargs.get("num_predict", 256) # Limit to 256 tokens for speed
            },
            **kwargs
        }
        import time
        start_time = time.time()
        try:
            timeout = aiohttp.ClientTimeout(total=600) # 10 minutes timeout for slow hardware
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        duration = time.time() - start_time
                        logger.info(f"Ollama Generation Time: {duration:.2f}s")
                        return data.get("response", "")
                    else:
                        logger.error(f"Ollama Error {response.status}: {await response.text()}")
                        return f"Error: Ollama returned {response.status}"
        except Exception as e:
            logger.error(f"Ollama Connection Error: {e}")
            return ""

    async def get_embedding(self, text: str) -> List[float]:
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": self.model,
            "prompt": text
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("embedding", [])
                    else:
                        logger.error(f"Ollama Embedding Error {response.status}: {await response.text()}")
                        return []
        except Exception as e:
            logger.error(f"Ollama Embedding Connection Error: {e}")
            return []

    async def health_check(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    return response.status == 200
        except:
            return False
