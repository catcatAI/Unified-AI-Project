"""Regression tests for hardware detector convergence (2026-09-03).

Covers the two recent fixes without depending on the local machine:
- `core.hardware.hal.HardwareManager` keeps stub keys and enriches spec via backbone
- `shared.utils.hardware_detector.SystemHardwareProbe` Intel Arc branch (mocked)
- shared probe structural invariants (portable across machines)
"""

from unittest.mock import patch

from core.hardware.hal import HardwareManager, detect_hardware


class TestHalManager:
    def test_stub_keys_always_present(self):
        profile = HardwareManager().get_hardware_profile()
        assert "architecture" in profile
        assert "capabilities" in profile
        assert "max_memory_mb" in profile["capabilities"]
        assert "compute_units" in profile["capabilities"]

    def test_tier_in_known_set_when_enriched(self):
        profile = HardwareManager().get_hardware_profile()
        if "tier" in profile:
            assert profile["tier"] in {
                "high_performance_desktop",
                "high_performance_gpu",
                "desktop_igpu",
                "laptop_normal",
                "laptop_power_saver",
                "low_power_device",
                "server_cloud",
            }

    def test_top_level_helper(self):
        profile = detect_hardware()
        assert "architecture" in profile


class TestSharedProbe:
    def test_detect_structure_portable(self):
        from shared.utils.hardware_detector import SystemHardwareProbe

        profile = SystemHardwareProbe().detect()
        assert profile.performance_tier in {"Low", "Medium", "High", "Extreme"}
        assert profile.vram_mb >= 0
        assert profile.cpu_cores_logical >= 1
        assert 0.0 <= profile.ai_capability_score <= 100.0

    def test_arc_branch_mocked(self):
        import subprocess

        from shared.utils.hardware_detector import AcceleratorType, SystemHardwareProbe

        def fake_run(cmd, **kwargs):
            if cmd[0] in ("nvidia-smi", "rocm-smi"):
                raise FileNotFoundError(cmd[0])
            if cmd[0] == "lspci":
                out = "03:00.0 VGA compatible controller [0300]: Intel Corporation Device [8086:e20c]"
                return subprocess.CompletedProcess(cmd, 0, out, "")
            if cmd[0] == "glxinfo":
                out = "OpenGL renderer string: Mesa Intel(R) Arc(tm) B570 Graphics (BMG G21)\nVideo memory: 10172MB\n"
                return subprocess.CompletedProcess(cmd, 0, out, "")
            raise AssertionError(f"unexpected command: {cmd}")

        probe = SystemHardwareProbe()
        probe.platform_name = "linux"
        with patch("subprocess.run", side_effect=fake_run):
            atype, name, vram = probe._detect_gpu()
        assert atype == AcceleratorType.INTEL
        assert "B570" in name
        assert vram == 10172

    def test_get_profile_helper(self):
        from shared.utils.hardware_detector import get_profile

        profile = get_profile()
        assert profile.performance_tier in {"Low", "Medium", "High", "Extreme"}


class TestModeRecommender:
    def test_get_cluster_capability(self):
        """Regression: used self.detect() (AttributeError); must use detector."""
        from shared.utils.hardware_detector import ModeRecommender

        result = ModeRecommender(config={}).get_cluster_capability()
        assert result["preferred_role"] in {"master", "worker"}
        assert isinstance(result["can_participate"], bool)
        assert result["max_tasks"] >= 1

    def test_get_hardware_profile_shim(self):
        """Regression: shim used self.detect(); must delegate to detector."""
        from shared.utils.hardware_detector import HardwareProfile, ModeRecommender

        profile = ModeRecommender(config={}).get_hardware_profile()
        assert isinstance(profile, HardwareProfile)
        assert profile.performance_tier in {"Low", "Medium", "High", "Extreme"}
