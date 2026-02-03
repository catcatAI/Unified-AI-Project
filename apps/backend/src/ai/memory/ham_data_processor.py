import json
import logging
import zlib
import hashlib
from collections import Counter
from typing import Any, Dict, Optional
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# Placeholder for stopwords, in a real system this would be loaded from a config or NLTK
stopwords = set(["a", "an", "the", "is", "are", "was", "were", "and", "or", "but", "if", "then", "else", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"])

class HAMDataProcessor:
    def __init__(self, fernet: Optional[Fernet] = None):
        self.fernet = fernet

    def _encrypt(self, data: bytes) -> bytes:
        """Encrypts data using Fernet if available, otherwise returns raw data."""
        if self.fernet:
            return self.fernet.encrypt(data)
        # Fallback: If Fernet is not initialized, return data unencrypted (with a warning)
        logger.warning("Fernet not initialized, data NOT encrypted.")
        return data

    def _decrypt(self, data: bytes) -> bytes:
        """Decrypts data using Fernet if available, otherwise returns raw data."""
        if self.fernet:
            try:
                return self.fernet.decrypt(data)
            except InvalidToken:
                logger.error("Invalid token during Fernet decryption. Data might be corrupted or wrong key.")
                return b''
            except Exception as e:
                logger.error(f"Error during Fernet decryption: {e}")
                return b''
        # Fallback: If Fernet is not initialized, return data as is (with a warning)
        logger.warning("Fernet not initialized, data NOT decrypted.")
        return data

    def _compress(self, data: bytes) -> bytes:
        return zlib.compress(data)

    def _decompress(self, data: bytes) -> bytes:
        try:
            return zlib.decompress(data)
        except zlib.error as e:
            logger.error(f"Error during decompression: {e}")
            return b'' # Return empty bytes on error

    def _abstract_text(self, text: str) -> Dict[str, Any]:
        """
        Abstracts a text input into a structured gist.
        Simplified for PoC - a full implementation would use NLP models.
        """
        words = [word.lower().strip("., !?;:'") for word in text.split()]
        # Basic keyword extraction (top N frequent words, excluding stopwords)
        filtered_words = [word for word in words if word and word not in stopwords]
        if not filtered_words: # Handle case where all words are stopwords or empty:
            keywords = []
        else:
            word_counts = Counter(filtered_words)
            keywords = [word for word, count in word_counts.most_common(5)]
        # Basic summarization (first sentence)
        sentences = text.split('.')
        summary = sentences[0].strip() + "." if sentences else text
        # Placeholder for advanced features based on language (conceptual for v0.2)
        # Language detection would ideally happen before this or be passed in metadata.
        # For now, a very simple check.
        radicals_placeholder = []
        pos_tags_placeholder = []

        # Rudimentary language detection for placeholder
        is_likely_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
        if is_likely_chinese:
            # Conceptual: In a real system, call a radical extraction library / function
            radicals_placeholder = ["RadicalPlaceholder1", "RadicalPlaceholder2"] # Dummy
            logger.debug(f"HAM: Placeholder: Detected Chinese - like text, conceptual radicals would be extracted.")
        else: # Assume English - like or other Latin script
            # Conceptual: In a real system, call POS tagging
            if keywords: # Only add if there are keywords, to simulate some processing:
                pos_tags_placeholder = [{"kw": "NOUN_placeholder"} for kw in keywords[:2]] # Dummy POS for first 2 keywords
            logger.debug(f"HAM: Placeholder: Detected English - like text, conceptual POS tags would be generated.")

        # Placeholder for relational context extraction (a key "deep mapping", enhancement)
        relational_context = {
            "entities": ["PlaceholderEntity1", "PlaceholderEntity2"],
            "relationships": [{"subject": "PlaceholderEntity1", "verb": "is_related_to", "object": "PlaceholderEntity2"}]
        }

        return {
            "summary": summary,
            "keywords": keywords,
            "original_length": len(text),
            "relational_context": relational_context, # Add the new structure
            "radicals_placeholder": radicals_placeholder if is_likely_chinese else None,
            "pos_tags_placeholder": pos_tags_placeholder if not is_likely_chinese and keywords else None,
        }

    def _rehydrate_text_gist(self, gist: Dict[str, Any]) -> str:
        """
        Rehydrates a structured gist back into a human - readable string.
        Simplified for PoC.
        """
        base_rehydration = f"Summary: {gist.get('summary', 'N/A')}\nKeywords: {', '.join(gist.get('keywords', []) or [])}"

        # Handle the new relational_context structure
        if "relational_context" in gist and gist["relational_context"]["entities"]:
            base_rehydration += f"\nRelational Context (Placeholder)"
            for rel in gist["relational_context"].get("relationships", []):
                base_rehydration += f"\n  - {rel.get('subject')} -> {rel.get('verb')} -> {rel.get('object')}"

        if gist.get("radicals_placeholder"):
            base_rehydration += f"\nRadicals (Placeholder): {gist.get('radicals_placeholder')}"
        if gist.get("pos_tags_placeholder"):
            base_rehydration += f"\nPOS Tags (Placeholder): {gist.get('pos_tags_placeholder')}"
        return base_rehydration
