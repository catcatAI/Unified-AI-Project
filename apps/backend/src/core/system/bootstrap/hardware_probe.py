"""
Hardware Probing & AI Tiering System
Formalized from install_angela.py
"""

import os
import sys
import platform
import subprocess
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

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
    Replaces the fragmented logic in root-level installation scripts.
    """
    
    def __init__(self):
        self.specs: Optional[HardwareSpecs] = None

    def probe(self) -> HardwareSpecs:
        """Execute full hardware detection."""
        try:
            cores = os.cpu_count() or 4
            memory = self._get_memory_gb()
            gpu_name = self._detect_gpu()
            
            # AI Capability Scoring (Formalized from install_angela.py)
            score = cores * 2 + (memory // 4) * 5
            if any(kw in gpu_name.upper() for kw in ["RTX", "GTX", "NVIDIA", "APPLE", "METAL"]):
                score += 40 if "RTX" in gpu_name.upper() else 30
            
            tier = self._assign_tier(score)
            
            self.specs = HardwareSpecs(
                platform=sys.platform,
                architecture=platform.machine(),
                processor=platform.processor(),
                cpu_cores=cores,
                memory_gb=memory,
                gpu=gpu_name,
                performance_tier=tier,
                ai_capability_score=score
            )
            return self.specs
        except Exception as e:
            logger.error(f"Hardware probe failed: {e}", exc_info=True)
            # Safe Fallback
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

    def _get_memory_gb(self) -> int:
        try:
            import psutil
            return int(psutil.virtual_memory().total // (1024**3))
        except ImportError:
            # Fallback for when psutil is not yet installed during bootstrap
            if sys.platform == "win32":
                try:
                    res = subprocess.run(["wmic", "ComputerSystem", "get", "TotalPhysicalMemory"], 
                                       capture_output=True, text=True)
                    lines = res.stdout.strip().split("\n")
                    if len(lines) > 1:
                        return int(lines[1].strip()) // (1024**3)
                except: pass
            return 8

    def _detect_gpu(self) -> str:
        try:
            if sys.platform == "win32":
                res = subprocess.run(["powershell", "-Command", 
                                    "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"],
                                    capture_output=True, text=True, timeout=5)
                name = res.stdout.strip().split("\n")[0]
                if name: return name
            elif sys.platform == "darwin":
                return "Apple Metal"
            else:
                res = subprocess.run(["lspci"], capture_output=True, text=True, timeout=5)
                for line in res.stdout.split("\n"):
                    if "VGA" in line or "3D" in line:
                        return line.split(":")[-1].strip()
        except Exception: pass
        return "Unknown/Software"

    def _assign_tier(self, score: int) -> str:
        if score > 80: return "Extreme"
        if score > 60: return "High"
        if score > 40: return "Medium"
        return "Low"

    def get_performance_constants(self) -> Dict[str, Any]:
        """Maps tier to actual system constants."""
        if not self.specs: self.probe()
        
        tier_map = {
            "Extreme": {"max_fps": 60, "llm_model": "gemini-1.5-pro-latest", "precision": 1.0},
            "High":    {"max_fps": 60, "llm_model": "gemini-pro", "precision": 0.8},
            "Medium":  {"max_fps": 30, "llm_model": "gemini-pro", "precision": 0.5},
            "Low":     {"max_fps": 24, "llm_model": "gemini-1.5-flash", "precision": 0.3},
        }
        return tier_map.get(self.specs.performance_tier, tier_map["Medium"])
