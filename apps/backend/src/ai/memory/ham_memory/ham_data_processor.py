import logging
import json
import zlib
import hashlib
import re
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
        if self.fernet:
            return self.fernet.encrypt(data)
        return data

    def _decrypt(self, data: bytes) -> bytes:
        if self.fernet:
            try:
                return self.fernet.decrypt(data)
            except InvalidToken:
                logger.error("Decryption failed: Invalid key or corrupted data.")
                raise
        return data

    def _abstract_text(self, text: str) -> Dict[str, Any]:
        """
        Enhanced text abstraction that extracts key information for memory storage.
        
        Extracts:
        - Gist (shortened version for quick scanning)
        - Keywords (important terms)
        - Entities (named entities like people, locations)
        - Key sentences (most important sentences)
        - Full text hash for verification
        """
        if not text or len(text) < 10:
            return {
                "gist": text,
                "keywords": [],
                "entities": [],
                "key_sentences": [],
                "full_text_hash": hashlib.sha256(text.encode('utf-8')).hexdigest()
            }
        
        # Extract gist (first 200 chars with smart truncation)
        if len(text) <= 200:
            gist = text
        else:
            # Try to truncate at sentence boundary
            last_period = text[:200].rfind('.')
            last_exclamation = text[:200].rfind('!')
            last_question = text[:200].rfind('?')
            truncation_point = max(last_period, last_exclamation, last_question)
            
            if truncation_point > 50:  # Ensure we don't truncate too early
                gist = text[:truncation_point + 1]
            else:
                gist = text[:200] + "..."
        
        # Extract keywords (simple frequency-based approach)
        words = re.findall(r'\b[a-zA-Z\u4e00-\u9fff]{3,}\b', text.lower())
        word_freq = {}
        for word in words:
            if word not in word_freq:
                word_freq[word] = 0
            word_freq[word] += 1
        
        # Get top 5 most frequent words (excluding common stop words)
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
            'her', 'was', 'one', 'our', 'out', 'has', 'have', 'been', 'this', 'that',
            '的', '了', '是', '在', '和', '有', '就', '不', '人', '都', '一', '一个', '上', '也'
        }
        
        keywords = []
        for word, freq in sorted(word_freq.items(), key=lambda x: x[1], reverse=True):
            if word not in stop_words and len(keywords) < 5:
                keywords.append(word)
        
        # Extract entities (simple pattern matching)
        entities = []
        
        # URLs
        urls = re.findall(r'https?://\S+', text)
        entities.extend([{"type": "url", "value": url} for url in urls[:3]])
        
        # Email addresses
        emails = re.findall(r'\b[\w.-]+@[\w.-]+\.\w+\b', text)
        entities.extend([{"type": "email", "value": email} for email in emails[:3]])
        
        # Numbers that might be IDs, quantities, etc.
        numbers = re.findall(r'\b\d{4,}\b|\b\d+\.\d+\b', text)
        entities.extend([{"type": "number", "value": num} for num in numbers[:5]])
        
        # Extract key sentences (sentences with high information content)
        sentences = re.split(r'[.!?。！？]', text)
        key_sentences = []
        
        # Score sentences by length and keyword presence
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10 or len(sentence) > 300:
                continue
            
            # Calculate score
            score = 0
            if any(keyword in sentence.lower() for keyword in keywords):
                score += 2
            if len(sentence.split()) > 5:  # Reasonable length
                score += 1
            if any(char in sentence for char in [':', '-', '•', '→']):  # Structural markers
                score += 0.5
            
            key_sentences.append((sentence, score))
        
        # Get top 3 sentences
        key_sentences.sort(key=lambda x: x[1], reverse=True)
        key_sentences = [s[0] for s in key_sentences[:3]]
        
        return {
            "gist": gist,
            "keywords": keywords,
            "entities": entities,
            "key_sentences": key_sentences,
            "full_text_hash": hashlib.sha256(text.encode('utf-8')).hexdigest()
        }

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
