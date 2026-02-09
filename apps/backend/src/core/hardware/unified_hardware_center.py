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

import os
import sys
import json
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import psutil

logger = logging.getLogger(__name__)


# ============================================================
# 1. 硬件類型定義
# ============================================================

class AcceleratorType(Enum):
    """計算加速器類型"""
    NVIDIA_GPU = "nvidia_gpu"
    AMD_GPU = "amd_gpu"
    INTEL_GPU = "intel_gpu"
    APPLE_METAL = "apple_metal"
    GOOGLE_TPU = "tpu"
    CPU_AVX512 = "cpu_avx512"
    CPU_AVX2 = "cpu_avx2"
    CPU_AVX = "cpu_avx"
    CPU_SSE42 = "cpu_sse42"
    CPU_BASIC = "cpu_basic"
    UNKNOWN = "unknown"


class PrecisionLevel(Enum):
    """精度級別 (FP8 ~ FP128, INT-DEC4)"""
    FP8 = "fp8"
    FP16 = "fp16"
    FP32 = "fp32"
    FP64 = "fp64"
    FP128 = "fp128"
    INT = "int"
    INT8 = "int8"
    INT16 = "int16"
    INT32 = "int32"
    INT64 = "int64"
    DEC4 = "dec4"  # 10,000x 精度


class PerformanceMode(Enum):
    """性能模式"""
    LOW = "low"        # 入門級: 30 FPS, 基礎特效
    MEDIUM = "medium"  # 中階級: 45 FPS, 標準特效
    HIGH = "high"      # 高階級: 60 FPS, 強化特效
    ULTRA = "ultra"    # 極致級: 120+ FPS, 全開特效


# ============================================================
# 2. 數據結構
# ============================================================

@dataclass
class ComputeResource:
    """計算資源"""
    type: AcceleratorType
    name: str
    memory_mb: int
    compute_capability: float = 0.0
    available: bool = True
    load: float = 0.0
    vendor: str = "unknown"
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "name": self.name,
            "memory_mb": self.memory_mb,
            "compute_capability": self.compute_capability,
            "available": self.available,
            "load": self.load,
            "vendor": self.vendor
        }


@dataclass
class CPUInfo:
    """CPU 信息"""
    brand: str = "Unknown"
    cores_physical: int = 0
    cores_logical: int = 0
    usage_percent: float = 0.0
    frequency_mhz: float = 0.0
    flags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "brand": self.brand,
            "cores_physical": self.cores_physical,
            "cores_logical": self.cores_logical,
            "usage_percent": self.usage_percent,
            "frequency_mhz": self.frequency_mhz,
            "flags": self.flags
        }


@dataclass
class GPUInfo:
    """GPU 信息"""
    name: str = "Unknown"
    memory_total_mb: int = 0
    memory_used_mb: int = 0
    load_percent: float = 0.0
    driver_version: str = "unknown"
    compute_cap: float = 0.0
    vendor: str = "unknown"
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "memory_total_mb": self.memory_total_mb,
            "memory_used_mb": self.memory_used_mb,
            "load_percent": self.load_percent,
            "driver_version": self.driver_version,
            "compute_cap": self.compute_cap,
            "vendor": self.vendor
        }


@dataclass
class MemoryInfo:
    """內存信息"""
    total_mb: int = 0
    available_mb: int = 0
    used_mb: int = 0
    percent_used: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "total_mb": self.total_mb,
            "available_mb": self.available_mb,
            "used_mb": self.used_mb,
            "percent_used": self.percent_used
        }


@dataclass
class HardwareProfile:
    """完整硬件配置檔"""
    cpu: CPUInfo
    gpus: List[GPUInfo]
    memory: MemoryInfo
    accelerator: ComputeResource = None
    ai_capability_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "cpu": {
                "brand": self.cpu.brand,
                "cores_physical": self.cpu.cores_physical,
                "cores_logical": self.cpu.cores_logical,
                "usage_percent": self.cpu.usage_percent,
                "frequency_mhz": self.cpu.frequency_mhz,
                "flags": self.cpu.flags
            },
            "gpus": [g.to_dict() for g in self.gpus],
            "memory": self.memory.__dict__,
            "accelerator": self.accelerator.to_dict() if self.accelerator else None,
            "ai_capability_score": self.ai_capability_score
        }


