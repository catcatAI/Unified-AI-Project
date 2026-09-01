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

    # Intel Arc PCI device ID -> model/VRAM mapping (spec-driven, not label-driven)
    _INTEL_ARC_IDS = {
        "e20b": ("Arc B580", 12),
        "e20c": ("Arc B570", 10),
        "e20d": ("Arc B570", 10),
        "56a0": ("Arc A770", 16),
        "56a1": ("Arc A750", 8),
        "56a5": ("Arc A380", 6),
        "5690": ("Arc A370M", 4),
    }

    @staticmethod
    def _detect_gpu() -> Dict[str, Any]:
        """Truly hardware-driven GPU detection — vendor/model/VRAM from actual hardware.

        Priority: nvidia-smi (NVIDIA) -> lspci -nn device ID (Intel Arc/AMD) ->
        glxinfo renderer + Video memory -> /dev/dri fallback.
        Returns actual specs, not form-factor labels.
        """
        result = {"gpu": None, "gpu_memory_gb": 0, "gpu_vendor": None, "gpu_device_id": None}
        import subprocess

        # 1) NVIDIA via nvidia-smi (most precise for NVIDIA)
        try:
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
                    result["gpu_vendor"] = "nvidia"
                    return result
                elif parts[0].strip():
                    result["gpu"] = parts[0].strip()
                    result["gpu_vendor"] = "nvidia"
                    return result
        except Exception as e:
            logger.debug("nvidia-smi unavailable: %s", e)

        # 2) Intel Arc / AMD via lspci -nn (device ID is hardware truth, not marketing string)
        try:
            out = subprocess.check_output(
                ["lspci", "-nn"], stderr=subprocess.DEVNULL, timeout=5
            ).decode()
            for line in out.splitlines():
                low = line.lower()
                # Intel Arc detection via device ID (e.g. 8086:e20c = B570)
                if "8086:" in low:
                    # Extract device ID: [8086:e20c]
                    import re
                    m = re.search(r"\[8086:([0-9a-f]{4})\]", low)
                    if m:
                        dev_id = m.group(1)
                        if dev_id in HardwareProfile._INTEL_ARC_IDS:
                            model, vram = HardwareProfile._INTEL_ARC_IDS[dev_id]
                            result["gpu"] = f"Intel Arc {model} ({dev_id})"
                            result["gpu_memory_gb"] = vram
                            result["gpu_vendor"] = "intel"
                            result["gpu_device_id"] = dev_id
                            # Try to refine VRAM via glxinfo (more accurate if available)
                            try:
                                glx = subprocess.check_output(
                                    ["glxinfo"], stderr=subprocess.DEVNULL, timeout=3
                                ).decode()
                                for gl in glx.splitlines():
                                    if "Video memory:" in gl or "Dedicated video memory:" in gl:
                                        # e.g. "Video memory: 10172MB"
                                        m2 = re.search(r"(\d+)\s*MB", gl)
                                        if m2:
                                            vram_mb = int(m2.group(1))
                                            result["gpu_memory_gb"] = round(vram_mb / 1024, 1)
                                            break
                            except Exception:
                                pass
                            logger.debug(f"Detected Intel Arc via device ID {dev_id}: {result}")
                            return result
                    # Fallback: string match for Arc without device ID
                    if "arc" in low:
                        result["gpu"] = line.split(":")[-1].strip()
                        if "b580" in low:
                            result["gpu_memory_gb"] = 12
                        elif "b570" in low:
                            result["gpu_memory_gb"] = 10
                        else:
                            result["gpu_memory_gb"] = 8
                        result["gpu_vendor"] = "intel"
                        return result
                if "amd" in low and ("radeon" in low or "vga" in low or "display" in low):
                    result["gpu"] = line.split(":")[-1].strip()
                    result["gpu_vendor"] = "amd"
                    result["gpu_memory_gb"] = 8
                    return result
        except Exception:
            pass

        # Legacy lspci without -nn (fallback)
        try:
            out = subprocess.check_output(
                ["lspci"], stderr=subprocess.DEVNULL, timeout=5
            ).decode()
            for line in out.splitlines():
                low = line.lower()
                if "arc" in low and "intel" in low:
                    result["gpu"] = line.split(":")[-1].strip()
                    if "b580" in low:
                        result["gpu_memory_gb"] = 12
                    elif "b570" in low:
                        result["gpu_memory_gb"] = 10
                    else:
                        result["gpu_memory_gb"] = 8
                    result["gpu_vendor"] = "intel"
                    return result
        except Exception:
            pass

        # 3) glxinfo renderer + Video memory (Mesa - accurate VRAM)
        try:
            out = subprocess.check_output(
                ["glxinfo"], stderr=subprocess.DEVNULL, timeout=5
            ).decode()
            vram_mb = None
            renderer = None
            for line in out.splitlines():
                if "Video memory:" in line or "Dedicated video memory:" in line:
                    import re
                    m = re.search(r"(\d+)\s*MB", line)
                    if m:
                        vram_mb = int(m.group(1))
                if "OpenGL renderer string" in line:
                    renderer = line.split(":", 1)[-1].strip()
            if renderer:
                low = renderer.lower()
                result["gpu"] = renderer
                if vram_mb:
                    result["gpu_memory_gb"] = round(vram_mb / 1024, 1)
                elif "arc" in low:
                    if "b580" in low:
                        result["gpu_memory_gb"] = 12
                    elif "b570" in low:
                        result["gpu_memory_gb"] = 10
                    else:
                        result["gpu_memory_gb"] = 8
                elif "intel" in low or "amd" in low:
                    result["gpu_memory_gb"] = result["gpu_memory_gb"] or 4
                if "intel" in low:
                    result["gpu_vendor"] = "intel"
                elif "amd" in low:
                    result["gpu_vendor"] = "amd"
                elif "nvidia" in low:
                    result["gpu_vendor"] = "nvidia"
                if result["gpu"]:
                    return result
        except Exception:
            pass

        # 4) /dev/dri existence (last resort)
        try:
            import os
            if os.path.exists("/dev/dri/renderD128"):
                result["gpu"] = result["gpu"] or "Intel/AMD GPU (renderD128)"
                result["gpu_memory_gb"] = result["gpu_memory_gb"] or 4
                result["gpu_vendor"] = result["gpu_vendor"] or "unknown"
        except Exception as e:
            logger.debug(f"GPU dri fallback failed: {e}", exc_info=True)
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
        """Hardware-driven tier — purely spec-based, not form-factor.

        Tiers are derived from actual RAM + VRAM + CPU cores, not whether the
        machine is called 'laptop' or 'desktop'. The same hardware gets the
        same tier and the same adaptive compute regardless of chassis.

        Tiers (backwards-compatible names, but spec-defined):
          server_cloud: headless or RAM≥32 or (GPU≥16+RAM≥32)
          high_performance_gpu: GPU≥8 + RAM≥16 (discrete GPU workstation)
          high_performance_desktop: GPU≥6 + RAM≥12 or RAM≥16 (current: Arc B570 10GB + 15GB -> this tier)
          desktop_igpu: iGPU + RAM≥8
          laptop_normal: RAM≥8 (no dGPU or <6GB VRAM)
          laptop_power_saver: RAM 4-8GB
          low_power_device: RAM<4GB
        """
        # Allow explicit override (hardware-adaptive respects user choice)
        import os
        env = os.environ.get("ANGELA_HARDWARE_PROFILE")
        if env:
            # Validate against known tiers
            known = {"high_performance_desktop", "desktop_igpu", "laptop_normal",
                     "laptop_power_saver", "low_power_device", "server_cloud",
                     "high_performance_gpu", "auto"}
            if env in known and env != "auto":
                return env

        has_gpu = bool(hw.get("gpu"))
        gpu_gb = hw.get("gpu_memory_gb", 0) or 0
        ram_gb = hw.get("ram_gb", 0) or 0
        cpu_cores = hw.get("cpu_cores", 0) or 0
        # Check headless (server) via env — but spec still matters
        is_headless = not bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
        is_ssh = "SSH_CLIENT" in os.environ or "SSH_TTY" in os.environ

        # Pure spec-driven tiers (hardware first, chassis irrelevant)
        if is_headless and not is_ssh and ram_gb >= 8:
            # Headless Linux without SSH display -> likely server/cloud
            if ram_gb >= 32 or (has_gpu and gpu_gb >= 16):
                return "server_cloud"
        if has_gpu and gpu_gb >= 8 and ram_gb >= 16:
            return "high_performance_gpu"
        if has_gpu and gpu_gb >= 6 and ram_gb >= 12:
            return "high_performance_desktop"
        if ram_gb >= 16:
            return "high_performance_desktop"
        # Distinguish iGPU vs dGPU for 8-12GB range
        vendor = (hw.get("gpu_vendor") or "").lower()
        if vendor == "intel" and gpu_gb <= 4 and ram_gb >= 8:
            # Intel iGPU (e.g. UHD) shares system RAM, not discrete VRAM
            return "desktop_igpu" if cpu_cores >= 4 else "laptop_normal"
        if ram_gb >= 8:
            return "laptop_normal"
        if ram_gb >= 4:
            return "laptop_power_saver"
        return "low_power_device"

    @staticmethod
    def get_adaptive_compute(hw: Dict[str, Any]) -> Dict[str, Any]:
        """Compute truly hardware-adaptive values from actual specs.

        Not tier-lookup, but formula-driven from RAM/VRAM/CPU.
        Works identically on desktop or laptop with same hardware.

        Returns dict with recommended values that can override tier defaults.
        """
        ram_gb = hw.get("ram_gb", 0) or 0
        gpu_gb = hw.get("gpu_memory_gb", 0) or 0
        cpu_cores = hw.get("cpu_cores", 0) or 1
        disk_gb = hw.get("disk_free_gb", 0) or 0

        # Usable RAM for models: total - 2GB OS reserve, clamped
        usable_ram = max(1.0, ram_gb - 2.0)
        # GARDEN vocab matrix: V^2 * 4 bytes. Cap by RAM: sqrt(usable*percent)
        # lean = 10K (0.38GB), extended scale with RAM
        max_vocab = int(min(51812, max(5000, (usable_ram * 1024**3 * 0.15 / 4) ** 0.5)))
        # Round to sensible steps
        if max_vocab < 10000:
            max_vocab = 10000
        elif max_vocab < 20000:
            max_vocab = 15000
        elif max_vocab < 40000:
            max_vocab = 35000
        else:
            max_vocab = 51812

        # Connection budget scales with RAM
        connection_budget = int(min(1000000, max(30000, usable_ram * 30000)))

        # Batch sizes scale with CPU cores and RAM
        ed3n_batch_mult = 1.0
        if cpu_cores >= 8 and ram_gb >= 16:
            ed3n_batch_mult = 2.0
        elif cpu_cores >= 4 and ram_gb >= 12:
            ed3n_batch_mult = 1.5

        # Unified slots: 32K saves 96MB, 65K default, 131K for high RAM
        unified_slots = 65536
        if ram_gb >= 32 and gpu_gb >= 8:
            unified_slots = 131072
        elif ram_gb < 8 or gpu_gb < 4:
            unified_slots = 32768

        # Three-layer batch scales with RAM
        tl_batch = 32
        if ram_gb >= 16:
            tl_batch = 64
        elif ram_gb < 8:
            tl_batch = 16

        return {
            "ram_gb": ram_gb,
            "gpu_gb": gpu_gb,
            "cpu_cores": cpu_cores,
            "disk_free_gb": disk_gb,
            "usable_ram_gb": round(usable_ram, 1),
            "garden_max_vocab": max_vocab,
            "garden_connection_budget": connection_budget,
            "ed3n_batch_multiplier": ed3n_batch_mult,
            "unified_slots": unified_slots,
            "three_layer_batch": tl_batch,
            "source": "spec-driven (not tier label)",
        }


__all__ = ["HardwareProfile"]
