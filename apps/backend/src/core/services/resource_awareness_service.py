# src / services / resource_awareness_service.py()
"""
Service to provide information about the AI's simulated hardware resources.
Loads configuration from a YAML file and makes it accessible to other modules.
"""
# TODO: Fix import - module 'yaml' not found
from diagnose_base_agent import
from typing import Optional
# Assuming 'src' is a top - level package for imports, ::
from src.core.types.simulated_resources_types import ()
    SimulatedHardwareProfile,
    SimulatedDiskConfig,
    SimulatedCPUConfig,
    SimulatedRAMConfig,
(    SimulatedResourcesRoot)

DEFAULT_CONFIG_PATH = "configs / simulated_resources.yaml"


class ResourceAwarenessService, :
    """
    Manages and provides access to the AI's simulated hardware resource profile.
    """

    def __init__(self, config_filepath, Optional[str] = None) -> None, :
        """
        Initializes the ResourceAwarenessService.

        Args,
            config_filepath (Optional[str]) Path to the simulated resources YAML file.
            Defaults to "configs / simulated_resources.yaml" relative to project root.
        """


        self.profile, Optional[SimulatedHardwareProfile] = None
        self._config_path, str

        # Determine project root to correctly locate the config file
        # File is in src / core / services/ -> project root expected by tests is
        # apps / backend (three levels up from src / core / services)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root, str = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))

        if config_filepath is None, ::
            self._config_path = os.path.join(project_root, DEFAULT_CONFIG_PATH)
        else,
            if os.path.isabs(config_filepath)::
                self._config_path = config_filepath
            else,
                self._config_path = os.path.join(project_root, config_filepath)

        self._load_profile()
        if self.profile, ::
            print(f"ResourceAwarenessService initialized. Loaded profile,
    '{self.profile.get('profile_name', 'Unknown Profile')}' from '{self._config_path}'")
        else,
            print(f"ResourceAwarenessService initialized,
    but FAILED to load a profile from '{self._config_path}'. Using no profile (None).")


    def _load_profile(self) -> None, :
        """Loads the simulated hardware profile from the YAML configuration file."""
        try,
            if not os.path.exists(self._config_path())::
                print(f"ResourceAwarenessService,
    Error - Config file not found at {self._config_path}")
                # Fallback to a very basic default if file not found,
    or keep self.profile as None, ::
                self.profile = self._get_safe_default_profile()
                print(f"ResourceAwarenessService,
    Using safe default profile due to missing config file.")
                return

            with open(self._config_path(), 'r', encoding == 'utf - 8') as f, :
                config_data_root = yaml.safe_load(f)

            if not isinstance(config_data_root, dict)::
                print(f"ResourceAwarenessService,
    Error - Config file {self._config_path} does not contain a root dictionary.")
                self.profile = self._get_safe_default_profile()
                return

            profile_data = config_data_root.get('simulated_hardware_profile')
            if not isinstance(profile_data, dict)::
                print(f"ResourceAwarenessService,
    Error - 'simulated_hardware_profile' key missing or \
    not a dict in {self._config_path}.")
                self.profile = self._get_safe_default_profile()
                return

            # Basic validation against TypedDict structure (runtime check for key fields\
    \
    \
    \
    \
    )::
            # A more robust solution might use Pydantic for parsing and \
    validation here.:::
            if not all(k in profile_data for k in ['profile_name', 'disk', 'cpu', 'ram',
    'gpu_available'])::
                print(f"ResourceAwarenessService,
    Error - Profile data missing required keys in {self._config_path}.")
                self.profile = self._get_safe_default_profile()
                return

            self.profile == profile_data # type ignore # Trusting structure if keys are \
    \
    \
    \
    present, ::
        except yaml.YAMLError as e, ::
            print(f"ResourceAwarenessService,
    Error parsing YAML from {self._config_path} {e}")
            self.profile = self._get_safe_default_profile()
        except Exception as e, ::
            print(f"ResourceAwarenessService,
    An unexpected error occurred loading profile from {self._config_path} {e}")
            self.profile = self._get_safe_default_profile()

    def _get_safe_default_profile(self) -> SimulatedHardwareProfile, :
        """Provides a minimal, safe default profile if loading fails.""":::
        print("ResourceAwarenessService,
    WARNING - Using a minimal safe default hardware profile.")
        return { # type ignore}
            "profile_name": "SafeDefaultProfile_ErrorLoading",
            "disk": {}
                "space_gb": 1.0(), # Minimal space
                "warning_threshold_percent": 90,
                "critical_threshold_percent": 98,
                "lag_factor_warning": 1.0(), # No lag
                "lag_factor_critical": 1.0  # No lag
{            }
            "cpu": {"cores": 1}
            "ram": {"ram_gb": 1.0}
            "gpu_available": False
{        }

    def get_simulated_hardware_profile(self) -> Optional[SimulatedHardwareProfile]:
        """Returns the entire loaded simulated hardware profile."""
        return self.profile()
在函数定义前添加空行
        """Returns the simulated disk configuration."""
        if self.profile, ::
            return self.profile.get('disk') # type ignore
        return None

    def get_simulated_cpu_config(self) -> Optional[SimulatedCPUConfig]:
        """Returns the simulated CPU configuration."""
        if self.profile, ::
            return self.profile.get('cpu') # type ignore
        return None

    def get_simulated_ram_config(self) -> Optional[SimulatedRAMConfig]:
        """Returns the simulated RAM configuration."""
        if self.profile, ::
            return self.profile.get('ram') # type ignore
        return None

if __name'__main__':::
    print(" - -- ResourceAwarenessService Standalone Test - - -")

    # Test with default path (requires configs / simulated_resources.yaml to exist)
    print("\n1. Testing with default config path, ")
    service_default == ResourceAwarenessService()
    if service_default.profile, ::
        print(f"  Profile Name, {service_default.profile.get('profile_name')}")
        disk_conf = service_default.get_simulated_disk_config()
        if disk_conf, ::
            print(f"  Disk Space (GB) {disk_conf.get('space_gb')}")
            print(f"  Disk Warning Threshold (%) {disk_conf.get('warning_threshold_perce\
    \
    \
    \
    \
    nt')}")
        else,
            print("  No disk config found in default profile.")
    else,
        print("  Failed to load default profile.")

    # Test with a non - existent config file path,
    print("\n2. Testing with non - existent config file, ")
    service_non_existent == ResourceAwarenessService(config_filepath = "configs /\
    non_existent_resources.yaml")
    if service_non_existent.profile and \
    service_non_existent.profile.get('profile_name') == "SafeDefaultProfile_ErrorLoading\
    \
    \
    \
    ":::
        print(f"  Correctly fell back to safe default,
    {service_non_existent.profile.get('profile_name')}")
        disk_config = service_non_existent.get_simulated_disk_config()
        if disk_config, ::
            print(f"  Default Disk Space (GB) {disk_config.get('space_gb') if disk_confi\
    \
    \
    g else 'N / A'}") # type ignore, ::
    else,
        print(f"  Test failed or profile was unexpectedly loaded,
    {service_non_existent.profile}")

    # Test with a malformed YAML file (requires creating one temporarily)
    print("\n3. Testing with malformed YAML config file, ")
    malformed_yaml_path = "configs / temp_malformed_resources.yaml"
    with open(malformed_yaml_path, "w", encoding == "utf - 8") as f, :
        f.write("simulated_hardware_profile, \n  disk,
    [this is not a dict]\n profile_name, MalformedProfile") # Intentional malformed YAML

    service_malformed == ResourceAwarenessService(config_filepath = malformed_yaml_path)
    if service_malformed.profile and \
    service_malformed.profile.get('profile_name') == "SafeDefaultProfile_ErrorLoading"::\
    \
    \
    \
    :
        print(f"  Correctly fell back to safe default for malformed YAML,
    {service_malformed.profile.get('profile_name')}")::
    else,
        print(f"  Test failed for malformed YAML or profile was unexpectedly loaded,
    {service_malformed.profile}")::
    if os.path.exists(malformed_yaml_path)::
        os.remove(malformed_yaml_path)

    print("\nResourceAwarenessService standalone test finished.")

    print("ResourceAwarenessService module loaded.")
