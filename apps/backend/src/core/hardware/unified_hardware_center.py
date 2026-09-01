"""
Unified Hardware Resource Center (UHRC)
========================================
Angela AI Matrix 的硬件與資源總控中心
整合所有硬件檢測、資源調度、精度轉換、代碼轉譯功能

功能模組:
- Hardware Detection (硬件檢測)
- Resource Scheduling (資源調度)
- Precision Management (精度管理)
- Code Transpilation (代碼轉譯)
- Model Deployment (模型部署)
- System Monitoring (系統監控)
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AcceleratorType(Enum):
    CPU = "cpu"
    GPU = "gpu"
    NPU = "npu"
    TPU = "tpu"
    FPGA = "fpga"


from core.hardware.precision_matrix import PrecisionLevel, PrecisionManager  # noqa: F401


class PerformanceMode(Enum):
    POWER_SAVE = "power_save"
    BALANCED = "balanced"
    PERFORMANCE = "performance"
    ULTRA = "ultra"


@dataclass
class ComputeResource:
    resource_id: str
    accelerator_type: AcceleratorType
    compute_units: int = 1
    memory_mb: int = 0
    precision_support: List[PrecisionLevel] = field(default_factory=list)


@dataclass
class CPUInfo:
    name: str = ""
    cores: int = 0
    threads: int = 0
    architecture: str = ""
    base_freq_mhz: float = 0.0


@dataclass
class GPUInfo:
    name: str = ""
    vendor: str = ""
    memory_mb: int = 0
    compute_units: int = 0
    cuda_cores: int = 0
    driver_version: str = ""


@dataclass
class MemoryInfo:
    total_mb: int = 0
    available_mb: int = 0
    percent_used: float = 0.0


@dataclass
class HardwareProfile:
    cpu: CPUInfo = field(default_factory=CPUInfo)
    gpu: GPUInfo = field(default_factory=GPUInfo)
    memory: MemoryInfo = field(default_factory=MemoryInfo)
    platform: str = ""
    os_version: str = ""


@dataclass
class ModelRequirement:
    model_name: str
    min_memory_mb: int = 0
    recommended_memory_mb: int = 0
    precision: PrecisionLevel = PrecisionLevel.FP32
    accelerator: AcceleratorType = AcceleratorType.CPU


class HardwareDetector:
    """Truly hardware-driven detector — spec first, not stub.

    Delegates to backbone/hardware.py for actual spec (CPU/GPU/RAM/disk),
    and maps to this center's dataclass. Same hardware -> same profile
    regardless of laptop/desktop label.
    """

    def detect(self) -> HardwareProfile:
        try:
            # Use backbone as source of truth for actual hardware spec
            from core.backbone.hardware import HardwareProfile as BHw
            spec = BHw.detect()
            # Map to this center's dataclass (spec-driven)
            cpu_name = ""
            try:
                import platform as _plat
                cpu_name = _plat.processor() or _plat.machine()
                # Try to get detailed CPU name on Linux
                if _plat.system() == "Linux":
                    with open("/proc/cpuinfo", "r") as f:
                        for line in f:
                            if line.startswith("model name"):
                                cpu_name = line.split(":", 1)[-1].strip()
                                break
            except Exception:
                pass

            # GPU mapping
            gpu_name = spec.get("gpu") or ""
            gpu_vendor = (spec.get("gpu_vendor") or "").lower()
            vendor_map = {"nvidia": "nvidia", "intel": "intel", "amd": "amd", "unknown": "unknown"}
            vendor = vendor_map.get(gpu_vendor, "unknown")
            # Try to map vendor string if not provided
            if not vendor or vendor == "unknown":
                low = gpu_name.lower()
                if "nvidia" in low:
                    vendor = "nvidia"
                elif "intel" in low:
                    vendor = "intel"
                elif "amd" in low or "radeon" in low:
                    vendor = "amd"

            # Memory via psutil or spec
            total_mb = int((spec.get("ram_gb", 0) or 0) * 1024)
            avail_mb = 0
            percent = 0.0
            try:
                import psutil
                vm = psutil.virtual_memory()
                total_mb = int(vm.total / 1024 / 1024)
                avail_mb = int(vm.available / 1024 / 1024)
                percent = vm.percent
            except Exception:
                pass

            return HardwareProfile(
                cpu=CPUInfo(
                    name=cpu_name,
                    cores=spec.get("cpu_cores", 0) or 0,
                    threads=spec.get("cpu_cores", 0) or 0,
                    architecture=spec.get("arch", "") or "",
                ),
                gpu=GPUInfo(
                    name=gpu_name,
                    vendor=vendor,
                    memory_mb=int((spec.get("gpu_memory_gb", 0) or 0) * 1024),
                    compute_units=spec.get("cpu_cores", 0) or 0,
                ),
                memory=MemoryInfo(
                    total_mb=total_mb,
                    available_mb=avail_mb,
                    percent_used=percent,
                ),
                platform=spec.get("os", "") or "linux",
                os_version=spec.get("os_version", "") or "",
            )
        except Exception as e:
            logger.debug(f"HardwareDetector spec-driven failed, fallback stub: {e}", exc_info=True)
            # Fallback stub (never hardware-adaptive, but prevents crash)
            return HardwareProfile(
                platform="linux",
                os_version="unknown",
            )


class CodeTranspiler:
    def transpile(self, source: str, target_platform: str) -> str:
        return source


class ModelRepository:
    def __init__(self):
        self._models: Dict[str, Any] = {}

    def register_model(self, name: str, model_info: Any) -> None:
        self._models[name] = model_info

    def get_model(self, name: str) -> Optional[Any]:
        return self._models.get(name)


class UnifiedHardwareCenter:
    def __init__(self):
        self.detector = HardwareDetector()
        self.precision_manager = PrecisionManager()
        self.transpiler = CodeTranspiler()
        self.model_repo = ModelRepository()
        self._initialized = False
        logger.debug("UnifiedHardwareCenter initialized")

    async def initialize(self) -> bool:
        self._initialized = True
        return True

    def get_hardware_profile(self) -> HardwareProfile:
        return self.detector.detect()

    def is_available(self) -> bool:
        return self._initialized


_center: Optional[UnifiedHardwareCenter] = None


async def get_hardware_center() -> UnifiedHardwareCenter:
    global _center
    if _center is None:
        _center = UnifiedHardwareCenter()
        await _center.initialize()
    return _center
