"""
Angela AI v6.0 - Hormone Kinetics
激素动力学

Models hormone metabolism, receptor occupancy, receptor regulation,
and secretion patterns using biologically-inspired mathematical models.

Features:
- Half-life metabolism (exponential decay)
- Receptor occupancy (Hill equation)
- Receptor regulation (upregulation/downregulation)
- Secretion regulation (basal + pulsatile)

Author: Angela AI Development Team
Version: 6.0.0
"""

# =============================================================================
# ANGELA-MATRIX: L1[生物层] α [A] L2+
# =============================================================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, Any
import math

from .endocrine_types import HormoneType


@dataclass
class ReceptorStatus:
    """受体状态 / Receptor status"""

    receptor_type: str
    occupancy: float  # 占用率 (0-1)
    upregulation: float  # 上调因子
    downregulation: float  # 下调因子
    sensitivity: float  # 当前敏感度


class HormoneKinetics:
    """
    激素动力学 / Hormone Kinetics

    Models hormone metabolism, receptor occupancy, receptor regulation,
    and secretion patterns using biologically-inspired mathematical models.

    Features:
    - Half-life metabolism (exponential decay)
    - Receptor occupancy (Hill equation)
    - Receptor regulation (upregulation/downregulation)
    - Secretion regulation (basal + pulsatile)

    Example:
        >>> kinetics = HormoneKinetics()
        >>>
        >>> # Calculate hormone level after time with half-life
        >>> level = kinetics.metabolize(
        ...     initial_level=50.0,
        ...     half_life_hours=1.5,
        ...     time_hours=2.0
        ... )
        >>> print(f"Remaining: {level:.2f}")

        >>> # Calculate receptor occupancy using Hill equation
        >>> occupancy = kinetics.calculate_occupancy(
        ...     hormone_level=30.0,
        ...     kd=15.0,  # Dissociation constant
        ...     hill_coefficient=1.5
        ... )
        >>> print(f"Receptor occupancy: {occupancy:.2%}")
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize hormone kinetics model

        Args:
            config: Configuration dictionary with optional parameters
        """
        self.config = config or {}

        # Default half-lives for hormones (hours)
        self.half_lives: Dict[HormoneType, float] = {
            HormoneType.ADRENALINE: 0.1,  # 6 minutes
            HormoneType.CORTISOL: 1.5,  # 90 minutes
            HormoneType.DOPAMINE: 0.1,  # 6 minutes
            HormoneType.SEROTONIN: 1.0,  # 1 hour
            HormoneType.OXYTOCIN: 0.1,  # 6 minutes
            HormoneType.ENDORPHIN: 0.5,  # 30 minutes
            HormoneType.THYROXINE: 168.0,  # 7 days
            HormoneType.ESTROGEN_TESTOSTERONE: 24.0,  # 1 day
            HormoneType.GROWTH_HORMONE: 0.3,  # 18 minutes
            HormoneType.INSULIN: 0.1,  # 6 minutes
            HormoneType.MELATONIN: 0.5,  # 30 minutes
            HormoneType.NOREPINEPHRINE: 0.05,  # 3 minutes
        }

        # Override with config
        if "half_lives" in self.config:
            self.half_lives.update(self.config["half_lives"])

        # Receptor parameters
        self.default_kd: float = self.config.get("default_kd", 20.0)  # Dissociation constant
        self.default_hill: float = self.config.get("default_hill", 1.0)

        # Receptor regulation tracking
        self.receptor_status: Dict[HormoneType, ReceptorStatus] = {}
        self._initialize_receptors()

    def _initialize_receptors(self) -> None:
        """Initialize receptor status for all hormones"""
        for hormone_type in HormoneType:
            self.receptor_status[hormone_type] = ReceptorStatus(
                receptor_type=f"{hormone_type.en_name}_receptor",
                occupancy=0.0,
                upregulation=1.0,
                downregulation=1.0,
                sensitivity=1.0,
            )

    def metabolize(
        self,
        initial_level: float,
        hormone_type: HormoneType,
        time_hours: float,
        half_life: Optional[float] = None,
    ) -> float:
        """
        半衰期代谢 / Half-life metabolism (exponential decay)

        Formula: C(t) = C₀ * (1/2)^(t/t½)

        Args:
            initial_level: Initial hormone level
            hormone_type: Type of hormone
            time_hours: Time elapsed (hours)
            half_life: Optional custom half-life (uses default if not provided)

        Returns:
            Remaining hormone level after metabolism
        """
        t_half = half_life or self.half_lives.get(hormone_type, 1.0)

        # Exponential decay formula
        remaining = initial_level * (0.5 ** (time_hours / t_half))

        return remaining

    def calculate_metabolism_rate(
        self, current_level: float, hormone_type: HormoneType, half_life: Optional[float] = None
    ) -> float:
        """
        计算代谢速率 / Calculate metabolism rate

        Args:
            current_level: Current hormone level
            hormone_type: Type of hormone
            half_life: Optional custom half-life

        Returns:
            Metabolism rate (amount per hour)
        """
        t_half = half_life or self.half_lives.get(hormone_type, 1.0)

        # Rate constant k = ln(2) / t½
        k = math.log(2) / t_half

        # Rate = k * [C]
        rate = k * current_level

        return rate

    def calculate_occupancy(
        self,
        hormone_level: float,
        kd: Optional[float] = None,
        hill_coefficient: Optional[float] = None,
        receptor_status: Optional[ReceptorStatus] = None,
    ) -> float:
        """
        受体占用计算 / Receptor occupancy (Hill equation)

        Hill equation: Y = [H]ⁿ / (Kdⁿ + [H]ⁿ)

        Args:
            hormone_level: Current hormone concentration
            kd: Dissociation constant (EC50)
            hill_coefficient: Hill coefficient (cooperativity)
            receptor_status: Optional receptor status for regulation effects

        Returns:
            Fraction of receptors occupied (0-1)
        """
        kd = kd or self.default_kd
        n = hill_coefficient or self.default_hill

        # Adjust effective KD based on receptor regulation
        if receptor_status:
            # Upregulation decreases effective KD (increases sensitivity)
            # Downregulation increases effective KD (decreases sensitivity)
            effective_kd = kd / receptor_status.sensitivity
        else:
            effective_kd = kd

        # Hill equation
        if effective_kd == 0:
            return 1.0 if hormone_level > 0 else 0.0

        occupancy = (hormone_level**n) / ((effective_kd**n) + (hormone_level**n))

        return min(1.0, max(0.0, occupancy))

    def update_receptor_regulation(
        self, hormone_type: HormoneType, chronic_level: float, time_days: float = 1.0
    ) -> ReceptorStatus:
        """
        受体调节 / Receptor regulation (upregulation/downregulation)

        Chronic high hormone levels lead to downregulation (desensitization).
        Chronic low levels lead to upregulation (sensitization).

        Args:
            hormone_type: Type of hormone
            chronic_level: Average level over time period (normalized 0-1)
            time_days: Time period for regulation (days)

        Returns:
            Updated ReceptorStatus
        """
        status = self.receptor_status[hormone_type]

        # Regulation rate (per day)
        regulation_rate = 0.1 * time_days

        if chronic_level > 0.7:
            # High chronic level -> downregulation (desensitization)
            status.downregulation += regulation_rate * (chronic_level - 0.7)
            status.upregulation = max(0.5, status.upregulation - regulation_rate * 0.5)
        elif chronic_level < 0.3:
            # Low chronic level -> upregulation (sensitization)
            status.upregulation += regulation_rate * (0.3 - chronic_level)
            status.downregulation = max(0.5, status.downregulation - regulation_rate * 0.5)
        else:
            # Normal levels -> gradual return to baseline
            status.upregulation = 1.0 + (status.upregulation - 1.0) * 0.9
            status.downregulation = 1.0 + (status.downregulation - 1.0) * 0.9

        # Calculate overall sensitivity
        status.sensitivity = status.upregulation / status.downregulation
        status.sensitivity = max(0.3, min(3.0, status.sensitivity))

        return status

    def calculate_secretion(
        self,
        basal_rate: float,
        stimulus: float,
        pulse_frequency: float = 1.0,
        pulse_amplitude: float = 0.3,
        time_hours: float = 0.0,
    ) -> float:
        """
        分泌调节计算 / Secretion regulation (basal + pulsatile)

        Many hormones are secreted in pulses superimposed on basal secretion.

        Formula: S = S_basal + S_stimulus + S_pulse

        Args:
            basal_rate: Basal secretion rate
            stimulus: Stimulus-induced secretion
            pulse_frequency: Pulses per hour
            pulse_amplitude: Amplitude of pulses (as fraction of basal)
            time_hours: Current time (for pulse phase)

        Returns:
            Total secretion rate
        """
        # Basal secretion
        secretion = basal_rate

        # Stimulus-induced secretion
        secretion += stimulus

        # Pulsatile component (sinusoidal)
        if pulse_frequency > 0:
            pulse_phase = 2 * math.pi * pulse_frequency * time_hours
            pulse = basal_rate * pulse_amplitude * math.sin(pulse_phase)
            secretion += pulse

        return max(0.0, secretion)

    def get_receptor_status(self, hormone_type: HormoneType) -> ReceptorStatus:
        """获取受体状态 / Get receptor status for a hormone"""
        return self.receptor_status.get(
            hormone_type,
            ReceptorStatus(
                receptor_type="unknown",
                occupancy=0.0,
                upregulation=1.0,
                downregulation=1.0,
                sensitivity=1.0,
            ),
        )

    def get_all_receptor_status(self) -> Dict[HormoneType, ReceptorStatus]:
        """获取所有受体状态 / Get all receptor statuses"""
        return self.receptor_status.copy()
