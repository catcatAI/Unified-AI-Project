"Real-time hardware resource awareness for Angela AI.\nProvides system load metrics (CPU/RAM), throttling factor for dynamic scaling,\nand available memory for LLM model selection.\n"

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import yaml  # type: ignore[import-untyped]

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)


# Mock types for syntax validation
@dataclass
class SimulatedDiskConfig:
    space_gb: float = 1.0
    warning_threshold_percent: int = 80
    critical_threshold_percent: int = 90
    lag_factor_warning: float = 1.0
    lag_factor_critical: float = 1.0


@dataclass
class SimulatedCPUConfig:
    cores: int = 1


@dataclass
class SimulatedRAMConfig:
    ram_gb: float = 1.0


@dataclass
class SimulatedHardwareProfile:
    profile_name: str = "DefaultProfile"
    disk: SimulatedDiskConfig = field(default_factory=SimulatedDiskConfig)
    cpu: SimulatedCPUConfig = field(default_factory=SimulatedCPUConfig)
    ram: SimulatedRAMConfig = field(default_factory=SimulatedRAMConfig)
    gpu_available: bool = False


DEFAULT_CONFIG_PATH = "configs/simulated_resources.yaml"


class ResourceAwarenessService:
    """
    Real-time system resource monitor for dynamic LLM model selection.
    Provides CPU load, memory pressure, throttling factor, and available RAM.
    Used by NeuroAutoSelector for [auto] LLM mode budget calculation.
    """

    def __init__(self, config_filepath: Optional[str] = None) -> None:
        self.psutil = psutil

        self.config_filepath = config_filepath or DEFAULT_CONFIG_PATH
        self.profile: Optional[SimulatedHardwareProfile] = None
        self._load_profile()

    def _load_profile(self) -> None:
        """Load profile."""
        try:
            backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            full_path = os.path.join(backend_root, self.config_filepath)
            if not os.path.exists(full_path):
                logger.warning("Simulated resources config not found: %s", full_path)
                return
            with open(full_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data or "simulated_hardware_profile" not in data:
                logger.warning("No simulated_hardware_profile in config")
                return
            profile_data = data["simulated_hardware_profile"]
            disk = SimulatedDiskConfig(**profile_data.get("disk", {}))
            cpu = SimulatedCPUConfig(**profile_data.get("cpu", {}))
            ram = SimulatedRAMConfig(**profile_data.get("ram", {}))
            self.profile = SimulatedHardwareProfile(
                profile_name=profile_data.get("profile_name", "DefaultProfile"),
                disk=disk,
                cpu=cpu,
                ram=ram,
                gpu_available=profile_data.get("gpu_available", False),
            )
        except Exception as e:
            logger.warning("Failed to load simulated resources: %s", e)

    def get_realtime_metrics(self) -> Dict[str, Any]:
        """獲取真實硬體指標"""
        if not self.psutil:
            return {"error": "psutil not available"}

        return {
            "cpu_percent": self.psutil.cpu_percent(interval=None),
            "memory_percent": self.psutil.virtual_memory().percent,
            "disk_percent": self.psutil.disk_usage("/").percent,
            "is_stressed": self.is_system_stressed(),
        }

    def is_system_stressed(self) -> bool:
        """判斷系統是否處於高壓力狀態"""
        if not self.psutil:
            return False

        cpu = self.psutil.cpu_percent(interval=None)
        mem = self.psutil.virtual_memory().percent

        # 壓力定義：CPU > 80% 或 MEM > 容量上限（預設 80%）
        from core.system.config.magic_numbers import capacity_percent

        mem_cap = capacity_percent("memory", 0.8)
        if isinstance(mem_cap, dict):
            mem_cap = mem_cap.get("max_percent", 0.8)
        mem_pct = float(mem_cap) if mem_cap else 0.8
        if 0 < mem_pct <= 1:
            mem_pct *= 100
        return cpu > 80 or mem > mem_pct

    def get_throttling_factor(self) -> float:
        """
        獲取節流因子 (0.0 - 1.0)
        連續縮放：1.0 (輕載) ~ 0.2 (滿載)
        反轉含義：因子的值代表可用預算比例，而非節流強度。
        """
        if not self.psutil:
            return 1.0

        cpu = self.psutil.cpu_percent(interval=0.1) / 100.0
        mem = self.psutil.virtual_memory().percent / 100.0

        # CPU 和記憶體的加權組合（已反轉：低負載→高預算，高負載→低預算）
        load = min(cpu * 0.6 + mem * 0.4, 1.0)

        return max(1.0 - load, 0.2)

    def get_available_disk_space_gb(self, path: Optional[str] = None) -> float:
        """Get free disk space in GB for ``path`` (default '/').

        Used by memory backends to refuse writes before the disk cap is hit
        (graceful precision-loss: skip the write, never truncate the store).
        Returns the free space on success, or 0.0 when psutil is unavailable.
        """
        if not self.psutil:
            return 0.0
        try:
            target = path or "/"
            usage = self.psutil.disk_usage(target)
            return usage.free / (1024 * 1024 * 1024)
        except Exception as e:
            logger.warning("Disk usage unavailable for %s: %s", path, e)
            return 0.0

    def is_disk_at_capacity(self, path: Optional[str] = None) -> bool:
        """True when disk usage is at/above the capacity cascade's disk cap.

        Uses the joint [bytes, percent] rule from system.capacity.capacity.disk:
        whichever of (numeric cap, percent cap) triggers first is the limit.
        """
        from core.system.config.magic_numbers import capacity_percent, effective_capacity_bytes

        if not self.psutil:
            return False
        try:
            target = path or "/"
            usage = self.psutil.disk_usage(target)
            disk_pct = usage.used / usage.total
            cap = capacity_percent("disk", 0.8)
            if isinstance(cap, dict):
                cap = cap.get("max_percent", 0.8)
            pct_cap = float(cap) if cap else 0.8
            if 0 < pct_cap <= 1:
                pct_cap *= 100
            numeric_cap_bytes = effective_capacity_bytes("disk", total_gb=usage.total / (1024**3))
            at_pct = disk_pct * 100 >= pct_cap
            at_bytes = usage.used >= numeric_cap_bytes if numeric_cap_bytes > 0 else False
            return at_pct or at_bytes
        except Exception as e:
            logger.warning("Disk capacity check failed: %s", e)
            return False

    def get_available_ram_mb(self) -> float:
        """獲取可用 RAM（MB）"""
        if not self.psutil:
            # No reliable cross-platform way to query available RAM without psutil;
            # 512 MB is a conservative safe fallback.
            return 512.0
        return self.psutil.virtual_memory().available / (1024 * 1024)

    def get_simulated_disk_config(self) -> Optional[SimulatedDiskConfig]:
        """獲取模擬磁碟配置（用於測試）"""
        if self.profile:
            return self.profile.disk
        return None

    def get_cpu_count(self) -> int:
        """獲取 CPU 邏輯核心數"""
        if not self.psutil:
            return os.cpu_count() or 1
        return self.psutil.cpu_count(logical=True)


if __name__ == "__main__":
    logger.info("--- ResourceAwarenessService Standalone Test ---")

    # Test with default path (requires configs/simulated_resources.yaml to exist)
    logger.info("\n1. Testing with default config path:")
    service_default = ResourceAwarenessService()
    if service_default.profile:
        logger.info(f"  Profile Name: {service_default.profile.profile_name}")
        disk_conf = service_default.get_simulated_disk_config()
        if disk_conf:
            logger.info(f"  Disk Space (GB): {disk_conf.space_gb}")
            logger.warning(f"  Disk Warning Threshold (%): {disk_conf.warning_threshold_percent}")
        else:
            logger.info("  No disk config found in default profile.")
    else:
        logger.error("  Failed to load default profile.")

    # Test with a non-existent config file path
    logger.info("\n2. Testing with non-existent config file:")
    service_non_existent = ResourceAwarenessService(
        config_filepath="configs/non_existent_resources.yaml"
    )
    if (
        service_non_existent.profile
        and service_non_existent.profile.profile_name == "SafeDefaultProfile_ErrorLoading"
    ):
        logger.info(
            f"  Correctly fell back to safe default: {service_non_existent.profile.profile_name}"
        )
        logger.info(
            f"  Default Disk Space (GB): {service_non_existent.get_simulated_disk_config().space_gb if service_non_existent.get_simulated_disk_config() else 'N/A'}"
        )
    else:
        logger.error(
            f"  Test failed or profile was unexpectedly loaded: {service_non_existent.profile}"
        )

    # Test with a malformed YAML file (requires creating one temporarily)
    logger.info("\n3. Testing with malformed YAML config file:")
    malformed_yaml_path = "configs/temp_malformed_resources.yaml"
    with open(malformed_yaml_path, "w", encoding="utf-8") as f:
        f.write(
            "simulated_hardware_profile: \n  disk: [this is not a dict]\n  profile_name: MalformedProfile"
        )  # Intentional malformed YAML

    service_malformed = ResourceAwarenessService(config_filepath=malformed_yaml_path)
    if (
        service_malformed.profile
        and service_malformed.profile.profile_name == "SafeDefaultProfile_ErrorLoading"
    ):
        logger.info(
            f"  Correctly fell back to safe default for malformed YAML: {service_malformed.profile.profile_name}"
        )
    else:
        logger.error(
            f"  Test failed for malformed YAML or profile was unexpectedly loaded: {service_malformed.profile}"
        )

    if os.path.exists(malformed_yaml_path):
        os.remove(malformed_yaml_path)

    logger.info("\nResourceAwarenessService standalone test finished.")
    logger.info("ResourceAwarenessService module loaded.")
