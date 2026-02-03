import aiohttp
import json
import logging
import os
from typing import List, Dict, Any
from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

class GeminiProvider(BaseLLMProvider):
    """
    Provider for Google Gemini API (via REST).
    Requires GOOGLE_API_KEY environment variable.
    """
    def __init__(self, api_key: str = None, model: str = "gemini-pro"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.api_key:
            return "Error: GOOGLE_API_KEY not set."

        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": kwargs.get("generation_config", {})
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        try:
                            return data["candidates"][0]["content"]["parts"][0]["text"]
                        except (KeyError, IndexError):
                            return "Error: Unexpected response format from Gemini."
                    else:
                        error_text = await response.text()
                        logger.error(f"Gemini Error {response.status}: {error_text}")
                        return f"Error: Gemini API returned {response.status}"
        except Exception as e:
            logger.error(f"Gemini Connection Error: {e}")
            return f"Error: Could not connect to Gemini. {e}"

    async def get_embedding(self, text: str) -> List[float]:
        if not self.api_key:
            return []

        # Use embedding-001 or configured model
        model = "embedding-001" 
        url = f"{self.base_url}/{model}:embedContent?key={self.api_key}"
        payload = {
            "model": f"models/{model}",
            "content": {
                "parts": [{"text": text}]
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("embedding", {}).get("values", [])
                    else:
                        logger.error(f"Gemini Embedding Error {response.status}: {await response.text()}")
                        return []
        except Exception as e:
            logger.error(f"Gemini Embedding Connection Error: {e}")
            return []

    async def health_check(self) -> bool:
        return self.api_key is not None
