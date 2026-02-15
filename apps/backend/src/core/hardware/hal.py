"""
Angela AI v6.0 - Hardware Abstraction Layer (HAL)
硬件抽象层

Provides unified access to diverse hardware architectures (CPU, GPU, TPU, etc.)
and instruction sets (CISC, RISC, EPIC, VLIW).

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-04
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple, Union
from enum import Enum
import platform
import cpuinfo
import psutil
import logging
logger = logging.getLogger(__name__)


class ArchitectureType(Enum):
    """处理器架构类型 / Processor Architecture Types"""
    X86_64 = "x86_64"
    X86_32 = "x86"
    ARM64 = "arm64"
    ARM32 = "arm"
    RISCV64 = "riscv64"
    RISCV32 = "riscv32"
    POWER64 = "power64"
    SPARC64 = "sparc64"
    MIPS64 = "mips64"
    UNKNOWN = "unknown"


class InstructionSet(Enum):
    """指令集分类 / Instruction Set Classifications"""
    CISC = "cisC"
    RISC = "risc"
    EPIC = "epic"
    VLIW = "vliw"
    VECTOR = "vector"


class HardwareVendor(Enum):
    """硬件厂商 / Hardware Vendors"""
    INTEL = "Intel"
    AMD = "AMD"
    ARM = "ARM"
    APPLE = "Apple"
    NVIDIA = "NVIDIA"
    GOOGLE = "Google"
    UNKNOWN = "Unknown"


class ComputeUnit(Enum):
    """计算单元类型 / Compute Unit Types"""
    CPU = "cpu"
    GPU = "gpu"
    TPU = "tpu"
    FPGA = "fpga"
    ASIC = "asic"
    DSP = "dsp"


class PrecisionLevel(Enum):
    """数值精度级别 / Numeric Precision Levels"""
    FP64 = "fp64"  # 双精度浮点
    FP32 = "fp32"  # 单精度浮点
    FP16 = "fp16"  # 半精度浮点
    BF16 = "bf16"  # Brain Float16
    TF32 = "tf32"  # Tensor Float32
    INT8 = "int8"  # 8位整数
    INT4 = "int4"  # 4位整数
    INT1 = "int1"  # 二进制


class OperatingSystem(Enum):
    """操作系统类型 / Operating System Types"""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    ANDROID = "android"
    IOS = "ios"
    FREEBSD = "freebsd"


@dataclass
class HardwareCapabilities:
    """硬件能力 / Hardware Capabilities"""
    architecture: ArchitectureType
    instruction_set: InstructionSet
    vendor: HardwareVendor
    cores: int
    threads: int
    clock_speed_hz: float
    memory_bytes: int
    cache_sizes: Dict[str, int]
    vector_width: int  # SIMD 宽度
    tensor_cores: bool
    fp16_support: bool
    bf16_support: bool
    avx512_support: bool
    neon_support: bool
    sve_support: bool
    
    @property
    def compute_capability(self) -> float:
        """计算能力指数 / Compute capability index"""
        base = self.cores * (self.clock_speed_hz / 1e9)
        vector_bonus = self.vector_width / 32
        tensor_bonus = 2.0 if self.tensor_cores else 1.0
        return base * vector_bonus * tensor_bonus


@dataclass
class HardwareMetrics:
    """硬件指标 / Hardware Metrics"""
    cpu_usage_percent: float
    memory_usage_percent: float
    temperature_celsius: Optional[float]
    power_watts: Optional[float]
    gpu_memory_used_mb: Optional[float]
    gpu_memory_total_mb: Optional[float]


class HardwareDetector:
    """硬件检测器 / Hardware Detector"""
    
    _capabilities: Optional[HardwareCapabilities] = None
    
    @classmethod
    def detect(cls) -> HardwareCapabilities:
        """检测当前硬件 / Detect current hardware"""
        if cls._capabilities:
            return cls._capabilities
        
        info = cpuinfo.get_cpu_info()
        arch = cls._detect_architecture()
        isa = cls._detect_instruction_set(arch, info)
        vendor = cls._detect_vendor(info)
        
        capabilities = HardwareCapabilities(
            architecture=arch,
            instruction_set=isa,
            vendor=vendor,
            cores=psutil.cpu_count(logical=False) or 4,
            threads=psutil.cpu_count(logical=True) or 8,
            clock_speed_hz=(psutil.cpu_freq().current * 1e6) if psutil.cpu_freq() else 0.0,
            memory_bytes=psutil.virtual_memory().total,
            cache_sizes={
                "L1": info.get("l1_data_cache_size", 32) * 1024,
                "L2": info.get("l2_cache_size", 256) * 1024,
                "L3": info.get("l3_cache_size", 8192) * 1024,
            },
            vector_width=cls._detect_vector_width(info),
            tensor_cores=False,
            fp16_support=cls._has_fp16_support(info),
            bf16_support=cls._has_bf16_support(info),
            avx512_support="avx512" in info.get("flags", ""),
            neon_support="asimd" in info.get("flags", ""),
            sve_support="sve" in info.get("flags", ""),
        )
        
        cls._capabilities = capabilities
        return capabilities
    
    @classmethod
    def _detect_architecture(cls) -> ArchitectureType:
        """检测架构 / Detect architecture"""
        machine = platform.machine().lower()
        if machine in ["x86_64", "amd64"]:
            return ArchitectureType.X86_64
        elif machine == "x86":
            return ArchitectureType.X86_32
        elif machine in ["arm64", "aarch64"]:
            return ArchitectureType.ARM64
        elif machine.startswith("arm"):
            return ArchitectureType.ARM32
        elif machine in ["riscv64", "riscv"]:
            return ArchitectureType.RISCV64
        elif machine == "powerpc64":
            return ArchitectureType.POWER64
        else:
            return ArchitectureType.UNKNOWN
    
    @classmethod
    def _detect_instruction_set(
        cls,
        arch: ArchitectureType,
        info: Dict
    ) -> InstructionSet:
        """检测指令集 / Detect instruction set"""
        flags = info.get("flags", [])
        
        if arch in [ArchitectureType.X86_64, ArchitectureType.X86_32]:
            return InstructionSet.CISC
        elif arch in [ArchitectureType.ARM64, ArchitectureType.ARM32]:
            if "sve" in flags:
                return InstructionSet.EPIC
            return InstructionSet.RISC
        elif arch in [ArchitectureType.RISCV64, ArchitectureType.RISCV32]:
            if "v" in flags:
                return InstructionSet.VLIW
            return InstructionSet.RISC
        elif arch == ArchitectureType.POWER64:
            return InstructionSet.CISC
        else:
            return InstructionSet.CISC
    
    @classmethod
    def _detect_vendor(cls, info: Dict) -> HardwareVendor:
        """检测厂商 / Detect vendor"""
        brand = info.get("brand", "").lower()
        if "intel" in brand:
            return HardwareVendor.INTEL
        elif "amd" in brand:
            return HardwareVendor.AMD
        elif "apple" in brand:
            return HardwareVendor.APPLE
        elif "nvidia" in brand:
            return HardwareVendor.NVIDIA
        elif "google" in brand:
            return HardwareVendor.GOOGLE
        return HardwareVendor.UNKNOWN
    
    @classmethod
    def _detect_vector_width(cls, info: Dict) -> int:
        """检测向量宽度 / Detect vector width"""
        if "avx512" in info.get("flags", ""):
            return 512
        elif "avx2" in info.get("flags", ""):
            return 256
        elif "avx" in info.get("flags", ""):
            return 128
        elif "neon" in info.get("flags", ""):
            return 128
        return 64
    
    @classmethod
    def _has_fp16_support(cls, info: Dict) -> bool:
        """检测FP16支持 / Detect FP16 support"""
        return "f16c" in info.get("flags", "")
    
    @classmethod
    def _has_bf16_support(cls, info: Dict) -> bool:
        """检测BF16支持 / Detect BF16 support"""
        return "avx512_bf16" in info.get("flags", "")


class HardwareManager:
    """
    硬件管理器 / Hardware Manager
    
    Manages hardware resources and provides optimized operations.
    管理硬件资源并提供优化操作。
    
    Attributes:
        capabilities: 硬件能力 / Hardware capabilities
        metrics: 当前指标 / Current metrics
    """
    
    def __init__(self):
        self.capabilities = HardwareDetector.detect()
        self.metrics: Optional[HardwareMetrics] = None
        self._compute_units: Dict[str, Any] = {}
    
    def get_capabilities(self) -> HardwareCapabilities:
        """获取硬件能力 / Get hardware capabilities"""
        return self.capabilities
    
    def get_current_metrics(self) -> HardwareMetrics:
        """获取当前指标 / Get current metrics"""
        return HardwareMetrics(
            cpu_usage_percent=psutil.cpu_percent(),
            memory_usage_percent=psutil.virtual_memory().percent,
            temperature_celsius=self._get_temperature(),
            power_watts=None,
            gpu_memory_used_mb=None,
            gpu_memory_total_mb=None,
        )
    
    def _get_temperature(self) -> Optional[float]:
        """获取温度 / Get temperature"""
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if entries:
                            return entries[0].current
        except (AttributeError, OSError, IndexError) as e:
            # 溫度傳感器探測失敗，使用默認值
            logger.debug(f"溫度探測失敗（可忽略）: {e}")
            pass
        return None
    
    def detect_compute_unit(self) -> List[str]:
        """检测可用的计算单元 / Detect available compute units"""
        units = ["cpu"]
        
        self._detect_gpu()
        self._detect_tpu()
        
        return list(self._compute_units.keys())
    
    def _detect_gpu(self):
        """检测GPU / Detect GPU"""
        try:
            import torch
            if torch.cuda.is_available():
                self._compute_units["gpu"] = {
                    "device_count": torch.cuda.device_count(),
                    "device_name": torch.cuda.get_device_name(0),
                    "memory": torch.cuda.get_device_properties(0).total_memory,
                }
        except (ImportError, NameError):
            pass
    
    def _detect_tpu(self):
        """检测TPU / Detect TPU"""
        try:
            import torch_xla
            self._compute_units["tpu"] = {
                "devices": torch_xla._XLAC._xla_num_devices(),
            }
        except (ImportError, AttributeError):
            pass
    
    def get_optimal_precision(self) -> PrecisionLevel:
        """获取最优精度 / Get optimal precision"""
        if self.capabilities.fp16_support and self.capabilities.tensor_cores:
            return PrecisionLevel.FP16
        elif self.capabilities.bf16_support:
            return PrecisionLevel.BF16
        elif self.capabilities.fp16_support:
            return PrecisionLevel.FP16
        else:
            return PrecisionLevel.FP32
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息 / Get system info"""
        caps = self.capabilities
        return {
            "architecture": caps.architecture.value if hasattr(caps.architecture, 'value') else str(caps.architecture),
            "instruction_set": caps.instruction_set.value if hasattr(caps.instruction_set, 'value') else str(caps.instruction_set),
            "vendor": caps.vendor.value if hasattr(caps.vendor, 'value') else str(caps.vendor),
            "cores": caps.cores,
            "threads": caps.threads,
            "clock_ghz": caps.clock_speed_hz / 1e9,
            "memory_gb": caps.memory_bytes / (1024**3),
            "compute_capability": caps.compute_capability,
        }


