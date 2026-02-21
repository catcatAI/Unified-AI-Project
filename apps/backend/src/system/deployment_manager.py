import logging
import os
import json
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from shared.utils.hardware_detector import SystemHardwareProbe, HardwareProfile
from .cluster_manager import ClusterManager, NodeType, cluster_manager

logger = logging.getLogger(__name__)

class DeploymentMode(Enum):
    MINIMAL = "minimal"
    LITE = "lite"
    STANDARD = "standard"
    PERFORMANCE = "performance"
    EXTREME = "extreme"
    CLUSTER = "cluster"

class ModelSize(Enum):
    TINY = "tiny"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    XLARGE = "xlarge"

@dataclass
class ModelConfig:
    size: ModelSize
    max_context_length: int
    batch_size: int
    precision: str
    use_gpu: bool
    cpu_threads: int
    memory_limit_mb: int

@dataclass
class CompressionConfig:
    compression_level: str
    vector_dimensions: int
    chunk_size: int
    cache_size_mb: int
    use_quantization: bool

@dataclass
class ProcessingConfig:
    enable_multimodal: bool
    enable_real_time: bool
    enable_background_learning: bool
    max_concurrent_tasks: int
    timeout_seconds: int

@dataclass
class DeploymentConfig:
    mode: DeploymentMode
    model_config: ModelConfig
    compression_config: CompressionConfig
    processing_config: ProcessingConfig
    hardware_profile: HardwareProfile
    features_enabled: List[str]
    features_disabled: List[str]
    cluster_role: Optional[str] = None

