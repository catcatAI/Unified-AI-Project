import logging
import math
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)

class KineticValidator:
    """
    Angela 的動力學驗證器 (2030 Standard)
    確保肢體動作與位移符合物理極限與生物約束。
    """
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        # 根據「四肢實體約束矩陣」定義的物理極限
        self.max_velocity = self.config.get('max_velocity', 500.0)  # px/s, overridable via config
        self.max_acceleration = self.config.get('max_acceleration', 200.0)  # px/s^2
        self.last_pos = None
        self.last_time = None

    def validate_action(self, action_name: str, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """
        驗證動作是否符合動力學限制。
        """
        if action_name == "move":
            return self._validate_movement(parameters)
        return True, ""

    def _validate_movement(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate movement parameters against physics constraints."""
        import time
        current_time = time.time()
        tx, ty = params.get("x", 0), params.get("y", 0)

        if self.last_pos is not None and self.last_time is not None:
            dt = current_time - self.last_time
            if dt > 0:
                dist = math.sqrt((tx - self.last_pos[0])**2 + (ty - self.last_pos[1])**2)
                velocity = dist / dt
                if velocity > self.max_velocity:
                    return False, f"Velocity too high ({velocity:.1f} > {self.max_velocity})"

        self.last_pos = (tx, ty)
        self.last_time = current_time
        return True, "Success"

    def apply_biological_strain(
        self, parameters: Dict[str, Any], strain_factor: float
    ) -> Dict[str, Any]:
        """Apply biological strain to action parameters based on current physical state.

        When strain is high, movement speeds and intensities are reduced
        to simulate fatigue or caution.

        Args:
            parameters: Action parameters dict
            strain_factor: Current biological strain level (0.0-1.0+)

        Returns:
            Modified parameters with strain applied
        """
        if strain_factor <= 0.0:
            return parameters

        params = dict(parameters)  # mutable copy

        # Reduce movement speed based on strain (strongest effect)
        if "speed" in params and isinstance(params["speed"], (int, float)):
            params["speed"] = params["speed"] * (1.0 - min(strain_factor, 1.0) * 0.5)

        # Reduce velocity/force/intensity (moderate effect)
        for key in ("velocity", "force", "intensity", "power"):
            if key in params and isinstance(params[key], (int, float)):
                params[key] = params[key] * (1.0 - min(strain_factor, 1.0) * 0.3)

        # Reduce movement distances/amplitudes (mild effect)
        for key in ("distance", "amplitude", "range", "step"):
            if key in params and isinstance(params[key], (int, float)):
                params[key] = params[key] * (1.0 - min(strain_factor, 1.0) * 0.2)

        logger.debug(
            "[KineticValidator] Applied strain %.2f to parameters: %s",
            strain_factor,
            {k: v for k, v in params.items() if parameters.get(k) != v},
        )

        return params

    def calculate_strain(self, velocity: float) -> float:
        """根據速度計算產生的生理負擔 (Strain)"""
        # 2030 標準：劇烈運動增加壓力
        if velocity > self.max_velocity * 0.8:
            return 0.15 # 顯著壓力
        return 0.01
