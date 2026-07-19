"""
Hardware Profile — 硬體場景頻率設定檔 (§8.6 #5)

Defines 5 hardware scenarios with baseline frequency tables.
Provides auto-detection and runtime overrides.

Reference: docs/06-project-management/CAUSAL_CHAIN_COMPLETENESS.md §8.7

Typical usage:
    profile = HardwareProfile()
    ans_interval = profile.get("ans_update", 0.5)
    hb_interval = profile.apply_multiplier(10.0)
"""

# =============================================================================
# ANGELA-MATRIX: [L2] [β] [C] [L1]
# =============================================================================

from __future__ import annotations

import logging
import os
import platform
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class HardwareScenario(Enum):
    """5 種硬體場景 / Hardware scenarios (§8.7)"""

    HIGH_PERFORMANCE_DESKTOP = "high_performance_desktop"
    LAPTOP_NORMAL = "laptop_normal"
    LAPTOP_POWER_SAVER = "laptop_power_saver"
    LOW_POWER_DEVICE = "low_power_device"
    SERVER_CLOUD = "server_cloud"


@dataclass
class FrequencyProfile:
    """頻率設定檔 — 每個循環的建議間隔（秒）"""

    # === Core loops ===
    ans_update: float = 0.5
    heartbeat_min: float = 5.0
    heartbeat_max: float = 30.0
    decision_interval: float = 60.0
    neuroplasticity_update: float = 60.0
    lifecycle_check: float = 10.0
    proactive_check: float = 15.0

    # === Agent / Polling ===
    agent_poll: float = 0.5
    agent_cleanup: float = 30.0
    scan_desktop: float = 30.0

    # === Bio / Endocrine ===
    endocrine_update: float = 5.0
    bio_monitor: float = 5.0
    emotion_update: float = 1.0
    execution_check: float = 1.0

    # === Low-priority background ===
    ham_sync: float = 3600.0
    narrative_update: float = 86400.0
    cml_auto_train: float = 60.0

    # === High-frequency (hardware-limited) ===
    action_executor: float = 0.05
    audio_poll: float = 0.1
    tactile_update: float = 0.1
    transport_poll: float = 0.1

    # Base frequency multiplier (1.0 = standard desktop)
    base_multiplier: float = 1.0


