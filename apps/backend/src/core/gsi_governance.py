import logging
import random
import time
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class GSIGovernance:
    """
    GSI-4 Governance Core (M6 Module - Hypothalamus).
    Manages logic homeostasis and dynamic exploration.
    """
    def __init__(self):
        # M2: Exploration Factor (Fixed default)
        self.E_M2 = 0.1
        
        # M6: Total System Value (V_Total)
        self.V_total = 0.0
        
        # HSM State
        self.C_gap = 0.0 # Cognitive Deficit
        
        # Identity State
        self.active_identity = "Standard"

    def calculate_hsm(self) -> float:
        """HSM = C_Gap * E_M2"""
        return self.C_gap * self.E_M2

    def update_v_total(self, incremental_value: float):
        """Updates system value and triggers alpha mode if needed."""
        self.V_total = min(1.0, self.V_total + incremental_value)
        if self.V_total > 0.65:
            logger.info(f"⚡ [M6] GSI-4 Alpha Mode triggered (V_total: {self.V_total:.2f})")
            # Trigger: 90% Stable + 10% Exploration
            self.E_M2 = 0.1
        else:
            self.E_M2 = 0.05 # Conservative mode

    def detect_cognitive_gap(self, task_result: Dict[str, Any]):
        """M3/HSM: Monitors if current method failed to meet goals."""
        if task_result.get("status") == "error" or task_result.get("confidence", 1.0) < 0.3:
            self.C_gap = min(1.0, self.C_gap + 0.2)
            logger.warning(f"🔍 [HSM] Cognitive Gap detected: {self.C_gap:.2f}. Increasing exploration.")
        else:
            self.C_gap = max(0.0, self.C_gap - 0.1)

    def get_routing_decision(self, context: str) -> str:
        """
        Identity Active = f(C_Gap, M6_History, Context)
        Decides whether to take a 'Standard' or 'Exploratory' path.
        """
        hsm_score = self.calculate_hsm()
        if random.random() < hsm_score or random.random() < self.E_M2:
            return "Exploratory"
        return "Standard"

# Singleton instance
governance_core = GSIGovernance()
