"""
Tests for HardwareProfile — hardware scenario detection + frequency tables (§8.6 #5)
"""

# =============================================================================
# ANGELA-MATRIX: [L2] [β] [C] [L1]
# =============================================================================

import os
from unittest.mock import patch

import pytest

from apps.backend.src.core.system.config.hardware_profile import (
    PROFILES,
    FrequencyProfile,
    HardwareProfile,
    HardwareScenario,
)


class TestHardwareScenario:
    """Verify 5 scenarios exist with distinct profiles"""

    def test_all_scenarios_have_profiles(self) -> None:
        """All 5 scenarios must have a predefined profile."""
        assert len(PROFILES) == 5
        for scenario in HardwareScenario:
            assert scenario in PROFILES, f"Missing profile for {scenario}"

    def test_profiles_have_distinct_multipliers(self) -> None:
        """Each scenario should have a different base_multiplier to be useful."""
        multipliers = {p.base_multiplier for p in PROFILES.values()}
        assert len(multipliers) == 5, f"Expected 5 distinct multipliers, got {multipliers}"

    def test_multiplier_ordering(self) -> None:
        """High-performance should be fastest, low-power slowest."""
        assert PROFILES[HardwareScenario.SERVER_CLOUD].base_multiplier > \
               PROFILES[HardwareScenario.HIGH_PERFORMANCE_DESKTOP].base_multiplier > \
               PROFILES[HardwareScenario.LAPTOP_NORMAL].base_multiplier > \
               PROFILES[HardwareScenario.LAPTOP_POWER_SAVER].base_multiplier > \
               PROFILES[HardwareScenario.LOW_POWER_DEVICE].base_multiplier

    def test_all_keys_defined_in_all_profiles(self) -> None:
        """Every profile must define the same set of keys."""
        keys = set()
        for profile in PROFILES.values():
            keys = keys | set(profile.__dataclass_fields__.keys())
        # base_multiplier is the only non-interval field
        interval_keys = keys - {"base_multiplier"}
        for scenario, profile in PROFILES.items():
            for key in interval_keys:
                val = getattr(profile, key, None)
                assert val is not None, f"{scenario}: missing {key}"
                assert isinstance(val, (int, float)), f"{scenario}: {key} is not numeric"


class TestHardwareProfile:
    """Test HardwareProfile detection, access, and overrides"""

    def test_default_scenario(self) -> None:
        """Without env overrides, should detect and return a valid profile."""
        profile = HardwareProfile()
        assert profile.scenario in HardwareScenario
        assert profile.profile is not None

    def test_explicit_scenario(self) -> None:
        """Explicit scenario override should work."""
        profile = HardwareProfile(scenario=HardwareScenario.SERVER_CLOUD)
        assert profile.scenario == HardwareScenario.SERVER_CLOUD

    def test_get_returns_default(self) -> None:
        """get() should return default for unknown keys."""
        profile = HardwareProfile(scenario=HardwareScenario.HIGH_PERFORMANCE_DESKTOP)
        assert profile.get("nonexistent_key", 42.0) == 42.0

    def test_get_returns_profile_value(self) -> None:
        """get() should return profile value for known keys."""
        profile = HardwareProfile(scenario=HardwareScenario.SERVER_CLOUD)
        # Server cloud: ans_update = 0.2
        assert profile.get("ans_update", 0.5) == 0.2

    def test_override_takes_precedence(self) -> None:
        """Runtime override should take precedence over profile value."""
        profile = HardwareProfile(scenario=HardwareScenario.SERVER_CLOUD)
        profile.set_override("ans_update", 1.0)
        assert profile.get("ans_update", 0.5) == 1.0

    def test_clear_overrides(self) -> None:
        """clear_overrides() should restore profile values."""
        profile = HardwareProfile(scenario=HardwareScenario.SERVER_CLOUD)
        profile.set_override("ans_update", 99.0)
        profile.clear_overrides()
        assert profile.get("ans_update", 0.5) == 0.2  # back to profile default

    def test_apply_multiplier_high_perf(self) -> None:
        """High perf desktop has multiplier 1.0 → interval unchanged."""
        profile = HardwareProfile(scenario=HardwareScenario.HIGH_PERFORMANCE_DESKTOP)
        assert profile.apply_multiplier(10.0) == 10.0

    def test_apply_multiplier_server(self) -> None:
        """Server cloud has multiplier 2.0 → interval halved (faster)."""
        profile = HardwareProfile(scenario=HardwareScenario.SERVER_CLOUD)
        expected = 10.0 * (1.0 / 2.0)
        assert profile.apply_multiplier(10.0) == expected

    def test_apply_multiplier_power_saver(self) -> None:
        """Power saver has multiplier 0.5 → interval doubled (slower)."""
        profile = HardwareProfile(scenario=HardwareScenario.LAPTOP_POWER_SAVER)
        expected = 10.0 * (1.0 / 0.5)
        assert profile.apply_multiplier(10.0) == expected

    def test_get_summary(self) -> None:
        """get_summary() should return structured dict."""
        profile = HardwareProfile(scenario=HardwareScenario.LOW_POWER_DEVICE)
        summary = profile.get_summary()
        assert summary["scenario"] == "low_power_device"
        assert isinstance(summary["base_multiplier"], float)
        assert isinstance(summary["override_count"], int)

    @patch.dict(os.environ, {"ANGELA_HARDWARE_PROFILE": "server_cloud"}, clear=False)
    def test_env_override(self) -> None:
        """ANGELA_HARDWARE_PROFILE env var should force scenario."""
        profile = HardwareProfile()
        assert profile.scenario == HardwareScenario.SERVER_CLOUD

    @patch.dict(os.environ, {"CI": "true"}, clear=False)
    def test_ci_detection(self) -> None:
        """CI env should map to LOW_POWER_DEVICE."""
        profile = HardwareProfile()
        assert profile.scenario == HardwareScenario.LOW_POWER_DEVICE


class TestFrequencyProfile:
    """Verify FrequencyProfile dataclass integrity"""

    def test_all_fields_numeric(self) -> None:
        """All frequency fields should be numeric."""
        profile = FrequencyProfile()
        for field_name, field_type in profile.__dataclass_fields__.items():
            val = getattr(profile, field_name)
            assert isinstance(val, (int, float)), f"{field_name} is {type(val)}"

    def test_heartbeat_range_valid(self) -> None:
        """heartbeat_min must be <= heartbeat_max in all profiles."""
        for scenario, profile in PROFILES.items():
            assert profile.heartbeat_min <= profile.heartbeat_max, \
                f"{scenario}: min={profile.heartbeat_min} > max={profile.heartbeat_max}"

    def test_positive_intervals(self) -> None:
        """All interval fields must be > 0."""
        for scenario, profile in PROFILES.items():
            for field_name in profile.__dataclass_fields__:
                if field_name == "base_multiplier":
                    continue
                val = getattr(profile, field_name)
                assert val > 0, f"{scenario}.{field_name} = {val} (must be > 0)"


class TestGetSummary:
    """Verify get_summary structure"""

    def test_summary_keys(self) -> None:
        """get_summary() should contain all expected keys."""
        profile = HardwareProfile(scenario=HardwareScenario.HIGH_PERFORMANCE_DESKTOP)
        summary = profile.get_summary()
        expected = {"scenario", "base_multiplier", "ans_update", "heartbeat_min",
                     "heartbeat_max", "decision_interval", "neuroplasticity_update",
                     "override_count"}
        assert set(summary.keys()) >= expected
