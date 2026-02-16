"Service to provide information about the AI's simulated hardware resources.\nLoads configuration from a YAML file and makes it accessible to other modules. (SKELETON)\n"

import os
import yaml  # type: ignore
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


# Mock types for syntax validation
@dataclass
class SimulatedDiskConfig:
    space_gb: float = 1.0
    warning_threshold_percent: int = 90
    critical_threshold_percent: int = 98
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
    Manages and provides access to the AI's simulated hardware resource profile. (SKELETON)
    """

    def __init__(self, config_filepath: Optional[str] = None) -> None:
        try:
            import psutil

            self.psutil = psutil
        except ImportError:
            self.psutil = None

        self.profile: Optional[SimulatedHardwareProfile] = None
        # ... (keep existing init logic for config path)
        self._load_profile()

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

        # 壓力定義：CPU > 80% 或 MEM > 90%
        return cpu > 80 or mem > 90

    def get_throttling_factor(self) -> float:
        """獲取節流因子 (0.0 - 1.0)"""
        if not self.is_system_stressed():
            return 1.0

        # 如果壓力大，返回更小的縮放因子
        return 0.5


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
            logger.warning(
                f"  Disk Warning Threshold (%): {disk_conf.warning_threshold_percent}"
            )
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
        and service_non_existent.profile.profile_name
        == "SafeDefaultProfile_ErrorLoading"
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
