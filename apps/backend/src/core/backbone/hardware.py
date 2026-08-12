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
        except Exception:
            return 0.0

    @staticmethod
    def _detect_gpu() -> Dict[str, Any]:
        result = {"gpu": None, "gpu_memory_gb": 0}
        try:
            import subprocess
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            lines = out.decode().strip().split("\n")
            if lines:
                parts = lines[0].split(",")
                if len(parts) >= 2:
                    result["gpu"] = parts[0].strip()
                    result["gpu_memory_gb"] = float(parts[1].strip()) / 1024
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass
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
        if hw.get("gpu") and hw.get("gpu_memory_gb", 0) >= 8 and hw.get("ram_gb", 0) >= 16:
            return "high_performance_gpu"
        if hw.get("ram_gb", 0) >= 16:
            return "high_performance_desktop"
        if hw.get("ram_gb", 0) >= 8:
            return "laptop_normal"
        if hw.get("ram_gb", 0) >= 4:
            return "laptop_power_saver"
        return "low_power_device"


__all__ = ["HardwareProfile"]
