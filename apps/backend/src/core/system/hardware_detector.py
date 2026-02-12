"""
Hardware Detection Module

Detects system hardware capabilities and recommends Angela mode.
Supports: Windows, macOS, Linux
"""

import os
import platform
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class HardwareProfile:
    """Hardware profile"""
    ram_gb: float
    cpu_cores: int
    has_gpu: bool
    gpu_vram_gb: float
    gpu_name: Optional[str]
    os_type: str
    is_laptop: bool
    disk_space_gb: float
    
    def meets_requirements(self, requirements: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if hardware meets mode requirements"""
        if self.ram_gb < requirements.get('min_ram_gb', 0):
            return False, f"RAM: {self.ram_gb}GB < {requirements['min_ram_gb']}GB required"
        
        if requirements.get('gpu_required', False) and not self.has_gpu:
            return False, "GPU required but not detected"
        
        if self.has_gpu and self.gpu_vram_gb < requirements.get('gpu_vram_gb', 0):
            return False, f"GPU VRAM: {self.gpu_vram_gb}GB < {requirements['gpu_vram_gb']}GB required"
        
        return True, "Meets all requirements"


class HardwareDetector:
    """
    Hardware detector - cross-platform
    
    Detects:
    - RAM (GB)
    - CPU cores
    - GPU availability and VRAM
    - Operating system
    - Device type (laptop/desktop)
    """
    
    def __init__(self):
        self.profile: Optional[HardwareProfile] = None
    
    def detect(self) -> HardwareProfile:
        """Detect hardware capabilities"""
        ram_gb = self._detect_ram()
        cpu_cores = self._detect_cpu()
        has_gpu, gpu_vram_gb, gpu_name = self._detect_gpu()
        os_type = platform.system().lower()
        is_laptop = self._detect_laptop()
        disk_space_gb = self._detect_disk_space()
        
        self.profile = HardwareProfile(
            ram_gb=ram_gb,
            cpu_cores=cpu_cores,
            has_gpu=has_gpu,
            gpu_vram_gb=gpu_vram_gb,
            gpu_name=gpu_name,
            os_type=os_type,
            is_laptop=is_laptop,
            disk_space_gb=disk_space_gb
        )
        
        logger.info(f"Hardware detected: {self.profile}")
        return self.profile
    
    def _detect_ram(self) -> float:
        """Detect total RAM in GB"""
        try:
            import psutil
            return psutil.virtual_memory().total / (1024 ** 3)
        except ImportError:
            # Fallback using os
            if platform.system() == "Windows":
                return self._detect_ram_windows()
            elif platform.system() == "Darwin":
                return self._detect_ram_macos()
            else:
                return self._detect_ram_linux()
    
    def _detect_ram_windows(self) -> float:
        """Detect RAM on Windows"""
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            c_ulong = ctypes.c_ulong
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", c_ulong),
                    ("dwMemoryLoad", c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            
            memStatus = MEMORYSTATUSEX()
            memStatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            kernel32.GlobalMemoryStatusEx(ctypes.byref(memStatus))
            return memStatus.ullTotalPhys / (1024 ** 3)
        except Exception as e:
            logger.error(f"Error detecting Windows RAM: {e}")
            return 8.0  # Default assumption
    
    def _detect_ram_macos(self) -> float:
        """Detect RAM on macOS"""
        try:
            import subprocess
            result = subprocess.run(['sysctl', 'hw.memsize'], capture_output=True, text=True)
            ram_bytes = int(result.stdout.split(':')[1].strip())
            return ram_bytes / (1024 ** 3)
        except Exception as e:
            logger.error(f"Error detecting macOS RAM: {e}")
            return 8.0
    
    def _detect_ram_linux(self) -> float:
        """Detect RAM on Linux"""
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        kb = int(line.split()[1])
                        return kb / (1024 ** 2)
        except Exception as e:
            logger.error(f"Error detecting Linux RAM: {e}")
            return 8.0
    
    def _detect_cpu(self) -> int:
        """Detect CPU cores"""
        try:
            import os
            return os.cpu_count() or 4
        except (OSError, AttributeError) as e:
            logger.debug(f"CPU核數探測失敗（可忽略）: {e}")
            return 4
    
    def _detect_gpu(self) -> Tuple[bool, float, Optional[str]]:
        """
        Detect GPU and VRAM
        Returns: (has_gpu, vram_gb, gpu_name)
        """
        # Try multiple methods
        methods = [
            self._detect_gpu_pytorch,
            self._detect_gpu_nvidia_smi,
            self._detect_gpu_platform_specific
        ]
        
        for method in methods:
            try:
                result = method()
                if result[0]:  # has_gpu is True
                    return result
            except Exception as e:
                logger.debug(f"GPU detection method {method.__name__} failed: {e}")
                continue
        
        return False, 0.0, None
    
    def _detect_gpu_pytorch(self) -> Tuple[bool, float, Optional[str]]:
        """Detect GPU using PyTorch"""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                vram_bytes = torch.cuda.get_device_properties(0).total_memory
                vram_gb = vram_bytes / (1024 ** 3)
                return True, vram_gb, gpu_name
        except ImportError:
            pass
        return False, 0.0, None
    
    def _detect_gpu_nvidia_smi(self) -> Tuple[bool, float, Optional[str]]:
        """Detect GPU using nvidia-smi"""
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(',')
                if len(parts) >= 2:
                    gpu_name = parts[0].strip()
                    vram_str = parts[1].strip().replace(' MiB', '').replace(' MB', '')
                    vram_gb = int(vram_str) / 1024
                    return True, vram_gb, gpu_name
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            pass

        return False, 0.0, None
    
    def _detect_gpu_platform_specific(self) -> Tuple[bool, float, Optional[str]]:
        """Platform-specific GPU detection"""
        if platform.system() == "Windows":
            return self._detect_gpu_windows()
        elif platform.system() == "Darwin":
            return self._detect_gpu_macos()
        else:
            return self._detect_gpu_linux()
    
    def _detect_gpu_windows(self) -> Tuple[bool, float, Optional[str]]:
        """Windows-specific GPU detection using WMI"""
        try:
            import subprocess
            result = subprocess.run(
                ['wmic', 'path', 'win32_VideoController', 'get', 'Name,AdapterRAM'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.rsplit(' ', 1)
                        if len(parts) >= 2:
                            gpu_name = parts[0].strip()
                            try:
                                vram_bytes = int(parts[1])
                                vram_gb = vram_bytes / (1024 ** 3)
                                return True, vram_gb, gpu_name
                            except ValueError:
                                continue
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            pass

        return False, 0.0, None
    
    def _detect_gpu_macos(self) -> Tuple[bool, float, Optional[str]]:
        """macOS-specific GPU detection"""
        try:
            import subprocess
            # Check for Metal-capable GPU
            result = subprocess.run(
                ['system_profiler', 'SPDisplaysDataType'],
                capture_output=True, text=True
            )
            if 'Metal' in result.stdout or 'Intel' in result.stdout or 'AMD' in result.stdout:
                # macOS doesn't easily expose VRAM, assume integrated or discrete
                if 'Apple' in result.stdout:
                    return True, 8.0, "Apple Silicon GPU"
                else:
                    return True, 4.0, "Discrete GPU"
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            pass

        return False, 0.0, None
    
    def _detect_gpu_linux(self) -> Tuple[bool, float, Optional[str]]:
        """Linux-specific GPU detection"""
        try:
            # Check for NVIDIA GPU
            if os.path.exists('/proc/driver/nvidia/gpus'):
                return True, 4.0, "NVIDIA GPU"
            # Check for AMD GPU
            if os.path.exists('/sys/class/drm/card0/device'):
                return True, 4.0, "AMD GPU"
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            pass

        return False, 0.0, None
    
    def _detect_laptop(self) -> bool:
        """Detect if device is a laptop"""
        if platform.system() == "Windows":
            try:
                import subprocess
                result = subprocess.run(
                    ['wmic', 'path', 'Win32_SystemEnclosure', 'get', 'ChassisTypes'],
                    capture_output=True, text=True
                )
                # Chassis type 9, 10, 11, 12, 14, 15, 16, 17 are laptops
                laptop_types = {'9', '10', '11', '12', '14', '15', '16', '17'}
                for line in result.stdout.split('\n'):
                    if any(t in line for t in laptop_types):
                        return True
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                pass

        
        # Default assumption: if it has battery, it's likely a laptop
        try:
            import psutil
            battery = psutil.sensors_battery()
            if battery is not None:
                return True
        except (ImportError, OSError, AttributeError) as e:
            logger.debug(f"電池探測失敗（可忽略）: {e}")
            pass
        
        return False
    
    def _detect_disk_space(self) -> float:
        """Detect available disk space in GB"""
        try:
            import shutil
            stat = shutil.disk_usage('.')
            return stat.free / (1024 ** 3)
        except (OSError, AttributeError) as e:
            logger.debug(f"磁盤空間探測失敗（可忽略）: {e}")
            return 100.0  # Default assumption


class ModeRecommender:
    """
    Recommends Angela mode based on hardware and user preferences
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.detector = HardwareDetector()
    
    def recommend_mode(self, preferred_mode: Optional[str] = None) -> Tuple[str, str, Dict[str, Any]]:
        """
        Recommend mode
        
        Returns:
            (mode_name, reason, mode_config)
        """
        profile = self.detector.detect()
        
        # Priority 1: User preference (if specified and compatible)
        if preferred_mode and preferred_mode in self.config.get('angela_modes', {}):
            mode_config = self.config['angela_modes'][preferred_mode]
            meets_req, reason = profile.meets_requirements(mode_config.get('hardware_requirements', {}))
            if meets_req:
                return preferred_mode, f"User selected {preferred_mode}, hardware compatible", mode_config
            else:
                logger.warning(f"Preferred mode {preferred_mode} not compatible: {reason}")
        
        # Priority 2: Check modes from best to fallback
        modes_to_check = ['extended', 'standard', 'lite']
        
        for mode_name in modes_to_check:
            if mode_name not in self.config.get('angela_modes', {}):
                continue
            
            mode_config = self.config['angela_modes'][mode_name]
            meets_req, reason = profile.meets_requirements(mode_config.get('hardware_requirements', {}))
            
            if meets_req:
                return mode_name, f"Auto-selected {mode_name} based on hardware: {profile.ram_gb:.1f}GB RAM, {profile.gpu_name or 'no GPU'}", mode_config
        
        # Fallback: Lite mode should always work
        return 'lite', "Fallback to Lite mode", self.config.get('angela_modes', {}).get('lite', {})
    
    def check_upgrade_feasibility(self, current_mode: str, target_mode: str) -> Tuple[bool, str]:
        """Check if upgrade from current_mode to target_mode is feasible"""
        profile = self.detector.detect()
        
        if target_mode not in self.config.get('angela_modes', {}):
            return False, f"Unknown mode: {target_mode}"
        
        target_config = self.config['angela_modes'][target_mode]
        meets_req, reason = profile.meets_requirements(target_config.get('hardware_requirements', {}))
        
        return meets_req, reason if meets_req else f"Cannot upgrade: {reason}"
    
    def should_auto_switch(self, current_mode: str) -> Optional[str]:
        """
        Check if auto-switch is recommended based on current system load
        Returns target mode or None
        """
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            
            auto_config = self.config.get('auto_mode_detection', {})
            thresholds = auto_config.get('thresholds', {})
            
            # Check if we need to downgrade (high resource usage)
            if memory.percent > thresholds.get('downgrade', {}).get('memory_percent', 80):
                if current_mode == 'extended':
                    return 'standard'
                elif current_mode == 'standard':
                    return 'lite'
            
            if cpu > thresholds.get('downgrade', {}).get('cpu_percent', 90):
                if current_mode == 'extended':
                    return 'standard'
                elif current_mode == 'standard':
                    return 'lite'
            
            # Check if we can upgrade (low resource usage)
            if memory.percent < thresholds.get('upgrade', {}).get('memory_percent', 50):
                if cpu < thresholds.get('upgrade', {}).get('cpu_percent', 50):
                    if current_mode == 'lite':
                        return 'standard'
                    elif current_mode == 'standard':
                        return 'extended'
            
            return None
            
        except ImportError:
            logger.warning("psutil not available, auto-switch disabled")
            return None


# Convenience function
def detect_hardware_and_recommend_mode(config: Dict[str, Any], preferred: Optional[str] = None) -> Tuple[str, str, Dict[str, Any]]:
    """Detect hardware and recommend mode"""
    recommender = ModeRecommender(config)
    return recommender.recommend_mode(preferred)
