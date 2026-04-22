import logging
import random
import time
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

from .autonomous.digital_life_constants import GovernanceConstants

class GSIGovernance:
    """
    GSI-4 Governance Core (M6 Module).
    Numbers are grounded in GovernanceConstants.
    """
    def __init__(self):
        # M2: Exploration Factor (Grounded)
        self.E_M2 = GovernanceConstants.EXPLORATION_BASE_FACTOR
        self.V_total = 0.0
        self.C_gap = 0.0
        self.active_identity = "Standard"

    def calculate_hsm(self) -> float:
        return self.C_gap * self.E_M2

    def update_v_total(self, is_strategic: bool = False):
        increment = GovernanceConstants.STRATEGIC_VALUE_INCREMENT if is_strategic else 0.01
        self.V_total = min(1.0, self.V_total + increment)
        
        if self.V_total > GovernanceConstants.ALPHA_MODE_THRESHOLD:
            # Alpha mode: Stable yet curious
            self.E_M2 = GovernanceConstants.EXPLORATION_BASE_FACTOR
        else:
            self.E_M2 = GovernanceConstants.EXPLORATION_BASE_FACTOR / 2

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
