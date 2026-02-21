"""
Unified Hardware Detection Module for Angela AI
===============================================
Merged and optimized from:
- system/hardware_probe.py
- core/services/hardware_detector.py
- core/system/hardware_detector.py

Provides a single source of truth for hardware capabilities, performance tiers,
and model recommendations (Ollama).
"""

import os
import platform
import logging
import subprocess
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from pathlib import Path

# Attempt to import psutil, provide fallback if not available
try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)

class AcceleratorType(Enum):
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    APPLE_METAL = "apple_metal"
    CPU_AVX512 = "cpu_avx512"
    CPU_AVX2 = "cpu_avx2"
    CPU_AVX = "cpu_avx"
    CPU_SSE42 = "cpu_sse42"
    NONE = "none"

@dataclass
class HardwareProfile:
    """Complete hardware profile for the system."""
    platform: str
    os_version: str
    cpu_brand: str
    cpu_cores_physical: int
    cpu_cores_logical: int
    cpu_flags: List[str] = field(default_factory=list)
    
    ram_total_gb: float = 0.0
    ram_available_gb: float = 0.0
    
    accelerator_type: AcceleratorType = AcceleratorType.NONE
    accelerator_name: str = "Unknown"
    vram_mb: int = 0
    
    is_laptop: bool = False
    is_virtual: bool = False
    disk_free_gb: float = 0.0
    
    performance_tier: str = "Low"  # Low / Medium / High / Extreme
    ai_capability_score: float = 0.0  # 0 - 100