class DeploymentManager:
    """Manages system deployment based on hardware capabilities"""
    
    def __init__(self, probe: Optional[SystemHardwareProbe] = None):
        self.probe = probe or SystemHardwareProbe()
        self.hardware_profile = self.probe.get_hardware_profile()
        self.config_cache: Optional[DeploymentConfig] = None
        
        # Feature requirements (min AI capability score)
        self.feature_requirements = {
            "gpu_acceleration": 10,
            "multimodal_processing": 40,
            "real_time_inference": 30,
            "large_context": 50,
            "background_learning": 25,
            "concurrent_tasks": 35,
            "high_precision": 60,
            "cluster_deployment": 70
        }

    def generate_config(self, force_refresh: bool = False, cluster_mode: bool = False) -> DeploymentConfig:
        """Generate optimal deployment configuration"""
        if self.config_cache and not force_refresh:
            return self.config_cache

        # Determine mode
        if cluster_mode:
            mode = DeploymentMode.CLUSTER
        else:
            mode = self._determine_deployment_mode()

        # Get cluster capability if needed
        cluster_info = self.probe.get_cluster_capability()
        cluster_role = cluster_info["preferred_role"] if mode == DeploymentMode.CLUSTER else None

        # Generate component configurations
        model_config = self._generate_model_config(mode)
        compression_config = self._generate_compression_config(mode)
        processing_config = self._generate_processing_config(mode)

        # Determine enabled/disabled features
        features_enabled, features_disabled = self._determine_features()
        
        if mode == DeploymentMode.CLUSTER:
            if "cluster_deployment" not in features_enabled:
                features_enabled.append("cluster_deployment")
            features_enabled.append("distributed_computing")

        config = DeploymentConfig(
            mode=mode,
            model_config=model_config,
            compression_config=compression_config,
            processing_config=processing_config,
            hardware_profile=self.hardware_profile,
            features_enabled=features_enabled,
            features_disabled=features_disabled,
            cluster_role=cluster_role
        )

        self.config_cache = config
        
        # Initialize cluster manager if in cluster mode
        if mode == DeploymentMode.CLUSTER:
            role = NodeType.MASTER if cluster_role == "master" else NodeType.WORKER
            cluster_manager.node_type = role
            logger.info(f"Initialized cluster manager as {role.value}")

        logger.info(f"Generated deployment config: {mode.value} mode with {len(features_enabled)} features enabled")
        return config

    def _generate_model_config(self, mode: DeploymentMode) -> ModelConfig:
        """Generate model configuration based on deployment mode"""
        memory_mb = self.hardware_profile.memory.total
        cpu_cores = self.hardware_profile.cpu.cores_logical
        
        gpu_available = False
        integrated_graphics = False
        best_gpu_memory_gb = 0

        if self.hardware_profile.gpu:
            best_gpu = max(self.hardware_profile.gpu, key=lambda g: g.memory_total)
            best_gpu_memory_gb = best_gpu.memory_total / 1024
            gpu_available = best_gpu_memory_gb > 1.0
            
            integrated_graphics = any(keyword in best_gpu.name.lower() 
                                    for keyword in ['intel', 'amd', 'radeon', 'hd graphics', 'uhd graphics', 'integrated'])

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
                "use_gpu": gpu_available,
                "cpu_threads": min(4, cpu_cores),
                "memory_limit_mb": min(1024, memory_mb // 6)
            },
            DeploymentMode.STANDARD: {
                "size": ModelSize.MEDIUM,
                "max_context_length": 4096,
                "batch_size": 4,
                "precision": "fp16" if (gpu_available and not integrated_graphics) else "int8",
                "use_gpu": gpu_available,
                "cpu_threads": min(6, cpu_cores),
                "memory_limit_mb": min(2048, memory_mb // 4)
            },
            DeploymentMode.PERFORMANCE: {
                "size": ModelSize.LARGE,
                "max_context_length": 8192,
                "batch_size": 8,
                "precision": "fp16" if (gpu_available and not integrated_graphics) else "int8",
                "use_gpu": gpu_available,
                "cpu_threads": min(8, cpu_cores),
                "memory_limit_mb": min(4096, memory_mb // 3)
            },
            DeploymentMode.EXTREME: {
                "size": ModelSize.XLARGE,
                "max_context_length": 16384,
                "batch_size": 16,
                "precision": "fp32" if memory_mb >= 32768 else "fp16",
                "use_gpu": gpu_available and not integrated_graphics,
                "cpu_threads": cpu_cores,
                "memory_limit_mb": min(8192, memory_mb // 2)
            },
            DeploymentMode.CLUSTER: {
                # Cluster mode uses high settings for master, optimized for worker
                "size": ModelSize.LARGE,
                "max_context_length": 8192,
                "batch_size": 8,
                "precision": "fp16",
                "use_gpu": gpu_available,
                "cpu_threads": cpu_cores,
                "memory_limit_mb": min(6144, memory_mb // 2)
            }
        }

        base_config = configs[mode]
        return ModelConfig(**base_config)

    def _generate_processing_config(self, mode: DeploymentMode) -> ProcessingConfig:
        """Generate processing configuration based on deployment mode"""
        cpu_cores = self.hardware_profile.cpu.cores_logical
        
        gpu_available = False
        gpu_memory_gb = 0
        if self.hardware_profile.gpu:
            best_gpu = max(self.hardware_profile.gpu, key=lambda g: g.memory_total)
            gpu_memory_gb = best_gpu.memory_total / 1024
            gpu_available = gpu_memory_gb > 1.0

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
                "enable_background_learning": gpu_available or cpu_cores >= 4,
                "max_concurrent_tasks": 2,
                "timeout_seconds": 90
            },
            DeploymentMode.STANDARD: {
                "enable_multimodal": gpu_memory_gb >= 2.0 or cpu_cores >= 6,
                "enable_real_time": True,
                "enable_background_learning": True,
                "max_concurrent_tasks": min(4, cpu_cores),
                "timeout_seconds": 60
            },
            DeploymentMode.PERFORMANCE: {
                "enable_multimodal": gpu_memory_gb >= 4.0 or cpu_cores >= 8,
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
            },
            DeploymentMode.CLUSTER: {
                "enable_multimodal": True,
                "enable_real_time": True,
                "enable_background_learning": True,
                "max_concurrent_tasks": cpu_cores * 2, # Cluster can handle more via distribution
                "timeout_seconds": 60
            }
        }

        return ProcessingConfig(**configs[mode])

    def _determine_features(self) -> Tuple[List[str], List[str]]:
        """Determine which features to enable/disable based on hardware"""
        score = self.hardware_profile.ai_capability_score
        enabled = []
        disabled = []

        gpu_available = False
        integrated_graphics = False
        gpu_memory_gb = 0
        if self.hardware_profile.gpu:
            best_gpu = max(self.hardware_profile.gpu, key=lambda g: g.memory_total)
            gpu_memory_gb = best_gpu.memory_total / 1024
            gpu_available = gpu_memory_gb > 1.0
            integrated_graphics = any(keyword in best_gpu.name.lower() 
                                    for keyword in ['intel', 'amd', 'radeon', 'hd graphics', 'uhd graphics', 'integrated'])

        for feature, min_score in self.feature_requirements.items():
            if feature == "gpu_acceleration":
                if gpu_available: enabled.append(feature)
                else: disabled.append(feature)
            elif feature == "multimodal_processing":
                if score >= min_score and (gpu_memory_gb >= 2.0 or self.hardware_profile.cpu.cores_logical >= 8):
                    enabled.append(feature)
                else: disabled.append(feature)
            elif feature == "real_time_inference":
                if score >= min_score and (gpu_available or self.hardware_profile.cpu.cores_logical >= 4):
                    enabled.append(feature)
                else: disabled.append(feature)
            elif feature == "large_context":
                if score >= min_score and (self.hardware_profile.memory.total >= 16384 or gpu_memory_gb >= 4.0):
                    enabled.append(feature)
                else: disabled.append(feature)
            elif feature == "background_learning":
                if score >= min_score and (gpu_available or self.hardware_profile.cpu.cores_logical >= 4):
                    enabled.append(feature)
                else: disabled.append(feature)
            elif feature == "concurrent_tasks":
                if score >= min_score and self.hardware_profile.cpu.cores_logical >= 4:
                    enabled.append(feature)
                else: disabled.append(feature)
            elif feature == "high_precision":
                if score >= min_score and not integrated_graphics:
                    enabled.append(feature)
                else: disabled.append(feature)
            elif score >= min_score:
                enabled.append(feature)
            else:
                disabled.append(feature)

        if gpu_available:
            enabled.append("cuda_acceleration")
        else:
            disabled.append("cuda_acceleration")

        if self.hardware_profile.storage.disk_type == "SSD":
            enabled.append("fast_storage_access")
        else:
            disabled.append("fast_storage_access")

        return enabled, disabled

    def _determine_deployment_mode(self) -> DeploymentMode:
        score = self.hardware_profile.ai_capability_score
        if score >= 90: return DeploymentMode.EXTREME
        if score >= 70: return DeploymentMode.PERFORMANCE
        if score >= 50: return DeploymentMode.STANDARD
        if score >= 30: return DeploymentMode.LITE
        return DeploymentMode.MINIMAL

    def _generate_compression_config(self, mode: DeploymentMode) -> CompressionConfig:
        """Generate compression configuration based on deployment mode"""
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
            },
            DeploymentMode.CLUSTER: {
                "compression_level": "low",
                "vector_dimensions": 768,
                "chunk_size": 2048,
                "cache_size_mb": 512,
                "use_quantization": False
            }
        }

        return CompressionConfig(**configs[mode])

    def apply_config(self, config: Optional[DeploymentConfig] = None) -> Dict[str, Any]:
        """Apply configuration to system and return settings dict"""
        if config is None:
            config = self.generate_config()
            
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
            "FEATURES_ENABLED": ", ".join(config.features_enabled),
            "FEATURES_DISABLED": ", ".join(config.features_disabled),
            "CLUSTER_ROLE": config.cluster_role or "none"
        }

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
            config_dict = asdict(config)
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

        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            mode = DeploymentMode(data['mode'])
            
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

            compression_data = data['compression_config']
            compression_config = CompressionConfig(
                compression_level=compression_data['compression_level'],
                vector_dimensions=compression_data['vector_dimensions'],
                chunk_size=compression_data['chunk_size'],
                cache_size_mb=compression_data['cache_size_mb'],
                use_quantization=compression_data['use_quantization']
            )

            processing_data = data['processing_config']
            processing_config = ProcessingConfig(
                enable_multimodal=processing_data['enable_multimodal'],
                enable_real_time=processing_data['enable_real_time'],
                enable_background_learning=processing_data['enable_background_learning'],
                max_concurrent_tasks=processing_data['max_concurrent_tasks'],
                timeout_seconds=processing_data['timeout_seconds']
            )

            # Reconstruct HardwareProfile if needed, but usually we just use the current one
            # For simplicity, we'll just use the saved one or re-probe
            hardware_profile = self.hardware_profile # Fallback to current

            return DeploymentConfig(
                mode=mode,
                model_config=model_config,
                compression_config=compression_config,
                processing_config=processing_config,
                hardware_profile=hardware_profile,
                features_enabled=data['features_enabled'],
                features_disabled=data['features_disabled'],
                cluster_role=data.get('cluster_role')
            )
        except Exception as e:
            logger.error(f"Failed to load deployment config: {e}")
            return None

def get_deployment_config(cluster_mode: bool = False) -> DeploymentConfig:
    """Helper function to get current deployment configuration"""
    manager = DeploymentManager()
    return manager.generate_config(cluster_mode=cluster_mode)
