"""
ERR-INTROSPECTOR: Semantic Anomaly Detector
Detects repetition, tonal shifts, and narrative divergence in AI outputs.
"""

import logging
import uuid
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from .types import (
    LIS_SemanticAnomalyDetectedEvent,
    LIS_AnomalyType,
    LIS_SeverityScore
)

logger = logging.getLogger(__name__)

class ERRIntrospector:
    """
    ERR-INTROSPECTOR monitors AI outputs for semantic anomalies.
    It uses simple heuristics (for now) to detect repetition and tonal misalignment.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.output_history: List[str] = []
        self.max_history = self.config.get("max_history", 10)
        logger.info("ERR-INTROSPECTOR initialized.")

    async def analyze_output(self, output_text: str, context: Dict[str, Any]) -> List[LIS_SemanticAnomalyDetectedEvent]:
        """Analyzes text for anomalies and returns a list of detected events."""
        anomalies = []
        
        # 1. Detect Repetition (ECHO-SHIELD logic)
        repetition_event = self._detect_repetition(output_text)
        if repetition_event:
            anomalies.append(repetition_event)
            
        # 2. Detect Tonal Shift (Simplified)
        tone_event = self._detect_tone_shift(output_text, context)
        if tone_event:
            anomalies.append(tone_event)
            
        # Update history
        self.output_history.append(output_text)
        if len(self.output_history) > self.max_history:
            self.output_history.pop(0)
            
        return anomalies

    def _detect_repetition(self, text: str) -> Optional[LIS_SemanticAnomalyDetectedEvent]:
        """Checks if the new output is too similar to recent history."""
        if not self.output_history:
            return None
            
        for past_text in self.output_history:
            if text.strip() == past_text.strip():
                return {
                    "anomaly_id": f"err_{uuid.uuid4().hex[:8]}",
                    "anomaly_type": "REPETITION_ECHO",
                    "severity_score": 0.8,
                    "description": "Output is identical to a recent previous output.",
                    "context_snippet": text[:100],
                    "timestamp_detected": datetime.now(timezone.utc).isoformat(),
                    "metadata": {"repeated_text": text}
                }
        return None

    def _detect_tone_shift(self, text: str, context: Dict[str, Any]) -> Optional[LIS_SemanticAnomalyDetectedEvent]:
        """Detects if the tone mismatch with the expected sentiment in context."""
        expected_sentiment = context.get("expected_sentiment", "neutral")
        # Very simple heuristic: if expected is happy but text has sad keywords
        sad_keywords = ["error", "fail", "bad", "unfortunate", "sorry"]
        
        if expected_sentiment == "joy" and any(k in text.lower() for k in sad_keywords):
            return {
                "anomaly_id": f"err_{uuid.uuid4().hex[:8]}",
                "anomaly_type": "UNEXPECTED_TONE_SHIFT",
                "severity_score": 0.5,
                "description": f"Output tone appears pessimistic ({text[:20]}...) while 'joy' was expected.",
                "context_snippet": text[:100],
                "timestamp_detected": datetime.now(timezone.utc).isoformat(),
                "metadata": {"expected_sentiment": expected_sentiment}
            }
        return None