class SystemHardwareProbe:
    """High-fidelity hardware detector."""

    def __init__(self):
        self.platform_name = platform.system().lower()
        self.os_version = platform.version()

    def detect(self) -> HardwareProfile:
        """Execute full hardware detection."""
        logger.info("Initializing unified hardware detection...")

        # 1. CPU Detection
        cpu_cores_phys = psutil.cpu_count(logical=False) if psutil else 1
        cpu_cores_log = psutil.cpu_count(logical=True) if psutil else 1
        cpu_brand = platform.processor() or "Unknown"
        cpu_flags = self._detect_cpu_flags()

        # 2. RAM Detection
        ram_total, ram_avail = self._detect_ram()

        # 3. GPU Detection
        accel_type, accel_name, vram = self._detect_gpu()

        # 4. Fallback to CPU acceleration if no GPU
        if accel_type == AcceleratorType.NONE:
            accel_type, accel_name = self._refine_cpu_acceleration(cpu_flags)

        # 5. Environment
        is_laptop = self._detect_laptop()
        is_virtual = self._detect_virtual()
        disk_free = self._detect_disk_space()

        profile = HardwareProfile(
            platform=self.platform_name,
            os_version=self.os_version,
            cpu_brand=cpu_brand,
            cpu_cores_physical=cpu_cores_phys or 1,
            cpu_cores_logical=cpu_cores_log or 1,
            cpu_flags=cpu_flags,
            ram_total_gb=ram_total,
            ram_available_gb=ram_avail,
            accelerator_type=accel_type,
            accelerator_name=accel_name,
            vram_mb=vram,
            is_laptop=is_laptop,
            is_virtual=is_virtual,
            disk_free_gb=disk_free
        )

        # 6. Scoring
        self._calculate_tier(profile)
        
        logger.info(f"Hardware detected: {profile.accelerator_type.value} | Tier: {profile.performance_tier}")
        return profile

    def _detect_cpu_flags(self) -> List[str]:
        flags = []
        if self.platform_name == "linux":
            try:
                with open('/proc/cpuinfo') as f:
                    for line in f:
                        if 'flags' in line:
                            return line.split(':')[-1].strip().split()
            except Exception: pass
        elif self.platform_name == "windows":
            # Windows flags are harder; usually inferred or via specialized tools
            # We can use 'coreinfo' if available, but for now we fallback
            pass
        elif self.platform_name == "darwin":
            try:
                result = subprocess.run(['sysctl', '-a'], capture_output=True, text=True)
                for line in result.stdout.splitlines():
                    if 'hw.optional.' in line and ': 1' in line:
                        flags.append(line.split('.')[2].split(':')[0])
            except Exception: pass
        return flags

    def _detect_ram(self) -> Tuple[float, float]:
        if psutil:
            mem = psutil.virtual_memory()
            return mem.total / (1024**3), mem.available / (1024**3)
        return 8.0, 4.0

    def _detect_gpu(self) -> Tuple[AcceleratorType, str, int]:
        # 1. NVIDIA
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines and lines[0]:
                    parts = lines[0].split(',')
                    return AcceleratorType.NVIDIA, parts[0].strip(), int(parts[1].strip())
        except Exception: pass

        # 2. Apple Metal
        if self.platform_name == "darwin":
            return AcceleratorType.APPLE_METAL, "Apple Silicon", 0 # macOS unified memory is tricky

        # 3. AMD (ROCm)
        try:
            result = subprocess.run(['rocm-smi', '--showid'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return AcceleratorType.AMD, "AMD GPU", 0
        except Exception: pass

        # 4. Windows WMIC Fallback
        if self.platform_name == "windows":
            try:
                cmd = "wmic path win32_VideoController get name,AdapterRAM /format:list"
                output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
                name, ram = "", 0
                for line in output.splitlines():
                    if 'Name=' in line: name = line.split('=')[1].strip()
                    if 'AdapterRAM=' in line: 
                        raw_ram = line.split('=')[1].strip()
                        if raw_ram.isdigit(): ram = int(raw_ram) // (1024*1024)
                if name:
                    # Very crude brand detection
                    atype = AcceleratorType.NONE
                    if "NVIDIA" in name.upper(): atype = AcceleratorType.NVIDIA
                    elif "AMD" in name.upper() or "RADEON" in name.upper(): atype = AcceleratorType.AMD
                    elif "INTEL" in name.upper(): atype = AcceleratorType.INTEL
                    return atype, name, ram
            except Exception: pass

        return AcceleratorType.NONE, "None", 0

    def _refine_cpu_acceleration(self, flags: List[str]) -> Tuple[AcceleratorType, str]:
        if 'avx512f' in flags or 'avx512' in flags:
            return AcceleratorType.CPU_AVX512, "CPU AVX-512"
        if 'avx2' in flags:
            return AcceleratorType.CPU_AVX2, "CPU AVX2"
        if 'avx' in flags:
            return AcceleratorType.CPU_AVX, "CPU AVX"
        return AcceleratorType.NONE, "CPU Baseline"

    def _detect_laptop(self) -> bool:
        if psutil and hasattr(psutil, "sensors_battery"):
            if psutil.sensors_battery() is not None:
                return True
        return False

    def _detect_virtual(self) -> bool:
        indicators = ['/proc/vz', '/proc/bc', '.dockerenv', '/sys/hypervisor']
        for i in indicators:
            if os.path.exists(i): return True
        return False

    def _detect_disk_space(self) -> float:
        try:
            import shutil
            return shutil.disk_usage('.').free / (1024**3)
        except Exception: return 0.0

    def _calculate_tier(self, profile: HardwareProfile):
        score = 0.0
        score += profile.cpu_cores_logical * 2
        score += profile.ram_total_gb * 4
        
        if profile.accelerator_type == AcceleratorType.NVIDIA:
            score += 40 + (profile.vram_mb / 1024) * 2
        elif profile.accelerator_type == AcceleratorType.APPLE_METAL:
            score += 35
        elif profile.accelerator_type == AcceleratorType.AMD:
            score += 30
        
        profile.ai_capability_score = min(100.0, score)
        
        if score > 80: profile.performance_tier = "Extreme"
        elif score > 60: profile.performance_tier = "High"
        elif score > 40: profile.performance_tier = "Medium"
        else: profile.performance_tier = "Low"

    def get_ollama_recommendations(self, profile: HardwareProfile) -> Dict[str, Any]:
        """Specific recommendations for LLM running (Ollama)."""
        ram = profile.ram_available_gb
        
        recommendations = []
        if ram < 2:
            recommendations.append({"name": "llama3.2:1b", "notes": "Ultra-lite for limited RAM"})
        elif ram < 4:
            recommendations.append({"name": "qwen2.5:1.5b", "notes": "Efficient for entry-level"})
        elif ram < 8:
            recommendations.append({"name": "llama3.2:3b", "notes": "Balanced for medium RAM"})
        else:
            recommendations.append({"name": "llama3.1:8b", "notes": "High performance standard"})
            
        return {
            "gpu_layers": -1 if profile.accelerator_type in [AcceleratorType.NVIDIA, AcceleratorType.AMD] else 0,
            "models": recommendations,
            "parallel": min(4, profile.cpu_cores_logical)
        }

class ModeRecommender:
    """
    Recommends Angela mode based on hardware capabilities and configurations.
    Ported from core/system/hardware_detector.py
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.detector = SystemHardwareProbe()

    def recommend_mode(self, preferred_mode: Optional[str] = None) -> Tuple[str, str, Dict[str, Any]]:
        """
        Recommend mode: (mode_name, reason, mode_config)
        """
        profile = self.detector.detect()
        
        # Priority 1: User preference (if specified and compatible)
        if preferred_mode and preferred_mode in self.config.get('angela_modes', {}):
            mode_config = self.config['angela_modes'][preferred_mode]
            meets_req, reason = self._meets_requirements(profile, mode_config.get('hardware_requirements', {}))
            if meets_req:
                return preferred_mode, f"User selected {preferred_mode}, hardware compatible", mode_config
            else:
                logger.warning(f"Preferred mode {preferred_mode} not compatible: {reason}")
        
        # Priority 2: Auto-selection based on profile
        modes_to_check = ['extended', 'standard', 'lite']
        for mode_name in modes_to_check:
            if mode_name not in self.config.get('angela_modes', {}):
                continue
            
            mode_config = self.config['angela_modes'][mode_name]
            meets_req, reason = self._meets_requirements(profile, mode_config.get('hardware_requirements', {}))
            if meets_req:
                return mode_name, f"Auto-selected {mode_name} based on hardware: {profile.ram_total_gb:.1f}GB RAM, {profile.accelerator_name}", mode_config
        
        # Fallback
        return 'lite', "Fallback to Lite mode", self.config.get('angela_modes', {}).get('lite', {})

    def _meets_requirements(self, profile: HardwareProfile, requirements: Dict[str, Any]) -> Tuple[bool, str]:
        if profile.ram_total_gb < requirements.get('min_ram_gb', 0):
            return False, f"RAM: {profile.ram_total_gb:.1f}GB < {requirements['min_ram_gb']}GB required"
        
        if requirements.get('gpu_required', False) and profile.accelerator_type == AcceleratorType.NONE:
            return False, "GPU required but not detected"
            
        return True, "Meets all requirements"

    def get_cluster_capability(self) -> Dict[str, Any]:
        """Assess node's capability for cluster participation (Ported from legacy HardwareProbe)"""
        profile = self.detect()
        score = profile.ai_capability_score
        
        # Logic to determine preferred role
        if score > 70:
            preferred_role = "master"
        else:
            preferred_role = "worker"
            
        return {
            "score": score,
            "preferred_role": preferred_role,
            "can_participate": score > 20,
            "max_tasks": int(score / 10) + 1
        }

    def get_hardware_profile(self) -> HardwareProfile:
        """Shim for compatibility with legacy HardwareProbe callers."""
        return self.detect()

def get_profile() -> HardwareProfile:
    """Helper function to get current hardware profile"""
    probe = SystemHardwareProbe()
    return probe.detect()
