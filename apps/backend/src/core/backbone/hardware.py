# =============================================================================
# ANGELA-MATRIX: [L1] [η] [A] [L1]
# =============================================================================
"""
Hardware Profile — 硬體檢測與自適應配置。

檢測 GPU/CPU/記憶體/OS，為 Backbone 自動選擇最佳引擎實現。
"""

import logging
import os
import platform
from typing import Any, Dict

logger = logging.getLogger(__name__)


class HardwareProfile:
    """檢測系統硬體配置。"""

    @staticmethod
    def detect() -> Dict[str, Any]:
        hw = {
            "os": platform.system(),
            "os_version": platform.version(),
            "arch": platform.machine(),
            "python_version": platform.python_version(),
            "cpu_cores": os.cpu_count() or 1,
            "ram_gb": HardwareProfile._get_ram_gb(),
            "gpu": None,
            "gpu_memory_gb": 0,
            "torch_available": False,
            "chromadb_available": False,
            "disk_free_gb": HardwareProfile._get_disk_free_gb(),
        }
        hw.update(HardwareProfile._detect_gpu())
        hw["torch_available"] = HardwareProfile._check_torch()
        hw["chromadb_available"] = HardwareProfile._check_chromadb()
        return hw

    @staticmethod
    def _get_ram_gb() -> float:
        try:
            import psutil
            return psutil.virtual_memory().total / (1024 ** 3)
        except ImportError:
            pass
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal"):
                        kb = int(line.split()[1])
                        return kb / (1024 ** 2)
        except (FileNotFoundError, ValueError):
            pass
        return 4.0

    @staticmethod
    def _get_disk_free_gb() -> float:
        try:
            import shutil
            return shutil.disk_usage("/").free / (1024 ** 3)
        except Exception as e:
            logger.debug(f"disk_usage failed: {e}", exc_info=True)
            return 0.0

    @staticmethod
    def _detect_gpu() -> Dict[str, Any]:
        result = {"gpu": None, "gpu_memory_gb": 0}
        # 1) NVIDIA via nvidia-smi
        try:
            import subprocess
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            lines = out.decode().strip().split("\n")
            if lines and lines[0].strip():
                parts = lines[0].split(",")
                if len(parts) >= 2:
                    result["gpu"] = parts[0].strip()
                    result["gpu_memory_gb"] = float(parts[1].strip()) / 1024
                    return result
                elif parts[0].strip():
                    result["gpu"] = parts[0].strip()
                    return result
        except Exception as e:
            logger.debug("nvidia-smi unavailable: %s", e)

        # 2) Intel Arc / AMD via lspci or glxinfo (no nvidia-smi)
        try:
            import subprocess
            # Try lspci for Intel Arc / AMD
            try:
                out = subprocess.check_output(
                    ["lspci"], stderr=subprocess.DEVNULL, timeout=5
                ).decode()
                for line in out.splitlines():
                    low = line.lower()
                    if "arc" in low and "intel" in low:
                        # e.g. "VGA: Intel Corporation Arc B570 Graphics (BMG G21)"
                        result["gpu"] = line.split(":")[-1].strip()
                        # Arc B570 = 10GB, B580 = 12GB; default 10 if unknown
                        if "b580" in low:
                            result["gpu_memory_gb"] = 12
                        elif "b570" in low:
                            result["gpu_memory_gb"] = 10
                        else:
                            result["gpu_memory_gb"] = 8
                        logger.debug(f"Detected Intel Arc via lspci: {result}")
                        return result
                    if "amd" in low and ("radeon" in low or "vga" in low):
                        result["gpu"] = line.split(":")[-1].strip()
                        result["gpu_memory_gb"] = 8
                        return result
            except Exception:
                pass

            # Fallback: glxinfo renderer string (Mesa)
            try:
                out = subprocess.check_output(
                    ["glxinfo"], stderr=subprocess.DEVNULL, timeout=5
                ).decode()
                for line in out.splitlines():
                    if "OpenGL renderer string" in line:
                        renderer = line.split(":", 1)[-1].strip()
                        low = renderer.lower()
                        if "arc" in low:
                            result["gpu"] = renderer
                            if "b580" in low:
                                result["gpu_memory_gb"] = 12
                            elif "b570" in low:
                                result["gpu_memory_gb"] = 10
                            else:
                                result["gpu_memory_gb"] = 8
                            return result
                        if "intel" in low or "amd" in low:
                            result["gpu"] = renderer
                            result["gpu_memory_gb"] = 4
                            return result
            except Exception:
                pass

            # Fallback: /dev/dri existence (Intel/AMD present but no info)
            import os
            if os.path.exists("/dev/dri"):
                # At least one GPU exists, try to infer via render name
                if os.path.exists("/dev/dri/renderD128"):
                    result["gpu"] = "Intel/AMD GPU (renderD128)"
                    result["gpu_memory_gb"] = 4
                    # Don't return yet — keep as fallback if nothing else matched
        except Exception as e:
            logger.debug(f"Intel/AMD GPU detect failed: {e}", exc_info=True)
        return result

    @staticmethod
    def _check_torch() -> bool:
        try:
            import torch
            return True
        except ImportError:
            return False

    @staticmethod
    def _check_chromadb() -> bool:
        try:
            import chromadb
            return True
        except ImportError:
            return False

    @staticmethod
    def get_tier(hw: Dict[str, Any]) -> str:
        # Intel Arc B570 (10GB) + 15GB RAM -> high_performance_desktop (desktop, not laptop)
        # Respect explicit env ANGELA_HARDWARE_PROFILE if set (handled in Backbone)
        has_gpu = bool(hw.get("gpu"))
        gpu_gb = hw.get("gpu_memory_gb", 0) or 0
        ram_gb = hw.get("ram_gb", 0) or 0
        # Desktop with discrete GPU (Arc/NVIDIA) + ≥12GB RAM -> high_performance_desktop
        if has_gpu and gpu_gb >= 8 and ram_gb >= 12:
            return "high_performance_desktop"
        if has_gpu and gpu_gb >= 8 and ram_gb >= 16:
            return "high_performance_gpu"
        if ram_gb >= 16:
            return "high_performance_desktop"
        if ram_gb >= 8:
            return "laptop_normal"
        if ram_gb >= 4:
            return "laptop_power_saver"
        return "low_power_device"


__all__ = ["HardwareProfile"]
