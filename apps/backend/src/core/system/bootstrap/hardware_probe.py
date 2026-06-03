"""
Hardware Probing & AI Tiering System
Formalized from install_angela.py
"""

import os
import sys
import platform
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class HardwareSpecs:
    platform: str
    architecture: str
    processor: str
    cpu_cores: int
    memory_gb: int
    gpu: str
    performance_tier: str
    ai_capability_score: int

class HardwareProbe:
    """
    Surgically detects hardware capabilities and assigns performance tiers.
    """
    
    def __init__(self):
        from app_config_loader import get_bootstrap_config
        self.bootstrap_config = get_bootstrap_config()
        self.specs: Optional[HardwareSpecs] = None

    def probe(self) -> HardwareSpecs:
        """Execute full hardware detection."""
        try:
            cores = os.cpu_count() or 4
            memory = self._get_memory_gb()
            gpu_name = self._detect_gpu()
            
            # AI Capability Scoring from config
            weights = self.bootstrap_config.get("scoring_weights", {})
            score = cores * weights.get("cpu_core_multiplier", 2) + memory * weights.get("memory_gb_multiplier", 1.25)
            
            if any(kw in gpu_name.upper() for kw in ["RTX", "GTX", "NVIDIA", "APPLE", "METAL"]):
                bonus = weights.get("gpu_rtx_bonus", 40) if "RTX" in gpu_name.upper() else weights.get("gpu_standard_bonus", 30)
                score += bonus
            
            tier = self._assign_tier(score)
            
            self.specs = HardwareSpecs(
                platform=sys.platform,
                architecture=platform.machine(),
                processor=platform.processor(),
                cpu_cores=cores,
                memory_gb=memory,
                gpu=gpu_name,
                performance_tier=tier,
                ai_capability_score=int(score)
            )
            return self.specs
        except Exception as e:
            logger.error(f"Hardware probe failed: {e}", exc_info=True)
            return HardwareSpecs(
                platform=sys.platform,
                architecture=platform.machine(),
                processor="Unknown",
                cpu_cores=4,
                memory_gb=8,
                gpu="Unknown/Software",
                performance_tier="Medium",
                ai_capability_score=50
            )

    def _assign_tier(self, score: float) -> str:
        """Assign tier."""
        tiers = self.bootstrap_config.get("hardware_tiers", {})
        # Sort tiers by threshold descending to find the highest match
        sorted_tiers = sorted(tiers.items(), key=lambda x: x[1].get("score_threshold", 0), reverse=True)
        for tier_name, config in sorted_tiers:
            if score >= config.get("score_threshold", 0):
                return tier_name
        return "Low"

    def get_performance_constants(self) -> Dict[str, Any]:
        """Maps tier to actual system constants from config."""
        if not self.specs: self.probe()
        tiers = self.bootstrap_config.get("hardware_tiers", {})
        tier_config = tiers.get(self.specs.performance_tier, tiers.get("Medium", {}))
        
        # Strip score_threshold from the constants
        return {k: v for k, v in tier_config.items() if k != "score_threshold"}
