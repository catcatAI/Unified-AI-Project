"""
Dynamic Resource Scheduler for Angela AI Matrix

Automatically detects and manages computing resources (CPU, GPU, TPU, etc.)
and dynamically allocates them for model inference.

Now uses the unified UnifiedHardwareCenter from core.hardware.
"""

import os
import sys
import json
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

# 使用統一的硬件資源總控中心
try:
    from core.hardware import (
        UnifiedHardwareCenter,
        AcceleratorType,
        PrecisionLevel,
        ComputeResource,
        ModelRequirement,
        get_hardware_center
    )
    UNIFIED_HARDWARE_AVAILABLE = True
except ImportError:
    UNIFIED_HARDWARE_AVAILABLE = False
    logger.warning("Unified hardware center not available, using standalone mode")


class AcceleratorType(Enum):
    """Types of computing accelerators."""
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


@dataclass
class ComputeResource:
    """Represents a computing resource."""
    type: AcceleratorType
    name: str
    memory_mb: int
    compute_capability: float = 0.0
    available: bool = True
    load: float = 0.0  # 0.0 to 1.0
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "name": self.name,
            "memory_mb": self.memory_mb,
            "compute_capability": self.compute_capability,
            "available": self.available,
            "load": self.load
        }


@dataclass
class ModelRequirement:
    """Requirements for a model to run on a resource."""
    model_name: str
    min_memory_mb: int
    recommended_memory_mb: int
    supported_accelerators: List[AcceleratorType]
    min_compute_capability: float = 0.0
    quantization: str = "q4_0"  # Default quantization
    
    def to_dict(self) -> Dict:
        return {
            "model_name": self.model_name,
            "min_memory_mb": self.min_memory_mb,
            "recommended_memory_mb": self.recommended_memory_mb,
            "supported_accelerators": [a.value for a in self.supported_accelerators],
            "min_compute_capability": self.min_compute_capability,
            "quantization": self.quantization
        }


