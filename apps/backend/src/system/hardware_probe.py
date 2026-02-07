"""
Hardware Probe Module for Unified-AI-Project
Provides hardware detection and capability assessment for adaptive deployment.
"""

import logging
import platform
import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# Attempt to import psutil, provide fallback if not available
try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)

@dataclass
class CPUInfo:
    """CPU information structure"""
    cores_physical: int
    cores_logical: int
    frequency_max: float  # MHz
    frequency_current: float  # MHz
    architecture: str
    brand: str
    usage_percent: float

@dataclass
class GPUInfo:
    """GPU information structure"""
    name: str
    memory_total: int  # MB
    memory_available: int  # MB
    driver_version: str
    cuda_version: Optional[str] = None
    opencl_support: bool = False
    vulkan_support: bool = False

@dataclass
class MemoryInfo:
    """Memory information structure"""
    total: int  # MB
    available: int  # MB
    used: int  # MB
    usage_percent: float

@dataclass
class StorageInfo:
    """Storage information structure"""
    total: int  # GB
    available: int  # GB
    used: int  # GB
    disk_type: str  # SSD / HDD / Unknown

@dataclass
class NetworkInfo:
    """Network information structure"""
    bandwidth_download: float  # Mbps (estimated)
    bandwidth_upload: float  # Mbps (estimated)
    latency: float  # ms
    connection_type: str  # WiFi / Ethernet / Mobile

@dataclass
class HardwareProfile:
    """Complete hardware profile"""
    cpu: CPUInfo
    gpu: List[GPUInfo]
    memory: MemoryInfo
    storage: StorageInfo
    network: NetworkInfo
    platform: str
    os_version: str
    performance_tier: str  # Low / Medium / High / Extreme
    ai_capability_score: float  # 0 - 100

class HardwareProbe:
    """Main hardware detection and profiling class"""

    def __init__(self) -> None:
        self.platform_name = platform.system().lower()
        self.os_version = platform.version()

    def get_hardware_profile(self) -> HardwareProfile:
        """Detect all hardware components and create profile"""
        cpu_info = self._detect_cpu()
        gpu_info = self._detect_gpu()
        memory_info = self._detect_memory()
        storage_info = self._detect_storage()
        network_info = self._detect_network()
        
        performance_tier, ai_score = self._calculate_performance_metrics(
            cpu_info, gpu_info, memory_info
        )

        return HardwareProfile(
            cpu=cpu_info,
            gpu=gpu_info,
            memory=memory_info,
            storage=storage_info,
            network=network_info,
            platform=self.platform_name,
            os_version=self.os_version,
            performance_tier=performance_tier,
            ai_capability_score=ai_score
        )

    def _detect_cpu(self) -> CPUInfo:
        """Detect CPU information"""
        if psutil:
            cores_physical = psutil.cpu_count(logical=False) or 0
            cores_logical = psutil.cpu_count(logical=True) or 0
            usage = psutil.cpu_percent()
            # Frequency info might not be available on all platforms
            freq = psutil.cpu_freq()
            freq_max = freq.max if freq else 0.0
            freq_curr = freq.current if freq else 0.0
        else:
            cores_physical = 1
            cores_logical = 1
            usage = 0.0
            freq_max = 0.0
            freq_curr = 0.0

        return CPUInfo(
            cores_physical=cores_physical,
            cores_logical=cores_logical,
            frequency_max=freq_max,
            frequency_current=freq_curr,
            architecture=platform.machine(),
            brand=platform.processor() or "Unknown",
            usage_percent=usage
        )

    def _detect_gpu(self) -> List[GPUInfo]:
        """Detect GPU information (Improved Windows implementation)"""
        gpus = []
        if self.platform_name == "windows":
            try:
                import subprocess
                # Use wmic to get GPU info on Windows
                cmd = "wmic path win32_VideoController get name,AdapterRAM,DriverVersion /format:list"
                output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
                
                gpu_data = {}
                for line in output.splitlines():
                    if '=' in line:
                        key, value = line.split('=', 1)
                        gpu_data[key.strip()] = value.strip()
                    
                    if 'Name' in gpu_data and 'AdapterRAM' in gpu_data and 'DriverVersion' in gpu_data:
                        gpus.append(GPUInfo(
                            name=gpu_data['Name'],
                            memory_total=int(gpu_data['AdapterRAM']) // (1024 * 1024) if gpu_data['AdapterRAM'].isdigit() else 4096,
                            memory_available=0, # Hard to get real-time availability via wmic
                            driver_version=gpu_data['DriverVersion']
                        ))
                        gpu_data = {}
            except Exception as e:
                logger.debug(f"Failed to detect GPU via wmic: {e}")

        if not gpus:
            # Fallback mock
            return [GPUInfo(
                name="Generic GPU",
                memory_total=4096,
                memory_available=2048,
                driver_version="Unknown"
            )]
        return gpus

    def _detect_memory(self) -> MemoryInfo:
        """Detect Memory information"""
        if psutil:
            mem = psutil.virtual_memory()
            return MemoryInfo(
                total=mem.total // (1024 * 1024),
                available=mem.available // (1024 * 1024),
                used=mem.used // (1024 * 1024),
                usage_percent=mem.percent
            )
        return MemoryInfo(total=8192, available=4096, used=4096, usage_percent=50.0)

    def _detect_storage(self) -> StorageInfo:
        """Detect Storage information"""
        if psutil:
            usage = psutil.disk_usage('/')
            return StorageInfo(
                total=usage.total // (1024**3),
                available=usage.free // (1024**3),
                used=usage.used // (1024**3),
                disk_type="Unknown"
            )
        return StorageInfo(total=512, available=256, used=256, disk_type="SSD")

    def _detect_network(self) -> NetworkInfo:
        """Detect Network information"""
        return NetworkInfo(
            bandwidth_download=100.0,
            bandwidth_upload=50.0,
            latency=10.0,
            connection_type="Ethernet"
        )

    def _calculate_performance_metrics(self, cpu, gpu, memory) -> tuple:
        """Calculate performance tier and AI capability score"""
        score = 0.0
        # Simple scoring logic
        score += cpu.cores_logical * 2
        score += sum(g.memory_total for g in gpu) / 1024 * 10
        score += memory.total / 1024 * 5
        
        # Normalize score to 0-100
        score = min(score, 100.0)
        
        if score > 80: tier = "Extreme"
        elif score > 60: tier = "High"
        elif score > 40: tier = "Medium"
        else: tier = "Low"
        
        return tier, score

    def get_cluster_capability(self) -> Dict[str, Any]:
        """Assess node's capability for cluster participation"""
        profile = self.get_hardware_profile()
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

def get_hardware_profile() -> HardwareProfile:
    """Helper function to get current hardware profile"""
    probe = HardwareProbe()
    return probe.get_hardware_profile()
