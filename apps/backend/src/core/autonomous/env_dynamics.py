import psutil
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class EnvironmentDynamics:
    """
    Computes dynamic thresholds based on actual hardware capability.
    Grounds Angela's biological life in the reality of your laptop.
    """
    def __init__(self):
        self.cpu_baseline = self._calibrate_cpu()
        self.adaptation_factor = 1.0 # Adjusts sensitivity to hardware limits

    def _calibrate_cpu(self) -> float:
        """Measures CPU response time to set the baseline."""
        start = time.time()
        _ = [i**2 for i in range(1000000)]
        duration = time.time() - start
        return duration

    def get_dynamic_threshold(self, key: str, default: float) -> float:
        """Dynamically scales thresholds based on hardware speed."""
        # If your machine is slow (duration > 0.05), we relax the timing thresholds
        if self.cpu_baseline > 0.05:
            return default * 1.5 
        return default

    def calculate_metabolic_rate(self) -> float:
        """Metabolic rate tied to CPU/RAM load."""
        cpu = psutil.cpu_percent()
        # High load -> Higher metabolic rate
        return 0.05 + (cpu / 100.0) * 0.1