class HardwareFactory:
    """硬件工厂 / Hardware Factory"""
    
    _instance: Optional[HardwareManager] = None
    
    @classmethod
    def get_manager(cls) -> HardwareManager:
        """获取硬件管理器 / Get hardware manager"""
        if cls._instance is None:
            cls._instance = HardwareManager()
        return cls._instance


def detect_hardware() -> HardwareCapabilities:
    """便捷函数：检测硬件"""
    return HardwareDetector.detect()


def create_hardware_manager() -> HardwareManager:
    """便捷函数：创建硬件管理器"""
    return HardwareFactory.get_manager()


def demo():
    """演示 / Demo"""
    logger.info("🔧 硬件抽象层 (HAL) 演示")
    logger.info("=" * 50)
    
    hw = HardwareManager()
    caps = hw.get_capabilities()
    
    logger.info(f"\n📋 硬件信息:")
    logger.info(f"  架构: {caps.architecture.value}")
    logger.info(f"  指令集: {caps.instruction_set.value}")
    logger.info(f"  厂商: {caps.vendor.value}")
    logger.info(f"  核心数: {caps.cores}")
    logger.info(f"  线程数: {caps.threads}")
    logger.info(f"  主频: {caps.clock_speed_hz / 1e9:.2f} GHz")
    logger.info(f"  内存: {caps.memory_bytes / (1024**3):.1f} GB")
    logger.info(f"  向量宽度: {caps.vector_width} bit")
    
    logger.info(f"\n🔢 特性支持:")
    logger.info(f"  FP16: {caps.fp16_support}")
    logger.info(f"  BF16: {caps.bf16_support}")
    logger.info(f"  AVX512: {caps.avx512_support}")
    logger.info(f"  NEON: {caps.neon_support}")
    logger.info(f"  SVE: {caps.sve_support}")
    
    logger.info(f"\n⚡ 计算能力: {caps.compute_capability:.1f}")
    logger.info(f"  最优精度: {hw.get_optimal_precision().value}")
    
    logger.info(f"\n🖥️ 可用计算单元:")
    units = hw.detect_compute_unit()
    for unit in units:
        logger.info(f"  ✅ {unit.value}")
    
    logger.info(f"\n📊 当前指标:")
    metrics = hw.get_current_metrics()
    logger.info(f"  CPU使用率: {metrics.cpu_usage_percent:.1f}%")
    logger.info(f"  内存使用率: {metrics.memory_usage_percent:.1f}%")
    
    logger.info("\n✅ 演示完成!")


if __name__ == "__main__":
    demo()