@dataclass
class ModelRequirement:
    """模型需求"""
    model_name: str
    min_memory_mb: int
    recommended_memory_mb: int
    supported_accelerators: List[AcceleratorType]
    min_compute_capability: float = 0.0
    quantization: str = "q4_0"
    precision_preference: PrecisionLevel = PrecisionLevel.FP16


# ============================================================
# 3. 硬件檢測模組
# ============================================================

class HardwareDetector:
    """統一硬件檢測器"""
    
    @staticmethod
    def detect_cpu() -> CPUInfo:
        """檢測 CPU"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
            
            flags = []
            for line in cpuinfo.split('\n'):
                if line.startswith('flags'):
                    flags = line.split(':')[1].strip().split()
                    break
            
            cpu_info = CPUInfo(
                brand=cpuinfo.split('\n')[0].split(':')[1].strip() if ':' in cpuinfo else "Unknown",
                cores_physical=psutil.cpu_count(logical=False) or 4,
                cores_logical=psutil.cpu_count(logical=True) or 4,
                usage_percent=psutil.cpu_percent(),
                frequency_mhz=psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                flags=flags
            )
            return cpu_info
        except Exception as e:
            logger.error(f"CPU detection failed: {e}")
            return CPUInfo()
    
    @staticmethod
    def detect_gpu() -> List[GPUInfo]:
        """檢測 GPU"""
        gpus = []
        
        # NVIDIA
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu,driver_version', 
                 '--format=csv,noheader'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 5:
                        gpus.append(GPUInfo(
                            name=parts[0],
                            memory_total_mb=int(parts[1].split()[0]) * 1024 if ' ' in parts[1] else int(parts[1]) * 1024,
                            memory_used_mb=int(parts[2].split()[0]) * 1024 if ' ' in parts[2] else int(parts[2]) * 1024,
                            load_percent=float(parts[3]),
                            driver_version=parts[4],
                            vendor="NVIDIA"
                        ))
        except Exception:
            pass
        
        # Intel (via lspci)
        if not gpus:
            try:
                result = subprocess.run(['lspci', '-vnn'], capture_output=True, text=True, timeout=10)
                if 'Intel' in result.stdout and 'UHD' in result.stdout:
                    gpus.append(GPUInfo(
                        name="Intel UHD Graphics",
                        memory_total_mb=2048,
                        vendor="Intel"
                    ))
            except Exception:
                pass
        
        # AMD (via sysfs)
        if not gpus:
            try:
                if os.path.exists('/sys/class/drm/'):
                    for d in os.listdir('/sys/class/drm/'):
                        if 'card' in d:
                            gpus.append(GPUInfo(
                                name="AMD GPU",
                                memory_total_mb=4096,
                                vendor="AMD"
                            ))
                            break
            except Exception:
                pass
        
        return gpus
    
    @staticmethod
    def detect_memory() -> MemoryInfo:
        """檢測內存"""
        try:
            mem = psutil.virtual_memory()
            return MemoryInfo(
                total_mb=int(mem.total / 1024 / 1024),
                available_mb=int(mem.available / 1024 / 1024),
                used_mb=int(mem.used / 1024 / 1024),
                percent_used=mem.percent
            )
        except Exception:
            return MemoryInfo()
    
    @staticmethod
    def get_compute_resource(gpu: GPUInfo = None, cpu_info: CPUInfo = None) -> ComputeResource:
        """獲取計算資源"""
        if gpu:
            # 檢測 GPU 加速器類型
            if gpu.vendor == "NVIDIA":
                acc_type = AcceleratorType.NVIDIA_GPU
            elif gpu.vendor == "AMD":
                acc_type = AcceleratorType.AMD_GPU
            elif gpu.vendor == "Intel":
                acc_type = AcceleratorType.INTEL_GPU
            else:
                acc_type = AcceleratorType.UNKNOWN
            
            return ComputeResource(
                type=acc_type,
                name=gpu.name,
                memory_mb=gpu.memory_total_mb,
                compute_capability=gpu.compute_cap or 7.0,
                vendor=gpu.vendor
            )
        
        # CPU fallback
        if cpu_info:
            flags = cpu_info.flags
            if 'avx512' in flags:
                acc_type = AcceleratorType.CPU_AVX512
            elif 'avx2' in flags:
                acc_type = AcceleratorType.CPU_AVX2
            elif 'avx' in flags:
                acc_type = AcceleratorType.CPU_AVX
            elif 'sse4_2' in flags:
                acc_type = AcceleratorType.CPU_SSE42
            else:
                acc_type = AcceleratorType.CPU_BASIC
            
            return ComputeResource(
                type=acc_type,
                name=f"CPU: {cpu_info.brand}",
                memory_mb=cpu_info.cores_logical * 1024,
                compute_capability=1.0 if acc_type == AcceleratorType.CPU_AVX512 else 0.7
            )
        
        return ComputeResource(type=AcceleratorType.UNKNOWN, name="Unknown", memory_mb=1024)
    
    @staticmethod
    def detect_all() -> HardwareProfile:
        """檢測所有硬件"""
        cpu = HardwareDetector.detect_cpu()
        gpus = HardwareDetector.detect_gpu()
        memory = HardwareDetector.detect_memory()
        
        # 計算 AI 能力分數
        score = 0.0
        score += cpu.cores_logical * 2
        if gpus:
            score += sum(g.memory_total_mb for g in gpus) / 1024 * 10
        score += memory.total_mb / 1024 * 0.5
        
        return HardwareProfile(
            cpu=cpu,
            gpus=gpus,
            memory=memory,
            accelerator=HardwareDetector.get_compute_resource(gpus[0] if gpus else None, cpu),
            ai_capability_score=score
        )


# ============================================================
# 4. 精度管理模組
# ============================================================

class PrecisionManager:
    """精度管理器 - INT-DEC4 動態精度管理"""
    
    PRECISION_FACTORS = {
        PrecisionLevel.FP8: 0.1,
        PrecisionLevel.FP16: 1.0,
        PrecisionLevel.FP32: 1.0,
        PrecisionLevel.FP64: 1.0,
        PrecisionLevel.FP128: 1.0,
        PrecisionLevel.INT: 1,
        PrecisionLevel.INT8: 1,
        PrecisionLevel.INT16: 10,
        PrecisionLevel.INT32: 100,
        PrecisionLevel.INT64: 1000,
        PrecisionLevel.DEC4: 10000  # 10,000x 精度
    }
    
    @staticmethod
    def get_precision_factor(level: PrecisionLevel) -> float:
        """獲取精度因子"""
        return PrecisionManager.PRECISION_FACTORS.get(level, 1.0)
    
    @staticmethod
    def convert_value(value: Any, from_level: PrecisionLevel, to_level: PrecisionLevel) -> Any:
        """轉換精度"""
        factor = PrecisionManager.get_precision_factor(from_level) / PrecisionManager.get_precision_factor(to_level)
        return value * factor
    
    @staticmethod
    def int_to_dec4(value: int) -> float:
        """INT 轉 DEC4"""
        return value / 10000.0
    
    @staticmethod
    def dec4_to_int(value: float) -> int:
        """DEC4 轉 INT"""
        return int(value * 10000)
    
    @staticmethod
    def quantize(value: float, precision: PrecisionLevel) -> float:
        """量化到指定精度"""
        if precision == PrecisionLevel.DEC4:
            return round(value, 4)
        elif precision == PrecisionLevel.INT:
            return int(round(value))
        else:
            return value


# ============================================================
# 5. 代碼轉譯模組
# ============================================================

class CodeTranspiler:
    """代碼轉譯器 - 跨平台代碼轉換"""
    
    SUPPORTED_PLATFORMS = ['linux', 'windows', 'macos']
    SUPPORTED_BACKENDS = ['cpu', 'cuda', 'metal', 'opencl']
    
    @staticmethod
    def transpile_code(code: str, source_platform: str, target_platform: str) -> str:
        """轉譯代碼"""
        transpiled = code
        
        # CUDA 到 OpenCL
        if source_platform == 'cuda' and target_platform == 'opencl':
            transpiled = transpiled.replace('cuda', 'opencl')
            transpiled = transpiled.replace('__global__', '__kernel')
            transpiled = transpiled.replace('threadIdx', 'get_local_id')
        
        # Metal 到 OpenCL
        elif source_platform == 'metal' and target_platform == 'opencl':
            transpiled = transpiled.replace('metal', 'opencl')
            transpiled = transpiled.replace('threadgroup', '__kernel')
        
        return transpiled
    
    @staticmethod
    def optimize_for_cpu(code: str) -> str:
        """優化代碼以適配 CPU"""
        optimized = code
        # 移除 GPU 特定語法
        optimized = optimized.replace('__device__', '')
        optimized = optimized.replace('__global__', '')
        return optimized
    
    @staticmethod
    def get_supported_backends() -> List[str]:
        """獲取支持的後端"""
        return CodeTranspiler.SUPPORTED_BACKENDS


# ============================================================
# 6. 模型倉庫
# ============================================================

class ModelRepository:
    """模型倉庫 - 管理模型需求"""
    
    MODELS = {
        'qwen:0.5b': ModelRequirement(
            model_name='qwen:0.5b',
            min_memory_mb=512,
            recommended_memory_mb=1024,
            supported_accelerators=[
                AcceleratorType.CPU_AVX512, AcceleratorType.CPU_AVX2,
                AcceleratorType.CPU_AVX, AcceleratorType.CPU_SSE42,
                AcceleratorType.NVIDIA_GPU, AcceleratorType.AMD_GPU,
                AcceleratorType.INTEL_GPU  # Intel GPU support
            ],
            quantization='q4_0'
        ),
        'qwen:1.5b': ModelRequirement(
            model_name='qwen:1.5b',
            min_memory_mb=1024,
            recommended_memory_mb=2048,
            supported_accelerators=[
                AcceleratorType.CPU_AVX512, AcceleratorType.CPU_AVX2,
                AcceleratorType.NVIDIA_GPU, AcceleratorType.AMD_GPU,
                AcceleratorType.INTEL_GPU
            ],
            quantization='q4_0'
        ),
        'llama3.2:1b': ModelRequirement(
            model_name='llama3.2:1b',
            min_memory_mb=1024,
            recommended_memory_mb=2048,
            supported_accelerators=[
                AcceleratorType.CPU_AVX512, AcceleratorType.CPU_AVX2,
                AcceleratorType.NVIDIA_GPU, AcceleratorType.AMD_GPU,
                AcceleratorType.INTEL_GPU
            ],
            quantization='q4_0'
        ),
        'phi:latest': ModelRequirement(
            model_name='phi:latest',
            min_memory_mb=2048,
            recommended_memory_mb=4096,
            supported_accelerators=[
                AcceleratorType.CPU_AVX512, AcceleratorType.CPU_AVX2,
                AcceleratorType.NVIDIA_GPU, AcceleratorType.AMD_GPU,
                AcceleratorType.INTEL_GPU
            ],
            quantization='q4_0'
        ),
        'mistral:latest': ModelRequirement(
            model_name='mistral:latest',
            min_memory_mb=4096,
            recommended_memory_mb=8192,
            supported_accelerators=[
                AcceleratorType.CPU_AVX512, AcceleratorType.NVIDIA_GPU,
                AcceleratorType.AMD_GPU, AcceleratorType.INTEL_GPU
            ],
            quantization='q4_0'
        ),
        'codellama:latest': ModelRequirement(
            model_name='codellama:latest',
            min_memory_mb=4096,
            recommended_memory_mb=8192,
            supported_accelerators=[
                AcceleratorType.CPU_AVX512, AcceleratorType.NVIDIA_GPU,
                AcceleratorType.AMD_GPU, AcceleratorType.INTEL_GPU
            ],
            quantization='q4_0'
        )
    }
    
    @classmethod
    def get_requirement(cls, model_name: str) -> Optional[ModelRequirement]:
        """獲取模型需求"""
        if model_name in cls.MODELS:
            return cls.MODELS[model_name]
        # 前綴匹配
        for name, req in cls.MODELS.items():
            if model_name.startswith(name):
                return req
        return None
    
    @classmethod
    def get_all_models(cls) -> List[str]:
        """獲取所有模型"""
        return list(cls.MODELS.keys())


# ============================================================
# 7. 統一硬件資源總控中心
# ============================================================

class UnifiedHardwareCenter:
    """
    統一硬件資源總控中心 (Unified Hardware Resource Center)
    
    整合所有硬件相關功能:
    - 硬件檢測與配置
    - 資源調度與管理
    - 精度轉換
    - 代碼轉譯
    - 模型部署
    - 系統監控
    """
    
    _instance: 'UnifiedHardwareCenter' = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.hardware_profile: HardwareProfile = None
        self.loaded_models: Dict[str, str] = {}
        self.ollama_url = "http://localhost:11434"
        self._running = False
        
        # 配置
        self.config = {
            'max_memory_percent': 0.80,
            'min_free_memory_mb': 512,
            'enable_gpu_priority': True,
            'fallback_to_cpu': True,
            'default_precision': PrecisionLevel.FP16
        }
    
    async def initialize(self) -> bool:
        """初始化總控中心"""
        logger.info("Initializing Unified Hardware Resource Center...")
        self.hardware_profile = HardwareDetector.detect_all()
        
        # 打印硬件信息
        cpu = self.hardware_profile.cpu
        logger.info(f"CPU: {cpu.brand} ({cpu.cores_physical} cores, {cpu.cores_logical} threads)")
        
        for gpu in self.hardware_profile.gpus:
            logger.info(f"GPU: {gpu.name} ({gpu.memory_total_mb} MB, {gpu.vendor})")
        
        mem = self.hardware_profile.memory
        logger.info(f"Memory: {mem.total_mb} MB total, {mem.available_mb} MB available")
        
        logger.info(f"AI Capability Score: {self.hardware_profile.ai_capability_score:.1f}")
        
        return True
    
    # ==================== 硬件接口 ====================
    
    def get_hardware_profile(self) -> HardwareProfile:
        """獲取硬件配置"""
        return self.hardware_profile
    
    def get_cpu_info(self) -> CPUInfo:
        """獲取 CPU 信息"""
        return self.hardware_profile.cpu
    
    def get_gpu_info(self) -> List[GPUInfo]:
        """獲取 GPU 信息"""
        return self.hardware_profile.gpus
    
    def get_memory_info(self) -> MemoryInfo:
        """獲取內存信息"""
        return self.hardware_profile.memory
    
    def get_accelerator(self) -> Optional[ComputeResource]:
        """獲取主要加速器"""
        return self.hardware_profile.accelerator
    
    # ==================== 資源調度 ====================
    
    async def get_best_resource(self, model_name: str) -> Optional[ComputeResource]:
        """獲取最佳資源"""
        req = ModelRepository.get_requirement(model_name)
        if not req:
            # 默認使用 CPU
            return self.hardware_profile.accelerator
        
        # 遍歷可用資源
        best_resource = None
        best_score = -1
        
        resources = [self.hardware_profile.accelerator]
        if self.hardware_profile.gpus:
            for gpu in self.hardware_profile.gpus:
                resources.append(HardwareDetector.get_compute_resource(gpu))
        
        for resource in resources:
            if not resource.available:
                continue
            
            if resource.type not in req.supported_accelerators:
                continue
            
            if resource.compute_capability < req.min_compute_capability:
                continue
            
            if resource.memory_mb < req.min_memory_mb:
                continue
            
            # 計算分數
            score = resource.memory_mb / req.min_memory_mb
            if self.config['enable_gpu_priority']:
                if resource.type in [AcceleratorType.NVIDIA_GPU, AcceleratorType.AMD_GPU]:
                    score *= 1.5
            
            if score > best_score:
                best_score = score
                best_resource = resource
        
        return best_resource
    
    async def load_model(self, model_name: str) -> bool:
        """加載模型"""
        resource = await self.get_best_resource(model_name)
        if not resource:
            logger.error(f"No resource for {model_name}")
            return False
        
        if model_name in self.loaded_models:
            return True
        
        # 檢查內存
        mem = self.hardware_profile.memory
        req = ModelRepository.get_requirement(model_name)
        if req and mem.available_mb < req.min_memory_mb:
            logger.error(f"Not enough memory for {model_name}")
            return False
        
        # Ollama 加載
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                # 檢查模型是否存在
                response = await client.get(f"{self.ollama_url}/api/tags", timeout=10)
                models = [m['name'] for m in response.json().get('models', [])]
                
                if model_name not in models:
                    logger.info(f"Pulling {model_name}...")
                    resp = await client.post(
                        f"{self.ollama_url}/api/pull",
                        json={"name": model_name, "stream": False},
                        timeout=300
                    )
                    if resp.status_code != 200:
                        return False
                
                self.loaded_models[model_name] = resource.type.value
                logger.info(f"✓ {model_name} loaded on {resource.name}")
                return True
        except Exception as e:
            logger.error(f"Model load failed: {e}")
            return False
    
    async def generate(self, prompt: str, model: str = None, **kwargs) -> Dict[str, Any]:
        """生成響應"""
        if model is None:
            # 自動選擇
            if self.loaded_models:
                model = list(self.loaded_models.keys())[0]
            else:
                model = 'qwen:0.5b'
        
        if model not in self.loaded_models:
            if not await self.load_model(model):
                return {"success": False, "error": "Failed to load model"}
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_predict": kwargs.get('max_tokens', 512),
                            "temperature": kwargs.get('temperature', 0.7)
                        }
                    },
                    timeout=120
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "model": model,
                        "resource": self.loaded_models.get(model),
                        "response": data.get('response', ''),
                        "stats": {
                            "duration_ms": data.get('total_duration', 0) / 1000000
                        }
                    }
                return {"success": False, "error": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== 精度管理 ====================
    
    def get_precision_factor(self, level: PrecisionLevel) -> float:
        """獲取精度因子"""
        return PrecisionManager.get_precision_factor(level)
    
    def convert_precision(self, value: Any, from_level: PrecisionLevel, to_level: PrecisionLevel) -> Any:
        """轉換精度"""
        return PrecisionManager.convert_value(value, from_level, to_level)
    
    def quantize(self, value: float, precision: PrecisionLevel) -> float:
        """量化"""
        return PrecisionManager.quantize(value, precision)
    
    # ==================== 代碼轉譯 ====================
    
    def transpile(self, code: str, source: str, target: str) -> str:
        """轉譯代碼"""
        return CodeTranspiler.transpile_code(code, source, target)
    
    def optimize_for_cpu(self, code: str) -> str:
        """優化 CPU 代碼"""
        return CodeTranspiler.optimize_for_cpu(code)
    
    # ==================== 系統監控 ====================
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """獲取系統指標"""
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        
        metrics = {
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "memory_available_mb": int(mem.available / 1024 / 1024),
            "loaded_models": list(self.loaded_models.keys()),
            "timestamp": datetime.now().isoformat()
        }
        
        # 添加 GPU 指標
        if self.hardware_profile.gpus:
            metrics["gpu"] = [{
                "name": g.name,
                "load_percent": g.load_percent,
                "memory_used_mb": g.memory_used_mb
            } for g in self.hardware_profile.gpus]
        
        return metrics
    
    # ==================== 狀態 ====================
    
    def get_status(self) -> Dict[str, Any]:
        """獲取狀態"""
        return {
            "hardware": self.hardware_profile.to_dict() if self.hardware_profile else None,
            "loaded_models": self.loaded_models,
            "config": self.config,
            "metrics": self.get_system_metrics()
        }
    
    async def cleanup(self):
        """清理"""
        self._running = False
        logger.info("Unified Hardware Resource Center cleanup complete")


# ============================================================
# 8. 單例接口
# ============================================================

_uhrc: UnifiedHardwareCenter = None


async def get_hardware_center() -> UnifiedHardwareCenter:
    """獲取硬件中心單例"""
    global _uhrc
    if _uhrc is None:
        _uhrc = UnifiedHardwareCenter()
        await _uhrc.initialize()
    return _uhrc


# ============================================================
# 9. 便捷函數
# ============================================================

def create_hardware_center() -> UnifiedHardwareCenter:
    """創建硬件中心"""
    return UnifiedHardwareCenter()


# ============================================================
# 導出
# ============================================================

__all__ = [
    # 類
    'UnifiedHardwareCenter',
    'HardwareDetector',
    'PrecisionManager',
    'CodeTranspiler',
    'ModelRepository',
    # 枚舉
    'AcceleratorType',
    'PrecisionLevel',
    'PerformanceMode',
    # 數據類
    'ComputeResource',
    'CPUInfo',
    'GPUInfo',
    'MemoryInfo',
    'HardwareProfile',
    'ModelRequirement',
    # 函數
    'get_hardware_center',
    'create_hardware_center'
]
