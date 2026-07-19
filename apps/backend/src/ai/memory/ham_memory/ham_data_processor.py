# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import hashlib
import logging
import re
import zlib
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class HAMDataProcessor:
    def __init__(self, fernet: Optional[Fernet]):
        self.fernet = fernet

    def _compress(self, data: bytes) -> bytes:
        return zlib.compress(data)

    def _decompress(self, data: bytes) -> bytes:
        return zlib.decompress(data)

    def _encrypt(self, data: bytes) -> bytes:
        """Encrypt."""
        if self.fernet:
            return self.fernet.encrypt(data)
        return data

    def _decrypt(self, data: bytes) -> bytes:
        """Decrypt."""
        if self.fernet:
            try:
                return self.fernet.decrypt(data)
            except InvalidToken:
                # No log here, let caller handle with fallback or log actual error
                raise
        return data

    def _abstract_text(self, text: str) -> Dict[str, Any]:
        if not text or len(text) < 10:
            return {
                "gist": text,
                "keywords": [],
                "entities": [],
                "key_sentences": [],
                "full_text_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            }

        gist = self._extract_gist(text)
        keywords = self._extract_keywords(text)
        entities = self._extract_entities(text)
        key_sentences = self._extract_key_sentences(text, keywords)

        return {
            "gist": gist,
            "keywords": keywords,
            "entities": entities,
            "key_sentences": key_sentences,
            "full_text_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        }

    @staticmethod
    def _extract_gist(text: str, max_chars: int = 200) -> str:
        if len(text) <= max_chars:
            return text
        for boundary in (".", "!", "?"):
            idx = text[:max_chars].rfind(boundary)
            if idx > 50:
                return text[: idx + 1]
        return text[:max_chars] + "..."

    _STOP_WORDS = {
        "the",
        "and",
        "for",
        "are",
        "but",
        "not",
        "you",
        "all",
        "can",
        "had",
        "her",
        "was",
        "one",
        "our",
        "out",
        "has",
        "have",
        "been",
        "this",
        "that",
        "的",
        "了",
        "是",
        "在",
        "和",
        "有",
        "就",
        "不",
        "人",
        "都",
        "一",
        "一个",
        "上",
        "也",
    }

    @staticmethod
    def _extract_keywords(text: str, top_n: int = 5) -> list:
        words = re.findall(r"\b[a-zA-Z\u4e00-\u9fff]{3,}\b", text.lower())
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        keywords = []
        for word, freq in sorted(word_freq.items(), key=lambda x: x[1], reverse=True):
            if word not in HAMDataProcessor._STOP_WORDS and len(keywords) < top_n:
                keywords.append(word)
        return keywords

    @staticmethod
    def _extract_entities(text: str) -> list:
        entities = []
        urls = re.findall(r"https?://\S+", text)
        entities.extend([{"type": "url", "value": url} for url in urls[:3]])
        emails = re.findall(r"\b[\w.-]+@[\w.-]+\.\w+\b", text)
        entities.extend([{"type": "email", "value": email} for email in emails[:3]])
        numbers = re.findall(r"\b\d{4,}\b|\b\d+\.\d+\b", text)
        entities.extend([{"type": "number", "value": num} for num in numbers[:5]])
        return entities

    @staticmethod
    def _extract_key_sentences(text: str, keywords: list, top_n: int = 3) -> list:
        sentences = re.split(r"[.!?。！？]", text)
        scored = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10 or len(sentence) > 300:
                continue
            score = 0
            if any(keyword in sentence.lower() for keyword in keywords):
                score += 2
            if len(sentence.split()) > 5:
                score += 1
            if any(char in sentence for char in [":", "-", "•", "→"]):
                score += 0.5
            scored.append((sentence, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored[:top_n]]

    def _rehydrate_text_gist(self, gist: Dict[str, Any]) -> str:
        """
        Rehydrate text from gist, attempting to reconstruct a useful representation.

        Returns:
            Reconstructed text combining gist, keywords, and key sentences
        """
        if not gist or not isinstance(gist, dict):
            return ""

        # Start with the main gist
        parts = [gist.get("gist", "")]

        # Add key sentences if available
        key_sentences = gist.get("key_sentences", [])
        if key_sentences:
            parts.append("\n\nKey points:")
            for sentence in key_sentences:
                parts.append(f"• {sentence}")

        # Add keywords if available
        keywords = gist.get("keywords", [])
        if keywords:
            parts.append(f"\n\nKeywords: {', '.join(keywords)}")

        # Add entities if available
        entities = gist.get("entities", [])
        if entities:
            parts.append("\n\nReferences:")
            for entity in entities[:5]:  # Limit to 5 entities
                entity_type = entity.get("type", "unknown")
                entity_value = entity.get("value", "")
                parts.append(f"  {entity_type}: {entity_value}")

        return "\n".join(parts)
