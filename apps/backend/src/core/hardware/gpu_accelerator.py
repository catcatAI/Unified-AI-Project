"""
Angela AI - GPU Accelerator Service
GPU 加速服務模組，為 Live2D/WebGL 提供模擬獨顯功能

功能:
- GPU 資源調度
- 渲染優先級管理
- 內存優化
- 精度模式切換
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class GPUPriority(Enum):
    """GPU 渲染優先級"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    REALTIME = 3


class RenderQuality(Enum):
    """渲染質量等級"""
    LOW = {"fps": 30, "width": 512, "height": 512}
    MEDIUM = {"fps": 45, "width": 768, "height": 768}
    HIGH = {"fps": 60, "width": 1024, "height": 1024}
    ULTRA = {"fps": 120, "width": 1536, "height": 1536}


@dataclass
class GPUContext:
    """GPU 上下文"""
    context_id: str
    priority: GPUPriority = GPUPriority.NORMAL
    quality: RenderQuality = RenderQuality.MEDIUM
    memory_mb: int = 128
    acceleration_enabled: bool = True
    precision_mode: str = "FP16"


@dataclass
class GPUMetrics:
    """GPU 指標"""
    context_id: str
    fps: float
    memory_used_mb: float
    frame_time_ms: float
    gpu_utilization: float
    timestamp: float = 0.0


