import asyncio
import time
import random
from typing import Dict, List, Optional, Tuple, Union, Iterator, Any
import logging

logger = logging.getLogger(__name__)

class SimultaneousTranslationService:
    """
    Enhanced translation service mockup.
    Simulates translation latency and basic language detection logic.
    """

    def __init__(self, default_target_lang: str = "en", base_latency_ms: int = 150) -> None:
        self.default_target_lang = default_target_lang
        self.base_latency_ms = base_latency_ms
        self.supported_languages = ["en", "zh", "ja", "ko", "fr", "de"]

    async def translate(self, text: str, source_lang: str = "auto", target_lang: Optional[str] = None) -> Dict[str, Union[str, float, int]]:
        """
        Async translation simulation.
        """
        if not text:
            return self._empty_result(source_lang, target_lang)

        tgt = target_lang or self.default_target_lang
        
        # Simulate network/processing latency
        latency = self.base_latency_ms + random.randint(50, 200)
        await asyncio.sleep(latency / 1000.0)

        # Mock translation logic: append target language code if it's not the same as source
        translated = text
        if source_lang != tgt:
            translated = f"[{tgt.upper()}] {text}"

        logger.info(f"[Translation] Translated {len(text)} chars to {tgt}")

        return {
            "source_lang": source_lang if source_lang != "auto" else "detected_en",
            "target_lang": tgt,
            "original_text": text,
            "translated_text": translated,
            "confidence": 0.95,
            "latency_ms": latency,
        }

    async def stream_translate(self, chunks: Iterator[str], source_lang: str = "auto", target_lang: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """
        Generator for streaming translation results.
        """
        tgt = target_lang or self.default_target_lang
        for idx, chunk in enumerate(chunks):
            if not chunk: continue
            
            latency = (self.base_latency_ms // 2) + random.randint(10, 50)
            await asyncio.sleep(latency / 1000.0)
            
            yield {
                "index": idx,
                "source_lang": source_lang,
                "target_lang": tgt,
                "original_text": chunk,
                "translated_text": f"~{chunk}", # Mock stream marker
                "is_final": False,
                "confidence": 0.88,
            }

    def _empty_result(self, src: str, tgt: Optional[str]) -> Dict[str, Any]:
        return {
            "source_lang": src,
            "target_lang": tgt or self.default_target_lang,
            "original_text": "",
            "translated_text": "",
            "confidence": 0.0,
            "latency_ms": 0
        }
