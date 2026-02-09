"""
Angela AI - WebGL Bridge
WebGL GPU 信息橋接模組

功能:
- 接收前端 WebGL GPU 檢測結果
- 轉換為 UHRC 格式
- 同步 GPU 加速服務配置
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class WebGLGPUInfo:
    """WebGL GPU 信息"""
    available: bool
    name: str
    vendor: str
    renderer: str
    version: str
    webgl_version: str
    unmasked_vendor: str
    unmasked_renderer: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebGLGPUInfo':
        """從字典創建 WebGLGPUInfo"""
        return cls(
            available=data.get("available", False),
            name=data.get("name", "Unknown GPU"),
            vendor=data.get("vendor", "Unknown"),
            renderer=data.get("renderer", "Unknown"),
            version=data.get("version", ""),
            webgl_version=data.get("webgl_version", "1.0"),
            unmasked_vendor=data.get("unmasked_vendor", ""),
            unmasked_renderer=data.get("unmasked_renderer", "")
        )
    
    def to_uhrc_format(self) -> Dict[str, Any]:
        """轉換為 UHRC 格式"""
        # 識別 GPU 類型
        gpu_type = self._detect_gpu_type()
        
        return {
            "name": self.name,
            "vendor": self.unmasked_vendor or self.vendor,
            "renderer": self.unmasked_renderer or self.renderer,
            "type": gpu_type,
            "webgl_version": self.webgl_version,
            "memory_estimate": self._estimate_memory(gpu_type),
            "capabilities": self._get_capabilities()
        }
    
    def _detect_gpu_type(self) -> str:
        """檢測 GPU 類型"""
        name_lower = self.name.lower()
        renderer_lower = self.renderer.lower() if self.renderer else ""
        
        if any(x in name_lower or x in renderer_lower for x in ["nvidia", "geforce", "rtx", "gtx"]):
            return "NVIDIA"
        elif any(x in name_lower or x in renderer_lower for x in ["amd", "radeon", "rx"]):
            return "AMD"
        elif any(x in name_lower or x in renderer_lower for x in ["intel", "uhd", "iris", "arc"]):
            return "INTEL"
        elif any(x in name_lower or x in renderer_lower for x in ["apple", "m1", "m2", "m3"]):
            return "APPLE"
        elif "swiftshader" in name_lower or "software" in renderer_lower:
            return "SOFTWARE"
        else:
            return "UNKNOWN"
    
    def _estimate_memory(self, gpu_type: str) -> int:
        """估算顯存"""
        memory_map = {
            "NVIDIA": 4096,
            "AMD": 4096,
            "INTEL": 2048,
            "APPLE": 8192,
            "SOFTWARE": 512,
            "UNKNOWN": 1024
        }
        return memory_map.get(gpu_type, 1024)
    
    def _get_capabilities(self) -> Dict[str, Any]:
        """獲取 GPU 能力"""
        return {
            "webgl2": self.webgl_version.startswith("2"),
            "float_textures": True,
            "half_float_textures": True,
            "instanced_rendering": True,
            "vertex_array_objects": True,
            "multisampled_buffers": True
        }


class WebGLBridge:
    """
    WebGL 到 UHRC 的橋接器
    
    使用方式:
    1. 前端發送 WebGL GPU 檢測結果
    2. WebGLBridge 轉換格式
    3. 更新 GPU 加速服務配置
    """
    
    _instance: Optional['WebGLBridge'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._gpu_info: Optional[WebGLGPUInfo] = None
        self._is_synced: bool = False
        
    async def process_gpu_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理前端發來的 GPU 信息
        
        Args:
            data: 前端 WebGL 檢測結果
            
        Returns:
            Dict: 處理結果
        """
        try:
            # 解析 GPU 信息
            self._gpu_info = WebGLGPUInfo.from_dict(data)
            
            logger.info(f"Received WebGL GPU info: {self._gpu_info.name}")
            
            # 轉換為 UHRC 格式
            uhrc_format = self._gpu_info.to_uhrc_format()
            
            # 初始化/更新 GPU 加速服務
            from .gpu_accelerator import initialize_gpu_service
            success = await initialize_gpu_service(uhrc_format)
            
            self._is_synced = success
            
            result = {
                "success": success,
                "gpu_type": uhrc_format["type"],
                "gpu_name": uhrc_format["name"],
                "gpu_memory_mb": uhrc_format["memory_estimate"],
                "webgl_version": uhrc_format["webgl_version"],
                "is_active": success
            }
            
            logger.info(f"WebGL Bridge result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process GPU info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_gpu_info(self) -> Optional[WebGLGPUInfo]:
        """獲取當前 GPU 信息"""
        return self._gpu_info
    
    def is_synced(self) -> bool:
        """檢查是否已同步"""
        return self._is_synced
    
    def get_summary(self) -> Dict[str, Any]:
        """獲取橋接器摘要"""
        if self._gpu_info:
            return {
                "gpu_name": self._gpu_info.name,
                "gpu_type": self._gpu_info._detect_gpu_type(),
                "vendor": self._gpu_info.vendor,
                "webgl_version": self._gpu_info.webgl_version,
                "is_synced": self._is_synced
            }
        return {
            "gpu_name": None,
            "gpu_type": None,
            "vendor": None,
            "webgl_version": None,
            "is_synced": False
        }


# 全局橋接器實例
_bridge: Optional[WebGLBridge] = None


def get_webgl_bridge() -> WebGLBridge:
    """獲取 WebGL 橋接器實例"""
    global _bridge
    if _bridge is None:
        _bridge = WebGLBridge()
    return _bridge


async def handle_gpu_info_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """處理 GPU 信息消息"""
    bridge = get_webgl_bridge()
    return await bridge.process_gpu_info(data)
