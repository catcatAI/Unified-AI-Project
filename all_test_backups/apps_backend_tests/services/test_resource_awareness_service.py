# tests/services/test_resource_awareness_service.py
import unittest
import pytest
import yaml
from pathlib import Path

from apps.backend.src.core.services.resource_awareness_service import ResourceAwarenessService, DEFAULT_CONFIG_PATH
SimulatedCPUConfig,
SimulatedRAMConfig,
)

# Determine project root for test file paths
TEST_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEST_CONFIGS_DIR = TEST_PROJECT_ROOT / "tests" / "test_data" / "resource_awareness_configs"


class TestResourceAwarenessService(unittest.TestCase):

    def setUp(self):
        # Ensure test config directory exists
TEST_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
self.valid_config_path = TEST_CONFIGS_DIR / "valid_simulated_resources.yaml"
self.malformed_config_path = TEST_CONFIGS_DIR / "malformed_simulated_resources.yaml"
self.incomplete_config_path = TEST_CONFIGS_DIR / "incomplete_simulated_resources.yaml"
self.non_existent_config_path = TEST_CONFIGS_DIR / "i_do_not_exist.yaml"

        # Create a valid config file for testing
self.sample_profile_data: SimulatedHardwareProfile = { # type: ignore
"profile_name": "TestProfile_Valid",
"disk": {
"space_gb": 20.0,
"warning_threshold_percent": 75,
"critical_threshold_percent": 90,
"lag_factor_warning": 1.2,
"lag_factor_critical": 2.5
},
"cpu": {"cores": 4},
"ram": {"ram_gb": 8.0},
"gpu_available": True
}
        with open(self.valid_config_path, 'w', encoding='utf-8') as f:
yaml.dump({"simulated_hardware_profile": self.sample_profile_data}, f)

        # Create a malformed YAML file
        with open(self.malformed_config_path, 'w', encoding='utf-8') as f:
f.write("simulated_hardware_profile: \n  disk: [this is not a dict]\n  profile_name: Malformed")

        # Create an incomplete (structurally valid YAML, but missing required keys)
        with open(self.incomplete_config_path, 'w', encoding='utf-8') as f:
yaml.dump({"simulated_hardware_profile": {"profile_name": "Incomplete"}}, f)


    def tearDown(self):
        # Clean up created test files
        if self.valid_config_path.exists():
self.valid_config_path.unlink()
        if self.malformed_config_path.exists():
self.malformed_config_path.unlink()
        if self.incomplete_config_path.exists():
self.incomplete_config_path.unlink()
        # Attempt to remove the directory if it's empty (optional)
        try:
            if TEST_CONFIGS_DIR.exists() and not any(TEST_CONFIGS_DIR.iterdir()):
TEST_CONFIGS_DIR.rmdir()
        except OSError:
            pass # Ignore if dir removal fails (e.g. other test files present)

    @pytest.mark.timeout(15)
    def test_load_valid_config(self) -> None:
service = ResourceAwarenessService(config_filepath=str(self.valid_config_path))
self.assertIsNotNone(service.profile)
self.assertEqual(service.profile.get("profile_name"), "TestProfile_Valid")

disk_config = service.get_simulated_disk_config()
self.assertIsNotNone(disk_config)
self.assertEqual(disk_config.get("space_gb"), 20.0)
self.assertEqual(disk_config.get("lag_factor_critical"), 2.5)

cpu_config = service.get_simulated_cpu_config()
self.assertIsNotNone(cpu_config)
self.assertEqual(cpu_config.get("cores"), 4)

ram_config = service.get_simulated_ram_config()
self.assertIsNotNone(ram_config)
self.assertEqual(ram_config.get("ram_gb"), 8.0)

self.assertTrue(service.profile.get("gpu_available"))

    @pytest.mark.timeout(15)
    def test_load_non_existent_config_falls_back_to_default(self) -> None:
        # Ensure the default path doesn't accidentally exist from other tests or real config
        # For a truly isolated test of non-existent, we use a unique path.
        # The service's default path logic will try to find DEFAULT_CONFIG_PATH relative to project root.
        # If that default file exists, this test might not reflect a true "file not found" for *that* path.
        # However, the constructor is passed a specific non-existent path here.

service = ResourceAwarenessService(config_filepath=str(self.non_existent_config_path))
self.assertIsNotNone(service.profile)
self.assertEqual(service.profile.get("profile_name"), "SafeDefaultProfile_ErrorLoading")
disk_config = service.get_simulated_disk_config()
self.assertIsNotNone(disk_config)
self.assertEqual(disk_config.get("space_gb"), 1.0) # Check against safe default value

    @pytest.mark.timeout(15)
    def test_load_malformed_yaml_falls_back_to_default(self) -> None:
service = ResourceAwarenessService(config_filepath=str(self.malformed_config_path))
self.assertIsNotNone(service.profile)
self.assertEqual(service.profile.get("profile_name"), "SafeDefaultProfile_ErrorLoading")

    @pytest.mark.timeout(15)
    def test_load_incomplete_yaml_falls_back_to_default(self) -> None:
        # Tests if the profile data is missing required keys after YAML parsing.
service = ResourceAwarenessService(config_filepath=str(self.incomplete_config_path))
self.assertIsNotNone(service.profile)
self.assertEqual(service.profile.get("profile_name"), "SafeDefaultProfile_ErrorLoading",
f"Profile loaded: {service.profile}")


    @pytest.mark.timeout(15)
    def test_default_config_path_loading_if_file_exists(self) -> None:
        # This test depends on whether the actual default config file exists and is valid.
        # For controlled testing, we can create a dummy default file.

        # Path relative to project root for DEFAULT_CONFIG_PATH
        default_path_abs = TEST_PROJECT_ROOT / DEFAULT_CONFIG_PATH
        default_path_abs.parent.mkdir(parents=True, exist_ok=True) # Ensure dir exists

original_content = None
        if default_path_abs.exists():
            with open(default_path_abs, 'r') as f_orig:
original_content = f_orig.read()

temp_default_profile_data = {
"profile_name": "TemporaryDefaultTestProfile",
"disk": {"space_gb": 5.0, "warning_threshold_percent": 50, "critical_threshold_percent": 70, "lag_factor_warning": 1.0, "lag_factor_critical": 1.0},
"cpu": {"cores": 1},
"ram": {"ram_gb": 2.0},
"gpu_available": False
}
        with open(default_path_abs, 'w', encoding='utf-8') as f:
yaml.dump({"simulated_hardware_profile": temp_default_profile_data}, f)

service = ResourceAwarenessService() # Initialize with no path, should use default
self.assertIsNotNone(service.profile)
self.assertEqual(service.profile.get("profile_name"), "TemporaryDefaultTestProfile")

        # Clean up / restore
        if original_content is not None:
            with open(default_path_abs, 'w') as f_orig_write:
f_orig_write.write(original_content)
        else:
            if default_path_abs.exists():
                default_path_abs.unlink()

if __name__ == '__main__':
unittest.main()