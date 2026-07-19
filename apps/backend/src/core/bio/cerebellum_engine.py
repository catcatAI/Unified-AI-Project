# =============================================================================
# ANGELA-MATRIX: L1-L6[小腦] γ [A] L2+
# =============================================================================
# 職責: 小腦運動神經系統 (Cerebellum Engine).
# 維度: 物理維度 (γ) 的運動插值、震顫控制與步態演化。
# =============================================================================


import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_POSTURES = {
    "standing": {
        "theta_matrix": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "finger_left": [0.0, 0.0, 0.0, 0.0, 0.0],
        "finger_right": [0.0, 0.0, 0.0, 0.0, 0.0],
        "description": "Neutral standing posture",
    },
    "walking": {
        "theta_matrix": [0.05, 0.02, -0.02, 0.08, 0.03, -0.03, 0.06, 0.01, -0.01],
        "finger_left": [0.2, 0.2, 0.1, 0.1, 0.0],
        "finger_right": [0.2, 0.2, 0.1, 0.1, 0.0],
        "description": "Bipedal walking gait",
    },
    "sitting": {
        "theta_matrix": [0.3, 0.2, 0.15, -0.4, -0.3, -0.2, -0.6, -0.5, -0.3],
        "finger_left": [0.3, 0.3, 0.2, 0.2, 0.1],
        "finger_right": [0.3, 0.3, 0.2, 0.2, 0.1],
        "description": "Seated posture with spine curved",
    },
    "reaching": {
        "theta_matrix": [0.1, 0.05, 0.0, 0.05, 0.15, 0.25, 0.2, 0.1, 0.05],
        "finger_left": [0.0, 0.0, 0.0, 0.0, 0.0],
        "finger_right": [0.8, 0.7, 0.6, 0.5, 0.3],
        "description": "Arm extended forward reaching",
    },
}


class CerebellumEngine:
    """Cerebellum motor coordination system.

    Manages posture library, smooth interpolation between postures,
    physiological tremor modeling, and proprioceptive error correction.
    Used by Heartbeat for real-time pose generation and by BiologicalIntegrator
    for state synchronization.
    """

    def __init__(self):
        self._postures: Dict[str, Dict[str, Any]] = dict(_DEFAULT_POSTURES)
        self._current_pose_name: str = "standing"
        self._current_posture: Dict[str, Any] = dict(self._postures["standing"])
        self._predicted_theta: List[float] = [0.0] * 9
        self._proprioception_error: List[float] = [0.0] * 9
        self._tremor_frequency: float = 10.0
        self._tremor_amplitude_base: float = 0.005
        self._initialized: bool = False
        self._total_time: float = 0.0

    async def initialize(self) -> None:
        """Load posture library and mark engine as ready."""
        self._current_posture = dict(self._postures.get("standing", {"theta_matrix": [0.0] * 9}))
        self._predicted_theta = list(self._current_posture.get("theta_matrix", [0.0] * 9))
        self._initialized = True
        logger.info("CerebellumEngine initialized with %d postures", len(self._postures))

    def update_proprioception(self, actual_theta: Optional[List[float]] = None) -> None:
        """Compare predicted vs actual theta to compute proprioceptive error."""
        if actual_theta is None:
            return
        predicted = self._predicted_theta
        actual = actual_theta
        n = min(len(predicted), len(actual))
        self._proprioception_error = [predicted[i] - actual[i] if i < n else 0.0 for i in range(9)]
        self._predicted_theta = (
            list(actual) if len(actual) >= 9 else (actual + [0.0] * (9 - len(actual)))
        )

    def get_posture(self, name: str = "default") -> Dict[str, Any]:
        """Retrieve a named posture from the library."""
        if name == "default":
            name = self._current_pose_name
        posture = self._postures.get(name)
        if posture is None:
            logger.debug("Unknown posture '%s', falling back to standing", name)
            name = "standing"
            posture = self._postures["standing"]
        return {
            "name": name,
            "joints": {},
            "theta_matrix": list(posture["theta_matrix"]),
            "finger_left": list(posture.get("finger_left", [0.0] * 5)),
            "finger_right": list(posture.get("finger_right", [0.0] * 5)),
        }

    def interpolate(
        self, from_posture: Dict[str, Any], to_posture: Dict[str, Any], t: float = 0.5
    ) -> Dict[str, Any]:
        """Linear interpolation between two postures.

        Args:
            from_posture: source posture (theta_matrix, finger_left, finger_right)
            to_posture: target posture with same structure
            t: interpolation factor (0.0 = source, 1.0 = target)
        """
        t = max(0.0, min(1.0, t))
        src_theta = from_posture.get("theta_matrix", [0.0] * 9)
        dst_theta = to_posture.get("theta_matrix", [0.0] * 9)
        n = min(len(src_theta), len(dst_theta))
        theta = [src_theta[i] + (dst_theta[i] - src_theta[i]) * t for i in range(n)]
        if n < 9:
            theta.extend([0.0] * (9 - n))
        result = {"theta_matrix": theta}

        for hand in ("finger_left", "finger_right"):
            src_f = from_posture.get(hand, [0.0] * 5)
            dst_f = to_posture.get(hand, [0.0] * 5)
            n_f = min(len(src_f), len(dst_f))
            fingers = [src_f[i] + (dst_f[i] - src_f[i]) * t for i in range(n_f)]
            if n_f < 5:
                fingers.extend([0.0] * (5 - n_f))
            result[hand] = fingers
        return result

    def execute_command(
        self, pose_name: str, bio_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a motor command for the given pose, modulated by biological state.

        Args:
            pose_name: target pose name (e.g. 'standing', 'walking', 'sitting')
            bio_state: optional dict with 'stress_level', 'fatigue', etc. from BiologicalIntegrator

        Returns:
            dict with 'pose_name', 'theta_matrix', 'finger_matrix', 'tremor_active'
        """
        self._current_pose_name = pose_name if pose_name in self._postures else "standing"
        target = self._postures[self._current_pose_name]

        self._total_time += 0.016

        stress = 0.0
        if bio_state and isinstance(bio_state, dict):
            stress = float(bio_state.get("stress_level", 0.0))
        tremor_amp = self._tremor_amplitude_base * (1.0 + stress * 3.0)
        tremor_active = tremor_amp > 0.002

        theta = list(target["theta_matrix"])
        if tremor_active:
            import math as _m

            for i in range(9):
                _phase = 2.0 * _m.pi * self._tremor_frequency * self._total_time + i * 1.3
                theta[i] += tremor_amp * _m.sin(_phase)
                corr = self._proprioception_error[i] * 0.1
                theta[i] += corr if i < len(self._proprioception_error) else 0.0

        self._predicted_theta = list(theta)

        return {
            "pose_name": self._current_pose_name,
            "theta_matrix": theta,
            "finger_matrix": {
                "left": list(target.get("finger_left", [0.0] * 5)),
                "right": list(target.get("finger_right", [0.0] * 5)),
            },
            "tremor_active": tremor_active,
        }