class GPUAcceleratorService:
    """
    GPU 加速服務
    
    為 Angela AI Matrix 提供模擬獨顯功能:
    - Live2D WebGL 渲染加速
    - 智能內存管理
    - 渲染優先級調度
    - 多精度模式支持
    """
    
    _instance: Optional['GPUAcceleratorService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.active_contexts: Dict[str, GPUContext] = {}
        self.metrics_history: List[GPUMetrics] = []
        self.quality_profiles: Dict[str, RenderQuality] = {}
        self._gpu_info: Dict[str, Any] = {}
        self._performance_mode: str = "balanced"
        self._is_active: bool = False
        
        # 初始化質量配置
        self._init_quality_profiles()
        
    def _init_quality_profiles(self):
        """初始化渲染質量配置"""
        self.quality_profiles = {
            "battery": RenderQuality.LOW,
            "balanced": RenderQuality.MEDIUM,
            "performance": RenderQuality.HIGH,
            "ultra": RenderQuality.ULTRA
        }
    
    async def initialize(self, gpu_info: Dict[str, Any] = None) -> bool:
        """
        初始化 GPU 加速服務
        
        Args:
            gpu_info: GPU 信息 (從 WebGL 獲取)
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("Initializing GPU Accelerator Service...")
            
            # 存儲 GPU 信息
            if gpu_info:
                self._gpu_info = gpu_info
                logger.info(f"GPU detected: {gpu_info.get('name', 'Unknown')}")
            else:
                # 使用模擬獨顯配置
                self._gpu_info = {
                    "name": "Angela Simulated Discrete GPU",
                    "vendor": "Angela AI Matrix",
                    "memory_mb": 2048,
                    "compute_units": 8,
                    "precision": ["FP16", "FP32", "INT8"],
                    "webgl_version": "2.0"
                }
                logger.info("Using simulated discrete GPU configuration")
            
            # 創建 Live2D 專用上下文
            await self._create_live2d_context()
            
            self._is_active = True
            logger.info("GPU Accelerator Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize GPU Accelerator: {e}")
            return False
    
    async def _create_live2d_context(self) -> str:
        """創建 Live2D 專用 GPU 上下文"""
        context_id = "live2d_main"
        
        context = GPUContext(
            context_id=context_id,
            priority=GPUPriority.HIGH,
            quality=self.quality_profiles.get(self._performance_mode, RenderQuality.MEDIUM),
            memory_mb=256,
            acceleration_enabled=True,
            precision_mode="FP16"
        )
        
        self.active_contexts[context_id] = context
        logger.info(f"Created Live2D context: {context_id}")
        
        return context_id
    
    def get_context(self, context_id: str) -> Optional[GPUContext]:
        """獲取 GPU 上下文"""
        return self.active_contexts.get(context_id)
    
    def get_live2d_context(self) -> Optional[GPUContext]:
        """獲取 Live2D 專用上下文"""
        return self.active_contexts.get("live2d_main")
    
    async def set_quality(self, context_id: str, quality: str) -> bool:
        """
        設置渲染質量
        
        Args:
            context_id: 上下文 ID
            quality: 質量等級 ("low", "medium", "high", "ultra")
            
        Returns:
            bool: 是否成功
        """
        try:
            render_quality = self.quality_profiles.get(quality, RenderQuality.MEDIUM)
            
            if context_id in self.active_contexts:
                self.active_contexts[context_id].quality = render_quality
                logger.info(f"Set quality for {context_id}: {quality}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to set quality: {e}")
            return False
    
    async def set_priority(self, context_id: str, priority: str) -> bool:
        """
        設置渲染優先級
        
        Args:
            context_id: 上下文 ID
            priority: 優先級 ("low", "normal", "high", "realtime")
            
        Returns:
            bool: 是否成功
        """
        try:
            priority_map = {
                "low": GPUPriority.LOW,
                "normal": GPUPriority.NORMAL,
                "high": GPUPriority.HIGH,
                "realtime": GPUPriority.REALTIME
            }
            
            gpu_priority = priority_map.get(priority, GPUPriority.NORMAL)
            
            if context_id in self.active_contexts:
                self.active_contexts[context_id].priority = gpu_priority
                logger.info(f"Set priority for {context_id}: {priority}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to set priority: {e}")
            return False
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """獲取 GPU 信息"""
        return {
            "name": self._gpu_info.get("name", "Simulated GPU"),
            "vendor": self._gpu_info.get("vendor", "Angela AI"),
            "active_contexts": len(self.active_contexts),
            "is_active": self._is_active,
            "performance_mode": self._performance_mode,
            "precision_mode": self.get_live2d_context().precision_mode if self.get_live2d_context() else "N/A",
            "webgl_info": {
                "version": self._gpu_info.get("webgl_version", "2.0"),
                "extensions": self._gpu_info.get("extensions", [])
            }
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """獲取 GPU 能力"""
        return {
            "max_texture_size": 4096,
            "max_vertex_attribs": 16,
            "max_varying_vectors": 16,
            "max_uniform_vectors": 256,
            "supports_float_textures": True,
            "supports_half_float_textures": True,
            "supports_instanced_rendering": True,
            "supports_geometry_shaders": True,
            "supports_compute_shaders": self._gpu_info.get("compute_units", 8) > 0
        }
    
    async def record_metrics(self, context_id: str, fps: float, memory_mb: float, 
                            frame_time_ms: float, gpu_util: float):
        """記錄 GPU 指標"""
        metrics = GPUMetrics(
            context_id=context_id,
            fps=fps,
            memory_used_mb=memory_mb,
            frame_time_ms=frame_time_ms,
            gpu_utilization=gpu_util,
            timestamp=asyncio.get_event_loop().time()
        )
        
        self.metrics_history.append(metrics)
        
        # 保持歷史在 100 條以內
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]
    
    def get_metrics(self, context_id: str = None) -> List[GPUMetrics]:
        """獲取 GPU 指標歷史"""
        if context_id:
            return [m for m in self.metrics_history if m.context_id == context_id]
        return self.metrics_history
    
    def get_average_fps(self, context_id: str = None) -> float:
        """計算平均 FPS"""
        metrics = self.get_metrics(context_id)
        if not metrics:
            return 0.0
        return sum(m.fps for m in metrics) / len(metrics)
    
    def set_performance_mode(self, mode: str) -> bool:
        """
        設置性能模式
        
        Args:
            mode: 模式 ("battery", "balanced", "performance", "ultra")
            
        Returns:
            bool: 是否成功
        """
        if mode in self.quality_profiles:
            self._performance_mode = mode
            # 更新 Live2D 上下文質量
            live2d_ctx = self.get_live2d_context()
            if live2d_ctx:
                live2d_ctx.quality = self.quality_profiles[mode]
            return True
        return False
    
    async def optimize_for_live2d(self) -> Dict[str, Any]:
        """
        優化 Live2D 渲染配置
        
        Returns:
            Dict: 優化配置
        """
        live2d_ctx = self.get_live2d_context()
        
        if not live2d_ctx:
            return {"error": "No Live2D context found"}
        
        # 自動優化配置
        optimizations = {
            "priority": "high",
            "quality": self._performance_mode,
            "precision": "FP16",
            "memory_mb": 256,
            "recommended_fps": live2d_ctx.quality.value["fps"],
            "recommended_resolution": {
                "width": live2d_ctx.quality.value["width"],
                "height": live2d_ctx.quality.value["height"]
            },
            "webgl_settings": {
                "antialias": True,
                "preserveDrawingBuffer": False,
                "powerPreference": "high-performance",
                "failIfMajorPerformanceCaveat": False
            }
        }
        
        logger.info(f"Live2D optimizations: {optimizations}")
        return optimizations
    
    def is_available(self) -> bool:
        """檢查 GPU 加速是否可用"""
        return self._is_active
    
    async def shutdown(self):
        """關閉 GPU 加速服務"""
        self.active_contexts.clear()
        self.metrics_history.clear()
        self._is_active = False
        logger.info("GPU Accelerator Service shutdown complete")


# 全局服務實例
_gpu_service: Optional[GPUAcceleratorService] = None


def get_gpu_service() -> GPUAcceleratorService:
    """獲取 GPU 加速服務實例"""
    global _gpu_service
    if _gpu_service is None:
        _gpu_service = GPUAcceleratorService()
    return _gpu_service


async def initialize_gpu_service(gpu_info: Dict[str, Any] = None) -> bool:
    """初始化 GPU 加速服務"""
    service = get_gpu_service()
    return await service.initialize(gpu_info)


def gpu_available() -> bool:
    """檢查 GPU 加速是否可用"""
    service = get_gpu_service()
    return service.is_available()
