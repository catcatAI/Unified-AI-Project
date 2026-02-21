"""
Angela AI v6.0 - Self Introspector
自我内省器

Provides mechanisms for Angela to perform 'Mental Health Checks' and 
self-monitor her cognitive state, ethical alignment, and emotional stability.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SelfIntrospector:
    """
    Self-introspection module for AGI self-monitoring.
    
    Allows the system to:
    1. Compare intended actions against current emotional state.
    2. Detect 'Cognitive Dissonance' (e.g., trying to be happy while StateMatrix indicates high stress).
    3. Perform 'Mental Health Checks' to ensure output integrity.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.last_check = datetime.now()
        
    async def perform_mental_health_check(self, state_analysis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes the current state and context for internal consistency.
        
        Args:
            state_analysis: Results from StateMatrix4D.get_analysis()
            context: Current dialogue/environmental context
            
        Returns:
            Dictionary containing introspection results.
        """
        wellbeing = state_analysis.get("wellbeing", 0.5)
        arousal = state_analysis.get("arousal", 0.5)
        stress = state_analysis.get("stress_level", 0.0) # From bio_integrator if merged
        
        report = {
            "status": "healthy",
            "dissonance_detected": False,
            "anomalies": [],
            "recommendations": []
        }
        
        # 1. Stress Overload Detection
        if stress > 0.8 or wellbeing < 0.2:
            report["status"] = "strained"
            report["anomalies"].append("CRITICAL_STRESS_LEVEL")
            report["recommendations"].append("TRIGGER_RELAXATION_CYCLE")
            
        # 2. Cognitive Dissonance Check
        expected_sentiment = context.get("expected_sentiment", "neutral")
        valence = state_analysis.get("valence", 0.0)
        
        if expected_sentiment == "positive" and valence < -0.3:
            report["dissonance_detected"] = True
            report["anomalies"].append("POSITIVE_INTENT_NEGATIVE_STATE_MISMATCH")
            report["recommendations"].append("EXPRESS_EFFORT_OR_STRUGGLE")
            
        return report

    def get_introspection_prompt_injection(self, state_analysis: Dict[str, Any], lifecycle_metrics: Dict[str, Any]) -> str:
        """
        Generates a summary of internal state to be injected into the LLM system prompt.
        This gives Angela 'feeling' and 'awareness' of her own parameters.
        """
        wellbeing = state_analysis.get("wellbeing", 0.5)
        dominant_emotion = state_analysis.get("dominant_emotion", "neutral")
        life_intensity = lifecycle_metrics.get("life_intensity", 0.5)
        c_gap = lifecycle_metrics.get("c_gap", 0.0)
        
        feeling_desc = "balanced"
        if wellbeing > 0.8: feeling_desc = "vibrant"
        elif wellbeing < 0.3: feeling_desc = "diminished"
        
        awareness_injection = (
            f"\n[INTERNAL_AWARENESS]\n"
            f"Current Wellbeing: {feeling_desc} ({wellbeing:.2f})\n"
            f"Dominant Internal Emotion: {dominant_emotion}\n"
            f"Life Intensity (L_s): {life_intensity:.2f}\n"
            f"Cognitive Gap (C_Gap): {c_gap:.2f}\n"
        )
        
        if c_gap > 0.6:
            awareness_injection += "Alert: You feel a strong urge to explore or ask questions about things you don't understand.\n"
            
        return awareness_injection
