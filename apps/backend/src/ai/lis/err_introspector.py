"""
ERR-INTROSPECTOR: Semantic Anomaly Detector
Detects repetition, tonal shifts, and narrative divergence in AI outputs.
"""

import logging
import uuid
import time
import math
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

try:
    import numpy as np
except ImportError:
    np = None

from .types import (
    LIS_SemanticAnomalyDetectedEvent,
    LIS_AnomalyType,
    LIS_SeverityScore
)

logger = logging.getLogger(__name__)

class ERRIntrospector:
    """
    ERR-INTROSPECTOR: Semantic Anomaly Detector.
    Advanced version using vector-like similarity and weighted sentiment analysis.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.output_history: List[Dict[str, Any]] = []  # Stores {text, vector, sentiment}
        self.max_history = self.config.get("max_history", 15)
        # Tonal Keywords with weights
        self.sentiment_lexicon = {
            "pessimistic": {"error": 0.8, "fail": 0.7, "bad": 0.6, "sorry": 0.4, "problem": 0.5, "unfortunate": 0.6},
            "optimistic": {"success": 0.8, "happy": 0.9, "great": 0.7, "good": 0.5, "excellent": 0.9, "joy": 1.0}
        }
        logger.info("ERR-INTROSPECTOR (Deep Logic) initialized.")

    async def analyze_output(self, output_text: str, context: Dict[str, Any]) -> List[LIS_SemanticAnomalyDetectedEvent]:
        """Analyzes text for anomalies and returns a list of detected events."""
        anomalies = []
        
        # 1. Vectorize text (Simple TF-IDF / Bag of Words implementation for low-resource AGI)
        current_vector = self._vectorize(output_text)
        
        # 2. Detect Repetition via Semantic Similarity
        # We must detect repetition BEFORE adding to history to avoid matching itself
        repetition_event = self._detect_semantic_repetition(output_text, current_vector)
        if repetition_event:
            anomalies.append(repetition_event)
            
        # 3. Detect Tonal Shift via Weighted Lexicon
        tone_event = self._detect_weighted_tone_shift(output_text, context)
        if tone_event:
            anomalies.append(tone_event)
            
        # Update history with meta-data
        self.output_history.append({
            "text": output_text,
            "vector": current_vector,
            "timestamp": time.time()
        })
        if len(self.output_history) > self.max_history:
            self.output_history.pop(0)
            
        return anomalies

    def _vectorize(self, text: str) -> Dict[str, float]:
        """Simple word-frequency vectorizer for semantic comparison."""
        # Strip punctuation and split
        clean_text = "".join(c.lower() for c in text if c.isalnum() or c.isspace())
        words = clean_text.split()
        vector = {}
        for word in words:
            if len(word) > 2:  # Ignore very short words
                vector[word] = vector.get(word, 0) + 1
        
        # Normalize vector
        total = sum(v*v for v in vector.values())
        if total > 0:
            mag = math.sqrt(total)
            for word in vector:
                vector[word] /= mag
        return vector

    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two word vectors."""
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum(vec1[x] * vec2[x] for x in intersection)
        return numerator

    def _detect_semantic_repetition(self, text: str, current_vector: Dict[str, float]) -> Optional[LIS_SemanticAnomalyDetectedEvent]:
        """Checks if the new output is semantically too similar to recent history."""
        if not self.output_history:
            return None
            
        threshold = self.config.get("repetition_threshold", 0.85)
        
        for record in self.output_history:
            similarity = self._cosine_similarity(current_vector, record["vector"])
            if similarity > threshold:
                return {
                    "anomaly_id": f"err_{uuid.uuid4().hex[:8]}",
                    "anomaly_type": "REPETITION_ECHO",
                    "severity_score": float(similarity),
                    "description": f"Semantic repetition detected (Similarity: {similarity:.2f}).",
                    "context_snippet": text[:100],
                    "timestamp_detected": datetime.now(timezone.utc).isoformat(),
                    "metadata": {"similarity": similarity, "matched_previous": record["text"][:50]}
                }
        return None

    def _detect_weighted_tone_shift(self, text: str, context: Dict[str, Any]) -> Optional[LIS_SemanticAnomalyDetectedEvent]:
        """Detects if the tone mismatch with the expected sentiment using weighted lexicon."""
        expected_sentiment = context.get("expected_sentiment", "neutral")
        if expected_sentiment == "neutral":
            return None

        text_lower = text.lower()
        pessimistic_score = sum(weight for word, weight in self.sentiment_lexicon["pessimistic"].items() if word in text_lower)
        optimistic_score = sum(weight for word, weight in self.sentiment_lexicon["optimistic"].items() if word in text_lower)

        # Scientific constraint: If joy is expected, but pessimism outweighs optimism
        if expected_sentiment == "joy" and pessimistic_score > optimistic_score:
            severity = min(1.0, (pessimistic_score - optimistic_score) / 2.0 + 0.5)
            return {
                "anomaly_id": f"err_{uuid.uuid4().hex[:8]}",
                "anomaly_type": "UNEXPECTED_TONE_SHIFT",
                "severity_score": severity,
                "description": f"Significant tonal misalignment. Expected 'joy' but text is predominantly pessimistic (Score: {pessimistic_score:.2f}).",
                "context_snippet": text[:100],
                "timestamp_detected": datetime.now(timezone.utc).isoformat(),
                "metadata": {"pessimistic_score": pessimistic_score, "optimistic_score": optimistic_score}
            }
        return None