# ---------------------------------------------------------------------------
# Predefined profiles — each scenario gets its own frequency table
# Values based on §8.4 "不同硬體的合理值" table
# ---------------------------------------------------------------------------
PROFILES: Dict[HardwareScenario, FrequencyProfile] = {
    HardwareScenario.HIGH_PERFORMANCE_DESKTOP: FrequencyProfile(
        ans_update=0.5,
        heartbeat_min=5.0,
        heartbeat_max=30.0,
        decision_interval=60.0,
        neuroplasticity_update=60.0,
        lifecycle_check=10.0,
        proactive_check=15.0,
        agent_poll=0.5,
        agent_cleanup=30.0,
        scan_desktop=30.0,
        endocrine_update=5.0,
        bio_monitor=5.0,
        emotion_update=1.0,
        execution_check=1.0,
        ham_sync=3600.0,
        narrative_update=86400.0,
        cml_auto_train=60.0,
        action_executor=0.05,
        audio_poll=0.1,
        tactile_update=0.1,
        transport_poll=0.1,
        base_multiplier=1.0,
    ),
    HardwareScenario.LAPTOP_NORMAL: FrequencyProfile(
        ans_update=1.0,
        heartbeat_min=10.0,
        heartbeat_max=60.0,
        decision_interval=120.0,
        neuroplasticity_update=120.0,
        lifecycle_check=20.0,
        proactive_check=30.0,
        agent_poll=1.0,
        agent_cleanup=60.0,
        scan_desktop=60.0,
        endocrine_update=10.0,
        bio_monitor=10.0,
        emotion_update=2.0,
        execution_check=2.0,
        ham_sync=3600.0,
        narrative_update=86400.0,
        cml_auto_train=120.0,
        action_executor=0.1,
        audio_poll=0.2,
        tactile_update=0.2,
        transport_poll=0.2,
        base_multiplier=0.7,
    ),
    HardwareScenario.LAPTOP_POWER_SAVER: FrequencyProfile(
        ans_update=2.0,
        heartbeat_min=30.0,
        heartbeat_max=120.0,
        decision_interval=300.0,
        neuroplasticity_update=300.0,
        lifecycle_check=30.0,
        proactive_check=60.0,
        agent_poll=2.0,
        agent_cleanup=120.0,
        scan_desktop=120.0,
        endocrine_update=15.0,
        bio_monitor=15.0,
        emotion_update=5.0,
        execution_check=5.0,
        ham_sync=7200.0,
        narrative_update=86400.0,
        cml_auto_train=300.0,
        action_executor=0.2,
        audio_poll=0.5,
        tactile_update=0.5,
        transport_poll=0.5,
        base_multiplier=0.5,
    ),
    HardwareScenario.LOW_POWER_DEVICE: FrequencyProfile(
        ans_update=5.0,
        heartbeat_min=60.0,
        heartbeat_max=300.0,
        decision_interval=600.0,
        neuroplasticity_update=600.0,
        lifecycle_check=60.0,
        proactive_check=120.0,
        agent_poll=5.0,
        agent_cleanup=300.0,
        scan_desktop=120.0,
        endocrine_update=30.0,
        bio_monitor=30.0,
        emotion_update=10.0,
        execution_check=10.0,
        ham_sync=14400.0,
        narrative_update=172800.0,
        cml_auto_train=600.0,
        action_executor=0.5,
        audio_poll=1.0,
        tactile_update=1.0,
        transport_poll=1.0,
        base_multiplier=0.3,
    ),
    HardwareScenario.SERVER_CLOUD: FrequencyProfile(
        ans_update=0.2,
        heartbeat_min=1.0,
        heartbeat_max=10.0,
        decision_interval=30.0,
        neuroplasticity_update=30.0,
        lifecycle_check=5.0,
        proactive_check=10.0,
        agent_poll=0.2,
        agent_cleanup=15.0,
        scan_desktop=15.0,
        endocrine_update=2.0,
        bio_monitor=2.0,
        emotion_update=0.5,
        execution_check=0.5,
        ham_sync=1800.0,
        narrative_update=43200.0,
        cml_auto_train=30.0,
        action_executor=0.02,
        audio_poll=0.05,
        tactile_update=0.05,
        transport_poll=0.05,
        base_multiplier=2.0,
    ),
}


