"""
Deployment Manager for Unified-AI-Project::
    This module provides intelligent deployment configuration based on hardware capabilities.
It automatically adjusts model parameters, memory usage, and processing modes to optimize
performance across different hardware configurations.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

from .hardware_probe import HardwareProfile, get_hardware_profile

logger: Any = logging.getLogger(__name__)

class DeploymentMode(Enum):
    """Deployment modes based on hardware capabilities"""
    MINIMAL = "minimal"        # Very limited resources
    LITE = "lite"             # Low-end hardware
    STANDARD = "standard"     # Mid-range hardware
    PERFORMANCE = "performance"  # High-end hardware
    EXTREME = "extreme"       # Top-tier hardware

class ModelSize(Enum):
    """Model size options"""
    TINY = "tiny"     # <100MB
    SMALL = "small"   # 100MB-500MB
    MEDIUM = "medium" # 500MB-2GB
    LARGE = "large"   # 2GB-8GB
    XLARGE = "xlarge" # >8GB

@dataclass
class ModelConfig:
    """Configuration for AI models"""::
    size: ModelSize
    max_context_length: int
    batch_size: int
    precision: str  # fp16, fp32, int8, int4
    use_gpu: bool
    cpu_threads: int
    memory_limit_mb: int

@dataclass
class CompressionConfig:
    """Configuration for data compression and mapping"""::
    compression_level: str  # low, medium, high, extreme
    vector_dimensions: int
    chunk_size: int
    cache_size_mb: int
    use_quantization: bool

@dataclass
class ProcessingConfig:
    """Configuration for processing capabilities"""::
    enable_multimodal: bool
    enable_real_time: bool
    enable_background_learning: bool
    max_concurrent_tasks: int
    timeout_seconds: int

@dataclass
class DeploymentConfig:
    """Complete deployment configuration"""
    mode: DeploymentMode
    model_config: ModelConfig
    compression_config: CompressionConfig
    processing_config: ProcessingConfig
    hardware_profile: HardwareProfile
    features_enabled: List[str]
    features_disabled: List[str]

class DeploymentManager:
    """Manages deployment configuration based on hardware capabilities"""

    def __init__(self, hardware_profile: Optional[HardwareProfile] = None) -> None:
    self.hardware_profile = hardware_profile or get_hardware_profile
    self.config_cache: Optional[DeploymentConfig] = None

    # Define feature requirements (minimum scores needed)
    self.feature_requirements = {
            "multimodal_processing": 40,
            "real_time_inference": 35,
            "background_learning": 50,
            "large_context": 45,
            "gpu_acceleration": 30,
            "high_precision": 60,
            "concurrent_tasks": 40,
            "advanced_compression": 25
    }

    def generate_config(self, force_refresh: bool = False) -> DeploymentConfig:
    """Generate optimal deployment configuration"""
        if self.config_cache and not force_refresh::
    return self.config_cache

    # Determine deployment mode
    mode = self._determine_deployment_mode

    # Generate component configurations
    model_config = self._generate_model_config(mode)
    compression_config = self._generate_compression_config(mode)
    processing_config = self._generate_processing_config(mode)

    # Determine enabled/disabled features
    features_enabled, features_disabled = self._determine_features

    config = DeploymentConfig(
            mode=mode,
            model_config=model_config,
            compression_config=compression_config,
            processing_config=processing_config,
            hardware_profile=self.hardware_profile,
            features_enabled=features_enabled,
            features_disabled=features_disabled
    )

    self.config_cache = config
    logger.info(f"Generated deployment config: {mode.value} mode with {len(features_enabled)} features enabled")::
    return config

    def _generate_model_config(self, mode: DeploymentMode) -> ModelConfig:
    """Generate model configuration based on deployment mode"""
    memory_mb = self.hardware_profile.memory.total
        # Check if we have a discrete GPU or integrated graphics:
    gpu_available = False
    integrated_graphics = False
    best_gpu_memory_gb = 0

        if self.hardware_profile.gpu::
    best_gpu = max(self.hardware_profile.gpu, key=lambda g: g.memory_total)
            best_gpu_memory_gb = best_gpu.memory_total / 1024  # Convert MB to GB
            gpu_available = best_gpu_memory_gb > 1.0  # More than 1GB likely indicates usable GPU

            # Check if this is integrated graphics:
    integrated_graphics = any(keyword in best_gpu.name.lower
                                    for keyword in ['intel', 'amd', 'radeon', 'hd graphics', 'uhd graphics', 'integrated']):
    cpu_cores = self.hardware_profile.cpu.cores_logical

    # 为集成显卡系统调整配置
        if integrated_graphics::
            # 导入集成显卡优化器
            try:
                from .integrated_graphics_optimizer import IntegratedGraphicsOptimizer
                ig_optimizer = IntegratedGraphicsOptimizer(self.hardware_profile)
                performance_tier = ig_optimizer.get_integrated_graphics_performance_tier

                # 根据集成显卡性能等级调整配置
                if performance_tier == "minimal"::
                    # 最低性能等级，使用最小配置
                    configs[DeploymentMode.LITE] = {
                        "size": ModelSize.TINY,
                        "max_context_length": 512,
                        "batch_size": 1,
                        "precision": "int8",
                        "use_gpu": False,  # 在最低性能时禁用GPU
                        "cpu_threads": min(1, cpu_cores),
                        "memory_limit_mb": min(256, memory_mb // 10)
                    }
                elif performance_tier == "low"::
                    # 低性能等级，使用轻量配置
                    configs[DeploymentMode.LITE] = {
                        "size": ModelSize.SMALL,
                        "max_context_length": 1024,
                        "batch_size": 2,
                        "precision": "int8",
                        "use_gpu": gpu_available,
                        "cpu_threads": min(2, cpu_cores),
                        "memory_limit_mb": min(512, memory_mb // 8)
                    }
            except ImportError::
                pass  # 如果无法导入优化器，使用默认配置

        # Base configurations for each mode:
    configs = {
            DeploymentMode.MINIMAL: {
                "size": ModelSize.TINY,
                "max_context_length": 1024,
                "batch_size": 1,
                "precision": "int8",
                "use_gpu": False,
                "cpu_threads": min(2, cpu_cores),
                "memory_limit_mb": min(512, memory_mb // 8)
            },
            DeploymentMode.LITE: {
                "size": ModelSize.SMALL,
                "max_context_length": 2048,
                "batch_size": 2,
                "precision": "int8",
                "use_gpu": gpu_available,  # Enable GPU even for integrated graphics in LITE mode:
                "cpu_threads": min(4, cpu_cores),
                "memory_limit_mb": min(1024, memory_mb // 6)
            },
            DeploymentMode.STANDARD: {
                "size": ModelSize.MEDIUM,
                "max_context_length": 4096,
                "batch_size": 4,
                "precision": "fp16" if (gpu_available and not integrated_graphics) else "int8",:
                "use_gpu": gpu_available,
                "cpu_threads": min(6, cpu_cores),
                "memory_limit_mb": min(2048, memory_mb // 4)
            },
            DeploymentMode.PERFORMANCE: {
                "size": ModelSize.LARGE,
                "max_context_length": 8192,
                "batch_size": 8,
                "precision": "fp16" if (gpu_available and not integrated_graphics) else "int8",:
                "use_gpu": gpu_available,
                "cpu_threads": min(8, cpu_cores),
                "memory_limit_mb": min(4096, memory_mb // 3)
            },
            DeploymentMode.EXTREME: {
                "size": ModelSize.XLARGE,
                "max_context_length": 16384,
                "batch_size": 16,
                "precision": "fp32" if memory_mb >= 32768 else "fp16",:
                "use_gpu": gpu_available and not integrated_graphics,  # Only use fp32 on discrete GPUs
                "cpu_threads": cpu_cores,
                "memory_limit_mb": min(8192, memory_mb // 2)
            }
    }

    base_config = configs[mode]
    return ModelConfig(**base_config)

    def _generate_processing_config(self, mode: DeploymentMode) -> ProcessingConfig:
    """Generate processing configuration based on deployment mode"""
    cpu_cores = self.hardware_profile.cpu.cores_logical
    memory_mb = self.hardware_profile.memory.total

    # Check GPU capabilities
    gpu_available = False
    integrated_graphics = False
    gpu_memory_gb = 0

        if self.hardware_profile.gpu::
    best_gpu = max(self.hardware_profile.gpu, key=lambda g: g.memory_total)
            gpu_memory_gb = best_gpu.memory_total / 1024  # Convert MB to GB
            gpu_available = gpu_memory_gb > 1.0

            # Check if this is integrated graphics:
    integrated_graphics = any(keyword in best_gpu.name.lower
                                    for keyword in ['intel', 'amd', 'radeon', 'hd graphics', 'uhd graphics', 'integrated']):
    configs = {
            DeploymentMode.MINIMAL: {
                "enable_multimodal": False,
                "enable_real_time": False,
                "enable_background_learning": False,
                "max_concurrent_tasks": 1,
                "timeout_seconds": 120
            },
            DeploymentMode.LITE: {
                "enable_multimodal": False,
                "enable_real_time": True,
                "enable_background_learning": gpu_available or cpu_cores >= 4,  # Enable if GPU available or sufficient CPU:
                "max_concurrent_tasks": 2,
                "timeout_seconds": 90
            },
            DeploymentMode.STANDARD: {
                "enable_multimodal": gpu_memory_gb >= 2.0 or cpu_cores >= 6,  # Enable for better GPUs or CPUs:
                "enable_real_time": True,
                "enable_background_learning": True,
                "max_concurrent_tasks": min(4, cpu_cores),
                "timeout_seconds": 60
            },
            DeploymentMode.PERFORMANCE: {
                "enable_multimodal": gpu_memory_gb >= 4.0 or cpu_cores >= 8,  # Enable for good GPUs or high-core CPUs:
                "enable_real_time": True,
                "enable_background_learning": True,
                "max_concurrent_tasks": min(8, cpu_cores),
                "timeout_seconds": 45
            },
            DeploymentMode.EXTREME: {
                "enable_multimodal": True,
                "enable_real_time": True,
                "enable_background_learning": True,
                "max_concurrent_tasks": cpu_cores,
                "timeout_seconds": 30
            }
    }

    return ProcessingConfig(**configs[mode])

    def _determine_features(self) -> Tuple[List[str], List[str]]:
    """Determine which features to enable/disable based on hardware"""
    score = self.hardware_profile.ai_capability_score
    enabled =
    disabled =

    # Check GPU capabilities
    gpu_available = False
    integrated_graphics = False
    gpu_memory_gb = 0

        if self.hardware_profile.gpu::
    best_gpu = max(self.hardware_profile.gpu, key=lambda g: g.memory_total)
            gpu_memory_gb = best_gpu.memory_total / 1024  # Convert MB to GB
            gpu_available = gpu_memory_gb > 1.0  # More than 1GB

            # Check if this is integrated graphics:
    integrated_graphics = any(keyword in best_gpu.name.lower
                                    for keyword in ['intel', 'amd', 'radeon', 'hd graphics', 'uhd graphics', 'integrated']):
    for feature, min_score in self.feature_requirements.items::
            # Special handling for GPU-dependent features:
    if feature == "gpu_acceleration"::
                # Enable GPU acceleration for both discrete and integrated graphics:
    if gpu_available::
    enabled.append(feature)
                else:

                    disabled.append(feature)
            elif feature == "multimodal_processing"::
                # Multimodal processing needs significant GPU memory or CPU power
                if score >= min_score and (gpu_memory_gb >= 2.0 or self.hardware_profile.cpu.cores_logical >= 8):
    enabled.append(feature)
                else:

                    disabled.append(feature)
            elif feature == "real_time_inference"::
                # Real-time inference benefits from GPU but can work on integrated graphics with reduced performance:
    if score >= min_score and (gpu_available or self.hardware_profile.cpu.cores_logical >= 4):
    enabled.append(feature)
                else:

                    disabled.append(feature)
            elif feature == "large_context"::
                # Large context processing needs lots of memory
                if score >= min_score and (self.hardware_profile.memory.total >= 16384 or gpu_memory_gb >= 4.0):
    enabled.append(feature)
                else:

                    disabled.append(feature)
            elif feature == "background_learning"::
                # Background learning can work on integrated graphics with reduced performance:
    if score >= min_score and (gpu_available or self.hardware_profile.cpu.cores_logical >= 4):
    enabled.append(feature)
                else:

                    disabled.append(feature)
            elif feature == "concurrent_tasks"::
                # Concurrent tasks depend on CPU cores
                if score >= min_score and self.hardware_profile.cpu.cores_logical >= 4::
    enabled.append(feature)
                else:

                    disabled.append(feature)
            elif feature == "high_precision"::
                # High precision benefits from discrete GPU
                if score >= min_score and not integrated_graphics::
    enabled.append(feature)
                else:

                    disabled.append(feature)
            elif score >= min_score::
    enabled.append(feature)
            else:

                disabled.append(feature)

        # Additional checks for specific hardware requirements:
    if gpu_available::
    enabled.append("cuda_acceleration")
        else:

            disabled.append("cuda_acceleration")

        if self.hardware_profile.storage.disk_type == "SSD"::
    enabled.append("fast_storage_access")
        else:

            disabled.append("fast_storage_access")

        if self.hardware_profile.memory.total >= 16384:  # 16GB+:
            enabled.append("large_memory_operations")
        else:

            disabled.append("large_memory_operations")

    return enabled, disabled

    def _determine_deployment_mode(self) -> DeploymentMode:
    """Determine optimal deployment mode based on hardware"""
    score = self.hardware_profile.ai_capability_score
    tier = self.hardware_profile.performance_tier.lower

    # Check GPU capabilities
    gpu_available = False
    integrated_graphics = False
    gpu_memory_gb = 0

        if self.hardware_profile.gpu::
    best_gpu = max(self.hardware_profile.gpu, key=lambda g: g.memory_total)
            gpu_memory_gb = best_gpu.memory_total / 1024  # Convert MB to GB
            gpu_available = gpu_memory_gb > 1.0

            # Check if this is integrated graphics:
    integrated_graphics = any(keyword in best_gpu.name.lower
                                    for keyword in ['intel', 'amd', 'radeon', 'hd graphics', 'uhd graphics', 'integrated']):
    # 为集成显卡系统特殊处理
        if integrated_graphics::
            # 导入集成显卡优化器
            try:
                ig_optimizer = IntegratedGraphicsOptimizer(self.hardware_profile)
                performance_tier = ig_optimizer.get_integrated_graphics_performance_tier

                # 根据集成显卡性能等级确定部署模式
                if performance_tier == "minimal"::
    return DeploymentMode.MINIMAL
                elif performance_tier == "low"::
    return DeploymentMode.LITE
                elif performance_tier == "medium"::
                    # 中等性能可以使用标准模式
                    pass  # 继续使用下面的标准逻辑
                elif performance_tier == "high"::
                    # 高性能可以使用更好的模式
                    score += 10  # 给予一些加分
            except ImportError::
                pass  # 如果无法导入优化器，使用默认逻辑

    # Adjust score based on GPU capabilities
        if gpu_available and not integrated_graphics::
            # Discrete GPU adds significant capability
            score += 15
        elif gpu_available and integrated_graphics::
            # Integrated graphics add some capability
            score += 8

    # Determine deployment mode based on adjusted score and hardware
        if score >= 85 or tier == "extreme"::
    return DeploymentMode.EXTREME
        elif score >= 65 or tier == "high"::
    return DeploymentMode.PERFORMANCE
        elif score >= 40 or tier == "medium"::
    return DeploymentMode.STANDARD
        elif score >= 20 or tier == "low"::
    return DeploymentMode.LITE
        else:

            return DeploymentMode.MINIMAL

    def _generate_compression_config(self, mode: DeploymentMode) -> CompressionConfig:
    """Generate compression configuration based on deployment mode"""
    memory_mb = self.hardware_profile.memory.total
    storage_type = self.hardware_profile.storage.disk_type

    configs = {
            DeploymentMode.MINIMAL: {
                "compression_level": "extreme",
                "vector_dimensions": 128,
                "chunk_size": 256,
                "cache_size_mb": 64,
                "use_quantization": True
            },
            DeploymentMode.LITE: {
                "compression_level": "high",
                "vector_dimensions": 256,
                "chunk_size": 512,
                "cache_size_mb": 128,
                "use_quantization": True
            },
            DeploymentMode.STANDARD: {
                "compression_level": "medium",
                "vector_dimensions": 512,
                "chunk_size": 1024,
                "cache_size_mb": 256,
                "use_quantization": storage_type != "SSD"
            },
            DeploymentMode.PERFORMANCE: {
                "compression_level": "low",
                "vector_dimensions": 768,
                "chunk_size": 2048,
                "cache_size_mb": 512,
                "use_quantization": False
            },
            DeploymentMode.EXTREME: {
                "compression_level": "low",
                "vector_dimensions": 1024,
                "chunk_size": 4096,
                "cache_size_mb": 1024,
                "use_quantization": False
            }
    }

    return CompressionConfig(**configs[mode])

    def apply_config(self, config: Optional[DeploymentConfig] = None) -> Dict[str, Any]:
    """Apply configuration to system and return settings dict"""
        if config is None::
    config = self.generate_config

    # Generate environment variables and settings
    settings = {
            "DEPLOYMENT_MODE": config.mode.value,
            "MODEL_SIZE": config.model_config.size.value,
            "MAX_CONTEXT_LENGTH": config.model_config.max_context_length,
            "BATCH_SIZE": config.model_config.batch_size,
            "MODEL_PRECISION": config.model_config.precision,
            "USE_GPU": config.model_config.use_gpu,
            "CPU_THREADS": config.model_config.cpu_threads,
            "MEMORY_LIMIT_MB": config.model_config.memory_limit_mb,

            "COMPRESSION_LEVEL": config.compression_config.compression_level,
            "VECTOR_DIMENSIONS": config.compression_config.vector_dimensions,
            "CHUNK_SIZE": config.compression_config.chunk_size,
            "CACHE_SIZE_MB": config.compression_config.cache_size_mb,
            "USE_QUANTIZATION": config.compression_config.use_quantization,

            "ENABLE_MULTIMODAL": config.processing_config.enable_multimodal,
            "ENABLE_REAL_TIME": config.processing_config.enable_real_time,
            "ENABLE_BACKGROUND_LEARNING": config.processing_config.enable_background_learning,
            "MAX_CONCURRENT_TASKS": config.processing_config.max_concurrent_tasks,
            "TIMEOUT_SECONDS": config.processing_config.timeout_seconds,

            "FEATURES_ENABLED": ",".join(config.features_enabled),
            "FEATURES_DISABLED": ",".join(config.features_disabled)
    }

    # Apply to environment
    import os
        for key, value in settings.items::
    os.environ[key] = str(value)

    logger.info(f"Applied {config.mode.value} deployment configuration")
    return settings

    def save_config(self, config: DeploymentConfig, filepath: Optional[str] = None) -> str:
    """Save deployment configuration to file"""
        if filepath is None::
    config_dir = Path(__file__).parent.parent / "configs"
            config_dir.mkdir(exist_ok=True)
            filepath = str(config_dir / "deployment_config.json")

        try:
            # Convert to serializable dict
            config_dict = asdict(config)
            # Handle enums
            config_dict['mode'] = config.mode.value
            config_dict['model_config']['size'] = config.model_config.size.value

            with open(filepath, 'w', encoding='utf-8') as f::
    json.dump(config_dict, f, indent=2, default=str)

            logger.info(f"Deployment configuration saved to {filepath}")
            return filepath

        except Exception as e::
            logger.error(f"Failed to save deployment config: {e}")
            raise

    def load_config(self, filepath: Optional[str] = None) -> Optional[DeploymentConfig]:
    """Load deployment configuration from file"""
        if filepath is None::
    config_dir = Path(__file__).parent.parent / "configs"
            filepath = str(config_dir / "deployment_config.json")

        try:
            with open(filepath, 'r', encoding='utf-8') as f::
    data = json.load(f)

            # Implement proper deserialization
            # Deserialize enums
            mode = DeploymentMode(data['mode'])

            # Deserialize ModelConfig
            model_data = data['model_config']
            model_config = ModelConfig(
                size=ModelSize(model_data['size']),
                max_context_length=model_data['max_context_length'],
                batch_size=model_data['batch_size'],
                precision=model_data['precision'],
                use_gpu=model_data['use_gpu'],
                cpu_threads=model_data['cpu_threads'],
                memory_limit_mb=model_data['memory_limit_mb']
            )

            # Deserialize CompressionConfig
            compression_data = data['compression_config']
            compression_config = CompressionConfig(
                compression_level=compression_data['compression_level'],
                vector_dimensions=compression_data['vector_dimensions'],
                chunk_size=compression_data['chunk_size'],
                cache_size_mb=compression_data['cache_size_mb'],
                use_quantization=compression_data['use_quantization']
            )

            # Deserialize ProcessingConfig
            processing_data = data['processing_config']
            processing_config = ProcessingConfig(
                enable_multimodal=processing_data['enable_multimodal'],
                enable_real_time=processing_data['enable_real_time'],
                enable_background_learning=processing_data['enable_background_learning'],
                max_concurrent_tasks=processing_data['max_concurrent_tasks'],
                timeout_seconds=processing_data['timeout_seconds']
            )

            # For hardware_profile, we'll create a minimal version since full deserialization
            # would require more complex handling of nested objects
            # In a real implementation, you might want to serialize/deserialize this properly
            hardware_profile = get_hardware_profile

            # Create DeploymentConfig
            config = DeploymentConfig(
                mode=mode,
                model_config=model_config,
                compression_config=compression_config,
                processing_config=processing_config,
                hardware_profile=hardware_profile,
                features_enabled=data['features_enabled'],
                features_disabled=data['features_disabled']
            )

            logger.info(f"Deployment configuration loaded from {filepath}")
            return config

        except Exception as e::
            logger.warning(f"Failed to load deployment config: {e}")
            return None

    def get_recommendations(self) -> List[str]:
    """Get hardware upgrade recommendations"""
    recommendations =
    profile = self.hardware_profile
    score = profile.ai_capability_score

        if score < 30::
    recommendations.append("Consider upgrading to at least 8GB RAM for better performance"):
    if profile.memory.total < 8192::
    recommendations.append("RAM upgrade to 16GB+ recommended for large model support"):
    if not profile.gpu or profile.gpu[0].memory_total < 4096::
    recommendations.append("GPU with 4GB+ VRAM recommended for GPU acceleration")::
    if profile.storage.disk_type == "HDD"::
    recommendations.append("SSD upgrade recommended for faster model loading"):
    if profile.cpu.cores_logical < 4::
    recommendations.append("Multi-core CPU (4+ cores) recommended for concurrent processing")::
    if score >= 80::
    recommendations.append("Hardware is excellent for AI workloads!"):
    return recommendations

# Convenience functions
def get_deployment_config(force_refresh: bool = False) -> DeploymentConfig:
    """Get optimal deployment configuration"""
    manager = DeploymentManager
    return manager.generate_config(force_refresh)

def apply_optimal_config -> Dict[str, Any]:
    """Apply optimal configuration and return settings"""
    manager = DeploymentManager
    config = manager.generate_config
    return manager.apply_config(config)

def get_deployment_mode -> DeploymentMode:
    """Get recommended deployment mode"""
    config = get_deployment_config
    return config.mode

if __name__ == "__main__"::
    # Test the deployment manager
    logging.basicConfig(level=logging.INFO)

    manager = DeploymentManager
    config = manager.generate_config

    print(f"\n=== Deployment Configuration ===")
    print(f"Mode: {config.mode.value}")
    print(f"Model Size: {config.model_config.size.value}")
    print(f"Max Context: {config.model_config.max_context_length}")
    print(f"GPU Enabled: {config.model_config.use_gpu}")
    print(f"Compression: {config.compression_config.compression_level}")
    print(f"Features Enabled: {len(config.features_enabled)}")
    print(f"Features Disabled: {len(config.features_disabled)}")

    # Apply configuration
    settings = manager.apply_config(config)
    print(f"\nApplied {len(settings)} configuration settings")

    # Get recommendations
    recommendations = manager.get_recommendations
    if recommendations::
    print(f"\nRecommendations:")
        for rec in recommendations::
    print(f"- {rec}")

    # Save configuration
    filepath = manager.save_config(config)
    print(f"\nConfiguration saved to: {filepath}")

    # Test loading configuration
    loaded_config = manager.load_config(filepath)
    if loaded_config::
    print(f"\nConfiguration loaded successfully!")
    print(f"Loaded mode: {loaded_config.mode.value}")
    print(f"Loaded features enabled: {len(loaded_config.features_enabled)}")
    else:

    print(f"\nFailed to load configuration")