class HardwareDetector:
    """Detects available computing hardware."""
    
    @staticmethod
    def detect_cpu() -> ComputeResource:
        """Detect CPU - uses unified hardware center if available."""
        if UNIFIED_HARDWARE_AVAILABLE:
            try:
                center = get_hardware_center()
                if center.hardware_profile and center.hardware_profile.accelerator:
                    acc = center.hardware_profile.accelerator
                    return ComputeResource(
                        type=acc.type,
                        name=acc.name,
                        memory_mb=acc.memory_mb,
                        compute_capability=acc.compute_capability
                    )
            except Exception:
                pass
        
        # Fallback to local detection
        """Detect CPU capabilities."""
        try:
            # Get CPU info
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
            
            # Check for flags
            flags = ""
            if 'flags' in cpuinfo:
                for line in cpuinfo.split('\n'):
                    if line.startswith('flags'):
                        flags = line.split(':')[1].strip()
                        break
            
            # Detect highest instruction set
            has_avx512 = 'avx512' in flags
            has_avx2 = 'avx2' in flags
            has_avx = 'avx' in flags
            has_sse42 = 'sse4_2' in flags
            
            # Get memory info
            mem_info = HardwareDetector.get_memory_info()
            
            if has_avx512:
                cpu_type = AcceleratorType.CPU_AVX512
                name = "CPU with AVX-512"
            elif has_avx2:
                cpu_type = AcceleratorType.CPU_AVX2
                name = "CPU with AVX2"
            elif has_avx:
                cpu_type = AcceleratorType.CPU_AVX
                name = "CPU with AVX"
            elif has_sse42:
                cpu_type = AcceleratorType.CPU_SSE42
                name = "CPU with SSE4.2"
            else:
                cpu_type = AcceleratorType.CPU_BASIC
                name = "CPU (basic)"
            
            return ComputeResource(
                type=cpu_type,
                name=name,
                memory_mb=mem_info['total_mb'],
                compute_capability=1.0 if has_avx512 else 0.7 if has_avx2 else 0.5 if has_avx else 0.3
            )
        except Exception as e:
            logger.error(f"CPU detection failed: {e}")
            return ComputeResource(
                type=AcceleratorType.CPU_BASIC,
                name="CPU (unknown)",
                memory_mb=1024,
                compute_capability=0.3
            )
    
    @staticmethod
    def detect_nvidia_gpu() -> Optional[ComputeResource]:
        """Detect NVIDIA GPU using nvidia-smi."""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total,compute_cap', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines and lines[0]:
                    parts = [p.strip() for p in lines[0].split(',')]
                    if len(parts) >= 3:
                        return ComputeResource(
                            type=AcceleratorType.NVIDIA_GPU,
                            name=f"NVIDIA {parts[0]}",
                            memory_mb=int(parts[1]) * 1024,  # Convert GB to MB
                            compute_capability=float(parts[2]) if parts[2] else 7.0
                        )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        except Exception as e:
            logger.warning(f"NVIDIA GPU detection error: {e}")
        
        return None
    
    @staticmethod
    def detect_amd_gpu() -> Optional[ComputeResource]:
        """Detect AMD GPU using rocm-smi or sysfs."""
        try:
            # Try rocm-smi first
            result = subprocess.run(
                ['rocm-smi', '--showproductname', '--showmeminfo', 'v'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse output
                if 'Card' in result.stdout or 'GPU' in result.stdout:
                    return ComputeResource(
                        type=AcceleratorType.AMD_GPU,
                        name="AMD GPU (ROCm)",
                        memory_mb=8192,  # Default assumption
                        compute_capability=9.0
                    )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try sysfs
        try:
            for path in Path('/sys/class/drm/').iterdir():
                if 'card' in str(path) and '-' in str(path):
                    # Found AMD GPU
                    return ComputeResource(
                        type=AcceleratorType.AMD_GPU,
                        name="AMD GPU (sysfs)",
                        memory_mb=4096,
                        compute_capability=9.0
                    )
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def detect_intel_gpu() -> Optional[ComputeResource]:
        """Detect Intel GPU."""
        try:
            # Check for Intel GPU via lspci
            result = subprocess.run(
                ['lspci', '-vnn'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if 'Intel' in result.stdout and ('Graphics' in result.stdout or 'UHD' in result.stdout):
                # Intel integrated or discrete GPU
                return ComputeResource(
                    type=AcceleratorType.INTEL_GPU,
                    name="Intel GPU",
                    memory_mb=2048,  # Shared memory
                    compute_capability=7.5
                )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return None
    
    @staticmethod
    def detect_tpu() -> Optional[ComputeResource]:
        """Detect Google TPU."""
        # TPU detection typically requires libtpu.so or environment variables
        if os.environ.get('TPU_NAME') or os.path.exists('/dev/libtpu'):
            return ComputeResource(
                type=AcceleratorType.GOOGLE_TPU,
                name="Google TPU",
                memory_mb=16384,  # HBM memory
                compute_capability=10.0
            )
        return None
    
    @staticmethod
    def get_memory_info() -> Dict[str, int]:
        """Get system memory information."""
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            total = 0
            available = 0
            
            for line in meminfo.split('\n'):
                if line.startswith('MemTotal:'):
                    total = int(line.split()[1]) // 1024  # KB to MB
                elif line.startswith('MemAvailable:'):
                    available = int(line.split()[1]) // 1024
            
            return {
                'total_mb': total,
                'available_mb': available,
                'used_mb': total - available
            }
        except Exception:
            return {'total_mb': 1024, 'available_mb': 512, 'used_mb': 512}
    
    @staticmethod
    def detect_all() -> List[ComputeResource]:
        """Detect all available computing resources - uses unified hardware center."""
        # Use unified hardware center if available
        if UNIFIED_HARDWARE_AVAILABLE:
            try:
                center = get_hardware_center()
                if center.hardware_profile:
                    resources = []
                    
                    # Add accelerator (CPU or GPU)
                    if center.hardware_profile.accelerator:
                        acc = center.hardware_profile.accelerator
                        resources.append(ComputeResource(
                            type=acc.type,
                            name=acc.name,
                            memory_mb=acc.memory_mb,
                            compute_capability=acc.compute_capability
                        ))
                    
                    # Add GPUs from profile
                    for gpu in center.hardware_profile.gpus:
                        resources.append(ComputeResource(
                            type=AcceleratorType.NVIDIA_GPU if 'NVIDIA' in gpu.name else 
                                 AcceleratorType.AMD_GPU if 'AMD' in gpu.name else
                                 AcceleratorType.INTEL_GPU,
                            name=gpu.name,
                            memory_mb=gpu.memory_total_mb,
                            compute_capability=gpu.compute_cap or 7.0
                        ))
                    
                    return resources
            except Exception as e:
                logger.warning(f"Unified hardware center detection failed: {e}")
        
        # Fallback to local detection
        resources = []
        
        # Always include CPU
        cpu = HardwareDetector.detect_cpu()
        resources.append(cpu)
        logger.info(f"CPU detected: {cpu.name} ({cpu.memory_mb} MB)")
        
        # Try to detect GPUs
        nvidia = HardwareDetector.detect_nvidia_gpu()
        if nvidia:
            resources.append(nvidia)
            logger.info(f"NVIDIA GPU detected: {nvidia.name}")
        
        amd = HardwareDetector.detect_amd_gpu()
        if amd:
            resources.append(amd)
            logger.info(f"AMD GPU detected: {amd.name}")
        
        intel = HardwareDetector.detect_intel_gpu()
        if intel:
            resources.append(intel)
            logger.info(f"Intel GPU detected: {intel.name}")
        
        tpu = HardwareDetector.detect_tpu()
        if tpu:
            resources.append(tpu)
            logger.info(f"TPU detected: {tpu.name}")
        
        return resources


class ModelRepository:
    """Repository of available models and their requirements - uses unified ModelRepository."""
    
    @staticmethod
    def get_requirement(model_name: str) -> Optional[ModelRequirement]:
        """Get requirements for a model - uses unified ModelRepository."""
        # Try unified repository first
        if UNIFIED_HARDWARE_AVAILABLE:
            try:
                from core.hardware import ModelRepository as UnifiedRepo
                return UnifiedRepo.get_requirement(model_name)
            except Exception:
                pass
        
        # Fallback to local requirements
        local_requirements = {
            'qwen:0.5b': ModelRequirement(
                model_name='qwen:0.5b',
                min_memory_mb=512,
                recommended_memory_mb=1024,
                supported_accelerators=[
                    AcceleratorType.CPU_AVX512, AcceleratorType.CPU_AVX2,
                    AcceleratorType.CPU_AVX, AcceleratorType.CPU_SSE42,
                    AcceleratorType.NVIDIA_GPU, AcceleratorType.AMD_GPU
                ],
                min_compute_capability=0.0,
                quantization='q4_0'
            ),
            'qwen:1.5b': ModelRequirement(
                model_name='qwen:1.5b',
                min_memory_mb=1024,
                recommended_memory_mb=2048,
                supported_accelerators=[
                    AcceleratorType.CPU_AVX512, AcceleratorType.CPU_AVX2,
                    AcceleratorType.NVIDIA_GPU, AcceleratorType.AMD_GPU
                ],
                min_compute_capability=0.3,
                quantization='q4_0'
            ),
            'llama3.2:1b': ModelRequirement(
                model_name='llama3.2:1b',
                min_memory_mb=1024,
                recommended_memory_mb=2048,
                supported_accelerators=[
                    AcceleratorType.CPU_AVX512, AcceleratorType.CPU_AVX2,
                    AcceleratorType.NVIDIA_GPU, AcceleratorType.AMD_GPU
                ],
                min_compute_capability=0.3,
                quantization='q4_0'
            ),
            'phi:latest': ModelRequirement(
                model_name='phi:latest',
                min_memory_mb=2048,
                recommended_memory_mb=4096,
                supported_accelerators=[
                    AcceleratorType.CPU_AVX512, AcceleratorType.CPU_AVX2,
                    AcceleratorType.NVIDIA_GPU, AcceleratorType.AMD_GPU
                ],
                min_compute_capability=0.5,
                quantization='q4_0'
            ),
            'mistral:latest': ModelRequirement(
                model_name='mistral:latest',
                min_memory_mb=4096,
                recommended_memory_mb=8192,
                supported_accelerators=[
                    AcceleratorType.CPU_AVX512, AcceleratorType.NVIDIA_GPU,
                    AcceleratorType.AMD_GPU
                ],
                min_compute_capability=0.7,
                quantization='q4_0'
            ),
            'codellama:latest': ModelRequirement(
                model_name='codellama:latest',
                min_memory_mb=4096,
                recommended_memory_mb=8192,
                supported_accelerators=[
                    AcceleratorType.CPU_AVX512, AcceleratorType.NVIDIA_GPU,
                    AcceleratorType.AMD_GPU
                ],
                min_compute_capability=0.7,
                quantization='q4_0'
            )
        }
        
        if model_name in local_requirements:
            return local_requirements[model_name]
        
        return None
    
    @staticmethod
    def get_best_model_for_resource(resource: ComputeResource, available_models: List[str]) -> Optional[str]:
        """Get the best model that can run on the given resource."""
        best = None
        best_score = -1
        
        for model_name in available_models:
            req = ModelRepository.get_requirement(model_name)
            if not req:
                continue
            
            # Check compatibility
            if resource.type not in req.supported_accelerators:
                continue
            
            if resource.compute_capability < req.min_compute_capability:
                continue
            
            if resource.memory_mb < req.min_memory_mb:
                continue
            
            # Calculate score (prefer larger models with lower resource usage)
            score = resource.memory_mb / req.min_memory_mb
            if resource.type in [AcceleratorType.NVIDIA_GPU, AcceleratorType.GOOGLE_TPU]:
                score *= 1.5  # Prefer GPU/TPU for heavy models
            
            if score > best_score:
                best_score = score
                best = model_name
        
        return best
    
    @staticmethod
    def get_all_available_models() -> List[str]:
        """Get all known model names."""
        return list(ModelRepository.MODEL_REQUIREMENTS.keys())


class DynamicScheduler:
    """
    Dynamic resource scheduler for Angela AI Matrix.
    
    Automatically allocates computing resources based on:
    - Available hardware
    - Model requirements
    - System load
    - Memory availability
    """
    
    def __init__(self):
        self.resources: List[ComputeResource] = []
        self.loaded_models: Dict[str, str] = {}  # model_name -> resource_type
        self.model_queue: asyncio.Queue = asyncio.Queue()
        self.ollama_base_url = "http://localhost:11434"
        self._running = False
        
        # Load configuration
        self.config = {
            'max_memory_percent': 0.80,  # Use up to 80% of available memory
            'min_free_memory_mb': 512,    # Keep at least 512MB free
            'check_interval': 5.0,       # Check every 5 seconds
            'enable_gpu_priority': True,   # Prefer GPU for large models
            'fallback_to_cpu': True       # Fallback to CPU if GPU unavailable
        }
    
    async def initialize(self) -> bool:
        """Initialize the scheduler and detect hardware."""
        logger.info("Initializing Dynamic Resource Scheduler...")
        
        # Detect hardware
        self.resources = HardwareDetector.detect_all()
        
        logger.info(f"Detected {len(self.resources)} computing resources")
        for r in self.resources:
            logger.info(f"  - {r.name}: {r.type.value} ({r.memory_mb} MB)")
        
        return True
    
    async def get_best_resource(self, model_name: str) -> Optional[ComputeResource]:
        """Find the best resource for running a model."""
        req = ModelRepository.get_requirement(model_name)
        if not req:
            logger.warning(f"Unknown model requirements: {model_name}")
            # Return CPU as fallback
            for r in self.resources:
                if r.type in [AcceleratorType.CPU_AVX512, AcceleratorType.CPU_AVX2, 
                              AcceleratorType.CPU_AVX, AcceleratorType.CPU_SSE42]:
                    return r
            return self.resources[0]  # Any CPU
        
        # Score each resource
        best_resource = None
        best_score = -1
        
        for resource in self.resources:
            if not resource.available:
                continue
            
            # Check compatibility
            if resource.type not in req.supported_accelerators:
                continue
            
            if resource.compute_capability < req.min_compute_capability:
                continue
            
            if resource.memory_mb < req.min_memory_mb:
                continue
            
            # Calculate score
            score = 0.0
            memory_score = resource.memory_mb / req.recommended_memory_mb
            compute_score = resource.compute_capability / max(req.min_compute_capability, 0.1)
            
            if self.config['enable_gpu_priority']:
                if resource.type in [AcceleratorType.NVIDIA_GPU, AcceleratorType.AMD_GPU]:
                    score = memory_score * compute_score * 2.0  # GPU bonus
                elif resource.type == AcceleratorType.GOOGLE_TPU:
                    score = memory_score * compute_score * 3.0  # TPU bonus
                else:
                    score = memory_score * compute_score
            else:
                score = memory_score * compute_score
            
            # Prefer less loaded resources
            score *= (1.0 - resource.load * 0.5)
            
            if score > best_score:
                best_score = score
                best_resource = resource
        
        return best_resource
    
    async def load_model(self, model_name: str) -> bool:
        """Load a model on the best available resource."""
        resource = await self.get_best_resource(model_name)
        
        if not resource:
            logger.error(f"No suitable resource found for {model_name}")
            return False
        
        logger.info(f"Loading {model_name} on {resource.name}...")
        
        # Check if already loaded
        if model_name in self.loaded_models:
            logger.info(f"Model {model_name} already loaded")
            return True
        
        # Check memory
        mem_info = HardwareDetector.get_memory_info()
        req = ModelRepository.get_requirement(model_name)
        
        if req:
            if mem_info['available_mb'] < req.min_memory_mb:
                logger.error(f"Not enough memory for {model_name}")
                return False
        
        # Load via Ollama
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                # Pull model if not exists
                response = await client.get(
                    f"{self.ollama_base_url}/api/tags",
                    timeout=30
                )
                models = [m['name'] for m in response.json().get('models', [])]
                
                if model_name not in models:
                    logger.info(f"Pulling {model_name}...")
                    async with client.stream(
                        'POST',
                        f"{self.ollama_base_url}/api/pull",
                        json={"name": model_name, "stream": False},
                        timeout=300
                    ) as response:
                        if response.status_code != 200:
                            logger.error(f"Failed to pull {model_name}")
                            return False
                
                self.loaded_models[model_name] = resource.type.value
                logger.info(f"✓ {model_name} loaded on {resource.name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    async def unload_model(self, model_name: str) -> bool:
        """Unload a model to free resources."""
        if model_name in self.loaded_models:
            del self.loaded_models[model_name]
            logger.info(f"✓ {model_name} unloaded")
            return True
        return False
    
    async def generate(self, prompt: str, model: str = None, **kwargs) -> Dict[str, Any]:
        """Generate response using the best available resource."""
        if model is None:
            # Auto-select best model
            available = list(self.loaded_models.keys())
            if not available:
                # Try to load best model for current resources
                for r in self.resources:
                    if r.available:
                        best = ModelRepository.get_best_model_for_resource(r, list(ModelRepository.MODEL_REQUIREMENTS.keys()))
                        if best:
                            model = best
                            await self.load_model(model)
                            break
            
            if not model:
                model = 'qwen:0.5b'  # Fallback to smallest
        
        # Ensure model is loaded
        if model not in self.loaded_models:
            await self.load_model(model)
        
        # Generate
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_predict": kwargs.get('max_tokens', 512),
                            "temperature": kwargs.get('temperature', 0.7),
                        }
                    },
                    timeout=120
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "model": model,
                        "response": data.get('response', ''),
                        "resource": self.loaded_models.get(model, 'unknown'),
                        "stats": {
                            "total_duration": data.get('total_duration', 0),
                            "load_duration": data.get('load_duration', 0),
                            "prompt_eval_count": data.get('prompt_eval_count', 0),
                            "eval_count": data.get('eval_count', 0)
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Generation failed: {response.status_code}"
                    }
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status."""
        return {
            "resources": [r.to_dict() for r in self.resources],
            "loaded_models": self.loaded_models,
            "config": self.config,
            "total_models_loaded": len(self.loaded_models)
        }
    
    async def cleanup(self):
        """Cleanup resources."""
        self._running = False
        logger.info("Dynamic Scheduler cleanup complete")


# Singleton instance
_scheduler: Optional[DynamicScheduler] = None


async def get_scheduler() -> DynamicScheduler:
    """Get or create the dynamic scheduler singleton."""
    global _scheduler
    if _scheduler is None:
        _scheduler = DynamicScheduler()
        await _scheduler.initialize()
    return _scheduler


if __name__ == "__main__":
    # Test the scheduler
    async def test():
        scheduler = await get_scheduler()
        status = scheduler.get_status()
        print(json.dumps(status, indent=2))
        
        # Test generation
        result = await scheduler.generate("Hello! Who are you?")
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())