class HardwareProfile:
    """硬體設定檔管理器 — 自動偵測環境 + 提供頻率建議

    Detects the runtime hardware environment and provides baseline
    frequency recommendations for all system loops.

    Usage:
        >>> profile = HardwareProfile()
        >>> profile.scenario
        <HardwareScenario.HIGH_PERFORMANCE_DESKTOP: 'high_performance_desktop'>
        >>> profile.get("ans_update", 0.5)
        0.5
        >>> profile.apply_multiplier(10.0)
        10.0
    """

    def __init__(self, scenario: Optional[HardwareScenario] = None) -> None:
        """Initialize with optional explicit scenario override.

        Args:
            scenario: If set, skip auto-detection and use this scenario.
                      Useful for tests and explicit config.
        """
        if scenario is not None:
            self._scenario = scenario
        else:
            self._scenario = self._detect_scenario()
        self._profile = PROFILES[self._scenario]
        self._overrides: Dict[str, float] = {}

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_scenario() -> HardwareScenario:
        """Auto-detect hardware scenario from runtime environment.

        Detection priority:
        1. ANGELA_HARDWARE_PROFILE env var (explicit override)
        2. CI environment → LOW_POWER_DEVICE
        3. Headless Linux → SERVER_CLOUD
        4. ARM Linux → LOW_POWER_DEVICE
        5. Battery discharging (laptop) → power mode
        6. Default → HIGH_PERFORMANCE_DESKTOP
        """
        # 1. Env override
        env_override = os.environ.get("ANGELA_HARDWARE_PROFILE")
        if env_override:
            try:
                detected = HardwareScenario(env_override)
                logger.info("HardwareProfile: using env override: %s", detected.value)
                return detected
            except ValueError:
                logger.warning("HardwareProfile: unknown env value: %s", env_override)

        system = platform.system()
        machine = platform.machine()

        # 2. CI
        if os.environ.get("CI") == "true":
            logger.info("HardwareProfile: CI detected → LOW_POWER_DEVICE")
            return HardwareScenario.LOW_POWER_DEVICE

        # 3. Headless Linux (no display, no SSH) → likely cloud server
        has_display = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
        is_ssh = "SSH_CLIENT" in os.environ or "SSH_TTY" in os.environ
        if system == "Linux" and not has_display and not is_ssh:
            logger.info("HardwareProfile: headless Linux → SERVER_CLOUD")
            return HardwareScenario.SERVER_CLOUD

        # 4. ARM Linux → RPi / low-power
        if system == "Linux" and machine in ("armv7l", "aarch64"):
            logger.info("HardwareProfile: ARM Linux → LOW_POWER_DEVICE")
            return HardwareScenario.LOW_POWER_DEVICE

        # 5. Laptop battery check
        if system in ("Windows", "Darwin"):
            battery_status = _check_battery(system)
            if battery_status == "power_saver":
                logger.info("HardwareProfile: battery discharging <30% → LAPTOP_POWER_SAVER")
                return HardwareScenario.LAPTOP_POWER_SAVER
            if battery_status == "laptop":
                logger.info("HardwareProfile: battery discharging → LAPTOP_NORMAL")
                return HardwareScenario.LAPTOP_NORMAL

        # 6. Default
        logger.info("HardwareProfile: default → HIGH_PERFORMANCE_DESKTOP")
        return HardwareScenario.HIGH_PERFORMANCE_DESKTOP

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def scenario(self) -> HardwareScenario:
        """Currently active hardware scenario."""
        return self._scenario

    @property
    def profile(self) -> FrequencyProfile:
        """Currently active frequency profile."""
        return self._profile

    def get(self, key: str, default: float) -> float:
        """Get recommended interval for a loop key.

        Args:
            key: Attribute name on FrequencyProfile (e.g. "ans_update").
            default: Fallback if key not found.

        Returns:
            Recommended interval in seconds.
        """
        if key in self._overrides:
            return self._overrides[key]
        return getattr(self._profile, key, default)

    def set_override(self, key: str, value: float) -> None:
        """Override a specific key at runtime.

        Args:
            key: Attribute name to override.
            value: New interval in seconds.
        """
        self._overrides[key] = value

    def clear_overrides(self) -> None:
        """Remove all runtime overrides."""
        self._overrides.clear()

    def apply_multiplier(self, base_value: float) -> float:
        """Apply the scenario's base frequency multiplier.

        Lower-power scenarios have lower multipliers (e.g. 0.3),
        meaning loops should run LESS frequently.
        High-performance scenarios have higher multipliers (e.g. 2.0),
        meaning loops can run MORE frequently.

        Args:
            base_value: The standard (desktop) interval.

        Returns:
            Scaled interval: base_value * (1 / multiplier).
        """
        if self._profile.base_multiplier <= 0:
            return base_value
        return base_value * (1.0 / self._profile.base_multiplier)

    def get_summary(self) -> Dict[str, object]:
        """Get human-readable summary dict."""
        return {
            "scenario": self._scenario.value,
            "base_multiplier": self._profile.base_multiplier,
            "ans_update": self._profile.ans_update,
            "heartbeat_min": self._profile.heartbeat_min,
            "heartbeat_max": self._profile.heartbeat_max,
            "decision_interval": self._profile.decision_interval,
            "neuroplasticity_update": self._profile.neuroplasticity_update,
            "override_count": len(self._overrides),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check_battery(system: str) -> Optional[str]:
    """Check battery status and return a hint string.

    Returns:
        "power_saver" — battery discharging below 30%
        "laptop"      — battery discharging above 30%
        None          — plugged in or unknown
    """
    try:
        if system == "Darwin":
            import subprocess  # noqa: S404 — intentional os-level check

            result = subprocess.run(
                ["pmset", "-g", "batt"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if "discharging" in result.stdout:
                for line in result.stdout.splitlines():
                    if "%" in line:
                        match = re.search(r"(\d+)%", line)
                        if match and int(match.group(1)) < 30:
                            return "power_saver"
                        return "laptop"
        elif system == "Windows":
            import psutil  # noqa: S404 — intentional os-level check

            battery = psutil.sensors_battery()
            if battery is not None and not battery.power_plugged:
                if battery.percent < 30:
                    return "power_saver"
                return "laptop"
    except Exception:  # noqa: S110 — broad except intentional; battery check is best-effort
        logger.debug("Battery detection failed (non-critical)")
    return None
