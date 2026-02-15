"""
硬件檢測與自適應配置系統
支持 NVIDIA, AMD, Intel, Apple Silicon, CPU (AVX/AVX2/AVX512/SSE4)
"""
import subprocess
import os
import json
import logging
import platform
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

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
class HardwareInfo:
    """硬件信息"""
    accelerator_type: AcceleratorType
    accelerator_name: str
    vram_mb: int = 0
    ram_total_gb: float = 0
    ram_available_gb: float = 0
    cpu_cores: int = 0
    cpu_flags: List[str] = None
    is_virtual: bool = False
    
    def __post_init__(self):
        if self.cpu_flags is None:
            self.cpu_flags = []


class HardwareDetector:
    """硬件檢測器"""
    
    def __init__(self):
        self.hardware_info: Optional[HardwareInfo] = None
    
    def detect(self) -> HardwareInfo:
        """執行完整硬件檢測"""
        logger.info("Starting hardware detection...")
        
        # 1. 檢測 GPU
        accelerator_type, accelerator_name, vram = self._detect_gpu()
        
        # 2. 檢測 CPU 加速特性
        if accelerator_type == AcceleratorType.NONE:
            accelerator_type, accelerator_name = self._detect_cpu_acceleration()
        
        # 3. 檢測內存
        ram_total, ram_available = self._detect_memory()
        
        # 4. 檢測 CPU 核心數
        cpu_cores = self._detect_cpu_cores()
        
        # 5. 檢測 CPU flags
        cpu_flags = self._detect_cpu_flags()
        
        # 6. 檢測是否為虛擬環境
        is_virtual = self._detect_virtual()
        
        self.hardware_info = HardwareInfo(
            accelerator_type=accelerator_type,
            accelerator_name=accelerator_name,
            vram_mb=vram,
            ram_total_gb=ram_total,
            ram_available_gb=ram_available,
            cpu_cores=cpu_cores,
            cpu_flags=cpu_flags,
            is_virtual=is_virtual
        )
        
        logger.info(f"Hardware detected: {self.hardware_info}")
        return self.hardware_info
    
    def _detect_gpu(self) -> tuple[AcceleratorType, str, int]:
        """檢測 GPU"""
        vram = 0
        name = "Unknown"
        
        # 1. 嘗試 NVIDIA
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines and lines[0]:
                    parts = lines[0].split(',')
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        vram = int(parts[1].strip())
                        logger.info(f"NVIDIA GPU detected: {name} with {vram}MB VRAM")
                        return AcceleratorType.NVIDIA, name, vram
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # 2. 嘗試 AMD ROCm
        try:
            result = subprocess.run(
                ['rocm-smi', '--showid', '--showmeminfo', 'v'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and 'GPU' in result.stdout:
                # Parse AMD info
                for line in result.stdout.split('\n'):
                    if 'Device Name' in line or 'ID' in line:
                        name = line.split(':')[-1].strip()
                        break
                logger.info(f"AMD GPU detected: {name}")
                return AcceleratorType.AMD, name, vram
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # 3. 檢查 Intel GPU
        intel_gpu = self._detect_intel_gpu()
        if intel_gpu:
            logger.info(f"Intel GPU detected: {intel_gpu}")
            return AcceleratorType.INTEL, intel_gpu, 0
        
        # 4. 檢查 Apple Metal
        if platform.system() == 'Darwin':
            try:
                result = subprocess.run(
                    ['system_profiler', 'SPDisplaysDataType'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0 and 'Metal' in result.stdout:
                    logger.info("Apple Silicon detected with Metal")
                    return AcceleratorType.APPLE_METAL, "Apple Silicon", 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        # 5. 檢查渲染設備
        if self._check_vulkan():
            # Vulkan 存在但無法識別品牌，可能也是加速器
            logger.info("Vulkan renderer detected but unknown GPU")
        
        return AcceleratorType.NONE, "No GPU", 0
    
    def _detect_intel_gpu(self) -> Optional[str]:
        """檢測 Intel GPU"""
        try:
            # 檢查 lspci
            result = subprocess.run(
                ['lspci'], capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split('\n'):
                if 'VGA' in line and 'Intel' in line:
                    # 提取 Intel GPU 型號
                    parts = line.split(':')[-1].strip()
                    return parts
            
            # 檢查 DRM 設備
            drm_path = '/sys/class/drm'
            if os.path.exists(drm_path):
                for card in os.listdir(drm_path):
                    if 'card' in card:
                        # 檢查 Intel 特定的 sysfs
                        intel_path = f'{drm_path}/{card}/device'
                        if os.path.exists(intel_path):
                            # 讀取設備信息
                            vendor_path = f'{intel_path}/vendor'
                            if os.path.exists(vendor_path):
                                with open(vendor_path) as f:
                                    vendor = f.read().strip()
                                    if vendor == '0x8086':  # Intel vendor ID
                                        return f"Intel UHD Graphics ({card})"
        except Exception as e:
            logger.warning(f"Intel GPU detection error: {e}")
        
        return None
    
    def _check_vulkan(self) -> bool:
        """檢查 Vulkan 支持"""
        try:
            result = subprocess.run(
                ['vulkaninfo', '--summary'],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0 and 'GPU' in result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _detect_cpu_acceleration(self) -> tuple[AcceleratorType, str]:
        """檢測 CPU 加速能力"""
        flags = self._detect_cpu_flags()
        
        if 'avx512f' in flags:
            return AcceleratorType.CPU_AVX512, "CPU with AVX-512"
        elif 'avx2' in flags:
            return AcceleratorType.CPU_AVX2, "CPU with AVX2"
        elif 'avx' in flags:
            return AcceleratorType.CPU_AVX, "CPU with AVX"
        elif 'sse4_2' in flags:
            return AcceleratorType.CPU_SSE42, "CPU with SSE4.2"
        else:
            return AcceleratorType.NONE, "CPU (baseline)"
    
    def _detect_cpu_flags(self) -> List[str]:
        """檢測 CPU Flags"""
        try:
            with open('/proc/cpuinfo') as f:
                for line in f:
                    if 'flags' in line:
                        return line.split(':')[-1].strip().split()
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            pass

        return []
    
    def _detect_memory(self) -> tuple[float, float]:
        """檢測內存"""
        try:
            with open('/proc/meminfo') as f:
                total = 0
                available = 0
                for line in f:
                    if 'MemTotal' in line:
                        total = int(line.split()[1]) / 1024 / 1024  # GB
                    elif 'MemAvailable' in line:
                        available = int(line.split()[1]) / 1024 / 1024  # GB
                return total, available
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            return 0, 0

    
    def _detect_cpu_cores(self) -> int:
        """檢測 CPU 核心數"""
        try:
            return os.cpu_count() or 1
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            return 1

    
    def _detect_virtual(self) -> bool:
        """檢測是否為虛擬環境"""
        indicators = [
            '/proc/vz',  # OpenVZ
            '/proc/bc',  # Balloon
            '.dockerenv',  # Docker
            '/sys/hypervisor',  # Hyper-V
        ]
        for indicator in indicators:
            if os.path.exists(indicator):
                return True
        return False


class HardwareAdapter:
    """硬件自適應適配器"""
    
    def __init__(self, hardware_info: HardwareInfo):
        self.hardware = hardware_info
    
    def get_recommended_settings(self) -> Dict[str, Any]:
        """獲取推薦配置"""
        settings = {
            "accelerator": self.hardware.accelerator_type.value,
            "accelerator_name": self.hardware.accelerator_name,
            "ollama_config": {},
            "model_recommendations": [],
            "performance_notes": []
        }
        
        # 基於加速器類型配置
        if self.hardware.accelerator_type == AcceleratorType.NVIDIA:
            self._configure_nvidia(settings)
        elif self.hardware.accelerator_type == AcceleratorType.AMD:
            self._configure_amd(settings)
        elif self.hardware.accelerator_type == AcceleratorType.INTEL:
            self._configure_intel(settings)
        elif self.hardware.accelerator_type == AcceleratorType.CPU_AVX512:
            self._configure_cpu_avx512(settings)
        elif self.hardware.accelerator_type == AcceleratorType.CPU_AVX2:
            self._configure_cpu_avx2(settings)
        elif self.hardware.accelerator_type == AcceleratorType.CPU_SSE42:
            self._configure_cpu_sse42(settings)
        else:
            self._configure_baseline(settings)
        
        # 添加模型推薦
        self._add_model_recommendations(settings)
        
        return settings
    
    def _configure_nvidia(self, settings: Dict):
        """NVIDIA 配置"""
        settings["ollama_config"] = {
            "CUDA_VISIBLE_DEVICES": "0",
            "OLLAMA_GPU_LAYERS": -1,  # 使用所有 GPU 層
            "OLLAMA_NUM_PARALLEL": min(4, self.hardware.cpu_cores)
        }
        settings["performance_notes"].append(
            f"NVIDIA GPU detected. {self.hardware.vram_mb}MB VRAM available."
        )
    
    def _configure_amd(self, settings: Dict):
        """AMD 配置"""
        settings["ollama_config"] = {
            "HIP_VISIBLE_DEVICES": "0",
            "OLLAMA_GPU_LAYERS": -1,
            "OLLAMA_NUM_PARALLEL": min(4, self.hardware.cpu_cores)
        }
        settings["performance_notes"].append("AMD GPU detected. Using ROCm backend.")
    
    def _configure_intel(self, settings: Dict):
        """Intel 配置 (使用 CPU 模式)"""
        settings["ollama_config"] = {
            "OLLAMA_GPU_LAYERS": 0,  # Intel GPU 不直接支持 LLM
            "OLLAMA_NUM_PARALLEL": 2,
            "USE_VAAPI": True  # 啟用 VA-API 加速
        }
        settings["performance_notes"].append(
            "Intel GPU detected. Using CPU-only mode with SSE4.2. "
            "For better performance, consider using OpenVINO."
        )
    
    def _configure_cpu_avx512(self, settings: Dict):
        """AVX-512 CPU 配置"""
        settings["ollama_config"] = {
            "OLLAMA_GPU_LAYERS": 0,
            "OLLAMA_NUM_PARALLEL": min(8, self.hardware.cpu_cores),
            "OLLAMA_CPU_EXTENSIONS": "avx512"
        }
        settings["performance_notes"].append("AVX-512 CPU. Full optimization enabled.")
    
    def _configure_cpu_avx2(self, settings: Dict):
        """AVX2 CPU 配置"""
        settings["ollama_config"] = {
            "OLLAMA_GPU_LAYERS": 0,
            "OLLAMA_NUM_PARALLEL": min(4, self.hardware.cpu_cores),
            "OLLAMA_CPU_EXTENSIONS": "avx2"
        }
        settings["performance_notes"].append("AVX2 CPU. Standard optimization enabled.")
    
    def _configure_cpu_sse42(self, settings: Dict):
        """SSE4.2 CPU 配置"""
        settings["ollama_config"] = {
            "OLLAMA_GPU_LAYERS": 0,
            "OLLAMA_NUM_PARALLEL": min(2, self.hardware.cpu_cores),
            "OLLAMA_CPU_EXTENSIONS": "sse4.2"
        }
        settings["performance_notes"].append(
            "SSE4.2 CPU only. Limited optimization. Consider upgrading hardware."
        )
    
    def _configure_baseline(self, settings: Dict):
        """基線配置"""
        settings["ollama_config"] = {
            "OLLAMA_GPU_LAYERS": 0,
            "OLLAMA_NUM_PARALLEL": 1
        }
        settings["performance_notes"].append(
            "No hardware acceleration detected. Using minimal configuration."
        )
    
    def _add_model_recommendations(self, settings: Dict):
        """添加模型推薦"""
        ram = self.hardware.ram_available_gb
        accel = self.hardware.accelerator_type
        
        # Very limited RAM (<1GB available) needs smallest model
        if ram < 1:
            settings["model_recommendations"] = [
                {"name": "qwen:0.5b", "size": "0.5B", "quantization": "Q4_0", "notes": "Alibaba Qwen 0.5B - smallest viable model for very limited RAM"}
            ]
        elif ram < 2:
            settings["model_recommendations"] = [
                {"name": "llama3.2:1b", "size": "1B", "quantization": "Q4_0", "notes": "Meta Llama 3.2 1B, recommended for JasperLake with limited RAM"}
            ]
        elif ram < 4:
            if accel in [AcceleratorType.NVIDIA, AcceleratorType.AMD, AcceleratorType.CPU_AVX512]:
                settings["model_recommendations"] = [
                    {"name": "llama3.2:1b", "size": "1B", "quantization": "Q4_0", "notes": "Meta Llama 3.2 1B"},
                    {"name": "qwen2.5:1.5b", "size": "1.5B", "quantization": "Q4_0", "notes": "Alibaba Qwen 2.5 1.5B"},
                    {"name": "gemma:2b", "size": "2B", "quantization": "Q4_0", "notes": "Google Gemma 2B"}
                ]
            else:
                settings["model_recommendations"] = [
                    {"name": "llama3.2:1b", "size": "1B", "quantization": "Q4_0", "notes": "Meta Llama 3.2 1B"},
                    {"name": "tinydolphin", "size": "1.5B", "quantization": "Q4_0", "notes": "Cognitive Computations TinyDolphin"}
                ]
        elif ram < 8:
            settings["model_recommendations"] = [
                {"name": "llama3.2:3b", "size": "3B", "quantization": "Q4_0", "notes": "Meta Llama 3.2 3B"},
                {"name": "qwen2.5:3b", "size": "3B", "quantization": "Q4_0", "notes": "Alibaba Qwen 2.5 3B"},
                {"name": "phi3:3.8b", "size": "3.8B", "quantization": "Q4_0", "notes": "Microsoft Phi-3"}
            ]
        else:
            settings["model_recommendations"] = [
                {"name": "llama3.2:7b", "size": "7B", "quantization": "Q4_0", "notes": "Meta Llama 3.2 7B"},
                {"name": "mistral:7b", "size": "7B", "quantization": "Q4_0", "notes": "Mistral 7B"},
                {"name": "qwen2.5:7b", "size": "7B", "quantization": "Q4_0", "notes": "Alibaba Qwen 2.5 7B"}
            ]
        
        # 添加 GPU 專用推薦
        if accel == AcceleratorType.NVIDIA and self.hardware.vram_mb > 8000:
            settings["model_recommendations"].insert(0, {
                "name": "llama3.1:8b", "size": "8B", "quantization": "FP16", 
                "notes": "Full precision for high-VRAM GPUs"
            })


def detect_hardware() -> HardwareInfo:
    """便捷硬件檢測函數"""
    detector = HardwareDetector()
    return detector.detect()


def get_ollama_settings() -> Dict[str, Any]:
    """獲取 Ollama 配置"""
    hardware = detect_hardware()
    adapter = HardwareAdapter(hardware)
    return adapter.get_recommended_settings()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    logger.info("=" * 70)
    logger.info("硬件檢測與自適應配置")
    logger.info("=" * 70)
    
    hardware = detect_hardware()
    logger.info(f"\n檢測結果:")
    logger.info(f"  加速器類型: {hardware.accelerator_type.value}")
    logger.info(f"  加速器名稱: {hardware.accelerator_name}")
    logger.info(f"  VRAM: {hardware.vram_mb}MB")
    logger.info(f"  RAM: {hardware.ram_total_gb:.1f}GB total, {hardware.ram_available_gb:.1f}GB available")
    logger.info(f"  CPU 核心: {hardware.cpu_cores}")
    logger.info(f"  CPU Flags: {', '.join(hardware.cpu_flags[:10])}...")
    logger.info(f"  虛擬環境: {'是' if hardware.is_virtual else '否'}")
    
    settings = get_ollama_settings()
    logger.info(f"\n推薦配置:")
    logger.info(f"  Ollama 配置: {json.dumps(settings['ollama_config'], indent=2)}")
    logger.info(f"  模型推薦:")
    for model in settings['model_recommendations']:
        logger.info(f"    - {model['name']} ({model['size']}, {model['quantization']})")
        logger.info(f"      {model['notes']}")
    logger.info(f"  性能備註:")
    for note in settings['performance_notes']:
        logger.info(f"    - {note}")
