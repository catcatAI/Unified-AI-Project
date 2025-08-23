"""
Deployment Manager for Unified-AI-Project

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

logger = logging.getLogger(__name__)

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
    """Configuration for AI models"""
    size: ModelSize
    max_context_length: int
    batch_size: int
    precision: str  # fp16, fp32, int8, int4
    use_gpu: bool
    cpu_threads: int
    memory_limit_mb: int

@dataclass
class CompressionConfig:
    """Configuration for data compression and mapping"""
    compression_level: str  # low, medium, high, extreme
    vector_dimensions: int
    chunk_size: int
    cache_size_mb: int
    use_quantization: bool

@dataclass
class ProcessingConfig:
    """Configuration for processing capabilities"""
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
    
    def __init__(self, hardware_profile: Optional[HardwareProfile] = None):
        self.hardware_profile = hardware_profile or get_hardware_profile()
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
        if self.config_cache and not force_refresh:
            return self.config_cache
        
        # Determine deployment mode
        mode = self._determine_deployment_mode()
        
        # Generate component configurations
        model_config = self._generate_model_config(mode)
        compression_config = self._generate_compression_config(mode)
        processing_config = self._generate_processing_config(mode)
        
        # Determine enabled/disabled features
        features_enabled, features_disabled = self._determine_features()
        
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
        logger.info(f"Generated deployment config: {mode.value} mode with {len(features_enabled)} features enabled")
        
        return config
    
    def _determine_deployment_mode(self) -> DeploymentMode:
        """Determine optimal deployment mode based on hardware"""
        score = self.hardware_profile.ai_capability_score
        tier = self.hardware_profile.performance_tier.lower()
        
        if score >= 80 or tier == "extreme":
            return DeploymentMode.EXTREME
        elif score >= 60 or tier == "high":
            return DeploymentMode.PERFORMANCE
        elif score >= 35 or tier == "medium":
            return DeploymentMode.STANDARD
        elif score >= 15 or tier == "low":
            return DeploymentMode.LITE
        else:
            return DeploymentMode.MINIMAL
    
    def _generate_model_config(self, mode: DeploymentMode) -> ModelConfig:
        """Generate model configuration based on deployment mode"""
        memory_mb = self.hardware_profile.memory.total
        gpu_available = (self.hardware_profile.gpu and 
                        self.hardware_profile.gpu[0].memory_total > 1024)
        cpu_cores = self.hardware_profile.cpu.cores_logical
        
        # Base configurations for each mode
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
                "use_gpu": gpu_available and self.hardware_profile.gpu[0].memory_total >= 2048,
                "cpu_threads": min(4, cpu_cores),
                "memory_limit_mb": min(1024, memory_mb // 6)
            },
            DeploymentMode.STANDARD: {
                "size": ModelSize.MEDIUM,
                "max_context_length": 4096,
                "batch_size": 4,
                "precision": "fp16" if gpu_available else "int8",
                "use_gpu": gpu_available,
                "cpu_threads": min(6, cpu_cores),
                "memory_limit_mb": min(2048, memory_mb // 4)
            },
            DeploymentMode.PERFORMANCE: {
                "size": ModelSize.LARGE,
                "max_context_length": 8192,
                "batch_size": 8,
                "precision": "fp16",
                "use_gpu": gpu_available,
                "cpu_threads": min(8, cpu_cores),
                "memory_limit_mb": min(4096, memory_mb // 3)
            },
            DeploymentMode.EXTREME: {
                "size": ModelSize.XLARGE,
                "max_context_length": 16384,
                "batch_size": 16,
                "precision": "fp32" if memory_mb >= 32768 else "fp16",
                "use_gpu": gpu_available,
                "cpu_threads": cpu_cores,
                "memory_limit_mb": min(8192, memory_mb // 2)
            }
        }
        
        base_config = configs[mode]
        return ModelConfig(**base_config)
    
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
    
    def _generate_processing_config(self, mode: DeploymentMode) -> ProcessingConfig:
        """Generate processing configuration based on deployment mode"""
        cpu_cores = self.hardware_profile.cpu.cores_logical
        memory_mb = self.hardware_profile.memory.total
        
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
                "enable_background_learning": False,
                "max_concurrent_tasks": 2,
                "timeout_seconds": 90
            },
            DeploymentMode.STANDARD: {
                "enable_multimodal": True,
                "enable_real_time": True,
                "enable_background_learning": True,
                "max_concurrent_tasks": min(4, cpu_cores),
                "timeout_seconds": 60
            },
            DeploymentMode.PERFORMANCE: {
                "enable_multimodal": True,
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
        enabled = []
        disabled = []
        
        for feature, min_score in self.feature_requirements.items():
            if score >= min_score:
                enabled.append(feature)
            else:
                disabled.append(feature)
        
        # Additional checks for specific hardware requirements
        if self.hardware_profile.gpu and self.hardware_profile.gpu[0].cuda_version:
            enabled.append("cuda_acceleration")
        else:
            disabled.append("cuda_acceleration")
        
        if self.hardware_profile.storage.disk_type == "SSD":
            enabled.append("fast_storage_access")
        else:
            disabled.append("fast_storage_access")
        
        if self.hardware_profile.memory.total >= 16384:  # 16GB+
            enabled.append("large_memory_operations")
        else:
            disabled.append("large_memory_operations")
        
        return enabled, disabled
    
    def apply_config(self, config: Optional[DeploymentConfig] = None) -> Dict[str, Any]:
        """Apply configuration to system and return settings dict"""
        if config is None:
            config = self.generate_config()
        
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
        for key, value in settings.items():
            os.environ[key] = str(value)
        
        logger.info(f"Applied {config.mode.value} deployment configuration")
        return settings
    
    def save_config(self, config: DeploymentConfig, filepath: Optional[str] = None) -> str:
        """Save deployment configuration to file"""
        if filepath is None:
            config_dir = Path(__file__).parent.parent / "configs"
            config_dir.mkdir(exist_ok=True)
            filepath = str(config_dir / "deployment_config.json")
        
        try:
            # Convert to serializable dict
            config_dict = asdict(config)
            # Handle enums
            config_dict['mode'] = config.mode.value
            config_dict['model_config']['size'] = config.model_config.size.value
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, default=str)
            
            logger.info(f"Deployment configuration saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save deployment config: {e}")
            raise
    
    def load_config(self, filepath: Optional[str] = None) -> Optional[DeploymentConfig]:
        """Load deployment configuration from file"""
        if filepath is None:
            config_dir = Path(__file__).parent.parent / "configs"
            filepath = str(config_dir / "deployment_config.json")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # TODO: Implement proper deserialization
            # This is a simplified version
            logger.info(f"Deployment configuration loaded from {filepath}")
            return None  # Placeholder
            
        except Exception as e:
            logger.warning(f"Failed to load deployment config: {e}")
            return None
    
    def get_recommendations(self) -> List[str]:
        """Get hardware upgrade recommendations"""
        recommendations = []
        profile = self.hardware_profile
        score = profile.ai_capability_score
        
        if score < 30:
            recommendations.append("Consider upgrading to at least 8GB RAM for better performance")
            
        if profile.memory.total < 8192:
            recommendations.append("RAM upgrade to 16GB+ recommended for large model support")
        
        if not profile.gpu or profile.gpu[0].memory_total < 4096:
            recommendations.append("GPU with 4GB+ VRAM recommended for GPU acceleration")
        
        if profile.storage.disk_type == "HDD":
            recommendations.append("SSD upgrade recommended for faster model loading")
        
        if profile.cpu.cores_logical < 4:
            recommendations.append("Multi-core CPU (4+ cores) recommended for concurrent processing")
        
        if score >= 80:
            recommendations.append("Hardware is excellent for AI workloads!")
        
        return recommendations

# Convenience functions
def get_deployment_config(force_refresh: bool = False) -> DeploymentConfig:
    """Get optimal deployment configuration"""
    manager = DeploymentManager()
    return manager.generate_config(force_refresh)

def apply_optimal_config() -> Dict[str, Any]:
    """Apply optimal configuration and return settings"""
    manager = DeploymentManager()
    config = manager.generate_config()
    return manager.apply_config(config)

def get_deployment_mode() -> DeploymentMode:
    """Get recommended deployment mode"""
    config = get_deployment_config()
    return config.mode

if __name__ == "__main__":
    # Test the deployment manager
    logging.basicConfig(level=logging.INFO)
    
    manager = DeploymentManager()
    config = manager.generate_config()
    
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
    recommendations = manager.get_recommendations()
    if recommendations:
        print(f"\nRecommendations:")
        for rec in recommendations:
            print(f"- {rec}")
    
    # Save configuration
    filepath = manager.save_config(config)
    print(f"\nConfiguration saved to: {filepath}")