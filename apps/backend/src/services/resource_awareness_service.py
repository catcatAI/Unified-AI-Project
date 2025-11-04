"Service to provide information about the AI's simulated hardware resources.\nLoads configuration from a YAML file and makes it accessible to other modules. (SKELETON)\n"
import os
import yaml # type: ignore
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

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
        self.profile: Optional[SimulatedHardwareProfile] = None
        self._config_path: str

        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))

        if config_filepath is None:
            self._config_path = os.path.join(project_root, DEFAULT_CONFIG_PATH)
        else:
            if os.path.isabs(config_filepath):
                self._config_path = config_filepath
            else:
                self._config_path = os.path.join(project_root, config_filepath)

        self._load_profile()
        if self.profile:
            print(f"ResourceAwarenessService initialized. Loaded profile: '{self.profile.profile_name}' from '{self._config_path}'")
        else:
            print(f"ResourceAwarenessService initialized, but FAILED to load a profile from '{self._config_path}'. Using no profile (None).")

    def _load_profile(self) -> None:
        try:
            if not os.path.exists(self._config_path):
                print(f"ResourceAwarenessService: Error - Config file not found at {self._config_path}")
                self.profile = self._get_safe_default_profile()
                return

            with open(self._config_path, 'r', encoding='utf-8') as f:
                config_data_root = yaml.safe_load(f)

            if not isinstance(config_data_root, dict):
                print(f"ResourceAwarenessService: Error - Config file {self._config_path} does not contain a root dictionary.")
                self.profile = self._get_safe_default_profile()
                return

            profile_data = config_data_root.get('simulated_hardware_profile')
            if not isinstance(profile_data, dict):
                print(f"ResourceAwarenessService: Error - 'simulated_hardware_profile' key missing or not a dict in {self._config_path}.")
                self.profile = self._get_safe_default_profile()
                return

            # In a real implementation, use Pydantic for robust parsing and validation
            self.profile = SimulatedHardwareProfile(**profile_data)

        except Exception as e:
            print(f"ResourceAwarenessService: An unexpected error occurred loading profile from {self._config_path}: {e}")
            self.profile = self._get_safe_default_profile()

    def _get_safe_default_profile(self) -> SimulatedHardwareProfile:
        print("ResourceAwarenessService: WARNING - Using a minimal safe default hardware profile.")
        return SimulatedHardwareProfile(
            profile_name="SafeDefaultProfile_ErrorLoading",
            disk=SimulatedDiskConfig(),
            cpu=SimulatedCPUConfig(),
            ram=SimulatedRAMConfig(),
            gpu_available=False
        )

    def get_simulated_hardware_profile(self) -> Optional[SimulatedHardwareProfile]:
        return self.profile

    def get_simulated_disk_config(self) -> Optional[SimulatedDiskConfig]:
        if self.profile:
            return self.profile.disk
        return None

    def get_simulated_cpu_config(self) -> Optional[SimulatedCPUConfig]:
        if self.profile:
            return self.profile.cpu
        return None

    def get_simulated_ram_config(self) -> Optional[SimulatedRAMConfig]:
        if self.profile:
            return self.profile.ram
        return None

if __name__ == '__main__':
    print("--- ResourceAwarenessService Standalone Test ---")

    # Test with default path (requires configs/simulated_resources.yaml to exist)
    print("\n1. Testing with default config path:")
    service_default = ResourceAwarenessService()
    if service_default.profile:
        print(f"  Profile Name: {service_default.profile.profile_name}")
        disk_conf = service_default.get_simulated_disk_config()
        if disk_conf:
            print(f"  Disk Space (GB): {disk_conf.space_gb}")
            print(f"  Disk Warning Threshold (%): {disk_conf.warning_threshold_percent}")
        else:
            print("  No disk config found in default profile.")
    else:
        print("  Failed to load default profile.")

    # Test with a non-existent config file path
    print("\n2. Testing with non-existent config file:")
    service_non_existent = ResourceAwarenessService(config_filepath="configs/non_existent_resources.yaml")
    if service_non_existent.profile and service_non_existent.profile.profile_name == "SafeDefaultProfile_ErrorLoading":
        print(f"  Correctly fell back to safe default: {service_non_existent.profile.profile_name}")
        print(f"  Default Disk Space (GB): {service_non_existent.get_simulated_disk_config().space_gb if service_non_existent.get_simulated_disk_config() else 'N/A'}")
    else:
        print(f"  Test failed or profile was unexpectedly loaded: {service_non_existent.profile}")

    # Test with a malformed YAML file (requires creating one temporarily)
    print("\n3. Testing with malformed YAML config file:")
    malformed_yaml_path = "configs/temp_malformed_resources.yaml"
    with open(malformed_yaml_path, "w", encoding="utf-8") as f:
        f.write("simulated_hardware_profile: \n  disk: [this is not a dict]\n  profile_name: MalformedProfile") # Intentional malformed YAML

    service_malformed = ResourceAwarenessService(config_filepath=malformed_yaml_path)
    if service_malformed.profile and service_malformed.profile.profile_name == "SafeDefaultProfile_ErrorLoading":
        print(f"  Correctly fell back to safe default for malformed YAML: {service_malformed.profile.profile_name}")
    else:
        print(f"  Test failed for malformed YAML or profile was unexpectedly loaded: {service_malformed.profile}")

    if os.path.exists(malformed_yaml_path):
        os.remove(malformed_yaml_path)

    print("\nResourceAwarenessService standalone test finished.")
    print("ResourceAwarenessService module loaded.")
